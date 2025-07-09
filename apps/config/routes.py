from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session

from apps.config.schema import ConfigResponse
from core.auth import get_current_user
from core.database import get_db
from core.models import User, TaxRate, Terminal
from core.services.activation import sync_global_config, sync_terminal_config
from core.services.config import get_configuration, save_tax_payer_config

router = APIRouter(
    prefix="/config",
    tags=["Config"],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_model=ConfigResponse)
async def get_config(
        user: User = Depends(get_current_user),
        x_device_id: str = Header(...),
        db: Session = Depends(get_db)
):
    tenant = user.tenant
    if not tenant:
        raise HTTPException(status_code=400, detail="Tenant not found")

    terminal = db.query(Terminal).filter(Terminal.device_id == x_device_id).first()
    if not terminal:
        raise HTTPException(status_code=400, detail="Terminal not found")

    config = await get_configuration(terminal, db)

    tax_rates = sync_global_config(db, config["data"]["globalConfiguration"])
    profile = save_tax_payer_config(db, tenant, config["data"]["taxpayerConfiguration"])
    terminal = sync_terminal_config(db, config["data"]["terminalConfiguration"], tenant, terminal.terminal_id)

    response = {
        "tax_rates": tax_rates,
        "tax_payer": profile,
        "terminal": terminal
    }
    return response


def save_tax_rates(db: Session, tax_rates: list[dict[str, Any]], config_id: UUID) -> list[TaxRate]:
    rates = []
    for rate_data in tax_rates:
        try:
            rate_dict = {
                'rate_id': rate_data['id'],
                'name': rate_data['name'],
                'rate': rate_data.get('rate'),
                'ordinal': rate_data.get('ordinal', 0),
                'charge_mode': rate_data.get('chargeMode', 'G'),
                'global_config_id': config_id
            }
            existing_rate = db.query(TaxRate).filter(TaxRate.name == rate_data["name"]).first()
            if existing_rate:
                for key, value in rate_dict.items():
                    setattr(existing_rate, key, value)
            else:
                tax_rate = TaxRate(**rate_dict)
                rates.append(tax_rate)
                db.add(tax_rate)
            db.commit()
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=str(e))
    return rates


def save_terminal_config(db: Session, terminal: Terminal, terminal_config: dict[str, Any]) -> Terminal:
    terminal_dict = {
        'trading_name': terminal_config['tradingName'],
        'email': terminal_config['emailAddress'],
        'phone_number': terminal_config['phoneNumber'],
        'label': terminal_config['terminalLabel'],
        'version': terminal_config['versionNo'],
        'address_lines': terminal_config['addressLines'],
        'offline_limit_hours': terminal_config['offlineLimit']['maxTransactionAgeInHours'],
        'offline_limit_amount': terminal_config['offlineLimit']['maxCummulativeAmount']
    }
    for key, value in terminal_dict.items():
        setattr(terminal, key, value)

    db.commit()
    return terminal
