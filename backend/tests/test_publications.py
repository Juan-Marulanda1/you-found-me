import asyncio
import json
import os
import unittest
from datetime import UTC, datetime
from urllib.parse import urlsplit
from uuid import uuid4

from pydantic import ValidationError

from app.core.exceptions import InvalidAdminPinError, TooManyAdminPinAttemptsError
from app.core.pin_limiter import PinAttemptLimiter
from app.core.security import hash_admin_pin, verify_admin_pin
from app.modules.announcement.enums import AnnouncementStatus
from app.modules.announcement.model import Announcement
from app.modules.announcement.schemas import AnnouncementCreate, AnnouncementUpdate
from app.modules.announcement.service import AnnouncementService
from app.modules.product.schemas import ProductCreate
from app.modules.product.service import ProductService
from app.modules.publication.repository import PageResult


def call_asgi(app, method: str, path: str, body: dict | None = None):
    """Exercise the real FastAPI router without requiring a test-client extra."""
    parsed_path = urlsplit(path)
    request_body = json.dumps(body).encode() if body is not None else b""
    messages = []
    request_sent = False

    async def receive():
        nonlocal request_sent
        if request_sent:
            return {"type": "http.disconnect"}
        request_sent = True
        return {"type": "http.request", "body": request_body, "more_body": False}

    async def send(message):
        messages.append(message)

    scope = {
        "type": "http",
        "asgi": {"version": "3.0", "spec_version": "2.3"},
        "http_version": "1.1",
        "method": method,
        "scheme": "http",
        "path": parsed_path.path,
        "raw_path": parsed_path.path.encode(),
        "query_string": parsed_path.query.encode(),
        "root_path": "",
        "headers": [
            (b"host", b"testserver"),
            (b"content-type", b"application/json"),
            (b"content-length", str(len(request_body)).encode()),
        ],
        "client": ("127.0.0.1", 12345),
        "server": ("testserver", 80),
    }
    asyncio.run(app(scope, receive, send))
    response = next(
        message for message in messages if message["type"] == "http.response.start"
    )
    response_body = b"".join(
        message.get("body", b"")
        for message in messages
        if message["type"] == "http.response.body"
    )
    return response["status"], json.loads(response_body) if response_body else None


def prepare_persisted_entity(entity):
    now = datetime.now(UTC)
    entity.id = uuid4()
    entity.created_at = now
    entity.updated_at = now
    return entity


class InMemoryAnnouncementRepository:
    def __init__(self, announcement: Announcement | None = None):
        self.announcement = announcement
        self.deleted = False

    def create(self, announcement: Announcement) -> Announcement:
        self.announcement = prepare_persisted_entity(announcement)
        return announcement

    def get_by_id(self, announcement_id):
        if self.announcement and self.announcement.id == announcement_id:
            return self.announcement
        return None

    def list(self, **kwargs):
        if self.announcement is None:
            return PageResult(items=[], total=0)
        status = kwargs.get("status")
        if status is not None and self.announcement.status != status:
            return PageResult(items=[], total=0)
        return PageResult(items=[self.announcement], total=1)

    def update(self, announcement: Announcement) -> Announcement:
        self.announcement = announcement
        return announcement

    def delete(self, announcement: Announcement) -> None:
        self.deleted = True


class ManagementPinTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ["DEBUG"] = "false"
        os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"
        from app.main import app

        cls.app = app

    def setUp(self):
        self.app.dependency_overrides.clear()

    def test_pin_hash_is_salted_and_verifiable(self):
        first_hash = hash_admin_pin("123456")
        second_hash = hash_admin_pin("123456")

        self.assertNotEqual(first_hash, "123456")
        self.assertNotEqual(first_hash, second_hash)
        self.assertTrue(verify_admin_pin("123456", first_hash))
        self.assertFalse(verify_admin_pin("000000", first_hash))

    def test_pin_limiter_blocks_after_five_failed_attempts(self):
        limiter = PinAttemptLimiter(max_attempts=5, window_seconds=900)
        publication_id = uuid4()

        for _ in range(5):
            limiter.record_failure("product", publication_id, "127.0.0.1")

        with self.assertRaises(TooManyAdminPinAttemptsError):
            limiter.check("product", publication_id, "127.0.0.1")

    def test_announcement_creation_requires_six_digit_pin(self):
        data = self.announcement_data()
        self.assertEqual(AnnouncementCreate.model_validate(data).admin_pin, "123456")

        data["admin_pin"] = "1234"
        with self.assertRaises(ValidationError):
            AnnouncementCreate.model_validate(data)

    def test_product_create_contract(self):
        product = ProductCreate.model_validate(
            {
                "admin_pin": "123456",
                "title": "Mesa de madera",
                "description": "Mesa artesanal en excelente estado.",
                "category": "Hogar",
                "price": "250000.00",
                "contact_name": "Ana Pérez",
                "contact_phone": "3001234567",
                "city": "Medellín",
            }
        )
        self.assertEqual(str(product.price), "250000.00")
        self.assertEqual(product.currency, "COP")

    def test_product_service_hashes_management_pin(self):
        from unittest.mock import Mock

        repository = Mock()
        repository.create.side_effect = lambda product: product
        service = ProductService(repository)
        product = service.create(
            ProductCreate.model_validate(
                {
                    "admin_pin": "123456",
                    "title": "Mesa de madera",
                    "description": "Mesa artesanal en excelente estado.",
                    "category": "Hogar",
                    "price": "250000.00",
                    "contact_name": "Ana Pérez",
                    "contact_phone": "3001234567",
                    "city": "Medellín",
                }
            )
        )
        self.assertTrue(verify_admin_pin("123456", product.admin_pin_hash))

    def test_public_announcement_hides_private_fields_and_inactive_items(self):
        from app.modules.announcement.dependencies import get_announcement_service

        repository = InMemoryAnnouncementRepository()
        service = AnnouncementService(repository)
        data = self.announcement_data()
        data.update(contact_email="hola@horno.example", address="Laureles")
        announcement = service.create(AnnouncementCreate.model_validate(data))
        announcement.id = uuid4()
        self.app.dependency_overrides[get_announcement_service] = lambda: service

        status_code, response = call_asgi(
            self.app, "GET", f"/api/v1/announcements/{announcement.id}"
        )

        self.assertEqual(status_code, 200)
        public_data = response["data"]
        self.assertIsNone(public_data["contact_phone"])
        self.assertNotIn("contact_email", public_data)
        self.assertNotIn("address", public_data)

        announcement.status = AnnouncementStatus.CLOSED
        status_code, _ = call_asgi(
            self.app, "GET", f"/api/v1/announcements/{announcement.id}"
        )
        self.assertEqual(status_code, 404)

        status_code, response = call_asgi(
            self.app,
            "GET",
            "/api/v1/announcements",
        )
        self.assertEqual(status_code, 200)
        self.assertEqual(response["data"]["items"], [])

    def test_management_access_returns_private_announcement_with_pin_only(self):
        from app.modules.announcement.dependencies import get_announcement_service

        repository = InMemoryAnnouncementRepository()
        service = AnnouncementService(repository)
        data = self.announcement_data()
        data.update(contact_email="hola@horno.example", address="Laureles")
        announcement = service.create(AnnouncementCreate.model_validate(data))
        announcement.id = uuid4()
        announcement.status = AnnouncementStatus.PAUSED
        self.app.dependency_overrides[get_announcement_service] = lambda: service

        wrong_pin_status, _ = call_asgi(
            self.app,
            "POST",
            f"/api/v1/announcements/{announcement.id}/manage",
            {"admin_pin": "000000"},
        )
        self.assertEqual(wrong_pin_status, 403)

        status_code, response = call_asgi(
            self.app,
            "POST",
            f"/api/v1/announcements/{announcement.id}/manage",
            {"admin_pin": "123456"},
        )
        self.assertEqual(status_code, 200)
        private_data = response["data"]
        self.assertEqual(private_data["contact_email"], "hola@horno.example")
        self.assertEqual(private_data["address"], "Laureles")
        self.assertEqual(private_data["contact_phone"], "3001234567")
        self.assertEqual(private_data["status"], "PAUSED")

    def test_product_phone_is_public_only_with_explicit_consent(self):
        from app.modules.product.dependencies import get_product_service

        repository = type("MemoryProductRepository", (), {})()

        def create_product(product):
            return prepare_persisted_entity(product)

        repository.create = create_product
        repository.get_by_id = lambda product_id: product
        product = ProductService(repository).create(
            ProductCreate.model_validate(
                {
                    "admin_pin": "123456",
                    "title": "Mesa de madera",
                    "description": "Mesa artesanal en excelente estado.",
                    "category": "Hogar",
                    "price": "250000.00",
                    "contact_name": "Ana Pérez",
                    "contact_phone": "3001234567",
                    "contact_phone_public": True,
                    "contact_email": "privado@example.com",
                    "city": "Medellín",
                    "address": "Laureles",
                }
            )
        )
        product.id = uuid4()
        repository.list = lambda **kwargs: PageResult(items=[product], total=1)
        self.app.dependency_overrides[get_product_service] = lambda: ProductService(
            repository
        )

        status_code, response = call_asgi(
            self.app, "GET", f"/api/v1/products/{product.id}"
        )

        self.assertEqual(status_code, 200)
        public_data = response["data"]
        self.assertEqual(public_data["contact_phone"], "3001234567")
        self.assertNotIn("contact_email", public_data)
        self.assertNotIn("address", public_data)

    def test_create_response_does_not_echo_private_contact_fields(self):
        from app.modules.announcement.dependencies import get_announcement_service

        service = AnnouncementService(InMemoryAnnouncementRepository())
        self.app.dependency_overrides[get_announcement_service] = lambda: service
        payload = self.announcement_data()
        payload.update(contact_email="hola@horno.example", address="Laureles")

        status_code, response = call_asgi(
            self.app, "POST", "/api/v1/announcements", payload
        )

        self.assertEqual(status_code, 201)
        public_data = response["data"]
        self.assertIsNone(public_data["contact_phone"])
        self.assertNotIn("contact_email", public_data)
        self.assertNotIn("address", public_data)

    def test_proxy_headers_are_trusted_only_from_configured_networks(self):
        from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

        observed_clients = []

        async def app(scope, receive, send):
            observed_clients.append(scope["client"])

        middleware = ProxyHeadersMiddleware(app, trusted_hosts=["10.0.0.0/8"])

        async def run_case(peer_ip: str):
            async def receive():
                return {"type": "http.request", "body": b"", "more_body": False}

            async def send(message):
                return None

            await middleware(
                {
                    "type": "http",
                    "scheme": "http",
                    "client": (peer_ip, 8000),
                    "headers": [(b"x-forwarded-for", b"203.0.113.99")],
                },
                receive,
                send,
            )

        asyncio.run(run_case("198.51.100.10"))
        asyncio.run(run_case("10.20.30.40"))

        self.assertEqual(observed_clients[0][0], "198.51.100.10")
        self.assertEqual(observed_clients[1][0], "203.0.113.99")

    def test_api_server_passes_configured_proxy_allowlist_to_uvicorn(self):
        import sys
        from unittest.mock import patch

        import server
        from app.core.config import settings

        with (
            patch.object(sys, "argv", ["server.py"]),
            patch.object(server.uvicorn, "run") as run_server,
        ):
            server.main()

        run_server.assert_called_once()
        self.assertTrue(run_server.call_args.kwargs["proxy_headers"])
        self.assertEqual(
            run_server.call_args.kwargs["forwarded_allow_ips"],
            settings.FORWARDED_ALLOW_IPS,
        )

    def test_proxy_allowlist_rejects_wildcard_and_invalid_addresses(self):
        from app.core.config import Settings

        for allowlist in ("*", "not-an-ip"):
            with self.subTest(allowlist=allowlist):
                with self.assertRaises(ValidationError):
                    Settings(
                        _env_file=None,
                        DATABASE_URL="sqlite+pysqlite:///:memory:",
                        DEBUG=False,
                        FORWARDED_ALLOW_IPS=allowlist,
                    )

    def test_update_requires_pin_and_at_least_one_field(self):
        with self.assertRaises(ValidationError):
            AnnouncementUpdate.model_validate({"admin_pin": "123456"})

        with self.assertRaises(ValidationError):
            AnnouncementUpdate.model_validate(
                {"admin_pin": "123456", "contact_name": None}
            )

        update = AnnouncementUpdate.model_validate(
            {"admin_pin": "123456", "address": None, "status": "CLOSED"}
        )
        self.assertIsNone(update.address)
        self.assertEqual(update.status, AnnouncementStatus.CLOSED)

    def test_service_hashes_pin_and_requires_it_for_edit_and_delete(self):
        repository = InMemoryAnnouncementRepository()
        service = AnnouncementService(repository)
        announcement = service.create(
            AnnouncementCreate.model_validate(self.announcement_data())
        )
        announcement.id = uuid4()

        self.assertTrue(verify_admin_pin("123456", announcement.admin_pin_hash))
        self.assertNotEqual(announcement.admin_pin_hash, "123456")

        with self.assertRaises(InvalidAdminPinError):
            service.update(
                announcement.id,
                AnnouncementUpdate.model_validate(
                    {"admin_pin": "000000", "title": "Cambio rechazado"}
                ),
            )

        updated = service.update(
            announcement.id,
            AnnouncementUpdate.model_validate(
                {"admin_pin": "123456", "title": "Aviso actualizado"}
            ),
        )
        self.assertEqual(updated.title, "Aviso actualizado")

        service.update(
            announcement.id,
            AnnouncementUpdate.model_validate(
                {"admin_pin": "123456", "new_admin_pin": "654321"}
            ),
        )
        self.assertFalse(verify_admin_pin("123456", announcement.admin_pin_hash))
        self.assertTrue(verify_admin_pin("654321", announcement.admin_pin_hash))

        with self.assertRaises(InvalidAdminPinError):
            service.delete(announcement.id, "123456")
        service.delete(announcement.id, "654321")
        self.assertTrue(repository.deleted)

    def test_openapi_includes_both_listing_domains_and_management_routes(self):
        paths = self.app.openapi()["paths"]
        self.assertIn("/api/v1/announcements", paths)
        self.assertIn("/api/v1/announcements/{announcement_id}/manage", paths)
        self.assertIn("patch", paths["/api/v1/announcements/{announcement_id}"])
        self.assertIn("/api/v1/products", paths)
        self.assertIn("/api/v1/products/{product_id}/manage", paths)
        self.assertIn("patch", paths["/api/v1/products/{product_id}"])
        announcement_filters = {
            parameter["name"]
            for parameter in paths["/api/v1/announcements"]["get"]["parameters"]
        }
        self.assertNotIn("status", announcement_filters)

    def test_alembic_model_registry_contains_all_tables(self):
        import app.database.models as registered_models
        from app.database.base import Base

        self.assertCountEqual(registered_models.__all__, ["Announcement", "Product"])
        self.assertCountEqual(Base.metadata.tables, ["announcements", "products"])

    @staticmethod
    def announcement_data():
        return {
            "admin_pin": "123456",
            "title": "Café de especialidad",
            "description": "Emprendimiento local con café tostado fresco.",
            "category": "Alimentos",
            "business_name": "Café Andino",
            "contact_name": "Ana Pérez",
            "contact_phone": "3001234567",
            "city": "Medellín",
        }


if __name__ == "__main__":
    unittest.main()
