"""
Promote a user to admin. Run once to bootstrap your first admin account.

Usage (from a Render shell, or locally with DATABASE_URL set):
    python -m scripts.make_admin your@email.com
"""
import sys
from app.database import SessionLocal
from app.models import User


def main(email: str):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            print(f"No user found with email {email}")
            return
        user.is_admin = True
        db.commit()
        print(f"{user.username} ({email}) is now an admin.")
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python -m scripts.make_admin <email>")
        sys.exit(1)
    main(sys.argv[1])
