from contextlib import asynccontextmanager
from app.component.database.postgres_client import PostgresClient
import uvicorn
from fastapi import FastAPI
from app.router import home_router,oauth_router,api_tool_router,file_router,library_router,session_router,test_router

@asynccontextmanager
async def lifespan(fastapi: FastAPI):
    #初始化
    await PostgresClient.initialize()

    yield

    #关闭连接
    await PostgresClient.cleanup()

app = FastAPI(lifespan=lifespan)

app.include_router(home_router)
app.include_router(oauth_router)
app.include_router(api_tool_router)
app.include_router(file_router)
app.include_router(library_router)

app.include_router(session_router)
app.include_router(test_router)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)