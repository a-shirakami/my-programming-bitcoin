from io import BytesIO
from src.my_helper import hash160, SIGHASH_ALL, int_to_little_endian
from src.my_ecc import PrivateKey
from src.my_script import Script, p2wpkh_script
from src.my_tx import Tx, TxIn, TxOut
from src.bech32 import segwit_encode, segwit_decode
from secret import SECRET

secret = SECRET
private_key = PrivateKey(secret)
public_key = private_key.point
compressed_pubkey = public_key.sec(compressed=True)
my_pubkey_hash = hash160(compressed_pubkey)
my_address = segwit_encode("tb", 0, my_pubkey_hash)
print(my_address)
