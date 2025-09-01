from fastapi import FastAPI, UploadFile, Form, Cookie, HTTPException
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
import os, json

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

VIDEOS_DIR = "/data/videos"
DATA_FILE = "/data/data.json"
USERS_FILE = "/data/users.json"

# Dosyalar
if not os.path.exists(VIDEOS_DIR):
    os.makedirs(VIDEOS_DIR)

if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        video_data = json.load(f)
else:
    video_data = {}

if os.path.exists(USERS_FILE):
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        users = json.load(f)
else:
    users = {}

def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(video_data, f, ensure_ascii=False, indent=2)

def save_users():
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

# Login sayfası
@app.get("/login")
def login_page():
    return FileResponse("login.html")

# Login / kayıt endpoint
@app.post("/login")
async def login(username: str = Form(...), password: str = Form(...)):
    if username in users:
        if users[username]["password"] != password:
            return {"status":"error","msg":"Şifre yanlış"}
    else:
        # otomatik kayıt
        users[username] = {"password": password, "nickname": username}
        save_users()
    response = RedirectResponse(url="/", status_code=302)
    response.set_cookie(key="user", value=username)
    return response

@app.get("/logout")
def logout():
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie("user")
    return response

# Ana sayfa
@app.get("/")
def read_index(user: str = Cookie(None)):
    if not user or user not in users:
        return RedirectResponse(url="/login")
    return FileResponse("index.html")

# Video upload
@app.post("/upload")
async def upload_video(file: UploadFile, user: str = Cookie(None)):
    if not user or user not in users:
        raise HTTPException(status_code=401, detail="Login gerekli")
    file_path = os.path.join(VIDEOS_DIR, file.filename)
    with open(file_path, "wb") as f:
        f.write(await file.read())
    if file.filename not in video_data:
        video_data[file.filename] = {"likes":0, "dislikes":0, "comments":[]}
        save_data()
    return {"status":"ok","filename":file.filename}

@app.get("/videos")
def list_videos(user: str = Cookie(None)):
    if not user or user not in users:
        raise HTTPException(status_code=401, detail="Login gerekli")
    return video_data

@app.post("/like")
def like_video(filename: str = Form(...), user: str = Cookie(None)):
    if not user or user not in users:
        raise HTTPException(status_code=401, detail="Login gerekli")
    if filename in video_data:
        video_data[filename]["likes"] += 1
        save_data()
        return {"status":"ok"}
    return {"status":"error","msg":"Video bulunamadı"}

@app.post("/dislike")
def dislike_video(filename: str = Form(...), user: str = Cookie(None)):
    if not user or user not in users:
        raise HTTPException(status_code=401, detail="Login gerekli")
    if filename in video_data:
        video_data[filename]["dislikes"] += 1
        save_data()
        return {"status":"ok"}
    return {"status":"error","msg":"Video bulunamadı"}

@app.post("/comment")
def comment_video(filename: str = Form(...), text: str = Form(...), user: str = Cookie(None)):
    if not user or user not in users:
        raise HTTPException(status_code=401, detail="Login gerekli")
    if filename in video_data:
        video_data[filename]["comments"].append(text)
        save_data()
        return {"status":"ok"}
    return {"status":"error","msg":"Video bulunamadı"}