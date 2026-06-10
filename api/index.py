import sys
import os
# Parent klasörü (kök dizini) Python import yoluna ekle
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, request, jsonify, session, send_from_directory
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from db_connection import execute_query, USE_MYSQL

# Statik klasörü projenin kök dizini yapıyoruz (Vercel CDN uyumluluğu için)
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
app = Flask(__name__, static_folder=root_dir, static_url_path='')
app.secret_key = 'challenge_tracker_secret_key_2026_final_project'

# Oturum açma kontrolü decorator'ı
def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Yetkilendirme hatası. Lütfen giriş yapın.'}), 401
        return f(*args, **kwargs)
    return decorated_function

# --- STATİK DOSYA SUNUCULARI ---

@app.route('/')
def index():
    return app.send_static_file('index.html')

# --- APIS (KULLANICI YETKİLENDİRME) ---

@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    username = data.get('username', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '')
    
    if not username or not email or not password:
        return jsonify({'error': 'Lütfen tüm alanları doldurun.'}), 400
        
    # Kullanıcı adı veya email zaten var mı kontrol et
    existing_user = execute_query(
        "SELECT id FROM users WHERE username = %s OR email = %s", 
        (username, email), 
        is_select=True
    )
    if existing_user:
        return jsonify({'error': 'Bu kullanıcı adı veya e-posta adresi zaten kullanımda.'}), 400
        
    password_hash = generate_password_hash(password)
    
    try:
        user_id = execute_query(
            "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)",
            (username, email, password_hash)
        )
        session['user_id'] = user_id
        session['username'] = username
        return jsonify({'success': 'Kayıt başarıyla oluşturuldu.', 'user': {'id': user_id, 'username': username}}), 201
    except Exception as e:
        return jsonify({'error': f'Kayıt sırasında bir hata oluştu: {str(e)}'}), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    username_or_email = data.get('username', '').strip()
    password = data.get('password', '')
    
    if not username_or_email or not password:
        return jsonify({'error': 'Lütfen tüm alanları doldurun.'}), 400
        
    # Kullanıcıyı getir
    user = execute_query(
        "SELECT id, username, password_hash FROM users WHERE username = %s OR email = %s",
        (username_or_email, username_or_email),
        is_select=True
    )
    
    if not user or not check_password_hash(user[0]['password_hash'], password):
        return jsonify({'error': 'Hatalı kullanıcı adı/e-posta veya şifre.'}), 401
        
    session['user_id'] = user[0]['id']
    session['username'] = user[0]['username']
    
    return jsonify({
        'success': 'Giriş başarılı.',
        'user': {'id': user[0]['id'], 'username': user[0]['username']}
    })

@app.route('/api/auth/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': 'Çıkış yapıldı.'})

@app.route('/api/auth/me', methods=['GET'])
def get_me():
    if 'user_id' in session:
        return jsonify({
            'logged_in': True,
            'user': {'id': session['user_id'], 'username': session['username']}
        })
    return jsonify({'logged_in': False}), 200


# --- APIS (ROZET KAZANMA SİSTEMİ) ---

def check_and_award_badges(user_id):
    """Kullanıcının kazandığı rozetleri dinamik olarak kontrol edip ekler."""
    awarded_badges = []
    
    # 1. Rozet: İlk Adım (En az 1 challenge oluşturulmuş olması)
    challenges = execute_query("SELECT id FROM challenges WHERE user_id = %s", (user_id,), is_select=True)
    if challenges:
        # Rozeti ver (id = 1)
        awarded = award_badge_if_not_exists(user_id, 1)
        if awarded:
            awarded_badges.append('İlk Adım')
            
    # 2. ve 3. Rozet: İstikrar Başlangıcı (3 Günlük Seri) ve Haftalık Savaşçı (7 Günlük Seri)
    # Kullanıcının tüm challenge'ları için günlük tamamlanan kayıtları alalım
    all_challenges = execute_query("SELECT id FROM challenges WHERE user_id = %s", (user_id,), is_select=True)
    max_streak = 0
    for ch in all_challenges:
        ch_id = ch['id']
        logs = execute_query(
            "SELECT log_date FROM daily_logs WHERE challenge_id = %s AND status = 'completed' ORDER BY log_date ASC",
            (ch_id,),
            is_select=True
        )
        if logs:
            dates = sorted([datetime.strptime(log['log_date'], "%Y-%m-%d").date() for log in logs])
            current_streak = 0
            longest_streak = 0
            prev_date = None
            
            for date in dates:
                if prev_date is None:
                    current_streak = 1
                elif date == prev_date + timedelta(days=1):
                    current_streak += 1
                elif date > prev_date + timedelta(days=1):
                    current_streak = 1 # Seri bozuldu, yeniden başla
                
                prev_date = date
                if current_streak > longest_streak:
                    longest_streak = current_streak
            
            if longest_streak > max_streak:
                max_streak = longest_streak
                
    if max_streak >= 3:
        awarded = award_badge_if_not_exists(user_id, 2) # İstikrar Başlangıcı
        if awarded:
            awarded_badges.append('İstikrar Başlangıcı')
            
    if max_streak >= 7:
        awarded = award_badge_if_not_exists(user_id, 3) # Haftalık Savaşçı
        if awarded:
            awarded_badges.append('Haftalık Savaşçı')
            
    # 4. Rozet: Fatih (En az 1 challenge'ın statüsünün 'completed' olması)
    completed_challenges = execute_query(
        "SELECT id FROM challenges WHERE user_id = %s AND status = 'completed'",
        (user_id,),
        is_select=True
    )
    if completed_challenges:
        awarded = award_badge_if_not_exists(user_id, 4) # Fatih
        if awarded:
            awarded_badges.append('Fatih')
            
    return awarded_badges

def award_badge_if_not_exists(user_id, badge_id):
    """Rozeti daha önce almamışsa kullanıcıya tanımlar."""
    existing = execute_query(
        "SELECT id FROM user_badges WHERE user_id = %s AND badge_id = %s",
        (user_id, badge_id),
        is_select=True
    )
    if not existing:
        execute_query(
            "INSERT INTO user_badges (user_id, badge_id) VALUES (%s, %s)",
            (user_id, badge_id)
        )
        return True
    return False


# --- APIS (CHALLENGE YÖNETİMİ) ---

@app.route('/api/challenges', methods=['GET'])
@login_required
def get_challenges():
    user_id = session['user_id']
    challenges = execute_query(
        "SELECT * FROM challenges WHERE user_id = %s ORDER BY created_at DESC",
        (user_id,),
        is_select=True
    )
    
    # Her challenge için günlük logları da çekelim
    for ch in challenges:
        ch_id = ch['id']
        logs = execute_query(
            "SELECT id, log_date, status, notes FROM daily_logs WHERE challenge_id = %s ORDER BY log_date ASC",
            (ch_id,),
            is_select=True
        )
        ch['logs'] = logs
        
        # Toplam gün sayısını hesapla
        try:
            start_dt = datetime.strptime(ch['start_date'], "%Y-%m-%d").date() if isinstance(ch['start_date'], str) else ch['start_date']
            end_dt = datetime.strptime(ch['end_date'], "%Y-%m-%d").date() if isinstance(ch['end_date'], str) else ch['end_date']
            ch['total_days'] = (end_dt - start_dt).days + 1
        except Exception:
            ch['total_days'] = 1
            
        ch['completed_days'] = sum(1 for log in logs if log['status'] == 'completed')
        
    return jsonify(challenges)

@app.route('/api/challenges', methods=['POST'])
@login_required
def create_challenge():
    user_id = session['user_id']
    data = request.get_json() or {}
    
    title = data.get('title', '').strip()
    description = data.get('description', '').strip()
    start_date = data.get('start_date', '')
    end_date = data.get('end_date', '')
    category = data.get('category', 'Diğer').strip()
    
    if not title or not start_date or not end_date:
        return jsonify({'error': 'Lütfen zorunlu alanları doldurun (Başlık, Başlangıç Tarihi, Bitiş Tarihi).'}), 400
        
    try:
        # Tarih formatlarını doğrula
        datetime.strptime(start_date, "%Y-%m-%d")
        datetime.strptime(end_date, "%Y-%m-%d")
    except ValueError:
        return jsonify({'error': 'Tarih formatı YYYY-AA-GG şeklinde olmalıdır.'}), 400
        
    try:
        challenge_id = execute_query(
            "INSERT INTO challenges (user_id, title, description, start_date, end_date, category) VALUES (%s, %s, %s, %s, %s, %s)",
            (user_id, title, description, start_date, end_date, category)
        )
        
        # Rozetleri kontrol et (İlk Adım rozeti eklenecektir)
        new_badges = check_and_award_badges(user_id)
        
        return jsonify({
            'success': 'Meydan okuma başarıyla oluşturuldu.',
            'challenge_id': challenge_id,
            'new_badges': new_badges
        }), 201
    except Exception as e:
        return jsonify({'error': f'Meydan okuma oluşturulurken hata: {str(e)}'}), 500

@app.route('/api/challenges/<int:challenge_id>', methods=['DELETE'])
@login_required
def delete_challenge(challenge_id):
    user_id = session['user_id']
    # Challenge'ın kullanıcıya ait olduğundan emin ol
    challenge = execute_query(
        "SELECT id FROM challenges WHERE id = %s AND user_id = %s",
        (challenge_id, user_id),
        is_select=True
    )
    if not challenge:
        return jsonify({'error': 'Meydan okuma bulunamadı veya yetkiniz yok.'}), 404
        
    try:
        execute_query("DELETE FROM challenges WHERE id = %s", (challenge_id,))
        return jsonify({'success': 'Meydan okuma başarıyla silindi.'})
    except Exception as e:
        return jsonify({'error': f'Meydan okuma silinirken hata: {str(e)}'}), 500

@app.route('/api/challenges/<int:challenge_id>/status', methods=['PUT'])
@login_required
def update_challenge_status(challenge_id):
    user_id = session['user_id']
    data = request.get_json() or {}
    new_status = data.get('status', 'active')
    
    if new_status not in ['active', 'completed', 'failed']:
        return jsonify({'error': 'Geçersiz statü değeri.'}), 400
        
    # Challenge kontrolü
    challenge = execute_query(
        "SELECT id FROM challenges WHERE id = %s AND user_id = %s",
        (challenge_id, user_id),
        is_select=True
    )
    if not challenge:
        return jsonify({'error': 'Meydan okuma bulunamadı.'}), 404
        
    try:
        execute_query(
            "UPDATE challenges SET status = %s WHERE id = %s",
            (new_status, challenge_id)
        )
        # Rozet kazanma durumunu tetikle (Fatih Rozeti vb.)
        new_badges = check_and_award_badges(user_id)
        
        return jsonify({
            'success': 'Meydan okuma durumu güncellendi.',
            'new_badges': new_badges
        })
    except Exception as e:
        return jsonify({'error': f'Güncelleme sırasında hata: {str(e)}'}), 500


# --- APIS (GÜNLÜK İLERLEME LOGLARI YÖNETİMİ) ---

@app.route('/api/challenges/<int:challenge_id>/log', methods=['POST'])
@login_required
def log_progress(challenge_id):
    user_id = session['user_id']
    data = request.get_json() or {}
    
    log_date = data.get('log_date')
    status = data.get('status') # 'completed', 'missed', 'pending'
    notes = data.get('notes', '').strip()
    
    if not log_date or not status:
        return jsonify({'error': 'Lütfen tarih ve durum bilgilerini gönderin.'}), 400
        
    if status not in ['completed', 'missed', 'pending']:
        return jsonify({'error': 'Geçersiz durum.'}), 400
        
    # Challenge'ın kullanıcıya ait olduğundan emin ol
    challenge = execute_query(
        "SELECT id FROM challenges WHERE id = %s AND user_id = %s",
        (challenge_id, user_id),
        is_select=True
    )
    if not challenge:
        return jsonify({'error': 'Meydan okuma bulunamadı veya yetkiniz yok.'}), 404
        
    try:
        # İlgili tarih için daha önce log girilmiş mi kontrol et
        existing_log = execute_query(
            "SELECT id FROM daily_logs WHERE challenge_id = %s AND log_date = %s",
            (challenge_id, log_date),
            is_select=True
        )
        
        if existing_log:
            # Güncelle
            execute_query(
                "UPDATE daily_logs SET status = %s, notes = %s WHERE id = %s",
                (status, notes, existing_log[0]['id'])
            )
        else:
            # Yeni ekle
            execute_query(
                "INSERT INTO daily_logs (challenge_id, log_date, status, notes) VALUES (%s, %s, %s, %s)",
                (challenge_id, log_date, status, notes)
            )
            
        # Rozet kazanma koşullarını kontrol et (3 ve 7 günlük seriler)
        new_badges = check_and_award_badges(user_id)
        
        return jsonify({
            'success': 'Günlük ilerleme başarıyla kaydedildi.',
            'new_badges': new_badges
        })
    except Exception as e:
        return jsonify({'error': f'Kayıt işlemi sırasında hata: {str(e)}'}), 500


# --- APIS (İSTATİSTİKLER VE ROZETLER PANELİ) ---

@app.route('/api/dashboard/stats', methods=['GET'])
@login_required
def get_dashboard_stats():
    user_id = session['user_id']
    
    # 1. Genel sayılar
    stats = execute_query(
        """SELECT 
            SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) as active_count,
            SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_count
           FROM challenges WHERE user_id = %s""",
        (user_id,),
        is_select=True
    )
    
    active_count = stats[0]['active_count'] or 0 if stats else 0
    completed_count = stats[0]['completed_count'] or 0 if stats else 0
    
    # 2. Kazanılan rozet sayısı ve rozet detayları
    user_badges = execute_query(
        """SELECT b.name, b.description, b.icon_url, ub.earned_at 
           FROM user_badges ub 
           JOIN badges b ON ub.badge_id = b.id 
           WHERE ub.user_id = %s 
           ORDER BY ub.earned_at DESC""",
        (user_id,),
        is_select=True
    )
    
    # Tüm rozetleri alalım (hangileri kilitli, hangileri açık olduğunu arayüzde göstermek için)
    all_badges = execute_query("SELECT * FROM badges", is_select=True)
    earned_names = {b['name'] for b in user_badges}
    for b in all_badges:
        b['earned'] = b['name'] in earned_names
        # Eğer kazanılmışsa kazanılma tarihini ekle
        if b['earned']:
            for ub in user_badges:
                if ub['name'] == b['name']:
                    # Tarih objesini string'e dönüştür
                    b['earned_at'] = ub['earned_at'].strftime("%Y-%m-%d %H:%M:%S") if hasattr(ub['earned_at'], 'strftime') else str(ub['earned_at'])
                    break
        else:
            b['earned_at'] = None
            
    # 3. Kategori Dağılımı
    categories = execute_query(
        "SELECT category, COUNT(*) as count FROM challenges WHERE user_id = %s GROUP BY category",
        (user_id,),
        is_select=True
    )
    
    # 4. En son yapılan 5 aktivite (Kazanılan rozetler veya yapılan günlük loglar)
    recent_logs = execute_query(
        """SELECT c.title as challenge_title, d.log_date, d.status, d.notes, d.created_at as time
           FROM daily_logs d
           JOIN challenges c ON d.challenge_id = c.id
           WHERE c.user_id = %s AND d.status != 'pending'
           ORDER BY d.created_at DESC LIMIT 5""",
        (user_id,),
        is_select=True
    )
    
    activities = []
    # Log aktivitelerini ekle
    for log in recent_logs:
        # Tarih formatlamasını yap
        time_str = log['time'].strftime("%Y-%m-%d %H:%M") if hasattr(log['time'], 'strftime') else str(log['time'])
        activities.append({
            'type': 'log',
            'title': f"'{log['challenge_title']}' için günlük kayıt",
            'detail': f"{log['log_date']} tarihi '{'Tamamlandı' if log['status']=='completed' else 'Kaçırıldı'}' olarak işaretlendi. Not: {log['notes'] or '-'}",
            'time': time_str
        })
        
    # Rozet kazanma aktivitelerini ekle
    for b in user_badges:
        time_str = b['earned_at'].strftime("%Y-%m-%d %H:%M") if hasattr(b['earned_at'], 'strftime') else str(b['earned_at'])
        activities.append({
            'type': 'badge',
            'title': f"Rozet Kazanıldı: {b['name']}",
            'detail': b['description'],
            'time': time_str
        })
        
    # Zaman sırasına göre sıralayıp ilk 5'i al
    activities = sorted(activities, key=lambda x: x['time'], reverse=True)[:5]
    
    # 5. Güncel En Uzun Seri (Streak)
    # Kullanıcının tüm challenge'ları arasında en uzun aktif serisini hesaplayalım
    total_streak = 0
    challenges = execute_query("SELECT id FROM challenges WHERE user_id = %s", (user_id,), is_select=True)
    for ch in challenges:
        ch_id = ch['id']
        logs = execute_query(
            "SELECT log_date FROM daily_logs WHERE challenge_id = %s AND status = 'completed' ORDER BY log_date ASC",
            (ch_id,),
            is_select=True
        )
        if logs:
            dates = sorted([datetime.strptime(log['log_date'], "%Y-%m-%d").date() for log in logs])
            current_streak = 0
            longest_streak = 0
            prev_date = None
            for date in dates:
                if prev_date is None:
                    current_streak = 1
                elif date == prev_date + timedelta(days=1):
                    current_streak += 1
                elif date > prev_date + timedelta(days=1):
                    current_streak = 1
                prev_date = date
                if current_streak > longest_streak:
                    longest_streak = current_streak
            if longest_streak > total_streak:
                total_streak = longest_streak
                
    # Veritabanı Modu Bilgisi
    db_mode = 'MySQL' if USE_MYSQL else 'SQLite'

    return jsonify({
        'active_challenges': active_count,
        'completed_challenges': completed_count,
        'badges_earned_count': len(user_badges),
        'all_badges': all_badges,
        'category_distribution': categories,
        'recent_activities': activities,
        'longest_streak': total_streak,
        'db_mode': db_mode
    })


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
