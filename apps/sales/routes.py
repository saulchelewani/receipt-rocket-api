from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import constr
from sqlalchemy.orm import Session
from starlette import status

from apps.sales.schema import TransactionRequest
from core.auth import get_current_user
from core.database import get_db
from core.models import User, Terminal, GlobalConfig, Product
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

    global_config = db.query(GlobalConfig).first()
    if not global_config:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Config is not saved")

    tax_breakdown = {}
    total_vat = 0
    invoice_total = 0
    line_items = []

    for item in request.invoice_line_items:
        product = db.query(Product).filter(Product.code == item.product_code).first()
        if not product:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Product not found")

        # TODO fetch tax rate

        rate_id = item.tax_rate_id
        taxable_amount = product.unit_price * item.quantity
        tax_amount = taxable_amount * item.tax_rate

        if rate_id not in tax_breakdown:
            tax_breakdown[rate_id] = {
                "taxableAmount": 0,
                "taxAmount": 0
            }

        tax_breakdown[rate_id]["taxableAmount"] += taxable_amount
        tax_breakdown[rate_id]["taxAmount"] += tax_amount
        total_vat += tax_amount
        invoice_total += item.total

        line_items.append({
            "id": 0,
            "productCode": item.product_code,
            "description": product.description,
            "unitPrice": product.unit_price,
            "quantity": item.quantity,
            "discount": 0,
            "total": 0,
            "totalVAT": tax_amount,
            "taxRateId": "string",
            "isProduct": True
        })

    tax_breakdown_list = []
    for rate_id, breakdown in tax_breakdown.items():
        tax_breakdown_list.append({
            "rateId": rate_id,
            "taxableAmount": breakdown["taxableAmount"],
            "taxAmount": breakdown["taxAmount"]
        })

    invoice = {
        "invoiceHeader": {
            "invoiceNumber": generate_invoice_number(),
            "invoiceDateTime": datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            "sellerTIN": terminal.tenant.tin,
            "buyerTIN": request.buyer_tin,
            "buyerName": request.buyer_name,
            "buyerAuthorizationCode": request.buyer_authorization_code,
            "siteId": "string",
            "globalConfigVersion": global_config.version,
            "taxpayerConfigVersion": terminal.tenant.version,
            "terminalConfigVersion": terminal.version,
            "isReliefSupply": request.is_relief_supply,
            "vat5CertificateDetails": {
                "id": 0,
                "projectNumber": "string",
                "certificateNumber": "string",
                "quantity": 0
            },
            "paymentMethod": request.payment_method
        },
        "invoiceLineItems": line_items,
        "invoiceSummary": {
            "taxBreakDown": tax_breakdown_list,
            "totalVAT": total_vat,
            "offlineSignature": "string",
            "invoiceTotal": invoice_total
        }
    }

    print(invoice)
    return request
