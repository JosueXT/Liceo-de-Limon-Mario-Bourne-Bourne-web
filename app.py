"""
==============================================================================
SERVIDOR PRINCIPAL (FLASK) - LICEO DE LIMÓN MARIO BOURNE BOURNE (MEP)
==============================================================================
"""

import os
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, Response
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

app = Flask(__name__)
# Clave secreta para firmar sesiones seguras
app.secret_key = os.environ.get('SECRET_KEY', 'liceo-limon-mario-bourne-mep-secret-key-2026')

# Inicializar Base de Datos SQLite al arrancar la aplicación
init_db()

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

# =============================================================================
# 1. RUTAS PÚBLICAS
# =============================================================================

@app.route('/')
def home():
    """Ruta Principal Pública: Carga el sitio institucional con los contenidos del CMS"""
    cms = get_all_content()
    news = get_all_news()
    is_admin = session.get('is_admin', False)
    pathway_features = get_pathway_features(cms)
    return render_template(
        'index.html',
        cms=cms,
        news=news,
        is_admin=is_admin,
        pathway_features=pathway_features
    )

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
    dynamic_lists = get_modality_dynamic_lists(slug, cms)

    return render_template(
        'modalidad.html',
        modalidad=modalidad_info,
        cms=cms,
        is_admin=is_admin,
        dynamic_lists=dynamic_lists
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

    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()

    if verify_admin_credentials(username, password):
        session['is_admin'] = True
        session['admin_username'] = username
        return redirect(url_for('admin_panel'))
    else:
        return render_template('login.html', cms=cms, error='Credenciales incorrectas. Verifique su usuario y contraseña.')

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    """Cierra la sesión administrativa y redirige al inicio público."""
    session.pop('is_admin', None)
    session.pop('admin_username', None)
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
    current_recovery_email = (admin_user['recovery_email'] if admin_user and admin_user.get('recovery_email') else 'liceo.limon@mep.go.cr')

    cms = get_all_content()
    news = get_all_news()
    inquiries = get_all_inquiries()
    snapshots = get_all_snapshots()
    return render_template('admin_panel.html', cms=cms, news=news, inquiries=inquiries, snapshots=snapshots, current_admin_username=current_admin_username, current_recovery_email=current_recovery_email)

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
    """Valida credenciales dinámicas en base de datos con hash seguro."""
    data = request.get_json() or {}
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()

    if verify_admin_credentials(username, password):
        session['is_admin'] = True
        session['admin_username'] = username
        return jsonify({
            'success': True,
            'message': 'Autenticación exitosa.',
            'redirect': '/admin/panel'
        })
    else:
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
    """Permite al personal directivo restablecer la contraseña en caso de olvido validando la clave de recuperación institucional."""
    data = request.get_json() or {}
    username = data.get('username', '').strip()
    recovery_key = data.get('recovery_key', '').strip()
    new_password = data.get('new_password', '').strip()

    if not recovery_key:
        return jsonify({
            'success': False,
            'message': 'Debe ingresar la Clave Maestra de Recuperación Institucional (o código de rescate).'
        }), 400

    if not new_password or len(new_password) < 4:
        return jsonify({
            'success': False,
            'message': 'La nueva contraseña debe contener un mínimo de 4 caracteres.'
        }), 400

    success, message = reset_admin_password_with_recovery(username, recovery_key, new_password)
    if success:
        return jsonify({
            'success': True,
            'message': message
        })
    else:
        return jsonify({
            'success': False,
            'message': message
        }), 401

@app.route('/api/auth/request-otp', methods=['POST'])
def api_request_otp():
    """Genera y envía un código temporal de 6 dígitos (OTP) al correo institucional de recuperación."""
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
    """Valida el código temporal recibido por correo y actualiza la contraseña."""
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
        return jsonify({'success': True, 'message': message})
    else:
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

    new_recovery_key = data.get('new_recovery_key', '').strip()
    if new_recovery_key and len(new_recovery_key) < 4:
        return jsonify({'success': False, 'message': 'La nueva clave maestra institucional debe tener un mínimo de 4 caracteres.'}), 400

    success = update_admin_credentials(
        new_username,
        new_password,
        new_recovery_email if new_recovery_email else None,
        new_recovery_key if new_recovery_key else None
    )
    if success:
        session['admin_username'] = new_username
        return jsonify({
            'success': True,
            'message': '¡Credenciales actualizadas exitosamente! Se utilizarán en los próximos inicios de sesión.',
            'new_username': new_username,
            'new_recovery_email': new_recovery_email or admin_user.get('recovery_email', 'liceo.limon@mep.go.cr'),
            'updated_recovery_key': bool(new_recovery_key)
        })
    else:
        return jsonify({'success': False, 'message': 'Error al actualizar credenciales en base de datos.'}), 500


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
    summary = data.get('summary', '').strip()
    content = data.get('content', '').strip()
    image = data.get('image', '').strip()
    author = data.get('author', 'Liceo de Limón MEP').strip()

    if not title or not summary:
        return jsonify({'success': False, 'message': 'El título y el resumen son obligatorios.'}), 400

    update_news(news_id, title, category, category_slug, subcategory, date, summary, content, image, author)
    return jsonify({
        'success': True,
        'message': f'Comunicado #{news_id} actualizado exitosamente.'
    })

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
    name = data.get('name') or "Copia Importada"

    if not isinstance(content, dict):
        return jsonify({'success': False, 'message': 'Estructura de respaldo no válida.'}), 400

    new_id = import_snapshot(name, content, news)

    apply_now = request.form.get('apply_now') == 'true' or (request.is_json and (request.get_json() or {}).get('apply_now'))
    if apply_now:
        restore_snapshot(new_id)

    return jsonify({
        'success': True,
        'message': f'Respaldo "{name}" importado exitosamente con ID #{new_id}.',
        'snapshot_id': new_id
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
