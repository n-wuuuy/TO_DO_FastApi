from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select, or_, insert
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from src.database import get_async_session
from src.user.models import User
from src.user.schemas import BaseUser, UserOut, TokenSchema
from src.user.utils import get_hashed_password, create_access_token, create_refresh_token
from src.user.deps import get_current_user

router = APIRouter()


@router.post('/signup', response_model=BaseUser)
async def create_user(data: BaseUser, session: AsyncSession = Depends(get_async_session)):
    query = select(User).where(or_(User.username == data.username,
                                   User.email == data.email))
    result = await session.execute(query)
    if result.scalars().all():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already exist"
        )
    user = {
        'username': data.username,
        'email': data.email,
        'hashed_password': get_hashed_password(data.password),
        'uuid': str(uuid4()),
        'name': data.name,
        'surname': data.surname
    }
    stmt = insert(User).values(user)
    await session.execute(stmt)
    await session.commit()
    return user


@router.post('/login', response_model=TokenSchema)
async def login(form_data: OAuth2PasswordRequestForm = Depends(),
                session: AsyncSession = Depends(get_async_session)):
    query = select(User).where(or_(User.username == form_data.username,
                                   User.hashed_password == get_hashed_password(form_data.password)))
    result = await session.execute(query)
    if result.fetchone() is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email or password"
        )
    return {
        "access_token": create_access_token(form_data.username),
        "refresh_token": create_refresh_token(form_data.username),
    }


@router.get('/me')
async def get_me(user: User = Depends(get_current_user)):
    return user
