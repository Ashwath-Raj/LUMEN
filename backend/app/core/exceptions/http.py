from fastapi import HTTPException, status


class LumenHTTPException(HTTPException):
    def __init__(self, status_code: int, detail: str, headers: dict | None = None):
        super().__init__(status_code=status_code, detail=detail, headers=headers)


class AuthenticationError(LumenHTTPException):
    def __init__(self, detail: str = "Invalid credentials."):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


class AuthorizationError(LumenHTTPException):
    def __init__(self, detail: str = "Insufficient clearance for this resource."):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


class NotFoundError(LumenHTTPException):
    def __init__(self, detail: str):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)
