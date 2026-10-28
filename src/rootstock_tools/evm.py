"""Minimal audited read-only ABI codec. No external dependency and no signing."""
from __future__ import annotations
import re
from .rpc import ChainError, require_address, HEX32

MASK=(1<<64)-1
ROT=(0,1,62,28,27,36,44,6,55,20,3,10,43,25,39,41,45,15,21,8,18,2,61,56,14)
ROUND=(0x0000000000000001,0x0000000000008082,0x800000000000808a,0x8000000080008000,0x000000000000808b,0x0000000080000001,0x8000000080008081,0x8000000000008009,0x000000000000008a,0x0000000000000088,0x0000000080008009,0x000000008000000a,0x000000008000808b,0x800000000000008b,0x8000000000008089,0x8000000000008003,0x8000000000008002,0x8000000000000080,0x000000000000800a,0x800000008000000a,0x8000000080008081,0x8000000000008080,0x0000000080000001,0x8000000080008008)

def keccak256(message:bytes)->bytes:
    """Ethereum Keccak-256 (NOT NIST SHA3-256)."""
    if type(message) is not bytes: raise ValueError('Keccak input must be bytes')
    rate=136
    # Keccak pad10*1: if the domain byte lands on the last rate byte,
    # the trailing 0x80 bit must be ORed into that SAME byte (0x81).
    # Appending another byte would add an entire spurious permutation block.
    data=bytearray(message)+b'\x01'
    data+=b'\x00'*((-len(data))%rate)
    data[-1]|=0x80
    state=[0]*25
    for start in range(0,len(data),rate):
        block=data[start:start+rate]
        for i in range(rate//8):state[i]^=int.from_bytes(block[i*8:(i+1)*8],'little')
        for rc in ROUND:
            C=[state[x]^state[x+5]^state[x+10]^state[x+15]^state[x+20] for x in range(5)]
            D=[C[(x-1)%5]^((C[(x+1)%5]<<1 | C[(x+1)%5]>>63)&MASK) for x in range(5)]
            for x in range(5):
                for y in range(5): state[x+5*y]^=D[x]
            B=[0]*25
            for x in range(5):
                for y in range(5):
                    i=x+5*y;r=ROT[i];v=state[i]
                    B[y+5*((2*x+3*y)%5)]=((v<<r)|(v>>(64-r if r else 64)))&MASK
            for x in range(5):
                for y in range(5):state[x+5*y]=B[x+5*y]^((~B[(x+1)%5+5*y])&B[(x+2)%5+5*y])
            state[0]^=rc
    return b''.join(x.to_bytes(8,'little') for x in state)[:32]

def selector(signature:str)->str: return '0x'+keccak256(signature.encode()).hex()[:8]
def word(v:int)->str:
    if type(v) is not int or v<0 or v>=2**256:raise ChainError('Invalid ABI uint256')
    return f'{v:064x}'
def addr_word(a:str)->str:return '0'*24+require_address(a)[2:].lower()
def encode_call(signature:str,*abi_words:str)->str:
    return selector(signature)+''.join(abi_words)
def decode_word(payload:str,position=0)->int:
    if not isinstance(payload,str) or not re.fullmatch(r'0x(?:[0-9a-fA-F]{2})*',payload):raise ChainError('Malformed ABI return bytes')
    b=bytes.fromhex(payload[2:]);pos=position*32
    if pos+32>len(b):raise ChainError('Truncated ABI result')
    return int.from_bytes(b[pos:pos+32],'big')
def decode_address(payload:str)->str:
    value=decode_word(payload)
    if value >= 2**160:raise ChainError('Invalid ABI address padding')
    return '0x'+f'{value:040x}'
def decode_addresses(payload:str,cap=32)->list[str]:
    off=decode_word(payload)
    b=bytes.fromhex(payload[2:])
    if off%32 or off+32>len(b):raise ChainError('Invalid ABI dynamic offset')
    n=int.from_bytes(b[off:off+32],'big')
    if n>cap or off+32+32*n>len(b):raise ChainError('Invalid or oversized address array')
    result=[]
    for i in range(n):
        val=int.from_bytes(b[off+32+i*32:off+64+i*32],'big')
        if val>=2**160:raise ChainError('Noncanonical ABI address')
        result.append('0x'+f'{val:040x}')
    return result

def decode_string(payload:str)->str|None:
    if not isinstance(payload,str) or not re.fullmatch(r'0x(?:[0-9a-fA-F]{2})*',payload):raise ChainError('Malformed ABI string bytes')
    b=bytes.fromhex(payload[2:])
    if len(b)==32: # legacy bytes32 symbol
        try:return b.rstrip(b'\x00').decode('utf8')[:100]
        except UnicodeDecodeError:return None
    if len(b)<64:return None
    offset=decode_word(payload)
    if offset%32 or offset+32>len(b):return None
    n=int.from_bytes(b[offset:offset+32],'big')
    if n>256 or offset+32+n>len(b):return None
    try:return b[offset+32:offset+32+n].decode('utf8')
    except UnicodeDecodeError:return None


def decode_dynamic_uint_array(payload:str,output_word_index:int,cap=32)->list[int]:
    offset=decode_word(payload,output_word_index)
    if offset%32:raise ChainError('Invalid ABI array offset')
    b=bytes.fromhex(payload[2:])
    if offset+32>len(b):raise ChainError('Truncated ABI array')
    n=int.from_bytes(b[offset:offset+32],'big')
    if n>cap or offset+32+n*32>len(b):raise ChainError('Oversized or truncated uint array')
    return [int.from_bytes(b[offset+32+i*32:offset+64+i*32],'big') for i in range(n)]
