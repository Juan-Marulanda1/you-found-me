import logging
from collections.abc import Callable
from decimal import Decimal
from uuid import UUID

from app.core.exceptions import InvalidAdminPinError, PublicationNotFoundError
from app.core.pin_limiter import PinAttemptLimiter, pin_attempt_limiter
from app.core.security import hash_admin_pin, verify_admin_pin
from app.modules.publication.repository import PublicationRepository

from .enums import ProductStatus
from .model import Product
from .schemas import ProductCreate, ProductUpdate

logger = logging.getLogger(__name__)


class ProductService:
    def __init__(
        self,
        repository: PublicationRepository[Product],
        limiter: PinAttemptLimiter = pin_attempt_limiter,
    ):
        self.repository = repository
        self.limiter = limiter

    def create(self, data: ProductCreate) -> Product:
        values = data.model_dump(exclude={"admin_pin"})
        product = Product(
            **values,
            admin_pin_hash=hash_admin_pin(data.admin_pin),
            status=ProductStatus.ACTIVE,
        )
        return self.repository.create(product)

    def get_by_id(self, product_id: UUID) -> Product:
        product = self.repository.get_by_id(product_id)
        if product is None:
            raise PublicationNotFoundError()
        return product

    def get_public_by_id(self, product_id: UUID) -> Product:
        product = self.get_by_id(product_id)
        if product.status != ProductStatus.ACTIVE:
            raise PublicationNotFoundError()
        return product

    def get_for_management(
        self, product_id: UUID, admin_pin: str, client_ip: str = "unknown"
    ) -> Product:
        product = self.get_by_id(product_id)
        self._validate_pin(product, admin_pin, client_ip)
        return product

    def list(
        self,
        *,
        page: int,
        page_size: int,
        city: str | None,
        category: str | None,
        status: ProductStatus | None,
        search: str | None,
        min_price: Decimal | None,
        max_price: Decimal | None,
    ):
        return self.repository.list(
            page=page,
            page_size=page_size,
            city=city,
            category=category,
            status=status,
            search=search,
            min_price=min_price,
            max_price=max_price,
        )

    def update(
        self,
        product_id: UUID,
        data: ProductUpdate,
        client_ip: str = "unknown",
    ) -> Product:
        product = self.get_by_id(product_id)
        self._validate_pin(product, data.admin_pin, client_ip)

        updates = data.model_dump(
            exclude_unset=True, exclude={"admin_pin", "new_admin_pin"}
        )
        for field, value in updates.items():
            setattr(product, field, value)
        if data.new_admin_pin:
            product.admin_pin_hash = hash_admin_pin(data.new_admin_pin)
        return self.repository.update(product)

    def delete(
        self,
        product_id: UUID,
        admin_pin: str,
        client_ip: str = "unknown",
        before_delete: Callable[[UUID], None] | None = None,
    ) -> None:
        product = self.get_by_id(product_id)
        self._validate_pin(product, admin_pin, client_ip)
        if before_delete is not None:
            before_delete(product_id)
        self.repository.delete(product)

    def _validate_pin(self, product: Product, admin_pin: str, client_ip: str) -> None:
        self.limiter.check("product", product.id, client_ip)
        if not verify_admin_pin(admin_pin, product.admin_pin_hash):
            self.limiter.record_failure("product", product.id, client_ip)
            logger.warning("Invalid management PIN for product %s", product.id)
            raise InvalidAdminPinError()
        self.limiter.record_success("product", product.id, client_ip)
