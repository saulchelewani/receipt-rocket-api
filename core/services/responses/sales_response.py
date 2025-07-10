from core.services.responses.mra_response import BaseResponse


class SalesResponse(BaseResponse):

    def validation_url(self) -> str | None:
        if not self.body or not isinstance(self.body, dict):
            return None

        if not isinstance(self.body.get("data", {}), dict):
            return None

        return self.body["data"]["validationURL"]

    def should_download_latest_config(self) -> bool | None:
        if not self.body or not isinstance(self.body, dict):
            return None

        if not isinstance(self.body.get("data", {}), dict):
            return None

        return self.body["data"]["shouldDownloadLatestConfig"]

    def should_block_terminal(self) -> bool | None:
        if not self.body or not isinstance(self.body, dict):
            return None

        if not isinstance(self.body.get("data", {}), dict):
            return None

        return self.body['data']['shouldBlockTerminal']
