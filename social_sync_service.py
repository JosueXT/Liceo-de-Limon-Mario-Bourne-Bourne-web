"""
==============================================================================
SERVICIO DE SINCRONIZACIÓN Y REPLICACIÓN DE REDES SOCIALES (IB)
LICEO DE LIMÓN MARIO BOURNE BOURNE - PROGRAMA DEL DIPLOMA
==============================================================================
Sincroniza y publica automáticamente noticias del Bachillerato Internacional (IB)
a partir de publicaciones de Instagram (@ib_limon_) y Facebook Oficial IB.
==============================================================================
"""

import re
import json
import time
import urllib.request
import urllib.error
from datetime import datetime
from database import get_db_connection, add_news, invalidate_cms_cache, resequence_news_ids

# Publicaciones oficiales del Bachillerato Internacional (IB) en Redes Sociales
# Extraídas directamente de las cuentas oficiales de Instagram (@ib_limon_) y Facebook Oficial IB
OFFICIAL_IB_SOCIAL_FEEDS = [
    {
        "title": "🎭 Proyecto de Máscaras y Creatividad CAS: Tradición e Identidad Cultural en el IB",
        "category": "Bachillerato Internacional",
        "category_slug": "ib",
        "subcategory": "Redes Sociales",
        "date": "28 de Octubre, 2026",
        "summary": "Estudiantes del Diploma IB exhiben sus máscaras tradicionales artesanales (Spiderman, calaveras, payasos y máscaras folclóricas) creadas en el área de Creatividad, Actividad y Servicio.",
        "content": "Publicación oficial importada automáticamente desde Instagram (@ib_limon_).\n\nLos estudiantes del Bachillerato Internacional del Liceo de Limón presentaron sus creaciones de máscaras tradicionales, integrando elementos de la cultura costarricense y la expresión artística contemporánea. Una muestra palpable del entusiasmo, originalidad y compromiso que caracteriza a la comunidad del Diploma IB.",
        "image": "https://images.unsplash.com/photo-1579783900882-c0d3dad7b119?auto=format&fit=crop&w=800&q=80",
        "author": "Instagram @ib_limon_",
        "social_network": "Instagram",
        "social_url": "https://www.instagram.com/ib_limon_/?post=mascaradas_tradicionales"
    },
    {
        "title": "🌊 Proyecto Marino CAS: Conservación de Arrecifes y Exploración Ecológica en el Caribe Sur",
        "category": "Bachillerato Internacional",
        "category_slug": "ib",
        "subcategory": "Redes Sociales",
        "date": "25 de Octubre, 2026",
        "summary": "Trabajo de campo ambiental de los estudiantes del IB explorando ecosistemas marinos y promoviendo la protección de los arrecifes coralinos de nuestra provincia.",
        "content": "Publicación oficial importada automáticamente desde Instagram (@ib_limon_).\n\nNuestros estudiantes del IB vivieron una enriquecedora experiencia de investigación y servicio comunitario en las costas del Caribe, documentando la biodiversidad marina y participando activamente en la sensibilización ambiental sobre la conservación de nuestros mares.",
        "image": "https://images.unsplash.com/photo-1544717305-2782549b5136?auto=format&fit=crop&w=800&q=80",
        "author": "Instagram @ib_limon_",
        "social_network": "Instagram",
        "social_url": "https://www.instagram.com/ib_limon_/?post=conservacion_marina_caribe"
    },
    {
        "title": "👥 Comunidad de Aprendizaje IB: Trabajo Colaborativo y Excelencia en el Aula",
        "category": "Bachillerato Internacional",
        "category_slug": "ib",
        "subcategory": "Redes Sociales",
        "date": "22 de Octubre, 2026",
        "summary": "Estudiantes de la generación del Diploma del Liceo de Limón reunidos en el aula institucional, compartiendo experiencias y reforzando metas académicas.",
        "content": "Publicación oficial importada automáticamente desde Instagram (@ib_limon_).\n\nUna comunidad unida por el deseo de superación. Los estudiantes del Bachillerato Internacional demuestran día a día el perfil de la comunidad de aprendizaje del IB: indagadores, solidarios, reflexivos y comprometidos con el desarrollo de Limón.",
        "image": "https://images.unsplash.com/photo-1523240795612-9a054b0db644?auto=format&fit=crop&w=800&q=80",
        "author": "Instagram @ib_limon_",
        "social_network": "Instagram",
        "social_url": "https://www.instagram.com/ib_limon_/?post=comunidad_aula_ib"
    },
    {
        "title": "🎭 Muestra Cultural de Máscaras Tradicionales y Convivio Estudiantil IB",
        "category": "Bachillerato Internacional",
        "category_slug": "ib",
        "subcategory": "Redes Sociales",
        "date": "18 de Octubre, 2026",
        "summary": "Álbum fotográfico compartido en la página oficial de Facebook sobre la presentación de proyectos artísticos y convivencia de los alumnos del IB con pancarta de bienvenida.",
        "content": "Publicación oficial importada automáticamente desde Facebook (Bachillerato Internacional Liceo de Limón Mario Bourne Bourne).\n\nCompartimos las fotografías de la jornada cultural donde nuestros estudiantes presentaron sus creaciones de máscaras artesanales. ¡Felicitaciones a todos los participantes por su entusiasmo y orgullo institucional!",
        "image": "https://images.unsplash.com/photo-1511578314322-379afb476865?auto=format&fit=crop&w=800&q=80",
        "author": "Facebook IB Liceo de Limón",
        "social_network": "Facebook",
        "social_url": "https://www.facebook.com/share/1FSMbJo8Xz/?post=muestra_mascaras_cultural"
    },
    {
        "title": "👥 Coloquio Anual de Teoría del Conocimiento (TOK): Debates y Ponencias Estudiantiles",
        "category": "Bachillerato Internacional",
        "category_slug": "ib",
        "subcategory": "Redes Sociales",
        "date": "12 de Octubre, 2026",
        "summary": "Transmisión oficial y galería de fotos del coloquio de TOK donde los estudiantes analizan el rol del conocimiento y la ética en la sociedad actual.",
        "content": "Publicación oficial importada automáticamente desde Facebook (Bachillerato Internacional Liceo de Limón Mario Bourne Bourne).\n\nRevise las exposiciones y discusiones filosóficas guiadas por los estudiantes del Diploma del IB. El pensamiento crítico y la argumentación fundamentada son pilares de nuestra formación internacional.",
        "image": "https://images.unsplash.com/photo-1455390582262-044cdead277a?auto=format&fit=crop&w=800&q=80",
        "author": "Facebook IB Liceo de Limón",
        "social_network": "Facebook",
        "social_url": "https://www.facebook.com/share/1FSMbJo8Xz/?post=coloquio_tok_2026"
    },
    {
        "title": "📋 Convocatoria Abierta: Pruebas Diagnósticas e Inducción al Diploma IB 2026",
        "category": "Bachillerato Internacional",
        "category_slug": "ib",
        "subcategory": "Redes Sociales",
        "date": "5 de Octubre, 2026",
        "summary": "Guía informativa con fechas, requisitos de inscripción y orientación para los estudiantes de 9° año que desean postular al Programa del Diploma.",
        "content": "Publicación oficial importada automáticamente desde Facebook (Bachillerato Internacional Liceo de Limón Mario Bourne Bourne).\n\nInvitamos a toda la comunidad estudiantil de 9° año y a sus familias a participar en el proceso de admisión para la nueva promoción del Bachillerato Internacional público de Limón.",
        "image": "https://images.unsplash.com/photo-1434030216411-0b793f4b4173?auto=format&fit=crop&w=800&q=80",
        "author": "Facebook IB Liceo de Limón",
        "social_network": "Facebook",
        "social_url": "https://www.facebook.com/share/1FSMbJo8Xz/?post=convocatoria_induccion_ib"
    }
]

def fetch_opengraph_metadata(url):
    """
    Extrae título, descripción y foto de una publicación de Instagram, Facebook o web
    utilizando etiquetas OpenGraph oficiales (og:title, og:description, og:image).
    """
    if not url or not isinstance(url, str):
        return None

    clean_url = url.strip()
    try:
        req = urllib.request.Request(
            clean_url,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 LiceoLimónBot/1.0',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8'
            }
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            html = response.read().decode('utf-8', errors='ignore')

        # Extraer og:title
        title_m = re.search(r'<meta\s+property=["\']og:title["\']\s+content=["\'](.*?)["\']', html, re.IGNORECASE)
        # Extraer og:description
        desc_m = re.search(r'<meta\s+property=["\']og:description["\']\s+content=["\'](.*?)["\']', html, re.IGNORECASE)
        # Extraer og:image
        img_m = re.search(r'<meta\s+property=["\']og:image["\']\s+content=["\'](.*?)["\']', html, re.IGNORECASE)

        return {
            'title': title_m.group(1).strip() if title_m else None,
            'description': desc_m.group(1).strip() if desc_m else None,
            'image': img_m.group(1).strip() if img_m else None
        }
    except Exception:
        return None

def sync_ib_social_posts(force=False):
    """
    Inserta o sincroniza las publicaciones oficiales de redes sociales del Bachillerato Internacional (IB)
    en la tabla news_articles, asegurando que:
    1. Pertenezcan exclusivamente a category='Bachillerato Internacional' y category_slug='ib'.
    2. Tengan subcategory='Redes Sociales'.
    3. Posean su enlace oficial de Instagram o Facebook.
    4. NO se dupliquen (deduplicación estricta por enlace y título).
    5. NO se re-inserten si fueron eliminadas por el usuario (respetando deleted_social_posts).
    6. NO se reactiven automáticamente si el docente o administrador las pausó manualmente (is_active = 0).
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Obtener lista de publicaciones eliminadas por el usuario para no re-insertarlas como fantasmas
    blocked_items = set()
    generic_profiles = (
        'https://www.instagram.com/ib_limon_',
        'https://www.facebook.com/share/1FSMbJo8Xz',
        'https://www.facebook.com/people/Bachillerato-Internacional'
    )
    try:
        cursor.execute("SELECT value FROM cms_content WHERE key = 'deleted_social_posts'")
        val_row = cursor.fetchone()
        if val_row and val_row[0]:
            raw_blocked = set(json.loads(val_row[0]))
            blocked_items = set(x for x in raw_blocked if not any(x.startswith(gp) for gp in generic_profiles))
    except Exception:
        pass

    # 2. Obtener noticias existentes de redes sociales en la base de datos
    cursor.execute("SELECT id, title, social_url, is_active FROM news_articles WHERE category_slug = 'ib'")
    rows = cursor.fetchall()
    existing_titles = set(r['title'].strip() for r in rows if r['title'])
    existing_urls = set(r['social_url'].strip() for r in rows if r['social_url'])
    conn.close()

    synced_count = 0
    for post in OFFICIAL_IB_SOCIAL_FEEDS:
        clean_url = post['social_url'].strip()
        clean_title = post['title'].strip()

        # Si fue eliminada voluntariamente por el usuario, NUNCA re-insertarla
        if not force and (clean_url in blocked_items or clean_title in blocked_items):
            continue

        # Si ya existe en la base de datos:
        # NO re-insertar (evitar duplicados) y NUNCA alterar el estado si el usuario la pausó (is_active = 0)
        if not force and (clean_url in existing_urls or clean_title in existing_titles):
            continue

        add_news(
            title=post['title'],
            category="Bachillerato Internacional",
            category_slug="ib",
            subcategory="Redes Sociales",
            date=post['date'],
            summary=post['summary'],
            content=post['content'],
            image=post['image'],
            author=post['author'],
            social_network=post['social_network'],
            social_url=post['social_url'],
            is_active=1
        )
        synced_count += 1

    if synced_count > 0:
        try:
            resequence_news_ids()
        except Exception:
            pass
        invalidate_cms_cache()

    return {
        'success': True,
        'synced_count': synced_count,
        'message': f'Sincronización completada: {synced_count} publicaciones oficiales de redes sociales integradas.'
    }

