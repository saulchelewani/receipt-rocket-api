import logging
from datetime import datetime
from typing import Annotated

import httpx
from fastapi import APIRouter, Header, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from starlette import status

from apps.products.schema import ProductRead
from core.auth import get_current_user
from core.database import get_db
from core.models import Terminal, Product, Tenant
from core.services.activation import write_api_log
from core.settings import settings

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/products",
    tags=["Products"],
    dependencies=[Depends(get_current_user)],
    responses={404: {"description": "Not found"}},
)


async def fetch_products_from_api(db: Session, terminal: Terminal | type[Terminal]) -> list[dict]:
    """Fetch products from the external API.

    Args:
        terminal: Merchant terminal
        db: Database session

    Returns:
        List of product dictionaries

    Raises:
        HTTPException: If the API request fails or returns an error
    """
    payload = {"siteId": terminal.site_id, "tin": terminal.tenant.tin}
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {terminal.token}"
    }
    try:
        async with httpx.AsyncClient(timeout=30.0, verify=False) as client:
            url = f"{settings.MRA_EIS_URL}/utilities/get-terminal-site-products"
            response = await client.post(
                url,
                json=payload,
                headers=headers,
            )
            await write_api_log(db, payload, response, url, headers)
            response.raise_for_status()

            data = response.json()
            if int(data.get("statusCode", 0)) < -1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=data.get("remark", "Failed to fetch products")
                )

            return data.get("data", [])

    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error fetching products: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to fetch products from external service"
        )
    except Exception as e:
        logger.error(f"Unexpected error fetching products: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


async def sync_products_with_db(db: Session, products_data: list[dict], tenant_id: Tenant.id,
                                site_id: Terminal.site_id) -> None:
    """Synchronize products in the database with the fetched data.

    Args:
        :param db: Database session
        :param products_data: List of product data from API
        :param tenant_id: Tenant ID to associate products with
        :param site_id: site ID to associate products with
    """
    try:
        existing_codes = {p['productCode'] for p in products_data if 'productCode' in p}
        existing_products = {p.code: p for p in db.query(Product).filter(Product.code.in_(existing_codes),
                                                                         Product.site_id == site_id).all()}

        for product_data in products_data:
            if not product_data.get('productCode'):
                continue

            product_dict = {
                "tenant_id": tenant_id,
                "code": product_data["productCode"],
                "name": product_data["productName"],
                "description": product_data.get("description"),
                "quantity": product_data.get("quantity", 0),
                "is_product": product_data.get("isProduct", True),
                "unit_of_measure": product_data.get("unitOfMeasure"),
                "unit_price": product_data.get("price", 0.0),
                "expiry_date": datetime.fromisoformat(product_data["productExpiryDate"]) if product_data.get(
                    "productExpiryDate") else None,
                "minimum_stock_level": product_data.get("minimumStockLevel", 0),
                "tax_rate_id": product_data.get("taxRateId"),
                "site_id": product_data["siteId"] if product_data.get("siteId") else site_id,
            }

            if product_dict["code"] in existing_products:
                # Update existing product
                for key, value in product_dict.items():
                    setattr(existing_products[product_dict["code"]], key, value)
            else:
                # Add new product
                db.add(Product(**product_dict))

        db.commit()

    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error syncing products: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to sync products with database"
        )


@router.get("/", response_model=list[ProductRead], summary="Get products for terminal")
async def get_products(
        x_device_id: Annotated[str, Header(..., description="Device ID of the terminal")],
        db: Session = Depends(get_db)
):
    """
    Retrieve products for a specific terminal.

    Fetches products from the external API, syncs them with the local database,
    and returns the products associated with the terminal's site.

    Args:
        x_device_id: The device ID of the terminal
        db: Database session dependency

    Returns:
        List of Product objects
    """
    terminal = db.query(Terminal).filter(Terminal.device_id == x_device_id).first()
    if not terminal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Terminal not found"
        )

    if not terminal.tenant or not terminal.tenant.tin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant configuration is incomplete"
        )

    try:
        # Fetch products from external API
        products_data = await fetch_products_from_api(
            db=db,
            terminal=terminal
        )

        # Sync with database
        if products_data:
            await sync_products_with_db(
                db=db,
                products_data=products_data,
                tenant_id=terminal.tenant_id,
                site_id=terminal.site_id
            )

        # Return products for the terminal's site
        return db.query(Product).filter(
            Product.site_id == terminal.site_id,
            Product.tenant_id == terminal.tenant_id
        ).all()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_products: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while processing your request"
        )


@router.get("/search", response_model=list[ProductRead])
async def search_products(
        name: str,
        x_device_id: Annotated[str, Header(..., description="Device ID of the terminal")],
        db: Session = Depends(get_db),
):
    terminal = db.query(Terminal).filter(Terminal.device_id == x_device_id).first()
    if not terminal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Terminal not found"
        )
    return db.query(Product).filter(
        func.lower(Product.name).contains(name),
        Product.site_id == terminal.site_id
    ).all()


@router.get("/{code}", summary="Get product by code", response_model=ProductRead)
async def get_product(
        code: str,
        x_device_id: Annotated[str, Header(..., description="Device ID of the terminal")],
        db: Session = Depends(get_db)):
    """
    Get product by bar code

    Args:
        code: The barcode of the product
        x_device_id: Device ID of the terminal
        db: Database session dependency

    Returns:
        The product
    """
    terminal = db.query(Terminal).filter(Terminal.device_id == x_device_id).first()
    if not terminal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Terminal not found"
        )
    product = db.query(Product).filter(Product.code == code, Product.site_id == terminal.site_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    return product
