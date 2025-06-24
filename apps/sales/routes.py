import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import constr
from sqlalchemy.orm import Session
from starlette import status

from apps.sales.schema import TransactionRequest
from core.auth import get_current_user
from core.database import get_db
from core.models import Terminal, GlobalConfig, Product, TaxRate
from core.services.sales import submit_transaction
from core.utils import generate_invoice_number, calculate_tax

router = APIRouter(
    prefix="/sales",
    tags=["Sales Transactions"],
    responses={404: {"description": "Not found"}},
)


@router.post("/", dependencies=[Depends(get_current_user)])
async def submit_a_transaction(
        request: TransactionRequest,
        x_device_id: Annotated[constr(pattern="^\w{16}$"), Header(..., description="Device ID of the terminal")],
        db: Session = Depends(get_db)):
    terminal = db.query(Terminal).filter(Terminal.device_id == x_device_id).first()
    if not terminal:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Device ID is not recognized")

    if not terminal.tenant.tin:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tax payer config is not saved")

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

        db_tax_rate = db.query(TaxRate).filter(TaxRate.rate_id == product.tax_rate_id).first()
        if not db_tax_rate:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tax rate not found")

        amount = product.unit_price * item.quantity

        rate_id = db_tax_rate.rate_id
        taxable_amount = calculate_tax(amount, db_tax_rate.rate)
        taxable_unit_price = calculate_tax(product.unit_price, db_tax_rate.rate)
        tax_amount = amount - taxable_amount

        if rate_id not in tax_breakdown:
            tax_breakdown[rate_id] = {
                "taxableAmount": 0,
                "taxAmount": 0
            }

        tax_breakdown[rate_id]["taxableAmount"] += taxable_amount
        tax_breakdown[rate_id]["taxAmount"] += tax_amount
        total_vat += tax_amount
        invoice_total += amount

        line_items.append({
            "id": str(uuid.uuid4()),
            "productCode": item.product_code,
            "description": product.description,
            "unitPrice": round(taxable_unit_price, 2),
            "quantity": item.quantity,
            "discount": 0,
            "total": round(taxable_amount, 2),
            "totalVAT": round(tax_amount, 2),
            "taxRateId": db_tax_rate.rate_id,
            "isProduct": product.is_product
        })

    tax_breakdown_list = []
    for rate_id, breakdown in tax_breakdown.items():
        tax_breakdown_list.append({
            "rateId": rate_id,
            "taxableAmount": round(breakdown["taxableAmount"], 2),
            "taxAmount": round(breakdown["taxAmount"], 2),
        })

    invoice = {
        "invoiceHeader": {
            "invoiceNumber": generate_invoice_number(int(terminal.tenant.tin), 1, datetime.now(), 1),
            "invoiceDateTime": datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            "sellerTIN": terminal.tenant.tin,
            "buyerTIN": request.buyer_tin,
            "buyerName": request.buyer_name,
            "buyerAuthorizationCode": request.buyer_authorization_code,
            "siteId": None,
            "globalConfigVersion": global_config.version,
            "taxpayerConfigVersion": terminal.tenant.config_version,
            "terminalConfigVersion": terminal.config_version,
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
            "totalVAT": round(total_vat, 2),
            "offlineSignature": None,
            "invoiceTotal": invoice_total
        }
    }

    try:
        response = await submit_transaction(invoice)
        if response["statusCode"] != 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=response["remark"])
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return response
