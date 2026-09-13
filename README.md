# SAT-DMS — Secure Digital Document Management System

**SIH 2026 · PS 26190 · Ministry of Home Affairs (NCRB) · Blockchain & Cybersecurity**

> Offline-first, tamper-evident document management for FIRs, witness statements, charge sheets, forensic reports, and case files.

---

## Overview

SAT-DMS applies **five security controls to every document**:

```text
                         ┌─────────────┐
                         │  DOCUMENT   │
                         └──────┬──────┘
                                │
              ┌─────────────────┼─────────────────┐
              │                 │                 │
              ▼                 ▼                 ▼
        ┌──────────┐      ┌──────────┐      ┌──────────┐
        │ AES-256  │      │ SHA-256  │      │ Ed25519  │
        │   GCM    │      │   Hash   │      │ Signature│
        └────┬─────┘      └────┬─────┘      └────┬─────┘
             │                 │                 │
             └─────────────────┼─────────────────┘
                               ▼
                    ┌────────────────────┐
                    │  AUDIT HASH CHAIN  │
                    └─────────┬──────────┘
                              ▼
                       CASE + VERSIONS
```

| Security        | Implementation                               |
| --------------- | -------------------------------------------- |
| Confidentiality | AES-256-GCM                                  |
| Integrity       | SHA-256                                      |
| Non-repudiation | Ed25519                                      |
| Audit Integrity | SHA-256 Hash Chain                           |
| Access Control  | RBAC                                         |
| Search          | Title · Case · Hash · Uploader · Description |

---

## Requirement Mapping

| SIH Requirement      | SAT-DMS Implementation               |
| -------------------- | ------------------------------------ |
| Centralized storage  | SQLite + encrypted file store        |
| Secure access        | Login + RBAC + AES-256-GCM           |
| Prevent modification | SHA-256 + Ed25519                    |
| Complete audit trail | Append-only hash chain               |
| Efficient search     | Multi-field search                   |
| Collaboration        | RBAC + version chains                |
| Compliance           | Cryptographic verification + history |
| Case management      | Case → Document relationships        |

---

## Architecture

```text
                         ┌────────────────────┐
                         │      SAT-DMS       │
                         └─────────┬──────────┘
                                   │
                         ┌─────────▼─────────┐
                         │ Authentication +  │
                         │       RBAC        │
                         └─────────┬─────────┘
                                   │
                         ┌─────────▼─────────┐
                         │ Case Management   │
                         └─────────┬─────────┘
                                   │
                         ┌─────────▼─────────┐
                         │ Document Engine    │
                         └─────────┬─────────┘
                                   │
              ┌────────────────────┼────────────────────┐
              ▼                    ▼                    ▼
       ┌────────────┐       ┌────────────┐       ┌────────────┐
       │ AES-256-GCM│       │  SHA-256   │       │  Ed25519   │
       │ Encryption │       │   Hashing  │       │  Signing   │
       └──────┬─────┘       └──────┬─────┘       └──────┬─────┘
              │                    │                    │
              └────────────────────┼────────────────────┘
                                   ▼
                    ┌─────────────────────────┐
                    │ SQLite + Encrypted Store│
                    └────────────┬────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │    Audit Hash Chain     │
                    └─────────────────────────┘
```

---

## Cryptographic Verification

### Upload

```text
DOCUMENT
   │
   ├──► SHA-256 ──────► Store Hash
   │
   ├──► Ed25519 ──────► Store Signature
   │
   └──► AES-256-GCM ──► Store Ciphertext
```

### Download

```text
Encrypted File
      │
      ▼
   Decrypt
      │
      ▼
   SHA-256
      │
   ┌──┴──┐
   ▼     ▼
 MATCH  MISMATCH
   │       │
   ▼       ▼
  ✓ OK    ✗ BLOCK
```

---

## Audit Ledger

```text
┌─────────┐      ┌─────────┐      ┌─────────┐
│ Entry 0 │─────►│ Entry 1 │─────►│ Entry 2 │─────► ...
│ hash    │      │prev_hash│      │prev_hash│
│ 0000... │      │ hash E0 │      │ hash E1 │
└─────────┘      └─────────┘      └─────────┘
```

```text
entry[i].hash =
SHA256(index || timestamp || prev_hash ||
       event_type || payload || actor)
```

```text
Modify Entry
     │
     ▼
Recalculate Hash
     │
     ▼
Hash ≠ Stored Hash
     │
     ▼
⚠ TAMPERING DETECTED
```

---

## Quick Start

```bash
git clone https://github.com/CalculusGuy/Secure-Legal-Investigation-DMS-SIH_26190.git
cd Secure-Legal-Investigation-DMS-SIH_26190
python -m venv .venv
```

```bash
# Windows
.venv\Scripts\activate.bat

# Linux / macOS
source .venv/bin/activate
```

```bash
pip install -r requirements.txt
python run.py
```

Open **http://127.0.0.1:5000**

`First Launch → Setup → Create Admin`

---

## Demo Flow

```text
Create Admin
     │
     ▼
Create Case
     │
     ▼
Upload Document
     │
     ▼
SHA-256 + Ed25519 + AES-256-GCM
     │
     ▼
Verify Integrity
     │
     ▼
Download
     │
     ▼
Audit Ledger
     │
     ▼
Upload Version 2
     │
     ▼
Tamper Test
```

### Tamper Test

```text
Stop Server
     │
     ▼
Edit instance/audit_chain.json
     │
     ▼
Restart SAT-DMS
     │
     ▼
Open Dashboard / Audit Ledger
     │
     ▼
⚠ TAMPERING DETECTED
```

Restore the original value → **chain becomes valid again.**

---

## Tech Stack

| Layer          | Technology                |
| -------------- | ------------------------- |
| Backend        | Python 3.8+ · Flask 3.0   |
| Database       | SQLite · Flask-SQLAlchemy |
| Authentication | Flask-Login               |
| Cryptography   | `cryptography` 47.x       |
| Encryption     | AES-256-GCM               |
| Hashing        | SHA-256                   |
| Signatures     | Ed25519                   |
| Passwords      | Passlib · Werkzeug        |
| Frontend       | Jinja2 · Vanilla CSS      |
| PDF            | pypdf                     |

---

## Project Structure

```text
sat-dms/
├── app/
│   ├── crypto/
│   │   ├── encryption.py
│   │   └── signatures.py
│   ├── ledger/
│   │   └── chain.py
│   ├── routes/
│   │   ├── auth.py
│   │   ├── documents.py
│   │   ├── cases.py
│   │   ├── audit.py
│   │   └── admin.py
│   ├── models.py
│   └── __init__.py
├── storage/
│   ├── encrypted/
│   └── keys/
├── instance/
├── config.py
├── run.py
└── requirements.txt
```

---

## Offline / Air-Gapped

```text
┌──────────────────────────────────────┐
│            AIR-GAPPED HOST           │
│                                      │
│   SAT-DMS                            │
│      │                               │
│      ├──► SQLite Metadata            │
│      ├──► Encrypted Documents        │
│      └──► Audit Hash Chain           │
│                                      │
└──────────────────────────────────────┘
```

**No Cloud · No External API · No SaaS · No Telemetry · No Internet Dependency**

---

## Roadmap

* [ ] Architecture document
* [ ] Automated security test suite
* [ ] Advanced RBAC
* [ ] PDF text extraction
* [ ] Case-level audit reports
* [ ] Offline deployment package
* [ ] SIH validation dataset

---

## SIH 2026 Deliverables

* [x] Source Code
* [x] README
* [ ] Architecture Document — 2 pages
* [ ] Demo Video — 2 minutes
* [ ] Technical Presentation — 5 slides

---

## License

**MIT License** — see [`LICENSE`](LICENSE).
