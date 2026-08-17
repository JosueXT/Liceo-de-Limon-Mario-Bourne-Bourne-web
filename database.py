"""
==============================================================================
BASE DE DATOS (SQLite) - LICEO DE LIMÓN MARIO BOURNE BOURNE
==============================================================================
"""

import sqlite3
import os
import json
from seed_data import DEFAULT_CMS_CONTENT, DEFAULT_NEWS

DB_PATH = os.path.join(os.path.dirname(__file__), 'liceo_cms.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
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

    # Migración segura: verificar si la columna subcategory existe en news_articles
    cursor.execute("PRAGMA table_info(news_articles)")
    columns = [row[1] for row in cursor.fetchall()]
    if 'subcategory' not in columns:
        cursor.execute("ALTER TABLE news_articles ADD COLUMN subcategory TEXT DEFAULT ''")

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

    conn.commit()

    # Verificar si necesitamos rellenar datos iniciales
    cursor.execute('SELECT COUNT(*) FROM cms_content')
    if cursor.fetchone()[0] == 0:
        seed_content(conn)

    cursor.execute('SELECT COUNT(*) FROM news_articles')
    if cursor.fetchone()[0] == 0:
        seed_news(conn)

    cursor.execute('SELECT COUNT(*) FROM contact_inquiries')
    if cursor.fetchone()[0] == 0:
        seed_inquiries(conn)

    conn.close()

def seed_content(conn):
    cursor = conn.cursor()
    for key, value in DEFAULT_CMS_CONTENT.items():
        cursor.execute('''
            INSERT OR REPLACE INTO cms_content (key, value)
            VALUES (?, ?)
        ''', (key, str(value)))
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
# FUNCIONES DE CONSULTA Y ACTUALIZACIÓN (CMS & NOTICIAS)
# =============================================================================

def get_all_content():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT key, value FROM cms_content')
    rows = cursor.fetchall()
    conn.close()
    
    content = {row['key']: row['value'] for row in rows}
    for k, v in DEFAULT_CMS_CONTENT.items():
        if k not in content:
            content[k] = v
    return content

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
    return True

def get_all_news():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM news_articles ORDER BY id DESC')
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_news_by_id(news_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM news_articles WHERE id = ?', (news_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def add_news(title, category, category_slug, subcategory, date, summary, content, image, author):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO news_articles (title, category, category_slug, subcategory, date, summary, content, image, author)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (title, category, category_slug, subcategory, date, summary, content, image, author))
    new_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return new_id

def update_news(news_id, title, category, category_slug, subcategory, date, summary, content, image, author):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE news_articles
        SET title = ?, category = ?, category_slug = ?, subcategory = ?, date = ?, summary = ?, content = ?, image = ?, author = ?
        WHERE id = ?
    ''', (title, category, category_slug, subcategory, date, summary, content, image, author, news_id))
    conn.commit()
    conn.close()
    return True

def delete_news(news_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM news_articles WHERE id = ?', (news_id,))
    conn.commit()
    conn.close()
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
    return True
