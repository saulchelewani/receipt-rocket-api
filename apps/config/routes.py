from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core.auth import get_current_user
from core.database import get_db
from core.models import User, TaxRate, Terminal, Profile
from core.services.config import get_configuration

router = APIRouter(
    prefix="/config",
    tags=["Config"],
    responses={404: {"description": "Not found"}},
)


@router.get("/{terminal_id}")
async def get_config(terminal_id: UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    tenant = user.tenant
    if not tenant:
        raise HTTPException(status_code=400, detail="Tenant not found")

    config = await get_configuration()

    global_config = config["data"]["globalConfiguration"]
    save_tax_rates(db, global_config.get("taxRates", []))

    terminal = db.query(Terminal).filter(Terminal.id == terminal_id).first()
    if not terminal:
        raise HTTPException(status_code=400, detail="Terminal not found")

    terminal_config = config["data"]["terminalConfiguration"]
    save_terminal_config(db, terminal, terminal_config)

    tax_payer_config = config["data"]["taxpayerConfiguration"]
    save_tax_payer_config(db, terminal, tax_payer_config)
    return config


def save_tax_rates(db: Session, tax_rates: list[dict]) -> None:
    for rate_data in tax_rates:
        try:
            existing_rate = db.query(TaxRate).filter(TaxRate.name == rate_data["name"]).first()
            if existing_rate:
                setattr(existing_rate, 'rate', rate_data.get('rate'))
                setattr(existing_rate, 'ordinal', rate_data.get('ordinal', 0))
                setattr(existing_rate, 'charge_mode', rate_data.get('chargeMode', 'G'))
            else:
                tax_rate = TaxRate(
                    rate_id=rate_data['id'],
                    name=rate_data['name'],
                    rate=rate_data.get('rate'),
                    ordinal=rate_data.get('ordinal', 0),
                    charge_mode=rate_data.get('chargeMode', 'G')
                )
                db.add(tax_rate)
            db.commit()
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=str(e))


def save_terminal_config(db: Session, terminal, terminal_config: dict) -> None:
    setattr(terminal, 'trading_name', terminal_config['tradingName'])
    setattr(terminal, 'email', terminal_config['emailAddress'])
    setattr(terminal, 'phone_number', terminal_config['phoneNumber'])
    setattr(terminal, 'label', terminal_config['terminalLabel'])
    setattr(terminal, 'version', terminal_config['versionNo'])
    setattr(terminal, 'address_lines', terminal_config['addressLines'])
    setattr(terminal, 'offline_limit_hours', terminal_config['offlineLimit']['maxTransactionAgeInHours'])
    setattr(terminal, 'offline_limit_amount', terminal_config['offlineLimit']['maxCummulativeAmount'])

    db.commit()


def save_tax_payer_config(db: Session, terminal: Terminal, tax_payer_config: dict) -> None:
    profile = terminal.tenant.profile
    profile_dict = {
        'tin': tax_payer_config['tin'],
        'version': tax_payer_config['versionNo'],
        'vat_registered': tax_payer_config['isVATRegistered'],
        'tax_office_code': tax_payer_config['taxOffice']['code'],
        'tax_office_name': tax_payer_config['taxOffice']['name'],
        'activated_tax_rate_ids': tax_payer_config['activatedTaxRateIds']
    }
    if not profile:
        profile = Profile(**profile_dict, tenant_id=terminal.tenant_id)
        db.add(profile)
    else:
        for key, value in profile_dict.items():
            setattr(profile, key, value)

    db.commit()
