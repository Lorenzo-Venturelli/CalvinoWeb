import hashlib
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

class rsaHandler():
    def __init__(self):
        (self.pubkey, self.privkey) = rsa.newkeys(512)

if __name__ == "__main__":
    print("Fatal error: This program have to be used as a module")
    exit()