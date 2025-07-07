from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core import Dictionary
from core.database import get_db

router = APIRouter(
    prefix="/dictionary",
    tags=["Dictionary"],
    responses={404: {"description": "Not found"}},
)


class DictionaryBase(BaseModel):
    term: int
    definition: str


class DictionaryRead(DictionaryBase):
    id: UUID


@router.get("/", response_model=list[DictionaryBase])
async def get_dictionary(db: Session = Depends(get_db)):
    return db.query(Dictionary).all()
