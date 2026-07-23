from fastapi import Depends, HTTPException

from app.entity.library.library import DocumentInfo, LibraryInfo
from app.repository.library.document_repository import (
    DocumentRepository,
    get_document_repository,
)
from app.repository.library.library_repository import (
    LibraryRepository,
    get_library_repository,
)
from app.request.library.library import (
    DocumentAddRequest,
    DocumentDeleteRequest,
    DocumentDownloadRequest,
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
    ):
        self.account_id = account_id
        self.library_repository = library_repository
        self.document_repository = document_repository

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

    async def download_document(self, request: DocumentDownloadRequest) -> dict:
        entity = await self.get_document(request.id)
        result = await FileService.get_presigned_download_url(entity.file_key)
        result["fileName"] = f"{entity.file_name}.{entity.file_ext.lstrip('.')}"
        return result

    async def get_document_list(self, library_id: str) -> list[dict]:
        await self._get_owned_library(library_id)
        documents = await self.document_repository.list_documents(library_id)
        return [self._document_to_dict(document) for document in documents]


async def get_library_service(
    account_id: int = Depends(CurrentUser()),
    library_repository: LibraryRepository = Depends(get_library_repository),
    document_repository: DocumentRepository = Depends(get_document_repository),
) -> LibraryService:
    return LibraryService(account_id, library_repository, document_repository)
