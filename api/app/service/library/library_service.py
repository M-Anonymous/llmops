from fastapi import Depends, HTTPException

from app.entity.library.library import ChunkInfo, DocumentInfo, LibraryInfo
from app.repository.library.chunk_repository import (
    ChunkRepository,
    get_chunk_repository,
)
from app.repository.library.document_repository import (
    DocumentRepository,
    get_document_repository,
)
from app.repository.library.library_repository import (
    LibraryRepository,
    get_library_repository,
)
from app.request.library.library import (
    ChunkAddRequest,
    ChunkBatchAddRequest,
    ChunkDeleteRequest,
    ChunkUpdateRequest,
    DocumentAddRequest,
    DocumentDeleteRequest,
    DocumentDownloadRequest,
    DocumentParseRequest,
    DocumentUpdateStatusRequest,
    LibraryDeleteRequest,
    LibraryRequest,
    LibraryUpdateRequest,
)
from app.service.file.file_service import FileService
from app.service.oauth.current_user import CurrentUser


class LibraryService:

    def __init__(
        self,
        account_id: int,
        library_repository: LibraryRepository,
        document_repository: DocumentRepository,
        chunk_repository: ChunkRepository,
    ):
        self.account_id = account_id
        self.library_repository = library_repository
        self.document_repository = document_repository
        self.chunk_repository = chunk_repository

    async def _get_owned_library(self, library_id: str) -> LibraryInfo:
        entity = await self.library_repository.find_library(library_id, self.account_id)
        if not entity:
            raise HTTPException(status_code=404, detail="知识库不存在")
        return entity

    @staticmethod
    def _to_dict(entity: LibraryInfo) -> dict:
        return {
            "id": entity.id,
            "name": entity.name,
            "desc": entity.desc,
            "icon": entity.icon,
            "createAt": entity.create_at,
            "updateAt": entity.update_at,
        }

    async def create_library(self, request: LibraryRequest) -> str:
        data = request.model_dump(exclude_unset=True)
        entity = LibraryInfo(account_id=self.account_id, **data)
        created = await self.library_repository.add_library(entity)
        return created.id

    async def delete_library(self, request: LibraryDeleteRequest) -> None:
        entity = await self._get_owned_library(request.id)
        await self.library_repository.delete_library(entity)

    async def update_library(self, request: LibraryUpdateRequest) -> dict:
        entity = await self._get_owned_library(request.id)
        data = request.model_dump(exclude_unset=True, exclude={"id"})
        if not data:
            raise HTTPException(status_code=400, detail="未提供需要更新的字段")
        for key, value in data.items():
            setattr(entity, key, value)
        updated = await self.library_repository.update_library(entity)
        return self._to_dict(updated)

    async def get_library_list(self) -> list[dict]:
        libraries = await self.library_repository.list_libraries(self.account_id)
        return [self._to_dict(library) for library in libraries]

    @staticmethod
    def _document_to_dict(entity: DocumentInfo) -> dict:
        return {
            "id": entity.id,
            "accountId": entity.account_id,
            "libraryId": entity.library_id,
            "fileName": entity.file_name,
            "fileExt": entity.file_ext,
            "desc": entity.desc,
            "fileKey": entity.file_key,
            "status": entity.status,
            "createAt": entity.create_at,
            "updateAt": entity.update_at,
        }

    async def get_document(self, document_id: str) -> DocumentInfo:
        entity = await self.document_repository.find_document(document_id, self.account_id)
        if not entity:
            raise HTTPException(status_code=404, detail="文档不存在")
        return entity

    async def add_document(self, request: DocumentAddRequest) -> str:
        await self._get_owned_library(request.library_id)
        entity = DocumentInfo(
            account_id=self.account_id,
            library_id=request.library_id,
            file_name=request.file_name,
            file_ext=request.file_ext.lstrip("."),
            desc=request.desc,
            file_key=request.file_key,
        ) # noqa
        created = await self.document_repository.add_document(entity)
        return created.id

    async def delete_document(self, request: DocumentDeleteRequest) -> None:
        entity = await self.get_document(request.id)
        await self.document_repository.delete_document(entity)

    async def update_document_status(self, request: DocumentUpdateStatusRequest) -> dict:
        entity = await self.get_document(request.id)
        entity.status = request.status
        updated = await self.document_repository.update_document(entity)
        return self._document_to_dict(updated)

    async def download_document(self, request: DocumentDownloadRequest) -> dict:
        entity = await self.get_document(request.id)
        result = await FileService.get_presigned_download_url(entity.file_key)
        result["fileName"] = f"{entity.file_name}.{entity.file_ext.lstrip('.')}"
        return result

    async def parse_document(self, request: DocumentParseRequest) -> dict:
        from app.task.task import process_document_task

        await self.get_document(request.id)
        task = process_document_task.delay(
            request.id,
            self.account_id,
            request.splitter_type.value,
            request.splitter_params,
        )
        return {"taskId": task.id}

    async def get_document_list(self, library_id: str) -> list[dict]:
        await self._get_owned_library(library_id)
        documents = await self.document_repository.list_documents(library_id)
        return [self._document_to_dict(document) for document in documents]

    @staticmethod
    def _chunk_to_dict(entity: ChunkInfo) -> dict:
        return {
            "id": entity.id,
            "documentId": entity.document_id,
            "position": entity.position,
            "content": entity.content,
            "hash": entity.hash,
            "enabled": entity.enabled,
            "createAt": entity.create_at,
            "updateAt": entity.update_at,
        }

    async def get_chunk(self, chunk_id: str) -> ChunkInfo:
        entity = await self.chunk_repository.find_chunk(chunk_id)
        if not entity:
            raise HTTPException(status_code=404, detail="分片不存在")
        await self.get_document(entity.document_id)
        return entity

    async def add_chunk(self, request: ChunkAddRequest) -> str:
        await self.get_document(request.document_id)
        entity = ChunkInfo(
            document_id=request.document_id,
            position=request.position,
            content=request.content,
            hash=request.hash,
            enabled=request.enabled,
        )
        created = await self.chunk_repository.add_chunk(entity)
        return created.id

    async def batch_add_chunks(self, request: ChunkBatchAddRequest) -> list[str]:
        await self.get_document(request.document_id)
        entities = [
            ChunkInfo(
                document_id=request.document_id,
                position=item.position,
                content=item.content,
                hash=item.hash,
                enabled=item.enabled,
            )
            for item in request.chunks
        ]
        created = await self.chunk_repository.add_chunks(entities)
        return [chunk.id for chunk in created]

    async def delete_chunk(self, request: ChunkDeleteRequest) -> None:
        entity = await self.get_chunk(request.id)
        await self.chunk_repository.delete_chunk(entity)

    async def update_chunk(self, request: ChunkUpdateRequest) -> dict:
        entity = await self.get_chunk(request.id)
        data = request.model_dump(exclude_unset=True, exclude={"id"})
        if not data:
            raise HTTPException(status_code=400, detail="未提供需要更新的字段")
        for key, value in data.items():
            setattr(entity, key, value)
        updated = await self.chunk_repository.update_chunk(entity)
        return self._chunk_to_dict(updated)

    async def get_chunk_list(self, document_id: str) -> list[dict]:
        await self.get_document(document_id)
        chunks = await self.chunk_repository.list_chunks(document_id)
        return [self._chunk_to_dict(chunk) for chunk in chunks]


async def get_library_service(
    account_id: int = Depends(CurrentUser()),
    library_repository: LibraryRepository = Depends(get_library_repository),
    document_repository: DocumentRepository = Depends(get_document_repository),
    chunk_repository: ChunkRepository = Depends(get_chunk_repository),
) -> LibraryService:
    return LibraryService(
        account_id,
        library_repository,
        document_repository,
        chunk_repository,
    )
