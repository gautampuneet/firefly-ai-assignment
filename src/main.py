import pytz
from fastapi import FastAPI
from datetime import datetime
from fastapi.responses import RedirectResponse, JSONResponse
from src.routes import essay_router_v1

firefly_app = FastAPI(
    title="Firefly Assignment API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url=None,
    swagger_ui_parameters={"displayRequestDuration": True},
    openapi_url="/openapi.json"
)

APPLICATION_STARTUP_TIME_IN_UTC = None


firefly_app.include_router(essay_router_v1)


@firefly_app.on_event("startup")
def startup_event():
    global APPLICATION_STARTUP_TIME_IN_UTC
    APPLICATION_STARTUP_TIME_IN_UTC = datetime.now(pytz.utc)


# Redirect root to health
@firefly_app.get("/", tags=["base"], include_in_schema=False)
async def main_route():
    return RedirectResponse(url="/v1/health", status_code=301)


@firefly_app.get("/v1/health", tags=["base"])
async def main_route():
    return JSONResponse(
        status_code=200,
        content={
            "status": "Decode Backend!",
            "startup_time": str(APPLICATION_STARTUP_TIME_IN_UTC),
            "duration": (
                    datetime.now(pytz.utc) - APPLICATION_STARTUP_TIME_IN_UTC
            ).total_seconds(),
            "version": "1.0.0",
        }
    )

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app="main:firefly_app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )