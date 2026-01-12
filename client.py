import socket
from protocol import *

class GameClient:
    def __init__(self):
        self.team_name = "HilaAndYarden"
        print("Client started, listening for offer requests...")
        
    def listen_for_offers(self):
        # לולאה אינסופית כדי שהלקוח יחזור להקשיב אחרי כל משחק
        while True:
            udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            udp_socket.bind(('', UDP_PORT))

            try:
                # האזנה להצעה
                data, addr = udp_socket.recvfrom(1024)
                result = unpack_offer(data)
                
                if result:
                    server_port, server_name = result
                    print(f"Received offer from {server_name} at address {addr[0]}, attempting to connect...")
                    # סוגרים את ה-UDP לפני שמתחילים לשחק
                    udp_socket.close()
                    
                    # מתחברים לשרת
                    self.connect_to_server(addr[0], server_port)
            except Exception as e:
                print(f"Error: {e}")
            finally:
                try: udp_socket.close() 
                except: pass

    def connect_to_server(self, server_ip, server_port):
        try:
            tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            tcp_socket.connect((server_ip, server_port))
            print("Connected to server!")
            
            try:
                rounds = int(input("How many rounds you want to play? "))
            except:
                rounds = 1
                
            tcp_socket.sendall(pack_request(rounds, self.team_name))
            
            wins = 0 # מונה ניצחונות
            
            for i in range(rounds):
                print(f"\n--- Round {i+1} ---")
                # הפונקציה מחזירה True אם ניצחנו
                if self.play_round(tcp_socket):
                    wins += 1
            
            # הדפסת הסיכום לפי דרישות המטלה
            win_rate = wins / rounds if rounds > 0 else 0
            print(f"Finished playing {rounds} rounds, win rate: {win_rate}")
            
        except Exception as e:
            print(f"Connection error: {e}")
        finally:
            tcp_socket.close()
            print("Game over, listening for new offers...")

    def play_round(self, sock):
        """מנהל סיבוב ומחזיר True לניצחון, False להפסד"""
        cards_received = 0
        while True:
            data = sock.recv(1024)
            if not data: return False
            
            parsed = unpack_server_payload(data)
            if not parsed: continue
            
            result, rank, suit = parsed
            
            if rank != 0:
                self.print_card(rank, suit, cards_received)
                cards_received += 1
            
            # בדיקת תוצאה והחזרת ערך בוליאני
            if result != RESULT_ACTIVE:
                if result == RESULT_WIN:
                    print("You Won! :)")
                    return True
                elif result == RESULT_LOSE:
                    print("You Lost! :(")
                    return False
                elif result == RESULT_TIE:
                    print("It's a Tie!")
                    return False # תיקו לא נחשב ניצחון בחישוב האחוזים
            
            # האם לשאול את המשתמש?
            if cards_received >= 3 and result == RESULT_ACTIVE:
                while True:
                    choice = input("Hit or Stand? (h/s): ").lower()
                    if choice == 'h':
                        sock.sendall(pack_client_payload("Hittt"))
                        break
                    elif choice == 's':
                        sock.sendall(pack_client_payload("Stand"))
                        return self.watch_dealer(sock)

    def watch_dealer(self, sock):
        """צפייה בתור הדילר"""
        while True:
            data = sock.recv(1024)
            parsed = unpack_server_payload(data)
            if not parsed: break
            
            result, rank, suit = parsed
            
            if rank != 0:
                self.print_card(rank, suit, -1)
            
            if result != RESULT_ACTIVE:
                if result == RESULT_WIN:
                    print("You Won! :)")
                    return True
                elif result == RESULT_LOSE:
                    print("You Lost! :(")
                    return False
                elif result == RESULT_TIE:
                    print("It's a Tie!")
                    return False
        return False

    def print_card(self, rank, suit, index):
        suit_names = ['Spades', 'Hearts', 'Diamonds', 'Clubs']
        rank_names = {1:'Ace', 11:'Jack', 12:'Queen', 13:'King'}
        r_str = rank_names.get(rank, str(rank))
        s_str = suit_names[suit] if 0 <= suit <= 3 else '?'
        
        if index == 0 or index == 1: print(f"You got: {r_str} of {s_str}")
        elif index == 2: print(f"Dealer got: {r_str} of {s_str}")
        elif index == -1: print(f"Dealer took: {r_str} of {s_str}")
        else: print(f"Card dealt: {r_str} of {s_str}")

if __name__ == "__main__":
    GameClient().listen_for_offers()