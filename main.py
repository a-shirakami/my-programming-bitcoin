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

prev_tx_hex = ""
stream = BytesIO(bytes.fromhex(prev_tx_hex))
prev_tx = Tx.parse(stream)
prev_tx_id = bytes.fromhex(prev_tx.id())
prev_index = 0
tx_ins = []
tx_ins.append(TxIn(prev_tx=prev_tx_id, prev_index=prev_index, script_sig=None, 
                   sequence=0xffffffff, witness=None))

target_address = "tb1q24v08fgsknnyt2qj53qkzmphnxp2aafdq6xd7w"
target_amount = ""
target_pubkey_hash = segwit_decode(target_address)[2]
target_script_pubkey = p2wpkh_script(target_pubkey_hash)

change_address = my_address
change_amount = ""
change_script_pubkey = p2wpkh_script(my_pubkey_hash)

tx_outs = []
tx_outs.append(TxOut(amount=target_amount, script_pubkey=target_script_pubkey))
tx_outs.append(TxOut(amount=change_amount, script_pubkey=change_script_pubkey))

tx_obj = Tx(version=2, tx_ins=tx_ins, tx_outs=tx_outs, 
            locktime=0, testnet=True, segwit=True)
z = tx_obj.sig_hash_bip143(0, redeem_script=None, witness_script=None)
sig = private_key.sign(z).der() + SIGHASH_ALL.to_bytes(1, 'big')
tx_obj.tx_ins[0].witness = [sig, compressed_pubkey]

print(tx_obj.verify_input(0))
print(f'tx fee : {tx_obj.tx_outs[0]-tx_obj.tx_outs[1]}')

print(tx_obj.serialize().hex())