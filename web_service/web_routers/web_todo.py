from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Request, Form
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from models import User, ToDo, task_status
from web_service.security import get_current_user
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import or_

router = APIRouter(prefix="/tasks", tags=["Web tasks"])
templates = Jinja2Templates(directory='web_service/static/html/')


@router.get('/', response_class=HTMLResponse)
async def get_tasks(request: Request, query: str | None = None, status: str | None = None, date_from: str | None = None,
                    date_to: str | None = None, db: AsyncSession = Depends(get_db),
                    current_user: User = Depends(get_current_user)):
    return await search_tasks(request, query, status, date_from, date_to, db, current_user)


@router.get('/search/', response_class=HTMLResponse)
async def search_tasks(request: Request, query: str | None = None, status: str | None = None,
                       date_from: str | None = None, date_to: str | None = None, db: AsyncSession = Depends(get_db),
                       current_user: User = Depends(get_current_user)):
    stmt = select(ToDo).filter(ToDo.user_id == current_user.id)
    if query:
        stmt = stmt.filter(
            or_(
                ToDo.title.ilike(f"%{query}%"),
                ToDo.description.ilike(f"%{query}%")
            )
        )

    if status:
        status_enum = task_status(status)
        stmt = stmt.filter(ToDo.status == status_enum)

    try:
        if date_from:
            date_from_obj = datetime.strptime(date_from, "%Y-%m-%d").date()
            stmt = stmt.filter(ToDo.plan_date >= date_from_obj)

        if date_to:
            date_to_obj = datetime.strptime(date_to, "%Y-%m-%d").date()
            stmt = stmt.filter(ToDo.plan_date <= date_to_obj)
    except ValueError:
        pass

    result = await db.execute(stmt)
    tasks = result.scalars().all()

    return templates.TemplateResponse("/task.html", {
        "request": request,
        "tasks": tasks,
        "user": current_user,
        "search_query": query or "",
        "selected_status": status or "",
        "date_from": date_from or "",
        "date_to": date_to or ""
    })


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
    new_task = ToDo(title=title, status=task_status(status), description=description,
                    plan_date=datetime.strptime(plan_date, "%Y-%m-%d").date(), user_id=current_user.id)
    try:
        db.add(new_task)
        await db.commit()
    except Exception as e:
        print(new_task)
        print(e)
        await db.rollback()

    return RedirectResponse(url="/tasks/", status_code=303)


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
        "task": task,
        "task_id": task_id
    })


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
    task.status = task_status(status)
    task.description = description
    task.plan_date = datetime.strptime(plan_date, "%Y-%m-%d").date()
    try:
        await db.commit()
    except Exception as e:
        print(e)
        await db.rollback()
        raise HTTPException(status_code=500)
    return RedirectResponse(url='/tasks/', status_code=303)


@router.get('/delete/{task_id}/', response_class=HTMLResponse)
async def update_task_form(request: Request, task_id: int, db: AsyncSession = Depends(get_db),
                           current_user: User = Depends(get_current_user)):
    result = await db.execute(select(ToDo).filter(ToDo.id == task_id, ToDo.user_id == current_user.id))
    task = result.scalars().first()

    if not task:
        return RedirectResponse("/tasks/delete/?error=Не существует такой записи",
                                status_code=404)

    return templates.TemplateResponse("delete_task.html", {
        "request": request,
        "task": task,
        "task_id": task_id
    })


@router.post('/delete/{task_id}/', response_class=RedirectResponse)
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
    return RedirectResponse(url='/tasks/', status_code=303)
