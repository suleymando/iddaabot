# 👑 SULEYMANDO İDDAA OTOMASYON & TELEGRAM BOT ADIM ADIM KURULUM REHBERİ

Bu rehber, **Suleymando İddaa Sistemini** Telegram botuna bağlamanızı, **n8n otomasyonunu** kurmanızı, **Railway/Render** üzerinde 7/24 canlıya almanızı ve **Ngrok** ile arkadaşlarınıza dağıtmanızı adım adım anlatır.

---

## 📱 AŞAMA 1: Telegram Botunu Oluşturma (1 Dakika)

1. Telegram'ı açın ve arama çubuğuna `@BotFather` yazın.
2. BotFather'a `/newbot` yazın.
3. Botunuz için bir isim girin (Örn: `Suleymando Iddaa Bot`).
4. Bot kullanıcı adı girin (Sonu `bot` ile bitmeli, örn: `suleymando_iddaa_bot`).
5. BotFather size bir **HTTP API Token** verecektir (Örn: `7123456789:AAFxxx_xxx_xxx`). **Bu tokenı kopyalayın (`8940991344:AAFA8qLKgNDdsp__3KThdtnMSXhh2VrrcI4`).**
6. Telegram'da yeni bir grup veya kanal açın ve botunuzu gruba ekleyin.
7. Botunuzun gruptaki **CHAT ID**'sini öğrenmek için gruptan bir mesaj yazın ve tarayıcıda şu adrese gidin:
   `https://api.telegram.org/bot<BURAYA_BOT_TOKEN>/getUpdates`
8. Çıkan ekranda `"chat":{"id": -100xxxxxx}` kısmındaki numarayı kopyalayın (**`CHAT_ID`**).

---

## ☁️ AŞAMA 2: Projeyi Railway veya Render'a Canlıya Alma (2 Dakika)

Projeyi internete 7/24 açık hale getirmek için:

### Yöntem A: Railway.app (Önerilen - En Hızlısı)
1. **[Railway.app](https://railway.app)** sitesine ücretsiz üye olun.
2. Proje klasörünü (`c:\Users\PC1\Documents\iddaaoranci`) GitHub hesabınıza yükleyin (Repo adı: `iddaaoranci`).
3. Railway paneline girip **New Project** -> **Deploy from GitHub repo** seçeneğine tıklayın.
4. Repo olarak `iddaaoranci` seçin. Railway otomatik olarak içindeki `Dockerfile`'ı algılayıp servisi 1 dakikada başlatacaktır.
5. Servis ayarlarından **Generate Domain** butonuna tıklayın. Size verilen canlı adresi kopyalayın:
   (Örn: `https://iddaaoranci-production.up.railway.app`)

---

## ⚙️ AŞAMA 3: n8n Otomasyonunu Kurma (1.5 Dakika)

n8n uygulamanıza otomatik taramaları eklemek için:

1. n8n panelinizi açın.
2. Sağ üstten **Workflows** -> **Import from File** butonuna tıklayın.
3. Proje klasöründeki `n8n_workflow.json` dosyasını seçin.
4. İçe aktarılan akışta 2 adet HTTP Request düğümü göreceksiniz:
   - **4 Saatlik Taramayı Gönder** düğümüne çift tıklayın:
     - URL kısmına Railway adresinizi yazın: `https://SİZİN-RAILWAY-URL/api/telegram_trigger`
     - JSON Body kısmında `"bot_token"` ve `"chat_id"` yerlerine Aşama 1'de aldığınız bilgileri yazın.
   - **23:45 Tüm Bülteni Gönder** düğümüne de aynı bilgileri girin.
5. n8n akışını sağ üstteki düğmeden **Active (Etkin)** yapın!

> 🎉 **Tebrikler!** Artık her gece **23:45'te** ertesi günün tüm bülteni, her **4 saatte bir** de yaklaşan maçlar Telegram grubunuza otomatik yağacak!

---

## 🌐 AŞAMA 4: Ngrok İle Arkadaşlarına Dağıtma (1 Dakika)

Bilgisayarınızda açık olan canlı Suleymando Web Panelini (`http://localhost:8501`) anında arkadaşlarınızla paylaşmak için:

1. Terminali veya PowerShell'i açın.
2. Şu komutu çalıştırın:
   ```powershell
   ngrok http 8501
   ```
3. Ekranda beliren **Forwarding** satırındaki HTTPS linkini kopyalayın:
   (Örn: `https://xxxx-xx-xx-xx.ngrok-free.app`)
4. Bu linki arkadaşlarına gönder! Arkadaşların dünyanın neresinde olurlarsa olsunlar Suleymando web panelini kullanabilir!
