#!/usr/bin/python3
import hashlib
import base64
try:
    import rsa
except ImportError:
    print("Fatal error: Missing RSA module")
    exit()
try:
    
    from Crypto.Cipher import AES
    from Crypto import Random
except ImportError:
    print("Fatal error: Missing Crypto module")
    exit()


# AES protocol costants
BLOCK_SIZE = 32
pad = lambda s: s + (BLOCK_SIZE - len(s) % BLOCK_SIZE) * chr(BLOCK_SIZE - len(s) % BLOCK_SIZE)
unpad = lambda s: s[:-ord(s[len(s) - 1:])]

def generateRSA():
    (pubkey, privkey) = rsa.newkeys(512)
    return (pubkey, privkey)

def generateAES():
    key = hashlib.sha256(rsa.randnum.read_random_bits(128)).digest()
    return key

def AESencrypt(key, raw, byteObject = False):
    try:
        if byteObject == False:
            raw = pad(raw)
        else:
            raw = raw.decode()
            raw = pad(raw)
            raw = raw.encode()
        iv = Random.new().read(AES.block_size)
        chiper = AES.new(key, AES.MODE_CBC, iv)
        secret = base64.b64encode(iv + chiper.encrypt(raw))
    except Exception:
        secret = None

    return secret

def AESdecrypt(key, secret, byteObject = False):
    try:
        secret = base64.b64decode(secret)
        iv = secret[:AES.block_size]
        cipher = AES.new(key, AES.MODE_CBC, iv)
        raw = cipher.decrypt(secret[AES.block_size:])
        if byteObject == False:
            raw = unpad(raw)
            raw = raw.decode()
        else:
            raw = raw.decode()
            raw = unpad(raw)
            raw = raw.encode()
    except Exception:
        raw = None

    return raw

def RSAencrypt(pubkey, raw):
    try:
        if type(raw) is not bytes:
            raw = raw.encode('UTF-8')
        secret = rsa.encrypt(message = raw, pub_key = pubkey)
    except Exception:
        secret = None
        
    return secret

def RSAdecrypt(privkey, secret, skipDecoding = False):
    try:
        raw = rsa.decrypt(crypto = secret, priv_key = privkey)
        if skipDecoding == False:
            raw = raw.decode('UTF-8')
        return raw
    except rsa.pkcs1.DecryptionError:
        return False

def exportRSApub(pubkey):
    return pubkey.save_pkcs1(format = "PEM")

def importRSApub(PEMfile):
    return rsa.PublicKey.load_pkcs1(keyfile = PEMfile, format = "PEM")
        
if __name__ == "__main__":
    print("Fatal error: This program have to be used as a module")
    exit()