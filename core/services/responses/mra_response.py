from pyasn1.type.univ import Any


class BaseResponse:
    def __init__(self, body: dict[str, str | Any]):
        self.body = body

    def status_code(self) -> int:
        return int(self.body["statusCode"])

    def success(self) -> bool:
        return self.status_code() > -1

    def remark(self) -> str:
        return self.body["remark"]
