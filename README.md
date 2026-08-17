# 🏫 Liceo de Limón Mario Bourne Bourne (MEP)
### Sitio Web Institucional & Sistema de Administración (CMS)

Sitio web oficial del **Liceo de Limón Mario Bourne Bourne**, colegio público del **Ministerio de Educación Pública (MEP)** de Costa Rica. Incluye información de las 3 modalidades (*Secundaria Regular, Francés Avanzado y Bachillerato Internacional IB*), redes sociales, sistema de noticias y panel de administración.

---

## 💻 GUÍA PARA ABRIR LA PÁGINA EN CUALQUIER COMPUTADORA
> **¿No sabes programar, no tienes VS Code ni conocimientos técnicos? ¡No te preocupes! Sigue estos sencillos pasos:**

---

### 🟢 Paso 1: Descargar e Instalar Python (Solo se hace una vez)
*Python es el único programa gratuito que tu computadora necesita para hacer funcionar la página.*

1. Entra en tu navegador a la página oficial de Python:  
   👉 **[https://www.python.org/downloads/](https://www.python.org/downloads/)**
2. Haz clic en el botón amarillo **"Download Python"**.
3. Abre el archivo descargado para comenzar la instalación.
4. ⚠️ **MUY IMPORTANTE (¡No te saltes esto!)**:
   En la primera ventana del instalador, en la parte de abajo, **marca la casilla que dice:**  
   ☑️ **"Add python.exe to PATH"** *(o "Agregar Python al PATH")*.
6. Luego haz clic en **"Install Now"** y espera a que termine. ¡Listo!

> ℹ️ *Nota: No necesitas instalar JavaScript ni nada adicional; los navegadores como Google Chrome, Edge o Safari ya lo traen incluido.*

---

### 🟢 Paso 2: Descargar el Proyecto en tu Computadora

1. En esta página de GitHub, haz clic en el botón verde que dice **`Code`** (arriba a la derecha).
2. Haz clic en **`Download ZIP`**.
3. Ve a tu carpeta de *Descargas*, busca el archivo ZIP descargado, hazle clic derecho y selecciona **"Extraer todo..."** para descomprimir la carpeta.

---

### 🟢 Paso 3: Abrir la Página (¡Con un solo clic!)

#### 🪟 Si usas Windows:
1. Abre la carpeta que descomprimiste.
2. Busca el archivo llamado **`iniciar_sitio.bat`** y dale **doble clic**.
3. Se abrirá una ventana negra que preparará todo automáticamente y **abrirá la página en tu navegador**.

#### 🍏 Si usas Mac o Linux:
1. Abre la terminal en la carpeta del proyecto y escribe:
   ```bash
   bash iniciar_sitio.sh
   ```

---

### 🟢 Paso 4: ¡Ver la Página en tu Navegador!

Si tu navegador no se abrió automáticamente, abre **Google Chrome**, **Edge** o tu navegador favorito y escribe en la barra de direcciones:

👉 **`http://localhost:5000`**

¡Y ya podrás ver y navegar por toda la página del Liceo de Limón! 🎉

---

## 🔐 ¿Cómo Iniciar Sesión como Administrador?

1. En la parte superior de la página (en la barra del MEP con la bandera de Costa Rica), haz clic en el botón:  
   👉 **`🔒 Iniciar Sesión`** (o entra directo a `http://localhost:5000/login`).
2. Ingresa las credenciales oficiales:
   - **Usuario**: `Admin`
   - **Contraseña**: `Admin`
3. Se abrirá el **Panel de Administración (`/admin/panel`)** donde podrás:
   - 📬 **Ver y responder consultas** de matrícula enviadas por padres o estudiantes.
   - 📢 **Publicar y borrar noticias** (con fotos y subcategorías como CAS, TOK, DELF, etc.).
   - 📱 **Cambiar enlaces de Redes Sociales** (Facebook, Instagram y WhatsApp).
   - 🎨 **Cambiar el escudo/logo** del colegio y textos principales.
   - 🔄 **Restaurar todo a los valores de fábrica** si alguna vez cometes un error.

---

## 🛑 ¿Cómo Apagar la Página cuando termines?

Para cerrar el servidor, simplemente **cierra la ventana negra (consola)** que se abrió en el Paso 3. Cuando quieras volver a usar la página, solo repites el Paso 3 dándole doble clic a `iniciar_sitio.bat`.

---

## 📁 ¿Qué contiene cada archivo? (Para los curiosos)

- **`iniciar_sitio.bat`**: El iniciador rápido para Windows.
- **`app.py`**: El cerebro del servidor (Flask).
- **`database.py`**: El sistema que guarda las noticias y mensajes (Base de datos SQLite).
- **`templates/`**: Las páginas web en HTML (Inicio, Modalidades, Login y Panel de Control).
- **`static/`**: Los estilos visuales (colores, fuentes) y las animaciones interactivas.
- **`requirements.txt`**: La lista de herramientas que Python instala automáticamente.
