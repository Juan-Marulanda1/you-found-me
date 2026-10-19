from fastapi import Depends
from sqlalchemy.orm import Session

from app.database.session import get_db

from .repository import ProductRepository
from .service import ProductService


def get_product_service(db: Session = Depends(get_db)) -> ProductService:
    return ProductService(ProductRepository(db))
