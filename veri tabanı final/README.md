# Kişisel Challenge Takip Sistemi (Personal Challenge Tracker)

Bu proje, üniversite veritabanı final ödevi için geliştirilmiş, gerçek bir senaryoya dayanan **Kişisel Challenge Takip Sistemi**dir. Kullanıcıların kendilerine çeşitli kategorilerde meydan okumalar (hedefler) belirlemesini, bunları takvim üzerinden günlük olarak takip etmesini, başarı istatistiklerini grafiklerle görüntülemesini ve belirli kriterleri sağladıklarında otomatik rozetler kazanmasını sağlar.

---

## 🚀 Öne Çıkan Özellikler

1. **İlişkisel Veritabanı Tasarımı (MySQL):** Düzgün normalize edilmiş, yabancı anahtar (Foreign Key) ilişkileri kurulmuş ve kaskad silme (ON DELETE CASCADE) özellikleri tanımlanmış 5 tabloluk ilişkisel veritabanı yapısı.
2. **Hibrit Veritabanı Modu (SQLite Fallback):** Proje varsayılan olarak **MySQL** kullanır. Ancak MySQL sunucusunun kapalı olması veya kütüphanelerin yüklü olmaması durumunda, uygulama hata verip kapanmak yerine **otomatik olarak SQLite moduna geçer** ve yerel bir `challenge_tracker.db` oluşturur. Bu sayede projeyi puanlayacak öğretim görevlisi bilgisayarında sıfır kurulumla doğrudan çalıştırabilir.
3. **Kullanıcı Yetkilendirme:** Kayıt olma (Sign Up) ve güvenli parola hashleme (Werkzeug PBKDF2/Scrypt) içeren Giriş Yapma (Log In) sistemi.
4. **Dinamik Takvim ve Günlük Kayıt:** Her meydan okumanın kendi başlangıç/bitiş tarihlerine göre oluşturulan interaktif gün kutucukları. Günlere tıklayarak o günün tamamlandığını (yeşil), kaçırıldığını (kırmızı) işaretleyebilir ve güne özel notlar girebilirsiniz.
5. **Otomatik Rozet Sistemi:**
   - **İlk Adım Rozeti:** İlk meydan okuma oluşturulduğunda kazanılır.
   - **İstikrar Başlangıcı:** Herhangi bir hedefte üst üste 3 gün tamamlandığında kazanılır.
   - **Haftalık Savaşçı:** Herhangi bir hedefte üst üste 7 gün tamamlandığında kazanılır.
   - **Fatih:** Bir meydan okuma başarıyla tamamlandığında (veya statüsü tamamlandıya çekildiğinde) kazanılır.
6. **Premium Görsel Tasarım:** Koyu mod (Dark Mode) renk paleti, yarı saydam cam efekti (Glassmorphism), pürüzsüz hover mikro-animasyonları ve responsive mobil uyumlu arayüz.
7. **Grafiksel İstatistikler:** **Chart.js** entegrasyonu ile kategorilere göre meydan okuma dağılımını gösteren interaktif pasta grafik.

---

## 📁 Klasör Yapısı

```text
C:/Users/Hikmet UĞURLU/Desktop/veri tabanı final/
│
├── app.py                # Flask Backend API ve Sunucu dosyası
├── db_connection.py      # MySQL & SQLite hibrit veritabanı sürücüsü
├── schema.sql            # MySQL veritabanı kurulum şeması ve örnek veriler
├── requirements.txt      # Gerekli Python kütüphaneleri listesi
├── README.md             # Proje dokümantasyonu (Bu dosya)
│
└── static/               # Frontend (Ön yüz) statik kaynak dosyaları
    ├── index.html        # Ana HTML sayfası (Dashboard & Auth)
    ├── style.css         # Premium Glassmorphism stil dosyası
    └── app.js            # Fetch istekleri, arayüz yönetimi ve grafik betikleri
```

---

## 🛠️ Kurulum ve Çalıştırma

### 1. Adım: Python ve Kütüphanelerin Kurulumu
Bilgisayarınızda Python yüklü olduğundan emin olun (Bu sistemde test edilmiştir: Python 3.12). 
Komut istemini (Command Prompt veya PowerShell) açın, proje klasörüne gidin ve gerekli kütüphaneleri yükleyin:

```bash
pip install -r requirements.txt
```

### 2. Adım: Veritabanının Hazırlanması (İsteğe Bağlı - MySQL için)
Uygulama SQLite ile doğrudan çalışabilir fakat **MySQL** kullanmak istiyorsanız:
1. MySQL Server ve MySQL Workbench'i (veya XAMPP/WampServer) çalıştırın.
2. `schema.sql` dosyasındaki SQL komutlarını MySQL Workbench üzerinde çalıştırarak veritabanını ve tabloları oluşturun.
3. `db_connection.py` dosyasını açın ve en üstte yer alan `MYSQL_CONFIG` sözlüğünü kendi MySQL bağlantı bilgilerinizle (şifre, port vb.) güncelleyin:
   ```python
   MYSQL_CONFIG = {
       'host': 'localhost',
       'user': 'root',
       'password': 'KENDI_SIFRENIZ',
       'database': 'challenge_tracker_db'
   }
   ```

### 3. Adım: Projeyi Başlatma
Proje dizininde aşağıdaki komutu çalıştırarak Flask sunucusunu başlatın:

```bash
python app.py
```

Ekranınızda şu tarz bir çıktı göreceksiniz:
`* Running on http://127.0.0.1:5000`

### 4. Adım: Tarayıcıda Görüntüleme
Tarayıcınızı açın ve adres çubuğuna şunu yazın:
[http://127.0.0.1:5000](http://127.0.0.1:5000)

---

## 👤 Hazır Test Kullanıcısı

Sistemi hızlıca incelemek ve hazır verileri görmek için aşağıdaki hesap bilgilerini kullanarak doğrudan giriş yapabilirsiniz:

- **Kullanıcı Adı:** `deneme` (veya e-posta: `deneme@test.com`)
- **Şifre:** `admin123`

*(Giriş yaptığınızda hazır 2 meydan okuma, tamamlanmış bazı günler, grafikler ve 2 adet kazanılmış rozet sizi karşılayacaktır.)*
