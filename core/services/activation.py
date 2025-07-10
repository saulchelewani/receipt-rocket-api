import logging
from typing import Any

import httpx

from core.utils.api_logger import write_api_log, write_api_exception_log
from core.utils.helpers import get_sequence_number, sign_hmac_sha512

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from fastapi import HTTPException
from sqlalchemy.orm import Session

from core.models import Terminal, TaxRate, Tenant, GlobalConfig
from core.services.config import save_tax_payer_config
from core.settings import settings


async def activate_terminal(
        code: str,
        tenant: Tenant,
        db: Session,
        x_mac_address: str | None = None
) -> type[Terminal] | Terminal:
    result = await activate_terminal_with_code(code=code, mac_address=x_mac_address, db=db)

    if not result:
        raise HTTPException(status_code=400, detail="Terminal activation failed")

    sync_global_config(db, result["data"]["configuration"]["globalConfiguration"])
    save_tax_payer_config(
        db,
        tenant,
        result["data"]["configuration"]["taxpayerConfiguration"],
        result["data"]["activatedTerminal"]["taxpayerId"]
    )
    return save_new_terminal(db, result["data"], tenant.id, code)


def save_new_terminal(
        db: Session,
        config: dict[str, Any],
        tenant_id: Tenant.id,
        activation_code: str
):
    terminal = db.query(Terminal).filter(Terminal.terminal_id == config['activatedTerminal']['terminalId']).first()
    if terminal:
        raise HTTPException(status_code=400, detail="Terminal exists")

    terminal = Terminal(
        tenant_id=tenant_id,
        terminal_id=config['activatedTerminal']['terminalId'],
        position=config['activatedTerminal']['terminalPosition'],
        secret_key=config['activatedTerminal']['terminalCredentials']['secretKey'],
        token=config['activatedTerminal']['terminalCredentials']['jwtToken'],
        trading_name=config['configuration']['terminalConfiguration']['tradingName'],
        email=config['configuration']['terminalConfiguration']['emailAddress'],
        phone_number=config['configuration']['terminalConfiguration']['phoneNumber'],
        label=config['configuration']['terminalConfiguration']['terminalLabel'],
        config_version=config['configuration']['terminalConfiguration']['versionNo'],
        address_lines=config['configuration']['terminalConfiguration']['addressLines'],
        offline_limit_hours=config['configuration']['terminalConfiguration']['offlineLimit'][
            'maxTransactionAgeInHours'],
        offline_limit_amount=config['configuration']['terminalConfiguration']['offlineLimit']['maxCummulativeAmount'],
        site_id=config['configuration']['terminalConfiguration']['terminalSite']['siteId'],
        site_name=config['configuration']['terminalConfiguration']['terminalSite']['siteName'],
        device_id=get_sequence_number(),
        activation_code=activation_code
    )

    db.add(terminal)
    db.commit()
    return terminal


def sync_terminal_config(
        db: Session,
        config: dict,
        tenant: Tenant,
        terminal_id: Terminal.terminal_id | None = None
) -> type[Terminal] | Terminal:
    db_terminal = db.query(Terminal).filter(
        Terminal.label == config['terminalLabel'],
        Terminal.terminal_id == terminal_id
    ).first()

    if db_terminal and db_terminal.config_version == config["versionNo"]:
        return db_terminal

    terminal_dict = {
        'tenant_id': tenant.id,
        'site_id': config['terminalSite']['siteId'],
        'trading_name': config['tradingName'],
        'email': config['emailAddress'],
        'phone_number': config['phoneNumber'],
        'label': config['terminalLabel'],
        'device_id': get_sequence_number() if not db_terminal else db_terminal.device_id,
        'config_version': config['versionNo'],
        'address_lines': config['addressLines'],
        'offline_limit_hours': config['offlineLimit']['maxTransactionAgeInHours'],
        'offline_limit_amount': config['offlineLimit']['maxCummulativeAmount'],
    }

    if terminal_id is not None:
        terminal_dict['terminal_id'] = terminal_id

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


async def confirm_terminal_activation(terminal, db: Session) -> dict[str, Any]:
    headers = {
        "accept": "text/plain",
        "x-signature": sign_hmac_sha512(terminal.activation_code, terminal.secret_key),
        "Content-Type": "application/json",
        "Authorization": f"Bearer {terminal.token}"
    }

    payload = {
        "terminalId": terminal.terminal_id
    }

    try:
        async with httpx.AsyncClient(verify=False) as client:
            url = f"{settings.MRA_EIS_URL}/onboarding/terminal-activated-confirmation"
            response = await client.post(
                url,
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            await write_api_log(db, payload, response, url, headers)
            data = response.json()

            if int(data.get("statusCode")) < 1:
                raise HTTPException(status_code=400, detail=data.get("remark"))

            return data
    except Exception as e:
        await write_api_exception_log(db, e, payload, url, headers)
        raise HTTPException(status_code=400, detail=f"error: {str(e)}")


async def activate_terminal_with_code(db: Session, code: str, mac_address: str) -> dict[str, Any]:
    payload = {
        "terminalActivationCode": code,
        "environment": {
            "platform": {
                "osName": "Android",
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
        async with httpx.AsyncClient(verify=False) as client:
            url = f"{settings.MRA_EIS_URL}/onboarding/activate-terminal"
            response = await client.post(
                url,
                timeout=settings.MRA_EIS_TIMEOUT,
                json=payload
            )
            response.raise_for_status()
            await write_api_log(db, payload, response, url)

            if int(response.json()["statusCode"]) < -1:
                raise HTTPException(status_code=400, detail=response.json()["remark"])
            return response.json()
    except Exception as e:
        await write_api_exception_log(db, e, payload, url)
        raise HTTPException(status_code=400, detail=f"error: {str(e)}")


def sync_global_config(db: Session, config: dict[str, Any]) -> list[type[TaxRate]]:
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
