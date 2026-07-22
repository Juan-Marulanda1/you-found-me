from fastapi import APIRouter

router =APIRouter()

@router.get(prefix="/announcement", tags=["Announcement"])
def announcement():
    return {"message": "This is the announcement endpoint."}