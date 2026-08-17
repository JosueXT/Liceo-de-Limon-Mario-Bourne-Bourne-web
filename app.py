"""
==============================================================================
SERVIDOR PRINCIPAL (FLASK) - LICEO DE LIMÓN MARIO BOURNE BOURNE (MEP)
==============================================================================
"""

import os
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
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
    reset_to_defaults
)
from seed_data import MODALIDADES_DETALLE

app = Flask(__name__)
# Clave secreta para firmar sesiones seguras
app.secret_key = os.environ.get('SECRET_KEY', 'liceo-limon-mario-bourne-mep-secret-key-2026')

# Inicializar Base de Datos SQLite al arrancar la aplicación
init_db()

# =============================================================================
# 1. RUTAS PÚBLICAS
# =============================================================================

@app.route('/')
def home():
    """Ruta Principal Pública: Carga el sitio institucional con los contenidos del CMS"""
    cms = get_all_content()
    news = get_all_news()
    is_admin = session.get('is_admin', False)
    return render_template('index.html', cms=cms, news=news, is_admin=is_admin)

@app.route('/modalidad/<slug>')
@app.route('/oferta/<slug>')
def modalidad_detalle(slug):
    """Subpáginas dedicadas de oferta educativa (ib, frances, regular)"""
    slug = slug.lower().strip()
    if slug not in MODALIDADES_DETALLE:
        return redirect(url_for('home') + '#modalidades')

    modalidad_info = MODALIDADES_DETALLE[slug]
    cms = get_all_content()
    is_admin = session.get('is_admin', False)

    return render_template(
        'modalidad.html',
        modalidad=modalidad_info,
        cms=cms,
        is_admin=is_admin
    )

# =============================================================================
# 2. SUBPÁGINA DEDICADA DE INICIO DE SESIÓN
# =============================================================================

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Subpágina dedicada de Inicio de Sesión."""
    if request.method == 'GET':
        if session.get('is_admin', False):
            return redirect(url_for('admin_panel'))
        return render_template('login.html')

    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()

    if username == 'Admin' and password == 'Admin':
        session['is_admin'] = True
        return redirect(url_for('admin_panel'))
    else:
        return render_template('login.html', error='Credenciales incorrectas (Usuario: Admin / Contraseña: Admin)')

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    """Cierra la sesión administrativa y redirige al inicio público."""
    session.pop('is_admin', None)
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

    cms = get_all_content()
    news = get_all_news()
    inquiries = get_all_inquiries()
    return render_template('admin_panel.html', cms=cms, news=news, inquiries=inquiries)

# =============================================================================
# 4. ENDPOINTS API REST (FORMULARIO DE CONTACTO PÚBLICO)
# =============================================================================

@app.route('/api/contact/submit', methods=['POST'])
def api_submit_contact():
    """Recibe y guarda las consultas enviadas desde el formulario institucional público"""
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
    """Valida credenciales estrictas: Usuario: Admin / Contraseña: Admin"""
    data = request.get_json() or {}
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()

    if username == 'Admin' and password == 'Admin':
        session['is_admin'] = True
        return jsonify({
            'success': True,
            'message': 'Autenticación exitosa.',
            'redirect': '/admin/panel'
        })
    else:
        return jsonify({
            'success': False,
            'message': 'Usuario o contraseña incorrectos. (Usuario: Admin / Contraseña: Admin)'
        }), 401

@app.route('/api/auth/logout', methods=['POST'])
def api_logout():
    session.pop('is_admin', None)
    return jsonify({'success': True, 'message': 'Sesión cerrada correctamente.'})

@app.route('/api/cms/content', methods=['GET'])
def api_get_content():
    content = get_all_content()
    return jsonify({'success': True, 'content': content})

@app.route('/api/cms/content', methods=['POST', 'PUT'])
def api_save_content():
    if not session.get('is_admin', False):
        return jsonify({'success': False, 'message': 'No autorizado. Inicie sesión.'}), 403

    data = request.get_json() or {}
    items = data.get('items', {})
    if not items and isinstance(data, dict):
        items = data

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
    summary = data.get('summary', '').strip()
    content = data.get('content', '').strip()
    image = data.get('image', 'https://images.unsplash.com/photo-1523240795612-9a054b0db644?auto=format&fit=crop&w=800&q=80').strip()
    author = data.get('author', 'Liceo de Limón MEP').strip()

    if not title or not summary:
        return jsonify({'success': False, 'message': 'El título y el resumen son obligatorios.'}), 400

    new_id = add_news(title, category, category_slug, subcategory, date, summary, content, image, author)
    return jsonify({
        'success': True,
        'message': 'Comunicado institucional publicado exitosamente.',
        'news_id': new_id
    })

@app.route('/api/cms/news/<int:news_id>', methods=['DELETE'])
def api_delete_news(news_id):
    if not session.get('is_admin', False):
        return jsonify({'success': False, 'message': 'No autorizado.'}), 403

    delete_news(news_id)
    return jsonify({'success': True, 'message': f'Noticia #{news_id} eliminada.'})

@app.route('/api/cms/reset', methods=['POST'])
def api_reset_defaults():
    if not session.get('is_admin', False):
        return jsonify({'success': False, 'message': 'No autorizado.'}), 403

    reset_to_defaults()
    return jsonify({'success': True, 'message': 'Contenidos y consultas restaurados a valores iniciales.'})

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
