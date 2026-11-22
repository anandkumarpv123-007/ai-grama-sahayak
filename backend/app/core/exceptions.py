from typing import Any, List, Optional
from fastapi import HTTPException, status


class AppBaseException(HTTPException):
    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        details: Optional[List[Any]] = None,
    ):
        super().__init__(status_code=status_code, detail=message)
        self.code = code
        self.message = message
        self.details = details or []


class ValidationErrorException(AppBaseException):
    def __init__(
        self,
        message: str = "The request contains invalid information.",
        details: Optional[List[Any]] = None,
    ):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            code="VALIDATION_ERROR",
            message=message,
            details=details,
        )


class BadRequestException(AppBaseException):
    def __init__(
        self,
        message: str = "Invalid request.",
        code: str = "BAD_REQUEST",
        details: Optional[List[Any]] = None,
    ):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            code=code,
            message=message,
            details=details,
        )


class NotFoundException(AppBaseException):
    def __init__(
        self,
        message: str = "The requested resource was not found.",
        code: str = "NOT_FOUND",
        details: Optional[List[Any]] = None,
    ):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            code=code,
            message=message,
            details=details,
        )


class InternalServerErrorException(AppBaseException):
    def __init__(
        self,
        message: str = "An unexpected server error occurred.",
        code: str = "INTERNAL_SERVER_ERROR",
        details: Optional[List[Any]] = None,
    ):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code=code,
            message=message,
            details=details,
        )
