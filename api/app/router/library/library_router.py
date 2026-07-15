from fastapi import APIRouter

library_router = APIRouter(prefix="/library")

@library_router.post("/create")
async def create_library():
    pass

@library_router.post("/delete")
async def delete_library():
    pass

@library_router.get("/update")
async def update_library():
    pass

@library_router.get("/list")
async def get_library_list():
    pass

@library_router.post("/document/add")
async def add_document():
    pass

@library_router.post("/document/delete")
async def delete_document():
    pass

@library_router.post("/document/update")
async def update_document():
    pass

@library_router.get("/document/list")
async def get_document_list():
    pass

@library_router.post("/document/segment/add")
async def add_segment():
    pass

@library_router.post("/document/segment/delete")
async def delete_segment():
    pass

@library_router.post("/document/segment/update")
async def update_segment():
    pass

@library_router.get("/document/segment/list")
async def get_segment_list():
    pass
