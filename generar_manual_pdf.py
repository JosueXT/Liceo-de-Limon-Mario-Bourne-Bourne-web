#!/usr/bin/env python3
"""
=============================================================================
GENERADOR DEL MANUAL DE USUARIO Y GUÍA DE ADMINISTRACIÓN WEB (PDF)
Liceo de Limón Mario Bourne Bourne (MEP)
=============================================================================
"""

import os
import sys
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas

# Colores Institucionales
VINO = colors.HexColor('#720026')
VINO_LIGHT = colors.HexColor('#9e1b42')
AZUL_IB = colors.HexColor('#003570')
AZUL_LIGHT = colors.HexColor('#0284c7')
AZUL_BG = colors.HexColor('#f0f9ff')
GRIS_DARK = colors.HexColor('#0f172a')
GRIS_BODY = colors.HexColor('#334155')
GRIS_MUTED = colors.HexColor('#64748b')
GRIS_LIGHT = colors.HexColor('#f8fafc')
GRIS_BORDER = colors.HexColor('#e2e8f0')
AMBAR = colors.HexColor('#d97706')
VERDE = colors.HexColor('#059669')
BLANCO = colors.HexColor('#ffffff')


class NumberedCanvas(canvas.Canvas):
    """Canvas de dos pasos para calcular el total de páginas y pintar cabeceras y pies dinámicos."""
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
        # La portada (página 1) no lleva encabezado ni pie estándar
        if self._pageNumber == 1:
            return

        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(GRIS_MUTED)

        # Encabezado superior
        self.drawString(54, letter[1] - 36, "LICEO DE LIMÓN MARIO BOURNE BOURNE · MANUAL OFICIAL DE ADMINISTRACIÓN")
        self.drawRightString(letter[0] - 54, letter[1] - 36, "MEP · CIRCUITO 01")
        self.setStrokeColor(GRIS_BORDER)
        self.setLineWidth(0.75)
        self.line(54, letter[1] - 42, letter[0] - 54, letter[1] - 42)

        # Pie de página
        self.line(54, 46, letter[0] - 54, 46)
        self.drawString(54, 32, "Plataforma Web Institucional · Documento Confidencial de Operación")
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

    # Estilos tipográficos personalizados
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
        fontSize=16,
        leading=20,
        textColor=AZUL_IB,
        spaceBefore=16,
        spaceAfter=10,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'Heading2Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=15,
        textColor=VINO,
        spaceBefore=12,
        spaceAfter=6,
        keepWithNext=True
    )

    h3_style = ParagraphStyle(
        'Heading3Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=13,
        textColor=GRIS_DARK,
        spaceBefore=8,
        spaceAfter=4,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'BodyCustom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=14,
        textColor=GRIS_BODY,
        spaceAfter=6
    )

    bullet_style = ParagraphStyle(
        'BulletCustom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13.5,
        textColor=GRIS_BODY,
        leftIndent=14,
        spaceAfter=4
    )

    callout_style = ParagraphStyle(
        'CalloutText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=13,
        textColor=GRIS_DARK
    )

    table_cell = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=11.5,
        textColor=GRIS_BODY
    )

    table_header = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11.5,
        textColor=BLANCO
    )

    def create_callout(text, title="NOTA IMPORTANTE", border_color=AZUL_IB, bg_color=AZUL_BG):
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
    # 1. PORTADA INSTITUCIONAL
    # =========================================================================
    story.append(Spacer(1, 15))
    story.append(Paragraph("MINISTERIO DE EDUCACIÓN PÚBLICA · DIRECCIÓN REGIONAL DE LIMÓN · CIRCUITO 01", ParagraphStyle('CoverMEP', fontName='Helvetica-Bold', fontSize=8.5, textColor=GRIS_MUTED, spaceAfter=15)))
    
    # Barra decorativa tricolor MEP/Liceo
    dec_bar = Table([['']], colWidths=[letter[0] - 108], rowHeights=[4])
    dec_bar.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, -1), VINO)]))
    story.append(dec_bar)
    story.append(Spacer(1, 20))

    story.append(Paragraph("MANUAL OFICIAL DE ADMINISTRACIÓN Y GUÍA DEL SISTEMA WEB", title_cover))
    story.append(Paragraph("Plataforma Institucional y Sistema de Gestión de Contenidos (CMS)", subtitle_cover))
    story.append(Paragraph("<b>Institución:</b> Liceo de Limón Mario Bourne Bourne<br/><b>Acreditación:</b> Colegio del Mundo del IB (Bachillerato Internacional - IB World School)<br/><b>Edición del Sistema:</b> Versión Oficial 2026", body_style))
    story.append(Spacer(1, 15))

    # Caja de metadatos de la portada
    cover_info_data = [
        [Paragraph("<b>Documento:</b>", table_cell), Paragraph("Manual de Operación, Edición y Mantenimiento Web", table_cell)],
        [Paragraph("<b>Destinatarios:</b>", table_cell), Paragraph("Directores, Asistentes de Dirección, Coordinación IB, Administradores Web", table_cell)],
        [Paragraph("<b>Seguridad:</b>", table_cell), Paragraph("Uso Oficial Interno · Protección de Credenciales MEP", table_cell)],
        [Paragraph("<b>Dominio Oficial:</b>", table_cell), Paragraph("<code>liceomariobourne.dpdns.org</code> (con alias <code>www</code>)", table_cell)],
        [Paragraph("<b>Última Actualización:</b>", table_cell), Paragraph("Octubre 2026 · Con soporte de video, modo mantenimiento y desarrolladores", table_cell)],
    ]
    cover_table = Table(cover_info_data, colWidths=[130, letter[0] - 108 - 130])
    cover_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), GRIS_LIGHT),
        ('BOX', (0, 0), (-1, -1), 1, GRIS_BORDER),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, GRIS_BORDER),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(cover_table)

    story.append(Spacer(1, 25))
    story.append(create_callout(
        "Este manual describe detalladamente todas las funciones del portal institucional: desde el acceso seguro con contraseñas y códigos temporales OTP, la edición visual directa de textos e imágenes, la publicación de noticias con videos de YouTube y Google Drive, el control de activación/desactivación de subpáginas en mantenimiento, hasta el respaldo completo con copias de seguridad descargables en JSON.",
        title="RESUMEN EJECUTIVO",
        border_color=VINO,
        bg_color=colors.HexColor('#fdf2f4')
    ))

    story.append(PageBreak())

    # =========================================================================
    # 2. ÍNDICE GENERAL (TABLA DE CONTENIDOS)
    # =========================================================================
    story.append(Paragraph("ÍNDICE GENERAL", h1_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=AZUL_IB, spaceAfter=12))

    toc_data = [
        [Paragraph("<b>Módulo</b>", table_header), Paragraph("<b>Título de la Sección</b>", table_header), Paragraph("<b>Contenidos y Funciones Tratadas</b>", table_header)],
        [Paragraph("<b>Módulo 1</b>", table_cell), Paragraph("<b>Introducción y Roles</b>", table_cell), Paragraph("Arquitectura general, doble modalidad de edición y privilegios.", table_cell)],
        [Paragraph("<b>Módulo 2</b>", table_cell), Paragraph("<b>Acceso y Seguridad</b>", table_cell), Paragraph("Inicio de sesión, cambio de claves, códigos OTP y clave de rescate.", table_cell)],
        [Paragraph("<b>Módulo 3</b>", table_cell), Paragraph("<b>Editor Visual In-Situ</b>", table_cell), Paragraph("Edición directa sobre la pantalla, fotos, encuadre 3x3 y listas +/-.", table_cell)],
        [Paragraph("<b>Módulo 4</b>", table_cell), Paragraph("<b>Panel de Control (Dashboard)</b>", table_cell), Paragraph("Navegación por pestañas, consultas de matrícula, identidad y contacto.", table_cell)],
        [Paragraph("<b>Módulo 5</b>", table_cell), Paragraph("<b>Noticias y Multimedia</b>", table_cell), Paragraph("Publicación de comunicados, subcategorías IB, videos YouTube/Drive/MP4.", table_cell)],
        [Paragraph("<b>Módulo 6</b>", table_cell), Paragraph("<b>Mantenimiento de Subpáginas</b>", table_cell), Paragraph("Activar/Desactivar IB, Francés, Regular o Desarrolladores; mensaje 503.", table_cell)],
        [Paragraph("<b>Módulo 7</b>", table_cell), Paragraph("<b>Equipo de Desarrolladores</b>", table_cell), Paragraph("Gestión de miembros, generación, roles y redes sociales de créditos.", table_cell)],
        [Paragraph("<b>Módulo 8</b>", table_cell), Paragraph("<b>Puntos de Control & Respaldo</b>", table_cell), Paragraph("Wayback Machine, exportar e importar JSON, restauración de fábrica.", table_cell)],
        [Paragraph("<b>Módulo 9</b>", table_cell), Paragraph("<b>Dominio, DNS y Redes</b>", table_cell), Paragraph("FreeDomain (dpdns.org), registro www y vista previa OpenGraph/WhatsApp.", table_cell)],
        [Paragraph("<b>Módulo 10</b>", table_cell), Paragraph("<b>Preguntas Frecuentes & Rescate</b>", table_cell), Paragraph("Solución de problemas comunes y script de rescate por consola.", table_cell)],
    ]
    toc_table = Table(toc_data, colWidths=[65, 155, letter[0] - 108 - 220])
    toc_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), AZUL_IB),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [BLANCO, GRIS_LIGHT]),
        ('BOX', (0, 0), (-1, -1), 1, GRIS_BORDER),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, GRIS_BORDER),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(toc_table)

    story.append(Spacer(1, 15))
    story.append(create_callout(
        "Para una navegación rápida en este documento PDF, cada módulo está estructurado con explicaciones claras, pasos ordenados con viñetas y tablas de parámetros.",
        title="SUGERENCIA DE LECTURA"
    ))

    story.append(PageBreak())

    # =========================================================================
    # MÓDULO 1: INTRODUCCIÓN Y ARQUITECTURA GENERAL
    # =========================================================================
    story.append(Paragraph("MÓDULO 1: INTRODUCCIÓN Y ARQUITECTURA GENERAL", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=VINO, spaceAfter=10))

    story.append(Paragraph("1.1 Propósito del Sistema Web", h2_style))
    story.append(Paragraph(
        "La plataforma web institucional del <b>Liceo de Limón Mario Bourne Bourne</b> es un sistema moderno desarrollado con Python Flask y SQLite, diseñado para comunicar la identidad del colegio benemérito, su acreditación como Colegio del Mundo del IB (Bachillerato Internacional), y sus modalidades de estudio (Secundaria Regular, Francés Avanzado e IB).",
        body_style
    ))
    story.append(Paragraph(
        "A diferencia de sitios web estáticos tradicionales, esta plataforma incorpora un <b>Sistema de Gestión de Contenidos (CMS)</b> propio y seguro que permite a los funcionarios del colegio modificar textos, fotos, requisitos, teléfonos, noticias y canales de contacto sin requerir conocimientos técnicos ni programación.",
        body_style
    ))

    story.append(Paragraph("1.2 Doble Modalidad de Administración", h2_style))
    story.append(Paragraph("El administrador dispone de dos entornos complementarios para gestionar la plataforma:", body_style))
    story.append(Paragraph("• <b>Editor Visual In-Situ:</b> Permite navegar por la página pública e interactuar directamente con los textos e imágenes con solo hacer clic sobre ellos (<i>WYSIWYG: What You See Is What You Get</i>). Ideal para cambios rápidos de ortografía, fotos o requisitos.", bullet_style))
    story.append(Paragraph("• <b>Panel de Control Administrativo (/admin/panel):</b> Un escritorio de trabajo estructurado por pestañas para gestionar comunicados de noticias, responder consultas de matrícula, descargar respaldos JSON, cambiar credenciales y activar/desactivar subpáginas en mantenimiento.", bullet_style))

    story.append(Spacer(1, 8))
    story.append(create_callout(
        "Cualquier cambio guardado tanto desde el Editor Visual como desde el Panel de Control se almacena de forma instantánea y permanente en la base de datos local SQLite del servidor.",
        title="PERSISTENCIA DE DATOS"
    ))

    story.append(Spacer(1, 10))

    # =========================================================================
    # MÓDULO 2: ACCESO Y SEGURIDAD
    # =========================================================================
    story.append(Paragraph("MÓDULO 2: ACCESO Y SEGURIDAD DEL SISTEMA", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=VINO, spaceAfter=10))

    story.append(Paragraph("2.1 Cómo Iniciar Sesión", h2_style))
    story.append(Paragraph("Para acceder como administrador al sistema:", body_style))
    story.append(Paragraph("1. En la barra superior institucional de cualquier página, haga clic en el botón <b>🔒 Iniciar Sesión</b> (o escriba en su navegador la ruta <code>/login</code>).", bullet_style))
    story.append(Paragraph("2. Ingrese el nombre de usuario y su contraseña asignada.", bullet_style))
    story.append(Paragraph("3. Presione el botón <b>Ingresar al Panel de Control</b>.", bullet_style))
    story.append(Paragraph("4. Al autenticarse con éxito, se le redirigirá al Panel Administrativo y en todas las páginas se habilitará la barra flotante inferior del Editor Visual.", bullet_style))

    story.append(Paragraph("2.2 Cambio Seguro de Credenciales", h2_style))
    story.append(Paragraph(
        "Dentro del panel de control, en la pestaña <b>🔐 Seguridad & Credenciales</b>, el administrador puede modificar en cualquier momento su nombre de usuario o su contraseña. Para prevenir accesos indebidos, el sistema exige digitar la <u>Contraseña Actual</u> como confirmación antes de autorizar el cambio.",
        body_style
    ))

    story.append(Paragraph("2.3 Mecanismos de Rescate ante Olvido de Contraseña", h2_style))
    story.append(Paragraph("Si en algún momento extravía su contraseña, la pantalla de inicio de sesión dispone del enlace interactivo <b>🔑 ¿Olvidó su contraseña?</b>, el cual ofrece dos vías de recuperación:", body_style))
    story.append(Paragraph("• <b>Vía 1: Código de 6 Dígitos por Correo (OTP):</b> Escriba su usuario y el sistema enviará un código numérico temporal con validez de 15 minutos al correo electrónico institucional registrado. Ingrese el código recibido y asigne su nueva clave.", bullet_style))
    story.append(Paragraph("• <b>Vía 2: Clave Maestra Institucional Inmutable:</b> Si no tiene acceso al correo, puede emplear la clave maestra institucional de rescate (<code>MEP-LIMON-2026</code>) para ingresar inmediatamente y restablecer sus claves.", bullet_style))

    story.append(Spacer(1, 8))
    story.append(create_callout(
        "Si administra directamente el servidor por terminal o consola, puede ejecutar el script de emergencia: <code>python restablecer_password.py --factory</code> para reiniciar inmediatamente el usuario a 'Admin' y la contraseña a 'Admin'.",
        title="RESCATE POR LÍNEA DE COMANDOS",
        border_color=VERDE,
        bg_color=colors.HexColor('#ecfdf5')
    ))

    story.append(PageBreak())

    # =========================================================================
    # MÓDULO 3: EL EDITOR VISUAL EN VIVO (CMS IN-SITU)
    # =========================================================================
    story.append(Paragraph("MÓDULO 3: EL EDITOR VISUAL EN VIVO (CMS IN-SITU)", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=VINO, spaceAfter=10))

    story.append(Paragraph("3.1 Edición Directa de Textos y Títulos (WYSIWYG)", h2_style))
    story.append(Paragraph(
        "Al estar autenticado como administrador, cualquier texto editable del portal (títulos, subtítulos, lemas, descripciones, misión, visión y avisos) muestra un contorno sutil punteado. Haga clic sobre el texto deseado y comience a escribir como si estuviera en un procesador de textos.",
        body_style
    ))

    story.append(Paragraph("3.2 Cambio y Reemplazo de Imágenes", h2_style))
    story.append(Paragraph(
        "Las fotografías de campus, banners, fotos de modalidades y logotipos institucionales muestran un botón flotante <b>📷 Cambiar Imagen</b> al colocar el cursor sobre ellas. Al hacer clic se despliega un diálogo donde puede pegar la URL de la nueva imagen (incluyendo vínculos directos de Google Drive). El sistema adapta el enlace automáticamente.",
        body_style
    ))

    story.append(Paragraph("3.3 Herramienta de Encuadre y Posición de Fotos (Botonera 3x3)", h2_style))
    story.append(Paragraph(
        "Para garantizar que los rostros de las personas, edificios o banderas no queden cortados en pantallas de computadoras o celulares, el editor incluye un selector de encuadre direccional:",
        body_style
    ))
    story.append(Paragraph("• <b>Matriz 3x3:</b> Permite alinear la foto al instante hacia cualquiera de los 9 cuadrantes: Arriba-Izquierda, Arriba-Centro, Arriba-Derecha, Centro, Abajo, etc.", bullet_style))
    story.append(Paragraph("• <b>Deslizadores Milimétricos (Sliders X e Y):</b> Ajuste fino de 0% a 100% para calibrar la posición exacta del foco visual.", bullet_style))

    story.append(Paragraph("3.4 Gestión Dinámica de Listas (+ y ✕)", h2_style))
    story.append(Paragraph(
        "En las secciones estructuradas (pilares curriculares, requisitos de matrícula, ventajas del IB, instalaciones destacadas):",
        body_style
    ))
    story.append(Paragraph("• Presione el botón verde <b>➕ Agregar Nuevo Elemento</b> para insertar una nueva fila numerada.", bullet_style))
    story.append(Paragraph("• Presione el botón rojo <b>✕</b> sobre cualquier elemento existente para eliminarlo. La numeración de la lista se actualiza automáticamente de forma correlativa.", bullet_style))

    story.append(Paragraph("3.5 Barra Flotante: Vista Previa y Guardado Asíncrono", h2_style))
    story.append(Paragraph(
        "En la parte inferior de la pantalla aparece una barra flotante de control:",
        body_style
    ))
    story.append(Paragraph("• <b>Contador de Cambios:</b> Indica cuántos textos o imágenes ha modificado en la sesión.", bullet_style))
    story.append(Paragraph("• <b>Botón 👁️ Vista Previa:</b> Oculta temporalmente los controles administrativos para apreciar cómo verá la página el visitante regular.", bullet_style))
    story.append(Paragraph("• <b>Botón 💾 Guardar Cambios:</b> Envía los datos modificados al servidor mediante peticiones asíncronas y muestra una notificación Toast de confirmación en verde.", bullet_style))

    story.append(PageBreak())

    # =========================================================================
    # MÓDULO 4: PANEL DE CONTROL ADMINISTRATIVO (DASHBOARD)
    # =========================================================================
    story.append(Paragraph("MÓDULO 4: PANEL DE CONTROL ADMINISTRATIVO (DASHBOARD)", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=VINO, spaceAfter=10))

    story.append(Paragraph("4.1 Estructura del Panel de Control (/admin/panel)", h2_style))
    story.append(Paragraph(
        "El Panel de Control centraliza la administración institucional a través de una barra lateral modular con las siguientes áreas operativas:",
        body_style
    ))

    panel_modules = [
        [Paragraph("<b>Pestaña</b>", table_header), Paragraph("<b>Función Institucional</b>", table_header)],
        [Paragraph("📊 <b>Bienvenida & Resumen</b>", table_cell), Paragraph("Indicadores clave (KPIs), accesos rápidos y estado del sistema.", table_cell)],
        [Paragraph("📬 <b>Bandeja de Consultas</b>", table_cell), Paragraph("Mensajes y preguntas de matrícula enviadas por estudiantes o padres.", table_cell)],
        [Paragraph("🎨 <b>Editor Visual</b>", table_cell), Paragraph("Lanzador directo a las páginas en modo de edición in-situ.", table_cell)],
        [Paragraph("📢 <b>Noticias & Avisos</b>", table_cell), Paragraph("Publicación, edición y filtrado de comunicados con fotos y videos.", table_cell)],
        [Paragraph("🌐 <b>Redes y Canales IB</b>", table_cell), Paragraph("Enlaces a WhatsApp, Facebook, Instagram y correos de coordinación.", table_cell)],
        [Paragraph("🏛️ <b>Identidad & Escudo</b>", table_cell), Paragraph("Nombres institucionales, bandera MEP editable y escudo del liceo.", table_cell)],
        [Paragraph("💻 <b>Desarrolladores & Créditos</b>", table_cell), Paragraph("Gestión de autores, estudiantes, colaboradores y redes sociales.", table_cell)],
        [Paragraph("🛠️ <b>Control de Subpáginas</b>", table_cell), Paragraph("Activar o pausar subpáginas en modo mantenimiento con mensaje 503.", table_cell)],
        [Paragraph("🛡️ <b>Puntos de Control</b>", table_cell), Paragraph("Wayback Machine, copias de seguridad descargables en JSON y restore.", table_cell)],
        [Paragraph("🔐 <b>Seguridad & Credenciales</b>", table_cell), Paragraph("Actualización del usuario administrativo y contraseña maestra.", table_cell)],
    ]
    t_panel = Table(panel_modules, colWidths=[150, letter[0] - 108 - 150])
    t_panel.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), AZUL_IB),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [BLANCO, GRIS_LIGHT]),
        ('BOX', (0, 0), (-1, -1), 1, GRIS_BORDER),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, GRIS_BORDER),
        ('TOPPADDING', (0, 0), (-1, -1), 4.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4.5),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(t_panel)

    story.append(Spacer(1, 12))
    story.append(Paragraph("4.2 Gestión de la Bandeja de Consultas", h2_style))
    story.append(Paragraph(
        "Cuando un visitante envía un formulario desde la sección de Contacto o Matrícula, la consulta queda registrada automáticamente en la pestaña <b>📬 Consultas</b>. El administrador puede:",
        body_style
    ))
    story.append(Paragraph("• Visualizar el nombre, correo electrónico, teléfono, asunto y mensaje completo.", bullet_style))
    story.append(Paragraph("• Marcar el mensaje como <b>⏳ Pendiente</b> o <b>✓ Atendida</b>.", bullet_style))
    story.append(Paragraph("• Hacer clic en <b>✉️ Responder por Correo</b> para abrir directamente su cliente de correo predeterminado dirigido al remitente.", bullet_style))
    story.append(Paragraph("• Eliminar consultas obsoletas con confirmación de seguridad.", bullet_style))

    story.append(PageBreak())

    # =========================================================================
    # MÓDULO 5: GESTIÓN DE NOTICIAS Y COMUNICADOS MULTIMEDIA
    # =========================================================================
    story.append(Paragraph("MÓDULO 5: GESTIÓN DE NOTICIAS Y COMUNICADOS MULTIMEDIA", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=VINO, spaceAfter=10))

    story.append(Paragraph("5.1 Publicación de un Nuevo Comunicado", h2_style))
    story.append(Paragraph(
        "En la pestaña <b>📢 Noticias & Avisos</b> del panel de control:",
        body_style
    ))
    story.append(Paragraph("1. Ingrese el <b>Título de la Noticia</b> y la <b>Fecha Oficial</b>.", bullet_style))
    story.append(Paragraph("2. Seleccione la <b>Categoría Principal</b> (Académico, Vida Estudiantil, Deporte, Efemérides o Bachillerato Internacional).", bullet_style))
    story.append(Paragraph("3. Si la noticia pertenece al IB, seleccione su <b>Subcategoría Especializada</b>: <code>CAS (Creatividad, Actividad y Servicio)</code>, <code>TOK (Teoría del Conocimiento)</code>, <code>Monografía</code>, <code>DELF Francés</code> o <code>Comunidad IB</code>.", bullet_style))
    story.append(Paragraph("4. Indique la URL de la fotografía de portada (muestra previsualización instantánea).", bullet_style))
    story.append(Paragraph("5. Redacte el cuerpo del comunicado y presione <b>Publicar Noticia</b>.", bullet_style))

    story.append(Paragraph("5.2 Soporte de Videos Multimedia (YouTube, Google Drive y MP4)", h2_style))
    story.append(Paragraph(
        "Las noticias admiten la inserción directa de videos interactivos. En el campo opcional <b>Enlace de Video</b>, puede ingresar cualquiera de los siguientes formatos:",
        body_style
    ))
    story.append(Paragraph("• <b>YouTube:</b> Enlaces estándar (<code>youtube.com/watch?v=...</code>), compartidos (<code>youtu.be/...</code>) o de Shorts (<code>youtube.com/shorts/...</code>). El sistema los transforma automáticamente en reproductores embebidos responsivos en formato 16:9.", bullet_style))
    story.append(Paragraph("• <b>Google Drive:</b> Enlaces compartidos de archivos de video almacenados en Drive. El sistema convierte la URL a modo de previsualización (<code>preview</code>) para reproducirlo de inmediato.", bullet_style))
    story.append(Paragraph("• <b>Archivos MP4 / WebM:</b> Enlaces directos a archivos de video en la web.", bullet_style))

    story.append(Spacer(1, 8))
    story.append(create_callout(
        "Al incluir un video en una noticia, la tarjeta en la página principal y en la sección de noticias exhibe una insignia distintiva pulsante <b>▶ VIDEO OFICIAL</b>. Al hacer clic en la noticia, el video se reproduce en alta definición sin salir del sitio web.",
        title="INDICADOR VISUAL DE VIDEO",
        border_color=AMBAR,
        bg_color=colors.HexColor('#fffbeb')
    ))

    story.append(Spacer(1, 10))
    story.append(Paragraph("5.3 Sección Exclusiva de Noticias IB con Filtros", h2_style))
    story.append(Paragraph(
        "En la subpágina del Bachillerato Internacional (<code>/modalidad/ib</code>) existe una sección dedicada que filtra automáticamente todas las noticias marcadas con la categoría IB. Los visitantes pueden filtrar con un solo clic entre las subcategorías oficiales: CAS, TOK, DELF, etc.",
        body_style
    ))

    story.append(PageBreak())

    # =========================================================================
    # MÓDULO 6: CONTROL DE ACTIVACIÓN Y MANTENIMIENTO DE SUBPÁGINAS
    # =========================================================================
    story.append(Paragraph("MÓDULO 6: CONTROL DE ACTIVACIÓN Y MODO MANTENIMIENTO", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=VINO, spaceAfter=10))

    story.append(Paragraph("6.1 Propósito del Modo Mantenimiento", h2_style))
    story.append(Paragraph(
        "Cuando el personal directivo o docente se encuentra actualizando planes de estudio, mallas curriculares, calendarios de admisión o proyectos de graduación, es deseable suspender temporalmente el acceso público a una sección específica sin alterar el resto del sitio web.",
        body_style
    ))

    story.append(Paragraph("6.2 Panel de Control: Pestaña 🛠️ Control de Subpáginas", h2_style))
    story.append(Paragraph(
        "En esta pestaña el administrador puede gestionar la disponibilidad de cuatro subpáginas clave:",
        body_style
    ))
    story.append(Paragraph("1. 🎓 <b>Bachillerato Internacional (IB)</b> (<code>/modalidad/ib</code>)", bullet_style))
    story.append(Paragraph("2. 🇫🇷 <b>Sección Bilingüe Francés</b> (<code>/modalidad/frances</code>)", bullet_style))
    story.append(Paragraph("3. 🏛️ <b>Modalidad Académica Regular</b> (<code>/modalidad/regular</code>)", bullet_style))
    story.append(Paragraph("4. 💻 <b>Desarrolladores & Créditos Web</b> (<code>/desarrolladores</code>)", bullet_style))

    story.append(Spacer(1, 8))
    story.append(Paragraph("6.3 Comportamiento según el Rol de Usuario", h2_style))

    maint_roles = [
        [Paragraph("<b>Tipo de Usuario</b>", table_header), Paragraph("<b>Experiencia al ingresar a una subpágina desactivada</b>", table_header)],
        [
            Paragraph("<b>Visitante Público</b><br/>(Estudiantes, Padres, Comunidad)", table_cell),
            Paragraph("El servidor devuelve la pantalla institucional de mantenimiento (HTTP 503) con el mensaje oficial: <i>'Este apartado se encuentra temporalmente fuera de servicio debido a que se está realizando mantenimiento. Por favor, vuelva nuevamente más tarde'</i> y el botón destacado <b>🏠 Volver al Inicio</b>.", table_cell)
        ],
        [
            Paragraph("<b>Administrador Autenticado</b><br/>(Personal con Sesión Iniciada)", table_cell),
            Paragraph("Conserva <b>acceso completo</b> a la subpágina para revisar y editar sus contenidos. En la parte superior de la pantalla se despliega una barra amarilla de advertencia: <i>'⚠️ AVISO DE ADMINISTRACIÓN: Esta subpágina está actualmente DESACTIVADA para visitantes públicos'</i>.", table_cell)
        ],
    ]
    t_maint = Table(maint_roles, colWidths=[160, letter[0] - 108 - 160])
    t_maint.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), AZUL_IB),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [BLANCO, GRIS_LIGHT]),
        ('BOX', (0, 0), (-1, -1), 1, GRIS_BORDER),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, GRIS_BORDER),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(t_maint)

    story.append(Spacer(1, 10))
    story.append(Paragraph("6.4 Interruptor Maestro Global", h2_style))
    story.append(Paragraph(
        "En la parte superior de la pestaña se encuentra el botón <b>🚨 Mantenimiento General del Sitio</b>. Al activarlo, todas las subpáginas secundarias pasan inmediatamente a estado fuera de servicio con un solo clic, ideal ante actualizaciones integrales del servidor o períodos vacacionales.",
        body_style
    ))

    story.append(PageBreak())

    # =========================================================================
    # MÓDULO 7: GESTIÓN DEL EQUIPO DE DESARROLLADORES Y CRÉDITOS
    # =========================================================================
    story.append(Paragraph("MÓDULO 7: GESTIÓN DEL EQUIPO DE DESARROLLADORES", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=VINO, spaceAfter=10))

    story.append(Paragraph("7.1 Reconocimiento al Talento Estudiantil", h2_style))
    story.append(Paragraph(
        "La plataforma cuenta con la subpágina dedicada <code>/desarrolladores</code> (accesible también como <code>/creditos</code> y <code>/equipo</code>) donde se rinde homenaje y testimonio a los estudiantes del Bachillerato Internacional y colaboradores que crearon el sitio web mediante la metodología <i>Vibe Coding</i>.",
        body_style
    ))

    story.append(Paragraph("7.2 Administración de Miembros desde el Panel", h2_style))
    story.append(Paragraph(
        "En la pestaña <b>💻 Desarrolladores & Créditos</b>, el administrador puede editar o añadir personas con los siguientes campos:",
        body_style
    ))
    story.append(Paragraph("• <b>Nombre Completo:</b> Nombre del desarrollador o colaborador.", bullet_style))
    story.append(Paragraph("• <b>Rol o Especialidad:</b> Puesto desempeñado (ej. Lead Full-Stack, Diseñador UI/UX, Editor de Contenidos).", bullet_style))
    story.append(Paragraph("• <b>Generación / Año:</b> Generación académica (ej. Generación IB 2026).", bullet_style))
    story.append(Paragraph("• <b>Fotografía:</b> Enlace de foto (con soporte para enlaces de Google Drive).", bullet_style))
    story.append(Paragraph("• <b>Biografía Breve:</b> Resumen de aportes y contribución técnica.", bullet_style))
    story.append(Paragraph("• <b>Redes Sociales Profesionales:</b> Enlaces directos a GitHub, LinkedIn, Instagram y Correo.", bullet_style))

    story.append(Spacer(1, 8))
    story.append(Paragraph("7.3 Operaciones Rápidas", h2_style))
    story.append(Paragraph("• <b>Agregar Integrante:</b> Presione <i>➕ Agregar Otro Desarrollador</i> para abrir una nueva tarjeta en blanco.", bullet_style))
    story.append(Paragraph("• <b>Eliminar Integrante:</b> Presione el botón rojo <i>🗑️ Eliminar</i> sobre la tarjeta deseada.", bullet_style))
    story.append(Paragraph("• <b>Guardar Cambios:</b> Haga clic en <i>💾 Guardar Cambios</i> para impactar de inmediato la página pública.", bullet_style))

    story.append(Spacer(1, 12))

    # =========================================================================
    # MÓDULO 8: PUNTOS DE CONTROL Y RESPALDO (WAYBACK MACHINE)
    # =========================================================================
    story.append(Paragraph("MÓDULO 8: PUNTOS DE CONTROL Y RESPALDO (WAYBACK MACHINE)", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=VINO, spaceAfter=10))

    story.append(Paragraph("8.1 Guardar un Nuevo Punto Base", h2_style))
    story.append(Paragraph(
        "Antes de realizar modificaciones mayores (ej. inicio de matrícula o cambio de fotos institucionales), se recomienda crear un punto de control. En la pestaña <b>🛡️ Puntos de Control</b>, escriba una etiqueta descriptiva (ej. <i>'Versión Previa Matrícula 2026'</i>) y presione <b>💾 Guardar como Nuevo Punto Base</b>. El sistema congelará una fotografía idéntica de la base de datos.",
        body_style
    ))

    story.append(Paragraph("8.2 Exportar y Descargar Respaldo JSON", h2_style))
    story.append(Paragraph(
        "En la tabla de historial, presione el botón <b>📥 Descargar JSON</b> junto a cualquier punto guardado. Se descargará a su computadora un archivo liviano con toda la información, listo para ser custodiado externamente o compartido con la dirección.",
        body_style
    ))

    story.append(Paragraph("8.3 Importar y Restaurar desde Archivo", h2_style))
    story.append(Paragraph(
        "Si desea regresar a una versión archivada en su computadora, utilice el botón <b>📤 Importar Respaldo</b>, seleccione el archivo <code>.json</code> y el sistema reconfigurará el portal con los datos históricos de ese archivo.",
        body_style
    ))

    story.append(PageBreak())

    # =========================================================================
    # MÓDULO 9: DOMINIO, DNS Y PREVISUALIZACIÓN SOCIAL
    # =========================================================================
    story.append(Paragraph("MÓDULO 9: DOMINIO, DNS Y PREVISUALIZACIÓN SOCIAL", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=VINO, spaceAfter=10))

    story.append(Paragraph("9.1 Configuración de Dominio con FreeDomain (dpdns.org)", h2_style))
    story.append(Paragraph(
        "El sitio web está preparado para operar bajo el nombre de dominio oficial registrado en FreeDomain: <b>liceomariobourne.dpdns.org</b> (con soporte simultáneo para el prefijo <b>www.liceomariobourne.dpdns.org</b>).",
        body_style
    ))
    story.append(Paragraph("Para apuntar el dominio hacia el servidor de alojamiento (ej. Render, VPS o servidor institucional):", body_style))
    story.append(Paragraph("• <b>Registro Principal (@):</b> Registro tipo <code>CNAME</code> apuntando al host de la aplicación (ej. <code>tu-app.onrender.com</code>) o tipo <code>A</code> con la dirección IP fija.", bullet_style))
    story.append(Paragraph("• <b>Registro WWW:</b> Registro tipo <code>CNAME</code> con alias <code>www</code> apuntando a <code>liceomariobourne.dpdns.org</code>.", bullet_style))

    story.append(Paragraph("9.2 Imagen de Previsualización en Redes Sociales (OpenGraph / WhatsApp)", h2_style))
    story.append(Paragraph(
        "Al compartir el enlace del colegio a través de <b>WhatsApp, Facebook, Twitter (X) o Telegram</b>, el sistema genera automáticamente una tarjeta enriquecida con:",
        body_style
    ))
    story.append(Paragraph("• <b>Título Oficial:</b> <i>Liceo de Limón Mario Bourne Bourne | Portal Institucional</i>", bullet_style))
    story.append(Paragraph("• <b>Descripción:</b> <i>Sitio web oficial del Liceo de Limón Mario Bourne Bourne (MEP). Colegio del Mundo del IB.</i>", bullet_style))
    story.append(Paragraph("• <b>Imagen Oficial (og_preview.jpg):</b> Fotografía de alta resolución con fondo blanco puro institucional, el escudo oficial del liceo, el emblema de Colegio del Mundo del IB y los colores oficiales (Negro, Rojo, Blanco y Azul IB).", bullet_style))

    story.append(Spacer(1, 12))

    # =========================================================================
    # MÓDULO 10: PREGUNTAS FRECUENTES Y SOLUCIÓN DE PROBLEMAS
    # =========================================================================
    story.append(Paragraph("MÓDULO 10: PREGUNTAS FRECUENTES Y RESOLUCIÓN DE PROBLEMAS", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=VINO, spaceAfter=10))

    faqs = [
        ("¿Qué hacer si una imagen de Google Drive no se visualiza?",
         "Asegúrese de que el archivo en Google Drive tenga permisos configurados como 'Cualquier persona con el enlace puede ver'. El editor visual de la página web convertirá automáticamente la URL para que se muestre en pantalla."),
        ("¿Cómo sé si los cambios en el editor visual ya están públicos?",
         "Al presionar 'Guardar Cambios' en la barra inferior flotante, aparece un mensaje verde en la esquina superior derecha indicando '✓ Cambios guardados correctamente'. En ese instante, todos los visitantes verán la versión actualizada."),
        ("¿Por qué un visitante ve la pantalla de mantenimiento en una subpágina?",
         "Revise en el panel de control la pestaña '🛠️ Control de Subpáginas'. Es probable que la subpágina individual o el 'Mantenimiento General' estén activados. Presione '✅ Activar Subpágina' para reanudar el acceso inmediato."),
        ("¿Cómo respaldar la base de datos completa de forma manual?",
         "El archivo físico de la base de datos se llama 'liceo_cms.db' y reside en la raíz del proyecto. También puede descargar el respaldo en formato JSON desde la pestaña '🛡️ Puntos de Control' del panel administrativo.")
    ]

    for q, a in faqs:
        story.append(Paragraph(f"<b>❓ {q}</b>", h3_style))
        story.append(Paragraph(f"<b>R:</b> {a}", body_style))
        story.append(Spacer(1, 4))

    story.append(Spacer(1, 12))
    story.append(create_callout(
        "Para asistencia técnica adicional o soporte sobre la infraestructura del servidor, contacte al administrador de tecnologías educativas o a la Coordinación del Bachillerato Internacional del Liceo de Limón Mario Bourne Bourne.",
        title="SOPORTE INSTITUCIONAL",
        border_color=AZUL_IB,
        bg_color=AZUL_BG
    ))

    # Construir el documento con el canvas de dos pasos
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Manual generado exitosamente: {filename}")


if __name__ == '__main__':
    build_manual_pdf()
