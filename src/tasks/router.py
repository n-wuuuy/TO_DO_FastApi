import os
import time
from functools import wraps
from uuid import UUID

from fastapi.openapi.models import Response
from fastapi_cache.backends import redis
from fastapi_cache.decorator import cache
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy import select, insert, update, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from starlette.requests import Request

from src.database import get_async_session
from src.tasks.models import Task, GroupTasks, GroupAccess, Role
from src.tasks.schemas import TaskCreate, GroupCreate, TaskUpdate, GroupUpdate, GroupGetWithTask, GroupGet, \
    AccessGroupUpdate, AccessGroupPost
from src.user.deps import get_current_user
from src.tasks.permissions import is_success_role_admin, is_success_role_admin_or_manager_for_task, \
    is_success_role_admin_or_manager_for_group

IMAGEDIR = 'src/tasks/images/'

router = APIRouter(
    prefix="/tasks",
    tags=["tasks"]
)


def request_key_builder(
        func,
        namespace: str = "",
        request: Request = None,
        **kwargs,
):
    info = kwargs.get('kwargs')
    user = info.get('user')
    print(kwargs)
    print(user.id)
    return (f":{namespace} {request.method.lower()} {request.url.path} {repr(sorted(request.query_params.items()))}"
            f"[('user_id', '{user.id}')]")


@router.get("/tasks/get")
@cache(expire=60, key_builder=request_key_builder)
async def get_tasks(group_id: int, session: AsyncSession = Depends(get_async_session),
                    user=Depends(get_current_user)):
    query = (select(GroupTasks)
             .options(selectinload(GroupTasks.tasks))
             .options(selectinload(GroupTasks.access))
             .where(GroupTasks.id == group_id))
    response = await session.execute(query)
    result_models = response.unique().scalars().all()
    result = [GroupGetWithTask.model_validate(row, from_attributes=True) for row in result_models]
    if user.id in [user_access.user_id for user_access in result[0].access if user_access.access == True]:
        return result
    else:
        raise HTTPException(status_code=403, detail="You don't have permission")


@router.post("/task/add")
async def create_task(task: TaskCreate, session: AsyncSession = Depends(get_async_session),
                      user=Depends(get_current_user)):
    await is_success_role_admin(task.group_id, Role.admin, session, user)
    stmt = insert(Task).values(**task.dict())
    await session.execute(stmt)
    await session.commit()
    return {"status": "success"}


@router.post("/image")
async def set_image(task_id: int, file: UploadFile = File(None),
                    session: AsyncSession = Depends(get_async_session)):
    file_path = os.path.join(IMAGEDIR, file.filename)
    with open(file_path, "wb") as buffer:
        buffer.write(file.file.read())
    query = update(Task).where(Task.id == task_id).values(photo=file_path)
    await session.execute(query)
    await session.commit()
    return {"image": file.filename}


@router.delete("/task/delete/{task}")
async def delete_task(task_id: int, session: AsyncSession = Depends(get_async_session),
                      user=Depends(get_current_user)):
    stmt = select(Task).where(Task.id == task_id)
    response = await session.execute(stmt)
    obj = response.scalar_one()
    await is_success_role_admin(obj.group_id, Role.admin, session, user)
    await session.delete(obj)
    await session.commit()
    return {"status": "success"}


@router.patch("/task/update")
async def update_task(task_id: int, new_body: TaskUpdate,
                      session: AsyncSession = Depends(get_async_session),
                      user=Depends(get_current_user)):
    await is_success_role_admin_or_manager_for_task(task_id, Role.user, session, user)
    if isinstance(new_body, dict):
        update_data = new_body
    else:
        update_data = new_body.dict(
            exclude_unset=True
        )
    query = update(Task).where(Task.id == task_id).values(update_data)
    await session.execute(query)
    await session.commit()
    return {"status": "success"}


@router.get("/group/get")
@cache(expire=300, key_builder=request_key_builder)
async def get_group(session: AsyncSession = Depends(get_async_session),
                    user=Depends(get_current_user)):
    query = (select(GroupTasks.id,
                    GroupTasks.name,
                    GroupTasks.owner,
                    GroupAccess.role)
             .join(GroupAccess)
             .where(and_(GroupAccess.user_id == user.id,
                         GroupAccess.access == True)))
    result = await session.execute(query)
    result_models = result.unique().all()
    result = [GroupGet.model_validate(row, from_attributes=True) for row in result_models]
    return result


@router.post("/group/add")
async def create_group(group: GroupCreate, session: AsyncSession = Depends(get_async_session),
                       user=Depends(get_current_user)):
    group_create = GroupTasks(**group.dict(), owner=user.id)
    access = GroupAccess(user_id=user.id, role='admin')
    group_create.access.append(access)
    session.add(group_create)
    await session.commit()
    return {"status": "success"}


@router.delete("/group/delete/{group}")
async def delete_group(group_id: int, session: AsyncSession = Depends(get_async_session),
                       user=Depends(get_current_user)):
    await is_success_role_admin(group_id, Role.admin, session, user)
    response = await session.execute(
        select(GroupTasks).where(GroupTasks.id == group_id)
    )
    obj = response.scalar_one()
    await session.delete(obj)
    await session.commit()
    return {"status": "success"}


@router.patch("/group/update")
async def update_group(group_id: int, new_body: GroupUpdate,
                       session: AsyncSession = Depends(get_async_session),
                       user=Depends(get_current_user)):
    await is_success_role_admin_or_manager_for_group(group_id, Role.user, session, user)
    if isinstance(new_body, dict):
        update_data = new_body
    else:
        update_data = new_body.dict(
            exclude_unset=True
        )
    query = update(GroupTasks).where(GroupTasks.id == group_id).values(update_data)
    await session.execute(query)
    await session.commit()
    return {"status": "success"}


@router.get("/group/users")
async def get_user_access_for_group(group_id: int, session: AsyncSession = Depends(get_async_session),
                                    user=Depends(get_current_user)):
    query = (select(GroupAccess)
             .where(and_(GroupAccess.group_id == group_id,
                         GroupAccess.user_id == user.id,
                         GroupAccess.access == True)))
    response = await session.execute(query)
    result = response.unique().scalars().all()
    if not result:
        raise HTTPException(status_code=403, detail="You don't have permission")
    query = (select(GroupAccess)
             .where(and_(GroupAccess.group_id == group_id,
                         GroupAccess.access == True)))
    result = await session.execute(query)
    result_models = result.unique().scalars().all()
    return result_models


@router.post("/group/add/users")
async def add_user_group(group_id: int, data: AccessGroupPost,
                         session: AsyncSession = Depends(get_async_session),
                         user=Depends(get_current_user)):
    query = (select(GroupAccess)
             .where(and_(GroupAccess.group_id == group_id,
                         GroupAccess.user_id == user.id,
                         GroupAccess.access == True,
                         GroupAccess.role == Role.admin)))
    response = await session.execute(query)
    result = response.unique().scalars().all()
    if not result:
        raise HTTPException(status_code=403, detail="You don't have permission")
    stmt = insert(GroupAccess).values(**data.dict(), group_id=group_id)
    await session.execute(stmt)
    await session.commit()
    return {"status": "success"}


@router.delete("/group/delete/user/{user_id}")
async def delete_user_by_group(group_id: int, user_id: UUID,
                               session: AsyncSession = Depends(get_async_session),
                               user=Depends(get_current_user)):
    query = (select(GroupAccess)
             .where(and_(GroupAccess.group_id == group_id,
                         GroupAccess.user_id == user.id,
                         GroupAccess.access == True,
                         GroupAccess.role == Role.admin)))
    response = await session.execute(query)
    result = response.unique().scalars().all()
    if not result:
        raise HTTPException(status_code=403, detail="You don't have permission")
    response = await session.execute(
        select(GroupAccess).where(and_(GroupAccess.group_id == group_id,
                                       GroupAccess.user_id == user_id))
    )
    obj = response.unique().scalar_one()
    await session.delete(obj)
    await session.commit()
    return {"status": "success"}


@router.patch("/group/update/user")
async def update_user_group(group_id: int, user_id: UUID,
                            new_body: AccessGroupUpdate,
                            session: AsyncSession = Depends(get_async_session),
                            user=Depends(get_current_user)):
    query = (select(GroupAccess)
             .where(and_(GroupAccess.group_id == group_id,
                         GroupAccess.user_id == user.id,
                         GroupAccess.access == True,
                         GroupAccess.role == Role.admin)))
    response = await session.execute(query)
    result = response.unique().scalars().all()
    if not result:
        raise HTTPException(status_code=403, detail="You don't have permission")
    if isinstance(new_body, dict):
        update_data = new_body
    else:
        update_data = new_body.dict(
            exclude_unset=True
        )
    query = update(GroupAccess).where(and_(GroupAccess.group_id == group_id,
                                           GroupAccess.user_id == user_id)).values(update_data)
    await session.execute(query)
    await session.commit()
    return {"status": "success"}
