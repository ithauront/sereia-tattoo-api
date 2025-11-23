from sqlalchemy.orm import Session
from app.db.models.users import User
from app.db.session import SessionLocal
from app.core.security.security import get_password_hash


ADMINS = [
    {"username": "admin1", "password": "admin1pass"},
    {"username": "admin2", "password": "admin2pass"},
]


def seed_admins(db: Session):
    for adm in ADMINS:
        user = db.query(User).filter(User.username == adm["username"]).first()
        if user:
            user.hashed_password = get_password_hash(adm["password"])
            user.is_admin = True
            db.add(user)
            continue
        user = User(
            username=adm["username"],
            hashed_password=get_password_hash(adm["password"]),
            is_admin=True,
        )
        db.add(user)
    db.commit()


if __name__ == "__main__":
    db = SessionLocal()
    try:
        seed_admins(db)
        print("Admins created/checked sucessfully")
    finally:
        db.close()
