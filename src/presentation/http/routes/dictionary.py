from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from application.dictionary.create_entry import CreateDictionaryEntryUseCase
from application.dictionary.delete_entry import DeleteDictionaryEntryUseCase
from application.dictionary.dtos import (
    CreateDictionaryEntryInput,
    ListDictionaryEntriesInput,
    UpdateDictionaryEntryInput,
)
from application.dictionary.get_entry import GetDictionaryEntryUseCase
from application.dictionary.list_entries import ListDictionaryEntriesUseCase
from application.dictionary.update_entry import UpdateDictionaryEntryUseCase
from domain.dictionary.entities import DictionaryEntryKind
from domain.dictionary.exceptions import DictionaryEntryNameAlreadyExists, DictionaryEntryNotFound
from presentation.http.dependencies.auth import get_current_user_id
from presentation.http.dependencies.dictionary import (
    get_create_entry_use_case,
    get_delete_entry_use_case,
    get_get_entry_use_case,
    get_list_entries_use_case,
    get_update_entry_use_case,
)
from presentation.http.schemas.dictionary import (
    CreateDictionaryEntryRequest,
    DictionaryEntryResponse,
    PaginatedDictionaryEntriesResponse,
    UpdateDictionaryEntryRequest,
)

# --- global dictionary (/dictionary) ---
router = APIRouter(prefix="/dictionary", tags=["dictionary"])

# --- project-scoped dictionary (/projects/{project_id}/dictionary) ---
project_dictionary_router = APIRouter(
    prefix="/projects/{project_id}/dictionary",
    tags=["dictionary"],
)


def _to_response(result) -> DictionaryEntryResponse:
    return DictionaryEntryResponse(
        id=result.id,
        user_id=result.user_id,
        project_id=result.project_id,
        kind=result.kind,
        name=result.name,
        payload=result.payload,
        created_at=result.created_at,
        updated_at=result.updated_at,
    )


# ── Global routes ─────────────────────────────────────────────────────────────

@router.post("", response_model=DictionaryEntryResponse, status_code=status.HTTP_201_CREATED)
async def create_global_entry(
    body: CreateDictionaryEntryRequest,
    user_id: UUID = Depends(get_current_user_id),
    use_case: CreateDictionaryEntryUseCase = Depends(get_create_entry_use_case),
) -> DictionaryEntryResponse:
    try:
        result = await use_case.execute(
            CreateDictionaryEntryInput(
                user_id=user_id,
                project_id=None,
                kind=body.kind,
                name=body.name,
                payload=body.payload,
            )
        )
    except DictionaryEntryNameAlreadyExists as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    return _to_response(result)


@router.get("", response_model=PaginatedDictionaryEntriesResponse)
async def list_global_entries(
    kind: DictionaryEntryKind | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    user_id: UUID = Depends(get_current_user_id),
    use_case: ListDictionaryEntriesUseCase = Depends(get_list_entries_use_case),
) -> PaginatedDictionaryEntriesResponse:
    result = await use_case.execute(
        ListDictionaryEntriesInput(
            user_id=user_id,
            project_id=None,
            kind=kind,
            page=page,
            page_size=page_size,
        )
    )
    return PaginatedDictionaryEntriesResponse(
        items=[_to_response(e) for e in result.items],
        total=result.total,
        page=result.page,
        page_size=result.page_size,
        total_pages=result.total_pages,
    )


@router.get("/{entry_id}", response_model=DictionaryEntryResponse)
async def get_entry(
    entry_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    use_case: GetDictionaryEntryUseCase = Depends(get_get_entry_use_case),
) -> DictionaryEntryResponse:
    try:
        result = await use_case.execute(id=entry_id, user_id=user_id)
    except DictionaryEntryNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return _to_response(result)


@router.patch("/{entry_id}", response_model=DictionaryEntryResponse)
async def update_entry(
    entry_id: UUID,
    body: UpdateDictionaryEntryRequest,
    user_id: UUID = Depends(get_current_user_id),
    use_case: UpdateDictionaryEntryUseCase = Depends(get_update_entry_use_case),
) -> DictionaryEntryResponse:
    try:
        result = await use_case.execute(
            UpdateDictionaryEntryInput(
                id=entry_id,
                user_id=user_id,
                name=body.name,
                payload=body.payload,
            )
        )
    except DictionaryEntryNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except DictionaryEntryNameAlreadyExists as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    return _to_response(result)


@router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_entry(
    entry_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    use_case: DeleteDictionaryEntryUseCase = Depends(get_delete_entry_use_case),
) -> None:
    try:
        await use_case.execute(id=entry_id, user_id=user_id)
    except DictionaryEntryNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# ── Project-scoped routes ──────────────────────────────────────────────────────

@project_dictionary_router.post("", response_model=DictionaryEntryResponse, status_code=status.HTTP_201_CREATED)
async def create_project_entry(
    project_id: UUID,
    body: CreateDictionaryEntryRequest,
    user_id: UUID = Depends(get_current_user_id),
    use_case: CreateDictionaryEntryUseCase = Depends(get_create_entry_use_case),
) -> DictionaryEntryResponse:
    try:
        result = await use_case.execute(
            CreateDictionaryEntryInput(
                user_id=user_id,
                project_id=project_id,
                kind=body.kind,
                name=body.name,
                payload=body.payload,
            )
        )
    except DictionaryEntryNameAlreadyExists as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    return _to_response(result)


@project_dictionary_router.get("", response_model=PaginatedDictionaryEntriesResponse)
async def list_project_entries(
    project_id: UUID,
    kind: DictionaryEntryKind | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    user_id: UUID = Depends(get_current_user_id),
    use_case: ListDictionaryEntriesUseCase = Depends(get_list_entries_use_case),
) -> PaginatedDictionaryEntriesResponse:
    result = await use_case.execute(
        ListDictionaryEntriesInput(
            user_id=user_id,
            project_id=project_id,
            kind=kind,
            page=page,
            page_size=page_size,
        )
    )
    return PaginatedDictionaryEntriesResponse(
        items=[_to_response(e) for e in result.items],
        total=result.total,
        page=result.page,
        page_size=result.page_size,
        total_pages=result.total_pages,
    )


@project_dictionary_router.get("/{entry_id}", response_model=DictionaryEntryResponse)
async def get_project_entry(
    project_id: UUID,
    entry_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    use_case: GetDictionaryEntryUseCase = Depends(get_get_entry_use_case),
) -> DictionaryEntryResponse:
    try:
        result = await use_case.execute(id=entry_id, user_id=user_id)
    except DictionaryEntryNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return _to_response(result)


@project_dictionary_router.patch("/{entry_id}", response_model=DictionaryEntryResponse)
async def update_project_entry(
    project_id: UUID,
    entry_id: UUID,
    body: UpdateDictionaryEntryRequest,
    user_id: UUID = Depends(get_current_user_id),
    use_case: UpdateDictionaryEntryUseCase = Depends(get_update_entry_use_case),
) -> DictionaryEntryResponse:
    try:
        result = await use_case.execute(
            UpdateDictionaryEntryInput(
                id=entry_id,
                user_id=user_id,
                name=body.name,
                payload=body.payload,
            )
        )
    except DictionaryEntryNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except DictionaryEntryNameAlreadyExists as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    return _to_response(result)


@project_dictionary_router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project_entry(
    project_id: UUID,
    entry_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    use_case: DeleteDictionaryEntryUseCase = Depends(get_delete_entry_use_case),
) -> None:
    try:
        await use_case.execute(id=entry_id, user_id=user_id)
    except DictionaryEntryNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
