# 👑 Suleymando İddaa Bülten Tarama, Oran Filtreleme & Telegram Otomasyonu

⚡ **Mackolik canlı iddaa bülteninin tamamını saniyeler içinde tarayan**, Contexticardici & Suleymando %86 başarı formülüne uyan maçları başlama saatine göre kronolojik listeleyen ve Telegram/n8n entegrasyonu sağlayan gelişmiş iddaa yazılımı.

---

## 🌟 Öne Çıkan Özellikler

- **⚽ Canlı Bülten Taraması**: Mackolik üzerindeki 350+ maçı saniyeler içinde tarar.
- **👑 Suleymando Oran Filtresi**: Favori takım oranı `1.00 - 1.23` arasındaki maçları süzer.
- **🎯 Detaylı Oran Servisi**: Mackolik AJAX servisi ile `MBS`, `İY 1.5 ÜST`, `İY Favori Gol`, `2/1` ve `1/X` oranlarını çeker.
- **🎴 Modern Glassmorphism Web Dashboard**: Streamlit tabanlı, yüksek kontrastlı, kronolojik sıralamalı arayüz.
- **📱 Telegram Bot & n8n Entegrasyonu**: Gece 23:45'te ertesi günün bültenini, gün içinde 4 saatte bir yaklaşan maçları Telegram'a atar.
- **🚀 Cloud Deploy Ready**: Railway, Render veya Docker üzerinde tek tıkla çalıştırılabilir.

---

## 🚀 Hızlı Başlangıç

### 1. Yerel Arayüzü Çalıştırma (Streamlit Web Dashboard)
```bash
pip install -r requirements.txt
python -m streamlit run app.py
```
👉 Tarayıcıda açın: `http://localhost:8501`

### 2. Canlı REST API & Telegram Servisini Çalıştırma
```bash
python server_api.py
```
👉 REST API Dokümantasyonu: `http://localhost:8000/docs`

---

## ⚙️ n8n & Telegram Kurulumu

Detaylı kurulum adımları ve Telegram Bot bağlantı rehberi için **[SULEYMANDO_KURULUM_REHBERI.md](SULEYMANDO_KURULUM_REHBERI.md)** dökümanını inceleyin.

---

## 🌐 Railway / Render Dağıtımı

Bu depoyu GitHub hesabınıza yükledikten sonra **Railway.app** veya **Render.com** üzerinden **New Project** diyerek repo adresinizi bağlayabilir ve servisinizi 7/24 ücretsiz yayına alabilirsiniz.
