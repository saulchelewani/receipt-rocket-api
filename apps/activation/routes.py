from typing import Annotated

from fastapi import Depends, APIRouter, Header, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from apps.activation.schema import TerminalActivationRequest, TerminalConfirmationRequest, TerminalRead, \
    TerminalConfigurationRead
from core.auth import get_tenant
from core.database import get_db
from core.models import Tenant, Terminal
from core.services.activation import activate_terminal, confirm_terminal_activation

router = APIRouter(
    prefix="/activation",
    tags=["Activation"],
    responses={404: {"description": "Not found"}},
)


@router.post("/activate", response_model=TerminalConfigurationRead)
async def activate(
        request: TerminalActivationRequest,
        db: Session = Depends(get_db),
        x_mac_address: Annotated[str | None, Header(), None] = None,
        tenant: Tenant = Depends(get_tenant)):
    terminal = activate_terminal(request.terminal_activation_code, tenant, db, x_mac_address)
    return terminal.configurations


@router.post("/confirm", response_model=TerminalRead)
async def confirm_activation(
        request: TerminalConfirmationRequest,
        db: Session = Depends(get_db),
):
    terminal = db.query(Terminal).filter(Terminal.id == request.terminal_id).first()

    if not terminal:
        raise HTTPException(status_code=400, detail="Terminal not found")

    response = await confirm_terminal_activation(terminal)

    if response["statusCode"] != 1:
        raise HTTPException(status_code=400, detail=response["remark"])

    terminal.confirmed_at = func.now()
    db.commit()
    db.refresh(terminal)
    return terminal
