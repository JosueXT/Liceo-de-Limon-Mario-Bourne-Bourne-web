#!/usr/bin/env python3
"""
=============================================================================
GENERADOR DEL MANUAL FÁCIL Y VISUAL PARA ADMINISTRADORES (PDF)
Liceo de Limón Mario Bourne Bourne (MEP)
Versión amigable, simple y clara (diseñada para jóvenes de 15+ y principiantes)
=============================================================================
"""

import os
import sys
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, HRFlowable
)
from reportlab.pdfgen import canvas

# Paleta de colores atractiva y moderna
VINO = colors.HexColor('#720026')
VINO_SOFT = colors.HexColor('#fdf2f4')
AZUL_IB = colors.HexColor('#003570')
AZUL_BRIGHT = colors.HexColor('#0284c7')
AZUL_BG = colors.HexColor('#f0f9ff')
GRIS_DARK = colors.HexColor('#0f172a')
GRIS_BODY = colors.HexColor('#334155')
GRIS_MUTED = colors.HexColor('#64748b')
GRIS_LIGHT = colors.HexColor('#f8fafc')
GRIS_BORDER = colors.HexColor('#e2e8f0')
AMBAR = colors.HexColor('#d97706')
AMBAR_BG = colors.HexColor('#fffbeb')
VERDE = colors.HexColor('#059669')
VERDE_BG = colors.HexColor('#ecfdf5')
BLANCO = colors.HexColor('#ffffff')


class NumberedCanvas(canvas.Canvas):
    """Canvas de dos pasos para numerar páginas dinámicamente: Página X de Y."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, total_pages):
        # La portada no lleva encabezado ni pie
        if self._pageNumber == 1:
            return

        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(GRIS_MUTED)

        # Encabezado superior
        self.drawString(54, letter[1] - 36, "🏫 LICEO DE LIMÓN MARIO BOURNE BOURNE · GUÍA PRÁCTICA DEL ADMINISTRADOR")
        self.drawRightString(letter[0] - 54, letter[1] - 36, "MEP · EDICIÓN FÁCIL")
        self.setStrokeColor(GRIS_BORDER)
        self.setLineWidth(0.75)
        self.line(54, letter[1] - 42, letter[0] - 54, letter[1] - 42)

        # Pie de página
        self.line(54, 46, letter[0] - 54, 46)
        self.drawString(54, 32, "Manual Explicado Paso a Paso para Estudiantes y Administradores")
        page_str = f"Página {self._pageNumber} de {total_pages}"
        self.drawRightString(letter[0] - 54, 32, page_str)
        self.restoreState()


def build_manual_pdf(filename="MANUAL_ADMINISTRADOR_LICEO_LIMON.pdf"):
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()

    # Estilos tipográficos claros y amigables
    title_cover = ParagraphStyle(
        'CoverTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=30,
        textColor=AZUL_IB,
        spaceAfter=8
    )

    subtitle_cover = ParagraphStyle(
        'CoverSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=19,
        textColor=VINO,
        spaceAfter=15
    )

    h1_style = ParagraphStyle(
        'Heading1Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=15,
        leading=19,
        textColor=AZUL_IB,
        spaceBefore=14,
        spaceAfter=8,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'Heading2Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11.5,
        leading=15,
        textColor=VINO,
        spaceBefore=10,
        spaceAfter=5,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'BodyCustom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=14.5,
        textColor=GRIS_BODY,
        spaceAfter=6
    )

    bullet_style = ParagraphStyle(
        'BulletCustom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=14,
        textColor=GRIS_BODY,
        leftIndent=14,
        spaceAfter=4
    )

    callout_style = ParagraphStyle(
        'CalloutText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13.5,
        textColor=GRIS_DARK
    )

    table_cell = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12,
        textColor=GRIS_BODY
    )

    table_header = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=12,
        textColor=BLANCO
    )

    def create_callout(text, title="TIP PRO", border_color=AZUL_BRIGHT, bg_color=AZUL_BG):
        content = [
            Paragraph(f"<b>{title}:</b> {text}", callout_style)
        ]
        t = Table([[content]], colWidths=[letter[0] - 108])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), bg_color),
            ('BOX', (0, 0), (-1, -1), 1, GRIS_BORDER),
            ('LINELEFT', (0, 0), (0, 0), 4, border_color),
            ('TOPPADDING', (0, 0), (-1, -1), 7),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ]))
        return t

    story = []

    # =========================================================================
    # 1. PORTADA MODERNA Y AMIGABLE
    # =========================================================================
    story.append(Spacer(1, 10))
    story.append(Paragraph("MINISTERIO DE EDUCACIÓN PÚBLICA · LICEO DE LIMÓN MARIO BOURNE BOURNE", ParagraphStyle('CoverMEP', fontName='Helvetica-Bold', fontSize=8.5, textColor=GRIS_MUTED, spaceAfter=12)))
    
    dec_bar = Table([['']], colWidths=[letter[0] - 108], rowHeights=[4])
    dec_bar.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, -1), VINO)]))
    story.append(dec_bar)
    story.append(Spacer(1, 18))

    story.append(Paragraph("GUÍA PRÁCTICA DEL ADMINISTRADOR WEB", title_cover))
    story.append(Paragraph("Aprende a controlar, editar y personalizar la página de tu colegio fácilmente", subtitle_cover))
    story.append(Paragraph("¡Bienvenido al equipo que mantiene viva la web oficial del <b>Liceo de Limón</b>! Esta guía está escrita de forma súper sencilla para que cualquier estudiante, profesor o colaborador aprenda en 10 minutos todo lo que puede hacer como administrador.", body_style))
    story.append(Spacer(1, 15))

    # Tarjeta de superpoderes
    powers_data = [
        [Paragraph("<b>¿Qué aprenderás en esta guía?</b>", table_header), Paragraph("<b>Tus superpoderes como Administrador:</b>", table_header)],
        [Paragraph("✏️ <b>Cambiar cualquier texto o foto</b>", table_cell), Paragraph("Escribir directo en la pantalla como en Word y cambiar fotos con 1 clic.", table_cell)],
        [Paragraph("🎬 <b>Subir noticias con video</b>", table_cell), Paragraph("Publicar eventos con videos de YouTube o Google Drive que se reproducen solos.", table_cell)],
        [Paragraph("🛠️ <b>Activar Modo Mantenimiento</b>", table_cell), Paragraph("Poner una página en pausa si la estás arreglando para que nadie la vea rota.", table_cell)],
        [Paragraph("👥 <b>Sumar al equipo de desarrollo</b>", table_cell), Paragraph("Agregar a tus compañeros con foto, generación y redes sociales.", table_cell)],
        [Paragraph("🛡️ <b>La Máquina del Tiempo</b>", table_cell), Paragraph("Guardar copias de seguridad por si te equivocas y quieres volver atrás.", table_cell)],
    ]
    t_powers = Table(powers_data, colWidths=[180, letter[0] - 108 - 180])
    t_powers.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), AZUL_IB),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [BLANCO, GRIS_LIGHT]),
        ('BOX', (0, 0), (-1, -1), 1, GRIS_BORDER),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, GRIS_BORDER),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(t_powers)

    story.append(Spacer(1, 20))
    story.append(create_callout(
        "<b>No necesitas saber programar</b> ni escribir código extraño. Todo se maneja con botones visuales, clics y formularios listos para usar.",
        title="¡TRANQUILO(A)!",
        border_color=VERDE,
        bg_color=VERDE_BG
    ))

    story.append(PageBreak())

    # =========================================================================
    # 2. ÍNDICE FÁCIL (TABLA DE CONTENIDOS)
    # =========================================================================
    story.append(Paragraph("MAPA DE LA GUÍA (ÍNDICE)", h1_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=AZUL_IB, spaceAfter=12))

    toc_data = [
        [Paragraph("<b>Capítulo</b>", table_header), Paragraph("<b>¿De qué trata?</b>", table_header), Paragraph("<b>Lo que vas a lograr</b>", table_header)],
        [Paragraph("<b>Capítulo 1</b>", table_cell), Paragraph("<b>Cómo Entrar al Sistema</b>", table_cell), Paragraph("Iniciar sesión en <code>/login</code> y qué hacer si olvidas la contraseña.", table_cell)],
        [Paragraph("<b>Capítulo 2</b>", table_cell), Paragraph("<b>El Editor Visual en Vivo</b>", table_cell), Paragraph("Tocar un texto para cambiarlo, cambiar fotos y cuadrar la cámara.", table_cell)],
        [Paragraph("<b>Capítulo 3</b>", table_cell), Paragraph("<b>Listas Dinámicas (+ y ✕)</b>", table_cell), Paragraph("Agregar y borrar requisitos o ventajas con numeración automática.", table_cell)],
        [Paragraph("<b>Capítulo 4</b>", table_cell), Paragraph("<b>El Panel de Control (Dashboard)</b>", table_cell), Paragraph("Tu centro de comando: ver mensajes de matrícula, teléfonos y redes.", table_cell)],
        [Paragraph("<b>Capítulo 5</b>", table_cell), Paragraph("<b>Publicar Noticias con Videos</b>", table_cell), Paragraph("Poner comunicados con fotos y videos de YouTube o Google Drive.", table_cell)],
        [Paragraph("<b>Capítulo 6</b>", table_cell), Paragraph("<b>El Botón de Mantenimiento</b>", table_cell), Paragraph("Pausar subpáginas temporalmente si estás haciendo cambios.", table_cell)],
        [Paragraph("<b>Capítulo 7</b>", table_cell), Paragraph("<b>Créditos y Desarrolladores</b>", table_cell), Paragraph("Poner tu nombre y el de tu equipo en la página de autores.", table_cell)],
        [Paragraph("<b>Capítulo 8</b>", table_cell), Paragraph("<b>Copias de Seguridad (Respaldos)</b>", table_cell), Paragraph("Descargar el archivo <code>.json</code> por si necesitas restaurar todo.", table_cell)],
        [Paragraph("<b>Capítulo 9</b>", table_cell), Paragraph("<b>Preguntas Frecuentes y Trucos</b>", table_cell), Paragraph("Respuestas rápidas a las dudas más comunes.", table_cell)],
    ]
    t_toc = Table(toc_data, colWidths=[65, 170, letter[0] - 108 - 235])
    t_toc.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), AZUL_IB),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [BLANCO, GRIS_LIGHT]),
        ('BOX', (0, 0), (-1, -1), 1, GRIS_BORDER),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, GRIS_BORDER),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(t_toc)

    story.append(Spacer(1, 15))
    story.append(create_callout(
        "Si tienes una prisa específica (por ejemplo, subir una noticia o cambiar un texto), ve directo al capítulo que necesitas.",
        title="CONSEJO RÁPIDO"
    ))

    story.append(PageBreak())

    # =========================================================================
    # CAPÍTULO 1: CÓMO ENTRAR AL SISTEMA
    # =========================================================================
    story.append(Paragraph("CAPÍTULO 1: CÓMO ENTRAR AL SISTEMA", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=VINO, spaceAfter=10))

    story.append(Paragraph("1. Iniciar sesión paso a paso:", h2_style))
    story.append(Paragraph("1. Abre la página del colegio en tu navegador (ej. <code>http://localhost:5000</code> o el dominio oficial).", bullet_style))
    story.append(Paragraph("2. Arriba a la derecha, en la barrita azul superior, toca el botón <b>🔒 Iniciar Sesión</b> (o entra directo a <code>/login</code>).", bullet_style))
    story.append(Paragraph("3. Escribe tu usuario (por defecto: <b>Admin</b>) y tu contraseña (por defecto: <b>Admin</b>).", bullet_style))
    story.append(Paragraph("4. Presiona el botón rojo <b>Ingresar al Panel de Control</b>. ¡Listo! Ya estás dentro.", bullet_style))

    story.append(Paragraph("2. ¿Qué pasa cuando entras como administrador?", h2_style))
    story.append(Paragraph("Notarás dos cosas geniales de inmediato:", body_style))
    story.append(Paragraph("• Se abre tu <b>Panel de Control</b> con todas las opciones.", bullet_style))
    story.append(Paragraph("• En la parte de abajo de la pantalla aparece una <b>barrita flotante negra</b> con botones para guardar o previsualizar tus cambios.", bullet_style))

    story.append(Paragraph("3. ¿Olvidaste tu contraseña? ¡Cero pánico!", h2_style))
    story.append(Paragraph("En la misma pantalla de login tienes el botón <b>🔑 ¿Olvidó su contraseña?</b>. Te da dos opciones sencillas:", body_style))
    story.append(Paragraph("• <b>Opción A (Código por correo):</b> Pides un código de 6 números que llega al correo del colegio. Lo escribes y pones tu nueva clave.", bullet_style))
    story.append(Paragraph("• <b>Opción B (Clave Maestra de Rescate):</b> Si no tienes acceso al correo, usas la clave fija del colegio: <code>MEP-LIMON-2026</code>. Esta clave nunca cambia y siempre te salvará.", bullet_style))

    story.append(Spacer(1, 8))
    story.append(create_callout(
        "Para cambiar tu usuario o clave por una más segura, entra a la pestaña <b>🔐 Seguridad & Credenciales</b> dentro del panel.",
        title="RECOMENDACIÓN DE SEGURIDAD"
    ))

    story.append(Spacer(1, 10))

    # =========================================================================
    # CAPÍTULO 2: EL EDITOR VISUAL EN VIVO
    # =========================================================================
    story.append(Paragraph("CAPÍTULO 2: EL EDITOR VISUAL EN VIVO", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=VINO, spaceAfter=10))

    story.append(Paragraph("1. Cambiar textos directamente sobre la pantalla", h2_style))
    story.append(Paragraph(
        "Esta es la función más divertida: cuando tienes la sesión abierta, navega por el sitio normalmente. Notarás que cuando pasas el ratón por un título o párrafo, se dibuja un recuadro punteado. <b>¡Solo haz clic y escribe lo que quieras!</b>",
        body_style
    ))
    story.append(Paragraph("Puedes corregir faltas de ortografía, actualizar horarios, cambiar lemas o nombres de profesores en segundos.", body_style))

    story.append(Paragraph("2. Cambiar fotos y logos", h2_style))
    story.append(Paragraph(
        "Al poner el ratón sobre cualquier foto del colegio (como las instalaciones o el escudo), aparece un botoncito que dice <b>📷 Cambiar Imagen</b>. Pégale el enlace de la nueva foto (puede ser de internet o de Google Drive) y cambiará al instante.",
        body_style
    ))

    story.append(Paragraph("3. Encuadrar la foto para que nadie quede cortado (Botonera 3x3)", h2_style))
    story.append(Paragraph(
        "¿Alguna vez pusiste una foto y la cabeza de una persona quedó cortada por el marco? Aquí lo resuelves en 2 segundos:",
        body_style
    ))
    story.append(Paragraph("• Te saldrá una botonera con <b>9 flechas (arriba, centro, abajo, izquierda, derecha)</b>. Toca una flecha para mover el foco hacia donde está la persona o el edificio.", bullet_style))
    story.append(Paragraph("• También tienes dos barritas deslizantes (X e Y) para mover la foto con precisión milimétrica.", bullet_style))

    story.append(Paragraph("4. Cómo guardar lo que hiciste", h2_style))
    story.append(Paragraph(
        "Abajo en la barrita flotante verás un botón verde que dice <b>💾 Guardar Cambios</b>. Púlsalo y aparecerá un mensaje verde arriba a la derecha confirmando que se guardó. Si quieres ver cómo le quedó al público antes de guardar, toca el botón del ojito <b>👁️ Vista Previa</b>.",
        body_style
    ))

    story.append(PageBreak())

    # =========================================================================
    # CAPÍTULO 3: LISTAS DINÁMICAS (+ Y ✕)
    # =========================================================================
    story.append(Paragraph("CAPÍTULO 3: LISTAS DINÁMICAS (+ Y ✕)", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=VINO, spaceAfter=10))

    story.append(Paragraph("1. ¿Qué son las listas dinámicas?", h2_style))
    story.append(Paragraph(
        "En páginas como la del <b>Bachillerato IB</b> o <b>Secundaria Regular</b> hay listas de requisitos, materias o ventajas numeradas (1, 2, 3...). No tienes que editar código para agregar o quitar cosas.",
        body_style
    ))
    story.append(Paragraph("• <b>Para agregar:</b> Al final de la lista verás un botón que dice <b>➕ Agregar Nuevo Elemento</b>. Al tocarlo se crea automáticamente un nuevo punto con el siguiente número.", bullet_style))
    story.append(Paragraph("• <b>Para borrar:</b> Al lado de cada punto hay una <b>✕ roja</b>. Tócala y el punto desaparecerá. ¡Lo mejor es que la lista se re-enumera sola automáticamente!", bullet_style))

    story.append(Spacer(1, 8))

    # =========================================================================
    # CAPÍTULO 4: EL PANEL DE CONTROL (TU CENTRO DE MANDO)
    # =========================================================================
    story.append(Paragraph("CAPÍTULO 4: EL PANEL DE CONTROL (DASHBOARD)", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=VINO, spaceAfter=10))

    story.append(Paragraph("1. Cómo entrar al Panel", h2_style))
    story.append(Paragraph(
        "En la barra superior siempre verás un botón azul que dice <b>⚙️ Panel Admin</b> (o visita <code>/admin/panel</code>).",
        body_style
    ))
    story.append(Paragraph("A la izquierda tienes un menú ordenado por pestañas. Aquí te explicamos las más importantes:", body_style))

    admin_tabs = [
        [Paragraph("<b>Pestaña</b>", table_header), Paragraph("<b>¿Para qué sirve?</b>", table_header)],
        [Paragraph("📊 <b>Bienvenida</b>", table_cell), Paragraph("El resumen de cuántas consultas hay, noticias y accesos rápidos.", table_cell)],
        [Paragraph("📬 <b>Consultas</b>", table_cell), Paragraph("Los mensajes que manda la gente interesada en matricularse en el colegio.", table_cell)],
        [Paragraph("📢 <b>Noticias</b>", table_cell), Paragraph("Donde publicas comunicados oficiales con fotos y videos.", table_cell)],
        [Paragraph("🌐 <b>Redes IB</b>", table_cell), Paragraph("Cambiar el WhatsApp, Facebook e Instagram oficiales del programa IB.", table_cell)],
        [Paragraph("🛠️ <b>Control Subpáginas</b>", table_cell), Paragraph("Poner páginas en modo mantenimiento si las estás arreglando.", table_cell)],
        [Paragraph("💻 <b>Desarrolladores</b>", table_cell), Paragraph("Gestionar la lista de estudiantes y colaboradores que hicieron la web.", table_cell)],
        [Paragraph("🛡️ <b>Puntos de Control</b>", table_cell), Paragraph("Guardar copias de respaldo (backups) en archivos JSON.", table_cell)],
    ]
    t_tabs = Table(admin_tabs, colWidths=[140, letter[0] - 108 - 140])
    t_tabs.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), AZUL_IB),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [BLANCO, GRIS_LIGHT]),
        ('BOX', (0, 0), (-1, -1), 1, GRIS_BORDER),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, GRIS_BORDER),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(t_tabs)

    story.append(Spacer(1, 10))
    story.append(Paragraph("2. Responder preguntas de padres y estudiantes", h2_style))
    story.append(Paragraph(
        "En la pestaña <b>📬 Consultas</b> verás la lista de mensajes recibidos con nombre, correo y pregunta. Puedes hacer clic en <b>✉️ Responder por Correo</b> para contestarles al instante, o marcarlas como <b>✓ Atendida</b>.",
        body_style
    ))

    story.append(PageBreak())

    # =========================================================================
    # CAPÍTULO 5: PUBLICAR NOTICIAS CON VIDEOS
    # =========================================================================
    story.append(Paragraph("CAPÍTULO 5: PUBLICAR NOTICIAS CON VIDEOS", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=VINO, spaceAfter=10))

    story.append(Paragraph("1. Cómo crear una noticia en 4 pasos:", h2_style))
    story.append(Paragraph("1. Entra a la pestaña <b>📢 Noticias & Avisos</b> en el panel de control.", bullet_style))
    story.append(Paragraph("2. Escribe el <b>Título</b> y la <b>Fecha</b> del evento.", bullet_style))
    story.append(Paragraph("3. Elige la <b>Categoría</b>: Académico, Vida Estudiantil, Deporte o Bachillerato Internacional.", bullet_style))
    story.append(Paragraph("4. Si es del IB, puedes elegir su subcategoría: <code>CAS</code>, <code>TOK</code>, <code>DELF</code> o <code>Comunidad IB</code>.", bullet_style))
    story.append(Paragraph("5. Pega el link de la foto de portada y escribe el texto. ¡Toca <b>Publicar Noticia</b> y ya está en vivo!", bullet_style))

    story.append(Paragraph("2. ¡Poner videos interactivos es facilísimo!", h2_style))
    story.append(Paragraph(
        "En el formulario verás un campo opcional llamado <b>Enlace de Video</b>. Puedes pegar:",
        body_style
    ))
    story.append(Paragraph("• <b>Cualquier video de YouTube:</b> El link normal de la barra (<code>youtube.com/watch?v=...</code>), el botón de compartir (<code>youtu.be/...</code>) o incluso un Short.", bullet_style))
    story.append(Paragraph("• <b>Google Drive:</b> Si tienes un video subido a Google Drive, comparte el enlace y pégalo. El sistema lo incrusta automáticamente.", bullet_style))

    story.append(Spacer(1, 8))
    story.append(create_callout(
        "Cuando una noticia tiene video, en la página principal le aparece una etiqueta pulsante roja que dice <b>▶ VIDEO OFICIAL</b>. Al tocar la noticia, el video se reproduce en pantalla grande sin salir de la web.",
        title="EFECTO VISUAL",
        border_color=AMBAR,
        bg_color=AMBAR_BG
    ))

    story.append(Spacer(1, 10))

    # =========================================================================
    # CAPÍTULO 6: EL BOTÓN DE MANTENIMIENTO
    # =========================================================================
    story.append(Paragraph("CAPÍTULO 6: EL BOTÓN DE MANTENIMIENTO", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=VINO, spaceAfter=10))

    story.append(Paragraph("1. ¿Para qué sirve poner una página en mantenimiento?", h2_style))
    story.append(Paragraph(
        "Imagina que estás cambiando los planes de estudio del IB o subiendo las fotos de una nueva generación y la página aún no está lista. En lugar de que el público vea cosas a medias, puedes <b>ponerle un aviso de pausa con un clic</b>.",
        body_style
    ))

    story.append(Paragraph("2. Cómo funciona en la pestaña 🛠️ Control de Subpáginas:", h2_style))
    story.append(Paragraph("• Tienes tarjetas para <b>Bachillerato IB</b>, <b>Sección Francés</b>, <b>Secundaria Regular</b> y <b>Desarrolladores</b>.", bullet_style))
    story.append(Paragraph("• Cada una tiene un botón: <b>🛑 Desactivar (Poner en Mantenimiento)</b> o <b>✅ Activar Subpágina</b>.", bullet_style))
    story.append(Paragraph("• <b>¿Qué ve un visitante normal?</b> Ve una pantalla muy bonita que dice que el apartado está en mantenimiento y un botón grande que dice <b>🏠 Volver al Inicio</b>.", bullet_style))
    story.append(Paragraph("• <b>¿Qué ves tú como administrador?</b> ¡Tú sí puedes seguir viendo la página completa para trabajar en ella! Solo te mostrará una barrita amarilla arriba recordándote que está en mantenimiento.", bullet_style))

    story.append(PageBreak())

    # =========================================================================
    # CAPÍTULO 7: CRÉDITOS Y DESARROLLADORES
    # =========================================================================
    story.append(Paragraph("CAPÍTULO 7: CRÉDITOS Y EQUIPO DE DESARROLLO", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=VINO, spaceAfter=10))

    story.append(Paragraph("1. La página de los autores (/desarrolladores)", h2_style))
    story.append(Paragraph(
        "La web del Liceo de Limón fue creada por estudiantes y colaboradores limonenses. Esta página especial celebra ese talento.",
        body_style
    ))

    story.append(Paragraph("2. Cómo agregar o editar a una persona:", h2_style))
    story.append(Paragraph("1. En el panel entra a <b>💻 Desarrolladores & Créditos</b>.", bullet_style))
    story.append(Paragraph("2. Puedes llenar el <b>Nombre</b>, su <b>Rol</b> (ej. Diseñador, Programador), y la <b>Generación</b> (ej. Generación IB 2026).", bullet_style))
    story.append(Paragraph("3. Pega el link de su foto y una pequeña descripción de lo que aportó.", bullet_style))
    story.append(Paragraph("4. Si tiene GitHub, LinkedIn o Instagram, puedes poner sus enlaces para que la gente conozca su trabajo.", bullet_style))
    story.append(Paragraph("5. Toca <b>💾 Guardar Cambios</b> y aparecerá en la página oficial.", bullet_style))

    story.append(Spacer(1, 10))

    # =========================================================================
    # CAPÍTULO 8: COPIAS DE SEGURIDAD (LA MÁQUINA DEL TIEMPO)
    # =========================================================================
    story.append(Paragraph("CAPÍTULO 8: COPIAS DE SEGURIDAD (RESPALDOS)", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=VINO, spaceAfter=10))

    story.append(Paragraph("1. ¿Por qué es genial la Máquina del Tiempo?", h2_style))
    story.append(Paragraph(
        "A todos nos da miedo tocar algo y 'arruinar la página'. <b>¡Con esta función no tienes nada que temer!</b> Antes de hacer cambios grandes, puedes congelar una copia exacta de la página en ese segundo.",
        body_style
    ))

    story.append(Paragraph("2. Los 3 botones mágicos de la pestaña 🛡️ Puntos de Control:", h2_style))
    story.append(Paragraph("• <b>💾 Guardar como Nuevo Punto Base:</b> Le pones un nombre (ej. <i>'Antes de editar fotos'</i>) y queda grabado en la memoria.", bullet_style))
    story.append(Paragraph("• <b>📥 Descargar JSON:</b> Descarga un archivito liviano a tu computadora. Ese archivo tiene todos los textos, noticias y fotos guardados.", bullet_style))
    story.append(Paragraph("• <b>📤 Importar Respaldo:</b> Si alguien borró algo sin querer, subes el archivito JSON y la página vuelve a estar exactamente como antes.", bullet_style))

    story.append(Spacer(1, 8))
    story.append(create_callout(
        "Si alguna vez quieres volver a los textos originales oficiales del MEP, hay un botón rojo al final que dice <b>Restaurar a Valores de Fábrica</b>.",
        title="RESTAURACIÓN TOTAL",
        border_color=VINO,
        bg_color=VINO_SOFT
    ))

    story.append(PageBreak())

    # =========================================================================
    # CAPÍTULO 9: PREGUNTAS FRECUENTES Y TRUCOS RÁPIDOS
    # =========================================================================
    story.append(Paragraph("CAPÍTULO 9: PREGUNTAS FRECUENTES Y TRUCOS PRO", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=VINO, spaceAfter=10))

    faqs = [
        ("¿Cómo pongo una foto de Google Drive en la página?",
         "Sube la foto a tu Google Drive, dale clic derecho > Compartir, y asegúrate de marcar 'Cualquier persona con el enlace puede ver'. Copia ese link y pégalo en la página web. ¡El sistema hace la magia y la muestra sola!"),
        ("¿Por qué el enlace en WhatsApp muestra el escudo del colegio?",
         "La web tiene configurada una tarjeta oficial (OpenGraph). Cuando compartes el link en WhatsApp o Facebook, automáticamente sale la imagen oficial con el logo del Liceo, el sello de IB World School y la descripción."),
        ("Hice un cambio en el editor visual pero no se ve desde mi teléfono, ¿por qué?",
         "Asegúrate de haber tocado el botón verde '💾 Guardar Cambios' de la barrita flotante. Si ya lo hiciste, refresca la página en tu teléfono deslizando hacia abajo para borrar la memoria caché."),
        ("¿Qué pasa si cierro sesión?",
         "Para salir de forma segura, toca el botón rojo '🚪 Cerrar Sesión' arriba a la derecha. La página volverá al modo público normal y nadie podrá hacer cambios hasta que vuelvan a poner la contraseña.")
    ]

    for q, a in faqs:
        story.append(Paragraph(f"<b>❓ {q}</b>", ParagraphStyle('FAQq', fontName='Helvetica-Bold', fontSize=10, textColor=AZUL_IB, spaceBefore=6, spaceAfter=2)))
        story.append(Paragraph(f"{a}", body_style))
        story.append(Spacer(1, 3))

    story.append(Spacer(1, 15))

    # Tabla resumen de superpoderes
    story.append(Paragraph("RESUMEN RÁPIDO DE COMANDOS Y RUTAS", h2_style))
    quick_routes = [
        [Paragraph("<b>¿A dónde quieres ir?</b>", table_header), Paragraph("<b>Ruta en el navegador</b>", table_header), Paragraph("<b>¿Qué haces ahí?</b>", table_header)],
        [Paragraph("Página Principal", table_cell), Paragraph("<code>/</code>", table_cell), Paragraph("Ver el portal oficial como un visitante regular.", table_cell)],
        [Paragraph("Iniciar Sesión", table_cell), Paragraph("<code>/login</code>", table_cell), Paragraph("Poner tu usuario y clave de administrador.", table_cell)],
        [Paragraph("Panel de Control", table_cell), Paragraph("<code>/admin/panel</code>", table_cell), Paragraph("Administrar noticias, consultas, subpáginas y backups.", table_cell)],
        [Paragraph("Bachillerato IB", table_cell), Paragraph("<code>/modalidad/ib</code>", table_cell), Paragraph("Ver noticias del IB, redes exclusivas y materias.", table_cell)],
        [Paragraph("Equipo de Desarrollo", table_cell), Paragraph("<code>/desarrolladores</code>", table_cell), Paragraph("Ver las fichas con fotos de los autores de la web.", table_cell)],
    ]
    t_quick = Table(quick_routes, colWidths=[130, 110, letter[0] - 108 - 240])
    t_quick.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), AZUL_IB),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [BLANCO, GRIS_LIGHT]),
        ('BOX', (0, 0), (-1, -1), 1, GRIS_BORDER),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, GRIS_BORDER),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(t_quick)

    story.append(Spacer(1, 20))
    story.append(create_callout(
        "¡Felicidades! Ahora conoces todas las herramientas para mantener la web del <b>Liceo de Limón Mario Bourne Bourne</b> moderna, activa y siempre al día. Si tienes dudas, revisa este manual cuando quieras.",
        title="¡LISTO PARA COMENZAR!",
        border_color=AZUL_IB,
        bg_color=AZUL_BG
    ))

    # Construir el documento con el canvas de dos pasos
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Manual simplificado generado exitosamente: {filename}")


if __name__ == '__main__':
    build_manual_pdf()
