# 🏫 Liceo de Limón Mario Bourne Bourne
### Plataforma Web Institucional & Sistema de Gestión de Contenidos (CMS)
**Ministerio de Educación Pública (MEP) • Dirección Regional de Educación de Limón • Circuito 01**

---

## 📌 Descripción General del Proyecto

Esta plataforma web es el portal oficial y sistema de administración del **Liceo de Limón Mario Bourne Bourne**, una institución pública de educación secundaria perteneciente al **Ministerio de Educación Pública (MEP)** de Costa Rica.

El sistema ha sido diseñado con dos propósitos fundamentales:
1. **Portal Público Informativo:** Brinda a la comunidad estudiantil, padres de familia y docentes una experiencia moderna, accesible y detallada sobre las tres ofertas académicas institucionales (**Secundaria Regular**, **Francés Avanzado** y **Bachillerato Internacional IB**), junto con un canal oficial de noticias y medios de contacto directo.
2. **Sistema de Administración y Edición en Vivo (CMS In-Situ):** Permite a las autoridades del colegio gestionar el contenido de todo el sitio de forma visual e intuitiva (escribiendo directamente sobre las páginas o desde el panel de control), administrar comunicados oficiales por subcategorías, atender consultas de matrícula y respaldar el estado del sitio mediante puntos de restauración.

---

## 🚀 Guía de Instalación y Puesta en Marcha

No se requieren conocimientos de programación ni entornos avanzados para ejecutar este proyecto. Siga los pasos a continuación para correr la plataforma en cualquier computadora.

### Requisito Previo Único: Python (Gratuito)
*Si ya tiene Python instalado en su equipo, puede avanzar directamente al Paso 2.*

1. Ingrese al sitio oficial de descarga de Python: **[https://www.python.org/downloads/](https://www.python.org/downloads/)**
2. Haga clic en el botón amarillo **"Download Python"** y abra el archivo descargado.
3. ⚠️ **Punto Crítico:** En la primera pantalla del instalador, marque la casilla inferior que indica:  
   ☑️ **"Add python.exe to PATH"** *(o "Agregar Python a las variables de entorno")*.
4. Presione **"Install Now"** y espere a que finalice la instalación.

---

### Paso 1: Descargar los Archivos del Proyecto
1. En la parte superior de este repositorio en GitHub, presione el botón verde **`Code`** y seleccione **`Download ZIP`**.
2. Descomprima la carpeta descargada en la ubicación de su preferencia.

---

### Paso 2: Iniciar el Servidor Local

#### 🪟 En sistemas Windows:
- Abra la carpeta del proyecto y haga **doble clic en el archivo `iniciar_sitio.bat`**.
- El script verificará las dependencias de forma automática, iniciará el servidor local y abrirá su navegador web predeterminado.

#### 🍏 En sistemas macOS o Linux:
- Abra la terminal dentro del directorio del proyecto y ejecute:
  ```bash
  bash iniciar_sitio.sh
  ```

#### 🧑‍💻 Método Manual por Terminal (Para Desarrolladores):
```bash
# 1. Instalar dependencias requeridas (Flask)
pip install -r requirements.txt

# 2. Ejecutar la aplicación
python app.py
```

---

### Paso 3: Acceder a la Plataforma
Una vez iniciado el servidor, abra su navegador web (Google Chrome, Mozilla Firefox, Microsoft Edge o Safari) e ingrese a:

👉 **`http://localhost:5000`**

Para detener el servidor en cualquier momento, simplemente cierre la ventana de la consola o presione `Ctrl + C` en la terminal.

---

## 🧭 Estructura y Navegación del Sitio

La plataforma está estructurada en secciones modulares claramente diferenciadas:

### 1. Portal Principal (`/`)
- **Encabezado y Barra MEP:** Identificación institucional, bandera nacional y acceso al inicio de sesión.
- **Hero Banner:** Lema educativo, título de bienvenida y aviso dinámico en marquesina (*ticker*).
- **Cifras Institucionales:** Cuatro métricas de impacto con animación numérica en tiempo real.
- **Ofertas Educativas:** Tarjetas de acceso directo con los colores oficiales de cada modalidad:
  - 🔵 **Bachillerato Internacional (IB):** Azul, Índigo, Blanco y Celeste.
  - 🟠 **Francés Avanzado:** Azul, Rojo, Amarillo y Naranja.
  - 🔴 **Secundaria Regular:** Vino, Azul y Gris.
- **Noticias y Avisos:** Sistema de comunicados filtrable por categoría general e individualizable por subcategorías (CAS, TOK, DELF, Actividades, etc.) con ventana de lectura detallada.
- **Comunidad Digital:** Enlaces oficiales a la página de Facebook, perfil de Instagram y Canal de Avisos de WhatsApp.
- **Historia e Ideario MEP:** Legado del educador Mario Bourne Bourne, valores cívicos, misión y visión del colegio.
- **Formulario de Contacto:** Recepción directa de dudas y solicitudes de matrícula por área de interés.
- **Pie de Página:** Directorio de enlaces, redes, información de secretaría y derechos reservados.

### 2. Subpáginas de Modalidades Académicas
Cada modalidad dispone de una página especializada con su propia identidad visual:
- **`/modalidad/ib`**: Información detallada del Programa del Diploma (PD), componentes centrales (Teoría del Conocimiento, Monografía, Creatividad, Actividad y Servicio), requisitos de admisión y **Malla Curricular completa celda por celda**.
- **`/modalidad/frances`**: Objetivos del programa bilingüe francófono, certificaciones internacionales DELF (A1 a B2), actividades culturales y plan de asignaturas.
- **`/modalidad/regular`**: Tercer ciclo y educación diversificada del plan nacional del MEP, talleres complementarios, laboratorios y cuadro de materias.

---

## 🔐 Manual de Administración del Sistema

### Acceso al Panel de Control
1. Haga clic en el botón **`🔒 Iniciar Sesión`** ubicado en el extremo derecho de la barra superior, o ingrese directamente a **`http://localhost:5000/login`**.
2. Introduzca las credenciales institucionales:
   - **Usuario:** `Admin`
   - **Contraseña:** `Admin`
3. Al autenticarse, será dirigido al **Panel Administrativo (`/admin/panel`)**.

---

### Módulos del Panel de Administración

#### 1. 🏠 Resumen & Bienvenida
Cuadro de mando con saludo institucional, estado de la base de datos en tiempo real, métricas clave (consultas recibidas, comunicados activos, versiones guardadas) y accesos directos a todas las herramientas.

#### 2. 🎨 Editor Visual en Vivo (In-Situ)
Permite editar cualquier texto o imagen directamente sobre el diseño real de las páginas:
- **Cómo utilizarlo:** Inicie sesión y navegue a cualquier página pública (`/`, `/modalidad/ib`, `/modalidad/frances`, `/modalidad/regular`).
- **Edición de Textos:** Todos los elementos editables mostrarán un borde punteado azul. Haga clic sobre cualquier título, párrafo o celda de tabla y escriba el nuevo texto.
- **Edición de Fotografías:** Haga clic sobre cualquier imagen o logotipo institucional para abrir el selector e ingresar una nueva URL con vista previa inmediata.
- **Barra Flotante Inferior:** 
  - Muestra un contador en vivo con la cantidad de modificaciones realizadas.
  - El botón **`👁️ Vista Previa`** permite ocultar los bordes de edición para revisar el aspecto final antes de guardar.
  - El botón **`💾 Guardar Cambios`** envía todas las modificaciones a la base de datos local SQLite.

#### 3. 📬 Bandeja de Consultas de Matrícula
- Muestra los mensajes enviados por padres de familia y estudiantes desde el formulario de contacto.
- Permite alternar el estado de cada solicitud entre **`⏳ Pendiente`** y **`✓ Atendida`**.
- Incluye un botón de **`✉️ Responder por Correo`** que abre su cliente de correo con el destinatario, asunto y plantilla listos para redactar.

#### 4. 📢 Gestión y Edición de Noticias
- **Publicar Comunicados:** Formulario completo para ingresar título, categoría, subcategoría (CAS, TOK, DELF, etc.), fecha, autor, fotografía con previsualización en vivo, resumen y contenido extenso.
- **Editar Comunicados Existentes:** Cada noticia en la tabla cuenta con un botón **`✏️ Editar`** que carga su información para realizar correcciones o cambiar fotografías.
- **Eliminar Comunicados:** Opción de borrado con confirmación de seguridad.

#### 5. 📱 Redes Sociales e Identidad
- Modificación de URLs, nombres de usuario y descripciones para Facebook, Instagram y el Canal de WhatsApp.
- Configuración del escudo oficial del MEP con previsualización en vivo.

#### 6. 🛡️ Puntos de Control y Respaldos (Wayback Machine)
- **Guardar Estado Actual:** Permite crear una copia de seguridad instantánea con nombre personalizado (ej. *"Versión Estable - Matrícula 2026"*).
- **Restaurar Versiones Anteriores:** Si comete un error en los textos o la estructura, puede consultar el historial cronológico y presionar **`⏪ Restaurar esta Versión`** para volver el sitio a ese estado exacto.
- **Restauración de Fábrica:** Botón de emergencia para reiniciar todos los contenidos a los valores iniciales oficiales del MEP.

---

## 📁 Estructura del Código Fuente

```text
liceo_limon/
├── app.py                  # Servidor web backend (Rutas Flask, API REST y autenticación)
├── database.py             # Capa de datos SQLite (Tablas, consultas, snapshots y transacciones)
├── seed_data.py            # Contenidos oficiales iniciales, textos base del MEP y modalidades
├── liceo_cms.db            # Base de datos local SQLite (Se crea automáticamente al iniciar)
├── requirements.txt        # Dependencias de Python requeridas (Flask)
├── iniciar_sitio.bat       # Iniciador rápido de un clic para entornos Windows
├── iniciar_sitio.sh        # Iniciador para sistemas macOS y Linux
├── LICENSE                 # Licencia de software libre (MIT)
├── README.md               # Manual de usuario y documentación técnica
├── static/                 # Recursos estáticos
│   ├── css/
│   │   ├── main.css        # Hoja de estilos principal (Diseño responsivo, temas de color y modales)
│   │   ├── admin.css       # Estilos del editor visual in-situ y barra flotante administrativa
│   │   └── animations.css  # Efectos visuales, parallax, scroll reveal y transiciones
│   └── js/
│       ├── main.js         # Lógica frontend pública (Filtros de noticias, contadores, modal y formulario)
│       └── admin_cms.js    # Motor de edición visual in-situ, control de cambios y guardado asíncrono
└── templates/              # Vistas HTML con motor Jinja2
    ├── index.html          # Página principal del Liceo de Limón
    ├── modalidad.html      # Plantilla modular para subpáginas (IB, Francés y Regular)
    ├── login.html          # Subpágina de acceso administrativo seguro
    └── admin_panel.html    # Panel de control institucional (Dashboard, CMS, Noticias y Respaldo)
```

---

## 🔒 Privacidad y Seguridad

- **Sesiones Criptográficas:** El acceso a los endpoints de guardado (`/api/cms/*`) está protegido mediante verificación estricta de sesión en el servidor (`session['is_admin']`).
- **Separación de Vistas:** Los usuarios comunes y visitantes del colegio nunca visualizan botones de edición, barras flotantes ni interfaces administrativas.
- **Almacenamiento Local:** Todos los datos se gestionan de forma autónoma en el archivo local SQLite `liceo_cms.db` sin depender de servicios de terceros en la nube.

---

## 📄 Licencia

Este proyecto está distribuido bajo los términos de la **Licencia MIT**. Puede consultar el archivo [`LICENSE`](LICENSE) para obtener más información sobre su uso, modificación y distribución.
