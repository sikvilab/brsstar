from fastapi import FastAPI, HTTPException
import requests
import os

app = FastAPI()

# Твой API ключ (закинь его в Environment Variables на Vercel/Railway)
BRAWL_API_KEY = os.getenv("BRAWL_API_KEY")
BASE_URL = "https://api.brawlstars.com/v1"

# Временное хранилище статусов (в памяти сервера)
# Для 9 человек этого хватит. Если сервер перезагрузится, статусы сбросятся.
online_players = {}

@app.get("/player/{tag}")
async def get_full_stats(tag: str):
    """Скачивает характеристики: кубки, бойцы и текущий статус в мессенджере"""
    clean_tag = tag.replace("#", "").upper()
    headers = {
        "Authorization": f"Bearer {BRAWL_API_KEY}",
        "Accept": "application/json"
    }
    
    # Запрос к официальному API
    response = requests.get(f"{BASE_URL}/players/%23{clean_tag}", headers=headers)
    
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="Brawl Stars API Error")
    
    data = response.json()
    
    # Формируем компактный ответ для твоего Kotlin/C++ клиента
    stats = {
        "name": data.get("name"),
        "trophies": data.get("trophies"),
        "highestTrophies": data.get("highestTrophies"),
        "expLevel": data.get("expLevel"),
        "brawlersCount": len(data.get("brawlers", [])),
        # Вытаскиваем список бойцов (имя и их кубки)
        "brawlers": [{"name": b["name"], "power": b["power"], "trophies": b["trophies"]} for b in data.get("brawlers", [])],
        # Добавляем наш внутренний статус "онлайн в мессенджере"
        "isOnline": online_players.get(clean_tag, False)
    }
    return stats

@app.post("/status/{tag}/{state}")
async def set_status(tag: str, state: str):
    """Kotlin шлет сюда: /status/TAG/online или /status/TAG/offline"""
    clean_tag = tag.replace("#", "").upper()
    
    if state.lower() == "online":
        online_players[clean_tag] = True
    elif state.lower() == "offline":
        online_players[clean_tag] = False
    else:
        raise HTTPException(status_code=400, detail="Invalid state. Use 'online' or 'offline'")
        
    return {"tag": clean_tag, "status": online_players[clean_tag]}

@app.get("/team-status")
async def get_team_status():
    """Показать список всех, кто сейчас онлайн в мессенджере"""
    return {"online_now": [tag for tag, status in online_players.items() if status]}
