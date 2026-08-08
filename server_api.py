import datetime
from fastapi import FastAPI, Query, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from bulletin_scanner import BulletinScanner
from telegram_notifier import (
    send_telegram_message, 
    send_matches_individually,
    check_and_update_won_matches,
    format_telegram_winrate_report,
    generate_csv_bulletin,
    send_telegram_document,
    send_daily_parlay_coupon,
    send_short_term_coupon,
    filter_upcoming_not_started_matches,
    turkey_now
)

app = FastAPI(
    title="Suleymando İddaa Bülten API & Telegram Otomasyonu",
    description="Mackolik bültenini tarar, Suleymando İY 1.5 ÜST formülünü uygular ve n8n / Telegram bot entegrasyonu sağlar.",
    version="2.1.0"
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
    mode: str = "every_4h" # "night_2345", "every_4h", "update_scores"
    min_odds: float = 1.00
    max_odds: float = 1.23

@app.get("/")
def home():
    return {
        "status": "online",
        "service": "Suleymando İddaa Automation API",
        "timestamp": turkey_now().strftime("%Y-%m-%d %H:%M:%S")
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
        filt_m = filter_upcoming_not_started_matches(filt_m, window_hours=hours)

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
    bot_token = payload.bot_token
    chat_id = payload.chat_id
    mode = payload.mode
    
    if not bot_token or not chat_id:
        raise HTTPException(status_code=400, detail="bot_token ve chat_id zorunludur.")
        
    all_m, filt_m = scanner.scan_bulletin(payload.min_odds, payload.max_odds, fetch_details=True)
    filt_m.sort(key=lambda m: parse_time_minutes(m['time']))
    
    if mode == "parlay_coupon":
        ok = send_daily_parlay_coupon(bot_token, chat_id, filt_m)
        return {
            "status": "success",
            "mode": mode,
            "parlay_sent": ok
        }
    elif mode == "short_term_coupon":
        ok = send_short_term_coupon(bot_token, chat_id, filt_m, window_hours=3)
        return {
            "status": "success",
            "mode": mode,
            "short_term_coupon_sent": ok
        }
    elif mode == "update_scores":
        up_res = check_and_update_won_matches(bot_token, chat_id, filt_m)
        return {
            "status": "success",
            "mode": mode,
            "updated_won_matches": up_res['updated'],
            "goal_alerts_sent": up_res.get('goal_alerts', 0),
            "total_tracked": up_res['total']
        }
    elif mode == "night_2345":
        today_date_str = turkey_now().strftime("%d.%m.%Y")
        report_text = format_telegram_winrate_report(filt_m, today_date_str)
        send_telegram_message(bot_token, chat_id, report_text)
        
        csv_bytes = generate_csv_bulletin(filt_m, f"Suleymando_GunSonu_{today_date_str}")
        filename = f"suleymando_bulten_{turkey_now().strftime('%Y%m%d_%H%M')}.csv"
        caption = f"📊 Suleymando {today_date_str} Tüm Bülten (.csv)"
        send_telegram_document(bot_token, chat_id, csv_bytes, filename, caption)
        
        return {"status": "success", "mode": mode, "total_matched": len(filt_m)}
    else:
        target_matches = filter_upcoming_not_started_matches(filt_m, window_hours=8)
        
        send_res = send_matches_individually(bot_token, chat_id, target_matches, window_hours=8)
        
        # Check and update scores as well
        check_and_update_won_matches(bot_token, chat_id, filt_m)

        return {
            "status": "success",
            "mode": mode,
            "sent_individually": send_res['sent'],
            "skipped_already_sent": send_res['skipped'],
            "total_matched": len(target_matches)
        }

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
