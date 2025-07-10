import httpx
from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from core.database import SessionLocal
from core.models import OfflineTransaction
from core.services.responses.sales_response import SalesResponse
from core.settings import settings
from core.utils.api_logger import write_api_log, write_api_exception_log
from core.utils.helpers import sign_hmac_sha512


async def submit_transaction(transaction, terminal, db) -> SalesResponse:
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Bearer {terminal.token}"
    }
    url = f"{settings.MRA_EIS_URL}/sales/submit-sales-transaction"
    try:
        async with httpx.AsyncClient(timeout=settings.MRA_EIS_TIMEOUT) as client:
            response = await client.post(
                url,
                json=transaction,
                headers=headers
            )
            await write_api_log(db, transaction, response, url, headers)
            # response.raise_for_status()
            return SalesResponse(response.json())
    except httpx.TimeoutException:
        await write_api_exception_log(db, "Request timed out", transaction, url, headers)
        txn_details = sign_offline_transaction(transaction, terminal)
        record = OfflineTransaction(
            terminal_id=terminal.id,
            transaction_id=transaction['invoiceHeader']['invoiceNumber'],
            details=txn_details,
            tenant_id=terminal.tenant_id
        )
        terminal.offline_transactions.append(record)
        db.commit()
        return SalesResponse({
            "statusCode": 0,
            "remark": "Transaction saved offline",
            "data": {
                "validationURL": txn_details['invoiceSummary']['offlineSignature'],
                "shouldDownloadLatestConfig": False,
                "shouldBlockTerminal": False
            }
        })
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error submitting transaction: {str(e)}")


async def submit_offline_transaction(txn: type[OfflineTransaction], db: Session):
    try:
        async with httpx.AsyncClient(timeout=settings.MRA_EIS_TIMEOUT) as client:
            response = await client.post(
                f"{settings.MRA_EIS_URL}/sales/submit-sales-transaction",
                json=txn.details,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    "Authorization": txn.terminal.token
                }
            )
            response_obj = SalesResponse(response.json())
            if response_obj.success():
                txn.submitted_at = func.now()
                db.commit()
            return response_obj
    except Exception as e:
        # pass
        raise HTTPException(status_code=400, detail=f"Error submitting transaction: {str(e)}")


def sign_offline_transaction(transaction, terminal) -> dict:
    transaction['invoiceSummary']['offlineSignature'] = offline_transaction_signature(transaction, terminal)
    return transaction


def offline_transaction_signature(transaction, terminal) -> str:
    invoice_number = transaction['invoiceHeader']['invoiceNumber']
    line_item_count = len(transaction['invoiceLineItems'])
    transaction_date = transaction['invoiceHeader']['invoiceDateTime']
    return sign_hmac_sha512(f"{invoice_number}{line_item_count}{transaction_date}", terminal.secret_key)


async def run_submission_job(db: Session = None):
    innerscope = db is None
    if not db:
        db = SessionLocal()

    transactions = db.query(OfflineTransaction).filter(OfflineTransaction.submitted_at.is_(None)).all()

    for transaction in transactions:
        await submit_offline_transaction(transaction, db)
    if innerscope:
        db.close()
