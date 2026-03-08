from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import select
from app.database import get_session, SessionDep
from app.models import User, UserCreate, UserPublic, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/", response_model=UserPublic)
async def create_user(
    user: UserCreate,
    session: SessionDep = Depends(get_session)
):
    # Check if user already exists
    statement = select(User).where(User.username == user.username)
    result = await session.execute(statement)
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )

    # Create new user (hash password in real app)
    db_user = User(**user.model_dump())
    session.add(db_user)
    await session.commit()
    await session.refresh(db_user)
    return db_user

@router.get("/", response_model=list[UserPublic])
async def read_users(
    session: SessionDep = Depends(get_session),
    skip: int = 0,
    limit: int = 100
):
    statement = select(User).offset(skip).limit(limit)
    result = await session.execute(statement)
    return result.scalars().all()

@router.get("/{user_id}", response_model=UserPublic)
async def read_user(
    user_id: int,
    session: SessionDep = Depends(get_session)
):
    user = await session.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user

@router.put("/{user_id}", response_model=UserPublic)
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    session: SessionDep = Depends(get_session)
):
    db_user = await session.get(User, user_id)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    for key, value in user_update.model_dump(exclude_unset=True).items():
        setattr(db_user, key, value)

    session.add(db_user)
    await session.commit()
    await session.refresh(db_user)
    return db_user

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    session: SessionDep = Depends(get_session)
):
    user = await session.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    await session.delete(user)
    await session.commit()
    return None