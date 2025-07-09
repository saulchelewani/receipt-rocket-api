from core import Role
from core.enums import RoleEnum

SEED_ENTRIES = [
    {"name": RoleEnum.GLOBAL_ADMIN, "description": "Global Admin"},
    {"name": RoleEnum.ADMIN, "description": "Tenant Admin"},
    {"name": RoleEnum.USER, "description": "Tenant User"},
]


def seed_roles(db):
    for entry in SEED_ENTRIES:
        role = db.query(Role).filter(Role.name == entry["name"]).first()
        if not role:
            db.add(Role(**entry))
    db.commit()
