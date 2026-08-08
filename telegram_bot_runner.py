import time
import datetime
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from bulletin_scanner import BulletinScanner
from telegram_notifier import send_telegram_message, format_telegram_bulletin

BOT_TOKEN = "8940991344:AAFA8qLKgNDdsp__3KThdtnMSXhh2VrrcI4"
CHAT_ID = "-5202583497"

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

def run_bot_scan(mode="every_4h"):
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{now_str}] Telegram Tarama Başlatılıyor... Mod: {mode}")
    
    try:
        all_m, filt_m = scanner.scan_bulletin(min_odds=1.00, max_odds=1.23, fetch_details=True)
        filt_m.sort(key=lambda m: parse_time_minutes(m['time']))
        
        if mode == "night_2345":
            title = "🌙 SULEYMANDO GECE 23:45 TÜM BÜLTEN TARAMASI"
            target_matches = filt_m
        else:
            title = "⏳ SULEYMANDO YAKLAŞAN 4 SAATLİK BÜLTEN TARAMASI"
            now_minutes = datetime.datetime.now().hour * 60 + datetime.datetime.now().minute
            max_target_minutes = now_minutes + (4 * 60)
            
            window_matches = [m for m in filt_m if now_minutes <= parse_time_minutes(m['time']) <= max_target_minutes]
            target_matches = window_matches if window_matches else filt_m[:5]
            
        msgs = format_telegram_bulletin(target_matches, title)
        for chunk in msgs:
            ok = send_telegram_message(BOT_TOKEN, CHAT_ID, chunk)
            print(f"[{now_str}] Mesaj Gönderim Durumu: {ok}")
            
    except Exception as e:
        print(f"[{now_str}] Tarama Hatası: {e}")

if __name__ == "__main__":
    print("🤖 Suleymando Telegram Otomatik Bot Servisi Başlatıldı...")
    print(f"🎯 Hedef Grup Chat ID: {CHAT_ID}")
    
    # İlk çalıştırmada hemen 1 tarama yapıp Telegram'a atalım
    run_bot_scan(mode="every_4h")
    
    last_night_scan_date = None
    last_4h_scan_time = time.time()
    
    while True:
        now = datetime.datetime.now()
        
        # 1. Gece 23:45 Taraması Kontrolü
        if now.hour == 23 and now.minute == 45 and last_night_scan_date != now.date():
            print("🌙 Gece 23:45 Zamanlayıcısı Tetiklendi!")
            run_bot_scan(mode="night_2345")
            last_night_scan_date = now.date()
            
        # 2. Her 4 Saatte Bir Periodik Tarama (14400 saniye)
        if time.time() - last_4h_scan_time >= 14400:
            print("⏳ 4 Saatlik Periyodik Zamanlayıcı Tetiklendi!")
            run_bot_scan(mode="every_4h")
            last_4h_scan_time = time.time()
            
        time.sleep(30)
