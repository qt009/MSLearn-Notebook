from fastapi import APIRouter
router = APIRouter()


@router.post("/scrap/{cert_id}")
async def scrap_certificate(cert_id):
    