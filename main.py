from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import UploadFile, File
from fastapi import UploadFile, File
from fastapi.responses import FileResponse
import time
import shutil
import json
import os

app = FastAPI()

# Подключаем папку static
app.mount("/static", StaticFiles(directory="static"), name="static")

# Подключаем папку templates
templates = Jinja2Templates(directory="templates")

# -----------------------------
#    ФУНКЦИИ ДЛЯ РАБОТЫ С JSON
# -----------------------------
def load_users():
    if os.path.exists("users.json"):
        return json.load(open("users.json", "r", encoding="utf-8"))
    return {}

def save_users(data):
    with open("users.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def load_chats():
    if os.path.exists("chats.json"):
        return json.load(open("chats.json", "r", encoding="utf-8"))
    return {}

def save_chats(data):
    with open("chats.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


# -----------------------------
#            ГЛАВНАЯ
# -----------------------------
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    username = request.cookies.get("username")
    return templates.TemplateResponse("home.html", {
        "request": request,
        "username": username
    })


# -----------------------------
#         РЕГИСТРАЦИЯ
# -----------------------------
@app.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.post("/register")
def register_user(username: str = Form(...), password: str = Form(...)):
    users = load_users()
    if username in users:
        return JSONResponse({"error": "Пользователь уже существует"})
    users[username] = {"password": password}
    save_users(users)
    response = RedirectResponse("/chat_placeholder", status_code=302)  # Сразу на чат
    response.set_cookie(key="username", value=username)
    return response


# -----------------------------
#            ВХОД
# -----------------------------
@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
def login_user(username: str = Form(...), password: str = Form(...)):
    users = load_users()
    if username not in users or users[username]["password"] != password:
        return JSONResponse({"error": "Неверный логин или пароль"})
    response = RedirectResponse("/chat_placeholder", status_code=302)  # Сразу на чат
    response.set_cookie(key="username", value=username)
    return response


# -----------------------------
#             ВЫХОД
# -----------------------------
@app.get("/logout")
def logout():
    response = RedirectResponse("/", status_code=302)
    response.delete_cookie("username")
    return response


# -----------------------------
#       ЧАТ-ЗАГЛУШКА
# -----------------------------
@app.get("/chat_placeholder", response_class=HTMLResponse)
def chat_placeholder(request: Request):
    username = request.cookies.get("username")
    if not username:
        return RedirectResponse("/login")
    users = load_users()
    chats = load_chats()
    return templates.TemplateResponse("chat.html", {
        "request": request,
        "username": username,
        "other_user": None,  # пока пользователь не выбран
        "messages": [],
        "users": users
    })


# -----------------------------
#           ОТКРЫТЬ ЧАТ
# -----------------------------
@app.get("/chat/{other_user}", response_class=HTMLResponse)
def open_chat(request: Request, other_user: str):
    username = request.cookies.get("username")
    if not username:
        return RedirectResponse("/login")
    chats = load_chats()
    pair = tuple(sorted([username, other_user]))
    if str(pair) not in chats:
        chats[str(pair)] = []
    return templates.TemplateResponse("chat.html", {
        "request": request,
        "username": username,
        "other_user": other_user,
        "messages": chats[str(pair)],
        "users": load_users()
    })


# -----------------------------
#        ОТПРАВКА СООБЩЕНИЙ
# -----------------------------
@app.post("/send_msg/{other_user}")
async def send_msg(other_user: str, request: Request):
    username = request.cookies.get("username")
    if not username:
        return {"error": "not logged"}
    form = await request.form()
    text = form.get("text")
    chats = load_chats()
    pair = tuple(sorted([username, other_user]))
    if str(pair) not in chats:
        chats[str(pair)] = []
    chats[str(pair)].append({
        "sender": username,
        "text": text
    })
    save_chats(chats)
    return RedirectResponse(f"/chat/{other_user}", status_code=302)


@app.get("/profile", response_class=HTMLResponse)
def profile(request: Request):
    username = request.cookies.get("username")
    if not username:
        return RedirectResponse("/login")

    users = load_users()
    avatar = users.get(username, {}).get("avatar", "/static/avatars/default.png")

    return templates.TemplateResponse(
        "profile.html",
        {
            "request": request,
            "username": username,
            "avatar": avatar
        }
    )


@app.post("/profile/update")
async def update_profile(
    request: Request,
    nickname: str = Form(...),
    avatar: UploadFile = File(None)
):
    username = request.cookies.get("username")
    if not username:
        return RedirectResponse("/login")

    users = load_users()
    if username in users:
        users[username]["nickname"] = nickname

        # Сохраняем аватарку, если выбрали
        if avatar is not None and avatar.filename != "":
            avatar_folder = "static/avatars"
            os.makedirs(avatar_folder, exist_ok=True)  # создаём папку, если нет
            avatar_path = os.path.join(avatar_folder, f"{username}.png")
            with open(avatar_path, "wb") as f:
                f.write(await avatar.read())
            users[username]["avatar"] = avatar_path

        save_users(users)

    return RedirectResponse("/profile", status_code=303)


@app.post("/send_voice/{other_user}")
async def send_voice(other_user: str, request: Request, voice: UploadFile = File(...)):
    username = request.cookies.get("username")
    if not username:
        return RedirectResponse("/login", status_code=302)

    # имя файла
    filename = f"{int(time.time())}_{username}.webm"
    filepath = f"voice/{filename}"

    # сохраняем файл
    with open(filepath, "wb") as f:
        f.write(await voice.read())

    chats = load_chats()
    pair = tuple(sorted([username, other_user]))

    if str(pair) not in chats:
        chats[str(pair)] = []

    chats[str(pair)].append({
        "sender": username,
        "type": "voice",
        "file": filename
    })

    save_chats(chats)

    return RedirectResponse(f"/chat/{other_user}", status_code=302)


@app.get("/voice/{filename}")
def get_voice(filename: str):
    return FileResponse(f"voice/{filename}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000)