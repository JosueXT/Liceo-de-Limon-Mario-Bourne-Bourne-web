"""
==============================================================================
SERVICIO DE INTELIGENCIA ARTIFICIAL GOOGLE GEMINI - LICEO DE LIMÓN (MEP)
==============================================================================
Genera resúmenes semánticos y títulos inteligentes para copias de seguridad
automáticas cada vez que se guardan cambios en el CMS o se publican noticias.
==============================================================================
"""

import os
import json
import time
import urllib.request
import urllib.error
from email_service import load_env_file

# Modelos recomendados en orden de prioridad para baja latencia
GEMINI_MODELS = [
    'gemini-3.5-flash',
    'gemini-3.7-flash',
    'gemini-3.8-flash',
    'gemini-flash-latest'
]

def get_gemini_api_key():
    """Obtiene la clave de API de Gemini desde variables de entorno."""
    load_env_file()
    return os.environ.get('GEMINI_API_KEY', '').strip()

def check_gemini_health():
    """Diagnóstico en tiempo real del estado de conexión con Google Gemini."""
    if os.environ.get('TESTING') == 'True':
        return {
            'active': True,
            'model': 'gemini-3.5-flash',
            'latency_ms': 15.0,
            'total_models': 50,
            'message': 'Modo de pruebas unitarias activo (Simulación de IA).'
        }

    api_key = get_gemini_api_key()
    if not api_key:
        return {
            'active': False,
            'model': 'No configurado',
            'latency_ms': 0,
            'message': 'API Key no configurada en variables de entorno.'
        }

    t0 = time.time()
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'LiceoDeLimon-CMS/2.0'})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            latency = (time.time() - t0) * 1000
            has_flash = any('3.5-flash' in m.get('name', '') or 'flash' in m.get('name', '') for m in data.get('models', []))
            return {
                'active': True,
                'model': 'gemini-3.5-flash' if has_flash else 'gemini-flash-latest',
                'latency_ms': round(latency, 1),
                'total_models': len(data.get('models', [])),
                'message': 'Conexión activa con Google Gemini.'
            }
    except Exception as e:
        latency = (time.time() - t0) * 1000
        return {
            'active': False,
            'model': 'Error de conexión',
            'latency_ms': round(latency, 1),
            'error': str(e),
            'message': f'No fue posible contactar con Google Gemini: {str(e)}'
        }

def _friendly_field_name(key):
    """Mapea claves técnicas de CMS a nombres legibles en español."""
    labels = {
        'site_title': 'Título del sitio',
        'site_logo': 'Logotipo institucional',
        'hero_title': 'Título de portada',
        'hero_subtitle': 'Subtítulo de portada',
        'hero_image': 'Foto de portada',
        'social_section_title': 'Título de redes sociales',
        'social_section_subtitle': 'Subtítulo de redes',
        'facebook_name': 'Página de Facebook',
        'facebook_handle': 'Usuario de Facebook',
        'facebook_url': 'Enlace de Facebook',
        'facebook_desc': 'Descripción de Facebook',
        'facebook_btn_text': 'Botón de Facebook',
        'instagram_title': 'Tarjeta de Instagram',
        'instagram_name': 'Usuario de Instagram',
        'instagram_url': 'Enlace de Instagram',
        'instagram_desc': 'Descripción de Instagram',
        'instagram_btn_text': 'Botón de Instagram',
        'whatsapp_name': 'Canal de WhatsApp',
        'whatsapp_handle': 'Usuario de WhatsApp',
        'whatsapp_url': 'Enlace de WhatsApp',
        'whatsapp_desc': 'Descripción de WhatsApp',
        'whatsapp_btn_text': 'Botón de WhatsApp',
        'ib_title': 'Título Bachillerato Internacional',
        'ib_hero_subtitle': 'Subtítulo modalidad IB',
        'ib_contact_phone': 'Teléfono de Coordinación IB',
        'ib_contact_email': 'Correo de Coordinación IB',
        'french_title': 'Título Francés Avanzado',
        'regular_title': 'Título Secundaria Regular',
        'contact_phone': 'Teléfono institucional',
        'contact_email': 'Correo de contacto'
    }
    if key in labels:
        return labels[key]
    clean = key.replace('_', ' ').title()
    return clean

def generate_backup_title(changed_items, fallback_label="Actualización de contenidos"):
    """
    Utiliza Google Gemini para analizar los campos modificados y generar un título
    breve, conciso y semántico para el punto de restauración.
    """
    if not changed_items:
        return fallback_label

    if os.environ.get('TESTING') == 'True':
        keys = list(changed_items.keys())[:3]
        friendly = [_friendly_field_name(k) for k in keys]
        suffix = f" y {len(changed_items) - 3} más" if len(changed_items) > 3 else ""
        return f"✨ Actualización: {', '.join(friendly)}{suffix}"

    api_key = get_gemini_api_key()
    if not api_key:
        # Fallback sin IA: lista compacta de campos modificados
        keys = list(changed_items.keys())[:3]
        friendly = [_friendly_field_name(k) for k in keys]
        suffix = f" y {len(changed_items) - 3} más" if len(changed_items) > 3 else ""
        return f"Actualización: {', '.join(friendly)}{suffix}"

    # Construir descripción legible de los cambios
    changes_desc_list = []
    for k, v in list(changed_items.items())[:8]:
        fname = _friendly_field_name(k)
        if isinstance(v, dict) and 'new' in v:
            new_val = str(v['new'])[:60]
            changes_desc_list.append(f"- {fname}: '{new_val}'")
        else:
            val_str = str(v)[:60]
            changes_desc_list.append(f"- {fname}: '{val_str}'")

    summary_text = "\n".join(changes_desc_list)

    prompt = (
        "Genera un título muy breve (máximo de 6 a 8 palabras) en español para una copia de seguridad "
        "de la página web del Liceo de Limón Mario Bourne Bourne que resuma los siguientes cambios realizados:\n"
        f"{summary_text}\n\n"
        "Reglas estrictas:\n"
        "1. Responde ÚNICAMENTE con el título en una sola línea.\n"
        "2. No uses comillas, asteriscos, markdown ni introducciones.\n"
        "3. Sé profesional, directo y descriptivo."
    )

    payload = {
        'contents': [{
            'parts': [{'text': prompt}]
        }],
        'generationConfig': {
            'temperature': 0.2,
            'maxOutputTokens': 50
        }
    }

    # Intentar con la lista de modelos rápidos
    for model in GEMINI_MODELS:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode('utf-8'),
                headers={'Content-Type': 'application/json', 'User-Agent': 'LiceoDeLimon-CMS/2.0'}
            )
            with urllib.request.urlopen(req, timeout=6) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                title = data['candidates'][0]['content']['parts'][0]['text'].strip()
                # Limpiar saltos de línea y caracteres extras
                title = title.replace('\n', ' ').strip().strip('"\'')
                if len(title) > 80:
                    title = title[:77] + "..."
                return f"✨ {title}"
        except Exception:
            continue

    # Fallback si todos los modelos fallan o no hay conexión
    keys = list(changed_items.keys())[:3]
    friendly = [_friendly_field_name(k) for k in keys]
    suffix = f" (+{len(changed_items) - 3})" if len(changed_items) > 3 else ""
    return f"Actualización: {', '.join(friendly)}{suffix}"

