from http import HTTPStatus

from app.exceptions.base import AppException


class LLMException(AppException):
    def __init__(self):
        super().__init__(
            message="An error occured during LLM calling",
            status_code=HTTPStatus.NO_CONTENT
        )