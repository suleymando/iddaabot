import streamlit as st
import pandas as pd
import datetime
import threading
import time
from bulletin_scanner import BulletinScanner
from telegram_notifier import (
    send_telegram_message, 
    send_telegram_document, 
    generate_csv_bulletin, 
    format_telegram_2h_bulletin,
    format_telegram_winrate_report
)

# Page Configuration
st.set_page_config(
    page_title="Suleymando - İddaa Bülten Oran Filtresi",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

DEFAULT_BOT_TOKEN = "8940991344:AAFA8qLKgNDdsp__3KThdtnMSXhh2VrrcI4"
DEFAULT_CHAT_ID = "-5202583497"

# Background Scheduler Thread for Streamlit Cloud 24/7 Automation
def run_cloud_telegram_scan(mode="every_2h"):
    scanner = BulletinScanner()
    today_date_str = datetime.datetime.now().strftime("%d.%m.%Y")
    try:
        all_m, filt_m = scanner.scan_bulletin(min_odds=1.00, max_odds=1.23, fetch_details=True)
        
        if mode == "night_2345":
            today_matches = [m for m in filt_m if m.get('date') == today_date_str]
            if not today_matches:
                today_matches = filt_m
            report_text = format_telegram_winrate_report(today_matches, today_date_str)
            csv_bytes = generate_csv_bulletin(filt_m, f"Suleymando_GunSonu_{today_date_str}")
            
            send_telegram_message(DEFAULT_BOT_TOKEN, DEFAULT_CHAT_ID, report_text)
            filename = f"suleymando_bulten_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.csv"
            send_telegram_document(DEFAULT_BOT_TOKEN, DEFAULT_CHAT_ID, csv_bytes, filename, f"📊 Suleymando {today_date_str} Bülten (.csv)")
        else:
            now_minutes = datetime.datetime.now().hour * 60 + datetime.datetime.now().minute
            max_target_minutes = now_minutes + (2 * 60)
            
            upcoming = [
                m for m in filt_m 
                if m.get('date') == today_date_str and now_minutes <= parse_time_minutes(m['time']) <= max_target_minutes
            ]
            msg_text = format_telegram_2h_bulletin(upcoming)
            send_telegram_message(DEFAULT_BOT_TOKEN, DEFAULT_CHAT_ID, msg_text)
    except Exception as e:
        print("Cloud Telegram Scan Error:", e)

def init_cloud_scheduler():
    if 'bg_scheduler_started' not in st.session_state:
        st.session_state['bg_scheduler_started'] = True
        
        def scheduler_loop():
            last_night_date = None
            last_2h_time = time.time()
            while True:
                now = datetime.datetime.now()
                if now.hour == 23 and now.minute == 45 and last_night_date != now.date():
                    run_cloud_telegram_scan(mode="night_2345")
                    last_night_date = now.date()
                if time.time() - last_2h_time >= 7200:
                    run_cloud_telegram_scan(mode="every_2h")
                    last_2h_time = time.time()
                time.sleep(30)
                
        t = threading.Thread(target=scheduler_loop, daemon=True)
        t.start()

init_cloud_scheduler()

# Ultra-Premium CSS Styling for Unified Glassmorphism UI
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', sans-serif;
}

.stApp {
    background: radial-gradient(circle at top right, #0f172a 0%, #020617 100%);
}

/* Header Box */
.header-box {
    background: linear-gradient(135deg, rgba(30, 27, 75, 0.85) 0%, rgba(15, 23, 42, 0.95) 100%);
    border: 1px solid rgba(99, 102, 241, 0.35);
    border-radius: 22px;
    padding: 26px 32px;
    margin-bottom: 24px;
    backdrop-filter: blur(16px);
    box-shadow: 0 20px 40px -15px rgba(0, 0, 0, 0.6);
}
.header-title {
    background: linear-gradient(90deg, #a5b4fc 0%, #38bdf8 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-size: 30px;
    font-weight: 800;
    letter-spacing: -0.5px;
    margin-bottom: 8px;
}
.header-subtitle {
    color: #94a3b8;
    font-size: 15px;
    line-height: 1.5;
}

/* Rule Card */
.rule-card {
    background: rgba(15, 23, 42, 0.7);
    border: 1px solid rgba(16, 185, 129, 0.35);
    border-radius: 18px;
    padding: 20px 26px;
    margin-bottom: 28px;
    backdrop-filter: blur(12px);
}
.rule-title {
    color: #34d399;
    font-weight: 800;
    font-size: 16px;
    margin-bottom: 8px;
}
.rule-desc {
    color: #cbd5e1;
    font-size: 14px;
    line-height: 1.6;
}

/* Metric Cards */
.metric-card {
    background: rgba(15, 23, 42, 0.75);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 20px;
    padding: 20px;
    text-align: center;
    backdrop-filter: blur(12px);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
.metric-card:hover {
    transform: translateY(-4px);
    border-color: rgba(99, 102, 241, 0.4);
    box-shadow: 0 12px 30px -10px rgba(99, 102, 241, 0.25);
}
.metric-val {
    font-size: 34px;
    font-weight: 800;
    letter-spacing: -1px;
}
.metric-lbl {
    font-size: 12px;
    color: #64748b;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    margin-top: 6px;
}

/* Unified Match Card */
.nextgen-card {
    background: linear-gradient(145deg, rgba(30, 41, 59, 0.7) 0%, rgba(15, 23, 42, 0.9) 100%);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 22px;
    padding: 22px;
    margin-bottom: 22px;
    position: relative;
    backdrop-filter: blur(16px);
    box-shadow: 0 12px 30px -8px rgba(0, 0, 0, 0.45);
    transition: all 0.3s ease;
}
.nextgen-card:hover {
    border-color: rgba(16, 185, 129, 0.5);
    box-shadow: 0 20px 40px -10px rgba(16, 185, 129, 0.3);
}

/* Top Pill Bar */
.card-top-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
}
.pill-mbs {
    background: linear-gradient(90deg, #ef4444 0%, #dc2626 100%);
    color: #ffffff;
    padding: 4px 12px;
    border-radius: 20px;
    font-weight: 800;
    font-size: 12px;
    box-shadow: 0 4px 12px rgba(239, 68, 68, 0.35);
}
.pill-code {
    background: rgba(99, 102, 241, 0.2);
    color: #a5b4fc;
    border: 1px solid rgba(99, 102, 241, 0.4);
    padding: 4px 12px;
    border-radius: 20px;
    font-weight: 700;
    font-size: 12px;
}
.pill-time {
    background: rgba(245, 158, 11, 0.2);
    color: #fbbf24;
    border: 1px solid rgba(245, 158, 11, 0.4);
    padding: 4px 12px;
    border-radius: 20px;
    font-weight: 700;
    font-size: 13px;
}
.pill-status-won {
    background: rgba(16, 185, 129, 0.25);
    color: #34d399;
    border: 1px solid #10b981;
    padding: 4px 12px;
    border-radius: 20px;
    font-weight: 800;
    font-size: 12px;
}
.pill-status-lost {
    background: rgba(239, 68, 68, 0.25);
    color: #f87171;
    border: 1px solid #ef4444;
    padding: 4px 12px;
    border-radius: 20px;
    font-weight: 800;
    font-size: 12px;
}

/* Teams Section */
.teams-flex {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    margin-bottom: 18px;
}
.team-card {
    flex: 1;
    background: rgba(15, 23, 42, 0.6);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 14px;
    padding: 12px 14px;
    text-align: center;
}
.team-card.fav {
    background: rgba(16, 185, 129, 0.16);
    border-color: rgba(16, 185, 129, 0.5);
}
.team-name {
    font-size: 16px;
    font-weight: 700;
    color: #f1f5f9;
}
.team-card.fav .team-name {
    color: #34d399;
}
.vs-circle {
    font-size: 12px;
    font-weight: 800;
    color: #64748b;
    background: #0f172a;
    width: 32px;
    height: 32px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    border: 1px solid #1e293b;
    flex-shrink: 0;
}

/* Odds Row */
.odds-row {
    display: flex;
    gap: 8px;
    margin-bottom: 16px;
}
.odd-box {
    flex: 1;
    background: rgba(15, 23, 42, 0.85);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 12px;
    padding: 8px;
    text-align: center;
}
.odd-box.active {
    background: rgba(16, 185, 129, 0.25);
    border-color: #10b981;
}
.odd-lbl {
    font-size: 11px;
    color: #64748b;
    font-weight: 600;
}
.odd-box.active .odd-lbl {
    color: #6ee7b7;
}
.odd-val {
    font-size: 16px;
    font-weight: 800;
    color: #f8fafc;
}
.odd-box.active .odd-val {
    color: #34d399;
}

/* Detailed Odds Highlights Bar */
.detail-highlights {
    background: rgba(15, 23, 42, 0.7);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 14px;
    padding: 10px 14px;
    margin-bottom: 16px;
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 8px;
    text-align: center;
}
.dh-item {
    border-right: 1px solid rgba(255, 255, 255, 0.08);
    padding-right: 6px;
}
.dh-item:last-child {
    border-right: none;
    padding-right: 0;
}
.dh-lbl {
    font-size: 10px;
    color: #94a3b8;
    font-weight: 700;
    text-transform: uppercase;
    margin-bottom: 2px;
}
.dh-val {
    font-size: 15px;
    font-weight: 800;
    color: #38bdf8;
}

/* Unified Prediction Banner with Contoured Odds */
.pred-banner {
    background: linear-gradient(90deg, rgba(16, 185, 129, 0.2) 0%, rgba(245, 158, 11, 0.2) 100%);
    border: 1px solid rgba(16, 185, 129, 0.4);
    border-radius: 16px;
    padding: 12px 18px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 12px;
}
.pred-group {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-wrap: wrap;
}
.pred-tag-primary {
    background: #10b981;
    color: #022c22;
    font-size: 10px;
    font-weight: 800;
    padding: 4px 8px;
    border-radius: 6px;
}
.pred-tag-extra {
    background: #f59e0b;
    color: #451a03;
    font-size: 10px;
    font-weight: 800;
    padding: 4px 8px;
    border-radius: 6px;
}
.pred-txt {
    font-size: 14px;
    font-weight: 800;
    color: #ffffff;
}
.pred-txt-extra {
    font-size: 14px;
    font-weight: 800;
    color: #fbbf24;
}

/* Contoured Odds Pill */
.odd-contour-green {
    background: rgba(15, 23, 42, 0.95);
    border: 1.5px solid #10b981;
    color: #34d399;
    padding: 3px 10px;
    border-radius: 10px;
    font-weight: 800;
    font-size: 14px;
    box-shadow: 0 0 12px rgba(16, 185, 129, 0.35);
    display: inline-block;
    letter-spacing: 0.3px;
}
.odd-contour-gold {
    background: rgba(15, 23, 42, 0.95);
    border: 1.5px solid #f59e0b;
    color: #fbbf24;
    padding: 3px 10px;
    border-radius: 10px;
    font-weight: 800;
    font-size: 14px;
    box-shadow: 0 0 12px rgba(245, 158, 11, 0.35);
    display: inline-block;
    letter-spacing: 0.3px;
}

/* Streamlit Expander Dark Glass Styling Fix */
div[data-testid="stExpander"] {
    background: #0f172a !important;
    border: 1px solid rgba(255, 255, 255, 0.15) !important;
    border-radius: 16px !important;
    margin-top: 10px !important;
}

div[data-testid="stExpander"] summary {
    background: #1e293b !important;
    color: #38bdf8 !important;
    font-weight: 700 !important;
    font-size: 14px !important;
    border-radius: 14px !important;
    padding: 12px 16px !important;
}

div[data-testid="stExpander"] summary:hover {
    color: #60a5fa !important;
    background: #334155 !important;
}

/* High Contrast Expander Card Grid */
.expander-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 12px;
    padding: 12px 0 4px 0;
}
.exp-card {
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 12px;
    padding: 12px 14px;
}
.exp-title {
    color: #38bdf8;
    font-size: 12px;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 8px;
    border-bottom: 1px solid #334155;
    padding-bottom: 4px;
}
.exp-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 13px;
    color: #cbd5e1;
    margin-bottom: 6px;
}
.exp-val {
    color: #34d399;
    font-weight: 800;
}
</style>
""", unsafe_allow_html=True)

# Initialize Session State
if 'scanner' not in st.session_state:
    st.session_state.scanner = BulletinScanner()

if 'all_matches' not in st.session_state:
    st.session_state.all_matches = []
    st.session_state.filtered_matches = []
    st.session_state.last_updated = None

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

def load_data(min_o: float, max_o: float):
    with st.spinner("⚡ Mackolik 1300+ Maçlık Bülten ve Detaylı Oranlar taranıyor..."):
        try:
            all_m, filt_m = st.session_state.scanner.scan_bulletin(min_o, max_o, fetch_details=True)
            st.session_state.all_matches = all_m
            st.session_state.filtered_matches = filt_m
            st.session_state.last_updated = datetime.datetime.now().strftime("%H:%M:%S")
        except Exception as e:
            st.error(f"Bülten taranırken hata oluştu: {str(e)}")

# Sidebar Controls
st.sidebar.markdown("## ⚙️ Tarama & Filtre Ayarları")

min_odds_val = st.sidebar.number_input("Minimum Oran", min_value=1.00, max_value=2.00, value=1.00, step=0.01)
max_odds_val = st.sidebar.number_input("Maksimum Oran", min_value=1.00, max_value=3.00, value=1.23, step=0.01)

if st.sidebar.button("🔄 Bülteni Canlı Yenile", use_container_width=True, type="primary"):
    load_data(min_odds_val, max_odds_val)

if not st.session_state.all_matches:
    load_data(min_odds_val, max_odds_val)

st.sidebar.markdown("---")
st.sidebar.markdown("### 🕒 Sıralama Ayarı")
sort_order = st.sidebar.radio(
    "Maç Sıralaması",
    ["⏰ Maç Saatine Göre (En Yakın -> En Uzak)", "🔢 Koda Göre", "📊 Orana Göre"],
    index=0
)

st.sidebar.markdown("---")
st.sidebar.markdown("### 🔍 Detaylı Filtreler")

fav_side_filter = st.sidebar.selectbox("Favori Taraf Seçimi", ["Tümü", "Ev Sahibi Favori", "Deplasman Favori"])
search_query = st.sidebar.text_input("Takım veya Kod Ara", "").strip().lower()

# Header Section
st.markdown("""<div class="header-box">
    <div class="header-title">⚡ Suleymando İY 1,5 ÜST Bülten Tarama Paneli</div>
    <div class="header-subtitle">Mackolik bülteninin tamamını tarar; MBS, İY 1.5 Üst ve Favori İY 1 Gol oranlarını çekerek başlama saatine göre kronolojik sıralar.</div>
</div>""", unsafe_allow_html=True)

# Rule Explanation Banner
st.markdown("""<div class="rule-card">
    <div class="rule-title">📌 Formül Kuralları (Suleymando %86 Başarı Formülü)</div>
    <div class="rule-desc">
        • Favori takımın oranı <b>1.00 ile 1.23</b> arasında ise bu maça <b>İY 1,5 ÜST</b> denenir.<br>
        • Tüm maçlarda <b>Ekstra Tahmin</b> olarak <b>FAVORİ İLK YARI 1 GOL ATAR</b> seçeneği önerilir.
    </div>
</div>""", unsafe_allow_html=True)

# Filter Data according to Sidebar Inputs
curr_filtered = list(st.session_state.filtered_matches)

if fav_side_filter == "Ev Sahibi Favori":
    curr_filtered = [m for m in curr_filtered if m['fav_side'] == 'EV SAHİBİ']
elif fav_side_filter == "Deplasman Favori":
    curr_filtered = [m for m in curr_filtered if m['fav_side'] == 'DEPLASMAN']

if search_query:
    curr_filtered = [
        m for m in curr_filtered 
        if search_query in m['home'].lower() or search_query in m['away'].lower() or search_query in m['code'].lower()
    ]

# Apply Sorting
if "Maç Saatine Göre" in sort_order:
    curr_filtered.sort(key=lambda m: (m.get('date', ''), parse_time_minutes(m['time'])))
elif "Koda Göre" in sort_order:
    curr_filtered.sort(key=lambda m: m['code'])
elif "Orana Göre" in sort_order:
    curr_filtered.sort(key=lambda m: m['fav_odds'])

# Telegram Bot Integration inside Sidebar
st.sidebar.markdown("---")
st.sidebar.markdown("### 📱 Telegram Bot Entegrasyonu")

tg_token = st.sidebar.text_input("Telegram Bot Token", value=DEFAULT_BOT_TOKEN, type="password")
tg_chat_id = st.sidebar.text_input("Telegram Chat ID", value=DEFAULT_CHAT_ID)

if st.sidebar.button("📥 CSV Listesini Telegram'a Gönder", use_container_width=True, type="primary"):
    if not tg_token or not tg_chat_id:
        st.sidebar.error("Lütfen Bot Token ve Chat ID girin.")
    else:
        with st.spinner("CSV dosyası oluşturulup Telegram grubuna gönderiliyor..."):
            csv_bytes = generate_csv_bulletin(curr_filtered, "Suleymando Bülten")
            caption = (
                f"👑 <b>SULEYMANDO BÜLTEN CSV DOSYASI</b>\n"
                f"📊 Eşleşen Maç Sayısı: <b>{len(curr_filtered)}</b>"
            )
            filename = f"suleymando_bulten_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.csv"
            ok = send_telegram_document(tg_token, tg_chat_id, csv_bytes, filename, caption)
            if ok:
                st.sidebar.success(f"✅ CSV dosyası ({len(curr_filtered)} maç) Telegram grubunuza gönderildi!")
            else:
                st.sidebar.error("Telegram mesajı gönderilemedi.")

if st.session_state.last_updated:
    st.sidebar.caption(f"🕒 Son Güncelleme: **{st.session_state.last_updated}**")

home_fav_count = sum(1 for m in curr_filtered if m['fav_side'] == 'EV SAHİBİ')
away_fav_count = sum(1 for m in curr_filtered if m['fav_side'] == 'DEPLASMAN')

# Metrics Display
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(f"""<div class="metric-card">
        <div class="metric-val" style="color: #a5b4fc;">{len(st.session_state.all_matches)}</div>
        <div class="metric-lbl">Taranan Toplam Maç</div>
    </div>""", unsafe_allow_html=True)

with col2:
    st.markdown(f"""<div class="metric-card">
        <div class="metric-val" style="color: #34d399;">{len(curr_filtered)}</div>
        <div class="metric-lbl">Formüle Uyan Maç</div>
    </div>""", unsafe_allow_html=True)

with col3:
    st.markdown(f"""<div class="metric-card">
        <div class="metric-val" style="color: #60a5fa;">{home_fav_count}</div>
        <div class="metric-lbl">Ev Sahibi Favori</div>
    </div>""", unsafe_allow_html=True)

with col4:
    st.markdown(f"""<div class="metric-card">
        <div class="metric-val" style="color: #fbbf24;">{away_fav_count}</div>
        <div class="metric-lbl">Deplasman Favori</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Main View Tabs
tab_cards_main, tab_table, tab_export = st.tabs(["🎴 Tarih Sekmeli Kartlar", "📊 Tablo Görünümü", "📋 Kuponu Kopyala & CSV İndir"])

with tab_cards_main:
    if not curr_filtered:
        st.info("Seçilen filtrelere uyan maç bulunamadı.")
    else:
        # Extract unique sorted dates for side-by-side tabs
        available_dates = sorted(list(dict.fromkeys(m['date'] for m in curr_filtered if m.get('date'))))
        date_tab_labels = ["🌐 Tüm Tarihler"] + [f"📅 {d}" for d in available_dates]
        date_tabs = st.tabs(date_tab_labels)
        
        for t_idx, d_tab in enumerate(date_tabs):
            with d_tab:
                if t_idx == 0:
                    tab_matches = curr_filtered
                else:
                    target_d = available_dates[t_idx - 1]
                    tab_matches = [m for m in curr_filtered if m.get('date') == target_d]
                    
                if not tab_matches:
                    st.info("Bu tarihte formüle uyan maç bulunamadı.")
                else:
                    for i in range(0, len(tab_matches), 2):
                        cols = st.columns(2)
                        for idx, col in enumerate(cols):
                            if i + idx < len(tab_matches):
                                m = tab_matches[i + idx]
                                
                                is_home_fav = (m['fav_side'] == 'EV SAHİBİ')
                                is_away_fav = (m['fav_side'] == 'DEPLASMAN')
                                
                                home_class = "fav" if is_home_fav else ""
                                away_class = "fav" if is_away_fav else ""
                                
                                mbs_val = m.get('mbs', 1)
                                iy_1_5_u_odd = m.get('iy_1_5_ust')
                                iy_1_5_u_str = f"{iy_1_5_u_odd:.2f}" if iy_1_5_u_odd else "N/A"
                                
                                if is_home_fav:
                                    fav_gol_odd = m.get('ev_iki_yari_gol') or m.get('iy_0_5_ust') or m.get('ev_0_5_ust')
                                else:
                                    fav_gol_odd = m.get('dep_iki_yari_gol') or m.get('iy_0_5_ust') or m.get('dep_0_5_ust')
                                    
                                fav_gol_str = f"{fav_gol_odd:.2f}" if fav_gol_odd else "N/A"
                                
                                status_val = m.get('iy_1_5_status', 'OYNANMADI')
                                if status_val == 'TUTTU':
                                    status_badge = f'<span class="pill-status-won">✅ İY {m.get("iy_score","")} (TUTTU)</span>'
                                elif status_val == 'YATTI':
                                    status_badge = f'<span class="pill-status-lost">❌ İY {m.get("iy_score","")} (YATTI)</span>'
                                else:
                                    status_badge = f'<span class="pill-time">⏰ SAAT: {m["time"]}</span>'
                                
                                card_html = f"""<div class="nextgen-card">
<div class="card-top-bar">
<div>
<span class="pill-mbs">🎯 MBS: {mbs_val}</span>
<span class="pill-code">📌 KOD: {m['code']}</span>
<span style="color:#94a3b8; font-size:12px; font-weight:700; margin-left:6px;">📅 {m.get('date','')}</span>
</div>
{status_badge}
</div>
<div class="teams-flex">
<div class="team-card {home_class}">
<div class="team-name">{"👑 " if is_home_fav else ""}{m['home']}</div>
</div>
<div class="vs-circle">VS</div>
<div class="team-card {away_class}">
<div class="team-name">{"👑 " if is_away_fav else ""}{m['away']}</div>
</div>
</div>
<div class="odds-row">
<div class="odd-box {"active" if is_home_fav else ""}">
<div class="odd-lbl">MS 1</div>
<div class="odd-val">{m['ms1']:.2f}</div>
</div>
<div class="odd-box">
<div class="odd-lbl">MS X</div>
<div class="odd-val">{m['msx']:.2f}</div>
</div>
<div class="odd-box {"active" if is_away_fav else ""}">
<div class="odd-lbl">MS 2</div>
<div class="odd-val">{m['ms2']:.2f}</div>
</div>
</div>
<div class="detail-highlights">
<div class="dh-item">
<div class="dh-lbl">🔥 İY 1.5 ÜST ORANI</div>
<div class="dh-val" style="color: #34d399;">{iy_1_5_u_str}</div>
</div>
<div class="dh-item">
<div class="dh-lbl">⚽ FAVORİ İY 1 GOL ORANI</div>
<div class="dh-val" style="color: #38bdf8;">{fav_gol_str}</div>
</div>
</div>
<div class="pred-banner">
<div class="pred-group">
<span class="pred-tag-primary">ANA TAHMİN</span>
<span class="pred-txt">🔥 İY 1.5 ÜST</span>
<span class="odd-contour-green">{iy_1_5_u_str}</span>
</div>
<div class="pred-group">
<span class="pred-tag-extra">EKSTRA</span>
<span class="pred-txt-extra">⚽ FAVORİ İY 1 GOL ATAR</span>
<span class="odd-contour-gold">{fav_gol_str}</span>
</div>
</div>
</div>"""
                                col.markdown(card_html, unsafe_allow_html=True)
                                
                                with col.expander(f"🔍 [{m['code']}] {m['home']} - {m['away']} Tüm İddaa Oranları"):
                                    exp_html = f"""<div class="expander-grid">
<div class="exp-card">
<div class="exp-title">1. YARI SONUCU</div>
<div class="exp-row"><span>İY 1:</span> <strong class="exp-val">{m.get('iy_1') or 'N/A'}</strong></div>
<div class="exp-row"><span>İY X:</span> <strong class="exp-val">{m.get('iy_x') or 'N/A'}</strong></div>
<div class="exp-row"><span>İY 2:</span> <strong class="exp-val">{m.get('iy_2') or 'N/A'}</strong></div>
</div>
<div class="exp-card">
<div class="exp-title">GOL ORANLARI</div>
<div class="exp-row"><span>2,5 Gol Üst:</span> <strong class="exp-val">{m.get('ms_2_5_ust') or 'N/A'}</strong></div>
<div class="exp-row"><span>KG Var:</span> <strong class="exp-val">{m.get('kg_var') or 'N/A'}</strong></div>
</div>
<div class="exp-card">
<div class="exp-title">İKİ YARIDA GOL</div>
<div class="exp-row"><span>Ev İki Yarı Gol:</span> <strong class="exp-val">{m.get('ev_iki_yari_gol') or 'N/A'}</strong></div>
<div class="exp-row"><span>Dep İki Yarı Gol:</span> <strong class="exp-val">{m.get('dep_iki_yari_gol') or 'N/A'}</strong></div>
</div>
</div>"""
                                    st.markdown(exp_html, unsafe_allow_html=True)

with tab_table:
    if curr_filtered:
        df = pd.DataFrame(curr_filtered)
        cols_order = ['date', 'time', 'code', 'mbs', 'home', 'away', 'ms1', 'msx', 'ms2', 'iy_1_5_ust', 'fav_side', 'fav_odds', 'primary_prediction', 'extra_prediction', 'iy_score', 'iy_1_5_status']
        df_display = df[[c for c in cols_order if c in df.columns]]
        df_display.columns = ['Tarih', 'Saat', 'Kod', 'MBS', 'Ev Sahibi', 'Deplasman', 'MS 1', 'MS X', 'MS 2', 'İY 1.5 Üst Oran', 'Favori Taraf', 'Favori Oran', 'Ana Tahmin', 'Ekstra Tahmin', 'İY Skor', 'İY 1.5 Durum']
        
        st.dataframe(
            df_display,
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("Tabloda gösterilecek maç yok.")

with tab_export:
    if curr_filtered:
        st.markdown("### 📋 Formüle Uyan Maç Listesi & Kupon Taslağı")
        
        coupon_lines = [
            f"⚡ SULEYMANDO FİLTRELEME LİSTESİ ({len(curr_filtered)} Maç)",
            f"📅 Tarih: {datetime.datetime.now().strftime('%d.%m.%Y %H:%M')}",
            "=" * 60
        ]
        for idx, m in enumerate(curr_filtered, 1):
            iy_ust_str = f"{m.get('iy_1_5_ust'):.2f}" if m.get('iy_1_5_ust') else "N/A"
            status_tag = f" -> [{m.get('iy_1_5_status')}]" if m.get('iy_1_5_status') != 'OYNANMADI' else ""
            coupon_lines.append(
                f"{idx}. 📅 {m.get('date','')} ⏰ {m['time']} | [MBS: {m.get('mbs',1)}] [{m['code']}] {m['home']} - {m['away']} "
                f"(Fav: {m['fav_side']} {m['fav_odds']:.2f}) "
                f"-> 🔥 Tahmin: İY 1.5 ÜST (Oran: {iy_ust_str}) | ⚽ Ekstra: FAVORİ İY 1 GOL ATAR{status_tag}"
            )
            
        coupon_text = "\n".join(coupon_lines)
        
        st.text_area("Tek Tıkla Kopyala", coupon_text, height=320)
        
        col_dl1, col_dl2 = st.columns(2)
        with col_dl1:
            csv_data = generate_csv_bulletin(curr_filtered, "Suleymando_Bulten")
            st.download_button(
                label="📥 CSV Olarak İndir (Excel Uyumlu)",
                data=csv_data,
                file_name=f"suleymando_bulten_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
                use_container_width=True
            )
    else:
        st.info("Kupon taslağı oluşturmak için maç bulunamadı.")
