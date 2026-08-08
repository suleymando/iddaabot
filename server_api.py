import datetime
from fastapi import FastAPI, Query, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from bulletin_scanner import BulletinScanner
from telegram_notifier import send_telegram_message, format_telegram_bulletin

app = FastAPI(
    title="Suleymando İddaa Bülten API & Telegram Otomasyonu",
    description="Mackolik bültenini tarar, Suleymando İY 1.5 ÜST formülünü uygular ve n8n / Telegram bot entegrasyonu sağlar.",
    version="2.0.0"
)

scanner = BulletinScanner()

def parse_time_minutes(time_str: str) -> int:
    try:
        parts = time_str.split(':')
        if len(parts) == 2:
            h, m = int(parts[0]), int(parts[1])
            if 0 <= h < 6:
                return (h + 24) * 60 + m
            return h * 60 + m
    except Exception:
        pass
    return 9999

class TelegramTriggerRequest(BaseModel):
    bot_token: str
    chat_id: str
    mode: str = "every_4h" # "night_2345" veya "every_4h"
    min_odds: float = 1.00
    max_odds: float = 1.23

@app.get("/")
def home():
    return {
        "status": "online",
        "service": "Suleymando İddaa Automation API",
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

@app.get("/api/scan")
def scan_bulletin(
    min_odds: float = Query(1.00, ge=1.00, le=2.00),
    max_odds: float = Query(1.23, ge=1.00, le=3.00),
    hours: Optional[int] = Query(None, description="Yaklaşan X saatlik maçları filtreler (örn: 4)")
):
    all_m, filt_m = scanner.scan_bulletin(min_odds, max_odds, fetch_details=True)
    filt_m.sort(key=lambda m: parse_time_minutes(m['time']))
    
    if hours and hours > 0:
        now_minutes = datetime.datetime.now().hour * 60 + datetime.datetime.now().minute
        max_target_minutes = now_minutes + (hours * 60)
        
        window_filtered = []
        for m in filt_m:
            tm = parse_time_minutes(m['time'])
            if now_minutes <= tm <= max_target_minutes:
                window_filtered.append(m)
        filt_m = window_filtered

    return {
        "total_scanned": len(all_m),
        "total_matched": len(filt_m),
        "min_odds": min_odds,
        "max_odds": max_odds,
        "filter_hours": hours,
        "matches": filt_m
    }

@app.post("/api/telegram_trigger")
def trigger_telegram(payload: TelegramTriggerRequest):
    """
    n8n veya cron job tarafından tetiklenen Telegram bildirim servis ucu.
    mode: 'night_2345' (Tüm Gece/Yarın bülteni) veya 'every_4h' (Önümüzdeki 4 saat)
    """
    bot_token = payload.bot_token
    chat_id = payload.chat_id
    mode = payload.mode
    
    if not bot_token or not chat_id:
        raise HTTPException(status_code=400, detail="bot_token ve chat_id zorunludur.")
        
    all_m, filt_m = scanner.scan_bulletin(payload.min_odds, payload.max_odds, fetch_details=True)
    filt_m.sort(key=lambda m: parse_time_minutes(m['time']))
    
    if mode == "night_2345":
        title = "🌙 GECE 23:45 TÜM BÜLTEN TARAMASI (YARINKİ MAÇLAR)"
        target_matches = filt_m
    else:
        title = "⏳ YAKLAŞAN 4 SAATLİK PERİYODİK BÜLTEN TARAMASI"
        now_minutes = datetime.datetime.now().hour * 60 + datetime.datetime.now().minute
        max_target_minutes = now_minutes + (4 * 60)
        
        window_matches = [m for m in filt_m if now_minutes <= parse_time_minutes(m['time']) <= max_target_minutes]
        target_matches = window_matches if window_matches else filt_m[:5]

    msg_chunks = format_telegram_bulletin(target_matches, title)
    
    success_count = 0
    for chunk in msg_chunks:
        ok = send_telegram_message(bot_token, chat_id, chunk)
        if ok:
            success_count += 1

    return {
        "status": "success",
        "mode": mode,
        "total_matched": len(target_matches),
        "telegram_messages_sent": success_count
    }

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
