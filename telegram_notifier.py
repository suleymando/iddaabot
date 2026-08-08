import urllib.request
import json
import uuid
import io
import os
import datetime
import time
import pandas as pd
from typing import Optional, Dict, Any, List, Tuple

TRACKER_FILE = "sent_telegram_matches.json"

def send_telegram_message_raw(bot_token: str, chat_id: str, text: str, reply_markup: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    if not bot_token or not chat_id:
        return {'ok': False}
        
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': 'HTML',
        'disable_web_page_preview': True
    }
    if reply_markup:
        payload['reply_markup'] = reply_markup
    
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except Exception as e:
        print(f"Telegram Mesaj Hatası: {e}")
        return {'ok': False, 'error': str(e)}

def send_telegram_message(bot_token: str, chat_id: str, text: str, reply_markup: Optional[Dict[str, Any]] = None) -> bool:
    res = send_telegram_message_raw(bot_token, chat_id, text, reply_markup=reply_markup)
    return res.get('ok', False)

def edit_telegram_message(bot_token: str, chat_id: str, message_id: int, text: str, reply_markup: Optional[Dict[str, Any]] = None) -> bool:
    if not bot_token or not chat_id or not message_id:
        return False
        
    url = f"https://api.telegram.org/bot{bot_token}/editMessageText"
    payload = {
        'chat_id': chat_id,
        'message_id': message_id,
        'text': text,
        'parse_mode': 'HTML',
        'disable_web_page_preview': True
    }
    if reply_markup:
        payload['reply_markup'] = reply_markup
    
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            res = json.loads(resp.read().decode('utf-8'))
            return res.get('ok', False)
    except Exception as e:
        print(f"Telegram Düzenleme Hatası: {e}")
        return False

def set_telegram_reaction(bot_token: str, chat_id: str, message_id: int, emoji: str = "🏆") -> bool:
    if not bot_token or not chat_id or not message_id:
        return False
        
    url = f"https://api.telegram.org/bot{bot_token}/setMessageReaction"
    payload = {
        'chat_id': chat_id,
        'message_id': message_id,
        'reaction': [{'type': 'emoji', 'emoji': emoji}]
    }
    
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            res = json.loads(resp.read().decode('utf-8'))
            return res.get('ok', False)
    except Exception as e:
        print(f"Telegram Reaksiyon Hatası: {e}")
        return False

def send_telegram_document(bot_token: str, chat_id: str, file_bytes: bytes, filename: str, caption: str = "") -> bool:
    if not bot_token or not chat_id:
        return False
        
    boundary = uuid.uuid4().hex
    url = f"https://api.telegram.org/bot{bot_token}/sendDocument"
    
    body = []
    body.append(f'--{boundary}'.encode('utf-8'))
    body.append(f'Content-Disposition: form-data; name="chat_id"'.encode('utf-8'))
    body.append(b'')
    body.append(str(chat_id).encode('utf-8'))
    
    if caption:
        body.append(f'--{boundary}'.encode('utf-8'))
        body.append(f'Content-Disposition: form-data; name="caption"'.encode('utf-8'))
        body.append(b'')
        body.append(caption.encode('utf-8'))
        
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
    rows = []
    for m in matches:
        is_home_fav = (m['fav_side'] == 'EV SAHİBİ')
        iy_ust_odd = m.get('iy_1_5_ust')
        iy_ust_str = f"{iy_ust_odd:.2f}" if iy_ust_odd else "N/A"
        
        if is_home_fav:
            fav_gol_odd = m.get('ev_iki_yari_gol') or m.get('iy_0_5_ust') or m.get('ev_0_5_ust') or m.get('iy_1')
        else:
            fav_gol_odd = m.get('dep_iki_yari_gol') or m.get('iy_0_5_ust') or m.get('dep_0_5_ust') or m.get('iy_2')
            
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

def format_single_match_card(m: dict, status_override: Optional[str] = None) -> Tuple[str, Optional[Dict[str, Any]]]:
    """
    Format single match as Telegram HTML text card along with Inline Keyboard Buttons.
    """
    is_home_fav = (m['fav_side'] == 'EV SAHİBİ')
    iy_ust_odd = m.get('iy_1_5_ust')
    iy_ust_str = f"{iy_ust_odd:.2f}" if iy_ust_odd else "N/A"
    
    if is_home_fav:
        fav_gol_odd = m.get('ev_iki_yari_gol') or m.get('iy_0_5_ust') or m.get('ev_0_5_ust') or m.get('iy_1')
    else:
        fav_gol_odd = m.get('dep_iki_yari_gol') or m.get('iy_0_5_ust') or m.get('dep_0_5_ust') or m.get('iy_2')
        
    fav_gol_str = f"{fav_gol_odd:.2f}" if fav_gol_odd else "N/A"
    fav_icon = "👑 EV SAHİBİ" if is_home_fav else "✈️ DEPLASMAN"
    
    status_val = status_override or m.get('iy_1_5_status', 'OYNANMADI')
    
    status_header = ""
    if status_val == 'TUTTU':
        status_header = f"✅ <b>İLK YARI 1.5 ÜST TUTTU! (İY SKOR: {m.get('iy_score','-')})</b>\n━━━━━━━━━━━━━━━━━━━\n"
    elif status_val == 'YATTI':
        status_header = f"❌ <b>İLK YARI 1.5 ÜST YATTI (İY SKOR: {m.get('iy_score','-')})</b>\n━━━━━━━━━━━━━━━━━━━\n"
        
    msg = (
        f"{status_header}"
        f"👑 <b>SULEYMANDO İDDAA BÜLTEN KARTI</b>\n"
        f"⏰ <b>SAAT: {m['time']}</b> | <code>MBS: {m.get('mbs',1)}</code> | 📌 <code>{m['code']}</code>\n"
        f"📅 <b>Tarih:</b> {m.get('date','')}\n\n"
        f"⚽ <b>{'👑 ' if is_home_fav else ''}{m['home']}</b> vs <b>{'👑 ' if not is_home_fav else ''}{m['away']}</b>\n"
        f"🎯 <b>Favori:</b> {fav_icon} (Oran: <code>{m['fav_odds']:.2f}</code>)\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"🔥 <b>ANA TAHMİN: İY 1.5 ÜST</b> (Oran: <code>{iy_ust_str}</code>) {'✅' if status_val == 'TUTTU' else ''}\n"
        f"⚽ <b>EKSTRA: FAVORİ İY 1 GOL ATAR</b> (Oran: <code>{fav_gol_str}</code>)\n"
        f"📊 <b>MS 1:</b> <code>{m['ms1']:.2f}</code> | <b>MS X:</b> <code>{m['msx']:.2f}</code> | <b>MS 2:</b> <code>{m['ms2']:.2f}</code>"
    )
    
    reply_markup = None
    match_id = m.get('match_id')
    if match_id:
        reply_markup = {
            "inline_keyboard": [
                [
                    {"text": "🔗 Mackolik Maç Detayı", "url": f"https://arsiv.mackolik.com/Mac/{match_id}"}
                ]
            ]
        }
        
    return msg, reply_markup

def generate_daily_parlay_coupon(matches: list, coupon_size: int = 3) -> Dict[str, Any]:
    """
    Formüle uyan en güçlü maçlardan Günün Banko Kasa Kuponunu oluşturur.
    """
    valid_matches = [m for m in matches if m.get('iy_1_5_ust') and m.get('iy_1_5_ust') > 1.00]
    if not valid_matches:
        valid_matches = matches
        
    selected = valid_matches[:coupon_size]
    
    total_odds = 1.0
    items = []
    
    for idx, m in enumerate(selected, 1):
        odd = m.get('iy_1_5_ust') or 1.50
        total_odds *= odd
        items.append({
            'num': idx,
            'time': m.get('time', ''),
            'code': m.get('code', ''),
            'home': m.get('home', ''),
            'away': m.get('away', ''),
            'odd': odd
        })
        
    today_str = datetime.datetime.now().strftime("%d.%m.%Y")
    
    coupon_text = (
        f"👑 <b>SULEYMANDO GÜNÜN BANKO KASA KUPONU</b> 👑\n"
        f"📅 <b>Tarih: {today_str}</b> | 📊 <b>TOPLAM ORAN: {total_odds:.2f}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━\n\n"
    )
    
    for item in items:
        coupon_text += (
            f"<b>{item['num']}. ⏰ {item['time']}</b> | 📌 <code>{item['code']}</code>\n"
            f"⚽ <b>{item['home']} vs {item['away']}</b>\n"
            f"🔥 <b>Tahmin: İY 1.5 ÜST</b> (Oran: <code>{item['odd']:.2f}</code>)\n"
            f"───────────────────\n"
        )
        
    coupon_text += (
        f"\n🎯 <b>ÖNERİLEN BAHİS: KASA %10</b>\n"
        f"🔥 <i>Suleymando %86 Başarı Formülü İle Seçilmiştir.</i>"
    )
    
    return {
        'text': coupon_text,
        'total_odds': total_odds,
        'matches': selected
    }

def send_daily_parlay_coupon(bot_token: str, chat_id: str, matches: list, coupon_size: int = 3) -> bool:
    coupon_data = generate_daily_parlay_coupon(matches, coupon_size)
    return send_telegram_message(bot_token, chat_id, coupon_data['text'])


# ─────────────────────────────────────────────────────────────────────────────
# KISA VADE KUPONU — Önümüzdeki 3 saatlik penceredeki en iyi 3 maç
# ─────────────────────────────────────────────────────────────────────────────

def _parse_time_minutes(time_str: str) -> int:
    """HH:MM formatını dakikaya çevirir. Gece yarısı sonrası saatlere +24*60 ekler."""
    try:
        h, m = map(int, time_str.split(':'))
        if 0 <= h < 6:
            return (h + 24) * 60 + m
        return h * 60 + m
    except Exception:
        return 9999

def parse_match_datetime(match: dict, now: Optional[datetime.datetime] = None) -> Optional[datetime.datetime]:
    now = now or datetime.datetime.now()
    date_str = str(match.get('date') or now.strftime("%d.%m.%Y")).strip()
    time_str = str(match.get('time') or "").strip()

    try:
        return datetime.datetime.strptime(f"{date_str} {time_str}", "%d.%m.%Y %H:%M")
    except Exception:
        return None

def is_match_not_started(match: dict, now: Optional[datetime.datetime] = None) -> bool:
    now = now or datetime.datetime.now()
    match_dt = parse_match_datetime(match, now)
    if not match_dt or match_dt <= now:
        return False

    status = str(match.get('iy_1_5_status') or 'OYNANMADI').upper()
    if status != 'OYNANMADI':
        return False

    if str(match.get('iy_score') or '').strip():
        return False

    return True

def filter_upcoming_not_started_matches(
    matches: list,
    window_hours: int = 8,
    now: Optional[datetime.datetime] = None
) -> list:
    now = now or datetime.datetime.now()
    window_end = now + datetime.timedelta(hours=window_hours)

    return [
        m for m in matches
        if is_match_not_started(m, now)
        and (match_dt := parse_match_datetime(m, now)) is not None
        and match_dt <= window_end
    ]

def generate_short_term_coupon(matches: list, window_hours: int = 3, coupon_size: int = 3) -> Dict[str, Any]:
    """
    Önümüzdeki `window_hours` saat içinde başlayacak maçlardan en iyi 3'ünü seçer
    ve 'Kısa Vade Kuponu' oluşturur.
    """
    now = datetime.datetime.now()
    window_matches = [m for m in matches if m.get('iy_1_5_ust')]
    window_matches = filter_upcoming_not_started_matches(window_matches, window_hours, now)

    selected = window_matches[:coupon_size]

    total_odds = 1.0
    items = []
    for idx, m in enumerate(selected, 1):
        odd = m.get('iy_1_5_ust') or 1.50
        total_odds *= odd
        items.append({
            'num': idx,
            'time': m.get('time', ''),
            'code': m.get('code', ''),
            'home': m.get('home', ''),
            'away': m.get('away', ''),
            'odd': odd
        })

    window_end = (now + datetime.timedelta(hours=window_hours)).strftime("%H:%M")
    now_str    = now.strftime("%H:%M")

    coupon_text = (
        f"⚡ <b>SULEYMANDO KISA VADE KUPONU</b> ⚡\n"
        f"🕐 <b>Saat Aralığı: {now_str} – {window_end}</b> (Önümüzdeki {window_hours} Saat)\n"
        f"📊 <b>TOPLAM ORAN: {total_odds:.2f}</b> | 🎯 <b>{len(selected)} Maç</b>\n"
        f"━━━━━━━━━━━━━━━━━━━\n\n"
    )

    for item in items:
        coupon_text += (
            f"<b>{item['num']}. ⏰ {item['time']}</b> | 📌 <code>{item['code']}</code>\n"
            f"⚽ <b>{item['home']} vs {item['away']}</b>\n"
            f"🔥 <b>Tahmin: İY 1.5 ÜST</b> (Oran: <code>{item['odd']:.2f}</code>)\n"
            f"───────────────────\n"
        )

    coupon_text += (
        f"\n💡 <b>ÖNERİLEN BAHİS: KASA %5</b>\n"
        f"⚡ <i>Önümüzdeki 3 saatin en güçlü kombinasyonu.</i>"
    )

    return {
        'text': coupon_text,
        'total_odds': total_odds,
        'matches': selected,
        'window_match_count': len(window_matches)
    }

def send_short_term_coupon(bot_token: str, chat_id: str, matches: list,
                           window_hours: int = 3, coupon_size: int = 3) -> bool:
    """Kısa Vade Kuponunu Telegram grubuna gönderir."""
    coupon_data = generate_short_term_coupon(matches, window_hours, coupon_size)
    if not coupon_data['matches']:
        return False
    return send_telegram_message(bot_token, chat_id, coupon_data['text'])


def load_tracker(tracker_file: str = TRACKER_FILE) -> dict:
    if os.path.exists(tracker_file):
        try:
            with open(tracker_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_tracker(data: dict, tracker_file: str = TRACKER_FILE):
    try:
        with open(tracker_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print("Tracker kaydetme hatasi:", e)

def send_matches_individually(
    bot_token: str,
    chat_id: str,
    matches: list,
    tracker_file: str = TRACKER_FILE,
    enforce_upcoming: bool = True,
    window_hours: int = 8
) -> dict:
    tracker = load_tracker(tracker_file)
    sent_count = 0
    skipped_count = 0
    skipped_started_count = 0

    if enforce_upcoming:
        original_count = len(matches)
        matches = filter_upcoming_not_started_matches(matches, window_hours)
        skipped_started_count = original_count - len(matches)
    
    for m in matches:
        match_id = str(m.get('match_id') or f"{m.get('date')}_{m.get('code')}")
        
        if match_id in tracker and tracker[match_id].get('message_id'):
            skipped_count += 1
            continue
            
        card_text, reply_markup = format_single_match_card(m)
        res = send_telegram_message_raw(bot_token, chat_id, card_text, reply_markup=reply_markup)
        
        if res.get('ok') and res.get('result', {}).get('message_id'):
            msg_id = res['result']['message_id']
            tracker[match_id] = {
                'match_id': match_id,
                'code': m.get('code'),
                'home': m.get('home'),
                'away': m.get('away'),
                'date': m.get('date'),
                'time': m.get('time'),
                'chat_id': str(chat_id),
                'message_id': msg_id,
                'status': m.get('iy_1_5_status', 'OYNANMADI'),
                'goal_alert_sent': False,
                'sent_at': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'match_data': m
            }
            sent_count += 1
            time.sleep(0.4)
            
    save_tracker(tracker, tracker_file)
    return {
        'sent': sent_count,
        'skipped': skipped_count,
        'skipped_started': skipped_started_count,
        'total_tracked': len(tracker)
    }

def check_and_update_won_matches(bot_token: str, chat_id: str, current_matches: list, tracker_file: str = TRACKER_FILE) -> dict:
    """
    Daha önce Telegram'a gönderilmiş maçların İY 1.5 ÜST sonucunu kontrol eder.
    TUTTU → mesaj güncellenir + 🏆 reaksiyon eklenir
    YATTI → mesaj güncellenir (kırmızı ❌ ile)
    """
    tracker = load_tracker(tracker_file)
    if not tracker:
        return {'updated': 0, 'goal_alerts': 0, 'total': 0}

    match_lookup = {str(m.get('match_id') or f"{m.get('date')}_{m.get('code')}"): m for m in current_matches}
    updated_count = 0

    for match_id, item in tracker.items():
        msg_id    = item.get('message_id')
        curr_status = item.get('status', 'OYNANMADI')

        # Zaten sonuçlandıysa atla
        if curr_status in ['TUTTU', 'YATTI']:
            continue

        latest_m = match_lookup.get(match_id)
        if not latest_m:
            continue

        new_status = latest_m.get('iy_1_5_status', 'OYNANMADI')
        if new_status not in ['TUTTU', 'YATTI']:
            continue

        # Telegram mesajını güncelle
        updated_text, reply_markup = format_single_match_card(latest_m, status_override=new_status)
        edit_telegram_message(bot_token, chat_id, msg_id, updated_text, reply_markup=reply_markup)

        # TUTTU ise 🏆 reaksiyonu ekle (Telegram'ın desteklediği emoji)
        if new_status == 'TUTTU':
            set_telegram_reaction(bot_token, chat_id, msg_id, emoji="🏆")

        item['status']     = new_status
        item['updated_at'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        updated_count += 1
        time.sleep(0.4)

    save_tracker(tracker, tracker_file)
    return {'updated': updated_count, 'goal_alerts': 0, 'total': len(tracker)}

def format_telegram_2h_bulletin(matches: list) -> str:
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
            fav_gol_odd = m.get('ev_iki_yari_gol') or m.get('iy_0_5_ust') or m.get('ev_0_5_ust') or m.get('iy_1')
        else:
            fav_gol_odd = m.get('dep_iki_yari_gol') or m.get('iy_0_5_ust') or m.get('dep_0_5_ust') or m.get('iy_2')
            
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
