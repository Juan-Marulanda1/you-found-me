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
