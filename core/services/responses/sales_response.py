from core.services.responses.mra_response import BaseResponse


class SalesResponse(BaseResponse):

    def validation_url(self) -> str:
        return self.body["data"]["validationURL"]

    def should_download_latest_config(self) -> bool:
        return self.body["data"]["shouldDownloadLatestConfig"]

    def should_block_terminal(self) -> bool:
        return self.body["data"]["shouldBlockTerminal"]
