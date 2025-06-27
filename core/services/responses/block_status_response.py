from core.services.responses.mra_response import BaseResponse


class BlockStatusResponse(BaseResponse):
    def is_blocked(self) -> bool:
        return self.body["data"]["isBlocked"]

    def blocking_reason(self) -> str:
        return self.body["data"]["blockingReason"]


class UnblockStatusResponse(BaseResponse):
    def is_unblocked(self) -> bool:
        return self.body["data"]["isUnblocked"]
