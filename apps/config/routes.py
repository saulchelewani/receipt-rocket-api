from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from apps.config.schema import ConfigResponse
from core.auth import get_current_user
from core.database import get_db
from core.models import User, TaxRate, Terminal, Tenant, GlobalConfig
from core.services.config import get_configuration

router = APIRouter(
    prefix="/config",
    tags=["Config"],
    responses={404: {"description": "Not found"}},
)


@router.get("/{terminal_id}", response_model=ConfigResponse)
async def get_config(terminal_id: UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    tenant = user.tenant
    if not tenant:
        raise HTTPException(status_code=400, detail="Tenant not found")

    config = await get_configuration()

    global_config = config["data"]["globalConfiguration"]
    global_config_version = global_config["versionNo"]

    db_global_config = db.query(GlobalConfig).filter(GlobalConfig.version == global_config_version).first()
    if not db_global_config:
        db_global_config = GlobalConfig(version=global_config_version)
        db.add(db_global_config)
        db.commit()
        db.refresh(db_global_config)

    db_tax_rates = db.query(TaxRate).filter(TaxRate.global_config_id == db_global_config.id).all()
    if db_tax_rates:
        for rate in db_tax_rates:
            db.delete(rate)
        db.commit()

    rates = save_tax_rates(db, global_config.get("taxRates", []), db_global_config.id)

    terminal = db.query(Terminal).filter(Terminal.id == terminal_id).first()
    if not terminal:
        raise HTTPException(status_code=400, detail="Terminal not found")

    terminal_config = config["data"]["terminalConfiguration"]
    db_terminal = save_terminal_config(db, terminal, terminal_config)

    tax_payer_config = config["data"]["taxpayerConfiguration"]
    profile = save_tax_payer_config(db, tenant, tax_payer_config)

    response = {
        "tax_rates": rates,
        "tax_payer": profile,
        "terminal": db_terminal
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


def save_terminal_config(db: Session, terminal, terminal_config: dict) -> Terminal:
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


def save_tax_payer_config(db: Session, tenant: Tenant, tax_payer_config: dict[str, Any]) -> Tenant:
    profile_dict = {
        'tin': tax_payer_config['tin'],
        'version': tax_payer_config['versionNo'],
        'vat_registered': tax_payer_config['isVATRegistered'],
        'tax_office_code': tax_payer_config['taxOffice']['code'],
        'tax_office_name': tax_payer_config['taxOffice']['name'],
        'activated_tax_rate_ids': tax_payer_config['activatedTaxRateIds']
    }
    for key, value in profile_dict.items():
        setattr(tenant, key, value)

    db.commit()
    return tenant
