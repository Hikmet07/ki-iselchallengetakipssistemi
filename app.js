// Frontend Uygulama Mantığı (Vanilla JS & AJAX)

// Sayfa yüklendiğinde çalışacak ana olay
document.addEventListener('DOMContentLoaded', () => {
    // Uygulama Durumu (State)
    const state = {
        user: null,
        challenges: [],
        stats: null
    };

    // Chart.js Grafik Değişkeni
    let categoryChart = null;

    // DOM Elementleri
    const authContainer = document.getElementById('auth-container');
    const appContainer = document.getElementById('app-container');
    const loginForm = document.getElementById('login-form');
    const registerForm = document.getElementById('register-form');
    const showRegisterLink = document.getElementById('show-register');
    const showLoginLink = document.getElementById('show-login');
    
    const sidebarMenuItems = document.querySelectorAll('.sidebar-menu .menu-item');
    const tabContents = document.querySelectorAll('.tab-content');
    const logoutBtn = document.getElementById('logout-btn');
    const dbModeText = document.getElementById('db-mode-text');
    
    const profileUsername = document.getElementById('profile-username');
    const welcomeMessage = document.getElementById('welcome-message');
    const headerStreakVal = document.getElementById('header-streak-val');
    
    // Stats
    const statActiveCount = document.getElementById('stat-active-count');
    const statCompletedCount = document.getElementById('stat-completed-count');
    const statBadgeCount = document.getElementById('stat-badge-count');
    const activeChallengesBadge = document.getElementById('active-challenges-badge');
    
    // Listeler
    const recentActivitiesList = document.getElementById('recent-activities-list');
    const quickBadgesList = document.getElementById('quick-badges-list');
    const challengesList = document.getElementById('challenges-list');
    const badgesGridFull = document.getElementById('badges-grid-full');
    
    // Formlar
    const createChallengeForm = document.getElementById('create-challenge-form');
    
    // Modal
    const logModal = document.getElementById('log-modal');
    const logForm = document.getElementById('log-form');
    const logChallengeId = document.getElementById('log-challenge-id');
    const logDateInput = document.getElementById('log-date');
    const logDateDisplay = document.getElementById('log-date-display');
    const logNotes = document.getElementById('log-notes');
    const closeModalBtn = document.getElementById('close-modal-btn');

    // --- BİLDİRİM (TOAST) YÖNETİMİ ---
    function showToast(message, type = 'success') {
        const toast = document.getElementById('toast');
        toast.textContent = message;
        toast.className = `toast ${type}`;
        toast.classList.remove('hidden');
        
        setTimeout(() => {
            toast.classList.add('hidden');
        }, 4000);
    }

    // --- OTURUM KONTROLÜ (AUTH) ---
    async function checkAuth() {
        try {
            const res = await fetch('/api/auth/me');
            const data = await res.json();
            
            if (data.logged_in) {
                state.user = data.user;
                showApp();
            } else {
                state.user = null;
                showAuth();
            }
        } catch (err) {
            console.error('Yetkilendirme kontrolü başarısız:', err);
            showAuth();
        }
    }

    function showApp() {
        authContainer.classList.add('hidden');
        appContainer.classList.remove('hidden');
        profileUsername.textContent = state.user.username;
        welcomeMessage.textContent = `Hoş Geldin, ${state.user.username}!`;
        loadDashboardData();
    }

    function showAuth() {
        appContainer.classList.add('hidden');
        authContainer.classList.remove('hidden');
    }

    // --- SAYFA GEÇİŞLERİ (TABS) ---
    sidebarMenuItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const targetTabId = item.getAttribute('data-target');
            
            sidebarMenuItems.forEach(mi => mi.classList.remove('active'));
            item.classList.add('active');
            
            tabContents.forEach(tab => {
                tab.classList.remove('active-tab');
                if (tab.id === targetTabId) {
                    tab.classList.add('active-tab');
                }
            });
            
            // Sekmeye göre veriyi yenile
            if (targetTabId === 'challenges-section') {
                loadChallenges();
            } else if (targetTabId === 'badges-section') {
                loadDashboardData();
            } else if (targetTabId === 'dashboard-section') {
                loadDashboardData();
            }
        });
    });

    // Giriş/Kayıt formları arası geçiş
    showRegisterLink.addEventListener('click', (e) => {
        e.preventDefault();
        loginForm.classList.add('hidden');
        registerForm.classList.remove('hidden');
        document.getElementById('auth-subtitle').textContent = "Aramıza katılın ve hedeflerinizi yönetmeye başlayın.";
    });

    showLoginLink.addEventListener('click', (e) => {
        e.preventDefault();
        registerForm.classList.add('hidden');
        loginForm.classList.remove('hidden');
        document.getElementById('auth-subtitle').textContent = "Hedeflerinizi belirleyin, serinizi koruyun ve kendinizi geliştirin.";
    });

    // --- FORM GÖNDERİMLERİ ---

    // Kayıt Formu
    registerForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const username = document.getElementById('register-username').value;
        const email = document.getElementById('register-email').value;
        const password = document.getElementById('register-password').value;
        
        try {
            const res = await fetch('/api/auth/register', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, email, password })
            });
            const data = await res.json();
            
            if (res.ok) {
                showToast(data.success);
                state.user = data.user;
                registerForm.reset();
                showApp();
            } else {
                showToast(data.error || 'Kayıt başarısız.', 'error');
            }
        } catch (err) {
            showToast('Sunucu bağlantı hatası.', 'error');
        }
    });

    // Giriş Formu
    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const usernameOrEmail = document.getElementById('login-username').value;
        const password = document.getElementById('login-password').value;
        
        try {
            const res = await fetch('/api/auth/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username: usernameOrEmail, password })
            });
            const data = await res.json();
            
            if (res.ok) {
                showToast(data.success);
                state.user = data.user;
                loginForm.reset();
                showApp();
            } else {
                showToast(data.error || 'Giriş başarısız.', 'error');
            }
        } catch (err) {
            showToast('Sunucu bağlantı hatası.', 'error');
        }
    });

    // Çıkış Butonu
    logoutBtn.addEventListener('click', async () => {
        try {
            const res = await fetch('/api/auth/logout', { method: 'POST' });
            if (res.ok) {
                state.user = null;
                showToast('Başarıyla çıkış yapıldı.');
                showAuth();
            }
        } catch (err) {
            showToast('Çıkış yapılırken hata oluştu.', 'error');
        }
    });

    // Yeni Challenge Başlatma Formu
    createChallengeForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const title = document.getElementById('ch-title').value;
        const description = document.getElementById('ch-desc').value;
        const start_date = document.getElementById('ch-start').value;
        const end_date = document.getElementById('ch-end').value;
        const category = document.getElementById('ch-category').value;
        
        if (new Date(start_date) > new Date(end_date)) {
            showToast('Başlangıç tarihi bitiş tarihinden sonra olamaz!', 'error');
            return;
        }

        try {
            const res = await fetch('/api/challenges', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ title, description, start_date, end_date, category })
            });
            const data = await res.json();
            
            if (res.ok) {
                showToast(data.success);
                createChallengeForm.reset();
                
                // Eğer yeni bir rozet kazanıldıysa bildir
                if (data.new_badges && data.new_badges.length > 0) {
                    setTimeout(() => {
                        showToast(`🏆 Tebrikler! Yeni Rozet Kazandınız: ${data.new_badges.join(', ')}`, 'success');
                    }, 1000);
                }
                
                loadDashboardData();
            } else {
                showToast(data.error || 'Oluşturma başarısız.', 'error');
            }
        } catch (err) {
            showToast('Bağlantı hatası.', 'error');
        }
    });

    // --- VERİ ÇEKME & ARAYÜZ YAZDIRMA ---

    // Dashboard İstatistiklerini ve Grafiklerini Yükle
    async function loadDashboardData() {
        try {
            const res = await fetch('/api/dashboard/stats');
            const data = await res.json();
            state.stats = data;
            
            // İstatistik sayılarını güncelle
            statActiveCount.textContent = data.active_challenges;
            statCompletedCount.textContent = data.completed_challenges;
            statBadgeCount.textContent = data.badges_earned_count;
            headerStreakVal.textContent = data.longest_streak;
            
            // Veritabanı modu bilgisi
            dbModeText.textContent = `Veritabanı: ${data.db_mode}`;
            
            // Son Aktivite Listesini Doldur
            renderRecentActivities(data.recent_activities);
            
            // Hızlı Rozet listesini doldur (ilk 4 rozet)
            renderQuickBadges(data.all_badges);
            
            // Rozetler sekmesindeki detaylı listeyi doldur
            renderFullBadges(data.all_badges);
            
            // Grafiği Çiz / Güncelle
            renderCategoryChart(data.category_distribution);
            
        } catch (err) {
            console.error('Dashboard istatistikleri yüklenemedi:', err);
        }
    }

    // Son aktiviteleri HTML'e dök
    function renderRecentActivities(activities) {
        recentActivitiesList.innerHTML = '';
        if (!activities || activities.length === 0) {
            recentActivitiesList.innerHTML = '<p class="text-muted text-center">Henüz bir ilerleme kaydedilmedi.</p>';
            return;
        }
        
        activities.forEach(act => {
            const item = document.createElement('div');
            item.className = 'activity-item';
            
            const isLog = act.type === 'log';
            const iconClass = isLog ? 'fa-solid fa-check' : 'fa-solid fa-trophy';
            const bgClass = isLog ? 'act-log' : 'act-badge';
            
            item.innerHTML = `
                <div class="activity-icon ${bgClass}">
                    <i class="${iconClass}"></i>
                </div>
                <div class="activity-details">
                    <h4>${act.title}</h4>
                    <p>${act.detail}</p>
                </div>
                <div class="activity-time">${formatDateString(act.time)}</div>
            `;
            recentActivitiesList.appendChild(item);
        });
    }

    // Sol panel rozetlerini güncelle
    function renderQuickBadges(badges) {
        quickBadgesList.innerHTML = '';
        badges.forEach(badge => {
            const item = document.createElement('div');
            item.className = `q-badge-item ${badge.earned ? 'active' : ''}`;
            
            // Rozet ikon haritası
            const icon = getBadgeIcon(badge.icon_url);
            
            item.innerHTML = `
                <div class="q-badge-icon">
                    <i class="${icon}"></i>
                </div>
                <span>${badge.name}</span>
            `;
            
            // Hover detay tooltip'i ekle
            item.setAttribute('title', `${badge.name}: ${badge.description} (${badge.earned ? 'Kazanıldı' : 'Kilitli'})`);
            quickBadgesList.appendChild(item);
        });
    }

    // Tüm Rozetler sekmesini doldur
    function renderFullBadges(badges) {
        badgesGridFull.innerHTML = '';
        badges.forEach(badge => {
            const card = document.createElement('div');
            card.className = `badge-card ${badge.earned ? 'earned' : ''}`;
            
            const icon = getBadgeIcon(badge.icon_url);
            const dateText = badge.earned_at ? `<div class="badge-earned-date"><i class="fa-solid fa-calendar-check"></i> Kazanılma: ${badge.earned_at}</div>` : '';
            
            card.innerHTML = `
                <div class="badge-card-icon">
                    <i class="${icon}"></i>
                </div>
                <div class="badge-card-info">
                    <h3>${badge.name}</h3>
                    <p>${badge.description}</p>
                    ${dateText}
                </div>
            `;
            badgesGridFull.appendChild(card);
        });
    }

    // Kategori Pasta Grafiği
    function renderCategoryChart(distribution) {
        if (!distribution || distribution.length === 0) {
            // Eğer veri yoksa grafiği sıfırla veya varsayılan göster
            distribution = [{ category: 'Kayıt Yok', count: 1 }];
        }
        
        const labels = distribution.map(d => d.category);
        const counts = distribution.map(d => d.count);
        
        const chartData = {
            labels: labels,
            datasets: [{
                data: counts,
                backgroundColor: [
                    '#6366f1', // Indigo
                    '#10b981', // Zümrüt Yeşili
                    '#8b5cf6', // Mor
                    '#f59e0b', // Amber
                    '#ef4444', // Kırmızı
                    '#64748b'  // Slate Gri
                ],
                borderWidth: 0
            }]
        };

        if (categoryChart) {
            categoryChart.destroy();
        }

        const ctx = document.getElementById('categoryChart').getContext('2d');
        categoryChart = new Chart(ctx, {
            type: 'doughnut',
            data: chartData,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            color: '#94a3b8',
                            font: {
                                family: 'Inter',
                                size: 11
                            },
                            padding: 15
                        }
                    }
                },
                cutout: '70%'
            }
        });
    }

    // --- MEYDAN OKUMALAR SAYFASI ---
    async function loadChallenges() {
        try {
            const res = await fetch('/api/challenges');
            const challenges = await res.json();
            state.challenges = challenges;
            
            // Üstteki rozet sayısını güncelle
            activeChallengesBadge.textContent = `${challenges.filter(c => c.status === 'active').length} Aktif`;
            
            renderChallenges(challenges);
        } catch (err) {
            showToast('Meydan okumalar yüklenirken hata oluştu.', 'error');
        }
    }

    function renderChallenges(challenges) {
        challengesList.innerHTML = '';
        if (challenges.length === 0) {
            challengesList.innerHTML = `
                <div class="text-center text-muted" style="grid-column: 1/-1; padding: 40px;">
                    <i class="fa-solid fa-folder-open" style="font-size: 3rem; margin-bottom: 15px; display:block;"></i>
                    <p>Henüz hiç meydan okuma başlatmadınız. Kontrol panelinden hemen yeni bir hedef ekleyin!</p>
                </div>
            `;
            return;
        }

        challenges.forEach(ch => {
            const card = document.createElement('div');
            card.className = `challenge-card ${ch.status}`;
            
            // Yüzdelik İlerleme Hesaplama
            const progressPercent = ch.total_days > 0 ? Math.round((ch.completed_days / ch.total_days) * 100) : 0;
            
            // Tarihler arası dizi üret
            const datesList = getDatesBetween(ch.start_date, ch.end_date);
            
            // Log listesini key-value yap (kolay erişim için)
            const logMap = {};
            if (ch.logs) {
                ch.logs.forEach(l => {
                    logMap[l.log_date] = { status: l.status, notes: l.notes };
                });
            }
            
            // Gün düğümlerini oluştur
            let calendarHtml = '';
            const todayStr = new Date().toISOString().split('T')[0];
            
            datesList.forEach((date, index) => {
                const log = logMap[date];
                let statusClass = '';
                let iconHtml = '';
                
                if (log) {
                    statusClass = log.status; // 'completed', 'missed', 'pending'
                }
                
                const isToday = date === todayStr ? 'today' : '';
                
                calendarHtml += `
                    <div class="calendar-day-node ${statusClass} ${isToday}" 
                         data-date="${date}" 
                         data-challenge-id="${ch.id}" 
                         data-challenge-title="${escapeHtml(ch.title)}"
                         data-status="${log ? log.status : 'pending'}"
                         data-notes="${log ? escapeHtml(log.notes || '') : ''}">
                        ${index + 1}
                    </div>
                `;
            });

            // Tamamlanma durum butonları
            let statusActionBtn = '';
            if (ch.status === 'active') {
                statusActionBtn = `
                    <button class="btn-icon-success complete-challenge-btn" data-id="${ch.id}" title="Meydan Okumayı Tamamlandı Olarak İşaretle">
                        <i class="fa-solid fa-check-double"></i>
                    </button>
                `;
            }

            card.innerHTML = `
                <div class="challenge-header">
                    <div class="ch-info-area">
                        <h3>${ch.title}</h3>
                        <div class="ch-meta">
                            <span class="ch-category-badge">${ch.category}</span>
                            <span><i class="fa-solid fa-calendar"></i> ${formatDateShort(ch.start_date)} - ${formatDateShort(ch.end_date)}</span>
                            <span><i class="fa-solid fa-clock"></i> ${ch.total_days} Gün</span>
                        </div>
                    </div>
                    <div class="ch-actions">
                        ${statusActionBtn}
                        <button class="btn-icon-danger delete-challenge-btn" data-id="${ch.id}" title="Meydan Okumayı Sil">
                            <i class="fa-solid fa-trash"></i>
                        </button>
                    </div>
                </div>
                
                <p class="challenge-desc">${ch.description || 'Açıklama belirtilmemiş.'}</p>
                
                <div class="progress-area">
                    <div class="progress-labels">
                        <span>İlerleme Oranı</span>
                        <span>%${progressPercent} (${ch.completed_days}/${ch.total_days} Gün)</span>
                    </div>
                    <div class="progress-track">
                        <div class="progress-bar" style="width: ${progressPercent}%"></div>
                    </div>
                </div>
                
                <div class="calendar-section">
                    <div class="calendar-section-title">Günlük Takip Takvimi</div>
                    <div class="calendar-grid">
                        ${calendarHtml}
                    </div>
                </div>
            `;
            challengesList.appendChild(card);
        });

        // Olay dinleyicilerini bağla (Silme, Tamamlama ve Günlere tıklama)
        bindChallengeCardEvents();
    }

    function bindChallengeCardEvents() {
        // Silme İşlemi
        document.querySelectorAll('.delete-challenge-btn').forEach(btn => {
            btn.addEventListener('click', async () => {
                const id = btn.getAttribute('data-id');
                if (confirm('Bu meydan okumayı silmek istediğinize emin misiniz? Tüm günlük kayıtlar silinecektir.')) {
                    try {
                        const res = await fetch(`/api/challenges/${id}`, { method: 'DELETE' });
                        const data = await res.json();
                        if (res.ok) {
                            showToast(data.success);
                            loadChallenges();
                        } else {
                            showToast(data.error, 'error');
                        }
                    } catch (err) {
                        showToast('Silme işlemi başarısız.', 'error');
                    }
                }
            });
        });

        // Hızlı Tamamlama (Arşivleme)
        document.querySelectorAll('.complete-challenge-btn').forEach(btn => {
            btn.addEventListener('click', async () => {
                const id = btn.getAttribute('data-id');
                try {
                    const res = await fetch(`/api/challenges/${id}/status`, {
                        method: 'PUT',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ status: 'completed' })
                    });
                    const data = await res.json();
                    if (res.ok) {
                        showToast(data.success);
                        if (data.new_badges && data.new_badges.length > 0) {
                            setTimeout(() => {
                                showToast(`🏆 Tebrikler! Yeni Rozet Kazandınız: ${data.new_badges.join(', ')}`, 'success');
                            }, 1000);
                        }
                        loadChallenges();
                    } else {
                        showToast(data.error, 'error');
                    }
                } catch (err) {
                    showToast('İşlem başarısız.', 'error');
                }
            });
        });

        // Takvim Gününe Tıklama (Günlük Kayıt Ekleme Modalı Açma)
        document.querySelectorAll('.calendar-day-node').forEach(node => {
            node.addEventListener('click', () => {
                const chId = node.getAttribute('data-challenge-id');
                const chTitle = node.getAttribute('data-challenge-title');
                const date = node.getAttribute('data-date');
                const status = node.getAttribute('data-status');
                const notes = node.getAttribute('data-notes');
                
                // Modalı yapılandır
                logChallengeId.value = chId;
                logDateInput.value = date;
                logDateDisplay.textContent = `${chTitle} - ${formatDateShort(date)}`;
                logNotes.value = notes || '';
                
                // Durum radyo butonunu seç
                const radio = logForm.querySelector(`input[name="log-status"][value="${status}"]`);
                if (radio) {
                    radio.checked = true;
                }
                
                // Modalı göster
                logModal.classList.add('active');
            });
        });
    }

    // Modal Kapatma Olayları
    closeModalBtn.addEventListener('click', () => {
        logModal.classList.remove('active');
    });

    logModal.addEventListener('click', (e) => {
        if (e.target === logModal) {
            logModal.classList.remove('active');
        }
    });

    // İlerleme Logu Kayıt Formu
    logForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const chId = logChallengeId.value;
        const logDate = logDateInput.value;
        const status = logForm.querySelector('input[name="log-status"]:checked').value;
        const notes = logNotes.value;
        
        try {
            const res = await fetch(`/api/challenges/${chId}/log`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ log_date: logDate, status, notes })
            });
            const data = await res.json();
            
            if (res.ok) {
                showToast(data.success);
                logModal.classList.remove('active');
                
                // Yeni rozet kazanıldıysa bildir
                if (data.new_badges && data.new_badges.length > 0) {
                    setTimeout(() => {
                        showToast(`🏆 Tebrikler! Yeni Rozet Kazandınız: ${data.new_badges.join(', ')}`, 'success');
                    }, 1000);
                }
                
                // Listeyi ve dashboard'u güncelle
                loadChallenges();
            } else {
                showToast(data.error, 'error');
            }
        } catch (err) {
            showToast('Bağlantı hatası.', 'error');
        }
    });


    // --- YARDIMCI (HELPER) FONKSİYONLAR ---

    // İki tarih arasındaki günleri listele
    function getDatesBetween(startDateStr, endDateStr) {
        const dates = [];
        let curr = new Date(startDateStr);
        const end = new Date(endDateStr);
        
        // Zaman dilimi hatalarını önlemek için UTC saatini sıfırla
        curr.setHours(0,0,0,0);
        end.setHours(0,0,0,0);
        
        while (curr <= end) {
            dates.push(new Date(curr).toISOString().split('T')[0]);
            curr.setDate(curr.getDate() + 1);
        }
        return dates;
    }

    // Kısa Tarih Formatlama (Örn: 2026-06-10 -> 10 Haz 2026)
    function formatDateShort(dateStr) {
        if (!dateStr) return '';
        const date = new Date(dateStr);
        return date.toLocaleDateString('tr-TR', { day: 'numeric', month: 'short', year: 'numeric' });
    }

    // Detaylı Tarih/Saat Formatlama
    function formatDateString(dateTimeStr) {
        if (!dateTimeStr) return '';
        try {
            const date = new Date(dateTimeStr.replace(' ', 'T')); // SQLite format uyumluluğu için
            if (isNaN(date.getTime())) return dateTimeStr;
            return date.toLocaleDateString('tr-TR', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' });
        } catch (e) {
            return dateTimeStr;
        }
    }

    // Rozet İkon Haritalaması
    function getBadgeIcon(iconName) {
        const iconMap = {
            'badge_first_step': 'fa-solid fa-shoe-prints',
            'badge_streak_3': 'fa-solid fa-fire',
            'badge_streak_7': 'fa-solid fa-bolt',
            'badge_completed': 'fa-solid fa-flag-checkered'
        };
        return iconMap[iconName] || 'fa-solid fa-award';
    }

    // HTML Kaçış Karakteri Temizleme (XSS Önleme)
    function escapeHtml(text) {
        if (!text) return '';
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return text.toString().replace(/[&<>"']/g, function(m) { return map[m]; });
    }

    // --- UYGULAMAYI BAŞLAT ---
    checkAuth();
});
