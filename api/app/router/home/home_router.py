from fastapi import APIRouter, Query

home_router = APIRouter()


@home_router.get("/")
async def root():
    return {"message": "Home Page"}

@home_router.get("/get_weather")
async def get_weather(city: str = Query(...)):
    return {"message": city + "天气很好"}
