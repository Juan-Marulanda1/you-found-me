"""Contrato de errores: Problem Details (RFC 9457) con mensajes en español."""

import asyncio
import json
import re
import unittest

from fastapi import FastAPI

from app.core import exceptions
from app.core.exception_handlers import register_exception_handlers
from app.core.exceptions import AppException, InvalidAdminPinError
from app.core.problems import PROBLEM_CONTENT_TYPE

PROBLEM_MEMBERS = {"type", "title", "status", "detail", "instance", "code"}


def request(app, method: str, path: str, body: bytes | None = None, query: str = ""):
    """Ejecuta una solicitud ASGI y devuelve estado, encabezados y cuerpo JSON."""
    messages = []
    sent = False

    async def receive():
        nonlocal sent
        if sent:
            return {"type": "http.disconnect"}
        sent = True
        return {"type": "http.request", "body": body or b"", "more_body": False}

    async def send(message):
        messages.append(message)

    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": method,
        "scheme": "http",
        "path": path,
        "raw_path": path.encode(),
        "query_string": query.encode(),
        "root_path": "",
        "headers": [(b"host", b"testserver"), (b"content-type", b"application/json")],
        "client": ("127.0.0.1", 1234),
        "server": ("testserver", 80),
    }
    try:
        asyncio.run(app(scope, receive, send))
    except Exception:
        # Starlette envía la respuesta 500 y luego relanza la excepción para que
        # el servidor la registre; aquí solo interesa la respuesta enviada.
        if not messages:
            raise
    start = next(m for m in messages if m["type"] == "http.response.start")
    headers = {k.decode().lower(): v.decode() for k, v in start["headers"]}
    payload = b"".join(m.get("body", b"") for m in messages if "body" in m)
    return start["status"], headers, json.loads(payload)


def build_test_app() -> FastAPI:
    """App mínima con los manejadores reales, sin base de datos."""
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/dominio")
    def domain_error():
        raise InvalidAdminPinError()

    @app.get("/fallo")
    def unexpected_error():
        raise RuntimeError("detalle interno que no debe filtrarse")

    @app.get("/paginas")
    def pages(page: int):
        return {"page": page}

    return app


class ProblemDetailsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from app.main import app

        cls.api = app
        cls.app = build_test_app()

    def assert_problem(self, status, headers, body, expected_status, expected_code):
        self.assertEqual(status, expected_status)
        self.assertEqual(headers["content-type"], PROBLEM_CONTENT_TYPE)
        self.assertTrue(PROBLEM_MEMBERS <= body.keys(), body)
        self.assertEqual(body["status"], expected_status)
        self.assertEqual(body["code"], expected_code)
        self.assertEqual(body["type"], "about:blank")

    def test_domain_error_uses_code_and_spanish_detail(self):
        status, headers, body = request(self.app, "GET", "/dominio")

        self.assert_problem(status, headers, body, 403, "invalid_admin_pin")
        self.assertEqual(body["title"], "Acceso denegado")
        self.assertEqual(body["detail"], "El PIN de administración no es correcto.")
        self.assertEqual(body["instance"], "/dominio")

    def test_unexpected_error_hides_internal_details(self):
        with self.assertLogs("app.core.exception_handlers", level="ERROR"):
            status, headers, body = request(self.app, "GET", "/fallo")

        self.assert_problem(status, headers, body, 500, "internal_error")
        self.assertNotIn("detalle interno", json.dumps(body))

    def test_query_validation_lists_field_errors_in_spanish(self):
        status, headers, body = request(self.app, "GET", "/paginas", query="page=x")

        self.assert_problem(status, headers, body, 422, "validation_error")
        self.assertEqual(
            body["errors"],
            [
                {
                    "field": "page",
                    "location": "query",
                    "message": "Debe ser un número entero.",
                }
            ],
        )
        self.assertEqual(body["detail"], "«page»: Debe ser un número entero.")

    def test_unknown_route_and_method_use_problem_details(self):
        status, headers, body = request(self.api, "GET", "/api/v1/no-existe")
        self.assert_problem(status, headers, body, 404, "not_found")
        self.assertEqual(body["detail"], "La ruta solicitada no existe.")

        status, headers, body = request(self.api, "PUT", "/api/v1/products")
        self.assert_problem(status, headers, body, 405, "method_not_allowed")
        self.assertIn("allow", headers)

    def test_body_validation_translates_constraints_and_custom_validators(self):
        status, _, body = request(
            self.api,
            "PATCH",
            "/api/v1/products/00000000-0000-0000-0000-000000000000",
            json.dumps({"admin_pin": "12"}).encode(),
        )
        self.assertEqual(status, 422)
        messages = {error["message"] for error in body["errors"]}
        self.assertIn("Debe tener al menos 4 caracteres.", messages)

        status, _, body = request(
            self.api,
            "PATCH",
            "/api/v1/products/00000000-0000-0000-0000-000000000000",
            json.dumps({"admin_pin": "1234"}).encode(),
        )
        self.assertEqual(status, 422)
        self.assertEqual(body["detail"], "Envía al menos un campo para actualizar.")

    def test_invalid_uuid_and_extra_fields_are_explained(self):
        status, _, body = request(
            self.api,
            "POST",
            "/api/v1/products/no-es-uuid/manage",
            json.dumps({"campo_extra": True}).encode(),
        )
        self.assertEqual(status, 422)
        by_field = {error["field"]: error["message"] for error in body["errors"]}
        self.assertEqual(
            by_field["product_id"], "Debe ser un identificador UUID válido."
        )
        self.assertEqual(by_field["campo_extra"], "Este campo no está permitido.")

    def test_malformed_json_is_reported_without_a_field(self):
        status, _, body = request(
            self.api,
            "PATCH",
            "/api/v1/products/00000000-0000-0000-0000-000000000000",
            b"{roto",
        )

        self.assertEqual(status, 422)
        self.assertIsNone(body["errors"][0]["field"])
        self.assertEqual(
            body["detail"], "El cuerpo de la solicitud no es un JSON válido."
        )

    def test_authentication_errors_include_www_authenticate(self):
        status, headers, body = request(
            self.api, "GET", "/api/v1/account-access/me/publications"
        )

        self.assert_problem(status, headers, body, 401, "authentication_required")
        self.assertEqual(headers["www-authenticate"], "Bearer")

    def test_invalid_price_range_is_a_domain_error(self):
        status, headers, body = request(
            self.api, "GET", "/api/v1/products", query="min_price=10&max_price=1"
        )

        self.assert_problem(status, headers, body, 422, "invalid_price_range")

    def test_every_domain_error_has_a_stable_code_and_spanish_message(self):
        english = re.compile(r"\b(the|not|found|invalid|please|error|try)\b", re.I)
        error_classes = [
            value
            for value in vars(exceptions).values()
            if isinstance(value, type) and issubclass(value, AppException)
        ]
        for error_class in error_classes:
            with self.subTest(error=error_class.__name__):
                self.assertRegex(error_class.code, r"^[a-z]+(_[a-z]+)*$")
                self.assertFalse(english.search(error_class.detail), error_class.detail)
                self.assertTrue(error_class.detail.endswith("."))

    def test_openapi_documents_errors_as_problem_json(self):
        schema = self.api.openapi()
        responses = schema["paths"]["/api/v1/products"]["post"]["responses"]

        self.assertIn(PROBLEM_CONTENT_TYPE, responses["4XX"]["content"])
        self.assertNotIn("422", responses)
        self.assertIn("ProblemDetail", schema["components"]["schemas"])


if __name__ == "__main__":
    unittest.main()
