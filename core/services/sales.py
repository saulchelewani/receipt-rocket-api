from typing import Any

import httpx
from fastapi import HTTPException

from core.settings import settings


async def submit_transaction(transaction) -> dict[str, Any]:
    try:
        async with httpx.AsyncClient(timeout=settings.MRA_EIS_TIMEOUT) as client:
            response = await client.post(
                f"{settings.MRA_EIS_URL}/sales/submit-sales-transaction",
                json=transaction,
            )
            return response.json()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error submitting transaction: {str(e)}")
