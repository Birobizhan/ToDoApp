from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from api_service.api_routers.todo import router as router_todo
from api_service.api_routers.auth import router as auth_api
from web_service.web_routers.auth import web_router as auth_web
from web_service.web_routers.web_todo import router as router_web

app = FastAPI()
templates = Jinja2Templates(directory='static/html')
app.include_router(router_todo)
app.include_router(auth_api)
app.include_router(router_web)
app.include_router(auth_web)


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
