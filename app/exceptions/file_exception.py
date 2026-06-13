from http import HTTPStatus
from fastapi import HTTPException


class FileException(HTTPException):
    def __init__(
            self, status_code: int = HTTPStatus.INTERNAL_SERVER_ERROR, 
            detail: str = None,
            headers: str = None
        ):
        super().__init__(
            status_code=status_code,
            detail=detail,
            headers=headers
        )

