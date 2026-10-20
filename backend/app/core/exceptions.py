"""Errores esperados de la API.

Cada error define el estado HTTP, un código estable en snake_case y un mensaje
en español para quien usa la aplicación. Los manejadores globales los convierten
en respuestas Problem Details (RFC 9457); los clientes deben decidir con `code`,
nunca comparando el texto de `detail`, que puede cambiar.
"""


class AppException(Exception):
    """Base de los errores esperados de la API."""

    status_code = 400
    code = "bad_request"
    detail = "No pudimos procesar la solicitud."
    headers: dict[str, str] | None = None

    def __init__(self, detail: str | None = None) -> None:
        if detail is not None:
            self.detail = detail
        super().__init__(self.detail)


# --- Publicaciones -----------------------------------------------------------


class PublicationNotFoundError(AppException):
    # También se usa cuando la publicación existe pero pertenece a otra cuenta,
    # para no revelar su existencia.
    status_code = 404
    code = "publication_not_found"
    detail = "No encontramos la publicación o no tienes acceso a ella."


class InvalidPriceRangeError(AppException):
    status_code = 422
    code = "invalid_price_range"
    detail = "El precio mínimo no puede ser mayor que el precio máximo."


class InvalidAdminPinError(AppException):
    status_code = 403
    code = "invalid_admin_pin"
    detail = "El PIN de administración no es correcto."


class TooManyAdminPinAttemptsError(AppException):
    status_code = 429
    code = "too_many_pin_attempts"
    detail = (
        "Hubo demasiados intentos con un PIN incorrecto. "
        "Espera 15 minutos antes de volver a intentarlo."
    )


# --- Imágenes ----------------------------------------------------------------


class ImageStorageUnavailableError(AppException):
    status_code = 503
    code = "image_storage_unavailable"
    detail = (
        "El almacenamiento de imágenes no está disponible en este momento. "
        "Inténtalo de nuevo más tarde."
    )


class PublicationImageNotFoundError(AppException):
    status_code = 404
    code = "image_not_found"
    detail = "No encontramos la imagen solicitada."


class ProductImageNotFoundError(PublicationImageNotFoundError):
    detail = "No encontramos esta imagen del producto."


class AnnouncementImageNotFoundError(PublicationImageNotFoundError):
    detail = "No encontramos esta imagen del aviso."


class PublicationImageLimitExceededError(AppException):
    status_code = 409
    code = "image_limit_reached"
    detail = "La publicación ya alcanzó el máximo de imágenes permitido."


class ProductImageLimitExceededError(PublicationImageLimitExceededError):
    detail = (
        "El producto ya alcanzó el máximo de imágenes. "
        "Elimina alguna antes de subir otra."
    )


class AnnouncementImageLimitExceededError(PublicationImageLimitExceededError):
    detail = (
        "El aviso ya alcanzó el máximo de imágenes. "
        "Elimina la actual antes de subir otra."
    )


class PublicationImageUploadPendingError(AppException):
    status_code = 409
    code = "image_upload_pending"
    detail = (
        "La imagen todavía no termina de subirse. "
        "Espera un momento y vuelve a intentarlo."
    )


class ProductImageUploadPendingError(PublicationImageUploadPendingError):
    pass


class AnnouncementImageUploadPendingError(PublicationImageUploadPendingError):
    pass


class PublicationImageValidationError(AppException):
    status_code = 422
    code = "invalid_image"
    detail = (
        "La imagen no cumple los requisitos: debe ser JPG, PNG o WebP, "
        "no superar el tamaño permitido y coincidir con el archivo declarado."
    )


class ProductImageValidationError(PublicationImageValidationError):
    pass


class AnnouncementImageValidationError(PublicationImageValidationError):
    pass


# --- Autenticación y cuentas -------------------------------------------------


class AuthenticationRequiredError(AppException):
    status_code = 401
    code = "authentication_required"
    detail = "Inicia sesión con una cuenta verificada para continuar."
    # RFC 9110: toda respuesta 401 debe indicar el esquema de autenticación.
    headers = {"WWW-Authenticate": "Bearer"}


class EmailNotConfirmedError(AppException):
    status_code = 403
    code = "email_not_confirmed"
    detail = "Confirma tu correo electrónico antes de administrar publicaciones."


class AccountNotInvitedError(AppException):
    status_code = 403
    code = "account_not_invited"
    detail = (
        "Esta cuenta no tiene invitación para publicar. "
        "Solicítala con la clave de invitación."
    )


class AuthNotConfiguredError(AppException):
    status_code = 503
    code = "auth_not_configured"
    detail = "La autenticación de cuentas no está configurada en el servidor."


class AuthUnavailableError(AppException):
    status_code = 503
    code = "auth_unavailable"
    detail = (
        "El servicio de cuentas no está disponible en este momento. "
        "Inténtalo de nuevo más tarde."
    )


class InvalidInvitationKeyError(AppException):
    status_code = 403
    code = "invalid_invitation_key"
    detail = "La clave de invitación no es correcta."


class InvitationKeyNotConfiguredError(AppException):
    status_code = 503
    code = "invitation_key_not_configured"
    detail = "La clave de invitación no está configurada en el servidor."


class InvitationsNotConfiguredError(AppException):
    status_code = 503
    code = "invitations_not_configured"
    detail = "Las invitaciones de cuenta no están configuradas en el servidor."


class InvitationsUnavailableError(AppException):
    status_code = 503
    code = "invitations_unavailable"
    detail = (
        "No pudimos enviar la invitación en este momento. Inténtalo de nuevo más tarde."
    )


class TooManyInvitationsError(AppException):
    status_code = 429
    code = "too_many_invitations"
    detail = (
        "Se enviaron demasiadas invitaciones. "
        "Espera unos minutos antes de intentarlo de nuevo."
    )


class AccountAlreadyExistsError(AppException):
    status_code = 409
    code = "account_already_exists"
    detail = (
        "Ya existe una cuenta con este correo. "
        "Usa «Iniciar sesión» para recibir un enlace de acceso."
    )


class EmailNotInvitableError(AppException):
    status_code = 422
    code = "email_not_invitable"
    detail = "No pudimos invitar este correo. Revisa que la dirección sea correcta."
