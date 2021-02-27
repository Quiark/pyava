from typing import List, Tuple, Dict
import binascii
import base58
import bech32
from base58 import b58encode, b58decode

to_hex = binascii.b2a_hex
from_hex = binascii.a2b_hex

def b58_tohex(x):
    return   to_hex(base58.b58decode(x)) 

def hex_tob58(x):
    return base58.b58encode(from_hex(x))


def to_addr(b: bytes, chain = 'X') -> str:
    return chain + '-' + bech32.bech32_encode('avax', bech32.convertbits(b, 8, 5, False))

def from_addr(a: str) -> bytes:
    return bytearray(bech32.convertbits(
        bech32.bech32_decode(a.split('-')[1])[1],
        5, 8))

def fmt_amount(a: bytes):
    'Converts amount on blockchain into human-readable AVAX amount.'
    num = struct.unpack('>Q', a)[0]
    return num / 10**9

