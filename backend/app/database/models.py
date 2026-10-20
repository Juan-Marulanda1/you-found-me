# Importa todos los modelos para que Alembic los registre en Base.metadata.
# Agrega aquí cada modelo nuevo antes de generar una migración.
from app.database.invitation import PublicationInvitation
from app.database.owner import PublicationOwner
from app.modules.announcement.image_model import AnnouncementImage
from app.modules.announcement.model import Announcement
from app.modules.product.image_model import ProductImage
from app.modules.product.model import Product

__all__ = [
    "Announcement",
    "AnnouncementImage",
    "Product",
    "ProductImage",
    "PublicationInvitation",
    "PublicationOwner",
]
