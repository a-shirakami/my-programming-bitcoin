from src.bech32 import segwit_encode, segwit_decode
from src.my_ecc import PrivateKey, Signature
from src.my_script import Script, p2wpkh_script
from src.my_tx import Tx, TxIn, TxOut
from src.my_helper import hash160, decode_base58, SIGHASH_ALL
from secret import TX_20260217
from io import BytesIO

secret = 20041129
private_key = PrivateKey(secret)
public_key = private_key.point
compressed_pubkey = public_key.sec(compressed=True)
my_pubkey_hash = hash160(compressed_pubkey)
my_address = segwit_encode("tb", 0, my_pubkey_hash)

prev_tx_hex = TX_20260217
stream = BytesIO(bytes.fromhex(prev_tx_hex))
prev_tx = Tx.parse(stream)
prev_tx_id = bytes.fromhex(prev_tx.id())
# input number
prev_index = 0
tx_ins = []
tx_ins.append(TxIn(prev_tx_id, prev_index, script_sig=None, witness=None))

# target address
target_address = 'tb1q7zfvf2zpaxueqf4zdtyusrlkkmvmscpm0n8ad3'
target_amount = 1000000
target_pubkey_hash = segwit_decode(target_address)[2]
target_script_pubkey = p2wpkh_script(target_pubkey_hash)

fee = 1000
# change address
change_address = my_address
change_amount = prev_tx.tx_outs[prev_index].amount - target_amount - fee
change_script_pubkey = p2wpkh_script(my_pubkey_hash)

tx_outs = []
tx_outs.append(TxOut(target_amount, target_script_pubkey))
tx_outs.append(TxOut(change_amount, change_script_pubkey))

tx_obj = Tx(2, tx_ins, tx_outs, locktime=0, testnet=True, segwit=True)
# input index
z = tx_obj.sig_hash_bip143(0, redeem_script=None, witness_script=None)
sig = private_key.sign(z).der() + SIGHASH_ALL.to_bytes(1, 'big')
# input index
tx_obj.tx_ins[0].witness = [sig, compressed_pubkey]

# check verify input
print(tx_obj.verify_input(0))
# check tx fee
print(f'fee : {tx_obj.fee(testnet=True)}')

my_tx_hex = tx_obj.serialize().hex()
print(my_tx_hex)