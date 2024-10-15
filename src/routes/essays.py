from fastapi import APIRouter
from fastapi.requests import Request
from src.common.routes import EssayRoutes
from src.schemas.essays import UploadEssays

from src.usecases.essays import UploadEssaysUseCase

essay_router_v1 = APIRouter(
    prefix="/v1",
    tags=EssayRoutes.TAGS
)


@essay_router_v1.post(
    path=EssayRoutes.BASE_PATH
)
async def upload_essay(request: Request, body: UploadEssays):
    return await UploadEssaysUseCase(http_urls=body.links).execute()

