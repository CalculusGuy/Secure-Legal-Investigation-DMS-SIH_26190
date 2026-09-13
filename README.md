SAT-DMS — Secure Digital Document Management System

SIH 2026 · PS 26190 · MHA (NCRB) · Blockchain & Cybersecurity

Offline, tamper-evident document management for FIRs, witness statements, charge sheets, forensic reports and case files.

Core Workflow
          UPLOAD
             │
             ▼
     ┌───────────────┐
     │ Document File │
     └───────┬───────┘
             │
     ┌───────┼────────┬──────────┐
     ▼       ▼        ▼          ▼
   SHA-256 AES-256   Ed25519   Metadata
   Hash     GCM      Signature    │
     │       │        │           │
     └───────┴────────┴───────────┘
                     │
                     ▼
              AUDIT LEDGER
                     │
                     ▼
             Version + Case
Security by Design
Layer	Protection
🔐 Confidentiality	AES-256-GCM at rest
🧬 Integrity	SHA-256 on upload/download
✍️ Non-repudiation	Ed25519 uploader signature
⛓️ Audit integrity	SHA-256 hash-chained ledger
👤 Access control	Admin / Investigator / Viewer RBAC
🔎 Search	Title / Case / Hash / Uploader / Description
Requirement Mapping
Centralized Storage ─────► SQLite + Encrypted Files
Secure Access ───────────► Login + RBAC + AES-256-GCM
Unauthorized Changes ───► SHA-256 + Ed25519
Complete Audit Trail ───► Hash-Chained Ledger
Efficient Search ───────► Multi-field Search
Collaboration ──────────► RBAC + Version Chains
Case Management ────────► Case → Document Relationships
Audit Chain
┌─────────┐      ┌─────────┐      ┌─────────┐
│ Entry 0 │─────►│ Entry 1 │─────►│ Entry 2 │─────► ...
│ hash    │      │ hash    │      │ hash    │
│ 0000... │      │ prev=E0 │      │ prev=E1 │
└─────────┘      └─────────┘      └─────────┘
entry[i].hash =
SHA256(
    index ||
    timestamp ||
    prev_hash ||
    event_type ||
    payload ||
    actor
)
MODIFY HISTORY
      │
      ▼
Recalculate Hash
      │
      ▼
Hash ≠ Stored Hash
      │
      ▼
⚠ TAMPERING DETECTED
Integrity Verification
DOWNLOAD
   │
   ▼
Decrypt AES-GCM
   │
   ▼
Recalculate SHA-256
   │
   ├── MATCH ──► ✓ Integrity Valid
   │
   └── MISMATCH ► ✗ Download Blocked
5-Minute Demo
1. Setup Admin
      ↓
2. Create Case: FIR-2026-0001
      ↓
3. Upload Document
      ↓
4. Verify SHA-256 + Ed25519
      ↓
5. Download / Search
      ↓
6. Open Audit Ledger
      ↓
7. Upload v2
      ↓
8. Tamper with audit_chain.json
      ↓
9. Restart → TAMPERING DETECTED
Run Locally
git clone https://github.com/CalculusGuy/Secure-Legal-Investigation-DMS-SIH_26190.git
cd Secure-Legal-Investigation-DMS-SIH_26190
python -m venv .venv
.venv\Scripts\activate.bat
pip install -r requirements.txt
python run.py

Open http://127.0.0.1:5000

Architecture
                    SAT-DMS
                       │
              ┌────────┴────────┐
              │ Authentication  │
              │      + RBAC     │
              └────────┬────────┘
                       │
          ┌────────────┴────────────┐
          ▼                         ▼
   Case Management            Document Engine
          │                         │
          │              ┌──────────┼──────────┐
          │              ▼          ▼          ▼
          │           Encrypt     Hash       Sign
          │           AES-GCM    SHA-256    Ed25519
          │              │          │          │
          └──────────────┴──────────┴──────────┘
                              │
                    ┌─────────┴─────────┐
                    ▼                   ▼
              SQLite Metadata     Encrypted Store
                    │
                    ▼
              Audit Ledger
             SHA-256 Chain
Project Structure
sat-dms/
├── app/
│   ├── crypto/
│   │   ├── encryption.py
│   │   └── signatures.py
│   ├── ledger/chain.py
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
Tech Stack
Python 3.8+
    │
    ├── Flask 3.0
    ├── Flask-SQLAlchemy + SQLite
    ├── Flask-Login
    ├── cryptography
    │     ├── AES-256-GCM
    │     ├── SHA-256
    │     └── Ed25519
    ├── Passlib + Werkzeug
    ├── Jinja2
    └── Vanilla CSS
Offline / Air-Gapped
        ┌─────────────────────────┐
        │     AIR-GAPPED HOST     │
        │                         │
        │  SAT-DMS ──► SQLite     │
        │      │ └──► Encrypted   │
        │      │     Documents    │
        │      └────► Audit Chain │
        │                         │
        └─────────────────────────┘

No cloud · No external API · No SaaS · No telemetry · No Internet dependency

Roadmap
 Complete architecture document
 Automated security test suite
 Advanced RBAC policies
 PDF text extraction
 Case-level audit reports
 Offline deployment package
 SIH validation dataset
SIH 2026 Deliverables
 Source Code
 README
 Architecture Document — 2 pages
 Demo Video — 2 minutes
 Technical Presentation — 5 slides
License

MIT License.
