from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from shemas import ToDoCreate, ToDoResponse, ToDoUpdate
from models import User, ToDo
from api_service.security import get_current_user

router = APIRouter(prefix="/api/tasks", tags=["api tasks"])


@router.post('/create/', status_code=201)
async def create_task(task: ToDoCreate, db: AsyncSession = Depends(get_db),
                      current_user: User = Depends(get_current_user)):
    if not task.title:
        HTTPException(status_code=400, detail='Нет названия задачи')
    new_task = ToDo(**task.model_dump(), user_id=current_user.id)
    try:
        db.add(new_task)
        await db.commit()
        await db.refresh(new_task)
    except Exception as e:
        print(new_task)
        print(e)
        await db.rollback()
        raise HTTPException(status_code=500, detail='Проблемы у сервера')
    return new_task


@router.get('/mytasks/', response_model=list[ToDoResponse])
async def get_tasks(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    my_tasks = await db.execute(select(ToDo).filter(ToDo.user_id == current_user.id))
    tasks = my_tasks.scalars().all()
    return tasks


@router.patch('/update/{task_id}/', response_model=ToDoResponse)
async def update_task(task_id: int, tododata: ToDoUpdate, db: AsyncSession = Depends(get_db),
                      current_user: User = Depends(get_current_user)):
    result = await db.execute(select(ToDo).filter(ToDo.id == task_id, ToDo.user_id == current_user.id))
    task = result.scalars().first()
    if not task:
        raise HTTPException(status_code=404)
    try:
        await db.execute(update(ToDo).where(ToDo.id == task_id).values(**tododata.model_dump(exclude_unset=True)))
        await db.commit()
    except Exception as e:
        print(e)
        await db.rollback()
        raise HTTPException(status_code=500)
    await db.refresh(task)
    return task


@router.delete('/delete/{task_id}/', status_code=204)
async def delete_task(task_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(ToDo).filter(ToDo.id == task_id, ToDo.user_id == current_user.id))
    task = result.scalars().first()

    if not task:
        raise HTTPException(status_code=404)
    try:
        await db.execute(delete(ToDo).where(ToDo.id == task_id))
        await db.commit()
    except Exception as e:
        print(e)
        await db.rollback()
        raise HTTPException(status_code=500)

