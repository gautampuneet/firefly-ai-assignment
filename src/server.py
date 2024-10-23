from fastapi import FastAPI
from fastapi.responses import JSONResponse

from common.constants import ServerConfiguration
from src.essays.routers.essays import essays_router_v1

# Initialize FastAPI app with custom title and version
app = FastAPI(
    title="FireFly AI Assignment",
    version="1.0.0",
    description="This is a FastAPI application with health check and Swagger setup for Firefly assignment.",
    swagger_ui_parameters={"displayRequestDuration": True}
)

# Include Routers
app.include_router(essays_router_v1)


# Health Check API
@app.get("/v1/health", tags=["Health"])
async def health_check():
    """
    Health check API to verify if the server is running properly.
    """
    return JSONResponse(status_code=200, content={
        "status": "healthy"
    })


# Run the FastAPI application using `uvicorn` server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app",
                host=ServerConfiguration.SERVER_HOST,
                port=ServerConfiguration.SERVER_PORT,
                reload=True,
                log_level=ServerConfiguration.LOG_LEVEL.lower()
                )
