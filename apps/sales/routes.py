from fastapi import APIRouter

from apps.sales.schema import TransactionRequest, TransactionResponse

router = APIRouter(
    prefix="/sales",
    tags=["Sales Transactions"],
    responses={404: {"description": "Not found"}},
)


@router.post("/", response_model=TransactionResponse)
async def submit_a_transaction(request: TransactionRequest):
    return request
