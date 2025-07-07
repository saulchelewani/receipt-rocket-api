from core import Base
from core.database import engine, SessionLocal
from core.seeders.dictionary_seeder import seed_dictionary


def run():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_dictionary(db)
        print("✅ Dictionary seeded.")
    finally:
        db.close()


if __name__ == "__main__":
    run()
