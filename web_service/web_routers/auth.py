from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.templating import Jinja2Templates
from database import get_db
from models import User
from passlib.context import CryptContext
from web_service.security import create_access_token


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
web_router = APIRouter(prefix="/web", tags=["auth-web"])
templates = Jinja2Templates(directory='web_service/static/html')


@web_router.get('/register/', response_class=HTMLResponse)
def register_form(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


@web_router.post('/register/', response_class=RedirectResponse)
async def register(request: Request, username: str = Form(), email: str = Form(),
                   password: str = Form(), db: AsyncSession = Depends(get_db)):
    existing_user = await db.execute(select(User).filter((User.username == username) | (User.email == email)))
    if existing_user.scalars().first():
        return RedirectResponse("/auth/register/?error=Пользователь с таким именем или почтой уже существует",
                                status_code=303)
    hashed_password = pwd_context.hash(password)

    new_user = User(username=username,
                    email=email,
                    hash_password=hashed_password)
    db.add(new_user)
    await db.commit()
    response = RedirectResponse(url="/tasks/login", status_code=303)
    return response


@web_router.get('/login/', response_class=HTMLResponse)
def register_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@web_router.post("/login/", response_class=RedirectResponse)
async def login(request: Request, username: str = Form(), password: str = Form(),
                db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).filter(User.username == username))
    user = result.scalars().first()
    if not user:
        return RedirectResponse(
            "/web/login/?error=Неверное имя пользователя или пароль",
            status_code=303
        )
    if not pwd_context.verify(password, user.hash_password):
        return RedirectResponse(
            "/tasks/login/?error=Неверное имя пользователя или пароль",
            status_code=303
        )
    access_token = create_access_token(data={"sub": username})
    response = RedirectResponse(url="/tasks/", status_code=303)
    response.set_cookie(key="access_token", value=f"Bearer {access_token}", httponly=True)
    return response


@web_router.get('/logout/', response_class=RedirectResponse)
async def logout():
    response = RedirectResponse(url="/web/login/", status_code=303)
    response.delete_cookie("access_token")
    return response
