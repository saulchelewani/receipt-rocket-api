import logging
from typing import Any

import httpx
from fastapi import HTTPException
from sqlalchemy.orm import Session

from core.models import Tenant
from core.settings import settings
from core.utils.api_logger import write_api_log, write_api_exception_log

logger = logging.getLogger(__name__)


async def get_configuration(terminal, db: Session):
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {terminal.token}",
    }
    try:
        async with httpx.AsyncClient() as client:
            url = f"{settings.MRA_EIS_URL}/configuration/get-latest-configs"
            response = await client.post(
                url,
                timeout=settings.MRA_EIS_TIMEOUT,
                headers=headers
            )
            await write_api_log(db, dict(), response, url, headers)
            response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Error getting configuration: {str(e)}")
        await write_api_exception_log(db, e, dict(), url, headers)
        raise HTTPException(status_code=400, detail=str(e))


def save_tax_payer_config(db: Session, tenant: Tenant, config: dict[str, Any]) -> Tenant:
    if tenant.config_version == config['versionNo']:
        return tenant

    profile_dict = {
        'tin': config['tin'],
        'version': config['versionNo'],
        'vat_registered': config['isVATRegistered'],
        'tax_office_code': config['taxOffice']['code'],
        'tax_office_name': config['taxOffice']['name'],
        'activated_tax_rate_ids': config['activatedTaxRateIds'],
        'config_version': config['versionNo']
    }
    for key, value in profile_dict.items():
        setattr(tenant, key, value)

    db.commit()
    return tenant
