class AppException(Exception):
    status_code = 400
    detail = "Application error"


class PublicationNotFoundError(AppException):
    status_code = 404
    detail = "Publication not found"


class AnnouncementNotFoundError(PublicationNotFoundError):
    detail = "Announcement not found"


class InvalidAdminPinError(AppException):
    status_code = 403
    detail = "Invalid management PIN."


class TooManyAdminPinAttemptsError(AppException):
    status_code = 429
    detail = "Too many invalid PIN attempts. Try again later."


class ImageStorageUnavailableError(AppException):
    status_code = 503
    detail = "Image storage is temporarily unavailable."


class ProductImageNotFoundError(AppException):
    status_code = 404
    detail = "Product image not found."


class ProductImageLimitExceededError(AppException):
    status_code = 409
    detail = "This product has reached its image limit."


class ProductImageUploadPendingError(AppException):
    status_code = 409
    detail = "The image has not been uploaded yet."


class ProductImageValidationError(AppException):
    status_code = 422
    detail = "The uploaded image does not match the requested file type or size."
