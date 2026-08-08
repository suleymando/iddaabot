import urllib.request
import re
import datetime
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Tuple, Optional

MACKOLIK_URL = "https://arsiv.mackolik.com/AjaxHandlers/IddaaHandler.aspx?command=tab&type=1&st=1&l=-1&d=-1&i=0&t=&ip=1&w=-1&g=7&np=0&srt=1&srtd=1"
MACKOLIK_FALLBACK_URL = "https://arsiv.mackolik.com/Iddaa-Programi"

class BulletinScanner:
    """
    Mackolik İddaa Bülteni Tarayıcı, Detaylı Oran Çekici, Tarih İzleyici ve Suleymando Filtre Motoru
    """
    def __init__(self, url: str = MACKOLIK_URL):
        self.url = url
        self.fallback_url = MACKOLIK_FALLBACK_URL
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7',
            'Referer': 'https://arsiv.mackolik.com/Iddaa-Programi'
        }

    def fetch_bulletin_html(self) -> str:
        def _decode(raw_bytes: bytes, http_charset: str = None) -> str:
            # 1. HTTP header'dan gelen charset'i dene
            if http_charset:
                try:
                    return raw_bytes.decode(http_charset, errors='ignore')
                except (LookupError, UnicodeDecodeError):
                    pass
            # 2. HTML <meta charset> etiketinden charset bul
            sniff = raw_bytes[:4096].decode('ascii', errors='ignore')
            meta_cs = re.search(r'charset=["\']?([\w-]+)', sniff, re.IGNORECASE)
            if meta_cs:
                cs = meta_cs.group(1).strip()
                try:
                    return raw_bytes.decode(cs, errors='ignore')
                except (LookupError, UnicodeDecodeError):
                    pass
            # 3. Mackolik her zaman windows-1254 → son fallback
            return raw_bytes.decode('windows-1254', errors='ignore')

        try:
            req = urllib.request.Request(self.url, headers=self.headers)
            resp = urllib.request.urlopen(req, timeout=20)
            raw_bytes = resp.read()
            # Content-Type header'dan charset al
            ct = resp.headers.get('Content-Type', '')
            cs_match = re.search(r'charset=([\w-]+)', ct, re.IGNORECASE)
            http_charset = cs_match.group(1) if cs_match else None
            html = _decode(raw_bytes, http_charset)
            if len(html) > 100000:
                return html
        except Exception:
            pass

        req = urllib.request.Request(self.fallback_url, headers=self.headers)
        resp = urllib.request.urlopen(req, timeout=20)
        raw_bytes = resp.read()
        ct = resp.headers.get('Content-Type', '')
        cs_match = re.search(r'charset=([\w-]+)', ct, re.IGNORECASE)
        http_charset = cs_match.group(1) if cs_match else None
        return _decode(raw_bytes, http_charset)



    def parse_matches(self, html: str) -> List[Dict[str, Any]]:
        tr_blocks = re.findall(r'<tr[^>]*>.*?</tr>', html, re.DOTALL | re.IGNORECASE)
        
        parsed_matches = []
        seen_keys = set()
        current_date = datetime.datetime.now().strftime("%d.%m.%Y")
        
        for tr in tr_blocks:
            date_m = re.search(r'(\d{2}\.\d{2}\.\d{4})', tr)
            if 'popMatch' not in tr and date_m:
                current_date = date_m.group(1)
                continue
                
            if 'popMatch' not in tr:
                continue
                
            mac_id_m = re.search(r'popMatch\((\d+)', tr)
            match_id = mac_id_m.group(1) if mac_id_m else ""
            
            teams = re.findall(r'popTeam\(\d+\)[^>]*>\s*([^<]+)', tr)
            if len(teams) < 2:
                continue
            home_team = teams[0].replace('&nbsp;', ' ').strip()
            away_team = teams[1].replace('&nbsp;', ' ').strip()
            
            time_m = re.search(r'<td[^>]*align=["\']center["\'][^>]*>(\d{2}:\d{2})</td>', tr)
            match_time = time_m.group(1) if time_m else "--:--"
            
            code_m = re.search(r'<td[^>]*align=["\']center["\'][^>]*>(\d{4,6})</td>', tr)
            code = code_m.group(1) if code_m else "------"
            
            tds = re.findall(r'<td[^>]*>(.*?)</td>', tr, re.DOTALL)
            score_cells = [t.strip() for t in tds if re.match(r'^\d+-\d+$', t.strip())]
            
            iy_score = score_cells[0] if len(score_cells) > 0 else ""
            ms_score = score_cells[1] if len(score_cells) > 1 else ""
            
            iy_goals = -1
            iy_1_5_status = "OYNANMADI"
            
            if iy_score:
                try:
                    hp, ap = map(int, iy_score.split('-'))
                    iy_goals = hp + ap
                    if iy_goals >= 2:
                        iy_1_5_status = "TUTTU"
                    else:
                        iy_1_5_status = "YATTI"
                except Exception:
                    pass
                    
            match_key = f"{current_date}_{code}_{home_team}_{away_team}"
            if match_key in seen_keys:
                continue
            seen_keys.add(match_key)
            
            dialogs = re.findall(r'openOddsDialog\((.*?)\)', tr)
            ms1, msx, ms2 = 0.0, 0.0, 0.0
            found_ms = False
            
            for d in dialogs:
                if 'Ma' in d and 'Sonucu' in d:
                    brackets = re.findall(r'\[(.*?)\]', d)
                    if len(brackets) >= 2:
                        odds_items = re.findall(r"'([^']+)'", brackets[1])
                        if len(odds_items) == 3:
                            try:
                                ms1 = float(odds_items[0].replace(',', '.')) if odds_items[0] != '-' else 0.0
                                msx = float(odds_items[1].replace(',', '.')) if odds_items[1] != '-' else 0.0
                                ms2 = float(odds_items[2].replace(',', '.')) if odds_items[2] != '-' else 0.0
                                found_ms = True
                                break
                            except Exception:
                                pass
                                
            if not found_ms:
                continue
                
            parsed_matches.append({
                'match_id': match_id,
                'date': current_date,
                'code': code,
                'time': match_time,
                'home': home_team,
                'away': away_team,
                'ms1': ms1,
                'msx': msx,
                'ms2': ms2,
                'iy_score': iy_score,
                'ms_score': ms_score,
                'iy_goals': iy_goals,
                'iy_1_5_status': iy_1_5_status
            })
            
        return parsed_matches

    def fetch_detailed_odds(self, match_id: str) -> Dict[str, Any]:
        if not match_id:
            return {}
            
        url = f"https://arsiv.mackolik.com/AjaxHandlers/IddaaHandler.aspx?command=morebets&mac={match_id}&type=ByLeague"
        try:
            req = urllib.request.Request(url, headers=self.headers)
            raw_text = urllib.request.urlopen(req, timeout=8).read().decode('utf-8', errors='ignore')
            
            # Clean unquoted keys and Date(...)
            json_text = re.sub(r'([{,])\s*([a-zA-Z0-9_]+)\s*:', r'\1"\2":', raw_text)
            json_text = re.sub(r'\\?/Date\([^)]*\)\\?', '0', json_text)
            
            data = json.loads(json_text)
            event = data.get('Event', {})
            markets = event.get('Markets') or event.get('m') or []
            
            details = {
                'mbs': event.get('mbs') or event.get('MBS', 1),
                'iy_1_5_ust': None,
                'iy_1_5_alt': None,
                'iy_0_5_ust': None,
                'iy_ms_2_1': None,
                'iy_ms_1_x': None,
                'iy_1': None,
                'iy_x': None,
                'iy_2': None,
                'ms_2_5_ust': None,
                'kg_var': None,
                'ev_iki_yari_gol': None,
                'dep_iki_yari_gol': None,
                'ev_0_5_ust': None,
                'dep_0_5_ust': None
            }
            
            for m in markets:
                mtype = m.get('MarketType')
                if isinstance(mtype, dict):
                    mid = mtype.get('Id')
                else:
                    mid = m.get('id')
                    
                mbs = m.get('MBS')
                if mbs and not details['mbs']:
                    details['mbs'] = mbs
                    
                outcomes = m.get('Outcomes')
                if isinstance(outcomes, list):
                    odd_by_no = {o.get('OutcomeNo'): o.get('Odd') for o in outcomes if isinstance(o, dict)}
                    odd_by_name = {str(o.get('OutcomeName')).lower().strip(): o.get('Odd') for o in outcomes if isinstance(o, dict)}
                    
                    def get_odd(no, name_kw=None):
                        v = odd_by_no.get(no)
                        if (v is None or v == 0) and name_kw:
                            for k, val in odd_by_name.items():
                                if name_kw in k:
                                    return val
                        return v if v != 0 else None

                    if mid == 14: # 1. Yarı 1,5 Alt/Üst
                        details['iy_1_5_alt'] = get_odd(1, 'alt')
                        details['iy_1_5_ust'] = get_odd(2, 'üst') or get_odd(2, 'st')
                    elif mid == 209: # 1. Yarı 0,5 Alt/Üst
                        details['iy_0_5_ust'] = get_odd(2, 'üst') or get_odd(2, 'st')
                    elif mid == 5: # İY / MS
                        details['iy_ms_2_1'] = get_odd(7, '2/1')
                        details['iy_ms_1_x'] = get_odd(2, '1/x')
                    elif mid == 7: # 1. Yarı Sonucu
                        details['iy_1'] = get_odd(1, '1')
                        details['iy_x'] = get_odd(2, 'x')
                        details['iy_2'] = get_odd(3, '2')
                    elif mid == 12: # 2,5 Alt/Üst
                        details['ms_2_5_ust'] = get_odd(2, 'üst') or get_odd(2, 'st')
                    elif mid == 38: # Karşılıklı Gol
                        details['kg_var'] = get_odd(1, 'var')
                    elif mid == 295: # Evsahibi İki Yarıda da Gol
                        details['ev_iki_yari_gol'] = get_odd(1, 'atar')
                    elif mid == 296: # Deplasman İki Yarıda da Gol
                        details['dep_iki_yari_gol'] = get_odd(1, 'atar')
                    elif mid == 256: # Deplasman 0,5 Alt/Üst
                        details['dep_0_5_ust'] = get_odd(2, 'üst') or get_odd(2, 'st')
                    elif mid in (20, 255): # Evsahibi Alt/Üst
                        details['ev_0_5_ust'] = get_odd(2, 'üst') or get_odd(2, 'st')
                
                elif isinstance(m.get('o'), str):
                    o_str = m.get('o', '')
                    items = o_str.split('|') if o_str else []
                    if mid == 14 and len(items) >= 2:
                        try:
                            details['iy_1_5_alt'] = float(items[0]) if items[0] and items[0] != '0' else None
                            details['iy_1_5_ust'] = float(items[1]) if items[1] and items[1] != '0' else None
                        except Exception: pass
                    elif mid == 5:
                        for item in items:
                            parts = item.split(':')
                            if len(parts) == 2:
                                o_id, val = parts[0], parts[1]
                                try:
                                    v_float = float(val) if val and val != '0' else None
                                    if o_id == '15': details['iy_ms_2_1'] = v_float
                                    elif o_id == '7': details['iy_ms_1_x'] = v_float
                                except Exception: pass
                    elif mid == 7 and len(items) >= 3:
                        try:
                            details['iy_1'] = float(items[0]) if items[0] and items[0] != '0' else None
                            details['iy_x'] = float(items[1]) if items[1] and items[1] != '0' else None
                            details['iy_2'] = float(items[2]) if items[2] and items[2] != '0' else None
                        except Exception: pass
                    elif mid == 12 and len(items) >= 2:
                        try: details['ms_2_5_ust'] = float(items[1]) if items[1] and items[1] != '0' else None
                        except Exception: pass
                    elif mid == 38 and len(items) >= 2:
                        try: details['kg_var'] = float(items[0]) if items[0] and items[0] != '0' else None
                        except Exception: pass
                    elif mid == 209 and len(items) >= 2:
                        try: details['iy_0_5_ust'] = float(items[1]) if items[1] and items[1] != '0' else None
                        except Exception: pass

            return details
        except Exception:
            return {}

    def apply_suleymando_filter(
        self, 
        matches: List[Dict[str, Any]], 
        min_odds: float = 1.00, 
        max_odds: float = 1.23,
        fetch_details: bool = True
    ) -> List[Dict[str, Any]]:
        return self.apply_contexticardici_filter(matches, min_odds, max_odds, fetch_details)

    def apply_contexticardici_filter(
        self, 
        matches: List[Dict[str, Any]], 
        min_odds: float = 1.00, 
        max_odds: float = 1.23,
        fetch_details: bool = True
    ) -> List[Dict[str, Any]]:
        filtered = []
        for m in matches:
            ms1, ms2 = m['ms1'], m['ms2']
            fav_side = None
            fav_odds = 0.0
            
            if 0 < ms1 <= max_odds and ms1 >= min_odds:
                fav_side = "EV SAHİBİ"
                fav_odds = ms1
            elif 0 < ms2 <= max_odds and ms2 >= min_odds:
                fav_side = "DEPLASMAN"
                fav_odds = ms2
                
            if fav_side:
                m_copy = dict(m)
                m_copy['fav_side'] = fav_side
                m_copy['fav_odds'] = fav_odds
                m_copy['primary_prediction'] = "İY 1,5 ÜST"
                m_copy['extra_prediction'] = "FAVORİ İY 1 GOL ATAR"
                filtered.append(m_copy)
                
        if fetch_details and filtered:
            with ThreadPoolExecutor(max_workers=10) as executor:
                future_to_match = {
                    executor.submit(self.fetch_detailed_odds, m['match_id']): m 
                    for m in filtered if m.get('match_id')
                }
                for future in as_completed(future_to_match):
                    match_item = future_to_match[future]
                    try:
                        det = future.result()
                        match_item.update(det)
                    except Exception:
                        pass
                        
        return filtered

    def scan_bulletin(
        self, 
        min_odds: float = 1.00, 
        max_odds: float = 1.23,
        fetch_details: bool = True
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        html = self.fetch_bulletin_html()
        all_matches = self.parse_matches(html)
        filtered_matches = self.apply_suleymando_filter(all_matches, min_odds, max_odds, fetch_details)
        return all_matches, filtered_matches
