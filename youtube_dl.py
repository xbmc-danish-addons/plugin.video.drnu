import binascii
import hashlib
from math import ceil
import struct

# https://github.com/rg3/youtube-dl/blob/master/youtube_dl/aes.py
from aes import aes_cbc_decrypt


# from utils.py
# https://github.com/rg3/youtube-dl/blob/master/youtube_dl/utils.py
def bytes_to_intlist(bs):
    if not bs:
        return []
    if isinstance(bs[0], int):  # Python 3
        return list(bs)
    else:
        return [ord(c) for c in bs]

def intlist_to_bytes(xs):
    if not xs:
        return b''
    return compat_struct_pack('%dB' % len(xs), *xs)


# from compat.py
# https://github.com/rg3/youtube-dl/blob/master/youtube_dl/compat.py
try:
    struct.pack('!I', 0)
except TypeError:
    # In Python 2.6 and 2.7.x < 2.7.7, struct requires a bytes argument
    # See https://bugs.python.org/issue19099
    def compat_struct_pack(spec, *args):
        if isinstance(spec, compat_str):
            spec = spec.encode('ascii')
        return struct.pack(spec, *args)
else:
    compat_struct_pack = struct.pack

# from drtv.py
# https://github.com/rg3/youtube-dl/blob/master/youtube_dl/extractor/drtv.py
def hex_to_bytes(hex):
    return binascii.a2b_hex(hex.encode('ascii'))

def decrypt_uri(e):
    n = int(e[2:10], 16)
    a = e[10 + n:]
    data = bytes_to_intlist(hex_to_bytes(e[10:10 + n]))
    key = bytes_to_intlist(hashlib.sha256(
        ('%s:sRBzYNXBzkKgnjj8pGtkACch' % a).encode('utf-8')).digest())
    iv = bytes_to_intlist(hex_to_bytes(a))
    decrypted = aes_cbc_decrypt(data, key, iv)
    return intlist_to_bytes(
        decrypted[:-decrypted[-1]]).decode('utf-8').split('?')[0]
