# QuickAnimations ⚡

SVG dosyalarını Manim animasyonlarına (MP4) dönüştüren modern ve hızlı bir araçtır.

## 🚀 Kurulum ve Kullanım

### Başlangıç
Özel bir kuruluma gerek yoktur. `QuickAnimations.exe` dosyasını çift tıklayarak çalıştırın.

#### İlk Çalıştırma
Uygulama ilk kez açıldığında **Otomatik Kurulum Sihirbazı** devreye girer:
1. Gerekli Python sürümünü ve Manim kütüphanesini otomatik indirir.
2. `~/.quickanimations` klasörüne izole bir ortam kurar.
3. Kurulum tamamlanınca ana ekrana geçer.

*Eğer zaten Manim yüklü bir Python'unuz varsa, kurulum ekranında **"Kurulumu Geç"** butonuna basarak `python.exe` dosyanızı gösterebilirsiniz.*

### Animasyon Oluşturma
1. Uygulamayı açın.
2. Bir **.SVG** dosyasını pencereye sürükleyin veya dosya seçici ile seçin.
3. **Çözünürlük** (1080p, 2K, 4K) ve **FPS** (30, 60) ayarlarını yapın.
4. **"Animasyonu Oluştur"** butonuna basın.
5. İşlem bitince masaüstünüzde MP4 video dosyanız hazır olacak!

---

## 🛠 Gelişmiş Özellikler

### CLI Modu (Komut Satırı)
Terminal veya CMD üzerinden arayüzsüz render alabilirsiniz:
```cmd
QuickAnimations.exe --cli "C:\dosya\ornek.svg"
```

### Klavye Kısayolları (Geliştirici Modu)
Eğer Python script olarak çalıştırıyorsanız (`QuickAnimations.py`), `Ctrl+Shift+M` kısayolu ile seçili dosyayı hızlıca render alabilirsiniz.

---

## 📂 Dosya Yapısı
- **QuickAnimations.exe**: Ana uygulama
- **~/.quickanimations/**: Uygulama verileri ve sanal ortam (Python, venv)

**Geliştirici:** QngChan
**Lisans:** MIT
