from http import HTTPStatus
from app.exceptions.base import AppException


class ConversationNotFoundException(AppException):
    def __init__(self):
        super().__init__(
            message="Conversation not found exception!!!",
            status_code=HTTPStatus.NOT_FOUND
        )