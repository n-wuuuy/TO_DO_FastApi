from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.celery_task.tasks import send_email_report_dashboard
from src.database import get_async_session
from src.user.deps import get_current_user
from src.tasks.models import GroupTasks, GroupAccess
from src.tasks.schemas import GroupGetWithTask

router = APIRouter(prefix="/email")


@router.get("/dashboard")
async def get_dashboard_report(session: AsyncSession = Depends(get_async_session),
                               user=Depends(get_current_user)):
    query = (select(GroupTasks)
             .options(selectinload(GroupTasks.tasks))
             .options(selectinload(GroupTasks.access))
             .join(GroupAccess)
             .where(and_(GroupAccess.user_id == user.id,
                         GroupAccess.access == True)))
    response = await session.execute(query)
    result_models = response.unique().scalars().all()
    result = [GroupGetWithTask.model_validate(row, from_attributes=True).json() for row in result_models]
    send_email_report_dashboard.delay(user.email, result)
    return {
        "status": 200,
        "data": "Письмо отправлено",
        "details": None
    }
