from http import HTTPStatus
from fastapi import HTTPException


class CredentialException(HTTPException):
    def __init__(self, status_code, detail = None):
        super().__init__(status_code, detail)



class VerificationException(HTTPException):
    def __init__(self, detail = None):
        super().__init__(
            status_code=HTTPStatus.UNAUTHORIZED, 
            detail=detail
        )