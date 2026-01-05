from app.core.security.passwords import hash_password
from app.domain.users.entities.user import User
from app.infrastructure.sqlalchemy.repositories.users_repository_sqlalchemy import (
    SQLAlchemyUsersRepository,
)
from app.infrastructure.sqlalchemy.session import SessionLocal


ADMINS = [
    {"username": "admin1", "password": "admin1pass"},
    {"username": "admin2", "password": "admin2pass"},
]


def seed_admins():
    db = SessionLocal()

    try:
        repo = SQLAlchemyUsersRepository(db)

        email = "admin@sereiatattoo.dev"
        password = "admin123"
        hashed_password = hash_password(password)

        existing = repo.find_by_email(email)
        if existing:
            print("admin ja existe")
            return

        user = User(
            email=email,
            username="admin",
            hashed_password=hashed_password,
            is_admin=True,
            is_active=True,
            has_activated_once=True,
        )

        repo.create(user)
        db.commit()

        print("Admin criado com sucesso")
        print(f"Email: {email}")
        print(f"Senha: {password}")

    finally:
        db.close()


if __name__ == "__main__":
    seed_admins()
