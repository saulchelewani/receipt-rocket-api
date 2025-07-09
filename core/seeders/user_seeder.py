from sqlalchemy.orm import Session

from core import Role, User
from core.enums import Scope, StatusEnum, RoleEnum
from core.settings import settings

SEED_USERS = [
    {
        "email": "test@example.com",
        "name": "John Doe",
        "phone_number": "0881245194",
        "hashed_password": settings.TEST_HASH,
        "scope": Scope.GLOBAL,
        "status": StatusEnum.ACTIVE
    },
]


def seed_users(db: Session):
    global_admin = db.query(Role).filter(Role.name == RoleEnum.GLOBAL_ADMIN).first()
    if not global_admin:
        global_admin = Role(name=RoleEnum.GLOBAL_ADMIN)
        db.add(global_admin)
        db.commit()
        db.refresh(global_admin)

    for entry in SEED_USERS:
        user = db.query(User).filter(User.email == entry["email"]).first()
        if not user:
            db.add(User(**entry, role_id=global_admin.id))
    db.commit()
