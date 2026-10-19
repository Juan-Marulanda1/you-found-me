import os
import unittest
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


class InMemoryAnnouncementRepository:
    def __init__(self, announcement: Announcement | None = None):
        self.announcement = announcement
        self.deleted = False

    def create(self, announcement: Announcement) -> Announcement:
        self.announcement = announcement
        return announcement

    def get_by_id(self, announcement_id):
        if self.announcement and self.announcement.id == announcement_id:
            return self.announcement
        return None

    def list(self, **kwargs):
        raise NotImplementedError

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
        self.assertIn("patch", paths["/api/v1/announcements/{announcement_id}"])
        self.assertIn("/api/v1/products", paths)
        self.assertIn("patch", paths["/api/v1/products/{product_id}"])

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
