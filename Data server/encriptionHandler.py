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
    key = hashlib.sha256(key.encode()).digest()
    return key

def AESencrypt(key, raw):
    raw = pad(raw)
    iv = Random.new().read(AES.block_size)
    chiper = AES.new(key, AES.MODE_CBC, iv)
    secret = base64.b64encode(iv + chiper.encrypt(raw))
    return secret

def AESdecrypt(key, secret):
    secret = base64.b64decode(secret)
    iv = secret[:AES.block_size]
    cipher = AES.new(key, AES.MODE_CBC, iv)
    raw = unpad(cipher.decrypt(secret[AES.block_size:])).decode('utf-8')
    return raw

def RSAencrypt(pubkey, raw):
    raw = raw.encode('UTF-8')
    secret = rsa.encrypt(message = raw, pub_key = pubkey)
    return secret

def RSAdecrypt(privkey, secret):
    try:
        raw = rsa.decrypt(crypto = secret, priv_key = privkey)
        raw = raw.decode('UTF-8')
        return raw
    except rsa.pkcs1.DecryptionError:
        return False
        
if __name__ == "__main__":
    print("Fatal error: This program have to be used as a module")
    exit()