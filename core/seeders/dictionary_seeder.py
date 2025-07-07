from sqlalchemy.orm import Session

from core import Dictionary

SEED_ENTRIES = [
    {"term": 1001, "definition": "Active"},
    {"term": 1002, "definition": "Change password"},
    {"term": 1003, "definition": "Suspended"},
]


def seed_dictionary(db: Session):
    for entry in SEED_ENTRIES:
        exists = db.query(Dictionary).filter(Dictionary.term == entry["term"]).first()
        if not exists:
            db.add(Dictionary(**entry))
    db.commit()
