from http import HTTPStatus

from fastapi import HTTPException


class ConversationNotFoundException(HTTPException):
    def __init__(self, id):
        super().__init__(
            status_code=HTTPStatus.NOT_FOUND, 
            detail=f"Conversation with id '{id}' not found!!!"
        )