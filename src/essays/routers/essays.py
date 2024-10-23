import uuid

from fastapi import APIRouter, UploadFile, File, BackgroundTasks
from fastapi.responses import JSONResponse

from src.essays.common.routes import EssaysRoutes
from src.essays.common.constants import EssayConfiguration
from src.essays.common.error_messages import EssayErrorMessages
from src.essays.usecases.essays import GetMaxWordCountsFromEssays, GetMaxCountsBasedOnID, UploadEssaysFileUseCase

essays_router_v1 = APIRouter(
    prefix=EssaysRoutes.PREFIX,
    tags=EssaysRoutes.TAGS,
)


@essays_router_v1.post(EssaysRoutes.BULK_FILE)
async def upload_essays_file(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    content = await file.read()
    content = content.decode("utf-8")
    http_urls = content.split("\n")
    file_name = file.filename
    file_id = str(uuid.uuid4())

    background_task = UploadEssaysFileUseCase(
        http_urls=http_urls,
        file_name=file_name,
        file_id=file_id
    )
    background_tasks.add_task(background_task.execute)
    return JSONResponse(content={
        "file_id": file_id
    }, status_code=200)


@essays_router_v1.post(EssaysRoutes.BASE_PATH)
async def get_max_occurrence_count(file: UploadFile = File(...)):
    content = await file.read()
    content = content.decode("utf-8")
    http_urls = content.split("\n")
    file_name = file.filename

    if len(http_urls) > EssayConfiguration.MAX_HTTP_URLS_SUPPORTED_FOR_API:
        return JSONResponse(status_code=400, content={"message": EssayErrorMessages.FILE_LIMIT_EXCEED})
    response = await GetMaxWordCountsFromEssays(
        http_urls=http_urls,
        file_name=file_name
    ).execute()
    return JSONResponse(status_code=200, content=response)


@essays_router_v1.get(EssaysRoutes.GET_ESSAYS_BY_ID)
async def get_max_occurrence_count_by_id(file_id: str):
    response = GetMaxCountsBasedOnID(file_id=file_id).execute()
    return JSONResponse(status_code=200, content=response)
