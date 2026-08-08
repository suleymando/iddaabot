import time
import datetime
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from bulletin_scanner import BulletinScanner
from telegram_notifier import (
    send_telegram_message, 
    send_telegram_document, 
    generate_csv_bulletin, 
    format_telegram_2h_bulletin,
    format_telegram_winrate_report
)

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

def run_bot_scan(mode="every_2h"):
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    today_date_str = datetime.datetime.now().strftime("%d.%m.%Y")
    print(f"[{now_str}] Telegram Tarama Başlatılıyor... Mod: {mode}")
    
    try:
        all_m, filt_m = scanner.scan_bulletin(min_odds=1.00, max_odds=1.23, fetch_details=True)
        filt_m.sort(key=lambda m: (m.get('date', ''), parse_time_minutes(m['time'])))
        
        if mode == "night_2345":
            # 23:45 GÜN SONU BAŞARI KONTROLÜ VE CSV GÖNDERİMİ
            today_matches = [m for m in filt_m if m.get('date') == today_date_str]
            if not today_matches:
                today_matches = filt_m
                
            report_text = format_telegram_winrate_report(today_matches, today_date_str)
            csv_bytes = generate_csv_bulletin(filt_m, f"Suleymando_GunSonu_{today_date_str}")
            
            # Send Victory Report Text
            send_telegram_message(BOT_TOKEN, CHAT_ID, report_text)
            
            # Send CSV File Document
            filename = f"suleymando_bulten_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.csv"
            caption = f"📊 Suleymando {today_date_str} Tüm Bülten ve İY Doğrulama Raporu (.csv)"
            ok = send_telegram_document(BOT_TOKEN, CHAT_ID, csv_bytes, filename, caption)
            print(f"[{now_str}] Gece 23:45 CSV Gönderim Durumu: {ok}")
            
        else:
            # ÖNÜMÜZDEKİ 2 SAAT İÇİNDE BAŞLAYACAK MAÇLAR (TEK MESAJ)
            now_minutes = datetime.datetime.now().hour * 60 + datetime.datetime.now().minute
            max_target_minutes = now_minutes + (2 * 60)
            
            upcoming_2h_matches = [
                m for m in filt_m 
                if m.get('date') == today_date_str and now_minutes <= parse_time_minutes(m['time']) <= max_target_minutes
            ]
            
            msg_text = format_telegram_2h_bulletin(upcoming_2h_matches)
            ok = send_telegram_message(BOT_TOKEN, CHAT_ID, msg_text)
            print(f"[{now_str}] 2 Saatlik Tek Mesaj Gönderim Durumu: {ok} (Maç Sayısı: {len(upcoming_2h_matches)})")
            
    except Exception as e:
        print(f"[{now_str}] Tarama Hatası: {e}")

if __name__ == "__main__":
    print("🤖 Suleymando Telegram Otomatik Bot Servisi Başlatıldı...")
    print(f"🎯 Hedef Grup Chat ID: {CHAT_ID}")
    
    # İlk çalıştırmada 2 saatlik yaklaşan maç taraması
    run_bot_scan(mode="every_2h")
    
    last_night_scan_date = None
    last_2h_scan_time = time.time()
    
    while True:
        now = datetime.datetime.now()
        
        # 1. Gece 23:45 Gün Sonu Başarı Raporu & CSV Gönderimi
        if now.hour == 23 and now.minute == 45 and last_night_scan_date != now.date():
            print("🌙 Gece 23:45 Gün Sonu Zamanlayıcısı Tetiklendi!")
            run_bot_scan(mode="night_2345")
            last_night_scan_date = now.date()
            
        # 2. Her 2 Saatte Bir Yaklaşan Maç Uyarısı (7200 saniye)
        if time.time() - last_2h_scan_time >= 7200:
            print("⏳ 2 Saatlik Periyodik Zamanlayıcı Tetiklendi!")
            run_bot_scan(mode="every_2h")
            last_2h_scan_time = time.time()
            
        time.sleep(30)
