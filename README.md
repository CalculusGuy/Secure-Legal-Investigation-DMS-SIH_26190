# SAT-DMS - Secure Digital Document Management System

**SIH 2026 | PS 26190 | Ministry of Home Affairs (NCRB) | Blockchain & Cybersecurity**

Offline-first, tamper-evident document management for FIRs, witness statements, charge sheets, forensic reports, and case files.

---

## Overview

SAT-DMS secures every document through five independent controls:
+-----------------+
| DOCUMENT |
+--------+--------+
|
+------------------+------------------+
| | |
v v v
AES-256-GCM SHA-256 Ed25519
Encryption Integrity Signature
| | |
+------------------+------------------+
|
v
+-----------------+
| Hash-Chained |
| Audit Ledger |
+--------+--------+
|
v
Case + Version Chain

text

| Security        | Implementation                           |
| --------------- | ---------------------------------------- |
| Confidentiality | AES-256-GCM                              |
| Integrity       | SHA-256                                  |
| Non-repudiation | Ed25519                                  |
| Audit integrity | SHA-256 hash chain                       |
| Access control  | RBAC                                     |
| Search          | Title, case, hash, uploader, description |

---

## Requirement Mapping

| SIH Requirement      | SAT-DMS                              |
| -------------------- | ------------------------------------ |
| Centralized storage  | SQLite + encrypted file store        |
| Secure access        | Login + RBAC + AES-256-GCM           |
| Prevent modification | SHA-256 + Ed25519                    |
| Complete audit trail | Append-only hash chain               |
| Efficient search     | Multi-field search                   |
| Collaboration        | RBAC + version chains                |
| Compliance           | Cryptographic verification + history |
| Case management      | Case -> Document relationships       |

---

## Architecture
SAT-DMS
|
+----------+----------+
| Authentication/RBAC |
+----------+----------+
|
+----------+----------+
| Case Management |
+----------+----------+
|
+----------+----------+
| Document Engine |
+----------+----------+
|
+--------------+--------------+
| | |
v v v
AES-256-GCM SHA-256 Ed25519
Encryption Hashing Signing
| | |
+--------------+--------------+
|
v
+---------------------+
| Encrypted Storage |
| SQLite Metadata |
+----------+----------+
|
v
+---------------------+
| Audit Hash Chain |
+---------------------+

text

---

## Cryptographic Verification

### Document
UPLOAD
|
+--> SHA-256 ------> Store hash
+--> Ed25519 ------> Store signature
+--> AES-256-GCM --> Store ciphertext

text

### Download
Encrypted File
|
v
Decrypt
|
v
SHA-256
|
+----+----+
| |
v v
MATCH MISMATCH
| |
v v
OK BLOCK

text

---

## Audit Ledger
Entry 0 Entry 1 Entry 2
+---------+ +---------+ +---------+
| hash |<------------| prevHash|<------------| prevHash|
| 0000... | | hash E0 | | hash E1 |
+---------+ +---------+ +---------+

text
entry[i].hash =
SHA256(index || timestamp || prev_hash ||
event_type || payload || actor)

text

Any modification breaks the chain:
Modify Entry
|
v
Recalculate Hash
|
v
Hash != Stored Hash
|
v
TAMPERING DETECTED

text

---

## Quick Start

```bash
git clone https://github.com/CalculusGuy/Secure-Legal-Investigation-DMS-SIH_26190.git
cd Secure-Legal-Investigation-DMS-SIH_26190

python -m venv .venv

# Windows
.venv\Scripts\activate.bat

# Linux/macOS
source .venv/bin/activate

pip install -r requirements.txt
python run.py
Open http://127.0.0.1:5000

First launch -> Setup -> Create Admin

Demo Flow
text
Create Admin
     |
     v
Create Case
     |
     v
Upload Document
     |
     v
SHA-256 + Ed25519 + AES-256-GCM
     |
     v
Verify Integrity
     |
     v
Download
     |
     v
Audit Ledger
     |
     v
Upload Version 2
     |
     v
Tamper Test
Tamper Test
text
Stop Server
    |
    v
Edit instance/audit_chain.json
    |
    v
Restart SAT-DMS
    |
    v
Open Dashboard / Audit Ledger
    |
    v
TAMPERING DETECTED
Restore the original value -> chain becomes valid again.

Tech Stack
Layer	Technology
Backend	Python 3.8+ / Flask 3.0
Database	SQLite / Flask-SQLAlchemy
Authentication	Flask-Login
Cryptography	cryptography 47.x
Encryption	AES-256-GCM
Hashing	SHA-256
Signatures	Ed25519
Passwords	Passlib + Werkzeug
Frontend	Jinja2 + Vanilla CSS
PDF	pypdf
Project Structure
text
sat-dms/
|
+-- app/
|   +-- crypto/
|   |   +-- encryption.py
|   |   +-- signatures.py
|   +-- ledger/
|   |   +-- chain.py
|   +-- routes/
|   |   +-- auth.py
|   |   +-- documents.py
|   |   +-- cases.py
|   |   +-- audit.py
|   |   +-- admin.py
|   +-- models.py
|   +-- __init__.py
+-- storage/
|   +-- encrypted/
|   +-- keys/
+-- instance/
+-- config.py
+-- run.py
+-- requirements.txt
Deployment
Designed for offline / air-gapped environments.

text
+---------------------------------+
|          AIR-GAPPED HOST        |
|                                 |
|  SAT-DMS --> SQLite             |
|      |      Encrypted Storage   |
|      +----> Audit Ledger        |
|                                 |
+---------------------------------+
No cloud | No external API | No SaaS | No telemetry | No Internet dependency

Roadmap
□ Architecture document
□ Automated security test suite
□ Advanced RBAC
□ PDF text extraction
□ Case-level audit reports
□ Offline deployment package
□ SIH validation dataset
SIH 2026 Deliverables
☑ Source Code
☑ README
□ Architecture Document - 2 pages
□ Demo Video - 2 minutes
□ Technical Presentation - 5 slides
License
MIT License - see LICENSE.
