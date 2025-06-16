from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from api_service.api_routers.todo import router as router_todo
from api_service.api_routers.auth import router as auth_api
from web_service.web_routers.auth import web_router as auth_web
from web_service.web_routers.web_todo import router as router_web

app = FastAPI()
templates = Jinja2Templates(directory='html')
app.include_router(router_todo)
app.include_router(auth_api)
app.include_router(router_web)
app.include_router(auth_web)


@app.get('/')
async def root(request: Request):
    return templates.TemplateResponse("/index.html", {"request": request})


@app.exception_handler(401)
async def not_found_exception_handler(request: Request, exc):
    return templates.TemplateResponse(
        "/401.html",
        {"request": request},
        status_code=401
    )


@app.exception_handler(404)
async def not_found_exception_handler(request: Request, exc):
    return templates.TemplateResponse(
        "/404.html",
        {"request": request},
        status_code=404
    )