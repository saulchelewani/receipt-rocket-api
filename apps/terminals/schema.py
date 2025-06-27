from pydantic import BaseModel


class UnblockStatusResponse(BaseModel):
    is_unblocked: bool
    details: str
