import httpx
from fastapi import HTTPException
from sqlalchemy.orm import Session

from core.models import Terminal, TaxRate, Tenant
from core.settings import settings
from core.utils import sign_hmac_sha512


def activate_terminal(code: str, tenant: Tenant, db: Session, x_mac_address: str | None = None):
    payload = {
        "terminalActivationCode": code,
        "environment": {
            "platform": {
                "osName": "Windows 11",
                "osVersion": "Windows 11",
                "osBuild": "11.901.2",
                "macAddress": x_mac_address
            },
            "pos": {
                "productID": "MRA-desktop/{guid}",
                "productVersion": "1.0.0"
            }
        }
    }

    response = httpx.post(f"{settings.MRA_EIS_URL}/onboarding/activate-terminal", json=payload)
    response_data = response.json()

    if response_data["statusCode"] < -1:
        raise HTTPException(status_code=400, detail=response_data["remark"])

    result = response_data["data"]

    terminal_data = result["activatedTerminal"]
    config = result["configuration"]

    terminal_dict = {
        'terminal_id': terminal_data["terminalId"],
        'secret_key': terminal_data["terminalCredentials"]["secretKey"],
        'tenant_id': tenant.id,
        'label': config["terminalConfiguration"]["terminalLabel"],
        'email': config["terminalConfiguration"]["emailAddress"],
        'phone_number': config["terminalConfiguration"]["phoneNumber"],
        'trading_name': config["terminalConfiguration"]["tradingName"],
        'version': config["terminalConfiguration"]["versionNo"],
        'address_lines': config["terminalConfiguration"]["addressLines"]
    }

    terminal = Terminal(**terminal_dict)
    db.add(terminal)

    for tax in config["globalConfiguration"]["taxrates"]:
        db_rate = db.query(TaxRate).filter(TaxRate.name == tax["name"]).first()
        if db_rate:
            db_rate.rate = tax["rate"]
            db_rate.charge_mode = tax["chargeMode"]
            db_rate.rate_id = tax["id"]
            continue
        tax_rate = TaxRate(
            rate_id=tax["id"],
            name=tax["name"],
            rate=tax["rate"],
            charge_mode=tax["chargeMode"],
        )
        db.add(tax_rate)

    db.commit()
    db.refresh(terminal)
    return terminal


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
        response = await client.post(f"{settings.MRA_EIS_URL}/onboarding/terminal-activated-confirmation",
                                     headers=headers, json=payload)

        if int(response.json()["statusCode"]) < -1:
            raise HTTPException(status_code=400, detail=response.json()["remark"])

        return response.json()
