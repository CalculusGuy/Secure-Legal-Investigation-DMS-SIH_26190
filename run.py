"""
SAT-DMS entry point.
Run:  python run.py
"""
from app import create_app, db

app = create_app()

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        print("[+] Database ready")
    print("[+] Starting SAT-DMS on http://127.0.0.1:7777")
    app.run(host="127.0.0.1", port=7777, debug=True)
