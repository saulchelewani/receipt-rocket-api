from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import constr
from sqlalchemy.orm import Session
from starlette import status

from apps.sales.schema import TransactionRequest
from core.auth import get_current_user
from core.database import get_db
from core.models import User, Terminal
from core.utils import generate_invoice_number

router = APIRouter(
    prefix="/sales",
    tags=["Sales Transactions"],
    responses={404: {"description": "Not found"}},
)


@router.post("/")
async def submit_a_transaction(
        request: TransactionRequest,
        x_device_id: Annotated[constr(pattern="^\w{16}$"), Header()],
        user: User = Depends(get_current_user),
        db: Session = Depends(get_db)):
    terminal = db.query(Terminal).filter(Terminal.device_id == x_device_id).first()
    if not terminal:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Device ID is not recognized")

    if not terminal.tenant.tin:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Config is not saved")

    invoice = {
        "invoiceHeader": {
            "invoiceNumber": generate_invoice_number(),
            "invoiceDateTime": datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            "sellerTIN": terminal.tenant.tin,
            "buyerTIN": request.buyer_tin,
            "buyerName": request.buyer_name,
            "buyerAuthorizationCode": request.buyer_authorization_code,
            "siteId": "string",
            "globalConfigVersion": 0,
            "taxpayerConfigVersion": 0,
            "terminalConfigVersion": 0,
            "isReliefSupply": request.is_relief_supply,
            "vat5CertificateDetails": {
                "id": 0,
                "projectNumber": "string",
                "certificateNumber": "string",
                "quantity": 0
            },
            "paymentMethod": "string"
        },
        "invoiceLineItems": [
            {
                "id": 0,
                "productCode": "string",
                "description": "string",
                "unitPrice": 0,
                "quantity": 0,
                "discount": 0,
                "total": 0,
                "totalVAT": 0,
                "taxRateId": "string",
                "isProduct": True
            }
        ],
        "invoiceSummary": {
            "taxBreakDown": [
                {
                    "rateId": "string",
                    "taxableAmount": 0,
                    "taxAmount": 0
                }
            ],
            "totalVAT": 0,
            "offlineSignature": "string",
            "invoiceTotal": 0
        }
    }

    print(invoice)
    return request
