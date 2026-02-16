# =============================================================
# SegWit Address Encode / Decode (Bech32 + Bech32m)
# hrp = 'tb' / witver=0 / witprog=<20byte-hash>
# =============================================================

CHARSET = "qpzry9x8gf2tvdw0s3jn54khce6mua7l"

# -------------------- Bech32 基本関数 ------------------------

def bech32_polymod(values):
    GENERATOR = [0x3b6a57b2, 0x26508e6d, 0x1ea119fa, 0x3d4233dd, 0x2a1462b3]
    chk = 1
    for v in values:
        b = (chk >> 25)
        chk = ((chk & 0x1ffffff) << 5) ^ v
        for i in range(5):
            if (b >> i) & 1:
                chk ^= GENERATOR[i]
    return chk

def bech32_hrp_expand(hrp):
    return [ord(x) >> 5 for x in hrp] + [0] + [ord(x) & 31 for x in hrp]

def bech32_create_checksum(hrp, data):
    values = bech32_hrp_expand(hrp) + data + [0]*6
    polymod = bech32_polymod(values) ^ 1
    return [(polymod >> 5*(5-i)) & 31 for i in range(6)]

def bech32m_create_checksum(hrp, data):
    values = bech32_hrp_expand(hrp) + data + [0]*6
    polymod = bech32_polymod(values) ^ 0x2bc830a3
    return [(polymod >> 5*(5-i)) & 31 for i in range(6)]

def bech32_verify_checksum(hrp, data):
    check = bech32_polymod(bech32_hrp_expand(hrp) + data)
    if check == 1:
        return "BECH32"
    if check == 0x2bc830a3:
        return "BECH32M"
    return None

def bech32_encode(hrp, data):
    combined = data + bech32_create_checksum(hrp, data)
    return hrp + '1' + ''.join([CHARSET[d] for d in combined])

def bech32m_encode(hrp, data):
    combined = data + bech32m_create_checksum(hrp, data)
    return hrp + '1' + ''.join([CHARSET[d] for d in combined])

def convertbits(data, frombits, tobits, pad=True):
    acc = 0
    bits = 0
    ret = []
    maxv = (1 << tobits) - 1
    for value in data:
        if value < 0 or value >> frombits:
            return None
        acc = (acc << frombits) | value
        bits += frombits
        while bits >= tobits:
            bits -= tobits
            ret.append((acc >> bits) & maxv)
    if pad and bits:
        ret.append((acc << (tobits - bits)) & maxv)
    if not pad and bits >= frombits:
        return None
    return ret

def segwit_encode(hrp, witver, witprog):
    if not (0 <= witver <= 16):
        raise ValueError("Invalid witness version")
    if not (2 <= len(witprog) <= 40):
        raise ValueError("Invalid witness program length")
    data = [witver] + convertbits(list(witprog), 8, 5)
    if witver == 0:
        return bech32_encode(hrp, data)
    else:
        return bech32m_encode(hrp, data)

def segwit_decode(addr):
    if (addr.lower() != addr and addr.upper() != addr) :
        raise ValueError("Mixed case")
    addr = addr.lower()
    pos = addr.rfind('1')
    if pos == -1:
        raise ValueError("No separator '1' found")
    hrp = addr[:pos]
    data_part = addr[pos+1:]
    if len(data_part) < 6:
        raise ValueError("Data part too short")
    data = []
    for ch in data_part:
        if ch not in CHARSET:
            raise ValueError("Invalid character in data part")
        data.append(CHARSET.index(ch))
    checksum_type = bech32_verify_checksum(hrp, data)
    if checksum_type is None:
        raise ValueError("Invalid checksum")
    payload = data[:-6]
    if len(payload) == 0:
        raise ValueError("No witness payload")
    witver = payload[0]
    witprog_5 = payload[1:]
    witprog_bytes = bytes(convertbits(witprog_5, 5, 8, False))
    if witprog_bytes is None:
        raise ValueError("convertbits failed")
    if not (2 <= len(witprog_bytes) <= 40):
        raise ValueError("Invalid witness program length after conversion")
    if witver == 0 and checksum_type != "BECH32":
        raise ValueError("v0 must use BECH32 checksum")
    if witver > 0 and checksum_type != "BECH32M":
        raise ValueError("v1+ must use BECH32M checksum")
    return hrp, witver, witprog_bytes

def scriptpubkey_from_witness(witver, witprog):
    if not (0 <= witver <= 16):
        raise ValueError("invalid witness version")
    if not isinstance(witprog, (bytes, bytearray)):
        raise TypeError("witprog must be bytes")
    l = len(witprog)
    if not (2 <= l <= 40):
        raise ValueError("invalid witness program length")
    if witver == 0:
        ver_byte = bytes([0x00])
    else:
        ver_byte = bytes([0x50 + witver])  # OP_1..OP_16 mapping
    if l <= 75:
        pushlen = bytes([l])
    elif l < 0x100:
        pushlen = bytes([76, l])
    else:
        pushlen = bytes([77]) + l.to_bytes(2, 'little')
    return ver_byte + pushlen + witprog


