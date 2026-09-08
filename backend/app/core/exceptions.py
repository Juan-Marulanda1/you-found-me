class AppException(Exception):
    status_code = 400
    detail = "Application error"


class AnnouncementNotFoundError(AppException):
    status_code = 404
    detail = "Announcement not found"


class InvalidAdminPinError(AppException):
    status_code = 403
    detail = "Invalid administration PIN."
