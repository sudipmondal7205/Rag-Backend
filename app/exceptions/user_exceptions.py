from http import HTTPStatus
from fastapi import HTTPException


class UserAlreadyExistsException(HTTPException):
    def __init__(self, name: str):
        super().__init__(
            status_code=HTTPStatus.BAD_REQUEST,
            detail=f"User with name '{name}' already exists."
        )


class UserNotFoundException(HTTPException):
    def __init__(self, name: str):
        super().__init__(
            status_code=HTTPStatus.NOT_FOUND,
            detail=f"User with name '{name}' not found."
        )
