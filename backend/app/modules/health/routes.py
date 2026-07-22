from fastapi import APIRouter

router = APIRouter()

@router.get(prefix="/health", tags=["Health"])
def health():
    return {"status": "healthy"}