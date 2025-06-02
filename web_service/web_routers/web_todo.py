from fastapi import APIRouter, Depends, HTTPException, Request, Form
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from models import User, ToDo, task_status
from api_service.security import get_current_user
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(prefix="/tasks", tags=["Web tasks"])
templates = Jinja2Templates(directory='web_service/static/html')


@router.get('/', response_class=HTMLResponse)
async def get_tasks(request: Request, db: AsyncSession = Depends(get_db),
                    current_user: User = Depends(get_current_user)):
    my_tasks = await db.execute(select(ToDo).filter(ToDo.user_id == current_user.id))
    tasks = my_tasks.scalars().all()
    return templates.TemplateResponse("task.html", context={'request': request, 'tasks': tasks, 'user': current_user})


@router.get('/create/', response_class=HTMLResponse)
async def create_task_form(request: Request):
    return templates.TemplateResponse('create_task.html', context={'request': request})


@router.post('/create/', response_class=RedirectResponse)
async def create_task(request: Request,
                      title: str = Form(), status: str = Form(default=task_status.PLANNED),
                      description: str = Form(None),
                      plan_date: str = Form(),
                      db: AsyncSession = Depends(get_db),
                      current_user: User = Depends(get_current_user)):
    new_task = ToDo(title=title, status=status, description=description, plan_date=plan_date, user_id=current_user.id)
    try:
        db.add(new_task)
        await db.commit()
    except Exception as e:
        print(new_task)
        print(e)
        await db.rollback()

    return RedirectResponse(url="/tasks/")


@router.get('/edit/{task_id}/', response_class=HTMLResponse)
async def update_task_form(request: Request, task_id: int, db: AsyncSession = Depends(get_db),
                      current_user: User = Depends(get_current_user)):
    result = await db.execute(select(ToDo).filter(ToDo.id == task_id, ToDo.user_id == current_user.id))
    task = result.scalars().first()

    if not task:
        return RedirectResponse("/tasks/edit/?error=Не существует такой записи",
                                status_code=404)

    return templates.TemplateResponse("edit_task.html", {
        "request": request,
        "task": task})


@router.post('/update/{task_id}/', response_class=RedirectResponse)
async def update_task(request: Request, task_id: int, title: str = Form(),
                      status: str = Form(default=task_status.PLANNED),
                      description: str = Form(None), plan_date: str = Form(), db: AsyncSession = Depends(get_db),
                      current_user: User = Depends(get_current_user)):
    result = await db.execute(select(ToDo).filter(ToDo.id == task_id, ToDo.user_id == current_user.id))
    task = result.scalars().first()
    if not task:
        raise HTTPException(status_code=404)
    task.title = title
    task.status = status
    task.description = description
    task.plan_date = plan_date
    try:
        await db.commit()
    except Exception as e:
        print(e)
        await db.rollback()
        raise HTTPException(status_code=500)
    return RedirectResponse(url='/tasks/')


@router.delete('/delete/{task_id}/', response_class=RedirectResponse)
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
    return RedirectResponse(url='/tasks/')
