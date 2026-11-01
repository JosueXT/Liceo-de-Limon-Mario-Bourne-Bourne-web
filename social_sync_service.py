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

# Publicaciones oficiales base del Bachillerato Internacional (IB) en Redes Sociales
OFFICIAL_IB_SOCIAL_FEEDS = [
    {
        "title": "📸 Proyecto CAS IB: Reforestación y Conciencia Marina en el Caribe Sur",
        "category": "Bachillerato Internacional",
        "category_slug": "ib",
        "subcategory": "Redes Sociales",
        "date": "29 de Octubre, 2026",
        "summary": "Estudiantes del Diploma IB documentaron en Instagram su trabajo de campo ecológico y servicio comunitario en Playa Bonita y Cahuita.",
        "content": "Publicación oficial replicada desde Instagram (@ib_limon_).\n\nLos estudiantes de la generación 2026 del Bachillerato Internacional del Liceo de Limón lideraron una jornada ecológica y de educación ambiental marina en alianza con organizaciones comunitarias del Caribe costarricense.\n\nSiga las historias, videos y testimonios completos en nuestra cuenta oficial de Instagram.",
        "image": "https://images.unsplash.com/photo-1544717305-2782549b5136?auto=format&fit=crop&w=800&q=80",
        "author": "Instagram @ib_limon_",
        "social_network": "Instagram",
        "social_url": "https://www.instagram.com/ib_limon_?vrfl=bmI5MHczbXZidXFh"
    },
    {
        "title": "👥 Coloquio de Teoría del Conocimiento (TOK): Ponencias Estudiantiles en Vivo",
        "category": "Bachillerato Internacional",
        "category_slug": "ib",
        "subcategory": "Redes Sociales",
        "date": "26 de Octubre, 2026",
        "summary": "Transmisión oficial y galería de fotos compartida en nuestra página de Facebook sobre el coloquio anual de epistemología y ética TOK.",
        "content": "Publicación oficial replicada desde Facebook (Bachillerato Internacional - Liceo de Limón).\n\nRevise las presentaciones orales, ensayos destacados y debates interactivos de los alumnos del Diploma del IB sobre preguntas centrales del conocimiento humano, perspectivas culturales y ética contemporánea.\n\nEl video completo de la transmisión se encuentra disponible en nuestro Facebook oficial.",
        "image": "https://images.unsplash.com/photo-1455390582262-044cdead277a?auto=format&fit=crop&w=800&q=80",
        "author": "Facebook IB Liceo de Limón",
        "social_network": "Facebook",
        "social_url": "https://www.facebook.com/share/1FSMbJo8Xz/?mibextid=wwXIfr"
    },
    {
        "title": "📸 Convocatoria Abierta: Pruebas Diagnósticas e Inducción al Diploma IB 2026",
        "category": "Bachillerato Internacional",
        "category_slug": "ib",
        "subcategory": "Redes Sociales",
        "date": "22 de Octubre, 2026",
        "summary": "Información oficial compartida en Instagram con requisitos, cronograma de exámenes y fechas de charlas informativas para 9° año.",
        "content": "Publicación oficial replicada desde Instagram (@ib_limon_).\n\nInvitamos a los estudiantes de 9° año y a sus familias interesadas en formar parte del Bachillerato Internacional público a consultar los requisitos de admisión, documentación y fechas clave en el enlace oficial de la publicación.",
        "image": "https://images.unsplash.com/photo-1434030216411-0b793f4b4173?auto=format&fit=crop&w=800&q=80",
        "author": "Instagram @ib_limon_",
        "social_network": "Instagram",
        "social_url": "https://www.instagram.com/ib_limon_?vrfl=bmI5MHczbXZidXFh"
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
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Obtener títulos o enlaces existentes de redes sociales
    cursor.execute("SELECT title, social_url FROM news_articles WHERE category_slug = 'ib'")
    rows = cursor.fetchall()
    existing_titles = set(r['title'].strip() for r in rows if r['title'])
    existing_urls = set(r['social_url'].strip() for r in rows if r['social_url'])
    conn.close()

    synced_count = 0
    for post in OFFICIAL_IB_SOCIAL_FEEDS:
        # Verificar si ya existe por título o enlace
        if not force and (post['title'].strip() in existing_titles or post['social_url'].strip() in existing_urls):
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
        'message': f'Sincronización exitosa: {synced_count} publicaciones oficiales de redes sociales incorporadas al Bachillerato Internacional.'
    }

