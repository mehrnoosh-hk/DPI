from fastapi import HTTPException, status


def not_found_handler(text: str):
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={
            "statusCode": status.HTTP_404_NOT_FOUND,
            "title": "Conflict",
            "errorText": text,
        }
    )


def conflict_handler(text: str):
    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail={
            "statusCode": status.HTTP_409_CONFLICT,
            "title": "Conflict",
            "errorText": text,
        }
    )


def internal_error_handler(text: str):
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail={
            "statusCode": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "title": "Internal Server Error",
            "errorText": text,
        }
    )


def forbidden_handler(text: str):
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail={
            "statusCode": status.HTTP_403_FORBIDDEN,
            "title": "Forbidden",
            "statusText": "Forbidden",
            "errorText": text
        }
    )


def unprocessable_entity_handler(text: str) -> None:
    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail={
            "statusCode": status.HTTP_422_UNPROCESSABLE_ENTITY,
            "title": "Forbidden",
            "statusText": "Forbidden",
            "errorText": text})


def unprocessable_token(text: str) -> None:
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={
            "statusCode": status.HTTP_401_UNAUTHORIZED,
            "title": "Unauthorized",
            "statusText": "Unauthorized",
            "errorText": text})
