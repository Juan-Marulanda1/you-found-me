import unittest
from uuid import uuid4

from app.core.exceptions import (
    AnnouncementImageLimitExceededError,
    AnnouncementImageNotFoundError,
)
from app.core.security import hash_admin_pin
from app.integrations.supabase_storage import SignedUpload
from app.modules.announcement.enums import AnnouncementStatus
from app.modules.announcement.image_schemas import AnnouncementImageUploadRequest
from app.modules.announcement.image_service import AnnouncementImageService
from app.modules.announcement.model import Announcement


class InMemoryAnnouncementImageRepository:
    def __init__(self):
        self.images = {}

    def list_for_publication(self, announcement_id, *, ready_only=False):
        images = [
            image
            for image in self.images.values()
            if image.announcement_id == announcement_id
            and (not ready_only or image.status == "READY")
        ]
        return sorted(images, key=lambda image: image.position)

    def list_cover_images(self, announcement_ids):
        covers = {}
        for image in self.images.values():
            if image.announcement_id in announcement_ids and image.status == "READY":
                covers.setdefault(image.announcement_id, image)
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
    project_url = "https://project.example"

    def __init__(self):
        self.info = None
        self.created_paths = []
        self.removed = []

    def create_signed_upload(self, path):
        self.created_paths.append(path)
        return SignedUpload(token="upload-token", url="https://storage.example/signed")

    def get_object_info(self, path):
        if self.info is None:
            raise AssertionError(f"No uploaded object metadata for {path}")
        return self.info

    def remove(self, paths):
        self.removed.extend(paths)

    def public_url(self, path):
        return f"{self.project_url}/storage/v1/object/public/product-images/{path}"


class AnnouncementImageTests(unittest.TestCase):
    def setUp(self):
        self.announcement = Announcement(
            title="Clases de guitarra",
            description="Clases para principiantes y estudiantes avanzados.",
            category="Música",
            status=AnnouncementStatus.ACTIVE,
            contact_name="Ana Pérez",
            contact_phone="3001234567",
            city="Medellín",
            admin_pin_hash=hash_admin_pin("123456"),
        )
        self.announcement.id = uuid4()
        self.repository = InMemoryAnnouncementImageRepository()
        self.storage = InMemoryStorage()
        self.service = AnnouncementImageService(
            self.repository,
            self.storage,
            bucket="product-images",
            max_bytes=5 * 1024 * 1024,
            max_count=1,
        )

    def request(self, *, content_type="image/png", size_bytes=123):
        return AnnouncementImageUploadRequest(
            admin_pin="123456",
            content_type=content_type,
            size_bytes=size_bytes,
            alt_text="Clases de guitarra",
        )

    def test_signed_upload_is_scoped_to_announcement_and_one_image(self):
        upload = self.service.create_upload(self.announcement, self.request())

        self.assertTrue(
            upload.path.startswith(f"announcements/{self.announcement.id}/")
        )
        self.assertEqual(upload.bucket, "product-images")
        self.assertEqual(self.storage.created_paths, [upload.path])
        with self.assertRaises(AnnouncementImageLimitExceededError):
            self.service.create_upload(self.announcement, self.request())

    def test_completed_image_is_public_and_can_be_listed_as_cover(self):
        upload = self.service.create_upload(self.announcement, self.request())
        self.storage.info = {
            "size": 123,
            "contentType": "image/png",
            "metadata": {},
        }

        image = self.service.complete(self.announcement.id, upload.id)

        self.assertTrue(image.url.endswith(upload.path))
        self.assertEqual(len(self.service.list_public(self.announcement.id)), 1)
        self.assertEqual(
            self.service.list_cover_images([self.announcement.id])[
                self.announcement.id
            ],
            image,
        )
        managed = self.service.list_management(self.announcement.id)
        self.assertEqual(managed[0].status, "READY")

    def test_image_id_cannot_be_used_for_another_announcement(self):
        upload = self.service.create_upload(self.announcement, self.request())
        with self.assertRaises(AnnouncementImageNotFoundError):
            self.service.complete(uuid4(), upload.id)


if __name__ == "__main__":
    unittest.main()
