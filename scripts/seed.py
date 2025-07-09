from core import Base
from core.database import engine, SessionLocal
from core.seeders.dictionary_seeder import seed_dictionary
from core.seeders.roles_seeder import seed_roles
from core.seeders.user_seeder import seed_users


def run():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_dictionary(db)
        print("✅ Dictionary seeded.")
        seed_roles(db)
        print("✅ Roles seeded.")
        seed_users(db)
        print("✅ Users seeded.")
    finally:
        db.close()


if __name__ == "__main__":
    run()
