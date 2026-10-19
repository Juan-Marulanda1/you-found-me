from sqlalchemy.orm import Session

from app.database.repositories import SQLAlchemyPublicationRepository

from .model import Product


class ProductRepository(SQLAlchemyPublicationRepository[Product]):
    def __init__(self, db: Session):
        super().__init__(db, Product)
