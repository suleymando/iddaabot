import urllib.request
import json
import uuid
import io
import pandas as pd

def send_telegram_message(bot_token: str, chat_id: str, text: str) -> bool:
    if not bot_token or not chat_id:
        return False
        
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': 'HTML',
        'disable_web_page_preview': True
    }
    
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            res = json.loads(resp.read().decode('utf-8'))
            return res.get('ok', False)
    except Exception as e:
        print(f"Telegram Mesaj Hatası: {e}")
        return False

def send_telegram_document(bot_token: str, chat_id: str, file_bytes: bytes, filename: str, caption: str = "") -> bool:
    if not bot_token or not chat_id:
        return False
        
    boundary = uuid.uuid4().hex
    url = f"https://api.telegram.org/bot{bot_token}/sendDocument"
    
    body = []
    
    # chat_id
    body.append(f'--{boundary}'.encode('utf-8'))
    body.append(f'Content-Disposition: form-data; name="chat_id"'.encode('utf-8'))
    body.append(b'')
    body.append(str(chat_id).encode('utf-8'))
    
    # caption
    if caption:
        body.append(f'--{boundary}'.encode('utf-8'))
        body.append(f'Content-Disposition: form-data; name="caption"'.encode('utf-8'))
        body.append(b'')
        body.append(caption.encode('utf-8'))
        
    # document
    body.append(f'--{boundary}'.encode('utf-8'))
    body.append(f'Content-Disposition: form-data; name="document"; filename="{filename}"'.encode('utf-8'))
    body.append(b'Content-Type: text/csv; charset=utf-8')
    body.append(b'')
    body.append(file_bytes)
    
    body.append(f'--{boundary}--'.encode('utf-8'))
    body.append(b'')
    
    payload_data = b'\r\n'.join(body)
    
    headers = {
        'Content-Type': f'multipart/form-data; boundary={boundary}',
        'Content-Length': str(len(payload_data))
    }
    
    req = urllib.request.Request(url, data=payload_data, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            res = json.loads(resp.read().decode('utf-8'))
            return res.get('ok', False)
    except Exception as e:
        print(f"Telegram Doküman Hatası: {e}")
        return False

def generate_csv_bulletin(matches: list, title: str = "SULEYMANDO BÜLTENİ") -> bytes:
    """
    Formüle uyan maçları UTF-8-SIG (Excel uyumlu CSV) dosyasına dönüştürür.
    """
    rows = []
    for m in matches:
        is_home_fav = (m['fav_side'] == 'EV SAHİBİ')
        iy_ust_odd = m.get('iy_1_5_ust')
        iy_ust_str = f"{iy_ust_odd:.2f}" if iy_ust_odd else "N/A"
        
        if is_home_fav:
            fav_gol_odd = m.get('ev_iki_yari_gol') or m.get('iy_0_5_ust') or m.get('ev_0_5_ust')
        else:
            fav_gol_odd = m.get('dep_iki_yari_gol') or m.get('iy_0_5_ust') or m.get('dep_0_5_ust')
            
        fav_gol_str = f"{fav_gol_odd:.2f}" if fav_gol_odd else "N/A"
        status_str = m.get('iy_1_5_status', 'OYNANMADI')
        
        rows.append({
            'Tarih': m.get('date', ''),
            'Saat': m.get('time', ''),
            'Kod': m.get('code', ''),
            'MBS': m.get('mbs', 1),
            'Ev Sahibi': m.get('home', ''),
            'Deplasman': m.get('away', ''),
            'MS 1': m.get('ms1', 0.0),
            'MS X': m.get('msx', 0.0),
            'MS 2': m.get('ms2', 0.0),
            'Favori Taraf': m.get('fav_side', ''),
            'Favori Oran': m.get('fav_odds', 0.0),
            'İY 1.5 Üst Oran': iy_ust_str,
            'Favori İY 1 Gol Oranı': fav_gol_str,
            'Ana Tahmin': 'İY 1.5 ÜST',
            'Ekstra Tahmin': 'FAVORİ İY 1 GOL ATAR',
            'İY Skoru': m.get('iy_score', '-'),
            'MS Skoru': m.get('ms_score', '-'),
            'İY 1.5 Üst Durumu': status_str
        })
        
    df = pd.DataFrame(rows)
    csv_string = df.to_csv(index=False, encoding='utf-8-sig')
    return csv_string.encode('utf-8-sig')

def format_telegram_2h_bulletin(matches: list) -> str:
    """
    Önümüzdeki 2 saat içinde başlayacak tüm maçların TEK BİR MESAJ HAFİF ŞABLONU.
    """
    if not matches:
        return "⏳ <b>SULEYMANDO BİLDİRİMİ</b>\n\nÖnümüzdeki 2 saat içinde başlayacak formüle uyan maç bulunmamaktadır."
        
    msg = f"⏳ <b>SULEYMANDO YAKLAŞAN 2 SAATLİK MAÇLAR</b>\n"
    msg += f"📊 <b>Başlayacak Maç Sayısı: {len(matches)}</b>\n"
    msg += "━━━━━━━━━━━━━━━━━━━\n\n"
    
    for idx, m in enumerate(matches, 1):
        is_home_fav = (m['fav_side'] == 'EV SAHİBİ')
        iy_ust_odd = m.get('iy_1_5_ust')
        iy_ust_str = f"{iy_ust_odd:.2f}" if iy_ust_odd else "N/A"
        
        if is_home_fav:
            fav_gol_odd = m.get('ev_iki_yari_gol') or m.get('iy_0_5_ust') or m.get('ev_0_5_ust')
        else:
            fav_gol_odd = m.get('dep_iki_yari_gol') or m.get('iy_0_5_ust') or m.get('dep_0_5_ust')
            
        fav_gol_str = f"{fav_gol_odd:.2f}" if fav_gol_odd else "N/A"
        fav_icon = "👑 EV" if is_home_fav else "✈️ DEP"
        
        msg += (
            f"<b>{idx}. ⏰ {m['time']}</b> | <code>MBS:{m.get('mbs',1)}</code> | 📌 <code>{m['code']}</code>\n"
            f"⚽ <b>{m['home']}</b> vs <b>{m['away']}</b> (Fav: {fav_icon})\n"
            f"🔥 <b>İY 1.5 ÜST:</b> <code>{iy_ust_str}</code> | ⚽ <b>Fav İY Gol:</b> <code>{fav_gol_str}</code>\n"
            f"───────────────────\n"
        )
        
    return msg

def format_telegram_winrate_report(matches: list, date_str: str) -> str:
    """
    Gece 23:45 Gün Sonu Başarı ve İY Skor Doğrulama TEK MESAJ Raporu.
    """
    played_matches = [m for m in matches if m.get('iy_1_5_status') in ['TUTTU', 'YATTI']]
    won_matches = [m for m in played_matches if m.get('iy_1_5_status') == 'TUTTU']
    lost_matches = [m for m in played_matches if m.get('iy_1_5_status') == 'YATTI']
    
    total_count = len(played_matches)
    won_count = len(won_matches)
    lost_count = len(lost_matches)
    
    win_rate = (won_count / total_count * 100) if total_count > 0 else 0.0
    
    report = (
        f"🏆 <b>SULEYMANDO GÜN SONU BAŞARI RAPORU (23:45)</b>\n"
        f"📅 <b>Tarih: {date_str}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━\n\n"
        f"✅ <b>Tutan İY 1.5 ÜST Maç Sayısı:</b> {won_count}\n"
        f"❌ <b>Yatan Maç Sayısı:</b> {lost_count}\n"
        f"📊 <b>Oynanan Toplam Maç:</b> {total_count}\n"
        f"🔥 <b>GÜNÜN BAŞARI ORANI:</b> <b>%{win_rate:.1f}</b>\n\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"📎 <i>Detaylı maç listesi ve İY skor doğrulama raporu ekteki CSV dosyasındadır.</i>"
    )
    return report
