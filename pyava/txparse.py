from collections import namedtuple
from enum import Enum, auto
import enum
import binascii
from typing import List, Tuple, Dict
import typing
import struct
import requests
import json
import os.path
from pprint import pprint
join = os.path.join

from pyava import *

TypedTuple = typing.NamedTuple

Chunk = namedtuple('Chunk', ['name', 'size', 'type', 'arrhdr'], defaults=[None, None, None, 4])
Struct = namedtuple('Struct', ['name', 'props'])

TypeSwitch = namedtuple('TypeSwitch', [])


@enum.unique
class SizeSpec(Enum):
    Array = 'Array' # contains N * Type
    NatArray = 'NatArray' # contains N, cast to (native) Type
    ByType = 'ByType'


Secp256k1Output = Struct('Secp256k1Output', [
    Chunk('typeid', 4, int),
    Chunk('amount', 8, int),  # TODO implement this
    Chunk('locktime', 8, int),
    Chunk('threshold', 4, int),
    Chunk('addresses', SizeSpec.Array, Chunk(None, 20, bytes))
])
    
TransferableOutput = Struct('TransferableOutput', [
    Chunk('assetid', 32, bytes),
    Chunk('output', SizeSpec.ByType, Secp256k1Output)
])

Secp256k1Input = Struct('Secp256k1Input', [
    Chunk('typeid', 4, int),
    Chunk('amount', 8, int),
    Chunk('addressindices', SizeSpec.Array, Chunk(None, 4, int))
])

TransferableInput = Struct('TransferableInput', [
    Chunk('txid', 32, bytes),
    Chunk('utxoindex', 4, int),
    Chunk('assetid', 32, bytes),
    Chunk('input', SizeSpec.ByType, Secp256k1Input)
])

BaseTx = Struct('BaseTx', [
    Chunk('typeid', 4, int),
    Chunk('networkid', 4, int),
    Chunk('blockchainid', 32, bytes),
    Chunk('outputs', SizeSpec.Array, TransferableOutput),
    Chunk('inputs', SizeSpec.Array, TransferableInput),
    Chunk('memo', SizeSpec.NatArray, bytes)
])

Validator = Struct('Validator', [
    Chunk('NodeID', 20, bytes),
    Chunk('Start', 8, int),
    Chunk('End', 8, int),
    Chunk('Wght', 8, int)
])


Secp256k1OutputOwners = Struct('Secp256k1OutputOwners', [
    Chunk('typeid', 4, int),
    Chunk('locktime', 8, int),
    Chunk('threshold', 4, int),
    Chunk('addresses', SizeSpec.Array, Chunk(None, 20, bytes))
])

AddDelegatorTx = Struct('AddDelegatorTx', [
    Chunk('baseTx', SizeSpec.ByType, BaseTx),
    Chunk('validator', SizeSpec.ByType, Validator),
    Chunk('stake', SizeSpec.Array, TransferableOutput),
    Chunk('rewardsOwner', SizeSpec.ByType, Secp256k1OutputOwners)
])

Secp256k1Credential = Struct('Secp256k1Credential', [
    Chunk('typeid', 4, int),
    Chunk('signatures', SizeSpec.Array, Chunk(None, 65, bytes))
])

SignedTx = Struct('SignedTx', [
    Chunk('codec', 2, int),
    Chunk('unsignedTx', SizeSpec.ByType, TypeSwitch),
    Chunk('credentials', SizeSpec.Array, TypeSwitch)
])

InitialState = Struct('InitialState', [
    Chunk('fxid', 4, int),
    Chunk('outputs', SizeSpec.Array, TypeSwitch)
])

CreateAssetTx = Struct('CreateAssetTx', [
    Chunk('baseTx', SizeSpec.ByType, BaseTx),
    Chunk('name', SizeSpec.NatArray, bytes, arrhdr=2),
    Chunk('symbol', SizeSpec.NatArray, bytes, arrhdr=2),
    Chunk('denomination', 1, int),
    Chunk('initialStates', SizeSpec.Array, InitialState)
])

TypeIDs = {
    0x0: BaseTx,
    0x5: Secp256k1Input,
    0x7: Secp256k1Output,
    0xe: AddDelegatorTx,
    0xb: Secp256k1OutputOwners,
    0x9: Secp256k1Credential,
    0x1: CreateAssetTx
}

class IndentPrinter:
    def __init__(self):
        self.cnt = 0

    def indent(self):
        self.cnt += 1

    def dedent(self):
        self.cnt -= 1

    def print(self, s):
        print('\t' * self.cnt + s)

p = IndentPrinter()

def parse_any(data, pos: int, chunk: Chunk) -> Tuple[object, int]:
    #p.print(':parse_any chunk.type={}'.format(chunk.type.name if isinstance(chunk.type, Struct) else chunk.type))
    p.print(':parse_any chunk={}'.format(chunk))

    if isinstance(chunk.type, Struct) or (chunk.type == TypeSwitch):
        return parse(data, pos, chunk.type)

    size = chunk.size
    chopped = data[pos : pos+size]
    if chunk.type == int:
        if size == 4:
            b = struct.unpack('>I', chopped)[0]
        elif size == 2:
            b = struct.unpack('>H', chopped)[0]
        elif size == 1:
            b = struct.unpack('>B', chopped)[0]
        elif size == 8:
            b = struct.unpack('>Q', chopped)[0]
        else:
            raise RuntimeError('unknown size={} for int'.format(size))
        return (b, pos + size)
    elif chunk.type == bytes:
        return (chopped, pos + size)
    elif chunk.type == str:
        return (chopped.decode(), pos + size)
    else:
        raise RuntimeError('unknown type {}'.format(chunk.type))
        

def parse(data, pos: int, typ) -> Tuple[object, int]:
    p.indent()
    result = {}

    if typ == TypeSwitch:
        typ = prescan_type(data, pos)

    for chunk in typ.props:
        p.print('+{} pos={} size={} type={}'.format(chunk.name, pos, chunk.size, typ.name))
        p.print('x' + to_hex(data[pos: pos+20]).decode())

        if chunk.size == SizeSpec.ByType:
            chopped, newpos = parse_any(data, pos, chunk)
            pos = newpos
        elif (chunk.size == SizeSpec.Array):
            rarr = []
            count, newpos = parse_any(data, pos, Chunk(None, chunk.arrhdr, int))
            pos = newpos
            subchunk = chunk
            if isinstance(chunk.type, Chunk): subchunk = chunk.type
            p.print('> Array size {}'.format(count))
            
            for i in range(count):
                p.print('>> Array item at {}'.format(pos))
                item, newpos = parse_any(data, pos, subchunk)
                pos = newpos
                rarr.append(item)
            
            chopped = rarr
        elif chunk.size == SizeSpec.NatArray:
            count, newpos = parse_any(data, pos, Chunk(None, chunk.arrhdr, int))
            pos = newpos
            p.print('> Array size {}'.format(count))

            chopped, newpos = parse_any(data, pos, Chunk(None, count, chunk.type))
            pos = newpos

        elif not(isinstance(chunk.type, Struct)):
            chopped, newpos = parse_any(data, pos, chunk)
            pos = newpos
        
        result_str = binascii.b2a_hex(chopped) if isinstance(chopped, bytes) else chopped
        p.print('. storing {}={}'.format(chunk.name, result_str))
        result[chunk.name] = chopped

    p.dedent()
    return result, pos

def prescan_type(data, pos: int) -> Struct:
    head = data[pos : pos+4]
    headint = struct.unpack('>I', head)[0]
    return TypeIDs[headint]


