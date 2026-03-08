from fastapi import Depends, HTTPException, status
from sqlmodel import select
from app.database import get_session, SessionDep
from app.models import User
from app.auth.security import decode_access_token

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: SessionDep = Depends(get_session)
) -> User:
    username = decode_access_token(token)

    statement = select(User).where(User.username == username)
    result = await session.execute(statement)
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )
    return user

async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

# Type aliases for dependency injection
CurrentUser = Depends(get_current_active_user)