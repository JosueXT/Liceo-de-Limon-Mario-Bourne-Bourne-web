/**
 * ============================================================================
 * SISTEMA CMS WYSIWYG & GESTOR VISUAL EN VIVO
 * Liceo de Limón Mario Bourne Bourne (MEP)
 * ============================================================================
 * GUÍA DE FUNCIONAMIENTO EN VIVO:
 * 1. Cuando un usuario con sesión de administrador visita cualquier página
 *    (Inicio o subpáginas de modalidades), se activa el MODO EDICIÓN VISUAL.
 * 2. Todos los textos marcados con [data-cms-key] se pueden editar directamente
 *    haciendo clic y escribiendo sobre ellos.
 * 3. Las imágenes y logotipos (.cms-image-wrapper) abren un selector para cambiar su URL.
 * 4. Botón "👁️ Vista Previa": Oculta los bordes para ver exactamente el resultado final.
 * 5. Botón "💾 Guardar Cambios": Guarda las modificaciones en SQLite sin recargar.
 * ============================================================================
 */

const CMS_STATE = {
  isAdmin: false,
  isEditMode: true,
  modifiedItems: {}, // Guarda los pares { clave: nuevoValor }
  currentEditingImageKey: null
};

document.addEventListener('DOMContentLoaded', () => {
  const isAdmin = document.body.getAttribute('data-is-admin') === 'true';

  if (isAdmin) {
    enableVisualEditMode();
  }

  initImageModal();
});

/**
 * 1. Activar Modo Edición Visual en la Página
 */
function enableVisualEditMode() {
  CMS_STATE.isAdmin = true;
  CMS_STATE.isEditMode = true;
  document.body.classList.add('cms-edit-mode');

  // Crear o mostrar la barra flotante inferior
  createOrShowFloatingToolbar();

  // Habilitar edición in-situ en todos los elementos con data-cms-key
  applyContentEditable(true);

  // Escuchar escritura en cualquier elemento editable
  document.addEventListener('input', (e) => {
    const target = e.target;
    if (target && target.hasAttribute && target.hasAttribute('data-cms-key')) {
      const key = target.getAttribute('data-cms-key');
      const newValue = target.innerText.trim();

      CMS_STATE.modifiedItems[key] = newValue;
      target.classList.add('cms-modified');
      updateModifiedCounter();
    }
  });

  // Escuchar clics en imágenes editables
  document.addEventListener('click', (e) => {
    if (!CMS_STATE.isAdmin || !CMS_STATE.isEditMode || document.body.classList.contains('cms-preview-mode')) return;

    const wrapper = e.target.closest('.cms-image-wrapper');
    if (wrapper) {
      e.preventDefault();
      const img = wrapper.querySelector('img[data-cms-img]') || wrapper.querySelector('img');
      const key = (img && img.getAttribute('data-cms-img')) || wrapper.getAttribute('data-cms-img');
      const currentSrc = (img && img.getAttribute('src')) || '';

      if (key) {
        openImageEditModal(key, currentSrc);
      }
    }
  });
}

/**
 * 2. Aplicar o retirar contentEditable
 */
function applyContentEditable(enabled) {
  const editables = document.querySelectorAll('[data-cms-key]');
  editables.forEach(el => {
    el.contentEditable = enabled ? 'true' : 'false';
    el.spellcheck = false;
  });
}

/**
 * 3. Crear Barra Flotante de Herramientas del Administrador
 */
function createOrShowFloatingToolbar() {
  let toolbar = document.getElementById('adminFloatingToolbar');
  if (toolbar) {
    toolbar.style.display = 'flex';
    return;
  }

  toolbar = document.createElement('div');
  toolbar.id = 'adminFloatingToolbar';
  toolbar.className = 'admin-toolbar-floating';
  toolbar.innerHTML = `
    <div class="admin-status-indicator">
      <span class="admin-pulse-dot"></span>
      <span class="admin-mode-text" id="adminModeStatusText">Modo Edición Activo</span>
    </div>
    <div class="admin-actions-group">
      <button class="btn-admin btn-admin-save" id="btnAdminSaveAll" title="Guardar todos los cambios en la base de datos">
        💾 Guardar Cambios (<span id="modifiedCount">0</span>)
      </button>
      <button class="btn-admin btn-admin-toggle" id="btnAdminTogglePreview" title="Ocultar bordes para ver el diseño final">
        👁️ Vista Previa
      </button>
      <a href="/admin/panel" class="btn-admin btn-admin-panel" title="Ir al panel de administración">
        ⚙️ Panel de Control
      </a>
      <a href="/logout" class="btn-admin btn-admin-logout" title="Cerrar sesión">
        🚪 Salir
      </a>
    </div>
  `;
  document.body.appendChild(toolbar);

  // Eventos de la barra
  document.getElementById('btnAdminSaveAll')?.addEventListener('click', saveAllCmsChanges);
  document.getElementById('btnAdminTogglePreview')?.addEventListener('click', togglePreviewMode);
}

/**
 * 4. Alternar Modo Vista Previa
 */
function togglePreviewMode() {
  const btn = document.getElementById('btnAdminTogglePreview');
  const statusText = document.getElementById('adminModeStatusText');

  if (document.body.classList.contains('cms-preview-mode')) {
    // Volver a modo edición
    document.body.classList.remove('cms-preview-mode');
    applyContentEditable(true);
    if (btn) btn.innerHTML = '👁️ Vista Previa';
    if (statusText) statusText.innerText = 'Modo Edición Activo';
    showToast('✏️ Modo Edición Reactivado: Haz clic sobre cualquier texto para editar.', 'info');
  } else {
    // Activar vista previa
    document.body.classList.add('cms-preview-mode');
    applyContentEditable(false);
    if (btn) btn.innerHTML = '✏️ Volver a Editar';
    if (statusText) statusText.innerText = 'Modo Vista Previa';
    showToast('👁️ Vista Previa: Visualizando la página exactamente como el público.', 'info');
  }
}

/**
 * 5. Contador de Cambios Pendientes
 */
function updateModifiedCounter() {
  const countSpan = document.getElementById('modifiedCount');
  const count = Object.keys(CMS_STATE.modifiedItems).length;
  if (countSpan) {
    countSpan.innerText = count;
  }
}

/**
 * 6. Guardar Todos los Cambios en SQLite vía Fetch
 */
async function saveAllCmsChanges() {
  const keys = Object.keys(CMS_STATE.modifiedItems);
  if (keys.length === 0) {
    showToast('No hay modificaciones pendientes por guardar.', 'info');
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
 * 7. Modal de Cambio de Imagen y Logotipo
 */
function initImageModal() {
  let modal = document.getElementById('editImageModal');
  if (!modal) {
    modal = document.createElement('div');
    modal.id = 'editImageModal';
    modal.className = 'modal-backdrop';
    modal.style.display = 'none';
    modal.innerHTML = `
      <div class="modal-dialog" style="max-width: 540px; padding: 2.2rem; background: var(--blanco); border-radius: var(--radius-xl);">
        <button class="modal-close-btn" id="closeImageModalBtn" style="top: 1rem; right: 1rem;">&times;</button>
        <h3 style="font-family: var(--font-heading); font-size: 1.4rem; color: var(--azul-dark); margin-bottom: 0.5rem;">📷 Cambiar Fotografía o Logotipo</h3>
        <p style="font-size: 0.875rem; color: var(--gris-600); margin-bottom: 1.2rem;">Ingrese la URL de la nueva imagen para actualizarla en vivo:</p>
        
        <div style="text-align: center; margin-bottom: 1.2rem;">
          <img id="imageModalPreview" src="" alt="Previsualización" style="max-height: 160px; margin: 0 auto; border-radius: var(--radius-md); object-fit: cover;">
        </div>

        <form id="editImageForm">
          <div class="form-group" style="text-align: left;">
            <label class="form-label" for="imageUrlInput">URL de la Imagen</label>
            <input type="url" id="imageUrlInput" class="form-control" required placeholder="https://ejemplo.com/foto.jpg">
          </div>

          <div style="margin-bottom: 1.2rem; text-align: left;">
            <label class="form-label">Sugerencias rápidas:</label>
            <div style="display: flex; gap: 0.4rem; flex-wrap: wrap;">
              <button type="button" class="btn btn-outline btn-sm" onclick="setImageModalPreset('https://imgs.search.brave.com/Ly6Ar6F6AGvQFNCB_BgS9qNxglA60fHIL7u-4j1cCN8/rs:fit:860:0:0:0/g:ce/aHR0cHM6Ly93d3cu/bWVwLmdvLmNyL3Np/dGVzL2RlZmF1bHQv/ZmlsZXMvc3R5bGVz/L3Jlc3BvbnNpdmVf/MV8xXzIwMHcvcHVi/bGljL21lZGlhL2Vz/Y3Vkby1saWNlby1u/dWV2by1saW1vbi5q/cGc_aD1jMDE3OWIz/NyZpdG9rPTZJQmo1/cnFx')">Escudo Oficial MEP</button>
              <button type="button" class="btn btn-outline btn-sm" onclick="setImageModalPreset('https://images.unsplash.com/photo-1541339907198-e08756dedf3f?auto=format&fit=crop&w=1200&q=80')">Campus y Edificio</button>
              <button type="button" class="btn btn-outline btn-sm" onclick="setImageModalPreset('https://images.unsplash.com/photo-1523240795612-9a054b0db644?auto=format&fit=crop&w=1200&q=80')">Estudiantes</button>
            </div>
          </div>

          <button type="submit" class="btn btn-vino btn-lg" style="width: 100%;">
            Aplicar a la Vista
          </button>
        </form>
      </div>
    `;
    document.body.appendChild(modal);

    document.getElementById('closeImageModalBtn')?.addEventListener('click', () => {
      modal.classList.remove('active');
      modal.style.display = 'none';
    });

    const urlInput = document.getElementById('imageUrlInput');
    const previewImg = document.getElementById('imageModalPreview');
    urlInput?.addEventListener('input', () => {
      if (previewImg) previewImg.src = urlInput.value.trim();
    });

    document.getElementById('editImageForm')?.addEventListener('submit', (e) => {
      e.preventDefault();
      const newUrl = urlInput.value.trim();
      const key = CMS_STATE.currentEditingImageKey;

      if (newUrl && key) {
        // Actualizar en la vista
        document.querySelectorAll(`img[data-cms-img="${key}"]`).forEach(img => {
          img.src = newUrl;
        });

        document.querySelectorAll(`[data-cms-img="${key}"]`).forEach(el => {
          if (!el.matches('img')) {
            el.style.backgroundImage = `url('${newUrl}')`;
          }
        });

        // Registrar como modificado
        CMS_STATE.modifiedItems[key] = newUrl;
        updateModifiedCounter();
        modal.classList.remove('active');
        modal.style.display = 'none';
        showToast('✓ Imagen actualizada en la vista. Recuerda guardar cambios.', 'info');
      }
    });
  }
}

function openImageEditModal(key, currentSrc) {
  CMS_STATE.currentEditingImageKey = key;
  const modal = document.getElementById('editImageModal');
  const urlInput = document.getElementById('imageUrlInput');
  const preview = document.getElementById('imageModalPreview');

  if (urlInput) urlInput.value = currentSrc;
  if (preview) preview.src = currentSrc;
  if (modal) {
    modal.style.display = 'flex';
    modal.classList.add('active');
  }
}

function setImageModalPreset(url) {
  const urlInput = document.getElementById('imageUrlInput');
  const preview = document.getElementById('imageModalPreview');
  if (urlInput) urlInput.value = url;
  if (preview) preview.src = url;
}
window.setImageModalPreset = setImageModalPreset;

/**
 * 8. Notificaciones Toast Flotantes
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

window.showToast = showToast;
