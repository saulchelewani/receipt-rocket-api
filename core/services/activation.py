import httpx
from sqlalchemy.orm import Session

from core.models import Terminal, TerminalConfiguration, TaxRate

API_URL = "https://dev-eis-api.mra.mw/api/v1/onboarding/activate-terminal"

def activate_terminal(code: str, db: Session):
    payload = {
        "terminalActivationCode": code,
        "environment": {
            "platform": {
                "osName": "Windows 11",
                "osVersion": "Windows 11",
                "osBuild": "11.901.2",
                "macAddress": "00-00-00-00-00-00"
            },
            "pos": {
                "productID": "MRA-desktop/{guid}",
                "productVersion": "1.0.0"
            }
        }
    }

    response = httpx.post(API_URL, json=payload)
    response.raise_for_status()
    result = response.json()["data"]

    terminal_data = result["activatedTerminal"]
    config = result["configuration"]

    terminal = Terminal(
        terminal_id=terminal_data["terminalId"],
        secret_key=terminal_data["terminalCredentials"]["secretKey"]
    )
    db.add(terminal)

    conf = config["terminalConfiguration"]
    terminal_config = TerminalConfiguration(
        terminal_id=terminal.terminal_id,
        label=conf["terminalLabel"],
        email=conf["emailAddress"],
        phone=conf["phoneNumber"],
        trading_name=conf["tradingName"]
    )
    db.add(terminal_config)

    for tax in config["globalConfiguration"]["taxrates"]:
        tax_rate = TaxRate(
            rate_id=tax["id"],
            name=tax["name"],
            rate=tax["rate"],
            charge_mode=tax["chargeMode"],
            terminal_id=terminal.terminal_id
        )
        db.add(tax_rate)

    db.commit()
    return terminal
