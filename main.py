from fastapi import APIRouter, Depends, FastAPI, Body, Request, Form
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from routers.todo import router as router_todo
from routers.auth import router as router_auth

app = FastAPI()
templates = Jinja2Templates(directory='static/html')
app.include_router(router_todo)
app.include_router(router_auth)


@app.get('/')
async def root(request: Request):
    person = Person(languages=[], name="Undefined")
    return templates.TemplateResponse('index.html', context={'request': request, 'person': person})


class Person:
    def __init__(self, languages, name):
        self.languages = languages
        self.name = name

@app.post('/postdata')
def postdata(request: Request, username: str = Form(default="Undefined", min_length=2, max_length=20),
             languages: list = Form()):
    person = Person(languages, username)
    return templates.TemplateResponse(name='index.html', context={'request': request, 'person': person})
