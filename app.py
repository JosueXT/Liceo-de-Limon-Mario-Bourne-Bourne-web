"""
==============================================================================
SERVIDOR PRINCIPAL (FLASK) - LICEO DE LIMÓN MARIO BOURNE BOURNE (MEP)
==============================================================================
"""

import os
import time
import secrets
from datetime import timedelta
from collections import defaultdict
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, Response, send_from_directory
from email_service import load_env_file, check_smtp_health
from database import (
    init_db,
    get_all_content,
    update_bulk_content,
    get_all_news,
    get_news_by_id,
    add_news,
    update_news,
    delete_news,
    add_inquiry,
    get_all_inquiries,
    update_inquiry_status,
    delete_inquiry,
    reset_to_defaults,
    create_snapshot,
    get_all_snapshots,
    get_snapshot_by_id,
    import_snapshot,
    restore_snapshot,
    delete_snapshot,
    export_full_database,
    get_system_health,
    get_admin_user,
    verify_admin_credentials,
    update_admin_credentials,
    reset_admin_password_with_recovery,
    reset_admin_password_direct,
    verify_recovery_key,
    create_password_reset_otp,
    verify_and_consume_otp,
    get_admin_recovery_email
)
from seed_data import MODALIDADES_DETALLE

# Cargar variables de entorno desde .env antes de inicializar servicios
load_env_file()

app = Flask(__name__)

# Clave secreta criptográfica para firmar sesiones seguras (no predecible)
secret_key = os.environ.get('SECRET_KEY')
if not secret_key:
    secret_key = secrets.token_hex(32)
app.secret_key = secret_key

# Configuración endurecida de cookies de sesión (Ciberseguridad OWASP)
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    SESSION_COOKIE_SECURE=bool(os.environ.get('RENDER') or os.environ.get('FLASK_ENV') == 'production'),
    PERMANENT_SESSION_LIFETIME=timedelta(hours=8)
)

@app.after_request
def add_security_headers(response):
    """Agrega cabeceras de seguridad HTTP endurecidas según estándares OWASP."""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Permissions-Policy'] = 'camera=(), microphone=(), geolocation=(), payment=()'
    
    # HSTS para forzar conexiones HTTPS cifradas en producción (Render)
    if os.environ.get('RENDER') or os.environ.get('FLASK_ENV') == 'production':
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains; preload'

    # Content Security Policy (permite fuentes de Google, recursos del MEP, YouTube y Unsplash)
    csp_directives = [
        "default-src 'self'",
        "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net",
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
        "font-src 'self' https://fonts.gstatic.com data:",
        "img-src 'self' data: https: blob:",
        "frame-src 'self' https://www.youtube.com https://www.youtube-nocookie.com",
        "connect-src 'self' https:"
    ]
    response.headers['Content-Security-Policy'] = "; ".join(csp_directives)
    return response

# =============================================================================
# ESCUDO DE SEGURIDAD (PROTECCIÓN CONTRA FUERZA BRUTA Y RATE LIMITING)
# =============================================================================
class SecurityShield:
    """Controlador en memoria para mitigar ataques de fuerza bruta y abusos de autenticación."""
    def __init__(self):
        self.failed_attempts = defaultdict(list)
        self.request_history = defaultdict(list)

    def is_locked(self, ip, action, max_attempts=5, window_seconds=600):
        now = time.time()
        self.failed_attempts[(ip, action)] = [
            t for t in self.failed_attempts[(ip, action)] if now - t < window_seconds
        ]
        if len(self.failed_attempts[(ip, action)]) >= max_attempts:
            oldest = self.failed_attempts[(ip, action)][0]
            remaining = int(window_seconds - (now - oldest))
            return True, max(1, remaining)
        return False, 0

    def record_failure(self, ip, action):
        self.failed_attempts[(ip, action)].append(time.time())

    def reset_failures(self, ip, action):
        self.failed_attempts.pop((ip, action), None)

    def is_rate_limited(self, ip, action, max_requests=4, window_seconds=600):
        now = time.time()
        self.request_history[(ip, action)] = [
            t for t in self.request_history[(ip, action)] if now - t < window_seconds
        ]
        if len(self.request_history[(ip, action)]) >= max_requests:
            oldest = self.request_history[(ip, action)][0]
            remaining = int(window_seconds - (now - oldest))
            return True, max(1, remaining)
        self.request_history[(ip, action)].append(now)
        return False, 0

    def reset_all(self):
        self.failed_attempts.clear()
        self.request_history.clear()

security_shield = SecurityShield()

def get_client_ip():
    """Obtiene la IP pública real del cliente considerando proxies inversos o balanceadores."""
    forwarded = request.headers.get('X-Forwarded-For')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.remote_addr or '127.0.0.1'

# Inicialización perezosa de Base de Datos (se ejecuta dentro del worker de Gunicorn para evitar deadlocks de Tokio/Rust)
_db_setup_done = False

@app.before_request
def setup_db_on_first_request():
    global _db_setup_done
    if not _db_setup_done:
        try:
            init_db()
        except Exception as e:
            print(f"[ADVERTENCIA] Error inicializando BD: {e}")
        _db_setup_done = True

def get_modality_dynamic_lists(slug, cms):
    """Extrae las listas dinámicas y editables para una modalidad (ventajas, requisitos, malla, pilares)."""
    advantages = []
    for i in range(1, 60):
        val = cms.get(f"{slug}_adv_{i}", "").strip()
        if val:
            advantages.append({
                'index': len(advantages) + 1,
                'key': f"{slug}_adv_{len(advantages) + 1}",
                'text': val
            })

    requirements = []
    for i in range(1, 60):
        val = cms.get(f"{slug}_req_{i}", "").strip()
        if val:
            requirements.append({
                'index': len(requirements) + 1,
                'key': f"{slug}_req_{len(requirements) + 1}",
                'text': val
            })

    curriculum = []
    for i in range(1, 60):
        grp = cms.get(f"{slug}_curr_group_{i}", "").strip()
        sub = cms.get(f"{slug}_curr_subject_{i}", "").strip()
        if grp or sub:
            c_idx = len(curriculum) + 1
            curriculum.append({
                'index': c_idx,
                'group_key': f"{slug}_curr_group_{c_idx}",
                'group': grp,
                'subject_key': f"{slug}_curr_subject_{c_idx}",
                'subject': sub
            })

    pillars = []
    for i in range(1, 60):
        title = cms.get(f"{slug}_pillar{i}_title", "").strip()
        desc = cms.get(f"{slug}_pillar{i}_desc", "").strip()
        if title or desc:
            p_idx = len(pillars) + 1
            pillars.append({
                'index': p_idx,
                'num': f"{p_idx:02d}",
                'title_key': f"{slug}_pillar{p_idx}_title",
                'title': title,
                'desc_key': f"{slug}_pillar{p_idx}_desc",
                'desc': desc
            })

    return {
        'advantages': advantages,
        'requirements': requirements,
        'curriculum': curriculum,
        'pillars': pillars
    }

def get_pathway_features(cms):
    """Extrae las listas dinámicas de pilares formativos en las tarjetas de inicio (regular, french, ib)."""
    cards = ['regular', 'french', 'ib']
    features = {card: [] for card in cards}
    for card in cards:
        for i in range(1, 60):
            val = cms.get(f"{card}_feature_{i}", "").strip()
            if val:
                features[card].append({
                    'index': len(features[card]) + 1,
                    'key': f"{card}_feature_{len(features[card]) + 1}",
                    'text': val
                })
    return features

def get_campus_dynamic_list(cms):
    """Extrae la lista dinámica de espacios educativos y vida estudiantil para #instalaciones."""
    items = []
    for i in range(1, 60):
        title = cms.get(f"campus_item_{i}_title", "").strip()
        desc = cms.get(f"campus_item_{i}_desc", "").strip()
        icon = cms.get(f"campus_item_{i}_icon", "").strip()
        if title or desc:
            c_idx = len(items) + 1
            items.append({
                'index': c_idx,
                'title_key': f"campus_item_{c_idx}_title",
                'title': title,
                'desc_key': f"campus_item_{c_idx}_desc",
                'desc': desc,
                'icon_key': f"campus_item_{c_idx}_icon",
                'icon': icon or '🏫'
            })

    # Si no hay registrados en base de datos aún, usar los 4 valores por defecto
    if not items:
        defaults = [
            ("🔬", "Laboratorio de Computación", "Espacios equipados para física, química, biología y tecnologías digitales MEP."),
            ("📚", "Biblioteca y Centro de Recursos", "Contenido bliográfico, áreas de estudio silencioso y acceso a bases de datos académicas."),
            ("🏀", "Áreas Deportivas", "Cancha multiuso para atletismo, baloncesto, voleibol y fútbol."),
            ("🎷", "Salón de Expresión Artística y Banda", "Cuna de la reconocida Banda del Liceo de Limón y talleres de música.")
        ]
        for idx, (default_icon, default_title, default_desc) in enumerate(defaults, 1):
            items.append({
                'index': idx,
                'title_key': f"campus_item_{idx}_title",
                'title': cms.get(f"campus_item_{idx}_title", default_title),
                'desc_key': f"campus_item_{idx}_desc",
                'desc': cms.get(f"campus_item_{idx}_desc", default_desc),
                'icon_key': f"campus_item_{idx}_icon",
                'icon': cms.get(f"campus_item_{idx}_icon", default_icon)
            })
    return items

def get_developers_dynamic_list(cms):
    """Extrae la lista dinámica de desarrolladores para la subpágina /desarrolladores."""
    items = []
    for i in range(1, 60):
        name = cms.get(f"dev_item_{i}_name", "").strip()
        role = cms.get(f"dev_item_{i}_role", "").strip()
        if name or role:
            c_idx = len(items) + 1
            items.append({
                'index': c_idx,
                'name_key': f"dev_item_{c_idx}_name",
                'name': name or f"Desarrollador {c_idx}",
                'role_key': f"dev_item_{c_idx}_role",
                'role': role or "Desarrollador Web",
                'year_key': f"dev_item_{c_idx}_year",
                'year': cms.get(f"dev_item_{i}_year", "Generación 2026").strip() or "Generación 2026",
                'bio_key': f"dev_item_{c_idx}_bio",
                'bio': cms.get(f"dev_item_{i}_bio", "").strip(),
                'photo_key': f"dev_item_{c_idx}_photo",
                'photo': cms.get(f"dev_item_{i}_photo", "").strip() or "https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=600&q=80",
                'github_key': f"dev_item_{c_idx}_github",
                'github': cms.get(f"dev_item_{i}_github", "").strip(),
                'linkedin_key': f"dev_item_{c_idx}_linkedin",
                'linkedin': cms.get(f"dev_item_{i}_linkedin", "").strip(),
                'instagram_key': f"dev_item_{c_idx}_instagram",
                'instagram': cms.get(f"dev_item_{i}_instagram", "").strip(),
                'email_key': f"dev_item_{c_idx}_email",
                'email': cms.get(f"dev_item_{i}_email", "").strip(),
            })

    if not items:
        # Miembro inicial por defecto
        items.append({
            'index': 1,
            'name_key': "dev_item_1_name",
            'name': cms.get("dev_item_1_name", "Josué"),
            'role_key': "dev_item_1_role",
            'role': cms.get("dev_item_1_role", "Desarrollador Principal & Arquitectura Web"),
            'year_key': "dev_item_1_year",
            'year': cms.get("dev_item_1_year", "Generación 2026"),
            'bio_key': "dev_item_1_bio",
            'bio': cms.get("dev_item_1_bio", "Diseño, desarrollo integral y despliegue del portal institucional."),
            'photo_key': "dev_item_1_photo",
            'photo': cms.get("dev_item_1_photo", "https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=600&q=80"),
            'github_key': "dev_item_1_github",
            'github': cms.get("dev_item_1_github", "https://github.com/JosueXT"),
            'linkedin_key': "dev_item_1_linkedin",
            'linkedin': cms.get("dev_item_1_linkedin", ""),
            'instagram_key': "dev_item_1_instagram",
            'instagram': cms.get("dev_item_1_instagram", ""),
            'email_key': "dev_item_1_email",
            'email': cms.get("dev_item_1_email", "soporte@liceomariobourne.dpdns.org"),
        })
    return items

# =============================================================================
# 1. RUTAS PÚBLICAS
# =============================================================================

@app.route('/favicon.ico')
def favicon():
    """Servir favicon.ico directamente para navegadores y motores de búsqueda"""
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/')
def home():
    """Ruta Principal Pública: Carga el sitio institucional con los contenidos del CMS"""
    is_admin = session.get('is_admin', False)
    cms = get_all_content(force_fresh=is_admin)
    news = get_all_news(force_fresh=is_admin)
    pathway_features = get_pathway_features(cms)
    dynamic_campus = get_campus_dynamic_list(cms)
    return render_template(
        'index.html',
        cms=cms,
        news=news,
        is_admin=is_admin,
        pathway_features=pathway_features,
        dynamic_campus=dynamic_campus
    )

@app.route('/modalidad/<slug>')
@app.route('/oferta/<slug>')
def modalidad_detalle(slug):
    """Subpáginas dedicadas de oferta educativa (ib, frances, regular)"""
    slug = slug.lower().strip()
    if slug not in MODALIDADES_DETALLE:
        return redirect(url_for('home') + '#modalidades')

    modalidad_info = MODALIDADES_DETALLE[slug]
    is_admin = session.get('is_admin', False)
    cms = get_all_content(force_fresh=is_admin)
    news = get_all_news(force_fresh=is_admin)

    # Verificación de mantenimiento para visitantes no administradores
    subpage_key = f"subpage_status_{slug}"
    is_deactivated = (cms.get(subpage_key, 'active') == 'maintenance') or (cms.get('subpages_global_maintenance') == 'true')

    if is_deactivated and not is_admin:
        return render_template(
            'mantenimiento_subpagina.html',
            cms=cms,
            subpage_name=modalidad_info.get('title', slug.upper()),
            subpage_slug=slug,
            is_admin=False
        ), 503

    dynamic_lists = get_modality_dynamic_lists(slug, cms)

    return render_template(
        'modalidad.html',
        modalidad=modalidad_info,
        cms=cms,
        is_admin=is_admin,
        dynamic_lists=dynamic_lists,
        news=news,
        is_maintenance_mode=is_deactivated
    )

@app.route('/desarrolladores')
@app.route('/creditos')
@app.route('/equipo')
def desarrolladores():
    """Subpágina dedicada del Equipo de Desarrolladores de la página web."""
    is_admin = session.get('is_admin', False)
    cms = get_all_content(force_fresh=is_admin)

    is_deactivated = (cms.get('subpage_status_developers', 'active') == 'maintenance') or (cms.get('subpages_global_maintenance') == 'true')

    if is_deactivated and not is_admin:
        return render_template(
            'mantenimiento_subpagina.html',
            cms=cms,
            subpage_name="Equipo de Desarrolladores & Créditos Web",
            subpage_slug="developers",
            is_admin=False
        ), 503

    developers = get_developers_dynamic_list(cms)
    return render_template(
        'desarrolladores.html',
        cms=cms,
        is_admin=is_admin,
        developers=developers,
        is_maintenance_mode=is_deactivated
    )

# =============================================================================
# 2. SUBPÁGINA DEDICADA DE INICIO DE SESIÓN
# =============================================================================

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Subpágina dedicada de Inicio de Sesión."""
    cms = get_all_content()
    if request.method == 'GET':
        if session.get('is_admin', False):
            return redirect(url_for('admin_panel'))
        return render_template('login.html', cms=cms)

    if not app.config.get('TESTING'):
        ip = get_client_ip()
        locked, remaining = security_shield.is_locked(ip, 'login', max_attempts=5, window_seconds=600)
        if locked:
            mins = (remaining + 59) // 60
            return render_template('login.html', cms=cms, error=f'Acceso bloqueado temporalmente por {mins} minuto(s) debido a múltiples intentos fallidos.')

    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()

    if verify_admin_credentials(username, password):
        if not app.config.get('TESTING'):
            security_shield.reset_failures(get_client_ip(), 'login')
        session.clear()  # Protección contra fijación de sesión (Session Fixation OWASP)
        session['is_admin'] = True
        session['admin_username'] = username
        return redirect(url_for('admin_panel'))
    else:
        if not app.config.get('TESTING'):
            security_shield.record_failure(get_client_ip(), 'login')
        return render_template('login.html', cms=cms, error='Credenciales incorrectas. Verifique su usuario y contraseña.')

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    """Cierra la sesión administrativa de forma segura y redirige al inicio público."""
    session.clear()
    return redirect(url_for('home'))

# =============================================================================
# 3. SUBPÁGINA DEDICADA DEL PANEL ADMINISTRATIVO & CMS
# =============================================================================

@app.route('/admin')
@app.route('/admin/panel')
def admin_panel():
    """Subpágina de Edición y Panel de Administración con Bandeja de Consultas."""
    if not session.get('is_admin', False):
        return redirect(url_for('login'))

    admin_user = get_admin_user()
    current_admin_username = session.get('admin_username') or (admin_user['username'] if admin_user else 'Admin')
    current_recovery_email = (admin_user['recovery_email'] if admin_user and admin_user.get('recovery_email') else 'jeredamaya@gmail.com')

    cms = get_all_content(force_fresh=True)
    news = get_all_news(force_fresh=True)
    inquiries = get_all_inquiries()
    snapshots = get_all_snapshots()
    developers = get_developers_dynamic_list(cms)
    system_health = get_system_health()
    smtp_status = check_smtp_health()
    return render_template(
        'admin_panel.html',
        cms=cms,
        news=news,
        inquiries=inquiries,
        snapshots=snapshots,
        developers=developers,
        system_health=system_health,
        smtp_status=smtp_status,
        current_admin_username=current_admin_username,
        current_recovery_email=current_recovery_email
    )

# =============================================================================
# 4. ENDPOINTS API REST (FORMULARIO DE CONTACTO PÚBLICO)
# =============================================================================

@app.route('/api/contact/submit', methods=['POST'])
def api_submit_contact():
    """Recibe y guarda las consultas enviadas desde el formulario institucional público con rate limiting."""
    if not app.config.get('TESTING'):
        ip = get_client_ip()
        if security_shield.is_rate_limited(ip, 'contact', max_requests=6, window_seconds=600):
            return jsonify({
                'success': False,
                'message': 'Ha enviado varias consultas recientemente. Por seguridad, espere unos minutos antes de enviar otra.'
            }), 429

    data = request.get_json() or {}
    name = data.get('name', '').strip()
    email = data.get('email', '').strip()
    phone = data.get('phone', '').strip()
    area = data.get('area', 'General').strip()
    message = data.get('message', '').strip()

    if not name or not email or not message:
        return jsonify({
            'success': False,
            'message': 'Por favor complete su nombre, correo electrónico y mensaje.'
        }), 400

    inquiry_id = add_inquiry(name, email, phone, area, message)
    return jsonify({
        'success': True,
        'message': 'Su consulta ha sido registrada exitosamente. La administración del Liceo de Limón se comunicará con usted.',
        'inquiry_id': inquiry_id
    })

# =============================================================================
# 5. ENDPOINTS API REST (CMS & BANDEJA DE CONSULTAS - ADMIN)
# =============================================================================

@app.route('/api/cms/inquiries', methods=['GET'])
def api_get_inquiries():
    """Obtiene la lista de consultas para el administrador"""
    if not session.get('is_admin', False):
        return jsonify({'success': False, 'message': 'No autorizado.'}), 403

    inquiries = get_all_inquiries()
    return jsonify({'success': True, 'inquiries': inquiries})

@app.route('/api/cms/inquiries/<int:inquiry_id>/status', methods=['PUT', 'POST'])
def api_update_inquiry_status(inquiry_id):
    """Actualiza el estado de una consulta (ej: 'Atendida' o 'Pendiente')"""
    if not session.get('is_admin', False):
        return jsonify({'success': False, 'message': 'No autorizado.'}), 403

    data = request.get_json() or {}
    status = data.get('status', 'Atendida').strip()
    update_inquiry_status(inquiry_id, status)
    return jsonify({'success': True, 'message': f'Consulta #{inquiry_id} marcada como {status}.'})

@app.route('/api/cms/inquiries/<int:inquiry_id>', methods=['DELETE'])
def api_delete_inquiry(inquiry_id):
    """Elimina una consulta de la base de datos"""
    if not session.get('is_admin', False):
        return jsonify({'success': False, 'message': 'No autorizado.'}), 403

    delete_inquiry(inquiry_id)
    return jsonify({'success': True, 'message': f'Consulta #{inquiry_id} eliminada.'})

@app.route('/api/auth/login', methods=['POST'])
def api_login():
    """Valida credenciales dinámicas en base de datos con hash seguro y protección contra fuerza bruta."""
    ip = get_client_ip()
    if not app.config.get('TESTING'):
        locked, remaining = security_shield.is_locked(ip, 'api_login', max_attempts=5, window_seconds=600)
        if locked:
            mins = (remaining + 59) // 60
            return jsonify({
                'success': False,
                'message': f'Acceso bloqueado temporalmente por {mins} minuto(s) debido a múltiples intentos fallidos.'
            }), 429

    data = request.get_json() or {}
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()

    if verify_admin_credentials(username, password):
        if not app.config.get('TESTING'):
            security_shield.reset_failures(ip, 'api_login')
        session['is_admin'] = True
        session['admin_username'] = username
        return jsonify({
            'success': True,
            'message': 'Autenticación exitosa.',
            'redirect': '/admin/panel'
        })
    else:
        if not app.config.get('TESTING'):
            security_shield.record_failure(ip, 'api_login')
        return jsonify({
            'success': False,
            'message': 'Usuario o contraseña incorrectos. Verifique sus credenciales.'
        }), 401

@app.route('/api/auth/logout', methods=['POST'])
def api_logout():
    session.pop('is_admin', None)
    session.pop('admin_username', None)
    return jsonify({'success': True, 'message': 'Sesión cerrada correctamente.'})

@app.route('/api/auth/reset-password', methods=['POST'])
def api_reset_password():
    """
    Ruta deshabilitada: la clave maestra estática ha sido eliminada por completo por seguridad.
    La recuperación de contraseña se realiza exclusivamente mediante código OTP enviado al correo institucional
    o mediante acceso a terminal con 'python restablecer_password.py'.
    """
    return jsonify({
        'success': False,
        'message': 'El método de clave maestra ha sido deshabilitado. La recuperación se realiza exclusivamente vía código OTP por correo institucional (/api/auth/reset-password-otp) o mediante terminal de servidor.'
    }), 400

@app.route('/api/auth/request-otp', methods=['POST'])
def api_request_otp():
    """Genera y envía un código temporal de 6 dígitos (OTP) al correo institucional con rate limiting."""
    ip = get_client_ip()
    if not app.config.get('TESTING'):
        limited, remaining = security_shield.is_rate_limited(ip, 'request_otp', max_requests=4, window_seconds=600)
        if limited:
            mins = (remaining + 59) // 60
            return jsonify({
                'success': False,
                'message': f'Ha alcanzado el límite de solicitudes de código. Por favor espere {mins} minuto(s) antes de solicitar otro.'
            }), 429

    data = request.get_json() or {}
    username = data.get('username', '').strip()
    success, message, masked_email = create_password_reset_otp(username)
    if success:
        return jsonify({
            'success': True,
            'message': message,
            'masked_email': masked_email
        })
    else:
        return jsonify({
            'success': False,
            'message': message
        }), 400

@app.route('/api/auth/reset-password-otp', methods=['POST'])
def api_reset_password_otp():
    """Valida el código temporal recibido por correo y actualiza la contraseña con protección contra fuerza bruta."""
    ip = get_client_ip()
    if not app.config.get('TESTING'):
        locked, remaining = security_shield.is_locked(ip, 'verify_otp', max_attempts=5, window_seconds=600)
        if locked:
            mins = (remaining + 59) // 60
            return jsonify({
                'success': False,
                'message': f'Demasiados intentos fallidos con el código de verificación. Bloqueado temporalmente por {mins} minuto(s).'
            }), 429

    data = request.get_json() or {}
    username = data.get('username', '').strip()
    otp = data.get('otp', '').strip()
    new_password = data.get('new_password', '').strip()

    if not otp:
        return jsonify({'success': False, 'message': 'Debe ingresar el código de 6 dígitos recibido en su correo.'}), 400

    if not new_password or len(new_password) < 4:
        return jsonify({'success': False, 'message': 'La nueva contraseña debe tener al menos 4 caracteres.'}), 400

    success, message = verify_and_consume_otp(username, otp, new_password)
    if success:
        if not app.config.get('TESTING'):
            security_shield.reset_failures(ip, 'verify_otp')
        return jsonify({'success': True, 'message': message})
    else:
        if not app.config.get('TESTING'):
            security_shield.record_failure(ip, 'verify_otp')
        return jsonify({'success': False, 'message': message}), 400

@app.route('/api/admin/change-credentials', methods=['POST'])
def api_change_credentials():
    """Permite al administrador modificar su nombre de usuario, contraseña y correo de recuperación institucional."""
    if not session.get('is_admin', False):
        return jsonify({'success': False, 'message': 'No autorizado.'}), 403

    data = request.get_json() or {}
    current_password = data.get('current_password', '').strip()
    new_username = data.get('new_username', '').strip()
    new_password = data.get('new_password', '').strip()
    new_recovery_email = data.get('new_recovery_email', '').strip()

    if not current_password:
        return jsonify({'success': False, 'message': 'Debe ingresar su contraseña actual para confirmar el cambio.'}), 400

    admin_user = get_admin_user()
    if not admin_user:
        return jsonify({'success': False, 'message': 'No se encontró la cuenta de administración.'}), 404

    # Validar que la contraseña actual ingresada coincida con la registrada
    if not verify_admin_credentials(admin_user['username'], current_password):
        return jsonify({'success': False, 'message': 'La contraseña actual ingresada es incorrecta.'}), 400

    if not new_username or len(new_username) < 3:
        return jsonify({'success': False, 'message': 'El nombre de usuario debe contener al menos 3 caracteres.'}), 400

    if not new_password or len(new_password) < 4:
        return jsonify({'success': False, 'message': 'La nueva contraseña debe tener un mínimo de 4 caracteres.'}), 400

    success = update_admin_credentials(
        new_username,
        new_password,
        new_recovery_email if new_recovery_email else None
    )
    if success:
        session['admin_username'] = new_username
        return jsonify({
            'success': True,
            'message': '¡Credenciales actualizadas exitosamente! Se utilizarán en los próximos inicios de sesión.',
            'new_username': new_username,
            'new_recovery_email': new_recovery_email or (admin_user.get('recovery_email') if admin_user else 'jeredamaya@gmail.com')
        })
    else:
        return jsonify({'success': False, 'message': 'Error al actualizar credenciales en base de datos.'}), 500


@app.route('/api/cms/content', methods=['GET'])
def api_get_content():
    content = get_all_content(force_fresh=True)
    return jsonify({'success': True, 'content': content})

@app.route('/api/cms/content', methods=['POST', 'PUT'])
def api_save_content():
    if not session.get('is_admin', False):
        return jsonify({'success': False, 'message': 'No autorizado. Inicie sesión.'}), 403

    data = request.get_json() or {}
    items = data.get('items', {})
    if not items and isinstance(data, dict):
        items = {k: v for k, v in data.items() if k not in ('items', '_csrf_token')}

    if not items:
        return jsonify({'success': False, 'message': 'No se enviaron datos.'}), 400

    try:
        update_bulk_content(items)
        return jsonify({
            'success': True,
            'message': 'Contenidos guardados correctamente en la base de datos.',
            'count': len(items)
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error en base de datos: {str(e)}'}), 500

@app.route('/api/cms/developers', methods=['GET'])
def api_get_developers():
    """Retorna la lista estructurada de desarrolladores."""
    cms = get_all_content()
    devs = get_developers_dynamic_list(cms)
    return jsonify({'success': True, 'developers': devs})

@app.route('/api/cms/developers', methods=['POST'])
def api_update_developers():
    """Actualiza la lista completa de desarrolladores desde el panel administrativo."""
    if not session.get('is_admin', False):
        return jsonify({'success': False, 'message': 'No autorizado.'}), 403

    data = request.get_json() or {}
    devs = data.get('developers', [])

    items_to_save = {}
    if 'devs_page_title' in data:
        items_to_save['devs_page_title'] = str(data['devs_page_title']).strip()
    if 'devs_hero_tag' in data:
        items_to_save['devs_hero_tag'] = str(data['devs_hero_tag']).strip()
    if 'devs_hero_title' in data:
        items_to_save['devs_hero_title'] = str(data['devs_hero_title']).strip()
    if 'devs_hero_subtitle' in data:
        items_to_save['devs_hero_subtitle'] = str(data['devs_hero_subtitle']).strip()

    for idx, dev in enumerate(devs, start=1):
        items_to_save[f"dev_item_{idx}_name"] = dev.get('name', '').strip()
        items_to_save[f"dev_item_{idx}_role"] = dev.get('role', '').strip()
        items_to_save[f"dev_item_{idx}_year"] = dev.get('year', 'Generación 2026').strip()
        items_to_save[f"dev_item_{idx}_bio"] = dev.get('bio', '').strip()
        items_to_save[f"dev_item_{idx}_photo"] = dev.get('photo', '').strip()
        items_to_save[f"dev_item_{idx}_github"] = dev.get('github', '').strip()
        items_to_save[f"dev_item_{idx}_linkedin"] = dev.get('linkedin', '').strip()
        items_to_save[f"dev_item_{idx}_instagram"] = dev.get('instagram', '').strip()
        items_to_save[f"dev_item_{idx}_email"] = dev.get('email', '').strip()

    # Limpiar campos de desarrolladores eliminados hasta el índice 60
    for idx in range(len(devs) + 1, 61):
        items_to_save[f"dev_item_{idx}_name"] = ""
        items_to_save[f"dev_item_{idx}_role"] = ""
        items_to_save[f"dev_item_{idx}_year"] = ""
        items_to_save[f"dev_item_{idx}_bio"] = ""
        items_to_save[f"dev_item_{idx}_photo"] = ""
        items_to_save[f"dev_item_{idx}_github"] = ""
        items_to_save[f"dev_item_{idx}_linkedin"] = ""
        items_to_save[f"dev_item_{idx}_instagram"] = ""
        items_to_save[f"dev_item_{idx}_email"] = ""

    try:
        update_bulk_content(items_to_save)
        return jsonify({
            'success': True,
            'message': 'Equipo de desarrolladores guardado exitosamente.',
            'count': len(devs)
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error al guardar en base de datos: {str(e)}'}), 500

# =============================================================================
# GESTIÓN DE DISPONIBILIDAD Y MANTENIMIENTO DE SUBPÁGINAS
# =============================================================================
@app.route('/api/cms/subpages/status', methods=['GET'])
def api_get_subpages_status():
    """Retorna el estado de activación y mantenimiento de todas las subpáginas."""
    cms = get_all_content()
    subpages = {
        'ib': cms.get('subpage_status_ib', 'active'),
        'frances': cms.get('subpage_status_frances', 'active'),
        'regular': cms.get('subpage_status_regular', 'active'),
        'developers': cms.get('subpage_status_developers', 'active'),
        'global_maintenance': cms.get('subpages_global_maintenance', 'false') == 'true',
        'maintenance_title': cms.get('subpages_maintenance_title', 'Apartado Temporalmente Fuera de Servicio'),
        'maintenance_message': cms.get('subpages_maintenance_message', 'Este apartado se encuentra temporalmente fuera de servicio debido a que se está realizando mantenimiento técnico y actualización de contenidos institucionales. Por favor, vuelva nuevamente más tarde.')
    }
    return jsonify({'success': True, 'subpages': subpages})

@app.route('/api/cms/subpages/toggle', methods=['POST'])
def api_toggle_subpage():
    """Activa o desactiva subpáginas específicas o el modo global de mantenimiento."""
    if not session.get('is_admin', False):
        return jsonify({'success': False, 'message': 'No autorizado.'}), 403

    data = request.get_json() or {}
    subpage = str(data.get('subpage', '')).strip().lower()
    target_status = data.get('status')

    valid_subpages = {'ib', 'frances', 'regular', 'developers', 'global'}
    if subpage not in valid_subpages:
        return jsonify({'success': False, 'message': f'Subpágina inválida. Opciones válidas: {list(valid_subpages)}'}), 400

    cms = get_all_content()
    items_to_save = {}

    if subpage == 'global':
        current = cms.get('subpages_global_maintenance', 'false') == 'true'
        if target_status is not None:
            new_val = 'true' if (target_status in ['maintenance', True, 'true', '1']) else 'false'
        else:
            new_val = 'false' if current else 'true'
        items_to_save['subpages_global_maintenance'] = new_val
        new_status = 'maintenance' if new_val == 'true' else 'active'
    else:
        key = f"subpage_status_{subpage}"
        current = cms.get(key, 'active')
        if target_status is not None:
            new_status = 'maintenance' if str(target_status).lower() in ['maintenance', 'false', '0', 'disabled'] else 'active'
        else:
            new_status = 'maintenance' if current == 'active' else 'active'
        items_to_save[key] = new_status

    if 'maintenance_title' in data:
        items_to_save['subpages_maintenance_title'] = str(data['maintenance_title']).strip()
    if 'maintenance_message' in data:
        items_to_save['subpages_maintenance_message'] = str(data['maintenance_message']).strip()

    try:
        update_bulk_content(items_to_save)
        return jsonify({
            'success': True,
            'subpage': subpage,
            'new_status': new_status,
            'global_maintenance': items_to_save.get('subpages_global_maintenance', cms.get('subpages_global_maintenance', 'false')) == 'true',
            'message': f'Estado de subpágina {subpage} actualizado a: {new_status}'
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error al guardar en base de datos: {str(e)}'}), 500

@app.route('/api/cms/news', methods=['GET'])
def api_get_news():
    return jsonify({'success': True, 'news': get_all_news()})

@app.route('/api/cms/news', methods=['POST'])
def api_add_news():
    if not session.get('is_admin', False):
        return jsonify({'success': False, 'message': 'No autorizado.'}), 403

    data = request.get_json() or {}
    title = data.get('title', '').strip()
    category = data.get('category', 'Institucionales').strip()
    category_slug = data.get('category_slug', 'institucionales').strip()
    subcategory = data.get('subcategory', '').strip()
    date = data.get('date', '').strip()
    if not date:
        from datetime import datetime
        meses = ['', 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
        now = datetime.now()
        date = f"{now.day} de {meses[now.month]}, {now.year}"

    summary = data.get('summary', '').strip()
    content = data.get('content', '').strip()
    image = data.get('image', 'https://images.unsplash.com/photo-1523240795612-9a054b0db644?auto=format&fit=crop&w=800&q=80').strip()
    image_position = data.get('image_position', 'center center').strip() or 'center center'
    video_url = data.get('video_url', '').strip()
    author = data.get('author', 'Liceo de Limón MEP').strip()

    if not title or not summary:
        return jsonify({'success': False, 'message': 'El título y el resumen son obligatorios.'}), 400

    try:
        new_id = add_news(title, category, category_slug, subcategory, date, summary, content, image, author, image_position, video_url)
        return jsonify({
            'success': True,
            'message': 'Comunicado institucional publicado exitosamente.',
            'id': new_id,
            'news_id': new_id
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error al guardar en base de datos: {str(e)}'}), 500

@app.route('/api/cms/news/<int:news_id>', methods=['GET'])
def api_get_single_news(news_id):
    """Obtiene una noticia individual por su ID"""
    item = get_news_by_id(news_id)
    if not item:
        return jsonify({'success': False, 'message': 'Comunicado no encontrado.'}), 404
    return jsonify({'success': True, 'news': item})

@app.route('/api/cms/news/<int:news_id>', methods=['PUT', 'POST'])
def api_update_news(news_id):
    """Actualiza una noticia existente en la base de datos"""
    if not session.get('is_admin', False):
        return jsonify({'success': False, 'message': 'No autorizado.'}), 403

    data = request.get_json() or {}
    title = data.get('title', '').strip()
    category = data.get('category', 'Institucionales').strip()
    category_slug = data.get('category_slug', 'institucionales').strip()
    subcategory = data.get('subcategory', '').strip()
    date = data.get('date', '').strip()
    if not date:
        from datetime import datetime
        meses = ['', 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
        now = datetime.now()
        date = f"{now.day} de {meses[now.month]}, {now.year}"

    summary = data.get('summary', '').strip()
    content = data.get('content', '').strip()
    image = data.get('image', '').strip()
    image_position = data.get('image_position', 'center center').strip() or 'center center'
    video_url = data.get('video_url', '').strip()
    author = data.get('author', 'Liceo de Limón MEP').strip()

    if not title or not summary:
        return jsonify({'success': False, 'message': 'El título y el resumen son obligatorios.'}), 400

    try:
        update_news(news_id, title, category, category_slug, subcategory, date, summary, content, image, author, image_position, video_url)
        return jsonify({
            'success': True,
            'message': f'Comunicado #{news_id} actualizado exitosamente.'
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error al actualizar en base de datos: {str(e)}'}), 500

@app.route('/api/cms/news/<int:news_id>', methods=['DELETE'])
def api_delete_news(news_id):
    if not session.get('is_admin', False):
        return jsonify({'success': False, 'message': 'No autorizado.'}), 403

    delete_news(news_id)
    return jsonify({'success': True, 'message': f'Noticia #{news_id} eliminada.'})

@app.route('/api/cms/snapshots', methods=['GET'])
def api_get_snapshots():
    """Obtiene la lista de puntos de restauración"""
    if not session.get('is_admin', False):
        return jsonify({'success': False, 'message': 'No autorizado.'}), 403

    snapshots = get_all_snapshots()
    return jsonify({'success': True, 'snapshots': snapshots})

@app.route('/api/cms/snapshots', methods=['POST'])
def api_create_snapshot():
    """Guarda el estado actual de los contenidos y noticias como un nuevo punto base / copia de seguridad"""
    if not session.get('is_admin', False):
        return jsonify({'success': False, 'message': 'No autorizado.'}), 403

    data = request.get_json() or {}
    name = data.get('name', '').strip()
    if not name:
        from datetime import datetime
        name = f"Copia de Seguridad - {datetime.now().strftime('%d/%m/%Y %H:%M')}"

    new_id = create_snapshot(name)
    return jsonify({
        'success': True,
        'message': f'Punto de restauración "{name}" creado exitosamente.',
        'snapshot_id': new_id
    })

@app.route('/api/cms/snapshots/<int:snapshot_id>/restore', methods=['POST'])
def api_restore_snapshot(snapshot_id):
    """Restaura los contenidos y noticias al estado guardado en el snapshot seleccionado"""
    if not session.get('is_admin', False):
        return jsonify({'success': False, 'message': 'No autorizado.'}), 403

    success = restore_snapshot(snapshot_id)
    if not success:
        return jsonify({'success': False, 'message': 'Punto de restauración no encontrado.'}), 404

    return jsonify({
        'success': True,
        'message': 'Base de datos restaurada correctamente al punto de restauración seleccionado.'
    })

@app.route('/api/cms/snapshots/<int:snapshot_id>', methods=['DELETE'])
def api_delete_snapshot(snapshot_id):
    """Elimina un punto de restauración"""
    if not session.get('is_admin', False):
        return jsonify({'success': False, 'message': 'No autorizado.'}), 403

    delete_snapshot(snapshot_id)
    return jsonify({'success': True, 'message': 'Punto de restauración eliminado.'})

@app.route('/api/cms/snapshots/<int:snapshot_id>/download', methods=['GET'])
def api_download_snapshot(snapshot_id):
    """Descarga el snapshot seleccionado como un archivo JSON de respaldo oficial."""
    if not session.get('is_admin', False):
        return jsonify({'success': False, 'message': 'No autorizado.'}), 403

    snapshot = get_snapshot_by_id(snapshot_id)
    if not snapshot:
        return jsonify({'success': False, 'message': 'Punto de restauración no encontrado.'}), 404

    import json
    json_data = json.dumps(snapshot, indent=2, ensure_ascii=False)
    safe_name = f"respaldo_liceo_limon_{snapshot_id}.json"

    return Response(
        json_data,
        mimetype="application/json",
        headers={"Content-Disposition": f"attachment;filename={safe_name}"}
    )

@app.route('/api/cms/snapshots/import', methods=['POST'])
def api_import_snapshot():
    """Importa un archivo JSON de respaldo externo como un nuevo punto de restauración."""
    if not session.get('is_admin', False):
        return jsonify({'success': False, 'message': 'No autorizado.'}), 403

    import json
    data = None
    if 'file' in request.files:
        uploaded_file = request.files['file']
        if uploaded_file.filename == '':
            return jsonify({'success': False, 'message': 'No se seleccionó ningún archivo.'}), 400
        try:
            raw_bytes = uploaded_file.read()
            data = json.loads(raw_bytes.decode('utf-8'))
        except Exception:
            return jsonify({'success': False, 'message': 'El archivo seleccionado no es un JSON válido.'}), 400
    else:
        data = request.get_json() or {}

    content = data.get('content', {})
    news = data.get('news', [])
    inquiries = data.get('inquiries', [])
    name = data.get('name') or "Copia Importada"

    if not isinstance(content, dict):
        return jsonify({'success': False, 'message': 'Estructura de respaldo no válida.'}), 400

    new_id = import_snapshot(name, content, news, inquiries)

    apply_now = request.form.get('apply_now') == 'true' or (request.is_json and (request.get_json() or {}).get('apply_now'))
    if apply_now:
        restore_snapshot(new_id)

    return jsonify({
        'success': True,
        'message': f'Respaldo "{name}" importado exitosamente con ID #{new_id}.',
        'snapshot_id': new_id
    })

@app.route('/api/cms/snapshots/export-full', methods=['GET'])
def api_export_full_backup():
    """Descarga una copia de seguridad integral (100% de la base de datos) en formato JSON."""
    if not session.get('is_admin', False):
        return jsonify({'success': False, 'message': 'No autorizado.'}), 403

    import json
    from datetime import datetime
    backup_data = export_full_database()
    json_bytes = json.dumps(backup_data, indent=2, ensure_ascii=False)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"respaldo_completo_liceo_limon_{timestamp}.json"

    return Response(
        json_bytes,
        mimetype="application/json",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@app.route('/api/admin/system-status', methods=['GET'])
def api_admin_system_status():
    """Retorna el diagnóstico en tiempo real de todos los subsistemas (BD Nube, SMTP, Seguridad, Runtime)."""
    if not session.get('is_admin', False):
        return jsonify({'success': False, 'message': 'No autorizado.'}), 403

    health = get_system_health()
    smtp = check_smtp_health()
    
    # Métricas del Escudo de Seguridad
    locked_count = len(security_shield.failed_attempts)

    return jsonify({
        'success': True,
        'database': health,
        'smtp': smtp,
        'security': {
            'shield_active': True,
            'locked_identities': locked_count,
            'hsts_enabled': bool(os.environ.get('RENDER') or os.environ.get('FLASK_ENV') == 'production'),
            'csp_enabled': True,
            'session_cookie_httponly': True,
            'session_cookie_samesite': 'Lax'
        },
        'environment': {
            'is_render': bool(os.environ.get('RENDER')),
            'python_version': os.sys.version.split(' ')[0],
            'runtime': 'Gunicorn WSGI (Producción Endurecida)' if os.environ.get('RENDER') else 'Desarrollo Local'
        }
    })

@app.route('/api/admin/test-smtp', methods=['POST'])
def api_admin_test_smtp():
    """Prueba de conexión SMTP en vivo ejecutada a solicitud del administrador."""
    if not session.get('is_admin', False):
        return jsonify({'success': False, 'message': 'No autorizado.'}), 403

    res = check_smtp_health()
    return jsonify({
        'success': res.get('connected', False),
        'result': res
    })

@app.route('/api/cms/reset', methods=['POST'])
def api_reset_defaults():
    if not session.get('is_admin', False):
        return jsonify({'success': False, 'message': 'No autorizado.'}), 403

    reset_to_defaults()
    return jsonify({'success': True, 'message': 'Contenidos y consultas restaurados a valores iniciales de fábrica.'})

# =============================================================================
# ARRANQUE DEL SERVIDOR
# =============================================================================
if __name__ == '__main__':
    print("==========================================================")
    print("  LICEO DE LIMÓN MARIO BOURNE BOURNE - SERVIDOR ACTIVO")
    print("  - Sitio público:     http://localhost:5000/")
    print("  - Iniciar sesión:    http://localhost:5000/login")
    print("  - Panel de control:  http://localhost:5000/admin/panel")
    print("  - Credenciales:      Usuario: Admin | Contraseña: Admin")
    print("==========================================================")
    app.run(host='0.0.0.0', port=5000, debug=True)
