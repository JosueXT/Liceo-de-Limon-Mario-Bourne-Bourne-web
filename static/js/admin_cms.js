/**
 * ============================================================================
 * SISTEMA CMS WYSIWYG & GESTIÓN ADMINISTRATIVA
 * Liceo de Limón Mario Bourne Bourne (MEP)
 * ============================================================================
 * GUÍA RÁPIDA DE FUNCIONAMIENTO:
 * 1. Autenticación:
 *    - Inicia sesión con Usuario: Admin / Contraseña: Admin.
 * 2. Modo Edición Visual:
 *    - Al iniciar sesión, todos los elementos con atributo [data-cms-key]
 *      se vuelven editables directamente en la pantalla (puedes escribir).
 *    - Las imágenes con [data-cms-img] o dentro de .cms-image-wrapper
 *      abren un modal al hacerles clic para cambiar su URL o escoger un logo/foto.
 * 3. Guardado Asíncrono (AJAX/Fetch):
 *    - Al hacer clic en "Guardar Cambios", se envían las modificaciones a Flask
 *      y se guardan en la base de datos SQLite sin necesidad de recargar la página.
 * ============================================================================
 */

// Estado global de la sesión administrativa y contenidos modificados
const CMS_STATE = {
  isAdmin: false,
  isEditMode: true,
  modifiedItems: {}, // Guarda los pares { clave: nuevoTextoOImagen }
  currentEditingImageKey: null
};

document.addEventListener('DOMContentLoaded', () => {
  initAdminAuth();
  checkInitialAdminState();
  initInlineEditor();
  initImageEditorModal();
  initNewsManager();
});

/**
 * 1. Comprobación y Control de Sesión Administrativa
 */
function checkInitialAdminState() {
  const adminFlag = document.body.getAttribute('data-is-admin');
  const openAdminFlag = document.body.getAttribute('data-open-admin');

  if (adminFlag === 'true') {
    enableAdminMode();
  } else if (openAdminFlag === 'true') {
    openLoginModal();
  }
}

function initAdminAuth() {
  const loginModal = document.getElementById('adminLoginModal');
  const closeBtn = document.getElementById('closeLoginModalBtn');
  const loginForm = document.getElementById('adminLoginForm');
  const loginTrigger = document.getElementById('adminPortalBtn');

  if (loginTrigger) {
    loginTrigger.addEventListener('click', (e) => {
      e.preventDefault();
      if (CMS_STATE.isAdmin) {
        showToast('Ya has iniciado sesión como Administrador.', 'info');
      } else {
        openLoginModal();
      }
    });
  }

  if (closeBtn && loginModal) {
    closeBtn.addEventListener('click', () => {
      loginModal.classList.remove('active');
    });
  }

  if (loginForm) {
    loginForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const usernameInput = document.getElementById('adminUsername');
      const passwordInput = document.getElementById('adminPassword');
      const errorBox = document.getElementById('loginErrorBox');
      const submitBtn = loginForm.querySelector('button[type="submit"]');

      const username = usernameInput.value.trim();
      const password = passwordInput.value.trim();

      errorBox.style.display = 'none';
      submitBtn.disabled = true;
      submitBtn.innerText = 'Validando credenciales...';

      try {
        const res = await fetch('/api/auth/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ username, password })
        });

        const data = await res.json();

        if (res.ok && data.success) {
          loginModal.classList.remove('active');
          enableAdminMode();
          showToast('✓ Sesión iniciada: Modo Edición Visual Activado.', 'success');
        } else {
          errorBox.innerText = data.message || 'Credenciales incorrectas.';
          errorBox.style.display = 'block';
        }
      } catch (err) {
        errorBox.innerText = 'Error de conexión con el servidor.';
        errorBox.style.display = 'block';
      } finally {
        submitBtn.disabled = false;
        submitBtn.innerText = 'Ingresar al Modo Edición';
      }
    });
  }
}

function openLoginModal() {
  const modal = document.getElementById('adminLoginModal');
  if (modal) {
    modal.classList.add('active');
    document.getElementById('adminUsername')?.focus();
  }
}

/**
 * 2. Activación y Desactivación del Modo Edición
 */
function enableAdminMode() {
  CMS_STATE.isAdmin = true;
  CMS_STATE.isEditMode = true;
  document.body.classList.add('cms-edit-mode');

  // Mostrar u ocultar barra flotante
  let toolbar = document.getElementById('adminFloatingToolbar');
  if (toolbar) {
    toolbar.style.display = 'flex';
  } else {
    createFloatingToolbar();
  }

  // Activar edición de texto in-situ
  applyContentEditable(true);
}

function disableAdminMode() {
  CMS_STATE.isEditMode = false;
  document.body.classList.remove('cms-edit-mode');
  applyContentEditable(false);
}

function applyContentEditable(enabled) {
  const editableElements = document.querySelectorAll('[data-cms-key]');
  editableElements.forEach(el => {
    el.contentEditable = enabled ? 'true' : 'false';
    el.spellcheck = false;
  });
}

/**
 * 3. Creación de la Barra de Herramientas Flotante del Administrador
 */
function createFloatingToolbar() {
  const bar = document.createElement('div');
  bar.id = 'adminFloatingToolbar';
  bar.className = 'admin-toolbar-floating';
  bar.innerHTML = `
    <div class="admin-status-indicator">
      <span class="admin-pulse-dot"></span>
      <span class="admin-mode-text" id="adminModeStatusText">Modo Edición Activo</span>
    </div>
    <div class="admin-actions-group">
      <button class="btn-admin btn-admin-save" id="btnAdminSaveAll" title="Guardar todos los cambios en la base de datos">
        💾 Guardar Cambios (<span id="modifiedCount">0</span>)
      </button>
      <button class="btn-admin btn-admin-add" id="btnAdminAddNews" title="Publicar nuevo comunicado institucional">
        ➕ Nueva Noticia
      </button>
      <button class="btn-admin btn-admin-toggle" id="btnAdminTogglePreview" title="Alternar entre modo edición y vista previa">
        👁️ Vista Previa
      </button>
      <button class="btn-admin btn-admin-reset" id="btnAdminReset" title="Restaurar textos e imágenes originales">
        🔄 Restaurar
      </button>
      <button class="btn-admin btn-admin-logout" id="btnAdminLogout" title="Salir del panel">
        🚪 Salir
      </button>
    </div>
  `;
  document.body.appendChild(bar);

  // Enlazar eventos de los botones
  document.getElementById('btnAdminSaveAll')?.addEventListener('click', saveAllCmsChanges);
  document.getElementById('btnAdminAddNews')?.addEventListener('click', openAddNewsModal);
  document.getElementById('btnAdminTogglePreview')?.addEventListener('click', togglePreviewMode);
  document.getElementById('btnAdminReset')?.addEventListener('click', confirmResetDefaults);
  document.getElementById('btnAdminLogout')?.addEventListener('click', handleLogout);
}

/**
 * 4. Edición de Textos Inline (Detección de Cambios en Tiempo Real)
 */
function initInlineEditor() {
  document.addEventListener('input', (e) => {
    const target = e.target;
    if (target.hasAttribute && target.hasAttribute('data-cms-key')) {
      const key = target.getAttribute('data-cms-key');
      const newValue = target.innerText.trim();

      CMS_STATE.modifiedItems[key] = newValue;
      target.classList.add('cms-modified');
      updateModifiedCounter();
    }
  });
}

function updateModifiedCounter() {
  const countSpan = document.getElementById('modifiedCount');
  const count = Object.keys(CMS_STATE.modifiedItems).length;
  if (countSpan) {
    countSpan.innerText = count;
  }
}

/**
 * 5. Guardado Asíncrono en la Base de Datos (AJAX/Fetch)
 */
async function saveAllCmsChanges() {
  const keys = Object.keys(CMS_STATE.modifiedItems);
  if (keys.length === 0) {
    showToast('No hay cambios pendientes por guardar.', 'info');
    return;
  }

  const saveBtn = document.getElementById('btnAdminSaveAll');
  if (saveBtn) {
    saveBtn.disabled = true;
    saveBtn.innerHTML = '⏳ Guardando...';
  }

  try {
    const res = await fetch('/api/cms/content', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ items: CMS_STATE.modifiedItems })
    });

    const data = await res.json();

    if (res.ok && data.success) {
      showToast('✓ ¡Todos los cambios han sido guardados en la base de datos!', 'success');
      CMS_STATE.modifiedItems = {};
      updateModifiedCounter();

      // Quitar clase de modificado
      document.querySelectorAll('.cms-modified').forEach(el => el.classList.remove('cms-modified'));
    } else {
      showToast('Error al guardar: ' + (data.message || 'Desconocido'), 'error');
    }
  } catch (err) {
    showToast('Error de conexión al guardar cambios.', 'error');
  } finally {
    if (saveBtn) {
      saveBtn.disabled = false;
      saveBtn.innerHTML = `💾 Guardar Cambios (<span id="modifiedCount">0</span>)`;
    }
  }
}

/**
 * 6. Edición de Imágenes y Logotipos
 */
function initImageEditorModal() {
  const modal = document.getElementById('editImageModal');
  const closeBtn = document.getElementById('closeEditImageModalBtn');
  const form = document.getElementById('editImageForm');

  // Clic en cualquier contenedor de imagen editable
  document.addEventListener('click', (e) => {
    if (!CMS_STATE.isAdmin || !CMS_STATE.isEditMode) return;

    const wrapper = e.target.closest('.cms-image-wrapper');
    if (wrapper) {
      e.preventDefault();
      const img = wrapper.querySelector('img[data-cms-img]');
      const bgElem = wrapper.hasAttribute('data-cms-img') ? wrapper : null;

      let key = null;
      let currentSrc = '';

      if (img) {
        key = img.getAttribute('data-cms-img');
        currentSrc = img.getAttribute('src');
      } else if (bgElem) {
        key = bgElem.getAttribute('data-cms-img');
        const styleBg = bgElem.style.backgroundImage;
        currentSrc = styleBg.replace(/url\(['"]?(.*?)['"]?\)/i, '$1');
      }

      if (key) {
        openImageEditModal(key, currentSrc);
      }
    }
  });

  if (closeBtn && modal) {
    closeBtn.addEventListener('click', () => modal.classList.remove('active'));
  }

  if (form) {
    form.addEventListener('submit', (e) => {
      e.preventDefault();
      const urlInput = document.getElementById('imageUrlInput');
      const newUrl = urlInput.value.trim();

      if (newUrl && CMS_STATE.currentEditingImageKey) {
        const key = CMS_STATE.currentEditingImageKey;

        // Actualizar en etiquetas <img>
        const targetImgs = document.querySelectorAll(`img[data-cms-img="${key}"]`);
        targetImgs.forEach(targetImg => {
          targetImg.src = newUrl;
          targetImg.classList.add('cms-modified');
        });

        // Actualizar si es fondo de Hero
        const targetBgs = document.querySelectorAll(`[data-cms-img="${key}"]:not(img)`);
        targetBgs.forEach(targetBg => {
          targetBg.style.backgroundImage = `url('${newUrl}')`;
          targetBg.classList.add('cms-modified');
        });

        CMS_STATE.modifiedItems[key] = newUrl;
        updateModifiedCounter();
        modal.classList.remove('active');
        showToast('Imagen actualizada en pantalla. Recuerde hacer clic en "Guardar Cambios".', 'info');
      }
    });
  }

  // Presets sugeridos
  document.querySelectorAll('.img-preset-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const url = btn.getAttribute('data-url');
      const urlInput = document.getElementById('imageUrlInput');
      if (urlInput && url) {
        urlInput.value = url;
        const preview = document.getElementById('imageModalPreview');
        if (preview) preview.src = url;
      }
    });
  });
}

function openImageEditModal(key, currentSrc) {
  CMS_STATE.currentEditingImageKey = key;
  const modal = document.getElementById('editImageModal');
  const urlInput = document.getElementById('imageUrlInput');
  const preview = document.getElementById('imageModalPreview');

  if (urlInput) urlInput.value = currentSrc;
  if (preview) preview.src = currentSrc;
  if (modal) modal.classList.add('active');
}

/**
 * 7. Gestor de Noticias (Crear y Eliminar)
 */
function initNewsManager() {
  const modal = document.getElementById('addNewsModal');
  const closeBtn = document.getElementById('closeAddNewsModalBtn');
  const form = document.getElementById('addNewsForm');

  if (closeBtn && modal) {
    closeBtn.addEventListener('click', () => modal.classList.remove('active'));
  }

  if (form) {
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const title = document.getElementById('newsFormTitle').value.trim();
      const category = document.getElementById('newsFormCategory').value;
      const categorySlug = document.getElementById('newsFormSlug').value;
      const date = document.getElementById('newsFormDate').value.trim() || new Date().toLocaleDateString('es-CR', { day: 'numeric', month: 'long', year: 'numeric' });
      const summary = document.getElementById('newsFormSummary').value.trim();
      const content = document.getElementById('newsFormContent').value.trim();
      const image = document.getElementById('newsFormImage').value.trim() || 'https://images.unsplash.com/photo-1523240795612-9a054b0db644?auto=format&fit=crop&w=800&q=80';
      const author = document.getElementById('newsFormAuthor').value.trim() || 'Liceo de Limón MEP';

      const submitBtn = form.querySelector('button[type="submit"]');
      submitBtn.disabled = true;
      submitBtn.innerText = 'Publicando...';

      try {
        const res = await fetch('/api/cms/news', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ title, category, category_slug: categorySlug, date, summary, content, image, author })
        });

        const data = await res.json();

        if (res.ok && data.success) {
          modal.classList.remove('active');
          form.reset();
          showToast('✓ Comunicado institucional publicado exitosamente.', 'success');
          setTimeout(() => window.location.reload(), 800);
        } else {
          showToast('Error al publicar: ' + data.message, 'error');
        }
      } catch (err) {
        showToast('Error de conexión al publicar noticia.', 'error');
      } finally {
        submitBtn.disabled = false;
        submitBtn.innerText = 'Publicar Comunicado';
      }
    });
  }

  // Delegar eliminación de noticias
  document.addEventListener('click', async (e) => {
    if (e.target.matches('.btn-card-delete') || e.target.closest('.btn-card-delete')) {
      const btn = e.target.matches('.btn-card-delete') ? e.target : e.target.closest('.btn-card-delete');
      const newsId = btn.getAttribute('data-news-id');

      if (confirm(`¿Está seguro de eliminar este comunicado institucional (#${newsId})?`)) {
        try {
          const res = await fetch(`/api/cms/news/${newsId}`, { method: 'DELETE' });
          const data = await res.json();
          if (res.ok && data.success) {
            showToast('✓ Noticia eliminada correctamente.', 'success');
            const card = btn.closest('.news-card');
            if (card) {
              card.style.opacity = '0';
              card.style.transform = 'scale(0.9)';
              setTimeout(() => card.remove(), 400);
            }
          }
        } catch (err) {
          showToast('Error al eliminar noticia.', 'error');
        }
      }
    }
  });
}

function openAddNewsModal() {
  const modal = document.getElementById('addNewsModal');
  if (modal) modal.classList.add('active');
}

/**
 * 8. Alternar Modo Vista Previa
 */
function togglePreviewMode() {
  const btn = document.getElementById('btnAdminTogglePreview');
  const statusText = document.getElementById('adminModeStatusText');

  if (CMS_STATE.isEditMode) {
    disableAdminMode();
    btn.innerHTML = '✏️ Volver a Editar';
    statusText.innerText = 'Modo Vista Previa';
    showToast('Modo Vista Previa: navegando como usuario público.', 'info');
  } else {
    enableAdminMode();
    btn.innerHTML = '👁️ Vista Previa';
    statusText.innerText = 'Modo Edición Activo';
    showToast('Modo Edición Reactivado.', 'info');
  }
}

/**
 * 9. Restaurar Valores Institucionales Base
 */
async function confirmResetDefaults() {
  if (confirm('¿Desea restaurar todos los textos, imágenes y noticias a los valores oficiales iniciales del MEP? Se perderán las modificaciones no respaldadas.')) {
    try {
      const res = await fetch('/api/cms/reset', { method: 'POST' });
      const data = await res.json();
      if (res.ok && data.success) {
        showToast('✓ Base de datos restaurada a los valores iniciales.', 'success');
        setTimeout(() => window.location.reload(), 1000);
      }
    } catch (err) {
      showToast('Error al restaurar valores.', 'error');
    }
  }
}

/**
 * 10. Cerrar Sesión
 */
async function handleLogout() {
  try {
    await fetch('/api/auth/logout', { method: 'POST' });
    showToast('Sesión de administrador finalizada.', 'info');
    setTimeout(() => {
      window.location.href = '/';
    }, 600);
  } catch (err) {
    window.location.href = '/';
  }
}

/**
 * 11. Sistema de Notificaciones Toast Flotantes
 */
function showToast(message, type = 'info') {
  let container = document.getElementById('toastContainer');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toastContainer';
    container.className = 'toast-container';
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.innerText = message;

  container.appendChild(toast);

  setTimeout(() => {
    toast.classList.add('toast-hiding');
    setTimeout(() => toast.remove(), 400);
  }, 4000);
}

// Exponer showToast para uso global
window.showToast = showToast;
