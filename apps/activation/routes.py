from fastapi import Depends, APIRouter
from sqlalchemy.orm import Session

from apps.activation.schema import TerminalActivationRequest
from core.database import get_db
from core.services.activation import activate_terminal

router = APIRouter(
    prefix="/activation",
    tags=["Activation"],
    responses={404: {"description": "Not found"}},
)

@router.post("/activate")
def activate(request: TerminalActivationRequest, db: Session = Depends(get_db)):
    terminal = activate_terminal(request.terminalActivationCode, db)
    return {"message": "Terminal activated", "terminal_id": terminal.terminal_id}
