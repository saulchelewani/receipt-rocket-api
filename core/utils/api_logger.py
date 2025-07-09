import json

from core import ApiLog


async def write_api_log(db, payload, response, url, headers=None):
    log = ApiLog(
        method="POST",
        url=url,
        request_headers=json.dumps(headers),
        request_body=json.dumps(payload),
        response_status=response.status_code,
        response_headers=json.dumps(dict(response.headers)),
        response_body=response.text
    )
    db.add(log)
    db.commit()


async def write_api_exception_log(db, e, payload, url, headers=None):
    log = ApiLog(
        method="POST",
        url=url,
        request_headers=json.dumps(headers),
        request_body=json.dumps(payload),
        response_status=0,
        response_headers="{}",
        response_body=str(e),
    )
    db.add(log)
    db.commit()
