import socket
from protocol import *

class GameClient:
    def __init__(self):
        self.team_name = "HilaAndYarden"
        print("Client started, listening for offer requests...")
        
    def listen_for_offers(self):
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        udp_socket.bind(('', UDP_PORT))

        try:
            data, addr = udp_socket.recvfrom(1024)
            result = unpack_offer(data)
            if result:
                server_port, server_name = result
                print(f"Received offer from {server_name} at address {addr[0]}, attempting to connect...")
                self.connect_to_server(addr[0], server_port)
        finally:
            udp_socket.close()

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
            
            # לולאת הסיבובים
            for i in range(rounds):
                print(f"\n--- Round {i+1} ---")
                self.play_round(tcp_socket)
                
            print("Game finished!")
            
        except Exception as e:
            print(f"Connection error: {e}")
        finally:
            tcp_socket.close()

    def play_round(self, sock):
        cards_received = 0
        
        while True:
            # קבלת הודעה מהשרת
            data = sock.recv(1024)
            if not data: break
            
            parsed = unpack_server_payload(data)
            if not parsed: continue
            
            result, rank, suit = parsed
            
            # אם קיבלנו קלף אמיתי (לא קלף סיום דמי)
            if rank != 0:
                suit_names = ['Spades', 'Hearts', 'Diamonds', 'Clubs']
                rank_names = {1:'Ace', 11:'Jack', 12:'Queen', 13:'King'}
                r_str = rank_names.get(rank, str(rank))
                s_str = suit_names[suit] if 0 <= suit <= 3 else '?'
                
                # זיהוי למי שייך הקלף לפי הסדר
                # 2 הראשונים לשחקן, השלישי לדילר. כל השאר תלוי במשחק.
                if cards_received == 0: print(f"You got: {r_str} of {s_str}")
                elif cards_received == 1: print(f"You got: {r_str} of {s_str}")
                elif cards_received == 2: print(f"Dealer got: {r_str} of {s_str}")
                else: print(f"Card dealt: {r_str} of {s_str}")
                
                cards_received += 1
            
            # בדיקת מצב המשחק
            if result != RESULT_ACTIVE:
                if result == RESULT_WIN: print("You Won! :)")
                elif result == RESULT_LOSE: print("You Lost! :(")
                elif result == RESULT_TIE: print("It's a Tie!")
                break # סוף הסיבוב
            
            # לוגיקה מתי לשאול את המשתמש
            # שואלים רק אחרי שקיבלנו את 3 הקלפים הראשונים, או אחרי כל קלף נוסף שלקחנו
            # אם זה תור הדילר (אנחנו ב-Stand), אנחנו לא שואלים
            
            # ההנחה: אם קיבלנו כרגע קלף והתוצאה עדיין ACTIVE, 
            # ואנחנו אחרי החלוקה הראשונית (3 קלפים), זה הזמן לשאול.
            # אבל צריך להיזהר לא לשאול אם אנחנו כבר עשינו Stand.
            # כאן נשתמש בטריק פשוט: אם הקלף שקיבלנו הוא ה-3 ומעלה, נשאל.
            # הדילר מתחיל לשחק רק אחרי שעשינו Stand, אז הקליינט שלנו יפסיק לשאול ברגע שנבחר Stand.
            
            if cards_received >= 3:
                # שואלים את המשתמש
                while True:
                    choice = input("Hit or Stand? (h/s): ").lower()
                    if choice == 'h':
                        sock.sendall(pack_client_payload("Hittt")) # חייב להיות 5 תווים
                        break # מחכים לקלף הבא
                    elif choice == 's':
                        sock.sendall(pack_client_payload("Stand"))
                        # עכשיו נכנסים למצב צפייה בלבד (לולאה פנימית) עד הסוף
                        self.watch_dealer(sock)
                        return # סיימנו את הסיבוב הזה בפונקציה הראשית

    def watch_dealer(self, sock):
        """פונקציה שרק מדפיסה קלפים עד שהסיבוב נגמר"""
        while True:
            data = sock.recv(1024)
            parsed = unpack_server_payload(data)
            if not parsed: break
            
            result, rank, suit = parsed
            
            if rank != 0:
                suit_names = ['Spades', 'Hearts', 'Diamonds', 'Clubs']
                rank_names = {1:'Ace', 11:'Jack', 12:'Queen', 13:'King'}
                r_str = rank_names.get(rank, str(rank))
                s_str = suit_names[suit] if 0 <= suit <= 3 else '?'
                print(f"Dealer took: {r_str} of {s_str}")
            
            if result != RESULT_ACTIVE:
                if result == RESULT_WIN: print("You Won! :)")
                elif result == RESULT_LOSE: print("You Lost! :(")
                elif result == RESULT_TIE: print("It's a Tie!")
                return

if __name__ == "__main__":
    GameClient().listen_for_offers()