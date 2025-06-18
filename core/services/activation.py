import uuid

import httpx
from fastapi import HTTPException
from sqlalchemy.orm import Session

from core.models import Terminal, TaxRate, Tenant, GlobalConfig
from core.services.config import save_tax_payer_config
from core.settings import settings
from core.utils import sign_hmac_sha512, get_sequence_number


async def activate_terminal(code: str, tenant: Tenant, db: Session, x_mac_address: str | None = None):
    result = await activate_terminal_with_code(code, x_mac_address)

    if not result:
        raise HTTPException(status_code=400, detail="Terminal activation failed")

    sync_global_config(db, result["data"]["configuration"]["globalConfiguration"])
    save_tax_payer_config(db, tenant, result["data"]["configuration"]["taxpayerConfiguration"])
    return sync_terminal_config(db, result["data"]["configuration"]["terminalConfiguration"], tenant)


def sync_terminal_config(db: Session, config: dict, tenant: Tenant):
    db_terminal = db.query(Terminal).filter(Terminal.label == config['terminalLabel']).first()
    if db_terminal and db_terminal.config_version == config["versionNo"]:
        return db_terminal

    terminal_dict = {
        'tenant_id': tenant.id,
        'site_id': uuid.UUID(config['terminalSite']['siteId']),
        'trading_name': config['tradingName'],
        'email': config['emailAddress'],
        'phone_number': config['phoneNumber'],
        'label': config['terminalLabel'],
        'device_id': get_sequence_number() if not db_terminal else db_terminal.device_id,
        'config_version': config['versionNo'],
        'address_lines': config['addressLines'],
        'offline_limit_hours': config['offlineLimit']['maxTransactionAgeInHours'],
        'offline_limit_amount': config['offlineLimit']['maxCummulativeAmount']
    }

    if not db_terminal:
        db_terminal = Terminal(**terminal_dict)
        db.add(db_terminal)
        db.commit()
        db.refresh(db_terminal)
        return db_terminal

    for key, value in terminal_dict.items():
        setattr(db_terminal, key, value)

    db.commit()
    return db_terminal


async def confirm_terminal_activation(terminal):
    headers = {
        "accept": "text/plain",
        "x-signature": sign_hmac_sha512(terminal.terminal_id, terminal.secret_key),
        "Content-Type": "application/json"
    }

    payload = {
        "terminalId": terminal.terminal_id
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{settings.MRA_EIS_URL}/onboarding/terminal-activated-confirmation",
            headers=headers,
            json=payload)

        if int(response.json()["statusCode"]) < -1:
            raise HTTPException(status_code=400, detail=response.json()["remark"])

        return response.json()


async def activate_terminal_with_code(code: str, mac_address: str) -> dict:
    payload = {
        "terminalActivationCode": code,
        "environment": {
            "platform": {
                "osName": "Windows 11",
                "osVersion": "Windows 11",
                "osBuild": "11.901.2",
                "macAddress": mac_address
            },
            "pos": {
                "productID": settings.APP_NAME,
                "productVersion": str(settings.APP_VERSION),
            }
        }
    }
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.MRA_EIS_URL}/onboarding/activate-terminal",
                timeout=settings.MRA_EIS_TIMEOUT,
                json=payload
            )
            if int(response.json()["statusCode"]) < -1:
                raise HTTPException(status_code=400, detail=response.json()["remark"])
            return response.json()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


def sync_global_config(db: Session, config: dict):
    db_global_config = db.query(GlobalConfig).first()
    if db_global_config and db_global_config.version == config["versionNo"]:
        return db.query(TaxRate).all()

    if not db_global_config:
        db_global_config = GlobalConfig(version=config["versionNo"])
        db.add(db_global_config)
        db.commit()

    db_global_config.version = config["versionNo"]

    for tax in config["taxrates"]:
        db_rate = db.query(TaxRate).filter(TaxRate.name == tax["name"]).first()
        if db_rate:
            db_rate.rate = tax["rate"]
            db_rate.charge_mode = tax["chargeMode"]
            db_rate.ordinal = tax["ordinal"]
            db_rate.rate_id = tax["id"]
            continue
        tax_rate = TaxRate(
            rate_id=tax["id"],
            name=tax["name"],
            rate=tax["rate"],
            charge_mode=tax["chargeMode"],
            ordinal=tax["ordinal"],
        )
        db.add(tax_rate)

    db.commit()
    return db.query(TaxRate).all()
