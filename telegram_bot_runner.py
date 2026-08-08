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
    format_telegram_winrate_report,
    send_matches_individually,
    check_and_update_won_matches,
    send_daily_parlay_coupon,
    send_short_term_coupon,
    filter_upcoming_not_started_matches
)

BOT_TOKEN = "8940991344:AAFA8qLKgNDdsp__3KThdtnMSXhh2VrrcI4"
CHAT_ID = "-5202583497"

scanner = BulletinScanner()

# ─── Kısa Vade Kuponu Gönderim Saatleri ─────────────────────────────────────
# 08:45  11:45  14:45  17:45  20:45  23:45
SHORT_TERM_COUPON_TIMES = [
    (8,  45),
    (11, 45),
    (14, 45),
    (17, 45),
    (20, 45),
    (23, 45),
]

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
        
        # Her çalışmada önceki mesajları güncelle
        update_res = check_and_update_won_matches(BOT_TOKEN, CHAT_ID, filt_m)
        if update_res['updated'] > 0:
            print(f"[{now_str}] ✅ {update_res['updated']} maç güncellendi (🏆 reaksiyon eklendi).")

        # ── Mod: Günün Banko Kuponu ──────────────────────────────────────────
        if mode == "parlay_coupon":
            ok = send_daily_parlay_coupon(BOT_TOKEN, CHAT_ID, filt_m)
            print(f"[{now_str}] 👑 Günün Banko Kupon Gönderim: {ok}")

        # ── Mod: Kısa Vade Kuponu (her 3 saatlik pencere) ───────────────────
        elif mode == "short_term_coupon":
            ok = send_short_term_coupon(BOT_TOKEN, CHAT_ID, filt_m, window_hours=3)
            print(f"[{now_str}] ⚡ Kısa Vade Kupon Gönderim: {ok}")

        # ── Mod: Gece 23:45 Gün Sonu Raporu & CSV ───────────────────────────
        elif mode == "night_2345":
            today_matches = [m for m in filt_m if m.get('date') == today_date_str]
            if not today_matches:
                today_matches = filt_m
                
            report_text = format_telegram_winrate_report(today_matches, today_date_str)
            csv_bytes = generate_csv_bulletin(filt_m, f"Suleymando_GunSonu_{today_date_str}")
            
            send_telegram_message(BOT_TOKEN, CHAT_ID, report_text)
            
            filename = f"suleymando_bulten_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.csv"
            caption = f"📊 Suleymando {today_date_str} Tüm Bülten ve İY Doğrulama Raporu (.csv)"
            ok = send_telegram_document(BOT_TOKEN, CHAT_ID, csv_bytes, filename, caption)
            print(f"[{now_str}] 🌙 Gece 23:45 CSV Gönderim: {ok}")
            
        # ── Mod: Her 2 Saatte Bir Yaklaşan Maç Bildirimi ────────────────────
        else:
            upcoming_8h_matches = filter_upcoming_not_started_matches(filt_m, window_hours=8)
            res = send_matches_individually(BOT_TOKEN, CHAT_ID, upcoming_8h_matches, window_hours=8)
            print(f"[{now_str}] 📱 Tek tek maç gönderim: {res}")
            
    except Exception as e:
        print(f"[{now_str}] ❌ Tarama Hatası: {e}")

if __name__ == "__main__":
    print("🤖 Suleymando Telegram Otomatik Bot Servisi Başlatıldı...")
    print(f"🎯 Hedef Grup Chat ID: {CHAT_ID}")
    print(f"⚡ Kısa Vade Kupon Saatleri: 08:45 | 11:45 | 14:45 | 17:45 | 20:45 | 23:45")
    
    # Başlangıçta bir tur çalıştır
    run_bot_scan(mode="every_2h")
    run_bot_scan(mode="parlay_coupon")
    
    # Zamanlayıcı kayıtları — aynı dakikada tekrar tetiklenmemesi için
    last_night_scan_date        = None       # 23:45 günlük rapor
    last_short_term_coupon_sent = set()      # (gün, saat, dakika) ikilisi
    last_2h_scan_time           = time.time()
    last_score_check_time       = time.time()
    
    while True:
        now = datetime.datetime.now()
        h, m = now.hour, now.minute
        today_key = now.date()

        # 1. ── Kısa Vade Kuponu: 08:45 / 11:45 / 14:45 / 17:45 / 20:45 / 23:45 ──
        for (target_h, target_m) in SHORT_TERM_COUPON_TIMES:
            slot_key = (today_key, target_h, target_m)
            if h == target_h and m == target_m and slot_key not in last_short_term_coupon_sent:
                print(f"⚡ {target_h:02d}:{target_m:02d} Kısa Vade Kupon Zamanlayıcısı Tetiklendi!")
                run_bot_scan(mode="short_term_coupon")
                last_short_term_coupon_sent.add(slot_key)
                # Seti temiz tut — sadece bugünün slotlarını sakla
                last_short_term_coupon_sent = {k for k in last_short_term_coupon_sent if k[0] == today_key}
        
        # 2. ── Gece 23:45 Gün Sonu Raporu (Kısa Vade ile aynı dakika — ayrı mod) ──
        if h == 23 and m == 45 and last_night_scan_date != today_key:
            print("🌙 Gece 23:45 Gün Sonu Zamanlayıcısı Tetiklendi!")
            run_bot_scan(mode="night_2345")
            last_night_scan_date = today_key

        # 3. ── Her 2 Saatte Bir Yaklaşan Maç Bildirimi ──────────────────────────
        if time.time() - last_2h_scan_time >= 7200:
            print("⏳ 2 Saatlik Periyodik Zamanlayıcı Tetiklendi!")
            run_bot_scan(mode="every_2h")
            last_2h_scan_time = time.time()

        # 4. ── Her 3 Dakikada Bir Sonuç Kontrolü (TUTTU/YATTI) ─────────────────
        if time.time() - last_score_check_time >= 180:
            try:
                _, filt_m = scanner.scan_bulletin(min_odds=1.00, max_odds=1.23, fetch_details=False)
                up_res = check_and_update_won_matches(BOT_TOKEN, CHAT_ID, filt_m)
                if up_res['updated'] > 0:
                    print(f"[{now.strftime('%H:%M:%S')}] 🏆 {up_res['updated']} maç TUTTU/YATTI güncellendi.")
            except Exception:
                pass
            last_score_check_time = time.time()

        time.sleep(30)
