from fastapi import Depends, APIRouter
from sqlalchemy.orm import Session

from apps.activation.schema import TerminalActivationRequest
from core.auth import get_tenant
from core.database import get_db
from core.models import Tenant
from core.services.activation import activate_terminal

router = APIRouter(
    prefix="/activation",
    tags=["Activation"],
    responses={404: {"description": "Not found"}},
)

@router.post("/activate")
def activate(request: TerminalActivationRequest, db: Session = Depends(get_db), tenant: Tenant = Depends(get_tenant)):
    terminal = activate_terminal(request.terminalActivationCode, tenant, db)
    return {"message": "Terminal activated", "terminal_id": terminal.terminal_id}
