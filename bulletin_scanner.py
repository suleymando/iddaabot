import urllib.request
import re
import json
import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Tuple, Optional

MACKOLIK_URL = 'https://arsiv.mackolik.com/Iddaa-Programi'

class BulletinScanner:
    """
    Mackolik İddaa Bülteni Tarayıcı, Detaylı Oran Çekici ve Suleymando Filtre Motoru
    """
    def __init__(self, url: str = MACKOLIK_URL):
        self.url = url
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7',
            'Referer': 'https://arsiv.mackolik.com/Iddaa-Programi'
        }

    def fetch_bulletin_html(self) -> str:
        req = urllib.request.Request(self.url, headers=self.headers)
        raw_bytes = urllib.request.urlopen(req, timeout=15).read()
        try:
            return raw_bytes.decode('windows-1254', errors='ignore')
        except Exception:
            return raw_bytes.decode('utf-8', errors='ignore')

    def parse_matches(self, html: str) -> List[Dict[str, Any]]:
        rows = re.findall(r'<tr[^>]*>(?:(?!</tr>).)*?popMatch(?:(?!</tr>).)*?</tr>', html, re.DOTALL | re.IGNORECASE)
        
        parsed_matches = []
        seen_keys = set()
        
        for r in rows:
            # Match ID (for getMoreBets AJAX)
            mac_id_m = re.search(r'popMatch\((\d+)', r)
            match_id = mac_id_m.group(1) if mac_id_m else ""
            
            # Takım İsimleri
            teams = re.findall(r'popTeam\(\d+\)[^>]*>\s*([^<]+)', r)
            if len(teams) < 2:
                continue
            home_team = teams[0].replace('&nbsp;', ' ').strip()
            away_team = teams[1].replace('&nbsp;', ' ').strip()
            
            # Maç Saati
            time_m = re.search(r'<td[^>]*align=["\']center["\'][^>]*>(\d{2}:\d{2})</td>', r)
            match_time = time_m.group(1) if time_m else "--:--"
            
            # Maç Kodu
            code_m = re.search(r'<td[^>]*align=["\']center["\'][^>]*>(\d{4,6})</td>', r)
            code = code_m.group(1) if code_m else "------"
            
            match_key = f"{code}_{home_team}_{away_team}"
            if match_key in seen_keys:
                continue
            seen_keys.add(match_key)
            
            # Oranlar (MS1, MSX, MS2)
            dialogs = re.findall(r'openOddsDialog\((.*?)\)', r)
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
                'code': code,
                'time': match_time,
                'home': home_team,
                'away': away_team,
                'ms1': ms1,
                'msx': msx,
                'ms2': ms2
            })
            
        return parsed_matches

    def fetch_detailed_odds(self, match_id: str) -> Dict[str, Any]:
        """
        Mackolik IddaaHandler AJAX servisine istek atarak maçın tüm detaylı oranlarını (MBS, İY 1.5 ÜST, İY Favori Gol vb.) çeker.
        """
        if not match_id:
            return {}
            
        ajax_url = f"https://arsiv.mackolik.com/AjaxHandlers/IddaaHandler.aspx?command=morebets&mac={match_id}&type=ByLeague"
        try:
            req = urllib.request.Request(ajax_url, headers=self.headers)
            raw_bytes = urllib.request.urlopen(req, timeout=5).read()
            text = raw_bytes.decode('windows-1254', errors='ignore')
            
            clean_json = re.sub(r'([{,])\s*([a-zA-Z0-9_]+)\s*:', r'\1"\2":', text)
            clean_json = re.sub(r'"\\/Date\([^)]+\)\\/"', '""', clean_json)
            data = json.loads(clean_json)
            
            event = data.get('Event', {})
            markets = event.get('Markets', [])
            
            detailed = {
                'mbs': 1,
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
                'dep_iki_yari_gol': None
            }
            
            for m in markets:
                mtype = m.get('MarketType', {})
                mid = mtype.get('Id')
                mname = mtype.get('Name') or m.get('Name') or ""
                
                mbs_val = m.get('MBS')
                if mbs_val and mbs_val > detailed['mbs']:
                    detailed['mbs'] = mbs_val
                    
                outcomes = m.get('Outcomes', [])
                outs = {}
                alt_odd = None
                ust_odd = None
                
                for o in outcomes:
                    oname = str(o.get('OutcomeName') or '')
                    odd = o.get('Odd')
                    outs[oname] = odd
                    if 'st' in oname.lower() or o.get('OutcomeNo') == 2:
                        ust_odd = odd
                    elif 'lt' in oname.lower() or o.get('OutcomeNo') == 1:
                        alt_odd = odd
                
                # Market ID 14: 1. Yarı 1,5 Alt/Üst
                if mid == 14 or '1. Yarı 1,5' in mname:
                    detailed['iy_1_5_ust'] = ust_odd
                    detailed['iy_1_5_alt'] = alt_odd
                    
                # Market ID 209: 1. Yarı 0,5 Alt/Üst
                elif mid == 209 or '1. Yarı 0,5' in mname:
                    detailed['iy_0_5_ust'] = ust_odd
                    
                # Market ID 5: İlk Yarı/Maç Sonucu
                elif mid == 5 or 'İlk Yarı/Maç Sonucu' in mname:
                    detailed['iy_ms_2_1'] = outs.get('2/1')
                    detailed['iy_ms_1_x'] = outs.get('1/X')
                    
                # Market ID 7: 1. Yarı Sonucu
                elif mid == 7 or '1. Yarı Sonucu' in mname:
                    detailed['iy_1'] = outs.get('1')
                    detailed['iy_x'] = outs.get('X')
                    detailed['iy_2'] = outs.get('2')
                    
                # Market ID 12: 2,5 Alt/Üst
                elif mid == 12 or '2,5 Alt/Üst' in mname:
                    detailed['ms_2_5_ust'] = ust_odd
                    
                # Market ID 38: Karşılıklı Gol
                elif mid == 38 or 'Karşılıklı Gol' in mname:
                    detailed['kg_var'] = outs.get('Var')
                    
                # Evsahibi İki Yarıda da Gol
                elif mid == 295 or 'Evsahibi İki Yarıda da Gol' in mname:
                    detailed['ev_iki_yari_gol'] = outs.get('Atar')
                    
                # Deplasman İki Yarıda da Gol
                elif mid == 296 or 'Deplasman İki Yarıda da Gol' in mname:
                    detailed['dep_iki_yari_gol'] = outs.get('Atar')
                    
            return detailed
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
            o1, ox, o2 = m['ms1'], m['msx'], m['ms2']
            
            fav_home = (min_odds <= o1 <= max_odds)
            fav_away = (min_odds <= o2 <= max_odds)
            
            if fav_home or fav_away:
                item = dict(m)
                fav_side = 'EV SAHİBİ' if fav_home else 'DEPLASMAN'
                fav_team = m['home'] if fav_home else m['away']
                fav_odds = o1 if fav_home else o2
                
                item['fav_side'] = fav_side
                item['fav_team'] = fav_team
                item['fav_odds'] = fav_odds
                item['primary_prediction'] = 'İY 1,5 ÜST'
                item['extra_prediction'] = '2/1 (İY 2 / MS 1)' if fav_home else '1/X (İY 1 / MS X)'
                
                filtered.append(item)
                
        # Detaylı oranları paralel (ThreadPoolExecutor) olarak saniyeler içinde çekelim
        if fetch_details and filtered:
            with ThreadPoolExecutor(max_workers=12) as executor:
                future_to_match = {
                    executor.submit(self.fetch_detailed_odds, m['match_id']): m 
                    for m in filtered
                }
                for future in as_completed(future_to_match):
                    match_item = future_to_match[future]
                    try:
                        det = future.result()
                        match_item.update(det)
                    except Exception:
                        pass
                        
        return filtered

    def scan_bulletin(self, min_odds: float = 1.00, max_odds: float = 1.23, fetch_details: bool = True) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        html = self.fetch_bulletin_html()
        all_matches = self.parse_matches(html)
        filtered_matches = self.apply_contexticardici_filter(all_matches, min_odds, max_odds, fetch_details)
        return all_matches, filtered_matches

if __name__ == '__main__':
    scanner = BulletinScanner()
    print("Bülten ve detaylı oranlar taranıyor...")
    all_m, filt_m = scanner.scan_bulletin(fetch_details=True)
    print(f"Toplam Taranan Maç: {len(all_m)}")
    print(f"Filtreye Uyan Maç Sayısı: {len(filt_m)}")
    for f in filt_m[:3]:
        print("\nMAÇ DETAYI:", f)
