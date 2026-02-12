from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.services import moderator_create, s3storage_manager
from app.api.auth.views import router as auth_router
from app.api.users.views import router as users_router
from app.api.posts.views import router as posts_router
from app.api.images.views import router as images_router
from app.middleware import AuthMiddleware


@asynccontextmanager
async def lifespan(
    application: FastAPI,
):
    await moderator_create()
    await s3storage_manager.initialize_buckets()
    yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(AuthMiddleware)

app.include_router(auth_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")
app.include_router(posts_router, prefix="/api/v1")
app.include_router(images_router, prefix="/api/v1")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", reload=True)
