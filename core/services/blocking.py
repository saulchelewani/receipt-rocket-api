import httpx
from fastapi import HTTPException

from core.services.responses.block_status_response import BlockStatusResponse, UnblockStatusResponse
from core.settings import settings


async def get_blocking_message(terminal) -> BlockStatusResponse:
    headers = {
        "accept": "application/json",
        "Authorization": terminal.token,
        "Content-Type": "application/json"
    }

    try:
        async with httpx.AsyncClient(timeout=settings.MRA_EIS_TIMEOUT) as client:
            response = await client.post(
                f"{settings.MRA_EIS_URL}/utilities/get-terminal-blocking-message",
                json={
                    "terminalId": terminal.terminal_id
                },
                headers=headers
            )
            return BlockStatusResponse(response.json())
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error submitting transaction: {str(e)}")


async def get_unblock_status(terminal) -> UnblockStatusResponse:
    headers = {
        "accept": "application/json",
        "Authorization": terminal.token,
        "Content-Type": "application/json"
    }

    try:
        async with httpx.AsyncClient(timeout=settings.MRA_EIS_TIMEOUT) as client:
            response = await client.post(
                f"{settings.MRA_EIS_URL}/utilities/check-terminal-unblock-status",
                json={
                    "terminalId": terminal.terminal_id
                },
                headers=headers
            )
            return UnblockStatusResponse(response.json())
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error submitting transaction: {str(e)}")
