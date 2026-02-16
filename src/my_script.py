from my_op import (OP_CODE_FUNCTIONS,
                   OP_CODE_NAMES,
                   op_hash160,
                   op_equal,
                   op_verify
                   )
from io import BytesIO

from my_helper import hash160, sha256

import hashlib
import hmac
import requests

import logging
LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.INFO)
LOGGER.addHandler(logging.StreamHandler())

from my_helper import (little_endian_to_int,
                       read_varint,
                       int_to_little_endian,
                       encode_varint)
       
        
class Script:
    
    def __init__(self,cmds=None):
        if cmds is None:
            self.cmds = []
        else:
            self.cmds = cmds

    def __repr__(self):
        result = []
        for cmd in self.cmds:
            if isinstance(cmd, int):
                name = OP_CODE_NAMES.get(cmd, f'OP_[{cmd}]')
                result.append(name)
            else:
                result.append(cmd.hex())
        return ' '.join(result)
    
    def __add__(self, other):
        return Script(self.cmds + other.cmds)
            
    @classmethod
    def parse(cls,s):
        
        length = read_varint(s)
        # script
        cmds = []
        count = 0
        
        while count < length:
            current = s.read(1)
            count += 1
            current_byte = current[0]
        
            if current_byte >= 1 and current_byte <= 75:
                n = current_byte
                cmds.append(s.read(n))
                count += n
        
            elif current_byte == 76:
                data_lenght = little_endian_to_int(s.read(1))
                cmds.append(s.read(data_lenght))
                count += data_lenght + 1
        
            elif current_byte == 77:
                data_lenght = little_endian_to_int(s.read(2))
                cmds.append(s.read(data_lenght))
                count += data_lenght + 2
        
            else:
                op_code = current_byte
                cmds.append(op_code)
        
        if count != length:
            raise SyntaxError('parsing script faild')
        return cls(cmds)
           
    def raw_serialize(self):
        result = b''
        for cmd in self.cmds:
            if type(cmd) == int:
                result += int_to_little_endian(cmd,1)
            else:
                length = len(cmd)
                if length <= 75:
                    result += int_to_little_endian(length,1)
                elif length > 75 and length < 0x100:
                    result += int_to_little_endian(76,1)
                    result += int_to_little_endian(length,1)
                elif length >= 0x100 and length <= 520:
                    result += int_to_little_endian(77,1)
                    result += int_to_little_endian(length,2)
                else:
                    raise ValueError('too long an cmd')
                result += cmd
        return result
    
    def serialize(self):
        result = self.raw_serialize()
        total = len(result)
        return encode_varint(total) + result
    
    def evaluate(self, z, witness):
        cmds = self.cmds[:]
        stack = []
        alstack = []
        while len(cmds) > 0:
            cmd = cmds.pop(0)
            if type(cmd) == int:
                operation = OP_CODE_FUNCTIONS[cmd]
                if cmd in (99,100):
                    if not operation(stack,cmds):
                        LOGGER.info(f'bad op:{OP_CODE_NAMES[cmd]}')
                        return False
                elif cmd in (107,108):
                    if not operation(stack,alstack):
                        LOGGER.info(f'bad op:{OP_CODE_NAMES[cmd]}')
                        return False
                elif cmd in (172,173,174,175):
                    if not operation(stack,z):
                        LOGGER.info(f'bad op:{OP_CODE_NAMES[cmd]}')
                        return False    
                else:
                    if not operation(stack):
                        LOGGER.info(f'bad op:{OP_CODE_NAMES[cmd]}')
                        return False
            else:
                stack.append(cmd)
                if len(cmds) == 3 and cmds[0] == 0xa9\
                    and type(cmds[1]) == bytes and len(cmds[1]) == 20\
                    and cmds[2] == 0x87:
                    redeem_script = encode_varint(len(cmd)) + cmd   
                    cmds.pop()
                    h160 = cmds.pop()
                    cmds.pop()
                    if not op_hash160(stack):
                        return False
                    stack.append(h160)
                    if not op_equal(stack):
                        return False
                    if not op_verify(stack):
                        LOGGER.info('bad p2sh h160')
                        return False
                    redeem_script = encode_varint(len(cmd)) + cmd
                    stream = BytesIO(redeem_script)
                    cmds.extend(Script.parse(stream).cmds)
                if len(stack) == 2 and stack[0] == b'' and  len(stack[1]) == 20:
                    h160 = stack.pop()
                    stack.pop()
                    cmds.extend(witness)
                    cmds.extend(p2pkh_script(h160).cmds)
                if len(stack) == 2 and stack[0] == b'' and len(stack[1]) == 32:
                    s256 = stack.pop()
                    stack.pop()
                    cmds.extend(witness[:-1])
                    witness_script = witness[-1]
                    if s256 != sha256(witness_script):
                        print(f'bad sha256 {s256.hex()} vs {sha256(witness_script).hex()}')
                        return False
                    stream = BytesIO(encode_varint(len(witness_script))+witness_script)
                    witness_script_cmds = Script.parse(stream).cmds
                    cmds.extend(witness_script_cmds)            
        if len(stack) == 0:
            return False
        if stack[0] != b'\x01':
            return False
        if stack.pop() == b'':
            return False
        return True

            
    def is_p2pkh_script_pubkey(self):
        return len(self.cmds) == 5 and self.cmds[0] == 0x76 \
            and self.cmds[1] == 0xa9 \
            and type(self.cmds[2]) == bytes and len(self.cmds[2]) == 20 \
            and self.cmds[3] == 0x88 and self.cmds[4] == 0xac

    def is_p2sh_script_pubkey(self):
        return len(self.cmds) == 3 and self.cmds[0] == 0xa9 \
            and type(self.cmds[1]) == bytes and len(self.cmds[1]) == 20 \
            and self.cmds[2] == 0x87
            
    def is_p2wpkh_script_pubkey(self):
        return len(self.cmds) == 2 and self.cmds[0] == 0x00 \
            and type(self.cmds[1]) == bytes and len(self.cmds[1]) == 20
            
    def is_p2wsh_script_pubkey(self):
        return len(self.cmds) == 2 and self.cmds[0] == 0x00 \
            and type(self.cmds[1]) == bytes and len(self.cmds[1]) == 32
 

def p2pkh_script(h160):
    return Script([0x76,0xa9,h160,0x88,0xac])

def p2sh_script(h160):
    return Script([0xa9, h160, 0x87])
        
def p2wpkh_script(h160):
    return Script([0x00, h160])

def p2wsh_script(h256):
    return Script([0x00, h256])
        
