import os
import unittest
from unittest.mock import MagicMock, Mock, patch
from uuid import uuid4

os.environ["DEBUG"] = "false"
os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"

from pydantic import ValidationError
from test_publications import call_asgi

from app.core.exceptions import (
    ProductImageLimitExceededError,
    ProductImageUploadPendingError,
    ProductImageValidationError,
)
from app.core.pin_limiter import PinAttemptLimiter
from app.core.security import hash_admin_pin
from app.integrations.supabase_storage import SignedUpload, SupabaseStorage
from app.modules.product.dependencies import (
    get_product_image_service,
    get_product_service,
)
from app.modules.product.enums import ProductStatus
from app.modules.product.image_model import ProductImage
from app.modules.product.image_schemas import ProductImageUploadRequest
from app.modules.product.image_service import ProductImageService
from app.modules.product.model import Product
from app.modules.product.service import ProductService


class InMemoryProductImageRepository:
    def __init__(self):
        self.images: dict = {}

    def list_for_publication(self, product_id, *, ready_only=False):
        images = [
            image
            for image in self.images.values()
            if image.product_id == product_id
            and (not ready_only or image.status == "READY")
        ]
        return sorted(images, key=lambda image: image.position)

    def list_cover_images(self, product_ids):
        covers = {}
        for image in self.images.values():
            if image.product_id in product_ids and image.status == "READY":
                covers.setdefault(image.product_id, image)
        return covers

    def get_by_id(self, image_id):
        return self.images.get(image_id)

    def create(self, image):
        image.id = uuid4()
        self.images[image.id] = image
        return image

    def update(self, image):
        self.images[image.id] = image
        return image

    def delete(self, image):
        self.images.pop(image.id, None)


class InMemoryStorage:
    def __init__(self):
        self.info = None
        self.removed = []
        self.created_paths = []

    def create_signed_upload(self, path):
        self.created_paths.append(path)
        return SignedUpload(
            token="temporary-capability",
            url=f"https://project.example/storage/v1/object/upload/sign/{path}?token=temporary-capability",
        )

    def get_object_info(self, path):
        if self.info is None:
            from app.integrations.supabase_storage import SupabaseStorageError

            raise SupabaseStorageError(not_found=True)
        return self.info

    def remove(self, paths):
        self.removed.extend(paths)

    def public_url(self, path):
        return f"https://project.example/storage/v1/object/public/product-images/{path}"


class ProductImageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import os

        os.environ["DEBUG"] = "false"
        os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"
        from app.main import app

        cls.app = app

    def setUp(self):
        self.app.dependency_overrides.clear()
        self.product = Product(
            title="Mesa de madera",
            description="Mesa artesanal en excelente estado.",
            category="Hogar",
            price=250000,
            currency="COP",
            quantity=1,
            status=ProductStatus.ACTIVE,
            contact_name="Ana Pérez",
            contact_phone="3001234567",
            city="Medellín",
            admin_pin_hash=hash_admin_pin("123456"),
        )
        self.product.id = uuid4()
        self.product_service = ProductService(
            InMemoryProductRepository(self.product),
            limiter=PinAttemptLimiter(max_attempts=5, window_seconds=900),
        )
        self.repository = InMemoryProductImageRepository()
        self.storage = InMemoryStorage()
        self.image_service = ProductImageService(
            self.repository,
            self.storage,
            bucket="product-images",
            max_bytes=5 * 1024 * 1024,
            max_count=8,
        )
        self.app.dependency_overrides[get_product_service] = lambda: (
            self.product_service
        )
        self.app.dependency_overrides[get_product_image_service] = lambda: (
            self.image_service
        )

    def test_upload_request_accepts_only_supported_image_mime_types(self):
        request = ProductImageUploadRequest.model_validate(
            {"admin_pin": "123456", "content_type": "image/webp", "size_bytes": 10}
        )
        self.assertEqual(request.content_type, "image/webp")
        with self.assertRaises(ValidationError):
            ProductImageUploadRequest.model_validate(
                {
                    "admin_pin": "123456",
                    "content_type": "image/svg+xml",
                    "size_bytes": 10,
                }
            )

    def test_upload_url_requires_pin_and_returns_only_scoped_upload_capability(self):
        wrong_status, _ = call_asgi(
            self.app,
            "POST",
            f"/api/v1/products/{self.product.id}/images/upload-url",
            {"admin_pin": "000000", "content_type": "image/jpeg", "size_bytes": 100},
        )
        self.assertEqual(wrong_status, 403)
        self.assertEqual(self.storage.created_paths, [])

        status_code, response = call_asgi(
            self.app,
            "POST",
            f"/api/v1/products/{self.product.id}/images/upload-url",
            {
                "admin_pin": "123456",
                "content_type": "image/jpeg",
                "size_bytes": 100,
                "alt_text": "Vista lateral de la mesa",
            },
        )
        self.assertEqual(status_code, 201)
        data = response["data"]
        self.assertEqual(data["bucket"], "product-images")
        self.assertEqual(data["token"], "temporary-capability")
        self.assertTrue(data["path"].startswith(f"products/{self.product.id}/"))
        self.assertNotIn("service_role", response)

    def test_complete_requires_uploaded_file_and_marks_matching_file_ready(self):
        pending = self.image_service.create_upload(
            self.product,
            ProductImageUploadRequest(
                admin_pin="123456", content_type="image/png", size_bytes=123
            ),
        )
        with self.assertRaises(ProductImageUploadPendingError):
            self.image_service.complete(self.product.id, pending.id)

        self.storage.info = {"size": 123, "contentType": "image/png", "metadata": {}}
        ready = self.image_service.complete(self.product.id, pending.id)
        self.assertEqual(ready.size_bytes, 123)
        self.assertTrue(ready.url.startswith("https://project.example/"))
        self.assertEqual(len(self.image_service.list_public(self.product.id)), 1)

    def test_mismatched_upload_is_removed_and_not_made_public(self):
        pending = self.image_service.create_upload(
            self.product,
            ProductImageUploadRequest(
                admin_pin="123456", content_type="image/png", size_bytes=123
            ),
        )
        self.storage.info = {"size": 321, "contentType": "image/png", "metadata": {}}
        with self.assertRaises(ProductImageValidationError):
            self.image_service.complete(self.product.id, pending.id)
        self.assertEqual(self.storage.removed, [pending.path])
        self.assertEqual(self.image_service.list_public(self.product.id), [])

    def test_image_count_and_byte_limits_are_enforced_before_signing(self):
        self.image_service.max_count = 1
        self.image_service.create_upload(
            self.product,
            ProductImageUploadRequest(
                admin_pin="123456", content_type="image/jpeg", size_bytes=100
            ),
        )
        with self.assertRaises(ProductImageLimitExceededError):
            self.image_service.create_upload(
                self.product,
                ProductImageUploadRequest(
                    admin_pin="123456", content_type="image/jpeg", size_bytes=100
                ),
            )

        other = ProductImageService(
            InMemoryProductImageRepository(),
            InMemoryStorage(),
            bucket="product-images",
            max_bytes=99,
            max_count=8,
        )
        with self.assertRaises(ProductImageValidationError):
            other.create_upload(
                self.product,
                ProductImageUploadRequest(
                    admin_pin="123456", content_type="image/jpeg", size_bytes=100
                ),
            )

    def test_public_image_list_rejects_inactive_product(self):
        self.product.status = ProductStatus.CLOSED
        status_code, _ = call_asgi(
            self.app,
            "GET",
            f"/api/v1/products/{self.product.id}/images",
        )
        self.assertEqual(status_code, 404)

    def test_management_can_list_images_of_inactive_product_with_pin(self):
        self.product.status = ProductStatus.SOLD
        image = ProductImage(
            product_id=self.product.id,
            storage_path=f"products/{self.product.id}/photo.jpg",
            content_type="image/jpeg",
            size_bytes=100,
            position=0,
            status="READY",
        )
        image.id = uuid4()
        self.repository.images[image.id] = image

        status_code, response = call_asgi(
            self.app,
            "POST",
            f"/api/v1/products/{self.product.id}/images/manage",
            {"admin_pin": "123456"},
        )
        self.assertEqual(status_code, 200)
        self.assertEqual(response["data"][0]["status"], "READY")

        denied_status, _ = call_asgi(
            self.app,
            "POST",
            f"/api/v1/products/{self.product.id}/images/manage",
            {"admin_pin": "000000"},
        )
        self.assertEqual(denied_status, 403)

    def test_image_delete_requires_pin_and_removes_storage_object(self):
        upload = self.image_service.create_upload(
            self.product,
            ProductImageUploadRequest(
                admin_pin="123456", content_type="image/jpeg", size_bytes=100
            ),
        )
        path = f"/api/v1/products/{self.product.id}/images/{upload.id}"
        denied_status, _ = call_asgi(self.app, "DELETE", path, {"admin_pin": "000000"})
        self.assertEqual(denied_status, 403)
        self.assertEqual(self.storage.removed, [])

        status_code, _ = call_asgi(self.app, "DELETE", path, {"admin_pin": "123456"})
        self.assertEqual(status_code, 200)
        self.assertEqual(self.storage.removed, [upload.path])
        self.assertIsNone(self.repository.get_by_id(upload.id))


class InMemoryProductRepository:
    def __init__(self, product):
        self.product = product

    def get_by_id(self, product_id):
        if product_id == self.product.id:
            return self.product
        return None

    def delete(self, product):
        pass


class SupabaseStorageAdapterTests(unittest.TestCase):
    def test_signed_url_response_is_resolved_against_storage_api(self):
        storage = SupabaseStorage(
            "https://project.example", "server-secret", "product-images"
        )
        storage._request = Mock(
            return_value={
                "url": "/object/upload/sign/product-images/path.jpg?token=temporary"
            }
        )
        signed = storage.create_signed_upload("path.jpg")
        self.assertEqual(signed.token, "temporary")
        self.assertEqual(
            signed.url,
            "https://project.example/storage/v1/object/upload/sign/product-images/path.jpg?token=temporary",
        )
        storage._request.assert_called_once_with(
            "POST",
            "/object/upload/sign/product-images/path.jpg",
            payload={},
        )

    def test_new_secret_key_is_sent_as_api_key_not_bearer_token(self):
        storage = SupabaseStorage(
            "https://project.example", "sb_secret_backend", "product-images"
        )
        response = MagicMock()
        response.__enter__.return_value.read.return_value = b"{}"

        with patch(
            "app.integrations.supabase_storage.urlopen", return_value=response
        ) as call:
            storage._request("GET", "/object/info/product-images/photo.jpg")

        request = call.call_args.args[0]
        headers = {key.lower(): value for key, value in request.header_items()}
        self.assertEqual(headers["apikey"], "sb_secret_backend")
        self.assertNotIn("authorization", headers)

    def test_legacy_service_role_key_keeps_bearer_compatibility(self):
        legacy_key = "eyJlegacy.jwt"
        storage = SupabaseStorage(
            "https://project.example", legacy_key, "product-images"
        )
        response = MagicMock()
        response.__enter__.return_value.read.return_value = b"{}"

        with patch(
            "app.integrations.supabase_storage.urlopen", return_value=response
        ) as call:
            storage._request("GET", "/object/info/product-images/photo.jpg")

        request = call.call_args.args[0]
        headers = {key.lower(): value for key, value in request.header_items()}
        self.assertEqual(headers["apikey"], legacy_key)
        self.assertEqual(headers["authorization"], f"Bearer {legacy_key}")


if __name__ == "__main__":
    unittest.main()
