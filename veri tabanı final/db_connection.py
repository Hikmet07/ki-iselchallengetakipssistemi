import os
import sqlite3
import logging

# Log yapılandırması
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# MySQL Bağlantı Ayarları (Değiştirilebilir)
MYSQL_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',  # Buraya kendi MySQL şifrenizi yazabilirsiniz
    'database': 'challenge_tracker_db'
}

USE_MYSQL = False
mysql_connector = None

# mysql-connector kütüphanesini içe aktarmayı dene
try:
    import mysql.connector
    mysql_connector = mysql.connector
    # MySQL'e bağlanmayı dene
    conn = mysql.connector.connect(
        host=MYSQL_CONFIG['host'],
        user=MYSQL_CONFIG['user'],
        password=MYSQL_CONFIG['password']
    )
    cursor = conn.cursor()
    # Veritabanını oluştur (yoksa)
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {MYSQL_CONFIG['database']}")
    conn.commit()
    cursor.close()
    conn.close()
    
    # Şimdi hedef veritabanına bağlan
    conn = mysql.connector.connect(**MYSQL_CONFIG)
    conn.close()
    USE_MYSQL = True
    logger.info("MySQL veritabanına başarıyla bağlanıldı. Sistem MySQL modunda çalışıyor.")
except Exception as e:
    logger.warning(f"MySQL bağlantısı kurulamadı veya mysql-connector kurulu değil. Hata: {e}")
    logger.info("Sistem otomatik olarak SQLite veritabanına (challenge_tracker.db) geçiş yapıyor.")
    USE_MYSQL = False

if os.environ.get('VERCEL') or os.environ.get('VERCEL_ENV'):
    SQLITE_DB_PATH = '/tmp/challenge_tracker.db'
else:
    SQLITE_DB_PATH = 'challenge_tracker.db'

def init_sqlite_db():
    """SQLite veritabanını oluşturur ve şemayı kurarak örnek verileri ekler."""
    if os.path.exists(SQLITE_DB_PATH):
        return
        
    logger.info("SQLite veritabanı dosyası oluşturuluyor...")
    conn = sqlite3.connect(SQLITE_DB_PATH)
    cursor = conn.cursor()
    
    # SQLite Şeması
    schema_queries = [
        "PRAGMA foreign_keys = ON;",
        
        """CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );""",
        
        """CREATE TABLE IF NOT EXISTS challenges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT NULL,
            start_date DATE NOT NULL,
            end_date DATE NOT NULL,
            status TEXT CHECK(status IN ('active', 'completed', 'failed')) DEFAULT 'active',
            category TEXT NOT NULL DEFAULT 'Diğer',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );""",
        
        """CREATE TABLE IF NOT EXISTS daily_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            challenge_id INTEGER NOT NULL,
            log_date DATE NOT NULL,
            status TEXT CHECK(status IN ('completed', 'missed', 'pending')) DEFAULT 'pending',
            notes TEXT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (challenge_id) REFERENCES challenges(id) ON DELETE CASCADE,
            UNIQUE(challenge_id, log_date)
        );""",
        
        """CREATE TABLE IF NOT EXISTS badges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            description TEXT NOT NULL,
            icon_url TEXT NOT NULL
        );""",
        
        """CREATE TABLE IF NOT EXISTS user_badges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            badge_id INTEGER NOT NULL,
            earned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (badge_id) REFERENCES badges(id) ON DELETE CASCADE,
            UNIQUE(user_id, badge_id)
        );"""
    ]
    
    for q in schema_queries:
        cursor.execute(q)
        
    # Örnek Rozetlerin eklenmesi
    badges_data = [
        ('İlk Adım', 'İlk meydan okumanı oluşturarak yolculuğa başladın.', 'badge_first_step'),
        ('İstikrar Başlangıcı', 'Herhangi bir meydan okumada üst üste 3 gün tamamladın.', 'badge_streak_3'),
        ('Haftalık Savaşçı', 'Herhangi bir meydan okumada üst üste 7 gün tamamladın.', 'badge_streak_7'),
        ('Fatih', 'Bir meydan okumayı başarıyla tamamladın.', 'badge_completed')
    ]
    
    for badge in badges_data:
        try:
            cursor.execute("INSERT INTO badges (name, description, icon_url) VALUES (?, ?, ?)", badge)
        except sqlite3.IntegrityError:
            pass # Zaten varsa atla
            
    # Örnek Test Kullanıcısı (Parola: 'admin123' pbkdf2:sha256 karşılığı)
    try:
        cursor.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)", 
            ('deneme', 'deneme@test.com', 'scrypt:32768:8:1$u7F5T2x1Z6e9w4q3$14ba81f6ca1c42289c09c91f6cc9bd708a2adfe17cb97cb52ea93998b4b79b908b8b0907e4d8fb8db1420b9df44b4d618d748f65be6e1a90d810149028bc25de')
        )
        # Örnek Challenge verileri
        cursor.execute(
            "INSERT INTO challenges (id, user_id, title, description, start_date, end_date, status, category) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (1, 1, '30 Gün Yazılım Geliştirme', 'Her gün en az 1 saat kod yazılacak ve Github commit atılacak.', '2026-06-01', '2026-06-30', 'active', 'Yazılım')
        )
        cursor.execute(
            "INSERT INTO challenges (id, user_id, title, description, start_date, end_date, status, category) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (2, 1, 'Kitap Okuma Serüveni', 'Her gün yatmadan önce 20 sayfa kitap okunacak.', '2026-06-01', '2026-06-15', 'active', 'Kişisel Gelişim')
        )
        # Örnek Günlük loglar
        logs = [
            (1, '2026-06-08', 'completed', 'Backend API rotaları kodlandı.'),
            (1, '2026-06-09', 'completed', 'Veritabanı şeması ve testler yapıldı.'),
            (1, '2026-06-10', 'completed', 'Frontend arayüzü tasarlandı.'),
            (2, '2026-06-08', 'completed', 'Sefiller kitabından 25 sayfa okundu.'),
            (2, '2026-06-09', 'missed', 'Yorgunluktan dolayı okunamadı.'),
            (2, '2026-06-10', 'completed', 'Dünün telafisiyle 40 sayfa okundu.')
        ]
        for log in logs:
            cursor.execute("INSERT INTO daily_logs (challenge_id, log_date, status, notes) VALUES (?, ?, ?, ?)", log)
            
        # Örnek kazanılan rozetler
        cursor.execute("INSERT INTO user_badges (user_id, badge_id) VALUES (?, ?)", (1, 1))
        cursor.execute("INSERT INTO user_badges (user_id, badge_id) VALUES (?, ?)", (1, 2))
    except sqlite3.IntegrityError:
        pass
        
    conn.commit()
    conn.close()
    logger.info("SQLite veritabanı başarıyla oluşturuldu ve örnek veriler eklendi.")

# SQLite başlangıcı
if not USE_MYSQL:
    init_sqlite_db()

def get_db_connection():
    """Aktif veritabanı moduna göre bağlantı nesnesi döndürür."""
    if USE_MYSQL:
        return mysql_connector.connect(**MYSQL_CONFIG)
    else:
        conn = sqlite3.connect(SQLITE_DB_PATH)
        # SQLite'da dictionary tabanlı çıktı almak için row_factory ayarlanır
        conn.row_factory = sqlite3.Row
        return conn

def execute_query(query, params=None, is_select=False):
    """
    SQL sorgularını güvenli ve tek bir standartta çalıştırır.
    MySQL'deki '%s' parametre formatını SQLite için otomatik olarak '?' yapar.
    """
    if params is None:
        params = ()
        
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # SQLite kullanılıyorsa sorgudaki %s yer tutucularını ? karakterine dönüştür
        if not USE_MYSQL:
            query = query.replace('%s', '?')
            # SQLite için PRAGMA foreign keys'i aktif et
            cursor.execute("PRAGMA foreign_keys = ON;")
            
        cursor.execute(query, params)
        
        if is_select:
            if USE_MYSQL:
                # MySQL için sütun isimleriyle birlikte dict formatında oku
                columns = [col[0] for col in cursor.description]
                result = [dict(zip(columns, row)) for row in cursor.fetchall()]
            else:
                # SQLite için sqlite3.Row nesnelerini dict yap
                result = [dict(row) for row in cursor.fetchall()]
            return result
        else:
            conn.commit()
            last_id = cursor.lastrowid
            return last_id
            
    except Exception as e:
        logger.error(f"Sorgu çalıştırılırken hata oluştu: {query} \n Hata: {e}")
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()
