from fastapi import FastAPI, Request, Form, HTTPException, Depends
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from db.init_db import init_db
from services.authentication import AuthService
from utils.security import verify_token
from pydantic import BaseModel
from typing import Optional
from services.task_service import TaskService
from services.task_analytics_server import AnalyticsService

app = FastAPI()
templates = Jinja2Templates(directory="templates")
init_db()
app.mount("/static", StaticFiles(directory="static"), name="static")

auth_service = AuthService()
task_service = TaskService()
analytics_service = AnalyticsService()

class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    plan_start_time: str
    plan_end_time: str
    priority: int = 3
    difficulty: int = 3

class TaskUpdate(BaseModel):
    title: str
    description: Optional[str] = None
    plan_start_time: str
    plan_end_time: str
    priority: int = 3
    difficulty: int = 3

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str

class TaskCompleteRequest(BaseModel):
    pleasure: int = 3
    productivity_score: int = 70

@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    public_paths = ["/", "/login", "/register", "/api/refresh"]

    if request.url.path in public_paths:
        return await call_next(request)
    access_token = request.cookies.get("access_token")
    if access_token:
        payload = verify_token(access_token)
        if payload and payload.get("type") == "access":
            request.state.user = payload
            return await call_next(request)

    refresh_token = request.cookies.get("refresh_token")
    if refresh_token:
        new_tokens = auth_service.refresh(refresh_token)
        if new_tokens:
            payload = verify_token(new_tokens["access_token"])
            request.state.user = payload
            response = await call_next(request)
            response.set_cookie(
                key="access_token",
                value=new_tokens["access_token"],
                httponly=True,
                samesite="lax"
            )
            return response
    if request.url.path.startswith("/api"):
        return JSONResponse(status_code=401, content={"detail": "Не авторизовано"})
    return RedirectResponse(url="/login", status_code=302)

def get_current_user(request: Request):
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(status_code=401, detail="Не авторизовано")
    return user

@app.get("/")
def root():
    return RedirectResponse(url="/login")

@app.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.post("/register")
def register(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...)
):
    if password != confirm_password:
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "Паролі не співпадають"}
        )
    success = auth_service.register(username, email, password)
    if not success:
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "Користувач вже існує"}
        )
    return RedirectResponse("/login", status_code=303)

@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
def login(request: Request, email: str = Form(...), password: str = Form(...)):
    result = auth_service.login(email, password)
    if result:
        response = RedirectResponse("/calendar", status_code=303)
        response.set_cookie(
            key="access_token",
            value=result["access_token"],
            httponly=True,
            samesite="lax"
        )
        response.set_cookie(
            key="refresh_token",
            value=result["refresh_token"],
            httponly=True,
            samesite="lax"
        )
        return response
    return templates.TemplateResponse(
        "login.html",
        {"request": request, "error": "Невірний логін або пароль"}
    )

@app.post("/api/refresh")
async def refresh_token(request: Request):
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=401, detail="No refresh token")
    result = auth_service.refresh(refresh_token)
    if not result:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    response = JSONResponse(content=result)
    response.set_cookie(
        key="access_token",
        value=result["access_token"],
        httponly=True,
        samesite="lax"
    )
    return response

@app.post("/api/logout")
async def logout(request: Request):
    refresh_token = request.cookies.get("refresh_token")
    if refresh_token:
        auth_service.logout(refresh_token)

    response = JSONResponse(content={"message": "Logged out"})
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return response

@app.get("/calendar", response_class=HTMLResponse)
def calendar(request: Request):
    user = getattr(request.state, "user", None)
    if not user:
        return RedirectResponse("/login")

    task_service.update_missed_and_late_tasks(user["user_id"])
    return templates.TemplateResponse(
        "calendar.html", {"request": request, "username": user["username"]})

@app.post("/api/tasks")
def create_task_endpoint(task: TaskCreate, user=Depends(get_current_user)):
    try:
        result = task_service.create(
            user_id=user["user_id"],
            title=task.title,
            description=task.description,
            plan_start=task.plan_start_time,
            plan_end=task.plan_end_time,
            priority=task.priority,
            difficulty=task.difficulty
        )
        return {"success": True, "task_id": result}
    except ValueError as e:
        if "Конфлікт" in str(e):
            raise HTTPException(status_code=409, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/tasks")
def get_tasks_endpoint(user=Depends(get_current_user)):
    tasks = task_service.get_all_user_tasks(user["user_id"])
    return [dict(task) for task in tasks]

@app.get("/api/tasks/day/{date}")
def get_tasks_by_day_endpoint(date: str, user = Depends(get_current_user)):
    try:
        tasks = task_service.get_by_day(user["user_id"], date)
        return tasks
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/day_page/{date}")
def day_page(request: Request, date: str):
    user = getattr(request.state, "user", None)
    if not user:
        return RedirectResponse("/login")
    task_service.update_missed_and_late_tasks(user["user_id"])
    return templates.TemplateResponse("day_page.html", {"request": request, "date": date, "username": user["username"]})

@app.delete("/api/tasks/{task_id}")
def delete_task(task_id: int, user=Depends(get_current_user)):
    success = task_service.delete(user["user_id"], task_id)
    if not success:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"success": True}

@app.post("/api/change-password")
def change_password_endpoint(request: ChangePasswordRequest, user=Depends(get_current_user)):
    try:
        auth_service.change_password(
            user_id=user["user_id"],
            old_password=request.old_password,
            new_password=request.new_password
        )
        return {"success": True, "message": "Пароль успішно змінено"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.put("/api/tasks/{task_id}")
def update_task(task_id: int, task: TaskUpdate, user=Depends(get_current_user)):
    try:
        success = task_service.update(
            task_id=task_id,
            user_id=user["user_id"],
            title=task.title,
            description=task.description,
            plan_start=task.plan_start_time,
            plan_end=task.plan_end_time,
            priority=task.priority,
            difficulty=task.difficulty
        )

        if not success:
            raise HTTPException(status_code=404, detail="Task not found")
        return {"success": True}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/tasks/{task_id}/start")
def start_task(task_id: int, user=Depends(get_current_user)):
    try:
        success = task_service.start_task(user["user_id"], task_id)
        if not success:
            raise HTTPException(status_code=404, detail="Task not found")
        return {"success": True, "message": "Задача розпочалася"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/tasks/{task_id}/complete")
def complete_task(task_id: int, request: TaskCompleteRequest, user=Depends(get_current_user)):
    try:
        success = task_service.complete_task(
            user_id=user["user_id"],
            task_id=task_id,
            pleasure=request.pleasure,
            productivity_score=request.productivity_score
        )
        if not success:
            raise HTTPException(status_code=404, detail="Task not found")
        return {"success": True, "message": "Задача виконана"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/analytics")
def get_analytics(user=Depends(get_current_user)):
    try:
        analytics = analytics_service.get_analytics(user["user_id"])
        return analytics
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/analytics", response_class=HTMLResponse)
def analytics_page(request: Request, user=Depends(get_current_user)):
    return templates.TemplateResponse(
        "analytics.html", {"request": request, "username": user["username"]})