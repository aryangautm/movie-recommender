import hmac
import hashlib
import base64
from app.core.config import settings

ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
BASE = len(ALPHABET)


def _b62_encode_fixed(n: int, width: int) -> str:
    if n < 0:
        raise ValueError("negative")
    chars = []
    while n > 0:
        n, rem = divmod(n, BASE)
        chars.append(ALPHABET[rem])
    s = "".join(reversed(chars)) if chars else "0"
    # left-pad with the first alphabet char ('0') to width
    if len(s) > width:
        raise ValueError("value too large for fixed width")
    return ALPHABET[0] * (width - len(s)) + s


def _b62_decode(s: str) -> int:
    n = 0
    for ch in s:
        idx = ALPHABET.find(ch)
        if idx == -1:
            raise ValueError("invalid base62 character")
        n = n * BASE + idx
    return n


def _hmac_digit(data: bytes, mac_key: bytes) -> int:
    mac = hmac.new(mac_key, data, hashlib.sha256).digest()
    # Use first byte to derive a digit 0..61
    return mac[0] % BASE


class IDCodec:
    def __init__(self, xor_key_24bit: int, mac_key: bytes):
        if not (0 <= xor_key_24bit <= 0xFFFFFF):
            raise ValueError("xor_key_24bit must be 24-bit (0..0xFFFFFF)")
        self.xor_key = xor_key_24bit
        self.mac_key = mac_key
        # Config: 24-bit space -> 5 base62 chars (since 62^5 > 2^24)
        self.payload_width = 5
        self.total_len = self.payload_width + 1  # +1 check digit

    def encrypt_id(self, id_value: int) -> str:
        if not (0 <= id_value <= 9_999_999):
            raise ValueError("id out of range (0..9,999,999)")
        m = id_value ^ self.xor_key  # 24-bit reversible mix
        code5 = _b62_encode_fixed(m, self.payload_width)
        t = _hmac_digit(code5.encode("ascii"), self.mac_key)
        check_char = ALPHABET[t]
        return code5 + check_char  # fixed 6 chars

    def decrypt_id(self, code: str) -> int:
        if len(code) != self.total_len:
            raise ValueError("invalid code length")
        code5, check_char = code[:-1], code[-1]
        # Verify check digit
        t = _hmac_digit(code5.encode("ascii"), self.mac_key)
        if ALPHABET[t] != check_char:
            raise ValueError("tamper detected or wrong key")
        m = _b62_decode(code5)
        id_value = m ^ self.xor_key
        if not (0 <= id_value <= 9_999_999):
            raise ValueError("decoded id out of allowed range")
        return id_value


XOR_KEY_24 = int(settings.IDCODEC_XOR_KEY_HEX, 16)
MAC_KEY = base64.urlsafe_b64decode(settings.IDCODEC_MAC_KEY_B64)

codec = IDCodec(XOR_KEY_24, MAC_KEY)


def encrypt_id(id_value: int) -> str:
    return codec.encrypt_id(id_value)


def decrypt_id(code: str) -> int:
    return codec.decrypt_id(code)
