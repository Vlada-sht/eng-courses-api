/**
 * English Courses Platform Frontend
 * Handles Single Page App (SPA) navigation, JWT auth lifecycle,
 * automatic token refreshing, teacher catalog, detailed profile modal,
 * and protected student bookings dashboard.
 */

const API_BASE = 'http://127.0.0.1:8000/api';

// State
let allTeachers = [];
let redirectAfterLogin = null;

// ==========================================
// 1. JWT & API Client with Auto-Refresh
// ==========================================

function getAccessToken() {
  return localStorage.getItem('access_token');
}

function getRefreshToken() {
  return localStorage.getItem('refresh_token');
}

function setTokens(access, refresh) {
  if (access) localStorage.setItem('access_token', access);
  if (refresh) localStorage.setItem('refresh_token', refresh);
}

function getUser() {
  const userStr = localStorage.getItem('user');
  try {
    return userStr ? JSON.parse(userStr) : null;
  } catch (e) {
    return null;
  }
}

function setUser(user) {
  localStorage.setItem('user', JSON.stringify(user));
}

function clearAuth() {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  localStorage.removeItem('user');
}

function isAuthenticated() {
  return !!getAccessToken();
}

/**
 * Universal fetch wrapper that handles:
 * - JSON serialization
 * - Authorization Bearer header
 * - Automatic JWT token refresh on 401 Unauthorized
 */
async function apiRequest(endpoint, options = {}, isRetry = false) {
  const url = endpoint.startsWith('http') ? endpoint : `${API_BASE}${endpoint}`;
  const headers = options.headers || {};

  if (!headers['Content-Type'] && !(options.body instanceof FormData)) {
    headers['Content-Type'] = 'application/json';
  }

  const token = getAccessToken();
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  try {
    const response = await fetch(url, { ...options, headers });

    // Handle 401 Unauthorized - Attempt Refresh
    if (response.status === 401 && !isRetry && getRefreshToken() && !endpoint.includes('/users/login') && !endpoint.includes('/users/token/refresh')) {
      const refreshed = await refreshAccessToken();
      if (refreshed) {
        // Retry the original request once with the new access token
        return apiRequest(endpoint, options, true);
      } else {
        // Refresh token expired or invalid -> log out
        handleLogout(false);
        showAlert('Сесію завершено. Будь ласка, увійдіть знову.', 'error');
        navigateTo('login');
        return { ok: false, status: 401, data: { error: 'Сесію завершено' } };
      }
    }

    let data = null;
    const contentType = response.headers.get('content-type');
    if (contentType && contentType.includes('application/json')) {
      data = await response.json();
    } else {
      data = await response.text();
    }

    return {
      ok: response.ok,
      status: response.status,
      data: data
    };
  } catch (err) {
    console.error(`API request error on ${endpoint}:`, err);
    return {
      ok: false,
      status: 0,
      data: { error: 'Не вдалося з’єднатися з сервером. Перевірте роботу Django сервера.' }
    };
  }
}

/**
 * Refresh the JWT access token using the refresh token
 */
async function refreshAccessToken() {
  const refreshToken = getRefreshToken();
  if (!refreshToken) return false;

  try {
    const res = await fetch(`${API_BASE}/users/token/refresh/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh: refreshToken })
    });

    if (res.ok) {
      const data = await res.json();
      setTokens(data.access, data.refresh);
      console.log('JWT Access Token refreshed successfully');
      return true;
    }
  } catch (err) {
    console.error('Failed to refresh access token:', err);
  }
  return false;
}

// ==========================================
// 2. Navigation & Router
// ==========================================

function navigateTo(page) {
  // Guard protected routes
  if (page === 'dashboard' && !isAuthenticated()) {
    redirectAfterLogin = 'dashboard';
    showAlert('Для доступу до кабінету необхідно увійти в систему.', 'error');
    navigateTo('login');
    return;
  }

  // Guard guest-only routes
  if ((page === 'login' || page === 'register') && isAuthenticated()) {
    navigateTo('dashboard');
    return;
  }

  // Hide all sections
  document.querySelectorAll('.page-section').forEach(sec => sec.classList.add('hidden'));

  // Show target section
  const targetId = `page${page.charAt(0).toUpperCase() + page.slice(1)}`;
  const targetEl = document.getElementById(targetId);
  if (targetEl) {
    targetEl.classList.remove('hidden');
  }

  // Update active nav button
  document.querySelectorAll('.nav-btn').forEach(btn => btn.classList.remove('active'));
  const activeBtn = document.getElementById(`nav${page.charAt(0).toUpperCase() + page.slice(1)}`);
  if (activeBtn) activeBtn.classList.add('active');

  // Trigger page-specific loads
  if (page === 'home') {
    loadTeachers();
    loadCourses();
  } else if (page === 'dashboard') {
    loadUserProfile();
    loadUserBookings();
  }

  window.location.hash = page;
}

// ==========================================
// 3. UI Helpers & Auth Controls
// ==========================================

function updateNavbar() {
  const authContainer = document.getElementById('authControls');
  if (!authContainer) return;

  if (isAuthenticated()) {
    const user = getUser() || {};
    const displayName = user.first_name || user.username || 'Користувач';
    authContainer.innerHTML = `
      <div class="user-pill">
        <span>👤 ${escapeHtml(displayName)}</span>
        <span class="badge badge-success">${escapeHtml(user.role || 'student')}</span>
      </div>
      <button class="btn btn-secondary btn-sm" onclick="handleLogout(true)">Вийти</button>
    `;
  } else {
    authContainer.innerHTML = `
      <button class="btn btn-secondary btn-sm" onclick="navigateTo('login')">Увійти</button>
      <button class="btn btn-primary btn-sm" onclick="navigateTo('register')">Зареєструватися</button>
    `;
  }
}

function showAlert(message, type = 'success') {
  const alertBox = document.getElementById('alertBox');
  if (!alertBox) return;

  alertBox.className = `alert-box alert-${type}`;
  alertBox.innerHTML = `
    <span>${escapeHtml(message)}</span>
    <button style="background:none; border:none; cursor:pointer; font-weight:bold;" onclick="hideAlert()">✕</button>
  `;
  alertBox.classList.remove('hidden');

  setTimeout(() => {
    hideAlert();
  }, 5000);
}

function hideAlert() {
  const alertBox = document.getElementById('alertBox');
  if (alertBox) alertBox.classList.add('hidden');
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

// ==========================================
// 4. Public Catalog: Teachers & Courses
// ==========================================

async function loadTeachers() {
  const grid = document.getElementById('teachersGrid');
  if (!grid) return;

  const spec = document.getElementById('filterSpecialization')?.value || '';
  const level = document.getElementById('filterLevel')?.value || '';

  let query = [];
  if (spec) query.push(`specialization=${encodeURIComponent(spec)}`);
  if (level) query.push(`english_level=${encodeURIComponent(level)}`);
  const qs = query.length > 0 ? `?${query.join('&')}` : '';

  grid.innerHTML = '<div class="loading-spinner">Оновлення списку викладачів...</div>';

  const res = await apiRequest(`/teachers/${qs}`);
  if (res.ok && Array.isArray(res.data)) {
    allTeachers = res.data;
    if (res.data.length === 0) {
      grid.innerHTML = '<p class="text-muted" style="grid-column: 1/-1;">Викладачів за обраними фільтрами не знайдено.</p>';
      return;
    }

    grid.innerHTML = res.data.map(t => `
      <div class="card">
        <div class="card-header">
          <div>
            <h3 class="card-title">${escapeHtml(t.name)}</h3>
            <div class="card-spec">${escapeHtml(t.specialization || 'General English')}</div>
          </div>
          <span class="card-badge">${escapeHtml(t.english_level || 'C2')}</span>
        </div>
        <p class="card-bio">${escapeHtml(t.bio || 'Досвідчений репетитор англійської мови.')}</p>
        <div class="card-footer">
          <div>
            <span class="card-price">${t.price_per_hour} грн</span> / год
            <div style="font-size: 0.8rem; color: #64748b;">★ ${t.rating} (досвід: ${t.experience_years} р.)</div>
          </div>
          <button class="btn btn-secondary btn-sm" onclick="openTeacherModal(${t.id})">Детальніше & Уроки</button>
        </div>
      </div>
    `).join('');
  } else {
    grid.innerHTML = '<p class="text-danger">Помилка завантаження викладачів.</p>';
  }
}

async function loadCourses() {
  const grid = document.getElementById('coursesGrid');
  if (!grid) return;

  const res = await apiRequest('/courses/');
  if (res.ok && Array.isArray(res.data)) {
    if (res.data.length === 0) {
      grid.innerHTML = '<p class="text-muted" style="grid-column: 1/-1;">Курсів поки що немає.</p>';
      return;
    }

    grid.innerHTML = res.data.map(c => `
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">${escapeHtml(c.title)}</h3>
          <span class="card-badge">${escapeHtml(c.english_level || c.level || 'B2')}</span>
        </div>
        <p class="card-bio">${escapeHtml(c.description)}</p>
        <div style="font-size: 0.85rem; color: #475569; margin-bottom: 12px;">
          👨‍🏫 Викладач: <strong>${escapeHtml(c.teacher_name || 'Не вказано')}</strong><br>
          📁 Категорія: <em>${escapeHtml(c.category_name || 'Загальна')}</em>
        </div>
        <div class="card-footer">
          <span class="card-price">${c.price} грн</span>
          <button class="btn btn-primary btn-sm" onclick="bookFromCourse(${c.teacher})">Записатися</button>
        </div>
      </div>
    `).join('');
  }
}

function resetFilters() {
  if (document.getElementById('filterSpecialization')) document.getElementById('filterSpecialization').value = '';
  if (document.getElementById('filterLevel')) document.getElementById('filterLevel').value = '';
  loadTeachers();
}

// ==========================================
// 5. Detailed Teacher Profile Modal
// ==========================================

async function openTeacherModal(teacherId) {
  const modal = document.getElementById('teacherModal');
  const body = document.getElementById('modalTeacherBody');
  const title = document.getElementById('modalTeacherName');
  if (!modal || !body) return;

  modal.classList.remove('hidden');
  body.innerHTML = '<div class="loading-spinner">Завантаження повного профілю...</div>';

  const res = await apiRequest(`/teachers/${teacherId}/`);
  if (res.ok && res.data) {
    const t = res.data;
    title.textContent = `${t.name} — Профіль`;

    let coursesHtml = '<p class="text-muted">Курсів не знайдено.</p>';
    if (t.courses && t.courses.length > 0) {
      coursesHtml = t.courses.map(c => `
        <div style="padding: 8px 12px; background: #f8fafc; border-radius: 6px; margin-bottom: 6px;">
          <strong>${escapeHtml(c.title)}</strong> (Рівень: ${c.english_level || c.level}, Ціна: ${c.price} грн)
        </div>
      `).join('');
    }

    let lessonsHtml = '<p class="text-muted">Запланованих занять поки немає.</p>';
    if (t.lessons && t.lessons.length > 0) {
      lessonsHtml = t.lessons.map(l => `
        <div style="padding: 10px 14px; border: 1px solid #e2e8f0; border-radius: 6px; margin-bottom: 8px; display:flex; justify-content:space-between; align-items:center;">
          <div>
            <strong>${escapeHtml(l.title)}</strong> (${escapeHtml(l.lesson_type)})<br>
            <span style="font-size:0.85rem; color:#64748b;">📅 ${l.date} о ${l.time} • Рівень: ${l.english_level} • ${l.price} грн</span>
          </div>
          <button class="btn btn-primary btn-sm" onclick="bookSpecificLesson(${t.id}, '${l.lesson_type}', '${l.date}', '${l.time}', ${l.id})">Забронювати</button>
        </div>
      `).join('');
    }

    body.innerHTML = `
      <div style="margin-bottom: 20px;">
        <p><strong>Спеціалізація:</strong> ${escapeHtml(t.specialization)}</p>
        <p><strong>Рівень володіння мовою (english_level):</strong> <span class="badge badge-success">${escapeHtml(t.english_level)}</span></p>
        <p><strong>Ціна:</strong> ${t.price_per_hour} грн / год | <strong>Рейтинг:</strong> ★ ${t.rating} | <strong>Досвід:</strong> ${t.experience_years} років</p>
        <p><strong>Email:</strong> ${escapeHtml(t.email)}</p>
        <p style="margin-top: 10px;"><strong>Про себе:</strong><br>${escapeHtml(t.bio || 'Немає опису.')}</p>
      </div>

      <h4 style="margin-bottom: 8px;">Курси викладача (${t.courses_count || 0})</h4>
      <div style="margin-bottom: 20px;">${coursesHtml}</div>

      <h4 style="margin-bottom: 8px;">Доступні заняття викладача (${t.lessons_count || 0})</h4>
      <div>${lessonsHtml}</div>

      <div style="margin-top: 24px; text-align: right;">
        <button class="btn btn-primary" onclick="closeTeacherModal(); openBookingModal(${t.id})">Забронювати індивідуальне заняття</button>
      </div>
    `;
  } else {
    body.innerHTML = '<p class="text-danger">Не вдалося завантажити профіль викладача.</p>';
  }
}

function closeTeacherModal() {
  const modal = document.getElementById('teacherModal');
  if (modal) modal.classList.add('hidden');
}

// ==========================================
// 6. Auth Handlers: Login, Register, Logout
// ==========================================

async function handleLogin(e) {
  e.preventDefault();
  const username = document.getElementById('loginUsername').value.trim();
  const password = document.getElementById('loginPassword').value;
  const errBox = document.getElementById('loginError');
  const btn = document.getElementById('loginBtn');

  errBox.classList.add('hidden');
  btn.disabled = true;
  btn.textContent = 'Вхід...';

  const res = await apiRequest('/users/login/', {
    method: 'POST',
    body: JSON.stringify({ username, password })
  });

  btn.disabled = false;
  btn.textContent = 'Увійти';

  if (res.ok && res.data) {
    setTokens(res.data.access, res.data.refresh);
    setUser(res.data.user);
    updateNavbar();
    showAlert('Успішний вхід у систему!', 'success');

    const dest = redirectAfterLogin || 'dashboard';
    redirectAfterLogin = null;
    navigateTo(dest);
  } else {
    errBox.textContent = res.data?.error || 'Помилка авторизації. Перевірте логін та пароль.';
    errBox.classList.remove('hidden');
  }
}

async function handleRegister(e) {
  e.preventDefault();
  const errBox = document.getElementById('generalRegisterError');
  const btn = document.getElementById('registerBtn');

  // Clear previous field errors
  document.querySelectorAll('.field-error').forEach(el => el.textContent = '');
  errBox.classList.add('hidden');

  const payload = {
    username: document.getElementById('regUsername').value.trim(),
    email: document.getElementById('regEmail').value.trim(),
    first_name: document.getElementById('regFirstName').value.trim(),
    last_name: document.getElementById('regLastName').value.trim(),
    password: document.getElementById('regPassword').value,
    password_confirm: document.getElementById('regPasswordConfirm').value,
    english_level: document.getElementById('regEnglishLevel').value,
    role: 'student'
  };

  btn.disabled = true;
  btn.textContent = 'Реєстрація...';

  const res = await apiRequest('/users/register/', {
    method: 'POST',
    body: JSON.stringify(payload)
  });

  btn.disabled = false;
  btn.textContent = 'Зареєструватися';

  if (res.ok && res.data) {
    if (res.data.tokens) {
      setTokens(res.data.tokens.access, res.data.tokens.refresh);
    }
    if (res.data.user) {
      setUser(res.data.user);
    }
    updateNavbar();
    showAlert('Реєстрація успішна! Ласкаво просимо на платформу.', 'success');

    const dest = redirectAfterLogin || 'dashboard';
    redirectAfterLogin = null;
    navigateTo(dest);
  } else {
    // Show field-specific 400 validation errors
    if (res.data?.details && typeof res.data.details === 'object') {
      for (const [field, messages] of Object.entries(res.data.details)) {
        const fieldErrEl = document.getElementById(`err_${field}`);
        if (fieldErrEl) {
          fieldErrEl.textContent = Array.isArray(messages) ? messages.join(' ') : String(messages);
        }
      }
    }
    errBox.textContent = res.data?.error || 'Помилка валідації. Перевірте заповнені поля.';
    errBox.classList.remove('hidden');
  }
}

async function handleLogout(callServer = true) {
  if (callServer && getRefreshToken()) {
    try {
      await apiRequest('/users/logout/', {
        method: 'POST',
        body: JSON.stringify({ refresh: getRefreshToken() })
      });
    } catch (e) {
      console.warn('Logout request completed with warning:', e);
    }
  }

  clearAuth();
  updateNavbar();
  showAlert('Ви успішно вийшли з акаунта.', 'success');
  navigateTo('home');
}

// ==========================================
// 7. Protected Dashboard & Bookings
// ==========================================

async function loadUserProfile() {
  const user = getUser();
  if (user) {
    document.getElementById('profUsername').textContent = user.username || '-';
    document.getElementById('profEmail').textContent = user.email || '-';
    document.getElementById('profFullName').textContent = `${user.first_name || ''} ${user.last_name || ''}`.trim() || '-';
    document.getElementById('profLevel').textContent = user.english_level || 'B2';
    document.getElementById('profRole').textContent = user.role || 'student';
  }

  // Fetch fresh profile from API
  const res = await apiRequest('/users/me/');
  if (res.ok && res.data) {
    setUser(res.data);
    document.getElementById('profUsername').textContent = res.data.username || '-';
    document.getElementById('profEmail').textContent = res.data.email || '-';
    document.getElementById('profFullName').textContent = `${res.data.first_name || ''} ${res.data.last_name || ''}`.trim() || '-';
    document.getElementById('profLevel').textContent = res.data.english_level || 'B2';
    document.getElementById('profRole').textContent = res.data.role || 'student';
  }
}

async function loadUserBookings() {
  const container = document.getElementById('bookingsList');
  if (!container) return;

  container.innerHTML = '<div class="loading-spinner">Отримання заброньованих занять...</div>';

  const res = await apiRequest('/users/me/bookings/');
  if (res.ok && Array.isArray(res.data)) {
    if (res.data.length === 0) {
      container.innerHTML = '<p class="text-muted">У вас поки немає заброньованих занять. Натисніть "+ Забронювати нове заняття".</p>';
      return;
    }

    container.innerHTML = res.data.map(b => {
      const isCancelled = b.status === 'cancelled';
      const statusBadge = isCancelled
        ? '<span class="badge badge-danger">Скасовано</span>'
        : '<span class="badge badge-success">Підтверджено</span>';

      return `
        <div class="booking-item">
          <div class="booking-info">
            <h4>${escapeHtml(b.lesson_type)} з ${escapeHtml(b.teacher_name)}</h4>
            <p>📅 <strong>${b.date}</strong> о <strong>${b.time}</strong></p>
            ${b.notes ? `<p style="font-size:0.8rem; margin-top:4px;"><em>Побажання: ${escapeHtml(b.notes)}</em></p>` : ''}
          </div>
          <div style="display:flex; align-items:center; gap:12px;">
            ${statusBadge}
            ${!isCancelled ? `<button class="btn btn-danger btn-sm" onclick="cancelBooking(${b.id || b.booking_id})">Скасувати</button>` : ''}
          </div>
        </div>
      `;
    }).join('');
  } else {
    container.innerHTML = '<p class="text-danger">Помилка завантаження бронювань.</p>';
  }
}

async function cancelBooking(bookingId) {
  if (!confirm('Ви дійсно бажаєте скасувати це бронювання?')) return;

  const res = await apiRequest(`/bookings/${bookingId}/`, { method: 'DELETE' });
  if (res.ok) {
    showAlert('Бронювання успішно скасовано!', 'success');
    loadUserBookings();
  } else {
    showAlert(res.data?.error || 'Помилка скасування бронювання.', 'error');
  }
}

// ==========================================
// 8. Booking Modal & Flow
// ==========================================

async function populateTeacherSelect(selectedId = null) {
  const select = document.getElementById('bookTeacherSelect');
  if (!select) return;

  if (allTeachers.length === 0) {
    const res = await apiRequest('/teachers/');
    if (res.ok && Array.isArray(res.data)) {
      allTeachers = res.data;
    }
  }

  select.innerHTML = '<option value="">-- Оберіть репетитора --</option>' +
    allTeachers.map(t => `<option value="${t.id}" ${t.id === selectedId ? 'selected' : ''}>${escapeHtml(t.name)} (${t.specialization}, ${t.english_level}) — ${t.price_per_hour} грн/год</option>`).join('');
}

function openBookingModal(teacherId = null) {
  if (!isAuthenticated()) {
    redirectAfterLogin = 'dashboard';
    showAlert('Будь ласка, увійдіть, щоб забронювати заняття.', 'error');
    navigateTo('login');
    return;
  }

  const modal = document.getElementById('bookingModal');
  if (!modal) return;

  populateTeacherSelect(teacherId);

  // Set default date to tomorrow
  const tomorrow = new Date();
  tomorrow.setDate(tomorrow.getDate() + 1);
  const dateInput = document.getElementById('bookDate');
  if (dateInput) {
    dateInput.value = tomorrow.toISOString().split('T')[0];
    dateInput.min = new Date().toISOString().split('T')[0];
  }

  document.getElementById('bookingError')?.classList.add('hidden');
  modal.classList.remove('hidden');
}

function closeBookingModal() {
  const modal = document.getElementById('bookingModal');
  if (modal) modal.classList.add('hidden');
}

function bookFromCourse(teacherId) {
  openBookingModal(teacherId);
}

function bookSpecificLesson(teacherId, lessonType, date, time, lessonId) {
  closeTeacherModal();
  openBookingModal(teacherId);

  if (document.getElementById('bookLessonType')) document.getElementById('bookLessonType').value = lessonType;
  if (document.getElementById('bookDate')) document.getElementById('bookDate').value = date;
  if (document.getElementById('bookTime')) document.getElementById('bookTime').value = time;
}

function onTeacherSelectChange() {
  // Can be extended to load teacher specific slots
}

async function handleCreateBooking(e) {
  e.preventDefault();
  const btn = document.getElementById('submitBookingBtn');
  const errBox = document.getElementById('bookingError');
  errBox.classList.add('hidden');

  const teacher_id = parseInt(document.getElementById('bookTeacherSelect').value);
  const lesson_type = document.getElementById('bookLessonType').value;
  const date = document.getElementById('bookDate').value;
  const time = document.getElementById('bookTime').value;
  const notes = document.getElementById('bookNotes').value.trim();

  if (!teacher_id) {
    errBox.textContent = 'Будь ласка, оберіть викладача.';
    errBox.classList.remove('hidden');
    return;
  }

  btn.disabled = true;
  btn.textContent = 'Бронювання...';

  const res = await apiRequest('/bookings/', {
    method: 'POST',
    body: JSON.stringify({ teacher_id, lesson_type, date, time, notes })
  });

  btn.disabled = false;
  btn.textContent = 'Підтвердити бронювання';

  if (res.ok) {
    closeBookingModal();
    showAlert('Заняття успішно заброньовано!', 'success');
    navigateTo('dashboard');
  } else {
    errBox.textContent = res.data?.error || 'Помилка при створенні бронювання.';
    errBox.classList.remove('hidden');
  }
}

// ==========================================
// 9. Initial App Bootstrap
// ==========================================

document.addEventListener('DOMContentLoaded', () => {
  updateNavbar();

  // Route based on URL hash
  const initialHash = window.location.hash.replace('#', '') || 'home';
  navigateTo(initialHash);

  window.addEventListener('hashchange', () => {
    const page = window.location.hash.replace('#', '') || 'home';
    navigateTo(page);
  });
});

