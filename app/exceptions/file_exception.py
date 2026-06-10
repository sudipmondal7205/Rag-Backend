from http import HTTPStatus
from fastapi import HTTPException


class FileException(HTTPException):
    def __init__(self, detail: str = None):
        super().__init__(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR, 
            detail=detail
        )


