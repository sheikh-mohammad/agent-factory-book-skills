from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import select
from app.database import get_session, SessionDep
from app.models import Item, ItemCreate, ItemPublic, ItemUpdate

router = APIRouter(prefix="/items", tags=["items"])

@router.post("/", response_model=ItemPublic)
async def create_item(
    item: ItemCreate,
    session: SessionDep = Depends(get_session)
):
    db_item = Item(**item.model_dump())
    session.add(db_item)
    await session.commit()
    await session.refresh(db_item)
    return db_item

@router.get("/", response_model=list[ItemPublic])
async def read_items(
    session: SessionDep = Depends(get_session),
    skip: int = 0,
    limit: int = 100
):
    statement = select(Item).offset(skip).limit(limit)
    result = await session.execute(statement)
    return result.scalars().all()

@router.get("/{item_id}", response_model=ItemPublic)
async def read_item(
    item_id: int,
    session: SessionDep = Depends(get_session)
):
    item = await session.get(Item, item_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )
    return item

@router.put("/{item_id}", response_model=ItemPublic)
async def update_item(
    item_id: int,
    item_update: ItemUpdate,
    session: SessionDep = Depends(get_session)
):
    db_item = await session.get(Item, item_id)
    if not db_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )

    for key, value in item_update.model_dump(exclude_unset=True).items():
        setattr(db_item, key, value)

    session.add(db_item)
    await session.commit()
    await session.refresh(db_item)
    return db_item

@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(
    item_id: int,
    session: SessionDep = Depends(get_session)
):
    item = await session.get(Item, item_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )

    await session.delete(item)
    await session.commit()
    return None