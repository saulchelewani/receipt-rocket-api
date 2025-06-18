from typing import Any

import httpx
from fastapi import HTTPException
from sqlalchemy.orm import Session

from core.models import Tenant
from core.settings import settings


async def get_configuration():
    headers = {
        "accept": "application/json",
    }
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.MRA_EIS_URL}/api/v1/configuration/get-latest-configs",
                timeout=settings.MRA_EIS_TIMEOUT,
                headers=headers)

        return response.json()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


def save_tax_payer_config(db: Session, tenant: Tenant, tax_payer_config: dict[str, Any]) -> Tenant:
    if tenant.config_version == tax_payer_config['versionNo']:
        return tenant

    profile_dict = {
        'tin': tax_payer_config['tin'],
        'version': tax_payer_config['versionNo'],
        'vat_registered': tax_payer_config['isVATRegistered'],
        'tax_office_code': tax_payer_config['taxOffice']['code'],
        'tax_office_name': tax_payer_config['taxOffice']['name'],
        'activated_tax_rate_ids': tax_payer_config['activatedTaxRateIds'],
        'config_version': tax_payer_config['versionNo']
    }
    for key, value in profile_dict.items():
        setattr(tenant, key, value)

    db.commit()
    return tenant
