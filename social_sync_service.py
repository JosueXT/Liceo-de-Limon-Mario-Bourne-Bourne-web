"""
==============================================================================
SERVICIO DE SINCRONIZACIÓN Y REPLICACIÓN DE REDES SOCIALES (IB)
LICEO DE LIMÓN MARIO BOURNE BOURNE - PROGRAMA DEL DIPLOMA
==============================================================================
Sincroniza y publica automáticamente noticias del Bachillerato Internacional (IB)
a partir de las publicaciones REALES de Instagram (@ib_limon_) mediante Behold API.
==============================================================================
"""

import json
import urllib.request
import urllib.error
from datetime import datetime
from database import get_db_connection, add_news, invalidate_cms_cache, resequence_news_ids

BEHOLD_FEED_URL = "https://feeds.behold.so/W8N8DJRtNSUmqg5S5yRs"

SPANISH_MONTHS = ['', 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']

# Publicaciones oficiales y 100% REALES extraídas directamente de la cuenta oficial @ib_limon_
# Se utilizan como respaldo si no hay conexión externa en el momento de la consulta.
FALLBACK_REAL_IB_POSTS = [
    {
        "title": "🏆 ¡Limón tiene motivos para sentirse orgulloso!",
        "category": "Bachillerato Internacional",
        "category_slug": "ib",
        "subcategory": "Redes Sociales",
        "date": "30 de Octubre, 2026",
        "summary": "Felicitamos a los grupos 2, 3 y 4 por su participación en el proyecto @epicostarica, impulsado por MSC Mediterranean Shipping Company. De manera especial, felicitamos al Grupo 1, ganador del proyecto nacional.",
        "content": "🏆 ¡Limón tiene motivos para sentirse orgulloso!\n\nFelicitamos a los grupos 2, 3 y 4 por su participación en el proyecto @epicostarica , impulsado por MSC Mediterranean Shipping Company. Ser parte de esta experiencia ya es un gran logro, y reconocemos el esfuerzo, la creatividad y el compromiso ambiental de todos nuestros estudiantes.\n\nDe manera especial, felicitamos al Grupo 1, ganador del proyecto y uno de los tres finalistas a nivel nacional, con una propuesta que busca aprovechar el agua de lluvia para abastecer los sanitarios y reducir el consumo de agua potable en nuestra provincia.\n\nEl equipo está integrado por:\nJosue Amaya, Engel Zúñiga, Sofia Matarrita, Jeycob Nuñez y Annie Sánchez.\n\nEste reconocimiento es motivo de orgullo para Limón, nuestro Liceo y el Bachillerato Internacional. ¡Nuestros jóvenes demuestran que las grandes ideas también nacen en nuestra provincia!\n\n¡Felicidades a todos!\n\nLiceo de Limón Mario Bourne Bourne | Bachillerato Internacional",
        "image": "https://behold.pictures/eyJ1IjoiTEdzU2pXQkNmQ1Z6YVRCb0RHeE9Id3B3RDAyMiIsImYiOiJXOE44REpSdE5TVW1xZzVTNXlScyIsInAiOiIxODExMzQ2MTAxOTE0NTE2NyIsImgiOiIxNGl6Mm54In0.jpg?class=squareLarge",
        "author": "Instagram @ib_limon_",
        "social_network": "Instagram",
        "social_url": "https://www.instagram.com/p/DfIuZD5jrHC/"
    },
    {
        "title": "🎭 ¡Nuestras tradiciones siguen vivas en las nuevas generaciones!",
        "category": "Bachillerato Internacional",
        "category_slug": "ib",
        "subcategory": "Redes Sociales",
        "date": "30 de Octubre, 2026",
        "summary": "Los estudiantes de la sección 11-7 celebraron el Día Nacional de la Mascarada Costarricense elaborando sus propias máscaras, llenando de creatividad y color esta actividad representativa.",
        "content": "🎭 ¡Nuestras tradiciones siguen vivas en las nuevas generaciones!\n\nLos estudiantes de la sección 11-7 celebraron el Día Nacional de la Mascarada Costarricense elaborando sus propias máscaras, llenando de creatividad y color esta actividad inspirada en una de las expresiones más representativas de nuestra identidad cultural.\n\nPorque conocer nuestras raíces también es una forma de mantenerlas vivas. 🇨🇷\n\nLiceo de Limón Mario Bourne Bourne | Bachillerato Internacional",
        "image": "https://behold.pictures/eyJ1IjoiTEdzU2pXQkNmQ1Z6YVRCb0RHeE9Id3B3RDAyMiIsImYiOiJXOE44REpSdE5TVW1xZzVTNXlScyIsInAiOiIxODExOTk5OTg0MzA4NDM0NCIsImgiOiIxMzNrN211In0.jpg?class=squareLarge",
        "author": "Instagram @ib_limon_",
        "social_network": "Instagram",
        "social_url": "https://www.instagram.com/p/DfIp6NUoApo/"
    },
    {
        "title": "Dos años de esfuerzo nos han traído hasta este momento.",
        "category": "Bachillerato Internacional",
        "category_slug": "ib",
        "subcategory": "Redes Sociales",
        "date": "27 de Octubre, 2026",
        "summary": "Hoy, nuestros estudiantes de sexto año iniciaron las pruebas internacionales del Bachillerato Internacional (BI), una etapa que representa sueños, sacrificios y aprendizajes construidos con perseverancia.",
        "content": "Dos años de esfuerzo nos han traído hasta este momento.\n\nHoy, nuestros estudiantes de sexto año iniciaron las pruebas internacionales del Bachillerato Internacional (BI), una etapa que representa mucho más que evaluaciones: representa sueños, sacrificios, aprendizajes y metas construidas con perseverancia.\n\nQueridos estudiantes, confíen en todo lo que han aprendido y en las capacidades que han desarrollado. Recuerden que son mucho más que una calificación. Estamos orgullosos de la historia que han construido y de todo lo que han superado para llegar hasta aquí.\n\nAgradecemos profundamente a nuestra coordinadora, Andra Edwards Loban, por su entrega y acompañamiento, y a los profesores de todas las asignaturas por compartir sus conocimientos y ser parte fundamental de este proceso.\n\nQue cada respuesta refleje su esfuerzo y que, al terminar, puedan decir con orgullo: lo di todo.\n\n¡Les deseamos el mayor de los éxitos! Toda nuestra comunidad educativa cree en ustedes.\n\nLiceo de Limón Mario Bourne Bourne | Bachillerato Internacional",
        "image": "https://behold.pictures/eyJ1IjoiTEdzU2pXQkNmQ1Z6YVRCb0RHeE9Id3B3RDAyMiIsImYiOiJXOE44REpSdE5TVW1xZzVTNXlScyIsInAiOiIxNzk5ODYzMDI3ODA1MTk3OCIsImgiOiIxdzBnajhkIn0.jpg?class=squareLarge",
        "author": "Instagram @ib_limon_",
        "social_network": "Instagram",
        "social_url": "https://www.instagram.com/p/DfA1lBYoJT5/"
    },
    {
        "title": "¡Compartiendo experiencias que dejan huella!",
        "category": "Bachillerato Internacional",
        "category_slug": "ib",
        "subcategory": "Redes Sociales",
        "date": "10 de Octubre, 2026",
        "summary": "Nuestros estudiantes de quinto año del Bachillerato Internacional participaron en una jornada de convivencia con las personas jubiladas de COLYPRO, cerca de Playa Bonita, Limón.",
        "content": "¡Compartiendo experiencias que dejan huella!\n\nNuestros estudiantes de quinto año del Bachillerato Internacional participaron en una jornada de convivencia con las personas jubiladas de COLYPRO, cerca de Playa Bonita, Limón.\n\nEntre bailes, juegos de mesa y momentos de alegría, fortalecieron los lazos entre generaciones y pusieron en práctica valores como el respeto, la empatía y la solidaridad.\n\n¡Aprender también es compartir con nuestra comunidad!",
        "image": "https://behold.pictures/eyJ1IjoiTEdzU2pXQkNmQ1Z6YVRCb0RHeE9Id3B3RDAyMiIsImYiOiJXOE44REpSdE5TVW1xZzVTNXlScyIsInAiOiIxODAyNjU5NTczNDg2OTcwMyIsImgiOiIxeHUwMGYzIn0.jpg?class=squareLarge",
        "author": "Instagram @ib_limon_",
        "social_network": "Instagram",
        "social_url": "https://www.instagram.com/p/DeS8i6Ijn2z/"
    },
    {
        "title": "🌎 ¿Por qué elegir el Bachillerato Internacional?",
        "category": "Bachillerato Internacional",
        "category_slug": "ib",
        "subcategory": "Redes Sociales",
        "date": "24 de Septiembre, 2026",
        "summary": "Elegir el Programa del Diploma del Bachillerato Internacional es apostar por una formación que va más allá del aula. Formación con visión global y excelencia académica.",
        "content": "🌎 ¿Por qué elegir el Bachillerato Internacional?\n\nElegir el Programa del Diploma del Bachillerato Internacional es apostar por una formación que va más allá del aula.\n\nDeslizá y descubrí por qué elegir el Bachillerato Internacional. ✨",
        "image": "https://behold.pictures/eyJ1IjoiTEdzU2pXQkNmQ1Z6YVRCb0RHeE9Id3B3RDAyMiIsImYiOiJXOE44REpSdE5TVW1xZzVTNXlScyIsInAiOiIxNzg4Njg0MjcxNTQ3OTA2NCIsImgiOiI2bjhpZW8ifQ.jpg?class=squareLarge",
        "author": "Instagram @ib_limon_",
        "social_network": "Instagram",
        "social_url": "https://www.instagram.com/p/DdpmlK2jnZu/"
    },
    {
        "title": "Celebramos nuestra independencia 🙌🏼🇨🇷",
        "category": "Bachillerato Internacional",
        "category_slug": "ib",
        "subcategory": "Redes Sociales",
        "date": "16 de Septiembre, 2026",
        "summary": "Con orgullo y alegría conmemoramos el Día de la Independencia de Costa Rica, participando en el tradicional desfile y celebrando juntos nuestra identidad, cultura y valores.",
        "content": "Celebramos nuestra independencia 🙌🏼🇨🇷\n\nCon orgullo y alegría conmemoramos el Día de la Independencia de Costa Rica, participando en el tradicional desfile y celebrando juntos nuestra identidad, cultura y valores.\n\n¡Viva Costa Rica! 🇨🇷🇨🇷",
        "image": "https://behold.pictures/eyJ1IjoiTEdzU2pXQkNmQ1Z6YVRCb0RHeE9Id3B3RDAyMiIsImYiOiJXOE44REpSdE5TVW1xZzVTNXlScyIsInAiOiIxODQwNjM0NTE4MDA4MDgzMSIsImgiOiIxYnd4OTU5In0.jpg?class=squareLarge",
        "author": "Instagram @ib_limon_",
        "social_network": "Instagram",
        "social_url": "https://www.instagram.com/p/DdVTXScjhhx/"
    }
]

def fetch_live_behold_posts():
    """
    Consulta en tiempo real la API de Behold.so para extraer las publicaciones
    oficiales más recientes de la cuenta de Instagram @ib_limon_.
    """
    try:
        req = urllib.request.Request(
            BEHOLD_FEED_URL,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) LiceoDeLimonIB/1.0',
                'Accept': 'application/json'
            }
        )
        with urllib.request.urlopen(req, timeout=4) as response:
            if response.status != 200:
                return None
            data = json.loads(response.read().decode('utf-8'))

        raw_posts = data.get('posts', [])
        if not raw_posts:
            return None

        parsed_posts = []
        for p in raw_posts:
            raw_caption = (p.get('prunedCaption') or p.get('caption') or '').strip()
            lines = [l.strip() for l in raw_caption.split('\n') if l.strip()]
            first_line = lines[0] if lines else "Publicación Oficial de Instagram"
            title = first_line[:110]

            summary = lines[1] if len(lines) > 1 else lines[0] if lines else ''
            if len(summary) > 220:
                summary = summary[:217] + '...'

            ts = p.get('timestamp')
            if ts:
                try:
                    dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
                    date_str = f"{dt.day} de {SPANISH_MONTHS[dt.month]}, {dt.year}"
                except Exception:
                    date_str = "Reciente"
            else:
                date_str = "Reciente"

            sizes = p.get('sizes') or {}
            img_url = (
                sizes.get('large', {}).get('mediaUrl') or
                sizes.get('medium', {}).get('mediaUrl') or
                sizes.get('small', {}).get('mediaUrl') or
                p.get('mediaUrl') or ''
            )

            permalink = p.get('permalink') or 'https://www.instagram.com/ib_limon_/'

            parsed_posts.append({
                "title": title,
                "category": "Bachillerato Internacional",
                "category_slug": "ib",
                "subcategory": "Redes Sociales",
                "date": date_str,
                "summary": summary,
                "content": raw_caption,
                "image": img_url,
                "author": "Instagram @ib_limon_",
                "social_network": "Instagram",
                "social_url": permalink
            })

        return parsed_posts
    except Exception:
        return None

def sync_ib_social_posts(force=False):
    """
    Inserta o sincroniza las publicaciones oficiales y REALES de Instagram (@ib_limon_)
    en la tabla news_articles, asegurando:
    1. Subcategoría exclusiva 'Redes Sociales'.
    2. Cero duplicados (deduplicación por enlace social_url y título).
    3. Si el usuario eliminó una publicación (deleted_social_posts), NO se vuelve a insertar.
    4. Si el docente o administrador desactivó una publicación (is_active = 0), NUNCA se reactiva automáticamente.
    5. Solo publicaciones auténticas de la institución.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Obtener lista de publicaciones bloqueadas/eliminadas voluntariamente por el usuario
    blocked_items = set()
    generic_profiles = (
        'https://www.instagram.com/ib_limon_',
        'https://www.facebook.com/share/1FSMbJo8Xz'
    )
    try:
        cursor.execute("SELECT value FROM cms_content WHERE key = 'deleted_social_posts'")
        val_row = cursor.fetchone()
        if val_row and val_row[0]:
            raw_blocked = set(json.loads(val_row[0]))
            blocked_items = set(x for x in raw_blocked if not any(x.rstrip('/') == gp.rstrip('/') for gp in generic_profiles))
    except Exception:
        pass

    # 2. Obtener noticias existentes de redes sociales en la base de datos
    cursor.execute("SELECT id, title, social_url, is_active FROM news_articles WHERE category_slug = 'ib'")
    rows = cursor.fetchall()
    existing_titles = set(r['title'].strip() for r in rows if r['title'])
    existing_urls = set(r['social_url'].strip() for r in rows if r['social_url'])
    conn.close()

    # 3. Intentar obtener publicaciones en vivo desde Behold; si falla, usar publicaciones reales de respaldo
    posts_to_sync = fetch_live_behold_posts()
    if not posts_to_sync:
        posts_to_sync = FALLBACK_REAL_IB_POSTS

    synced_count = 0
    for post in posts_to_sync:
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
        'message': f'Sincronización completada: {synced_count} publicaciones oficiales de Instagram integradas.'
    }
