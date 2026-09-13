# SAT-DMS Architecture Document

**SIH 2026 | Problem Statement 26190 | Ministry of Home Affairs (NCRB)**
**Secure Digital Document Management System for Legal and Investigation Documents**

---

## 1. Problem Summary

Law enforcement agencies, courts, and investigative departments handle vast
quantities of sensitive documents across the lifecycle of a case: FIRs, witness
statements, charge sheets, forensic reports, and judgments. Existing approaches
- paper-based systems, shared drives, and generic DMS tools - fail on one or
more of six required properties:

- Confidentiality      (no unauthorized access)
- Integrity            (no undetected modification)
- Attribution          (every action traceable to a user)
- Auditability         (complete, tamper-evident history)
- Retrievability       (fast search across cases)
- Compliance           (evidentiary integrity for legal use)

SAT-DMS addresses all six through cryptographic controls combined with a
tamper-evident audit ledger.

---

## 2. Solution Overview

SAT-DMS is an offline, air-gapped document management system. Every document
that enters the system is processed through four independent cryptographic
controls:

1. Encrypted at rest with AES-256-GCM
2. Hashed with SHA-256 for integrity anchoring
3. Signed with the uploader's Ed25519 private key for non-repudiation
4. Committed to an append-only, hash-chained audit ledger

The system supports role-based access (admin / investigator / viewer), case
grouping, document versioning, and full-text search across document metadata.

The core design principle: **verify, do not trust.** No single user - not even
an administrator with database access - can alter a document or its audit trail
without detection.

---

## 3. System Architecture
+-------------------------------------------------------------+
| Flask Web Application |
| 127.0.0.1:5000 (local) |
| |
| /auth /documents /cases |
| /audit /admin /search |
+-----------------------------+-------------------------------+
|
+---------------------+---------------------+
| | |
v v v
+-----------+ +-------------+ +-------------+
| Auth | | Document | | Audit |
| RBAC | | Service | | Ledger |
+-----------+ +-------------+ +-------------+
| passlib | | AES-256-GCM | | SHA-256 |
| sessions | | SHA-256 | | hash chain |
| roles | | Ed25519 | | append-only |
+-----+-----+ +------+------+ +------+------+
| | |
+----------------------+---------------------+
|
v
+-----------------------+
| SQLite |
| sat-dms.db |
| users / cases / |
| documents metadata |
+-----------+-----------+
|
v
+-----------------------+
| Encrypted File |
| Store (on disk) |
| storage/encrypted/ |
+-----------------------+

text

### Component Descriptions

**Authentication / RBAC** - Flask-Login sessions with three roles: admin
(full access + user management), investigator (upload + view + version),
viewer (read-only). Passwords hashed with Werkzeug's PBKDF2-based scheme.

**Case Management** - Cases group related documents. Each document belongs to
at most one case. Case numbers are unique and indexed.

**Document Engine** - Handles upload, download, verification, search, and
versioning. On every upload, the file passes through hashing, signing, and
encryption before being persisted. On every download, the hash is recomputed
and compared before delivery.

**Audit Ledger** - Append-only JSON file with SHA-256 hash chaining. Every
state-changing action is logged with actor, timestamp, event type, and
payload. The full chain is re-verified on every page load.

**Storage Layer** - SQLite for structured metadata (users, cases, document
records), and a flat-file directory for AES-encrypted document blobs. Both
are local, no network storage.

---

## 4. Cryptographic Design

### 4.1 Confidentiality - AES-256-GCM

Each document is encrypted with AES-256-GCM using a 12-byte cryptographically
random nonce generated per file. The ciphertext is stored on disk; the
plaintext never persists after the request completes.
nonce = os.urandom(12)
ciphertext = AESGCM(master_key).encrypt(nonce, plaintext, None)
stored_blob = nonce || ciphertext || auth_tag

text

GCM mode provides authenticated encryption: any modification to the ciphertext
is detected during decryption and raises an exception.

### 4.2 Integrity - SHA-256

Every document's SHA-256 digest is computed at upload time and stored in the
database. On every download and every manual verification, the digest is
recomputed from the decrypted plaintext and compared. A single-bit difference
blocks delivery.

### 4.3 Non-Repudiation - Ed25519

Each user receives a persistent Ed25519 keypair on their first upload. The
private key is stored at `storage/keys/user_<id>_private.key` with restrictive
permissions. Every document is signed by the uploader's private key at upload
time.
signature = Ed25519_private_key.sign(document_bytes)
public_key = Ed25519_private_key.public_key()

text

At any later time, the signature can be verified against the stored public
key, proving that the uploader cannot deny having uploaded that exact content.

### 4.4 Tamper-Evidence - Hash-Chained Ledger

Every event is appended to a hash chain:
entry[i].hash = SHA256(
index[i] ||
timestamp[i] ||
prev_hash[i] ||
event_type[i] ||
payload[i] ||
actor[i]
)

where prev_hash[i] = entry[i-1].hash
and prev_hash[0] = "0000000000000000000000000000000000000000000000000000000000000000"

text

To tamper with entry N without detection, an attacker must:

1. Modify entry N
2. Recompute entry N's hash
3. Modify entry N+1's prev_hash field
4. Recompute entry N+1's hash
5. Repeat for every subsequent entry

Effectively, they must rewrite the entire chain from the point of tampering
forward. This is the tamper-evidence guarantee.

---

## 5. Security Properties

| Property          | Mechanism                                     |
| ----------------- | --------------------------------------------- |
| Confidentiality   | AES-256-GCM at rest; login required for access|
| Integrity         | SHA-256 hash verified on every download       |
| Non-repudiation   | Ed25519 signature with user private key       |
| Tamper-evidence   | Hash-chained append-only ledger               |
| Access control    | RBAC: admin / investigator / viewer           |
| Attribution       | Every event logged with username + timestamp  |
| Auditability      | Full event history, cryptographically verifiable|
| Offline operation | No network calls; no cloud dependency         |

---

## 6. Requirement Mapping

| PS Requirement                   | Implementation                             |
| -------------------------------- | ------------------------------------------ |
| Digitize and centralize storage  | SQLite metadata + encrypted file store     |
| Secure access and confidentiality| Login + RBAC + AES-256-GCM                 |
| Prevent unauthorized modification| SHA-256 + Ed25519                          |
| Complete audit trail             | Hash-chained append-only ledger            |
| Efficient document search        | Multi-field search (title, case, hash, user)|
| Collaboration among stakeholders | RBAC + version chains preserved            |
| Legal and regulatory compliance  | Cryptographic non-repudiation + history    |
| Case management                  | Case -> Document relationship model        |

---

## 7. Deployment Model

The system is designed for deployment within an NCIIPC / law-enforcement
controlled environment with the following properties:

- Fully offline / air-gapped network operation
- No internet connectivity required at any time
- No cloud services, no external APIs, no SaaS dependencies
- No telemetry to third parties
- Local SQLite persistence
- Local file storage

### Minimum Infrastructure

| Component   | Requirement                          |
| ----------- | ------------------------------------ |
| CPU         | Any modern x86-64                    |
| RAM         | 2 GB minimum (4 GB recommended)      |
| Disk        | 500 MB for application + storage     |
| OS          | Windows 10+, Ubuntu 20.04+, or macOS 12+ |
| Python      | 3.8 or later                         |
| Network     | None required                        |

### Deployment Steps

1. Copy the repository to the target machine
2. Create a Python virtual environment
3. Install dependencies via `pip install -r requirements.txt`
4. Run `python run.py`
5. Access via `http://127.0.0.1:5000`

---

## 8. Validation Methodology

The PS requires demonstrating "compliance with legal and regulatory
requirements" and preserving "evidentiary integrity." SAT-DMS validates this
through three layers:

**Layer 1 - Integrity validation.** For every document, the SHA-256 hash is
recomputed at download time and compared against the stored hash. A mismatch
blocks delivery and raises a security warning.

**Layer 2 - Signature validation.** For every document, the Ed25519 signature
is verified against the uploader's stored public key. An invalid signature
indicates either content modification or unauthorized signer.

**Layer 3 - Chain validation.** On every page load, the entire audit ledger
is re-verified: each entry's stored hash is recomputed and each entry's
prev_hash is compared to its predecessor. Any discrepancy produces a red
tamper-alert with the exact entry index.

The following live demonstration proves the design:

1. Upload a document
2. Verify - both hash and signature pass
3. Download - integrity re-checked before delivery
4. Manually modify `instance/audit_chain.json`
5. Restart the application
6. Observe: red banner - "TAMPERING DETECTED - Entry N: hash mismatch"
7. Restore the original value
8. Restart - green banner returns

This proves detection is deterministic and free of false positives.

---

## 9. Data Requirements

SAT-DMS operates on structured submissions containing:

- Document files (PDF, text, images - any format)
- Case metadata (case number, title, description, status)
- User metadata (username, full name, role)
- Audit events (login, upload, download, verify, version)

No raw logs, packet captures, or customer information are required. All data
is processed locally; none leaves the deployment environment.

---

## 10. Summary

SAT-DMS delivers a tamper-evident document management system for legal and
investigative use. It combines four independent cryptographic controls
(AES-256-GCM, SHA-256, Ed25519, and a hash-chained ledger) to guarantee
confidentiality, integrity, non-repudiation, and auditability - properties
that no single administrative account can silently undermine.

The system runs fully offline, requires no external dependencies, and is
deployable on commodity hardware within an air-gapped environment.

---

*SAT-DMS - SIH 2026 - PS 26190 - Ministry of Home Affairs (NCRB)*
