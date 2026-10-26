"""
==============================================================================
BASE DE DATOS (SQLite) - LICEO DE LIMÓN MARIO BOURNE BOURNE
==============================================================================
"""

import sqlite3
import os
import json
import time
import secrets
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from seed_data import DEFAULT_CMS_CONTENT, DEFAULT_NEWS
from email_service import send_recovery_otp_email, mask_email, load_env_file

try:
    import libsql
    HAS_LIBSQL = True
except ImportError:
    HAS_LIBSQL = False

DB_PATH = os.path.join(os.path.dirname(__file__), 'liceo_cms.db')

class LibsqlRow:
    """Emula sqlite3.Row para el cliente de Turso (libsql)."""
    def __init__(self, cols, vals):
        self._cols = cols or []
        self._vals = vals
        self._map = {c: v for c, v in zip(self._cols, vals)}

    def __getitem__(self, item):
        if isinstance(item, int):
            return self._vals[item]
        return self._map[item]

    def keys(self):
        return self._cols

    def values(self):
        return [self._map[c] for c in self._cols]

    def items(self):
        return [(c, self._map[c]) for c in self._cols]

    def get(self, key, default=None):
        return self._map.get(key, default)

    def __iter__(self):
        return iter(self._cols)

    def __repr__(self):
        return f"<LibsqlRow {self._map}>"


class LibsqlCursorWrapper:
    """Envuelve el cursor de libsql para retornar filas compatibles con sqlite3.Row."""
    def __init__(self, cursor):
        self._cursor = cursor

    def __getattr__(self, name):
        return getattr(self._cursor, name)

    def _wrap_row(self, row):
        if row is None:
            return None
        cols = [d[0] for d in self._cursor.description] if self._cursor.description else []
        return LibsqlRow(cols, row)

    def fetchone(self):
        return self._wrap_row(self._cursor.fetchone())

    def fetchall(self):
        rows = self._cursor.fetchall()
        if not rows:
            return []
        cols = [d[0] for d in self._cursor.description] if self._cursor.description else []
        return [LibsqlRow(cols, r) for r in rows]

    def fetchmany(self, size=None):
        rows = self._cursor.fetchmany(size) if size is not None else self._cursor.fetchmany()
        if not rows:
            return []
        cols = [d[0] for d in self._cursor.description] if self._cursor.description else []
        return [LibsqlRow(cols, r) for r in rows]

    def __iter__(self):
        for row in self.fetchall():
            yield row


class LibsqlConnectionWrapper:
    """Envuelve la conexión de libsql para compatibilidad con context managers y row_factory."""
    def __init__(self, conn):
        self._conn = conn

    def __getattr__(self, name):
        return getattr(self._conn, name)

    def cursor(self):
        return LibsqlCursorWrapper(self._conn.cursor())

    def execute(self, *args, **kwargs):
        cur = self.cursor()
        cur.execute(*args, **kwargs)
        return cur

    def commit(self):
        return self._conn.commit()

    def rollback(self):
        try:
            return self._conn.rollback()
        except Exception:
            pass

    def close(self):
        return self._conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.commit()
        else:
            self.rollback()


def get_db_connection():
    load_env_file()

    # Si estamos en modo de pruebas unitarias, usar siempre la base de datos local temporal
    if os.environ.get('TESTING') == 'True':
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn

    try:
        from flask import current_app
        if current_app and current_app.config.get('TESTING'):
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            return conn
    except Exception:
        pass

    turso_url = os.environ.get('TURSO_DATABASE_URL', '').strip()
    turso_token = os.environ.get('TURSO_AUTH_TOKEN', '').strip()

    if turso_url and HAS_LIBSQL:
        # Conexión persistente en la nube (Turso)
        conn = getattr(libsql, "connect")(database=turso_url, auth_token=turso_token)
        return LibsqlConnectionWrapper(conn)

    # Conexión local a archivo SQLite (desarrollo o sin Turso configurado)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

_DB_ALREADY_INITIALIZED = False

def init_db(force=False):
    """Inicializa la base de datos con optimización de arranque rápido (evita timeouts en Render/Gunicorn)."""
    global _DB_ALREADY_INITIALIZED
    is_testing = os.environ.get('TESTING') == 'True'
    if not is_testing and _DB_ALREADY_INITIALIZED and not force:
        return

    # Si la base de datos ya está inicializada en la nube (Turso), saltar consultas redundantes
    if not is_testing and not force:
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM cms_content LIMIT 1")
            row = cursor.fetchone()
            conn.close()
            if row:
                _DB_ALREADY_INITIALIZED = True
                return
        except Exception as e:
            print(f"[INFO] Comprobación inicial de BD: {e}")

    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Tabla para contenidos clave-valor del CMS
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cms_content (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 2. Tabla para noticias y comunicados con soporte de subcategorías
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS news_articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            category TEXT NOT NULL,
            category_slug TEXT NOT NULL,
            subcategory TEXT DEFAULT '',
            date TEXT NOT NULL,
            summary TEXT NOT NULL,
            content TEXT NOT NULL,
            image TEXT NOT NULL,
            author TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Migración segura: verificar si subcategory e image_position existen en news_articles
    cursor.execute("PRAGMA table_info(news_articles)")
    columns = [row[1] for row in cursor.fetchall()]
    if 'subcategory' not in columns:
        cursor.execute("ALTER TABLE news_articles ADD COLUMN subcategory TEXT DEFAULT ''")
    if 'image_position' not in columns:
        cursor.execute("ALTER TABLE news_articles ADD COLUMN image_position TEXT DEFAULT 'center center'")

    # 3. Tabla para consultas de contacto
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS contact_inquiries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT,
            area TEXT NOT NULL,
            message TEXT NOT NULL,
            status TEXT DEFAULT 'Pendiente',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 4. Tabla para copias de seguridad y puntos de restauración (Wayback Machine)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cms_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            content_json TEXT NOT NULL,
            news_json TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 5. Tabla para usuarios y credenciales de acceso administrativo
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admin_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            recovery_key_hash TEXT,
            recovery_email TEXT DEFAULT 'jeredamaya@gmail.com',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Migración segura: verificar columnas recovery_key_hash y recovery_email en admin_users
    cursor.execute("PRAGMA table_info(admin_users)")
    admin_cols = [row[1] for row in cursor.fetchall()]
    if 'recovery_key_hash' not in admin_cols:
        cursor.execute("ALTER TABLE admin_users ADD COLUMN recovery_key_hash TEXT")
    if 'recovery_email' not in admin_cols:
        cursor.execute("ALTER TABLE admin_users ADD COLUMN recovery_email TEXT DEFAULT 'jeredamaya@gmail.com'")

    # Clave de recuperación institucional por defecto e inmutable (MEP-LIMON-2026)
    default_recovery_key = os.environ.get('ADMIN_RECOVERY_KEY', 'MEP-LIMON-2026')
    default_rec_hash = generate_password_hash(default_recovery_key)

    cursor.execute("UPDATE admin_users SET recovery_key_hash = ? WHERE recovery_key_hash IS NULL OR recovery_key_hash = ''", (default_rec_hash,))
    cursor.execute("UPDATE admin_users SET recovery_email = 'jeredamaya@gmail.com' WHERE recovery_email IS NULL OR recovery_email = '' OR recovery_email = 'liceo.limon@mep.go.cr'")

    # 6. Tabla para tokens de restablecimiento temporal (OTP)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS password_reset_tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            username TEXT NOT NULL,
            email TEXT NOT NULL,
            token_hash TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            used INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES admin_users(id)
        )
    ''')

    conn.commit()

    def _is_empty():
        row = cursor.fetchone()
        return not row or row[0] == 0

    # Verificar si necesitamos rellenar datos iniciales
    cursor.execute('SELECT COUNT(*) FROM cms_content')
    if _is_empty():
        seed_content(conn)

    cursor.execute('SELECT COUNT(*) FROM news_articles')
    if _is_empty():
        seed_news(conn)

    cursor.execute('SELECT COUNT(*) FROM contact_inquiries')
    if _is_empty():
        seed_inquiries(conn)

    cursor.execute('SELECT COUNT(*) FROM admin_users')
    if _is_empty():
        cursor.execute('''
            INSERT INTO admin_users (username, password_hash, recovery_key_hash)
            VALUES (?, ?, ?)
        ''', ('Admin', generate_password_hash('Admin'), default_rec_hash))
        conn.commit()

    # Crear punto de restauración inicial base de fábrica si la tabla de snapshots está vacía
    cursor.execute('SELECT COUNT(*) FROM cms_snapshots')
    if _is_empty():
        cursor.execute('SELECT key, value FROM cms_content')
        content_dict = {row['key']: row['value'] for row in cursor.fetchall()}
        cursor.execute('SELECT title, category, category_slug, subcategory, date, summary, content, image, author FROM news_articles')
        news_list = [dict(row) for row in cursor.fetchall()]
        cursor.execute('''
            INSERT INTO cms_snapshots (name, content_json, news_json)
            VALUES (?, ?, ?)
        ''', ("Punto Base Inicial MEP (Valores de Fábrica)", json.dumps(content_dict, ensure_ascii=False), json.dumps(news_list, ensure_ascii=False)))
        conn.commit()

    # Actualizar site_logo si tiene la imagen de prueba anterior
    cursor.execute("SELECT value FROM cms_content WHERE key = 'site_logo'")
    row = cursor.fetchone()
    if not row or 'unsplash' in row[0]:
        cursor.execute("INSERT OR REPLACE INTO cms_content (key, value) VALUES ('site_logo', ?)", (DEFAULT_CMS_CONTENT['site_logo'],))
    conn.close()
    _DB_ALREADY_INITIALIZED = True

def seed_content(conn):
    cursor = conn.cursor()
    for key, value in DEFAULT_CMS_CONTENT.items():
        cursor.execute('''
            INSERT OR REPLACE INTO cms_content (key, value)
            VALUES (?, ?)
        ''', (key, value))
    conn.commit()

def seed_news(conn):
    cursor = conn.cursor()
    for item in DEFAULT_NEWS:
        cursor.execute('''
            INSERT INTO news_articles (title, category, category_slug, subcategory, date, summary, content, image, author)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            item['title'],
            item['category'],
            item['category_slug'],
            item.get('subcategory', ''),
            item['date'],
            item['summary'],
            item['content'],
            item['image'],
            item['author']
        ))
    conn.commit()

def seed_inquiries(conn):
    cursor = conn.cursor()
    sample_inquiries = [
        (
            "Carlos Alvarado Brenes",
            "carlos.alvarado@gmail.com",
            "+506 8834-1290",
            "Bachillerato Internacional (IB)",
            "Buenas tardes, quisiera saber cuándo inician las inscripciones para las pruebas de admisión del programa IB para el curso lectivo y si se requiere algún promedio mínimo de noveno año.",
            "Pendiente"
        ),
        (
            "Marjorie Campbell Smith",
            "m.campbell@outlook.com",
            "+506 8712-4455",
            "Francés Avanzado",
            "Hola, mi hija entra a séptimo año y tenemos interés en la Sección de Francés. ¿Tienen alguna reunión informativa para padres sobre las certificaciones DELF?",
            "Atendida"
        ),
        (
            "Esteban Mora Jiménez",
            "esteban.mora@hotmail.com",
            "+506 8320-9911",
            "Secundaria Regular",
            "Deseo solicitar constancia de matrícula y notas de décimo año para trámite de beca en el departamento de secretaría.",
            "Pendiente"
        )
    ]
    for inq in sample_inquiries:
        cursor.execute('''
            INSERT INTO contact_inquiries (name, email, phone, area, message, status)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', inq)
    conn.commit()

# =============================================================================
# CACHÉ EN MEMORIA PARA MÁXIMA VELOCIDAD (SUB-MILISEGUNDO)
# =============================================================================
_CACHE_CONTENT = None
_CACHE_CONTENT_TIME = 0
_CACHE_NEWS = None
_CACHE_NEWS_TIME = 0
CACHE_TTL_SECONDS = 120  # 2 minutos de TTL en memoria o invalidación inmediata al editar

def invalidate_cms_cache():
    """Invalida la memoria caché para forzar lectura fresca desde la base de datos."""
    global _CACHE_CONTENT, _CACHE_CONTENT_TIME, _CACHE_NEWS, _CACHE_NEWS_TIME
    _CACHE_CONTENT = None
    _CACHE_CONTENT_TIME = 0
    _CACHE_NEWS = None
    _CACHE_NEWS_TIME = 0

def get_all_content(force_fresh=False):
    """Obtiene todos los contenidos del CMS utilizando caché en RAM ultra-rápida."""
    global _CACHE_CONTENT, _CACHE_CONTENT_TIME
    now = time.time()
    if not force_fresh and _CACHE_CONTENT is not None and (now - _CACHE_CONTENT_TIME < CACHE_TTL_SECONDS):
        return dict(_CACHE_CONTENT)

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT key, value FROM cms_content')
    rows = cursor.fetchall()
    conn.close()
    
    content = {row['key']: row['value'] for row in rows}
    for k, v in DEFAULT_CMS_CONTENT.items():
        if k not in content:
            content[k] = v

    _CACHE_CONTENT = content
    _CACHE_CONTENT_TIME = now
    return dict(content)

def update_bulk_content(items_dict):
    conn = get_db_connection()
    cursor = conn.cursor()
    for key, value in items_dict.items():
        cursor.execute('''
            INSERT INTO cms_content (key, value)
            VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=CURRENT_TIMESTAMP
        ''', (key, str(value)))
    conn.commit()
    conn.close()
    invalidate_cms_cache()
    return True

def get_all_news(force_fresh=False):
    """Obtiene todas las noticias utilizando caché en RAM ultra-rápida."""
    global _CACHE_NEWS, _CACHE_NEWS_TIME
    now = time.time()
    if not force_fresh and _CACHE_NEWS is not None and (now - _CACHE_NEWS_TIME < CACHE_TTL_SECONDS):
        return list(_CACHE_NEWS)

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM news_articles ORDER BY id DESC')
    rows = cursor.fetchall()
    conn.close()
    news = [dict(row) for row in rows]
    _CACHE_NEWS = news
    _CACHE_NEWS_TIME = now
    return list(news)

def get_news_by_id(news_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM news_articles WHERE id = ?', (news_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def add_news(title, category, category_slug, subcategory, date, summary, content, image, author, image_position='center center'):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO news_articles (title, category, category_slug, subcategory, date, summary, content, image, author, image_position)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (title, category, category_slug, subcategory, date, summary, content, image, author, image_position or 'center center'))
    new_id = cursor.lastrowid
    conn.commit()
    conn.close()
    invalidate_cms_cache()
    return new_id

def update_news(news_id, title, category, category_slug, subcategory, date, summary, content, image, author, image_position='center center'):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE news_articles
        SET title = ?, category = ?, category_slug = ?, subcategory = ?, date = ?, summary = ?, content = ?, image = ?, author = ?, image_position = ?
        WHERE id = ?
    ''', (title, category, category_slug, subcategory, date, summary, content, image, author, image_position or 'center center', news_id))
    conn.commit()
    conn.close()
    invalidate_cms_cache()
    return True

def delete_news(news_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM news_articles WHERE id = ?', (news_id,))
    conn.commit()
    conn.close()
    invalidate_cms_cache()
    return True

# =============================================================================
# FUNCIONES PARA GESTIÓN DE CONSULTAS DE CONTACTO
# =============================================================================

def add_inquiry(name, email, phone, area, message):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO contact_inquiries (name, email, phone, area, message)
        VALUES (?, ?, ?, ?, ?)
    ''', (name, email, phone, area, message))
    new_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return new_id

def get_all_inquiries():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM contact_inquiries ORDER BY id DESC')
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def update_inquiry_status(inquiry_id, status):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE contact_inquiries
        SET status = ?
        WHERE id = ?
    ''', (status, inquiry_id))
    conn.commit()
    conn.close()
    return True

def delete_inquiry(inquiry_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM contact_inquiries WHERE id = ?', (inquiry_id,))
    conn.commit()
    conn.close()
    return True

def reset_to_defaults():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM cms_content')
    cursor.execute('DELETE FROM news_articles')
    cursor.execute('DELETE FROM contact_inquiries')
    seed_content(conn)
    seed_news(conn)
    seed_inquiries(conn)
    conn.close()
    invalidate_cms_cache()
    return True

# =============================================================================
# FUNCIONES PARA PUNTOS DE RESTAURACIÓN Y SNAPSHOTS (WAYBACK MACHINE)
# =============================================================================

def create_snapshot(name="Copia de Seguridad"):
    """Crea una instantánea completa del estado de los contenidos y noticias actuales asegurando el 100% de las claves."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Obtener todo el contenido CMS actual consolidado (incluyendo personalizaciones y claves base)
    content_dict = get_all_content()

    # Obtener todas las noticias actuales
    cursor.execute('SELECT title, category, category_slug, subcategory, date, summary, content, image, author FROM news_articles')
    news_rows = [dict(row) for row in cursor.fetchall()]

    cursor.execute('''
        INSERT INTO cms_snapshots (name, content_json, news_json)
        VALUES (?, ?, ?)
    ''', (name, json.dumps(content_dict, ensure_ascii=False), json.dumps(news_rows, ensure_ascii=False)))
    
    new_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return new_id

def get_all_snapshots():
    """Retorna la lista de todas las copias de seguridad / puntos de restauración"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, name, created_at FROM cms_snapshots ORDER BY id DESC')
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_snapshot_by_id(snapshot_id):
    """Obtiene un punto de restauración completo con sus datos para descarga o inspección."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, name, content_json, news_json, created_at FROM cms_snapshots WHERE id = ?', (snapshot_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    return {
        'id': row['id'],
        'name': row['name'],
        'content': json.loads(row['content_json']),
        'news': json.loads(row['news_json']),
        'created_at': str(row['created_at'])
    }

def import_snapshot(name, content_dict, news_list):
    """Registra una copia de seguridad importada desde archivo JSON externo."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO cms_snapshots (name, content_json, news_json)
        VALUES (?, ?, ?)
    ''', (name, json.dumps(content_dict, ensure_ascii=False), json.dumps(news_list, ensure_ascii=False)))
    new_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return new_id

def restore_snapshot(snapshot_id):
    """Restaura todos los contenidos y noticias a un punto de restauración específico"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT content_json, news_json FROM cms_snapshots WHERE id = ?', (snapshot_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return False

    content_dict = json.loads(row['content_json'])
    news_list = json.loads(row['news_json'])

    # Restaurar CMS content
    cursor.execute('DELETE FROM cms_content')
    for key, value in content_dict.items():
        cursor.execute('INSERT INTO cms_content (key, value) VALUES (?, ?)', (key, value))

    # Restaurar Noticias
    cursor.execute('DELETE FROM news_articles')
    for item in news_list:
        cursor.execute('''
            INSERT INTO news_articles (title, category, category_slug, subcategory, date, summary, content, image, author)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            item.get('title', ''),
            item.get('category', 'Institucionales'),
            item.get('category_slug', 'institucionales'),
            item.get('subcategory', ''),
            item.get('date', ''),
            item.get('summary', ''),
            item.get('content', ''),
            item.get('image', ''),
            item.get('author', 'Liceo de Limón MEP')
        ))

    conn.commit()
    conn.close()
    invalidate_cms_cache()
    return True

def delete_snapshot(snapshot_id):
    """Elimina un punto de restauración"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM cms_snapshots WHERE id = ?', (snapshot_id,))
    conn.commit()
    conn.close()
    return True

# =============================================================================
# FUNCIONES DE GESTIÓN DE CREDENCIALES DEL ADMINISTRADOR
# =============================================================================

DEFAULT_RECOVERY_KEY = os.environ.get('ADMIN_RECOVERY_KEY', 'MEP-LIMON-2026')

def get_admin_user():
    """Obtiene los datos del usuario administrador registrado en la base de datos."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, username, password_hash, recovery_key_hash, recovery_email, created_at, updated_at FROM admin_users ORDER BY id ASC LIMIT 1')
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_admin_recovery_email(username=None):
    """Obtiene el correo de recuperación institucional configurado."""
    conn = get_db_connection()
    cursor = conn.cursor()
    if username and username.strip():
        cursor.execute('SELECT recovery_email FROM admin_users WHERE LOWER(username) = LOWER(?) LIMIT 1', (username.strip(),))
        row = cursor.fetchone()
    else:
        row = None

    if not row:
        cursor.execute('SELECT recovery_email FROM admin_users ORDER BY id ASC LIMIT 1')
        row = cursor.fetchone()

    conn.close()
    return row['recovery_email'] if row and row['recovery_email'] else 'jeredamaya@gmail.com'

def create_password_reset_otp(username):
    """Genera un código OTP de 6 dígitos con validez de 15 minutos y lo envía al correo institucional."""
    conn = get_db_connection()
    cursor = conn.cursor()

    target_user = None
    if username and username.strip():
        cursor.execute('SELECT id, username, recovery_email FROM admin_users WHERE LOWER(username) = LOWER(?) LIMIT 1', (username.strip(),))
        target_user = cursor.fetchone()

    if not target_user:
        cursor.execute('SELECT id, username, recovery_email FROM admin_users ORDER BY id ASC LIMIT 1')
        target_user = cursor.fetchone()

    if not target_user:
        conn.close()
        return False, "No se encontró ningún usuario administrador en el sistema.", None

    target_email = target_user['recovery_email'] or 'jeredamaya@gmail.com'
    user_id = target_user['id']
    target_username = target_user['username']

    # Generar código OTP seguro de 6 dígitos numéricos
    otp_code = f"{secrets.randbelow(900000) + 100000:06d}"
    token_hash = generate_password_hash(otp_code)
    expires_at = (datetime.now() + timedelta(minutes=15)).strftime('%Y-%m-%d %H:%M:%S')

    # Invalidar códigos OTP previos sin usar
    cursor.execute('UPDATE password_reset_tokens SET used = 1 WHERE user_id = ? AND used = 0', (user_id,))

    # Registrar el nuevo token OTP
    cursor.execute('''
        INSERT INTO password_reset_tokens (user_id, username, email, token_hash, expires_at, used)
        VALUES (?, ?, ?, ?, ?, 0)
    ''', (user_id, target_username, target_email, token_hash, expires_at))

    conn.commit()
    conn.close()

    # Enviar correo vía servicio SMTP o simulador institucional
    success, mail_msg = send_recovery_otp_email(target_email, otp_code, target_username, expiration_minutes=15)
    masked = mask_email(target_email)

    if success:
        return True, f"Hemos enviado un código de verificación de 6 dígitos al correo institucional ({masked}). Es válido por 15 minutos.", masked
    else:
        return False, f"Error al enviar el código de verificación: {mail_msg}", masked

def verify_and_consume_otp(username, otp_code, new_password):
    """Valida el código OTP recibido por correo y actualiza la contraseña."""
    if not otp_code or not new_password:
        return False, "Debe proporcionar el código de 6 dígitos y la nueva contraseña."

    otp_code = otp_code.strip()
    if len(otp_code) != 6 or not otp_code.isdigit():
        return False, "El código de verificación debe constar exactamente de 6 dígitos numéricos."

    if len(new_password) < 4:
        return False, "La nueva contraseña debe contener al menos 4 caracteres."

    conn = get_db_connection()
    cursor = conn.cursor()

    target_user = None
    if username and username.strip():
        cursor.execute('SELECT id, username FROM admin_users WHERE LOWER(username) = LOWER(?) LIMIT 1', (username.strip(),))
        target_user = cursor.fetchone()

    if not target_user:
        cursor.execute('SELECT id, username FROM admin_users ORDER BY id ASC LIMIT 1')
        target_user = cursor.fetchone()

    if not target_user:
        conn.close()
        return False, "No se encontró el usuario administrador."

    user_id = target_user['id']

    # Buscar el token activo más reciente
    cursor.execute('''
        SELECT id, token_hash, expires_at
        FROM password_reset_tokens
        WHERE user_id = ? AND used = 0
        ORDER BY id DESC LIMIT 1
    ''', (user_id,))
    token_row = cursor.fetchone()

    if not token_row:
        conn.close()
        return False, "No existe ninguna solicitud de código activa o ya fue utilizado. Solicite uno nuevo."

    expires_at = datetime.strptime(token_row['expires_at'], '%Y-%m-%d %H:%M:%S')
    if datetime.now() > expires_at:
        cursor.execute('UPDATE password_reset_tokens SET used = 1 WHERE id = ?', (token_row['id'],))
        conn.commit()
        conn.close()
        return False, "El código de verificación ha expirado (validez: 15 minutos). Por favor solicite uno nuevo."

    # Verificar el código
    if not check_password_hash(token_row['token_hash'], otp_code):
        conn.close()
        return False, "El código de verificación de 6 dígitos ingresado es incorrecto. Revise su correo e intente de nuevo."

    # Código válido: marcar como usado y actualizar la contraseña del usuario
    new_hash = generate_password_hash(new_password)
    cursor.execute('UPDATE password_reset_tokens SET used = 1 WHERE id = ?', (token_row['id'],))
    cursor.execute('''
        UPDATE admin_users
        SET password_hash = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (new_hash, user_id))

    conn.commit()
    conn.close()
    return True, f"¡Contraseña de '{target_user['username']}' restablecida exitosamente mediante código de correo! Ya puede iniciar sesión."

def verify_admin_credentials(username, password):
    """Valida el usuario y contraseña del administrador con hash seguro."""
    if not username or not password:
        return False
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, username, password_hash FROM admin_users WHERE LOWER(username) = LOWER(?) LIMIT 1', (username.strip(),))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return False

    stored_hash = row['password_hash']
    # Verificar con hash seguro werkzeug o soporte retrocompatible si fuese texto plano
    if stored_hash.startswith(('scrypt:', 'pbkdf2:')):
        return check_password_hash(stored_hash, password)
    else:
        is_valid = (stored_hash == password)
        if is_valid:
            update_admin_credentials(row['username'], password)
        return is_valid

def verify_recovery_key(username, recovery_key):
    """Verifica si la clave de recuperación institucional es válida contra el hash de base de datos."""
    if not recovery_key:
        return False
    recovery_key = recovery_key.strip()

    conn = get_db_connection()
    cursor = conn.cursor()
    if username and username.strip():
        cursor.execute('SELECT recovery_key_hash FROM admin_users WHERE LOWER(username) = LOWER(?) LIMIT 1', (username.strip(),))
        row = cursor.fetchone()
    else:
        cursor.execute('SELECT recovery_key_hash FROM admin_users ORDER BY id ASC LIMIT 1')
        row = cursor.fetchone()
    conn.close()

    if row and row['recovery_key_hash']:
        stored_hash = row['recovery_key_hash']
        if stored_hash.startswith(('scrypt:', 'pbkdf2:')):
            return check_password_hash(stored_hash, recovery_key)
        return secrets.compare_digest(stored_hash, recovery_key)

    # Si no hay hash en BD pero hay clave definida en variable de entorno
    if DEFAULT_RECOVERY_KEY:
        return secrets.compare_digest(recovery_key, DEFAULT_RECOVERY_KEY)

    return False

def reset_admin_password_with_recovery(username, recovery_key, new_password):
    """Restablece la contraseña del administrador validando la clave de recuperación institucional."""
    if not recovery_key or not new_password:
        return False, "Debe proporcionar la clave de recuperación institucional y la nueva contraseña."

    if len(new_password) < 4:
        return False, "La nueva contraseña debe contener al menos 4 caracteres."

    if not verify_recovery_key(username, recovery_key):
        return False, "Clave de recuperación institucional incorrecta. Verifique sus credenciales institucionales o use la recuperación por correo OTP."

    conn = get_db_connection()
    cursor = conn.cursor()

    target_user = None
    if username and username.strip():
        cursor.execute('SELECT id, username FROM admin_users WHERE LOWER(username) = LOWER(?) LIMIT 1', (username.strip(),))
        target_user = cursor.fetchone()

    if not target_user:
        cursor.execute('SELECT id, username FROM admin_users ORDER BY id ASC LIMIT 1')
        target_user = cursor.fetchone()

    if not target_user:
        conn.close()
        return False, "No se encontró ningún usuario administrador en el sistema."

    new_hash = generate_password_hash(new_password)
    cursor.execute('''
        UPDATE admin_users
        SET password_hash = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (new_hash, target_user['id']))
    conn.commit()
    conn.close()
    return True, f"¡Contraseña de '{target_user['username']}' restablecida exitosamente! Ya puede iniciar sesión con sus nuevas credenciales."

def reset_admin_password_direct(new_username='Admin', new_password='Admin'):
    """Restaura de forma directa las credenciales del administrador (utilizado por herramientas CLI de emergencia)."""
    conn = get_db_connection()
    cursor = conn.cursor()

    pass_hash = generate_password_hash(new_password)
    rec_hash = generate_password_hash(DEFAULT_RECOVERY_KEY)

    cursor.execute('SELECT id FROM admin_users ORDER BY id ASC LIMIT 1')
    row = cursor.fetchone()
    if row:
        cursor.execute('''
            UPDATE admin_users
            SET username = ?, password_hash = ?, recovery_key_hash = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (new_username.strip(), pass_hash, rec_hash, row['id']))
    else:
        cursor.execute('''
            INSERT INTO admin_users (username, password_hash, recovery_key_hash, recovery_email)
            VALUES (?, ?, ?, 'liceo.limon@mep.go.cr')
        ''', (new_username.strip(), pass_hash, rec_hash))

    conn.commit()
    conn.close()
    return True

def update_admin_credentials(new_username, new_password, new_recovery_email=None, new_recovery_key=None):
    """
    Actualiza el nombre de usuario, contraseña, correo de recuperación institucional y opcionalmente la clave maestra institucional.
    """
    if not new_username or not new_password:
        return False
    new_username = new_username.strip()
    new_hash = generate_password_hash(new_password)

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM admin_users ORDER BY id ASC LIMIT 1')
    row = cursor.fetchone()

    if row:
        update_fields = ['username = ?', 'password_hash = ?', 'updated_at = CURRENT_TIMESTAMP']
        params = [new_username, new_hash]
        if new_recovery_email and new_recovery_email.strip():
            update_fields.append('recovery_email = ?')
            params.append(new_recovery_email.strip())
        if new_recovery_key and new_recovery_key.strip():
            update_fields.append('recovery_key_hash = ?')
            params.append(generate_password_hash(new_recovery_key.strip()))

        params.append(row['id'])
        cursor.execute(f'''
            UPDATE admin_users
            SET {", ".join(update_fields)}
            WHERE id = ?
        ''', tuple(params))
    else:
        rec_key = new_recovery_key.strip() if new_recovery_key and new_recovery_key.strip() else DEFAULT_RECOVERY_KEY
        rec_hash = generate_password_hash(rec_key)
        cursor.execute('''
            INSERT INTO admin_users (username, password_hash, recovery_key_hash, recovery_email)
            VALUES (?, ?, ?, ?)
        ''', (new_username, new_hash, rec_hash, new_recovery_email.strip() if new_recovery_email else 'jeredamaya@gmail.com'))

    conn.commit()
    conn.close()
    return True

