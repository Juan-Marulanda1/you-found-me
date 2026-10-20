"""Errores de dominio que los manejadores globales convierten en JSON."""


class AppException(Exception):
    """Base de los errores esperados; define el código HTTP y el mensaje público."""

    status_code = 400
    detail = "Application error"


class PublicationNotFoundError(AppException):
    status_code = 404
    detail = "Publication not found"


class InvalidAdminPinError(AppException):
    status_code = 403
    detail = "Invalid management PIN."


class TooManyAdminPinAttemptsError(AppException):
    status_code = 429
    detail = "Too many invalid PIN attempts. Try again later."


class ImageStorageUnavailableError(AppException):
    status_code = 503
    detail = "Image storage is temporarily unavailable."


class PublicationImageNotFoundError(AppException):
    status_code = 404
    detail = "Publication image not found."


class ProductImageNotFoundError(PublicationImageNotFoundError):
    detail = "Product image not found."


class AnnouncementImageNotFoundError(PublicationImageNotFoundError):
    detail = "Announcement image not found."


class PublicationImageLimitExceededError(AppException):
    status_code = 409
    detail = "This publication has reached its image limit."


class ProductImageLimitExceededError(PublicationImageLimitExceededError):
    detail = "This product has reached its image limit."


class AnnouncementImageLimitExceededError(PublicationImageLimitExceededError):
    detail = "This announcement has reached its image limit."


class PublicationImageUploadPendingError(AppException):
    status_code = 409
    detail = "The image has not been uploaded yet."


class ProductImageUploadPendingError(PublicationImageUploadPendingError):
    pass


class AnnouncementImageUploadPendingError(PublicationImageUploadPendingError):
    pass


class PublicationImageValidationError(AppException):
    status_code = 422
    detail = "The uploaded image does not match the requested file type or size."


class ProductImageValidationError(PublicationImageValidationError):
    pass


class AnnouncementImageValidationError(PublicationImageValidationError):
    pass
