from app.services.HTTPClient import HTTPClient
from app.scraper.helper import getAccessToken
from fastapi import APIRouter
router = APIRouter()


@router.post("/scrap/{cert_id}")
def scrap_certificate(cert_id):
    token = getAccessToken()
    print(token)

    res = HTTPClient.get(f"https://learn.microsoft.com/en-us/training/support/integrations-learn-platform-api-catalog")
    print(res)