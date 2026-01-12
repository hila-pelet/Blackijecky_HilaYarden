import socket
import time
import threading
import random
from protocol import *

class GameServer:
    def __init__(self, port=0):
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_socket.bind(('', port))
        self.tcp_socket.listen()
        self.tcp_port = self.tcp_socket.getsockname()[1]
        self.server_name = "HilaAndYarden"
        
        try:
            self.ip_address = socket.gethostbyname(socket.gethostname())
        except:
            self.ip_address = "127.0.0.1"
            
        print(f"Server started, listening on IP address {self.ip_address}")

    def broadcast_offers(self):
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        packet = pack_offer(self.tcp_port, self.server_name)
        while True:
            udp_socket.sendto(packet, ('<broadcast>', UDP_PORT))
            time.sleep(1)

    def get_card_value(self, rank):
        """חישוב ערך קלף לבלאק ג'ק"""
        if rank == 1: return 11 # Ace מתחיל כ-11
        if rank >= 10: return 10 # J, Q, K הם 10
        return rank

    def calculate_hand(self, cards):
        """חישוב סכום היד עם טיפול באסים"""
        total = sum(self.get_card_value(c[0]) for c in cards)
        aces = sum(1 for c in cards if c[0] == 1)
        while total > 21 and aces > 0:
            total -= 10
            aces -= 1
        return total

    def handle_game(self, client_socket, num_rounds):
        for i in range(num_rounds):
            print(f"--- Starting Round {i+1} ---")
            # יצירת חפיסה וערבוב (1-13 דרגות, 0-3 צורות)
            deck = [(rank, suit) for rank in range(1, 14) for suit in range(4)]
            random.shuffle(deck)
            
            player_cards = []
            dealer_cards = []
            
            # חלוקה ראשונית: שחקן מקבל 2, דילר מקבל 2 (אחד מוסתר)
            # שולחים ללקוח את הקלפים שלו ואת הקלף הגלוי של הדילר
            
            # קלף 1 לשחקן
            card = deck.pop()
            player_cards.append(card)
            client_socket.sendall(pack_server_payload(RESULT_ACTIVE, card[0], card[1]))
            time.sleep(0.1) # השהייה קטנה למנוע הדבקת הודעות

            # קלף 2 לשחקן
            card = deck.pop()
            player_cards.append(card)
            client_socket.sendall(pack_server_payload(RESULT_ACTIVE, card[0], card[1]))
            time.sleep(0.1)

            # קלף 1 לדילר (גלוי)
            card = deck.pop()
            dealer_cards.append(card)
            client_socket.sendall(pack_server_payload(RESULT_ACTIVE, card[0], card[1]))
            time.sleep(0.1)

            # קלף 2 לדילר (מוסתר - לא שולחים עדיין)
            dealer_hidden = deck.pop()
            dealer_cards.append(dealer_hidden)

            # תור השחקן
            player_bust = False
            while True:
                try:
                    data = client_socket.recv(1024)
                    decision = unpack_client_payload(data)
                    
                    if decision == "Hittt": # הלקוח ביקש קלף
                        new_card = deck.pop()
                        player_cards.append(new_card)
                        
                        # בדיקה אם נשרף
                        if self.calculate_hand(player_cards) > 21:
                            # שלח קלף עם הודעת הפסד
                            client_socket.sendall(pack_server_payload(RESULT_LOSE, new_card[0], new_card[1]))
                            player_bust = True
                            break
                        else:
                            # שלח קלף והמשך
                            client_socket.sendall(pack_server_payload(RESULT_ACTIVE, new_card[0], new_card[1]))
                            
                    elif decision == "Stand":
                        break
                except:
                    return # התנתקות

            # אם השחקן לא נשרף, תור הדילר
            if not player_bust:
                # קודם כל חושפים את הקלף המוסתר
                client_socket.sendall(pack_server_payload(RESULT_ACTIVE, dealer_hidden[0], dealer_hidden[1]))
                time.sleep(0.1)
                
                # הדילר לוקח קלפים עד 17
                while self.calculate_hand(dealer_cards) < 17:
                    new_card = deck.pop()
                    dealer_cards.append(new_card)
                    client_socket.sendall(pack_server_payload(RESULT_ACTIVE, new_card[0], new_card[1]))
                    time.sleep(0.1)
                
                # חישוב המנצח
                p_sum = self.calculate_hand(player_cards)
                d_sum = self.calculate_hand(dealer_cards)
                
                result = RESULT_TIE
                if d_sum > 21: result = RESULT_WIN # דילר נשרף
                elif p_sum > d_sum: result = RESULT_WIN
                elif d_sum > p_sum: result = RESULT_LOSE
                
                # שליחת התוצאה הסופית (עם קלף דמי כי הפרוטוקול מחייב)
                client_socket.sendall(pack_server_payload(result, 0, 0))

    def handle_client(self, client_socket, addr):
        print(f"Connection accepted from {addr}")
        try:
            data = client_socket.recv(1024)
            request = unpack_request(data)
            if request:
                num_rounds, team_name = request
                print(f"Team '{team_name}' wants to play {num_rounds} rounds.")
                self.handle_game(client_socket, num_rounds)
            else:
                print("Invalid request.")
        except Exception as e:
            print(f"Error: {e}")
        finally:
            client_socket.close()
            print(f"Connection closed for {addr}")

    def start(self):
        threading.Thread(target=self.broadcast_offers, daemon=True).start()
        while True:
            client_socket, addr = self.tcp_socket.accept()
            threading.Thread(target=self.handle_client, args=(client_socket, addr)).start()

if __name__ == "__main__":
    GameServer().start()