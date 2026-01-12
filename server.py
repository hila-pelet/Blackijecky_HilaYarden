import socket
import time
import threading
import random
from protocol import *

class GameServer:
    def __init__(self, port=0):
        # Initialize TCP socket for game connections
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_socket.bind(('', port))
        self.tcp_socket.listen()
        self.tcp_port = self.tcp_socket.getsockname()[1]
        self.server_name = "HilaAndYarden"
        
        # Try to find the local IP address for printing
        try:
            self.ip_address = socket.gethostbyname(socket.gethostname())
        except:
            self.ip_address = "127.0.0.1"
            
        print(f"Server started, listening on IP address {self.ip_address}")

    def broadcast_offers(self):
        """
        Broadcasts UDP offer messages every 1 second.
        Runs in a separate thread.
        """
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        packet = pack_offer(self.tcp_port, self.server_name)
        
        while True:
            # Broadcast to the specified UDP port
            udp_socket.sendto(packet, ('<broadcast>', UDP_PORT))
            time.sleep(1)

    def get_card_value(self, rank):
        """Returns the Blackjack value of a card."""
        if rank == 1: return 11 # Ace starts as 11
        if rank >= 10: return 10 # Face cards are 10
        return rank

    def calculate_hand(self, cards):
        """Calculates the total hand value, adjusting Aces if needed."""
        total = sum(self.get_card_value(c[0]) for c in cards)
        aces = sum(1 for c in cards if c[0] == 1)
        # If bust, treat Aces as 1 instead of 11
        while total > 21 and aces > 0:
            total -= 10
            aces -= 1
        return total

    def handle_game(self, client_socket, num_rounds):
        """Manages the full game session for a specific client."""
        for i in range(num_rounds):
            print(f"--- Starting Round {i+1} ---")
            # Create and shuffle a deck (ranks 1-13, suits 0-3)
            deck = [(rank, suit) for rank in range(1, 14) for suit in range(4)]
            random.shuffle(deck)
            
            player_cards = []
            dealer_cards = []
            
            # Initial deal: Player gets 2, Dealer gets 2 (one hidden)
            
            # Deal card 1 to player
            card = deck.pop()
            player_cards.append(card)
            client_socket.sendall(pack_server_payload(RESULT_ACTIVE, card[0], card[1]))
            time.sleep(0.1) # Small delay to prevent packet merging

            # Deal card 2 to player
            card = deck.pop()
            player_cards.append(card)
            client_socket.sendall(pack_server_payload(RESULT_ACTIVE, card[0], card[1]))
            time.sleep(0.1)

            # Deal card 1 to dealer (visible)
            card = deck.pop()
            dealer_cards.append(card)
            client_socket.sendall(pack_server_payload(RESULT_ACTIVE, card[0], card[1]))
            time.sleep(0.1)

            # Deal card 2 to dealer (hidden)
            dealer_hidden = deck.pop()
            dealer_cards.append(dealer_hidden)

            # Player's turn
            player_bust = False
            while True:
                try:
                    data = client_socket.recv(1024)
                    decision = unpack_client_payload(data)
                    
                    if decision == "Hittt":
                        new_card = deck.pop()
                        player_cards.append(new_card)
                        
                        # Check if player busted
                        if self.calculate_hand(player_cards) > 21:
                            # Send card with LOSS result
                            client_socket.sendall(pack_server_payload(RESULT_LOSE, new_card[0], new_card[1]))
                            player_bust = True
                            break
                        else:
                            # Send card and continue
                            client_socket.sendall(pack_server_payload(RESULT_ACTIVE, new_card[0], new_card[1]))
                            
                    elif decision == "Stand":
                        break
                except:
                    return # Connection lost

            # If player didn't bust, Dealer's turn
            if not player_bust:
                # Reveal dealer's hidden card
                client_socket.sendall(pack_server_payload(RESULT_ACTIVE, dealer_hidden[0], dealer_hidden[1]))
                time.sleep(0.1)
                
                # Dealer logic: Hit until 17 or more
                while self.calculate_hand(dealer_cards) < 17:
                    new_card = deck.pop()
                    dealer_cards.append(new_card)
                    client_socket.sendall(pack_server_payload(RESULT_ACTIVE, new_card[0], new_card[1]))
                    time.sleep(0.1)
                
                # Determine winner
                p_sum = self.calculate_hand(player_cards)
                d_sum = self.calculate_hand(dealer_cards)
                
                result = RESULT_TIE
                if d_sum > 21: result = RESULT_WIN # Dealer busted
                elif p_sum > d_sum: result = RESULT_WIN
                elif d_sum > p_sum: result = RESULT_LOSE
                
                # Send final result (with dummy card values)
                client_socket.sendall(pack_server_payload(result, 0, 0))

    def handle_client(self, client_socket, addr):
        """Thread function to handle a new client connection."""
        print(f"Connection accepted from {addr}")
        try:
            # Step 1: Receive TCP Request
            data = client_socket.recv(1024)
            request = unpack_request(data)
            
            if request:
                num_rounds, team_name = request
                print(f"Team '{team_name}' wants to play {num_rounds} rounds.")
                self.handle_game(client_socket, num_rounds)
            else:
                print("Invalid request received.")
                
        except Exception as e:
            print(f"Error handling client: {e}")
        finally:
            client_socket.close()
            print(f"Connection closed for {addr}")

    def start(self):
        # Start UDP broadcast in background thread
        threading.Thread(target=self.broadcast_offers, daemon=True).start()
        
        # Main loop to accept TCP connections
        while True:
            client_socket, addr = self.tcp_socket.accept()
            # Handle each client in a separate thread
            threading.Thread(target=self.handle_client, args=(client_socket, addr)).start()

if __name__ == "__main__":
    GameServer().start()