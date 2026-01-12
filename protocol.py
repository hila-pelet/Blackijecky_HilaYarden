import struct

# קבועים
MAGIC_COOKIE = 0xabcddcba
MSG_TYPE_OFFER = 0x02
MSG_TYPE_REQUEST = 0x03
MSG_TYPE_PAYLOAD = 0x04
UDP_PORT = 13117

# קבועי תוצאת סיבוב
RESULT_ACTIVE = 0
RESULT_TIE = 1
RESULT_LOSE = 2
RESULT_WIN = 3

def pack_offer(server_port, server_name):
    server_name_bytes = server_name.encode('utf-8')[:32].ljust(32, b'\x00')
    return struct.pack('>IBH32s', MAGIC_COOKIE, MSG_TYPE_OFFER, server_port, server_name_bytes)

def unpack_offer(data):
    if len(data) < 39: return None
    try:
        cookie, msg_type, server_port, server_name_bytes = struct.unpack('>IBH32s', data[:39])
        if cookie != MAGIC_COOKIE or msg_type != MSG_TYPE_OFFER: return None
        return server_port, server_name_bytes.decode('utf-8').rstrip('\x00')
    except: return None

def pack_request(num_rounds, team_name):
    team_name_bytes = team_name.encode('utf-8')[:32].ljust(32, b'\x00')
    return struct.pack('>IBB32s', MAGIC_COOKIE, MSG_TYPE_REQUEST, num_rounds, team_name_bytes)

def unpack_request(data):
    if len(data) < 38: return None
    try:
        cookie, msg_type, num_rounds, team_name_bytes = struct.unpack('>IBB32s', data[:38])
        if cookie != MAGIC_COOKIE or msg_type != MSG_TYPE_REQUEST: return None
        return num_rounds, team_name_bytes.decode('utf-8').rstrip('\x00')
    except: return None

def pack_client_payload(decision_str):
    """
    אריזת החלטת הלקוח: Hit/Stand
    Format: Cookie(4) + Type(1) + Decision(5 bytes string)
    """
    # מוודאים שאורך המחרוזת הוא 5 תווים בדיוק (Hittt או Stand)
    decision_bytes = decision_str.encode('utf-8')[:5].ljust(5, b'\x00')
    return struct.pack('>IB5s', MAGIC_COOKIE, MSG_TYPE_PAYLOAD, decision_bytes)

def unpack_client_payload(data):
    """פתיחת החלטת הלקוח בשרת"""
    if len(data) < 10: return None
    try:
        cookie, msg_type, decision_bytes = struct.unpack('>IB5s', data[:10])
        if cookie != MAGIC_COOKIE or msg_type != MSG_TYPE_PAYLOAD: return None
        return decision_bytes.decode('utf-8').rstrip('\x00')
    except: return None

def pack_server_payload(result, rank, suit):
    """
    אריזת הודעת שרת (קלף או תוצאה)
    Format: Cookie(4) + Type(1) + Result(1) + Rank(2) + Suit(1)
    """
    return struct.pack('>IBBHB', MAGIC_COOKIE, MSG_TYPE_PAYLOAD, result, rank, suit)

def unpack_server_payload(data):
    """פתיחת הודעת שרת בלקוח"""
    if len(data) < 9: return None
    try:
        cookie, msg_type, result, rank, suit = struct.unpack('>IBBHB', data[:9])
        if cookie != MAGIC_COOKIE or msg_type != MSG_TYPE_PAYLOAD: return None
        return result, rank, suit
    except: return None