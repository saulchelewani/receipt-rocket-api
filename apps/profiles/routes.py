from fastapi import APIRouter

router = APIRouter(
    prefix="/profiles",
    tags=["Profiles"],
    responses={404: {"description": "Not found"}},
)
