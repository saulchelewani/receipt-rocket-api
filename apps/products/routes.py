import uuid
from datetime import datetime
from typing import Annotated

import httpx
from fastapi import APIRouter, Header, Depends, HTTPException
from sqlalchemy.orm import Session

from apps.products.schema import ProductRead
from core.auth import get_current_user
from core.database import get_db
from core.models import Terminal, Product
from core.settings import settings

router = APIRouter(
    prefix="/products",
    tags=["Products"],
    dependencies=[Depends(get_current_user)],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_model=list[ProductRead])
async def get_products(
        x_device_id: Annotated[str, Header()],
        db: Session = Depends(get_db)
):
    terminal = db.query(Terminal).filter(Terminal.device_id == x_device_id).first()
    if not terminal:
        raise HTTPException(status_code=400, detail="Terminal not found")

    if not terminal.tenant.tin:
        raise HTTPException(status_code=400, detail="Config is not saved")

    async with httpx.AsyncClient() as client:
        response = await client.post(f"{settings.MRA_EIS_URL}/utilities/get-terminal-site-products", json={
            "siteId": terminal.site_id,
            "tin": terminal.tenant.tin
        }, headers={
            "Content-Type": "application/json",
        })

        if int(response.json()["statusCode"]) < -1:
            raise HTTPException(status_code=400, detail=response.json()["remark"])

        products = response.json()["data"]

        response_products = []
        for product in products:
            product_in = {
                "tenant_id": terminal.tenant_id,
                "code": product["productCode"],
                "name": product["productName"],
                "description": product["description"],
                "quantity": product["quantity"],
                "is_product": product["isProduct"],
                "unit_of_measure": product["unitOfMeasure"],
                "unit_price": product["price"],
                "expiry_date": datetime.strptime(product["productExpiryDate"], "%Y-%m-%dT%H:%M:%S.%fZ"),
                "minimum_stock_level": product["minimumStockLevel"],
                "tax_rate_id": product["taxRateId"],
                "site_id": uuid.UUID(product["siteId"]),
            }
            response_products.append(product_in)
            if not db.query(Product).filter(Product.code == product["productCode"]).first():
                db.add(Product(**product_in))
                db.commit()
            else:
                db.query(Product).filter(Product.code == product["productCode"]).update(product_in)
                db.commit()

        products = db.query(Product).filter(Product.site_id == terminal.site_id,
                                            Product.tenant_id == terminal.tenant_id).all()
        return products
