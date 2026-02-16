from unittest import TestCase
from random import randint

import hashlib
import hmac

from my_helper import (encode_base58_checksum,
                       hash160,)


class FieldElement:

    def __init__(self, num, prime):
        if num >= prime or num < 0: 
            error = f'Num {num} not in field range 0 to {prime - 1}'
            raise ValueError(error)
        self.num = num 
        self.prime = prime
    
    def __repr__(self):
        return f'FieldElement_{self.prime}({self.num})'

    def __eq__(self, other):
        if other is None:
            return False
        return self.num == other.num and self.prime == other.prime
    
    def __ne__(self,other):
        return not(self == other)
    
    def __add__(self,other):
        if self.prime != other.prime:
            raise TypeError('Cannnot add two numbers in different Fields')
        num = (self.num + other.num) % self.prime
        return self.__class__(num,self.prime)
    
    def __sub__(self,other):
        if self.prime != other.prime:
                raise TypeError('Cannnot subtract two numbers in different Fields')
        num = (self.num - other.num) % self.prime
        return self.__class__(num,self.prime)
    
    def __mul__(self,other):
        if self.prime != other.prime:
            raise TypeError('Cannnot multiply two numbers in different Fields')
        num = (self.num * other.num) % self.prime
        return self.__class__(num,self.prime)
    
    def __pow__(self,exponent):
        n = exponent % (self.prime-1)
        num = pow(self.num , n , self.prime)
        return self.__class__(num,self.prime) 
    
    def __truediv__(self,other):
        if self.prime != other.prime:
            raise TypeError('Cannnot divide two numbers in different Fields')
        num = self.num * pow(other.num,self.prime-2,self.prime) % self.prime
        return self.__class__(num,self.prime)

    def __rmul__(self, coefficient):
        num = (self.num * coefficient) % self.prime
        return self.__class__(num=num, prime=self.prime)

class Point:
    
    def __init__(self,x,y,a,b):
        self.a = a
        self.b = b
        self.x = x
        self.y = y
        if self.x is None and self.y is None:
            return
        if self.y**2 != self.x**3 + a*x + b:
            raise ValueError(f'({self.x},{self.y}) is not on the curve')
        
    def __eq__(self,other):
        return self.x == other.x and self.y ==other.y \
            and self.a == other.a and self.b == other.b
            
    def __ne__(self,other):
        return not (self == other)
    
    def __repr__(self):
        if self.x is None:
            return 'Point(infinity)'
        elif isinstance(self.x, FieldElement):
            return f'Point({self.x.num},{self.y.num})_{self.a.num}_{self.b.num} FieldElement({self.x.prime})'
        else:
            return f'Point({self.x},{self.y})_{self.a}_{self.b}'
        
    def __add__(self,other):
        if self.a != other.a or self.b != other.b:
            raise TypeError(f'Points({self}と{other}) is not on the same curve')
        
        if self.x is None:
            return other
        
        if other.x is None:
            return self
        
        if self.x == other.x and self.y != other.y :
            return self.__class__(None,None,self.a,self.b)
        
        if self.x != other.x:
            s = (other.y - self.y) / (other.x - self.x)
            x = s**2 - self.x - other.x
            y = s*(self.x - x) - self.y
            return self.__class__(x,y,self.a,self.b)
        
        if self == other:
            s = (3*(self.x)**2 + self.a) / (2*self.y)
            x = s**2 - 2*self.x
            y = s*(self.x-x) - self.y
            return self.__class__(x,y,self.a,self.b)
        
        if self == other and self.y == 0 * self.x:
            return self.__class__(None,None,self.a,self.b)
        
    def __rmul__(self, coefficient):
        coef = coefficient
        current = self  
        result = self.__class__(None, None, self.a, self.b)  
        while coef:
            if coef & 1:  
                result += current
            current += current  
            coef >>= 1  
        return result

       
class ECCTest(TestCase):
    
    def test_on_curve(self):
        prime = 223
        a = FieldElement(0,prime)
        b = FieldElement(7,prime)
        valid_points = ((192,105),(17,56),(1,193))
        invalid_points = ((200,119),(42,99))
        for x_raw , y_raw in valid_points:
            x = FieldElement(x_raw,prime)
            y = FieldElement(y_raw,prime)
            Point(x,y,a,b)    
        for x_raw , y_raw in invalid_points:
            x = FieldElement(x_raw,prime)
            y = FieldElement(y_raw,prime)
            with self.assertRaises(ValueError):
                Point(x,y,a,b)
                
    def test_add(self):
        prime = 223
        a = FieldElement(0,prime)
        b = FieldElement(7,prime)
        additions = (
            (170,142,60,139,220,181),
            (47,71,17,56,215,68),
            (143,98,76,66,47,71)
        )
        for x1_raw , y1_raw , x2_raw , y2_raw , x3_raw , y3_raw in additions:
            x1 = FieldElement(x1_raw,prime)
            y1 = FieldElement(y1_raw,prime)
            p1 = Point(x1,y1,a,b)
            x2 = FieldElement(x2_raw,prime)
            y2 = FieldElement(y2_raw,prime)
            p2 = Point(x2,y2,a,b)
            x3 = FieldElement(x3_raw,prime)
            y3 = FieldElement(y3_raw,prime)
            p3 = Point(x3,y3,a,b)
        self.assertEqual(p1 + p2 , p3)    

""" 署名 """

P = 2**256 - 2**32 - 977
A = 0
B = 7
N = 0xfffffffffffffffffffffffffffffffebaaedce6af48a03bbfd25e8cd0364141

class S256Field(FieldElement):
    
    def __init__(self,num,prime=None):
        super().__init__(num=num,prime=P)
        
    def __repr__(self):
        return '{:x}'.format(self.num).zfill(64)
    
    def sqrt(self):
        return self**((P+1)//4)

    
class S256Point(Point):
    
    def __init__(self,x,y,a=None,b=None):
        a,b = S256Field(A),S256Field(B)
        if type(x) == int:
            super().__init__(x=S256Field(x), y=S256Field(y), a=a, b=b)
        else:
            super().__init__(x=x, y=y, a=a, b=b)

    def __repr__(self):
        if self.x is None:
            return 'S256Point(infinity)'
        else:
            return 'S256Point({}, {})'.format(self.x, self.y)            
           
    def __rmul__(self, coefficient):
        coef = coefficient % N
        return super().__rmul__(coef)
    
    def verify(self, z, sig):
        s_inv = pow(sig.s, N - 2, N)
        u = z * s_inv % N
        v = sig.r * s_inv % N
        total = u * G + v * self
        return total.x.num == sig.r
    
    def sec(self, compressed=True):
        # SECフォーマットをバイナリ形式にて返す
        if compressed:
            #圧縮
            if self.y.num % 2 == 0:
                return b'\x02' + self.x.num.to_bytes(32, 'big')
            else:
                return b'\x03' + self.x.num.to_bytes(32, 'big')
        else:
             #非圧縮
            return b'\x04' + self.x.num.to_bytes(32, 'big') + \
                self.y.num.to_bytes(32, 'big')
                
    def hash160(self,compressed=True):
        return hash160(self.sec(compressed))
    
    def address(self,compressed=True,testnet=False):
        # アドレスの文字列を返す 
        h160 = self.hash160(compressed)
        if testnet:
            prefix = b'\x6f'
        else:
            prefix = b'\x00'
        return encode_base58_checksum(prefix + h160)
                
    @classmethod
    def parse(self,sec_bin):
        # SECバイナリ（16進数でない）からPointオブジェクトを返す 
        if sec_bin[0] == 4:
            x = int.from_bytes(sec_bin[1:33],'big')
            y = int.from_bytes(sec_bin[33:65],'big')
            return S256Point(x=x,y=y)
        is_even = sec_bin[0] == 2
        x = S256Field(int.from_bytes(sec_bin[1:],'big'))
        # 式y^2 = x^3 + 7の右辺
        alpha = x**3 + S256Field(B)
        #左辺を解く
        beta = alpha.sqrt()
        if beta.num % 2 == 0:
            even_beta = beta
            odd_beta = S256Field(P - beta.num)
        else:
            even_beta = S256Field(P - beta.num)
            odd_beta = beta
        if is_even:
            return S256Point(x,even_beta)
        else:
            return S256Point(x,odd_beta)
    
G = S256Point(
    0x79be667ef9dcbbac55a06295ce870b07029bfcdb2dce28d959f2815b16f81798,
    0x483ada7726a3c4655da4fbfc0e1108a8fd17b448a68554199c47d08ffb10d4b8)


class Signature:
    
    def __init__(self,r,s):
        self.r = r
        self.s = s
        
    def __repr__(self):
        return 'Signature({:x},{:x})'.format(self.r,self.s)
    
    def der(self):
        
        rbin = self.r.to_bytes(32,byteorder = 'big')
        rbin = rbin.lstrip(b'\x00')
        if rbin[0] & 0x80:
            rbin = b'\x00' + rbin
        result = bytes([2,len(rbin)]) + rbin
        
        sbin = self.s.to_bytes(32,byteorder='big')
        sbin = sbin.lstrip(b'\x00')
        if sbin[0] & 0x80:
            sbin = b'\x00' + sbin
        result += bytes([2,len(sbin)]) + sbin
        
        return bytes([0x30,len(result)]) + result
    
    "補足　簡易版"
    @classmethod
    def parse(cls, der_bytes):

        if der_bytes[0] != 0x30:
            raise ValueError("Invalid DER")

        r_len = der_bytes[3]
        r = int.from_bytes(der_bytes[4:4+r_len], 'big')
        s_len = der_bytes[4+r_len+1]
        s = int.from_bytes(der_bytes[4+r_len+2:], 'big')
        return cls(r, s)
        
class PrivateKey:
    
    def __init__(self,secret):
        self.secret = secret
        self.point = secret*G #公開鍵の生成（S256Pointオブジェクト）
        
    def hex(self):
        return '{:x}'.format(self.secret).zfill(64) 
    
    #署名する
    def sign(self,z) :
        k = self.deterministic_k(z)
        r = (k*G).x.num
        k_inv = pow(k,N-2,N)
        s = (z + r*self.secret) * k_inv % N
        if s > N/2:
            s = N-s
        return Signature(r,s)
    
    #一意なｋを選ぶ
    def deterministic_k(self,z):
        k = b'\x00' * 32
        v = b'\x01' * 32
        if z > N:
            z -= N
        z_bytes = z.to_bytes(32,'big')
        secret_bytes = self.secret.to_bytes(32,'big')
        s256 = hashlib.sha256
        k = hmac.new(k,v + b'\x00' + secret_bytes + z_bytes,s256).digest()
        v = hmac.new(k,v,s256).digest()
        k = hmac.new(k,v + b'\x01' + secret_bytes + z_bytes,s256).digest()
        v = hmac.new(k,v,s256).digest()
        while True:
            v = hmac.new(k,v,s256).digest()
            candidate = int.from_bytes(v,'big')
            if candidate >= 1 and candidate < N:
                return candidate
            k = hmac.new(k,v + b'\x00',s256).digest()
            v = hmac.new(k,v,s256).digest()
            
    def wif(self,compressed=True,testnet=False):
        secret_bytes = self.secret.to_bytes(32,'big')
        if testnet:
            prefix = b'\xef'
        else:
            prefix = b'\x80'
        if compressed:
            suffix = b'\x01'
        else:
            suffix = b''
        return encode_base58_checksum(prefix + secret_bytes + suffix)

