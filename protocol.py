import struct

"""
Protocol Constants and Packet Definitions
Based on the Blackijecky assignment specifications.
"""

# Magic cookie validation (4 bytes)
MAGIC_COOKIE = 0xabcddcba

# Message types
MSG_TYPE_OFFER = 0x02
MSG_TYPE_REQUEST = 0x03
MSG_TYPE_PAYLOAD = 0x04

# UDP Port for broadcast listening/sending
# Specified in the assignment guidelines
UDP_PORT = 13122  # FIXED: Changed from 13117 to 13122 per instructions

# Game Result Constants
RESULT_ACTIVE = 0
RESULT_TIE = 1
RESULT_LOSE = 2
RESULT_WIN = 3

def pack_offer(server_port, server_name):
    """
    Packs a UDP offer message.
    Format: Cookie(4), Type(1), Port(2), Name(32)
    """
    # Ensure name is exactly 32 bytes (padded with nulls)
    server_name_bytes = server_name.encode('utf-8')[:32].ljust(32, b'\x00')
    return struct.pack('>IBH32s', MAGIC_COOKIE, MSG_TYPE_OFFER, server_port, server_name_bytes)

def unpack_offer(data):
    """
    Unpacks a UDP offer message.
    Returns: (server_port, server_name) or None if invalid.
    """
    if len(data) < 39: return None
    try:
        cookie, msg_type, server_port, server_name_bytes = struct.unpack('>IBH32s', data[:39])
        if cookie != MAGIC_COOKIE or msg_type != MSG_TYPE_OFFER: return None
        return server_port, server_name_bytes.decode('utf-8').rstrip('\x00')
    except: return None

def pack_request(num_rounds, team_name):
    """
    Packs a TCP request message.
    Format: Cookie(4), Type(1), Rounds(1), Name(32)
    """
    team_name_bytes = team_name.encode('utf-8')[:32].ljust(32, b'\x00')
    return struct.pack('>IBB32s', MAGIC_COOKIE, MSG_TYPE_REQUEST, num_rounds, team_name_bytes)

def unpack_request(data):
    """
    Unpacks a TCP request message.
    Returns: (num_rounds, team_name) or None if invalid.
    """
    if len(data) < 38: return None
    try:
        cookie, msg_type, num_rounds, team_name_bytes = struct.unpack('>IBB32s', data[:38])
        if cookie != MAGIC_COOKIE or msg_type != MSG_TYPE_REQUEST: return None
        return num_rounds, team_name_bytes.decode('utf-8').rstrip('\x00')
    except: return None

def pack_client_payload(decision_str):
    """
    Packs the player's decision (Hit/Stand).
    Format: Cookie(4), Type(1), Decision(5 bytes)
    """
    # Decision must be 5 bytes (e.g., "Hittt", "Stand")
    decision_bytes = decision_str.encode('utf-8')[:5].ljust(5, b'\x00')
    return struct.pack('>IB5s', MAGIC_COOKIE, MSG_TYPE_PAYLOAD, decision_bytes)

def unpack_client_payload(data):
    """Unpacks the client's payload."""
    if len(data) < 10: return None
    try:
        cookie, msg_type, decision_bytes = struct.unpack('>IB5s', data[:10])
        if cookie != MAGIC_COOKIE or msg_type != MSG_TYPE_PAYLOAD: return None
        return decision_bytes.decode('utf-8').rstrip('\x00')
    except: return None

def pack_server_payload(result, rank, suit):
    """
    Packs the server's response (Card or Game Result).
    Format: Cookie(4), Type(1), Result(1), Rank(2), Suit(1)
    """
    return struct.pack('>IBBHB', MAGIC_COOKIE, MSG_TYPE_PAYLOAD, result, rank, suit)

def unpack_server_payload(data):
    """Unpacks the server's payload."""
    if len(data) < 9: return None
    try:
        cookie, msg_type, result, rank, suit = struct.unpack('>IBBHB', data[:9])
        if cookie != MAGIC_COOKIE or msg_type != MSG_TYPE_PAYLOAD: return None
        return result, rank, suit
    except: return None