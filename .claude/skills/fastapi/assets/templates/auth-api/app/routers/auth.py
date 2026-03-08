from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import select
from app.database import get_session, SessionDep
from app.models import User, UserCreate, UserPublic, UserUpdate
from app.auth.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    oauth2_scheme
)
from app.auth.dependencies import get_current_active_user

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=UserPublic)
async def register(
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

    # Create new user
    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=get_password_hash(user.password)
    )
    session.add(db_user)
    await session.commit()
    await session.refresh(db_user)
    return db_user

@router.post("/token")
async def login(
    username: str,
    password: str,
    session: SessionDep = Depends(get_session)
):
    # Find user
    statement = select(User).where(User.username == username)
    result = await session.execute(statement)
    user = result.scalar_one_or_none()

    # Verify credentials
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create token
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserPublic)
async def read_users_me(
    current_user: User = Depends(get_current_active_user)
):
    return current_user

@router.put("/me", response_model=UserPublic)
async def update_user_me(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    session: SessionDep = Depends(get_session)
):
    # Update current user
    for key, value in user_update.model_dump(exclude_unset=True).items():
        setattr(current_user, key, value)

    session.add(current_user)
    await session.commit()
    await session.refresh(current_user)
    return current_user