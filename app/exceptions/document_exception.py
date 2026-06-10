from fastapi import HTTPException
from http import HTTPStatus
import uuid


class DocumentNotFoundException(HTTPException):
    def __init__(self, document_id: uuid.UUID):
        super().__init__(
            status_code=HTTPStatus.NOT_FOUND,
            detail=f"Document with Id: {document_id} not found !!!"
        )