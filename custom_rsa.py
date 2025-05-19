import random
import math
import base64

# Helper function to check if a number is prime using Miller-Rabin test
def is_prime(n, k=5):
    if n <= 1:
        return False
    if n <= 3:
        return True
    for _ in range(k):
        a = random.randint(2, n - 1)
        if pow(a, n - 1, n) != 1:
            return False
    return True

# Generate a prime number of specified bit length
def generate_prime(bits):
    while True:
        p = random.getrandbits(bits)
        if is_prime(p):
            return p

# Generate RSA key pair (public and private keys)
def generate_keys(bits=1024):
    p = generate_prime(bits // 2)
    q = generate_prime(bits // 2)
    n = p * q
    phi = (p - 1) * (q - 1)
    e = 65537  # Common public exponent
    while math.gcd(e, phi) != 1:
        e = random.randint(2, phi - 1)
    d = pow(e, -1, phi)  # Modular multiplicative inverse
    return (n, e), (n, d)  # (public_key), (private_key)

# Encrypt a message using the public key
def encrypt(message, public_key):
    n, e = public_key
    m = int.from_bytes(message.encode(), 'big')
    c = pow(m, e, n)
    return c.to_bytes((c.bit_length() + 7) // 8, 'big')

# Decrypt a ciphertext using the private key
def decrypt(ciphertext, private_key):
    n, d = private_key
    c = int.from_bytes(ciphertext, 'big')
    m = pow(c, d, n)
    m_bytes = m.to_bytes((m.bit_length() + 7) // 8, 'big')
    return m_bytes.decode()

# Serialize a key to a PEM-like format
def save_pkcs1(key, key_type):
    if key_type == 'public':
        n, e = key
        key_str = f"RSA PUBLIC KEY\nn={n}\ne={e}"
    elif key_type == 'private':
        n, d = key
        key_str = f"RSA PRIVATE KEY\nn={n}\nd={d}"
    else:
        raise ValueError("Invalid key type")
    return base64.b64encode(key_str.encode()).decode()

# Deserialize a key from a PEM-like format
def load_pkcs1(pem_data, key_type):
    key_str = base64.b64decode(pem_data).decode()
    lines = key_str.split('\n')
    if lines[0] != f"RSA {key_type.upper()} KEY":
        raise ValueError("Invalid key format")
    n = int(lines[1].split('=')[1])
    if key_type == 'public':
        e = int(lines[2].split('=')[1])
        return (n, e)
    elif key_type == 'private':
        d = int(lines[2].split('=')[1])
        return (n, d)
    else:
        raise ValueError("Invalid key type")
