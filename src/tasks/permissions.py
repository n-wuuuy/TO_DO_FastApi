from fastapi import HTTPException
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.tasks.models import GroupTasks, GroupAccess, Task
from src.tasks.schemas import GroupGet


async def is_success_role_admin(group_id: int, role, session: AsyncSession,
                                user):
    query = (select(GroupTasks.id,
                    GroupTasks.name,
                    GroupTasks.owner,
                    GroupAccess.role,
                    GroupAccess.user_id)
             .join(GroupAccess)
             .where(and_(GroupTasks.id == group_id,
                         GroupAccess.user_id == user.id,
                         GroupAccess.access == True)))
    result = await session.execute(query)
    result_models = result.unique().all()
    result = [GroupGet.model_validate(row, from_attributes=True) for row in result_models]
    if not result:
        raise HTTPException(status_code=404, detail="Group not found")
    if result[0].role != role:
        raise HTTPException(status_code=403, detail="You don't have permission")
    return result


async def is_success_role_admin_or_manager_for_task(task_id: int, role,
                                                    session: AsyncSession,
                                                    user):
    query = (select(GroupTasks.id,
                    GroupTasks.name,
                    GroupTasks.owner,
                    GroupAccess.role,
                    GroupAccess.user_id)
             .join(GroupAccess)
             .join(Task)
             .where(and_(GroupAccess.user_id == user.id,
                         Task.id == task_id,
                         GroupAccess.access == True)))
    result = await session.execute(query)
    result_models = result.unique().all()
    result = [GroupGet.model_validate(row, from_attributes=True) for row in result_models]
    if not result:
        raise HTTPException(status_code=404, detail="Group not found")
    if result[0].role == role:
        raise HTTPException(status_code=403, detail="You don't have permission")
    return result


async def is_success_role_admin_or_manager_for_group(group_id: int, role,
                                                     session: AsyncSession,
                                                     user):
    query = (select(GroupTasks.id,
                    GroupTasks.name,
                    GroupTasks.owner,
                    GroupAccess.role,
                    GroupAccess.user_id)
             .join(GroupAccess)
             .where(and_(GroupTasks.id == group_id,
                         GroupAccess.user_id == user.id,
                         GroupAccess.access == True)))
    result = await session.execute(query)
    result_models = result.unique().all()
    result = [GroupGet.model_validate(row, from_attributes=True) for row in result_models]
    if not result:
        raise HTTPException(status_code=404, detail="Group not found")
    if result[0].role == role:
        raise HTTPException(status_code=403, detail="You don't have permission")
    return result
