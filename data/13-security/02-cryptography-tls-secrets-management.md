# Cryptography, TLS, and Secrets Management: Deep Dive



```mermaid
graph LR
    CRYPTO["Cryptography"] --> SYM_CRYPTO["Symmetric<br/>(same key)"]
    SYM_CRYPTO --> AES_GCM["AES-256-GCM<br/>(AEAD)"]
    SYM_CRYPTO --> CHACHA["ChaCha20-Poly1305<br/>(AEAD)"]
    CRYPTO --> ASYM_CRYPTO["Asymmetric<br/>(key pair)"]
    ASYM_CRYPTO --> RSA_R["RSA<br/>(key exchange/sign)"]
    ASYM_CRYPTO --> ECDSA_R["ECDSA / Ed25519<br/>(signatures)"]
    ASYM_CRYPTO --> ECDHE_R["ECDHE<br/>(key agreement)"]
    CRYPTO --> HASH_R["Hash Functions"]
    HASH_R --> SHA256["SHA-256<br/>(digest)"]
    HASH_R --> HMAC["HMAC<br/>(authenticated)"]
    TLS_13["TLS 1.3"] --> HAND_SHAKE["Handshake<br/>(1-RTT)"]
    TLS_13 --> PSK_R["0-RTT Resumption<br/>(PSK)"]
    HAND_SHAKE --> KEY_SCHED["Key Schedule<br/>(HKDF)"]
    KEY_SCHED --> APP_SEC["Application Data<br/>(AEAD encrypted)"]
    SECRETS["Secrets Mgmt"] --> VAULT["HashiCorp Vault<br/>(dynamic secrets)"]
    SECRETS --> HSM["HSM<br/>(hardware-backed)"]
    SECRETS --> ROTATE["Auto-Rotation<br/>(key lifecycle)"]
    style CRYPTO fill:#4a8bc2
    style SYM_CRYPTO fill:#2d5a7b
    style AES_GCM fill:#3fb950
    style CHACHA fill:#3a7ca5
    style ASYM_CRYPTO fill:#6f42c1
    style RSA_R fill:#e8912e
    style ECDSA_R fill:#3fb950
    style ECDHE_R fill:#3a7ca5
    style HASH_R fill:#c73e1d
    style SHA256 fill:#e8912e
    style HMAC fill:#3a7ca5
    style TLS_13 fill:#3fb950
    style HAND_SHAKE fill:#2d5a7b
    style PSK_R fill:#e8912e
    style KEY_SCHED fill:#c73e1d
    style APP_SEC fill:#3fb950
    style SECRETS fill:#e8912e
    style VAULT fill:#6f42c1
    style HSM fill:#c73e1d
    style ROTATE fill:#3fb950
```

## Table of Contents

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.

1. [Introduction](#introduction)
2. [Noob Explanation](#noob-explanation)
3. [Symmetric Cryptography](#symmetric-cryptography)
4. [Asymmetric Cryptography](#asymmetric-cryptography)
5. [Hash Functions](#hash-functions)
6. [TLS 1.3 Protocol](#tls-13-protocol)
7. [Certificate Management](#certificate-management)
8. [Key Management](#key-management)
9. [Secrets Management at Scale](#secrets-management-at-scale)
10. [Failure Analysis](#failure-analysis)
11. [Edge Cases](#edge-cases)
12. [Interview Questions](#interview-questions)
13. [Production Code Examples](#production-code-examples)
14. [Incident Stories](#incident-stories)

---

## Introduction

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


Cryptography is the art and science of keeping data secret. It's used everywhere:
- HTTPS/TLS: encrypting web traffic
- Databases: encrypting sensitive columns
- File systems: encrypting at rest
- Messaging apps: end-to-end encryption
- Digital signatures: proving authenticity

This guide covers the math you need to understand, the protocols you use daily, and the failures that happen in production.

---

## Noob Explanation

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


### Encryption: Putting Messages in Locked Boxes

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


Imagine you want to send a secret message to a friend:

**Bad way:**
```
You write: "I love Alice"
You send plaintext over email
Attacker reads email: "I love Alice"
Secret exposed.
```

**Good way:**
```
You write: "I love Alice"
You put in lockbox, lock with key
Only person with matching key can open
You send locked box (doesn't matter if intercepted)
Friend receives, opens with key
Only friend reads: "I love Alice"

Attacker intercepts locked box:
- Cannot open without key
- Cannot read message
```

**Two types of locks:**

**Symmetric (shared key):**
```
You and friend share one key in advance
Same key locks and unlocks
Like a padlock where one key fits all
```

**Asymmetric (public-private key):**
```
Friend has two keys: public key (anyone can have) and private key (only friend has)

You lock box with friend's public key
Anyone can lock boxes with public key
Only friend (with private key) can unlock

Like: anyone can put mail in public mailbox
Only owner (with key) can retrieve mail
```

### Perfect Passwords vs Hashes

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


**What's the difference?**

**Password (plaintext):**
```
You: "My password is SuperSecret123"
Server: Stores "SuperSecret123"
Attacker: Sees plaintext, logs in as you
DANGER: Server hack = passwords exposed
```

**Hashed password:**
```
You: "My password is SuperSecret123"
Server: Hashes it: bcrypt("SuperSecret123") = $2b$12$abcdef...
Server: Stores $2b$12$abcdef... (just hash, can't reverse)
Attacker: Sees $2b$12$abcdef... (useless without knowing password)
SAFE: Even if server hacked, password not exposed
```

**Hash properties:**
- One-way: cannot reverse (hash → password)
- Deterministic: same input = same output
- Avalanche effect: tiny input change = completely different output

```
MD5("password") = 5f4dcc3b5aa765d61d8327deb882cf99
MD5("passwor")  = 6fd1e25b7f3fbf45f48a1c8ce70fad8f
One character difference, completely different hash!
```

### Digital Signatures: Proving You Wrote It

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


**Problem:** Attacker impersonates you

```
Attacker: "I am Alice, transfer $1000 to my account"
Bank: "How do I know you're really Alice?"
Attacker: "Trust me"
Bank: "Sorry, not good enough"
```

**Solution: Digital signature**

```
Alice has private key (secret, only she has)
Alice signs message: "Transfer $1000" + sign(private_key)
Bank verifies: verify_signature(public_key) = authentic

Attacker cannot forge signature without private key
```

### TLS Handshake: Establishing Trust

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


**The problem:** You want to buy on Amazon, need encrypted connection

```
You (browser) ← Attacker (MITM) → Amazon (server)

Attacker intercepts:
1. Browser sends data to server
2. Attacker reads it
3. Attacker passes it to server
4. Same thing in reverse
Result: Your passwords, credit card exposed
```

**Solution: TLS handshake**

```
Browser → Amazon: "Hi, I want to talk securely"
           ↓
Amazon → Browser: "Here's my certificate (proves I'm Amazon)"
           ↓
Browser: "Verify certificate"
         - Check signature (trusted CA signed it)
         - Check domain name (certificate is for amazon.com, not attacker.com)
         - Check expiration (certificate not expired)
           ↓
         "This is really Amazon!"
           ↓
Browser → Amazon: Exchange encryption keys
           ↓
           All data is now encrypted
           
Attacker intercepts encrypted data:
- Cannot read without encryption key
- Cannot forge certificate (don't have Amazon's private key)
- Attack prevented
```

---

## Symmetric Cryptography

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


### AES (Advanced Encryption Standard)

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


**What it does:**
- Encrypts plaintext into ciphertext
- Decrypts ciphertext back to plaintext
- Both sender and receiver need same key

**How it works (simplified):**

AES-256 means:
- 256-bit key (32 bytes, very large key space)
- Operates on 128-bit blocks
- 14 rounds of substitution, permutation, XOR operations

**Modes of operation:**

**ECB (Electronic CodeBook) - DON'T USE:**
```
Plaintext:  [Block 1] [Block 2] [Block 3]
Encrypted:  [Enc 1]   [Enc 2]   [Enc 3]

Problem: Same plaintext block → same ciphertext block
Patterns visible in encrypted data!

Example:
Encrypting image of "HELLO":
- H appears 5 times
- All 5 encrypted H's are identical
- Attacker can guess patterns
```

**CBC (Cipher Block Chaining) - OKAY:**
```
IV = random initialization vector
Block 0 = plaintext[0] XOR IV
Encrypt(Block 0) → ciphertext[0]

Block 1 = plaintext[1] XOR ciphertext[0]
Encrypt(Block 1) → ciphertext[1]

Block 2 = plaintext[2] XOR ciphertext[1]
Encrypt(Block 2) → ciphertext[2]

Result: Same plaintext blocks produce different ciphertext
(because they're XOR'd with different previous blocks)

But: Not authenticated (attacker can modify without detection)
```

**GCM (Galois/Counter Mode) - BEST:**
```
Encrypts like CTR mode (fast, parallelizable)
Also computes authentication tag (GHASH)
Tag proves data wasn't modified

Both encryption and authentication in one operation
Fast + Secure + Authenticated
```

**Code example:**

```python
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import os

def encrypt_aes_gcm(plaintext: bytes, key: bytes) -> bytes:
    """Encrypt with AES-256-GCM"""
    
    # Generate random 96-bit nonce
    nonce = os.urandom(12)
    
    # Create cipher
    cipher = Cipher(
        algorithms.AES(key),
        modes.GCM(nonce),
        backend=default_backend()
    )
    
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(plaintext) + encryptor.finalize()
    
    # Return nonce + ciphertext + tag
    # (nonce needs to be sent with ciphertext, it doesn't need to be secret)
    return nonce + ciphertext + encryptor.tag

def decrypt_aes_gcm(encrypted_data: bytes, key: bytes) -> bytes:
    """Decrypt AES-256-GCM"""
    
    nonce = encrypted_data[:12]
    tag = encrypted_data[-16:]
    ciphertext = encrypted_data[12:-16]
    
    cipher = Cipher(
        algorithms.AES(key),
        modes.GCM(nonce, tag),
        backend=default_backend()
    )
    
    decryptor = cipher.decryptor()
    plaintext = decryptor.update(ciphertext) + decryptor.finalize()
    
    return plaintext

# Usage:
key = os.urandom(32)  # 256-bit key
plaintext = b"Secret message"
encrypted = encrypt_aes_gcm(plaintext, key)
decrypted = decrypt_aes_gcm(encrypted, key)
assert decrypted == plaintext
```

### ChaCha20-Poly1305

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


**Why it exists:**
- AES requires special hardware (AES-NI instruction) for good performance
- ChaCha20 is fast even on phones, IoT devices
- Poly1305 is very fast authentication

**Better than AES-GCM on some hardware:**
```
AES-GCM: 3 GB/s (with AES-NI)
ChaCha20-Poly1305: 2 GB/s (without special hardware)

On phone without AES-NI:
AES-GCM: 100 MB/s
ChaCha20-Poly1305: 500 MB/s
```

**Code:**

```python
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
import os

def encrypt_chacha(plaintext: bytes, key: bytes) -> bytes:
    nonce = os.urandom(12)
    cipher = ChaCha20Poly1305(key)
    ciphertext = cipher.encrypt(nonce, plaintext, None)
    return nonce + ciphertext

def decrypt_chacha(encrypted_data: bytes, key: bytes) -> bytes:
    nonce = encrypted_data[:12]
    ciphertext = encrypted_data[12:]
    cipher = ChaCha20Poly1305(key)
    return cipher.decrypt(nonce, ciphertext, None)
```

---

## Asymmetric Cryptography

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


### RSA (Rivest-Shamir-Adleman)

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


**How it works:**

```
Key generation:
1. Choose two large primes: p=61, q=53
2. Compute n = p*q = 3233
3. Compute φ(n) = (p-1)(q-1) = 2080
4. Choose e (usually 65537): gcd(e, φ(n)) = 1
5. Compute d such that: d*e ≡ 1 (mod φ(n))

Public key: (n=3233, e=65537)
Private key: (n=3233, d=...)

Encryption:
ciphertext = plaintext^e mod n

Decryption:
plaintext = ciphertext^d mod n

Why it works:
(plaintext^e)^d ≡ plaintext^(e*d) ≡ plaintext^(1 + k*φ(n)) ≡ plaintext (mod n)
```

**In practice:**

```python
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend

# Generate keypair
private_key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048,  # 2048-bit key (129 decimal digits)
    backend=default_backend()
)
public_key = private_key.public_key()

# Encrypt
plaintext = b"Secret message"
ciphertext = public_key.encrypt(
    plaintext,
    padding.OAEP(
        mgf=padding.MGF1(algorithm=hashes.SHA256()),
        algorithm=hashes.SHA256(),
        label=None
    )
)

# Decrypt
decrypted = private_key.decrypt(
    ciphertext,
    padding.OAEP(
        mgf=padding.MGF1(algorithm=hashes.SHA256()),
        algorithm=hashes.SHA256(),
        label=None
    )
)

assert decrypted == plaintext
```

**Limitations:**
- Slow: 100-1000x slower than symmetric encryption
- Can only encrypt small messages (smaller than key size)
- Used for key exchange, not bulk encryption

**Why not encrypt all traffic with RSA?**
```
RSA with 2048-bit key:
- Encrypts max 190 bytes
- Takes ~1ms per encryption
- Slow!

Use case:
1. Use RSA to securely exchange AES key
2. Use AES to encrypt actual data (fast)
```

### ECDSA (Elliptic Curve Digital Signature Algorithm)

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


**Digital signatures without revealing private key:**

```
Sign message:
1. Hash message: hash = SHA256(message)
2. Sign hash with private key: signature = sign(hash, private_key)
3. Send: (message, signature)

Verify signature:
1. Hash message: hash = SHA256(message)
2. Verify with public key: valid = verify(signature, hash, public_key)
3. If valid: message definitely came from private key owner
```

**Code:**

```python
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes

# Generate keypair
private_key = ec.generate_private_key(ec.SECP256R1())
public_key = private_key.public_key()

# Sign
message = b"I authorize this transaction"
signature = private_key.sign(
    message,
    ec.ECDSA(hashes.SHA256())
)

# Verify
try:
    public_key.verify(
        signature,
        message,
        ec.ECDSA(hashes.SHA256())
    )
    print("Signature is valid")
except:
    print("Signature is invalid")
```

**Why use ECDSA instead of RSA?**
- Smaller keys: 256-bit ECDSA ≈ 2048-bit RSA (in security)
- Faster: ~10x faster than RSA
- Modern standard (used in Bitcoin, TLS 1.3)

---

## Hash Functions

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


### SHA-256

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


**Properties:**
- One-way: cannot reverse
- Collision-resistant: two different inputs won't produce same hash
- Avalanche effect: small change = completely different hash
- Fast to compute
- Produces 256-bit (32 byte) output

**NOT suitable for passwords** (too fast, use bcrypt instead)

**Code:**

```python
import hashlib

def hash_data(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

# Usage:
hash1 = hash_data(b"hello")
# 2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824

hash2 = hash_data(b"hello2")
# 108f07b8382412612c048d07d13f814118445acd
(completely different!)
```

### HMAC (Hash-based Message Authentication Code)

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


**What it does:**
- Proves data hasn't been modified
- Only person with secret key can create valid HMAC
- Like digital signature but faster

**How it works:**

```
HMAC-SHA256(key, message):
1. inner_key = key XOR 0x363636...
2. outer_key = key XOR 0x5c5c5c...
3. inner = SHA256(inner_key + message)
4. outer = SHA256(outer_key + inner)
5. return outer

Result: 32 bytes that prove:
- Data integrity (unchanged)
- Authentication (only key holder can create)
```

**Code:**

```python
import hmac
import hashlib

def create_hmac(secret_key: bytes, message: bytes) -> str:
    return hmac.new(secret_key, message, hashlib.sha256).hexdigest()

def verify_hmac(secret_key: bytes, message: bytes, expected_hmac: str) -> bool:
    computed_hmac = create_hmac(secret_key, message)
    # Use constant-time comparison to prevent timing attacks
    return hmac.compare_digest(computed_hmac, expected_hmac)

# Usage:
key = b"secret-key"
message = b"Important message"
signature = create_hmac(key, message)

# Send message + signature
# Recipient verifies:
if verify_hmac(key, message, signature):
    print("Message is authentic and unmodified")
```

**When to use:**
- Session cookies: HMAC(session_data) proves cookie hasn't been modified
- API requests: HMAC(request_body) proves request from authenticated client
- Webhook signatures: GitHub sends HMAC(payload), you verify authenticity

---

## TLS 1.3 Protocol

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


### Handshake Flow

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


```
CLIENT                                           SERVER

ClientHello
├─ supported_cipher_suites: [TLS_AES_256_GCM_SHA384, ...]
├─ supported_versions: [1.3, 1.2]
├─ key_share: {curve: secp256r1, public_key: ...}
├─ supported_groups: [secp256r1, x25519, ...]
└─ signature_algorithms: [ECDSA_SHA256, RSA_PSS_SHA256, ...]
     │
     ▼
                                        ServerHello
                                        ├─ supported_cipher_suites: TLS_AES_256_GCM_SHA384
                                        ├─ key_share: {curve: secp256r1, public_key: ...}
                                        └─ supported_versions: 1.3
                                        
                                        EncryptedExtensions
                                        ├─ server_name
                                        └─ supported_groups
                                        
                                        CertificateVerify
                                        ├─ certificate: server certificate chain
                                        ├─ signature: sign(handshake_transcript, server_private_key)
                                        └─ verified_by: trusted CA
                                        
                                        Finished
                                        └─ mac: HMAC(all_messages_so_far)
                                        
     [Derive shared keys from key_share exchange]
     ▼
ClientFinished
└─ mac: HMAC(all_messages_so_far)
     │
     ▼
[Connection is now encrypted]

All subsequent data: encrypted with AES-256-GCM
```

### Key Derivation

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


```
Both client and server have:
- Client's public key (sent in ClientHello)
- Server's public key (sent in ServerHello)

Perform ECDH (Elliptic Curve Diffie-Hellman):
- Shared secret = ECDH(client_private, server_public)
- Same as ECDH(server_private, client_public)

Derive actual encryption keys:
- client_handshake_key = PRF(shared_secret, "client handshake")
- server_handshake_key = PRF(shared_secret, "server handshake")
- client_application_key = PRF(shared_secret, "client application")
- server_application_key = PRF(shared_secret, "server application")

Why this works:
- Attacker sees public keys
- Cannot compute shared secret (ECDH is one-way)
- Cannot derive encryption keys
- Perfect forward secrecy: even if server's long-term private key is stolen,
  this session's keys cannot be recovered (they depend on ephemeral keys, not stored)
```

### 0-RTT (Early Data)

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


**Problem:** TLS handshake adds latency

```
Client → Server: ClientHello (1ms latency)
Server → Client: ServerHello (1ms latency)
Client → Server: ClientFinished (1ms latency)
Server → Client: Finished (1ms latency)

Total: 4ms minimum for encrypted connection
```

**Solution: 0-RTT**

```
First connection:
- Normal TLS handshake
- Server sends PSK (Pre-Shared Key)

Second connection:
- Client: "Here's my session ticket" + encrypted data
- Server decrypts, verifies ticket
- Connection is encrypted, no handshake needed!

Latency saved!

Risk: PSK can be replayed
Mitigation:
- Replay protection per server
- Only non-idempotent operations need full handshake
- Mark data as "early data" so app knows to reject if replayed
```

---

## Certificate Management

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


### X.509 Certificate Structure

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


```
Certificate {
  version: v3
  serialNumber: 1234567890
  signature: {
    algorithm: sha256WithRSAEncryption
  }
  issuer: CN=DigiCert Global Root CA
  validity: {
    notBefore: 2024-01-01T00:00:00Z
    notAfter: 2025-01-01T00:00:00Z
  }
  subject: CN=amazon.com, C=US, ST=Washington
  subjectPublicKeyInfo: {
    algorithm: RSA
    publicKey: (2048-bit key)
  }
  extensions: {
    basicConstraints: CA=FALSE
    keyUsage: digitalSignature, keyEncipherment
    extendedKeyUsage: serverAuth
    subjectAlternativeNames: [amazon.com, www.amazon.com, *.amazon.com]
    authorityKeyIdentifier: ...
  }
  signatureValue: (RSA signature over entire certificate by issuer's private key)
}
```

**Key fields:**
- `notBefore` / `notAfter`: When certificate is valid
- `CN` (Common Name): Domain name (amazon.com)
- `subjectAlternativeNames`: All domains covered
- `publicKey`: Server's public key (for TLS)
- `signatureValue`: Proof it came from trusted CA

### Certificate Chain of Trust

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


```
Your Browser
    │
    ▼
[Trusts] Mozilla (or Apple) root CA
    │
    ├─→ Intermediate CA: DigiCert Global Root CA
    │   (signed by Mozilla)
    │
    ├─→ Intermediate CA: DigiCert TLS RSA SG2
    │   (signed by DigiCert Global Root CA)
    │
    └─→ End Entity Certificate: amazon.com
        (signed by DigiCert TLS RSA SG2)
        
Browser verifies chain:
1. Trust anchor: Mozilla root CA is in browser's trust store ✓
2. Verify: DigiCert signature over Intermediate CA
3. Verify: Intermediate CA signature over amazon.com certificate
4. Verify: amazon.com certificate domain matches amazon.com

Attack prevented if:
- Attacker doesn't have private key (can't forge signature)
- Attacker doesn't have trusted CA (can't impersonate)
```

### Certificate Pinning

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


**Problem:**
```
100+ trusted CAs can issue amazon.com certificates
If any CA is hacked, attacker can issue fake amazon.com certificate
```

**Solution: Pin the certificate**

```python
import ssl
import requests

# Hardcode expected certificate
AMAZON_CERT_FINGERPRINT = "12345678abcdef..."

response = requests.get("https://amazon.com", verify=False)

# Manually verify certificate
cert = ssl.get_server_certificate(("amazon.com", 443))
computed_fingerprint = hashlib.sha256(cert).hexdigest()

if computed_fingerprint != AMAZON_CERT_FINGERPRINT:
    raise SecurityError("Certificate mismatch, possible MITM attack")
```

**Better: Use a library**

```python
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.ssl_ import create_urllib3_context
import ssl

class PinningHTTPAdapter(HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        ctx = create_urllib3_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        ctx.cert_reqs = ssl.CERT_REQUIRED
        # Add pinning logic here
        kwargs['ssl_context'] = ctx
        return super().init_poolmanager(*args, **kwargs)
```

---

## Key Management

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


### Key Lifecycle

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


```
GENERATION → DISTRIBUTION → USAGE → ROTATION → REVOCATION
    │            │            │         │           │
    ▼            ▼            ▼         ▼           ▼
Generate    Store securely  Sign data  Replace old  Destroy old
random key  (HSM, vault)    Encrypt   with new     key
                            Verify    Transition   Securely
                                      clients
```

### Key Generation

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


**Secure random number generation:**

```python
import secrets
import os

# GOOD: Use OS entropy
key = os.urandom(32)  # 256-bit key from /dev/urandom

# GOOD: Use cryptographic PRNG
key = secrets.token_bytes(32)

# BAD: Don't use random.random()
import random
key = random.randint(0, 2**256-1)  # NOT cryptographically secure!
```

**Why randomness matters:**

```
Weak key: 12345678901234567890123456789012
Attacker: Brute force all keys 10^8 to 10^8+1000000 (guess in minutes)

Strong key: (from /dev/urandom)
Attacker: Brute force 2^256 ≈ 10^77 possibilities (impossible)
```

### Key Rotation

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


**Strategy: Rolling update**

```
Day 0:
Server has key: key_v1
Client requests: decrypt(data_encrypted_with_key_v1, key_v1) ✓

Day 1:
Generate new key: key_v2
Server stores both: key_v1, key_v2
Client requests: decrypt(data_encrypted_with_key_v1, key_v1) ✓
New data encrypted with: key_v2

Day 2:
More clients updated to key_v2
Old clients still work: decrypt(old_data, key_v1) ✓
New clients work: decrypt(new_data, key_v2) ✓

Day 30:
All clients updated
Server deletes: key_v1
Server keeps: key_v2
No disruption, smooth transition
```

### HSM (Hardware Security Module)

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


**Physical device for key storage:**

```
┌─────────────────────────────┐
│   Application Server        │
│                             │
│   Generate key request      │
└────────────────┬────────────┘
                 │ HTTPS
        ┌────────▼────────┐
        │   HSM Device    │
        │                 │
        │ Generate key:   │
        │ - Private key   │
        │   NEVER leaves  │
        │   device        │
        │                 │
        │ Operations:     │
        │ - Decrypt       │
        │ - Sign          │
        │ - Verify        │
        │                 │
        │ Output only:    │
        │ - Plaintext     │
        │ - Signature     │
        └────────────────┘

Benefits:
- Private key never exposed to application
- Even if server hacked, attacker can't get key
- Tamper-resistant hardware
- Audit logging built-in
- Can require additional authentication (PIN, card)
```

---

## Secrets Management at Scale

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


### The Problem

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


```
Database passwords, API keys, TLS certificates, encryption keys:
All must be:
- Accessible only to authorized services
- Rotated regularly
- Never in plaintext in code
- Logged for audit trail
- Protected from insider threats
```

**Bad:** Hardcoded in code
```python
DB_PASSWORD = "MySecretPassword123"
API_KEY = "sk_live_abc123"
```

**Worse:** In environment variables
```bash
export DB_PASSWORD="MySecretPassword123"
```

**Good:** Secrets vault
```python
from vault_client import VaultClient

client = VaultClient()
db_password = client.get_secret("database/prod/password")
```

### HashiCorp Vault Architecture

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


```
┌─────────────────────────────────────────────┐
│         Vault Server (Encrypted)            │
├─────────────────────────────────────────────┤
│                                             │
│  Secrets Storage (AES-256 encrypted):       │
│  ├─ database/prod/password                 │
│  ├─ api_keys/stripe/secret_key            │
│  ├─ tls/certs/amazon_cert                 │
│  └─ encryption_keys/master_key            │
│                                             │
│  Access Control:                            │
│  ├─ database/prod/* → app-prod role       │
│  ├─ api_keys/stripe/* → payment-service   │
│  └─ tls/certs/* → web-servers             │
│                                             │
│  Audit Log:                                 │
│  ├─ 2024-05-27 10:30:45 app-prod accessed │
│  │  database/prod/password - SUCCESS       │
│  └─ 2024-05-27 10:45:12 attacker attempted│
│     to access database/prod/password       │
│     from unauthorized IP - DENIED          │
│                                             │
│  Automatic Rotation:                        │
│  ├─ Generate new password                  │
│  ├─ Update database                        │
│  ├─ Rotate old password in Vault           │
│  └─ Notify services                        │
│                                             │
└─────────────────────────────────────────────┘
              │
    ┌─────────┼─────────┐
    ▼         ▼         ▼
┌─────┐  ┌──────┐  ┌──────┐
│App1 │  │App2  │  │App3  │
│     │  │      │  │      │
│Auth │  │Auth  │  │Auth  │
│Get  │  │Get   │  │Get   │
│sec  │  │sec   │  │sec   │
│Decrypt  Decrypt  Decrypt
└─────┘  └──────┘  └──────┘
```

### AWS Secrets Manager

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


**Similar concept, AWS-native:**

```python
import boto3

client = boto3.client('secretsmanager', region_name='us-east-1')

# Get secret
response = client.get_secret_value(SecretId='database/prod/password')
password = response['SecretString']

# Automatic rotation
client.rotate_secret(
    SecretId='database/prod/password',
    RotationRules={'AutomaticallyAfterDays': 30}
)
```

**Features:**
- Multi-region replication (disaster recovery)
- Cross-account access (shared secrets between AWS accounts)
- Rotation Lambda functions (automate password updates)
- CloudTrail integration (audit logging)
- Cost: ~$0.40 per secret per month

---

## Failure Analysis

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


### Weak Key Derivation → Complete Data Loss

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


**Scenario:**
```python
# BAD: User-provided password as encryption key directly
password = input("Enter password: ")
key = password.encode()  # Only 8-32 characters!

# Attacker brute forces:
for word in wordlist:
    key = word.encode()
    try:
        decrypt(encrypted_data, key)
        print(f"Found password: {word}")
    except:
        pass

Result: Password cracked in minutes
All encrypted data compromised
```

**Defense: Use key derivation function (KDF)**

```python
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
import os

# Generate random salt
salt = os.urandom(16)

# Derive key from password
kdf = PBKDF2(
    algorithm=hashes.SHA256(),
    length=32,  # 256-bit key
    salt=salt,
    iterations=100000  # Computationally expensive
)
key = kdf.derive(password.encode())

# Store salt + encrypted_data
# (salt doesn't need to be secret, it just needs to be unique)
```

**Why it's better:**
- 100,000 iterations: Takes 100ms to derive each key
- Attacker: 1 billion passwords/second ÷ 100ms = 10,000 attempts/second
- 1 billion passwords: 100,000 seconds = 27 hours (vs minutes before)

### Unrotated Keys → Compromise Spreads

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


**Scenario:**
```
Database encryption key: key_v1
Key has been in use for 5 years
Never rotated

Attacker steals disk
Attacker has access to key_v1
Attacker decrypts 5 years of customer data
- Customer names, emails, SSNs, credit cards
- All exposed

Company discovers breach
Company can't recover
- All data encrypted with compromised key
- No way to know which data was stolen
- Assume all is compromised
```

**Defense: Regular rotation**

```
Day 1: key_v1 (decrypt, encrypt new data)
Day 30: key_v2 (use for new data, old data still readable with v1)
Day 60: key_v3 (reencrypt old data)
Day 90: Delete key_v1, keep v2, v3

Each compromise:
- Only affects data encrypted with that key
- Old data unaffected
- Recryption process ensures compromise is limited
```

### Certificate Expiration → Unavailability

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


**Scenario:**
```
SSL certificate expires: 2024-05-27 23:59:59
Nobody renews it

2024-05-28 00:00:00
Users visit website
Browser: "Certificate expired!"
Browser: "This connection is not secure"
Users: Close tab, go to competitor

Revenue loss: Millions per day per company
```

**Defense: Monitoring + automation**

```python
import ssl
import datetime

def check_cert_expiration(hostname, port=443):
    context = ssl.create_default_context()
    with socket.create_connection((hostname, port), timeout=5) as sock:
        with context.wrap_socket(sock, server_hostname=hostname) as ssock:
            cert = ssock.getpeercert()
            expiry = datetime.datetime.strptime(
                cert['notAfter'],
                '%b %d %H:%M:%S %Y %Z'
            )
            days_left = (expiry - datetime.datetime.now()).days
            
            if days_left < 30:
                alert(f"Certificate expiring in {days_left} days")
            
            return days_left

# Automate renewal with Let's Encrypt (free)
from acme_client import ACMEClient

client = ACMEClient()
client.renew_certificates()  # Runs daily via cron
```

---

## Edge Cases

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


### Nonce Reuse in GCM Mode → Complete Key Recovery

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


**Vulnerability:**
```
If you encrypt two messages with same key AND same nonce:
ciphertext1 = plaintext1 XOR keystream
ciphertext2 = plaintext2 XOR keystream

Attacker XORs:
ciphertext1 XOR ciphertext2 = plaintext1 XOR plaintext2

If attacker knows plaintext1, they can recover plaintext2
And with a few more messages, recover keystream
And with keystream, recover key!
```

**Defense:**
```python
# ALWAYS generate new random nonce
def encrypt_gcm(plaintext, key):
    nonce = os.urandom(12)  # NEW random nonce each time
    cipher = Cipher(algorithms.AES(key), modes.GCM(nonce))
    ciphertext = cipher.encryptor().update(plaintext) + cipher.encryptor().finalize()
    return nonce + ciphertext  # Send nonce with ciphertext

# DON'T use counter-based nonce
def bad_encrypt_gcm(plaintext, key):
    counter = database.get_and_increment_counter(key)  # BUG: Can repeat!
    nonce = counter.to_bytes(12, 'big')
    # If database crashes and counter resets, attacker wins
```

### Weak Certificate Validation → MITM

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


**Vulnerability:**
```python
import requests

# VULNERABLE: Ignores certificate validation
response = requests.get("https://api.example.com", verify=False)

Attacker MITM:
- Intercepts HTTPS connection
- Presents fake certificate
- App ignores certificate validation (verify=False)
- App sends API key, tokens, data to attacker
```

**Defense:**
```python
# GOOD: Default (verify=True)
response = requests.get("https://api.example.com")

# GOOD: Explicitly specify cert bundle
response = requests.get(
    "https://api.example.com",
    verify="/etc/ssl/certs/ca-bundle.crt"
)

# GOOD: Pin certificate
response = requests.get(
    "https://api.example.com",
    cert=("client_cert.pem", "client_key.pem")
)
```

---

## Interview Questions

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


### Q1: Design Key Management System for Petabyte-Scale Encryption

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


**Answer:**

Architecture:
```
1. Master Key
   - Stored in HSM in highly restricted location
   - Never used directly for data encryption
   - Only used to encrypt Data Encryption Keys (DEK)

2. Key Hierarchy
   Master Key (in HSM)
       ↓
   Region Keys (replicated across regions)
       ↓
   Data Encryption Keys (one per object)

3. DEK Generation
   - Generate 256-bit random DEK
   - Encrypt DEK with Region Key: encrypted_dek = AES(dek, region_key)
   - Store encrypted_dek with data
   - Never store DEK in plaintext

4. Encryption at REST
   plaintext → AES-256-GCM(plaintext, dek) → ciphertext
   Store: ciphertext + encrypted_dek + metadata

5. Decryption
   Read: ciphertext + encrypted_dek
   Decrypt DEK: dek = AES_decrypt(encrypted_dek, region_key)
   Decrypt data: plaintext = AES_decrypt(ciphertext, dek)

6. Key Rotation
   Day 1: Generate new region_key_v2
   Day 1-30: Transition period (both keys valid)
   Day 2-7: Reencrypt critical data
   Day 8-15: Reencrypt warm data
   Day 16-30: Reencrypt cold data
   Day 31: Disable old key, keep for audit
   Day 90: Delete old key

7. Disaster Recovery
   - Regional failover: replicate keys to DR region
   - 3 of 5 key shards required to recover Master Key (Shamir's secret sharing)
   - Escrow copies stored in safe deposit boxes
   - Quarterly key recovery drills
```

### Q2: How to Implement TLS Certificate Pinning?

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


**Answer:**

```python
import ssl
import hashlib
import requests
from requests.adapters import HTTPAdapter

class CertificatePinningAdapter(HTTPAdapter):
    def __init__(self, pinned_hashes, *args, **kwargs):
        self.pinned_hashes = pinned_hashes
        super().__init__(*args, **kwargs)
    
    def init_poolmanager(self, *args, **kwargs):
        context = ssl.create_default_context()
        
        # Custom certificate verification
        original_verify = context.check_hostname
        
        def verify_pin(conn, cert, errno, depth, ok):
            if not ok:
                return False
            
            cert_bytes = conn.get_peer_certificate_binary(depth)
            cert_hash = hashlib.sha256(cert_bytes).hexdigest()
            
            if cert_hash not in self.pinned_hashes:
                return False
            
            return True
        
        context.set_verify_callback(verify_pin)
        kwargs['ssl_context'] = context
        return super().init_poolmanager(*args, **kwargs)

# Usage
pinned_hashes = {
    "12345678abcdef...",  # Current certificate
    "87654321fedcba...",  # Backup certificate
}

session = requests.Session()
adapter = CertificatePinningAdapter(pinned_hashes)
session.mount('https://api.example.com', adapter)

response = session.get('https://api.example.com/data')
```

### Q3: Difference Between Encryption and Hashing?

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


**Answer:**

| Aspect | Encryption | Hashing |
|--------|-----------|---------|
| **Purpose** | Confidentiality | Integrity |
| **Reversible** | Yes (with key) | No (one-way) |
| **Key needed** | Yes (secret) | No (public) |
| **Input size** | Any | Any |
| **Output size** | Same as input | Fixed (SHA256: 256 bits) |
| **Use case** | Encrypting passwords, data | Checksums, digital signatures |
| **Example** | AES(password) | SHA256(password) |

---

## Production Code Examples

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


### Secure Data Encryption Service

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


```python
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
import os
import json
import base64

class EncryptionService:
    def __init__(self, master_key: bytes):
        self.master_key = master_key
    
    def encrypt_data(self, plaintext: str, associated_data: str = "") -> str:
        """Encrypt data with AES-256-GCM"""
        
        # Generate random key and nonce
        data_key = os.urandom(32)
        nonce = os.urandom(12)
        
        # Encrypt plaintext
        cipher = AESGCM(data_key)
        ciphertext = cipher.encrypt(nonce, plaintext.encode(), associated_data.encode())
        
        # Encrypt the data key with master key
        master_cipher = AESGCM(self.master_key)
        encrypted_key = master_cipher.encrypt(os.urandom(12), data_key, b"")
        
        # Combine: nonce + encrypted_key + ciphertext
        result = {
            'nonce': base64.b64encode(nonce).decode(),
            'encrypted_key': base64.b64encode(encrypted_key).decode(),
            'ciphertext': base64.b64encode(ciphertext).decode()
        }
        
        return json.dumps(result)
    
    def decrypt_data(self, encrypted: str, associated_data: str = "") -> str:
        """Decrypt data"""
        
        data = json.loads(encrypted)
        nonce = base64.b64decode(data['nonce'])
        encrypted_key = base64.b64decode(data['encrypted_key'])
        ciphertext = base64.b64decode(data['ciphertext'])
        
        # Decrypt the data key
        master_cipher = AESGCM(self.master_key)
        data_key = master_cipher.decrypt(nonce, encrypted_key, b"")
        
        # Decrypt the ciphertext
        cipher = AESGCM(data_key)
        plaintext = cipher.decrypt(nonce, ciphertext, associated_data.encode())
        
        return plaintext.decode()

# Usage
master_key = os.urandom(32)
service = EncryptionService(master_key)

encrypted = service.encrypt_data("Secret message", "metadata")
decrypted = service.decrypt_data(encrypted, "metadata")
assert decrypted == "Secret message"
```

### Certificate Renewal Automation

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


```python
import subprocess
import datetime
import pytz
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa

class CertificateManager:
    def __init__(self, domains: list):
        self.domains = domains
    
    def check_expiration(self) -> int:
        """Check days until certificate expiration"""
        try:
            with open('/etc/ssl/certs/server.crt', 'rb') as f:
                cert = x509.load_pem_x509_certificate(f.read())
            
            expiry = cert.not_valid_after_utc.replace(tzinfo=pytz.UTC)
            days_left = (expiry - datetime.datetime.now(tz=pytz.UTC)).days
            return days_left
        except:
            return -1
    
    def renew_certificate(self):
        """Renew using Let's Encrypt"""
        
        # Generate private key if not exists
        try:
            with open('/etc/ssl/private/server.key', 'rb') as f:
                private_key = serialization.load_pem_private_key(f.read(), password=None)
        except:
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048
            )
            with open('/etc/ssl/private/server.key', 'wb') as f:
                f.write(private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.TraditionalOpenSSL,
                    encryption_algorithm=serialization.NoEncryption()
                ))
        
        # Use certbot (Let's Encrypt client)
        domains_arg = ",".join(self.domains)
        result = subprocess.run([
            'certbot', 'certonly',
            '--standalone',
            '-d', domains_arg,
            '--email', 'admin@example.com',
            '--agree-tos'
        ], capture_output=True)
        
        if result.returncode == 0:
            # Reload web server
            subprocess.run(['systemctl', 'reload', 'nginx'])
            return True
        return False

# Usage
manager = CertificateManager(['example.com', 'www.example.com'])
days_left = manager.check_expiration()
if days_left < 30:
    manager.renew_certificate()
```

---

## Incident Stories

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


### Story 1: Hardcoded API Key → AWS Account Compromise

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


**The Setup:**
Developer pushes code with API key:

```python
# src/config.py
AWS_ACCESS_KEY = "AKIAIOSFODNN7EXAMPLE"
AWS_SECRET_KEY = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
```

**The Breach:**
- Code pushed to GitHub
- GitHub notifies AWS (they scan for leaked keys)
- AWS notifies company
- But attacker already found it on GitHub

**The Attack:**
Attacker uses key to:
- Launch EC2 instances (crypto mining)
- Create S3 buckets, dump data
- Create IAM users for persistence

Bill: $50,000 for 24 hours of crypto mining
Company detects anomaly, revokes key

**Lesson: Use IAM roles, not hardcoded keys**

### Story 2: SSL Certificate Expiration → Outage

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


**The Setup:**
Company's SSL certificate expired at 2024-05-27 23:59:59
Nobody had set up automatic renewal

**The Outage:**
- 2024-05-28 00:00:00: Certificate expires
- Users visit website
- Browser shows "This connection is not secure"
- 95% of users leave
- Revenue: $0 for 2 hours
- Cost to resolve: 1 engineer (1 hour) + ops overhead
- Total cost: $100,000+

**Discovery:**
Customer complaint email: "Your website is broken"
(Not from monitoring, from angry customer)

**Lesson: Automate certificate renewal**

---

**End of File: 800+ lines**

---

## Related

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


- [Networking](../../11-networking/) — TLS, DNS security
- [Cloud Platforms](../../05-cloud/) — IAM, network policies
- [Kubernetes](../../07-kubernetes/) — Pod security, RBAC
- [Backend](../../03-backend/) — Input validation, auth
- [Databases](../../08-databases/) — Encryption, access control
