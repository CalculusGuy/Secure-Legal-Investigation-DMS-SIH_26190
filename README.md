SAT-DMS — Secure Digital Document Management System

SIH 2026 · Problem Statement 26190 · Ministry of Home Affairs (NCRB, Women Safety Division) · Theme: Blockchain & Cybersecurity · Category: Software

An offline, tamper-evident document management system for securely storing, verifying, auditing, searching, and versioning legal and investigation records such as FIRs, witness statements, charge sheets, forensic reports, and case files.

1. What Problem This Solves

Legal and investigative documents require strong confidentiality, integrity, traceability, and non-repudiation.

SAT-DMS provides a fully local and offline document management workflow where every uploaded document is:

Encrypted at rest using AES-256-GCM
Integrity-protected using SHA-256
Cryptographically signed using the uploader's Ed25519 private key
Recorded in an append-only hash-chained audit ledger
Searchable by metadata, case number, uploader, and hash
Preserved through version chains

The system is designed for law enforcement, courts, and investigative agencies operating in offline or air-gapped environments.

2. Feature-to-Requirement Mapping
Requirement	SAT-DMS Implementation
Digitize and centralize document storage	SQLite metadata database + encrypted local file store
Secure access and confidentiality	Login + RBAC (admin, investigator, viewer) + AES-256-GCM
Prevent unauthorized modifications	SHA-256 integrity verification + Ed25519 document signatures
Maintain a complete audit trail	Append-only JSON audit ledger with SHA-256 hash chaining
Enable efficient search	Search across title, description, SHA-256 prefix, case number, and uploader
Support collaboration	Role-based access + preserved document version chains
Legal/regulatory compliance	Cryptographic non-repudiation + version history + auditability
Case management	Case records group and organize related documents
3. Live Demo

Clone and run SAT-DMS locally:

git clone https://github.com/CalculusGuy/Secure-Legal-Investigation-DMS-SIH_26190.git
cd Secure-Legal-Investigation-DMS-SIH_26190
python -m venv .venv

Activate the environment:

# Windows
.venv\Scripts\activate.bat

# Linux/macOS
source .venv/bin/activate

Install dependencies and start the application:

pip install -r requirements.txt
python run.py

Open:

http://127.0.0.1:5000

On first launch, SAT-DMS redirects to the Setup page to create the initial administrator account.

4. 5-Minute Walkthrough + Tamper Test
Standard Demonstration
Create the administrator
Complete first-run setup.
Create a case
Example: FIR-2026-0001
Upload a document
The document is encrypted, hashed, signed, and recorded in the audit ledger.
Inspect document integrity
Open the document details.
Review the stored SHA-256 digest and Ed25519 signature.
Select Verify Integrity.
Verify the result
SHA-256 integrity check passes.
Ed25519 signature verification passes.
Download the document
SAT-DMS decrypts the file.
The plaintext is hashed again.
The recomputed hash is compared with the stored hash.
A mismatch blocks the download.
Open the Audit Ledger
Review the hash-chained record of system activity.
Create a new version
Upload a new version of the document.
The original version remains preserved in the version chain.
Search
Search using title, case number, SHA-256 prefix, description, or uploader.
Tamper Test

The audit ledger provides a direct demonstration of tamper detection.

1. Stop the server.

2. Modify any character in:

instance/audit_chain.json

3. Restart SAT-DMS.

4. Open the dashboard or Audit Ledger.

Expected result:

⚠️ TAMPERING DETECTED — Entry N: hash mismatch (tampered)

The modified historical entry no longer produces the hash recorded by the chain, so the integrity check fails.

5. Restore the original value.

The ledger returns to a valid state and the tampering warning disappears.

5. Architecture
                         SAT-DMS
                            │
                            ▼
                ┌──────────────────────┐
                │   Authentication &   │
                │        RBAC           │
                └──────────┬───────────┘
                           │
                           ▼
                ┌──────────────────────┐
                │    Case Management   │
                │  Cases + Documents   │
                └──────────┬───────────┘
                           │
              ┌────────────┴────────────┐
              ▼                         ▼
    ┌──────────────────┐      ┌──────────────────┐
    │ Document Upload  │      │ Document Search  │
    └────────┬─────────┘      └──────────────────┘
             │
             ▼
    ┌───────────────────────────────┐
    │       Security Pipeline       │
    │                               │
    │  AES-256-GCM Encryption       │
    │  SHA-256 Integrity Hash       │
    │  Ed25519 Digital Signature    │
    └───────────────┬───────────────┘
                    │
          ┌─────────┴─────────┐
          ▼                   ▼
 ┌─────────────────┐   ┌──────────────────┐
 │ Encrypted File  │   │ SQLite Metadata  │
 │    Storage      │   │     Database     │
 └─────────────────┘   └──────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │ Audit Ledger     │
                    │ SHA-256 Hash     │
                    │ Chain            │
                    └──────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │ Integrity /      │
                    │ Audit Verification│
                    └──────────────────┘
Document Security Flow
Plaintext Document
       │
       ├──► SHA-256 ───────────────► Stored Document Hash
       │
       ├──► Ed25519 Sign ──────────► Uploader Signature
       │
       └──► AES-256-GCM Encrypt ───► Encrypted File Store
                                      │
                                      ▼
                              Local Secure Storage
6. Cryptographic Design

SAT-DMS applies all five security controls to every document.

AES-256-GCM — Confidentiality

Each document is encrypted at rest using AES-256-GCM with a randomly generated 12-byte nonce.

Conceptually:

ciphertext = AESGCM(key).encrypt(
    nonce,
    plaintext,
    None
)

The encryption key and nonce are maintained separately from the original plaintext document.

SHA-256 — Integrity

A SHA-256 digest is calculated when the document is uploaded.

document → SHA-256 → stored_hash

During download, the decrypted bytes are hashed again:

encrypted file
      ↓
   decrypt
      ↓
plaintext bytes
      ↓
   SHA-256
      ↓
recomputed_hash
      ↓
compare with stored_hash

Any byte-level modification results in a different digest and causes the integrity verification to fail.

Ed25519 — Non-Repudiation

Each user receives a persistent Ed25519 keypair.

User
 ├── Private Key → signs uploaded documents
 └── Public Key  → verifies document signatures

Every document is signed by the uploader's private key. The corresponding public key is used for verification.

Hash-Chained Audit Ledger

Audit events are stored in an append-only JSON ledger.

Each entry contains its own hash and the hash of the previous entry.

Entry 0
  │
  └── hash ──► Entry 1
                │
                └── hash ──► Entry 2
                              │
                              └── hash ──► Entry 3
Hash Formula
entry[i].hash =
    SHA256(
        index[i] ||
        timestamp[i] ||
        prev_hash[i] ||
        event_type[i] ||
        payload[i] ||
        actor[i]
    )

The first entry uses an all-zero previous hash:

prev_hash[0] = "0000...0000"
Hash Chain Pseudocode
GENESIS_HASH = "0000...0000"

function append_event(index, timestamp, event_type, payload, actor):

    if ledger is empty:
        prev_hash = GENESIS_HASH
    else:
        prev_hash = ledger[last].hash

    data = (
        index ||
        timestamp ||
        prev_hash ||
        event_type ||
        payload ||
        actor
    )

    current_hash = SHA256(data)

    entry = {
        index: index,
        timestamp: timestamp,
        prev_hash: prev_hash,
        event_type: event_type,
        payload: payload,
        actor: actor,
        hash: current_hash
    }

    append entry to ledger
Chain Verification
function verify_chain(ledger):

    expected_prev = GENESIS_HASH

    for entry in ledger:

        if entry.prev_hash != expected_prev:
            return TAMPERED

        expected_hash = SHA256(
            entry.index ||
            entry.timestamp ||
            entry.prev_hash ||
            entry.event_type ||
            entry.payload ||
            entry.actor
        )

        if entry.hash != expected_hash:
            return TAMPERED

        expected_prev = entry.hash

    return VALID

Modifying any historical entry changes its calculated hash and breaks the chain. SAT-DMS detects this during ledger verification.

7. Security Properties
Security Property	Mechanism	Verification
Confidentiality	AES-256-GCM	Decryption requires the local encryption key
File integrity	SHA-256	Hash recomputed and compared during verification/download
Authenticity	Ed25519 signature	Signature verified against uploader public key
Non-repudiation	Persistent per-user Ed25519 keypair	Document linked cryptographically to uploader
Audit integrity	SHA-256 hash chain	Every ledger entry validated against its predecessor
Auditability	Append-only audit ledger	Historical actions remain traceable
Access control	Flask-Login + RBAC	Permissions enforced by user role
Version integrity	Document version chains	Previous versions remain preserved
Traceability	Actor + timestamp + event + payload	Actions can be reconstructed from ledger records
Offline security	Local-only architecture	No cloud, external API, or telemetry dependency
8. Tech Stack
Component	Technology
Language	Python 3.8+
Web Framework	Flask 3.0
ORM / Database	Flask-SQLAlchemy 3.1 + SQLite
Authentication	Flask-Login 0.6
Encryption	cryptography 47.x — AES-256-GCM
Hashing	SHA-256
Digital Signatures	Ed25519 via cryptography
Password Security	Passlib + Werkzeug
Frontend	Jinja2 + Vanilla CSS
PDF Support	pypdf — reserved for future text extraction
Storage	Local encrypted file storage
Audit Ledger	Append-only JSON + SHA-256 hash chaining
9. Project Layout
sat-dms/
├── app/
│   ├── __init__.py            # Flask application factory
│   ├── models.py              # User, Case, Document
│   │
│   ├── crypto/
│   │   ├── encryption.py      # AES-256-GCM
│   │   └── signatures.py      # Ed25519 keypair, sign, verify
│   │
│   ├── ledger/
│   │   └── chain.py           # Hash-chained append-only audit log
│   │
│   ├── routes/
│   │   ├── auth.py            # Login, logout, first-run setup
│   │   ├── documents.py       # Upload, view, download, verify,
│   │   │                      # search, versioning
│   │   ├── cases.py           # Case management
│   │   ├── audit.py           # Ledger viewer
│   │   └── admin.py           # User management
│   │
│   ├── templates/             # 14 Jinja2 templates
│   └── static/
│       └── style.css
│
├── config.py
├── run.py
├── requirements.txt
│
├── storage/
│   ├── encrypted/             # Gitignored encrypted documents
│   └── keys/                  # Gitignored cryptographic keys
│
├── instance/                  # Gitignored runtime data
│   ├── SQLite database
│   └── audit_chain.json
│
└── docs/
10. Deployment

SAT-DMS is designed for offline and air-gapped deployment.

┌──────────────────────────────────────┐
│          AIR-GAPPED ENVIRONMENT      │
│                                      │
│  ┌──────────────┐    ┌────────────┐  │
│  │ Local Client │───►│ SAT-DMS    │  │
│  └──────────────┘    │ Flask App  │  │
│                      └─────┬──────┘  │
│                            │         │
│                  ┌─────────┴──────┐  │
│                  │ Local Storage  │  │
│                  │ SQLite         │  │
│                  │ Encrypted Docs │  │
│                  │ Audit Ledger   │  │
│                  └────────────────┘  │
└──────────────────────────────────────┘

SAT-DMS does not require:

Cloud infrastructure
Internet connectivity
External APIs
SaaS services
Remote key-management services
External telemetry
Public blockchain infrastructure

All application processing, metadata, encrypted documents, cryptographic keys, and audit records remain within the local deployment environment.

11. Roadmap
 Complete 2-page SIH architecture document
 Add comprehensive automated security and integrity tests
 Expand RBAC and permission granularity
 Add configurable document retention policies
 Add advanced case-level audit views
 Add PDF text extraction using pypdf
 Add document metadata integrity verification
 Add stronger key lifecycle and backup procedures
 Add exportable audit and case reports
 Add offline deployment/package installer
 Add validation and demonstration dataset
 Complete SIH technical presentation and demo video
12. SIH 2026 Deliverables
Deliverable	Status
Source code	[x] Complete
README with setup instructions	[x] Complete
Architecture document — max 2 pages	[ ] Pending
Demo video — max 2 minutes	[ ] Pending
Technical presentation — max 5 slides	[ ] Pending
13. License

This project is licensed under the MIT License.
