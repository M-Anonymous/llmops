# 最先加载环境变量
from dotenv import load_dotenv
load_dotenv(verbose=True)


import uvicorn
from fastapi import FastAPI, Query
from app.router import oauth_router,api_tool_router,file_router,library_router

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Home Page"}

@app.get("/get_weather")
async def get_weather(city: str = Query(...)):
    return {"message": city + "天气很好"}


app.include_router(oauth_router)
app.include_router(api_tool_router)
app.include_router(file_router)
app.include_router(library_router)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)