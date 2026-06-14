from http import HTTPStatus
from typing import Annotated
import uuid
from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import JSONResponse
from app.api.deps import get_current_user, get_doc_service
from app.schema.document import DocumentResponse
from app.schema.user import TokenUser
from app.services.document_service import DocumentService


router = APIRouter(prefix="/documents", tags=["document"])


@router.put("/upload_document/{conversation_id}")
async def upload_docs(
        file: Annotated[UploadFile, File(...)],
        conversation_id: uuid.UUID,
        current_user: Annotated[TokenUser, Depends(get_current_user)],
        document_service: Annotated[DocumentService, Depends(get_doc_service)]
    ):
    return await document_service.upload_document(file, current_user.id, conversation_id)
    


@router.post("/upload_document/new")
async def upload_new_docs(
        file: Annotated[UploadFile, File(...)],
        current_user: Annotated[TokenUser, Depends(get_current_user)],
        document_service: Annotated[DocumentService, Depends(get_doc_service)]
    ):
    return await document_service.upload_document(file, current_user.id, None)


@router.get("/get_document/conversation/{conversation_id}/all", response_model=list[DocumentResponse])
async def get_documents_of_conversation(
        conversation_id: uuid.UUID,
        current_user: Annotated[TokenUser, Depends(get_current_user)],
        document_service: Annotated[DocumentService, Depends(get_doc_service)]
    ):
    return await document_service.get_documents_of_conversation(current_user.id, conversation_id)


@router.get("/get_document/{document_id}/view")
async def get_document(
        document_id: uuid.UUID,
        current_user: Annotated[TokenUser, Depends(get_current_user)],
        document_service: Annotated[DocumentService, Depends(get_doc_service)]
    ):
    return await document_service.get_document_stream(current_user.id, document_id)


@router.delete("/delete-document/{document_id}")
async def delete_document(
        document_id: uuid.UUID,
        current_user: Annotated[TokenUser, Depends(get_current_user)],
        document_service: Annotated[DocumentService, Depends(get_doc_service)]
    ):
    await document_service.delete_document(current_user.id, document_id)
    return JSONResponse(
        content="Document successfully deleted.",
        status_code=HTTPStatus.OK
    )