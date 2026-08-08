import sys, io, os, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bulletin_scanner import BulletinScanner
from telegram_notifier import (
    send_matches_individually,
    check_and_update_won_matches,
    send_daily_parlay_coupon,
    generate_daily_parlay_coupon,
    load_tracker, save_tracker
)

BOT_TOKEN = "8940991344:AAFA8qLKgNDdsp__3KThdtnMSXhh2VrrcI4"
CHAT_ID   = "-5202583497"
TRACKER   = "test_tracker2.json"

print("=" * 60)
print("🧪 TEMİZ TEST: GÖNDER + SONUÇ GÜNCELLE")
print("=" * 60)

# 1. Bültenden 3 maç al
print("\n[1/3] 📡 Bülten taranıyor...")
scanner = BulletinScanner()
_, filt  = scanner.scan_bulletin(1.00, 1.23, fetch_details=True)
sample   = filt[:3]
print(f"    ✅ {len(sample)} maç kullanılacak")
for m in sample:
    print(f"       • [{m['code']}] {m['home']} vs {m['away']}  İY 1.5 ÜST: {m.get('iy_1_5_ust','N/A')}")

# 2. Tek tek gönder
print("\n[2/3] 📱 Maçlar Telegram'a gönderiliyor...")
res = send_matches_individually(BOT_TOKEN, CHAT_ID, sample, tracker_file=TRACKER)
print(f"    ✅ Gönderildi: {res['sent']}  |  Atlandı: {res['skipped']}")

# 3. TUTTU simülasyonu — 1. maç kazandı
print("\n[3/3] 🏆 1. maç TUTTU simülasyonu, mesaj Telegram'da güncelleniyor...")
time.sleep(2)
sim_matches = [dict(m) for m in sample]
sim_matches[0]['iy_1_5_status'] = 'TUTTU'   # 1. maç TUTTU
sim_matches[1]['iy_1_5_status'] = 'YATTI'   # 2. maç YATTI
# 3. maç hala OYNANMADI

up = check_and_update_won_matches(BOT_TOKEN, CHAT_ID, sim_matches, tracker_file=TRACKER)
print(f"    ✅ Güncellenen: {up['updated']} maç")
print(f"       → Telegram'da 1. maç kartı ✅ TUTTU olarak düzenlendi + 🏆 reaksiyon eklendi")
print(f"       → 2. maç kartı ❌ YATTI olarak düzenlendi")

# 4. Kupon
print("\n[BONUS] 👑 Günün Banko Kuponu gönderiliyor...")
ok = send_daily_parlay_coupon(BOT_TOKEN, CHAT_ID, filt)
coupon = generate_daily_parlay_coupon(filt)
print(f"    {'✅ Gönderildi!' if ok else '❌ Gönderilemedi!'} Toplam Oran: {coupon['total_odds']:.2f}")

# Cleanup
try:
    os.remove(TRACKER)
    print("\n🧹 Test tracker temizlendi.")
except:
    pass

print("\n" + "=" * 60)
print("🎉 TEST TAMAMLANDI — Telegram grubunu kontrol edin!")
print("=" * 60)
