import os
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware import Middleware

from app.component.database.postgres_client import PostgresClient
from app.router import home_router,oauth_router,api_tool_router,file_router,library_router,session_router,test_router

@asynccontextmanager
async def lifespan(fastapi: FastAPI):
    #初始化
    await PostgresClient.initialize()

    yield

    #关闭连接
    await PostgresClient.cleanup()

frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")

API_PREFIX = "/api"

app = FastAPI(
    lifespan=lifespan,
    middleware=[
        Middleware(
            CORSMiddleware, # noqa
            allow_origins=[frontend_url],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        ),
    ],
)

app.include_router(home_router, prefix=API_PREFIX)
app.include_router(oauth_router, prefix=API_PREFIX)
app.include_router(api_tool_router, prefix=API_PREFIX)
app.include_router(file_router, prefix=API_PREFIX)
app.include_router(library_router, prefix=API_PREFIX)

app.include_router(session_router, prefix=API_PREFIX)
app.include_router(test_router, prefix=API_PREFIX)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8888)