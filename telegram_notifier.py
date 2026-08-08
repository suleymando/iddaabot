import urllib.request
import urllib.parse
import json

def send_telegram_message(bot_token: str, chat_id: str, text: str) -> bool:
    """
    Telegram Bot API üzerinden belirtilen Chat ID'ye mesaj gönderir.
    """
    if not bot_token or not chat_id:
        print("Telegram Bot Token veya Chat ID eksik.")
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
        print(f"Telegram Mesaj Gönderme Hatası: {e}")
        return False

def format_telegram_bulletin(matches: list, title: str) -> list:
    """
    Maç listesini Telegram HTML formatında mesaj parçalarına böler (Telegram 4096 karakter sınırına uygun).
    """
    if not matches:
        return [f"<b>{title}</b>\n\n⚠️ Bu periyotta Suleymando formülüne uyan maç bulunamadı."]
        
    messages = []
    header = f"⚡ <b>{title}</b>\n"
    header += f"📊 <b>Eşleşen Maç Sayısı: {len(matches)}</b>\n"
    header += "━━━━━━━━━━━━━━━━━━━\n\n"
    
    current_msg = header
    
    for idx, m in enumerate(matches, 1):
        iy_ust_str = f"{m.get('iy_1_5_ust'):.2f}" if m.get('iy_1_5_ust') else "N/A"
        extra_odd_str = ""
        
        if m['fav_side'] == 'EV SAHİBİ':
            extra_odd = m.get('iy_ms_2_1')
            extra_odd_str = f"{extra_odd:.2f}" if extra_odd else "N/A"
        else:
            extra_odd = m.get('iy_ms_1_x')
            extra_odd_str = f"{extra_odd:.2f}" if extra_odd else "N/A"
            
        fav_icon = "👑 EV" if m['fav_side'] == 'EV SAHİBİ' else "✈️ DEP"
        
        match_block = (
            f"<b>{idx}. ⏰ {m['time']}</b> | 🎯 <code>MBS:{m.get('mbs',1)}</code> | 📌 <code>Kod:{m['code']}</code>\n"
            f"⚽ <b>{m['home']}</b> vs <b>{m['away']}</b>\n"
            f"📊 MS1: <b>{m['ms1']:.2f}</b> | MSX: <b>{m['msx']:.2f}</b> | MS2: <b>{m['ms2']:.2f}</b> (Fav: {fav_icon})\n"
            f"🔥 <b>Ana Tahmin: İY 1.5 ÜST</b> (Oran: <code>{iy_ust_str}</code>)\n"
            f"🎯 <b>Ekstra: {m['extra_prediction']}</b> (Oran: <code>{extra_odd_str}</code>)\n"
            f"───────────────────\n"
        )
        
        if len(current_msg) + len(match_block) > 3900:
            messages.append(current_msg)
            current_msg = f"⚡ <b>{title} (Devamı)</b>\n\n" + match_block
        else:
            current_msg += match_block
            
    if current_msg:
        messages.append(current_msg)
        
    return messages

if __name__ == '__main__':
    # Test format
    sample_matches = [
        {
            'code': '18198', 'time': '21:00', 'home': 'PSV Eindhoven', 'away': 'Fortuna Sittard',
            'ms1': 1.00, 'msx': 7.71, 'ms2': 12.40, 'fav_side': 'EV SAHİBİ',
            'iy_1_5_ust': 1.50, 'iy_ms_2_1': 18.50, 'mbs': 1, 'extra_prediction': '2/1 (İY 2 / MS 1)'
        }
    ]
    formatted = format_telegram_bulletin(sample_matches, "GECE 23:45 TÜM BÜLTEN TARAMASI")
    print(formatted[0])
