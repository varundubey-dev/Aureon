class AppError(Exception):

    def __init__(
        self,
        status_code: int,
        detail: str,
        code: str,
    ):
        self.status_code = status_code
        self.detail = detail
        self.code = code