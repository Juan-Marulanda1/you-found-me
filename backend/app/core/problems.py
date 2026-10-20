"""Respuestas de error con el formato Problem Details (RFC 9457).

Todas las respuestas de error usan `Content-Type: application/problem+json` y
los miembros estándar `type`, `title`, `status`, `detail` e `instance`, más dos
extensiones permitidas por el RFC:

- `code`: identificador estable para que los clientes decidan sin leer textos.
- `errors`: lista de campos inválidos en los errores de validación (422).

`type` es "about:blank" porque los tipos se distinguen con `code`; en ese caso
el RFC indica que `title` corresponde a la frase del estado HTTP.
"""

from collections.abc import Mapping, Sequence
from http import HTTPStatus
from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

PROBLEM_CONTENT_TYPE = "application/problem+json"

# Frases de estado HTTP en español usadas como `title`.
_STATUS_TITLES = {
    400: "Solicitud incorrecta",
    401: "No autenticado",
    403: "Acceso denegado",
    404: "No encontrado",
    405: "Método no permitido",
    409: "Conflicto",
    413: "Contenido demasiado grande",
    415: "Tipo de contenido no admitido",
    422: "Datos no válidos",
    429: "Demasiadas solicitudes",
    500: "Error interno del servidor",
    502: "Error en un servicio externo",
    503: "Servicio no disponible",
}


class FieldError(BaseModel):
    """Error de un campo concreto dentro de una respuesta 422."""

    field: str | None
    location: str
    message: str


class ProblemDetail(BaseModel):
    """Esquema de error documentado en OpenAPI."""

    type: str = "about:blank"
    title: str
    status: int
    detail: str
    instance: str
    code: str
    errors: list[FieldError] | None = None


def status_title(status_code: int) -> str:
    """Frase en español del estado HTTP; usa la inglesa si no está traducida."""
    if status_code in _STATUS_TITLES:
        return _STATUS_TITLES[status_code]
    try:
        return HTTPStatus(status_code).phrase
    except ValueError:
        return "Error"


def problem_response(
    request: Request,
    *,
    status_code: int,
    code: str,
    detail: str,
    headers: Mapping[str, str] | None = None,
    errors: Sequence[FieldError] | None = None,
) -> JSONResponse:
    """Construye la respuesta application/problem+json."""
    problem = ProblemDetail(
        title=status_title(status_code),
        status=status_code,
        detail=detail,
        instance=request.url.path,
        code=code,
        errors=list(errors) if errors else None,
    )
    content = problem.model_dump()
    # `errors` solo aparece en validaciones; dentro de cada error, field puede ser null.
    if content["errors"] is None:
        del content["errors"]
    return JSONResponse(
        status_code=status_code,
        content=content,
        headers=dict(headers) if headers else None,
        media_type=PROBLEM_CONTENT_TYPE,
    )


# --- Traducción de errores de validación de Pydantic -------------------------

# Plantillas por tipo de error de Pydantic v2. Los marcadores se completan con
# el contexto (`ctx`) que Pydantic adjunta a cada error.
_VALIDATION_MESSAGES = {
    "missing": "Este campo es obligatorio.",
    "extra_forbidden": "Este campo no está permitido.",
    "string_type": "Debe ser un texto.",
    "string_too_short": "Debe tener al menos {min_length} caracteres.",
    "string_too_long": "Debe tener como máximo {max_length} caracteres.",
    "string_pattern_mismatch": "No tiene el formato esperado.",
    "int_type": "Debe ser un número entero.",
    "int_parsing": "Debe ser un número entero.",
    "int_from_float": "Debe ser un número entero, sin decimales.",
    "float_type": "Debe ser un número.",
    "float_parsing": "Debe ser un número.",
    "decimal_type": "Debe ser un número.",
    "decimal_parsing": "Debe ser un número.",
    "decimal_max_digits": "Debe tener como máximo {max_digits} dígitos.",
    "decimal_max_places": "Debe tener como máximo {decimal_places} decimales.",
    "decimal_whole_digits": "Tiene demasiados dígitos antes del punto decimal.",
    "greater_than": "Debe ser mayor que {gt}.",
    "greater_than_equal": "Debe ser mayor o igual que {ge}.",
    "less_than": "Debe ser menor que {lt}.",
    "less_than_equal": "Debe ser menor o igual que {le}.",
    "bool_type": "Debe ser verdadero o falso.",
    "bool_parsing": "Debe ser verdadero o falso.",
    "uuid_type": "Debe ser un identificador UUID válido.",
    "uuid_parsing": "Debe ser un identificador UUID válido.",
    "literal_error": "Debe ser uno de estos valores: {expected}.",
    "enum": "Debe ser uno de estos valores: {expected}.",
    "list_type": "Debe ser una lista.",
    "dict_type": "Debe ser un objeto JSON.",
    "model_type": "Debe ser un objeto JSON.",
    "model_attributes_type": "Debe ser un objeto JSON.",
    "json_invalid": "El cuerpo de la solicitud no es un JSON válido.",
    "json_type": "El cuerpo de la solicitud no es un JSON válido.",
}
_DEFAULT_VALIDATION_MESSAGE = "El valor no es válido."


def _validation_message(error: Mapping[str, Any]) -> str:
    """Traduce un error de Pydantic a un mensaje en español."""
    error_type = error.get("type", "")
    context = error.get("ctx") or {}
    # Los validadores propios lanzan ValueError con el mensaje ya en español.
    if error_type in ("value_error", "assertion_error") and "error" in context:
        return str(context["error"])

    template = _VALIDATION_MESSAGES.get(error_type, _DEFAULT_VALIDATION_MESSAGE)
    values = {key: str(value) for key, value in context.items()}
    if "expected" in values:
        # Pydantic enumera las opciones en inglés: "'A', 'B' or 'C'".
        values["expected"] = values["expected"].replace(" or ", " o ")
    try:
        return template.format(**values)
    except KeyError:
        return _DEFAULT_VALIDATION_MESSAGE


def validation_field_errors(errors: Sequence[Mapping[str, Any]]) -> list[FieldError]:
    """Convierte los errores de FastAPI en una lista de FieldError."""
    field_errors = []
    for error in errors:
        location, *path = error.get("loc") or ("body",)
        if error.get("type") in ("json_invalid", "json_type"):
            # En JSON mal formado, loc trae la posición del error de sintaxis,
            # no un campo.
            path = []
        field_errors.append(
            FieldError(
                # Los errores de modelo completo (validadores de clase) no
                # tienen campo; su mensaje ya nombra el campo afectado.
                field=".".join(str(part) for part in path) or None,
                location=str(location),
                message=_validation_message(error),
            )
        )
    return field_errors


def validation_summary(field_errors: Sequence[FieldError]) -> str:
    """Resume los errores en `detail` para clientes que no lean `errors`."""
    if len(field_errors) == 1:
        error = field_errors[0]
        return f"«{error.field}»: {error.message}" if error.field else error.message
    return f"Hay {len(field_errors)} datos no válidos. Revisa los campos indicados."


# --- Documentación OpenAPI ---------------------------------------------------

PROBLEM_RESPONSES: dict[int | str, dict[str, Any]] = {
    "4XX": {"model": ProblemDetail, "description": "Error del cliente (RFC 9457)."},
    "5XX": {"model": ProblemDetail, "description": "Error del servidor (RFC 9457)."},
}


def use_problem_media_type(schema: dict) -> dict:
    """Publica las respuestas 4XX/5XX como application/problem+json.

    FastAPI documenta los modelos de `responses` como application/json; este
    ajuste refleja el Content-Type que realmente envían los manejadores.
    """
    for path in schema.get("paths", {}).values():
        for operation in path.values():
            for status_key, response in operation.get("responses", {}).items():
                content = response.get("content", {})
                if status_key in ("4XX", "5XX") and "application/json" in content:
                    content[PROBLEM_CONTENT_TYPE] = content.pop("application/json")
    return schema
