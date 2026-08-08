import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from bulletin_scanner import BulletinScanner
from telegram_notifier import send_short_term_coupon, generate_short_term_coupon

scanner = BulletinScanner()
_, filt = scanner.scan_bulletin(1.00, 1.23, fetch_details=True)

coupon = generate_short_term_coupon(filt, window_hours=3)
print(f"Penceredeki mac: {coupon['window_match_count']}")
print(f"Secilen mac: {len(coupon['matches'])}")
print(f"Toplam oran: {coupon['total_odds']:.2f}")
print("--- Mesaj onizleme ---")
print(coupon['text'][:600])
print()

ok = send_short_term_coupon("8940991344:AAFA8qLKgNDdsp__3KThdtnMSXhh2VrrcI4", "-5202583497", filt)
print(f"Telegram gonderim: {'BASARILI' if ok else 'HATA'}")
