from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import constr
from sqlalchemy.orm import Session
from starlette import status

from apps.terminals.schema import UnblockStatusResponse
from core.auth import get_current_user
from core.database import get_db
from core.models import Terminal
from core.services.blocking import get_unblock_status

router = APIRouter(
    prefix="/terminals",
    tags=["Terminals"],
    responses={404: {"description": "Not found"}},
)


@router.get("/unblock-status", dependencies=[Depends(get_current_user)], response_model=UnblockStatusResponse)
async def get_terminal_unblock_status(
        x_device_id: Annotated[constr(pattern="^\w{16}$"), Header(..., description="Device ID of the terminal")],
        db: Session = Depends(get_db),
):
    terminal = db.query(Terminal).filter(Terminal.device_id == x_device_id).first()
    if not terminal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Terminal not found"
        )

    unblock_status = await get_unblock_status(terminal)
    if unblock_status.is_unblocked():
        terminal.is_blocked = False
        terminal.blocking_reason = None
        db.commit()
    return {
        "is_unblocked": unblock_status.is_unblocked(),
        "details": terminal.blocking_reason if terminal.is_blocked else "Terminal is unblocked"
    }
