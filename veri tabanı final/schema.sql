-- Kişisel Challenge Takip Sistemi Veritabanı Şeması (MySQL)

CREATE DATABASE IF NOT EXISTS challenge_tracker_db;
USE challenge_tracker_db;

-- 1. Tabloları temizle (Sırasıyla ilişkileri bozmadan siler)
SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE IF EXISTS user_badges;
DROP TABLE IF EXISTS badges;
DROP TABLE IF EXISTS daily_logs;
DROP TABLE IF EXISTS challenges;
DROP TABLE IF EXISTS users;
SET FOREIGN_KEY_CHECKS = 1;

-- 2. Tabloların Oluşturulması

-- Kullanıcılar Tablosu
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Meydan Okumalar (Challenges) Tablosu
CREATE TABLE challenges (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    title VARCHAR(100) NOT NULL,
    description TEXT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    status ENUM('active', 'completed', 'failed') DEFAULT 'active',
    category VARCHAR(50) NOT NULL DEFAULT 'Diğer',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Günlük İlerleme Kayıtları (Daily Logs) Tablosu
CREATE TABLE daily_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    challenge_id INT NOT NULL,
    log_date DATE NOT NULL,
    status ENUM('completed', 'missed', 'pending') DEFAULT 'pending',
    notes TEXT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (challenge_id) REFERENCES challenges(id) ON DELETE CASCADE,
    UNIQUE KEY unique_challenge_date (challenge_id, log_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Rozetler (Badges) Tablosu
CREATE TABLE badges (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT NOT NULL,
    icon_url VARCHAR(255) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Kullanıcı-Rozet İlişkisi Tablosu
CREATE TABLE user_badges (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    badge_id INT NOT NULL,
    earned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (badge_id) REFERENCES badges(id) ON DELETE CASCADE,
    UNIQUE KEY unique_user_badge (user_id, badge_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3. Örnek Verilerin Eklenmesi (Rozet Tanımlamaları)
INSERT INTO badges (name, description, icon_url) VALUES
('İlk Adım', 'İlk meydan okumanı oluşturarak yolculuğa başladın.', 'badge_first_step'),
('İstikrar Başlangıcı', 'Herhangi bir meydan okumada üst üste 3 gün tamamladın.', 'badge_streak_3'),
('Haftalık Savaşçı', 'Herhangi bir meydan okumada üst üste 7 gün tamamladın.', 'badge_streak_7'),
('Fatih', 'Bir meydan okumayı başarıyla tamamladın.', 'badge_completed');

-- Örnek Kullanıcı Tanımlaması (Parola: 'admin123' pbkdf2:sha256 hash karşılığı)
INSERT INTO users (username, email, password_hash) VALUES
('deneme', 'deneme@test.com', 'scrypt:32768:8:1$u7F5T2x1Z6e9w4q3$14ba81f6ca1c42289c09c91f6cc9bd708a2adfe17cb97cb52ea93998b4b79b908b8b0907e4d8fb8db1420b9df44b4d618d748f65be6e1a90d810149028bc25de');

-- Örnek Challenge Tanımlamaları
INSERT INTO challenges (id, user_id, title, description, start_date, end_date, status, category) VALUES
(1, 1, '30 Gün Yazılım Geliştirme', 'Her gün en az 1 saat kod yazılacak ve Github commit atılacak.', '2026-06-01', '2026-06-30', 'active', 'Yazılım'),
(2, 1, 'Kitap Okuma Serüveni', 'Her gün yatmadan önce 20 sayfa kitap okunacak.', '2026-06-01', '2026-06-15', 'active', 'Kişisel Gelişim');

-- Örnek Günlük Kayıtlar (Log)
INSERT INTO daily_logs (challenge_id, log_date, status, notes) VALUES
(1, '2026-06-08', 'completed', 'Backend API rotaları kodlandı.'),
(1, '2026-06-09', 'completed', 'Veritabanı şeması ve testler yapıldı.'),
(1, '2026-06-10', 'completed', 'Frontend arayüzü tasarlandı.'),
(2, '2026-06-08', 'completed', 'Sefiller kitabından 25 sayfa okundu.'),
(2, '2026-06-09', 'missed', 'Yorgunluktan dolayı okunamadı.'),
(2, '2026-06-10', 'completed', 'Dünün telafisiyle 40 sayfa okundu.');

-- Örnek Kazanılan Rozetler
INSERT INTO user_badges (user_id, badge_id, earned_at) VALUES
(1, 1, CURRENT_TIMESTAMP),
(1, 2, CURRENT_TIMESTAMP);
