import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from bulletin_scanner import BulletinScanner
s = BulletinScanner()
html = s.fetch_bulletin_html()
ms = s.parse_matches(html)

# Yabanci karakter iceren takim isimlerini bul
print("Yabanci karakter kontrolu (u-umlaut, o-umlaut vs):")
for m in ms:
    teams = m['home'] + m['away']
    if any(c in teams for c in ['ü','ö','ä','ú','ó','é','ñ']):
        print(f"  DOGRU: {m['home']} vs {m['away']}")
    elif any(c in teams for c in ['Ã','Å','Ä','Ã¼','Ã¶']):
        print(f"  BOZUK: {m['home']} vs {m['away']}")

# Ilk 8 mac
print("\nIlk 8 mac:")
for m in ms[:8]:
    print(f"  {m['home']} vs {m['away']}")
