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

  // Inicializar controles de listas y tablas dinámicas (agregar / eliminar items)
  initDynamicListControls();

  // Inicializar controles de visibilidad de secciones y bloques (ocultar / mostrar al público)
  initVisibilityToggleControls();

  // Escuchar escritura en cualquier elemento editable (con soporte para nodos hijos y formato)
  let autoSaveTimeout = null;
  function triggerAutoSave() {
    clearTimeout(autoSaveTimeout);
    autoSaveTimeout = setTimeout(() => {
      if (Object.keys(CMS_STATE.modifiedItems).length > 0) {
        saveAllCmsChanges(false); // auto-guardado en segundo plano
      }
    }, 1500);
  }

  function recordEditableChange(el) {
    if (!el) return;
    const key = el.getAttribute('data-cms-key');
    if (!key) return;
    const newValue = el.innerText.trim();
    CMS_STATE.modifiedItems[key] = newValue;
    el.classList.add('cms-modified');
    updateModifiedCounter();
    triggerAutoSave();
  }

  document.addEventListener('input', (e) => {
    const el = e.target.closest ? e.target.closest('[data-cms-key]') : null;
    if (el) {
      recordEditableChange(el);
    }
  });

  // Escuchar desenfoque (blur / focusout) para asegurar captura inmediata
  document.addEventListener('focusout', (e) => {
    const el = e.target.closest ? e.target.closest('[data-cms-key]') : null;
    if (el) {
      recordEditableChange(el);
    }
  });

  // Atajo de teclado: Ctrl+S o Cmd+S para guardar de inmediato
  document.addEventListener('keydown', (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 's') {
      if (CMS_STATE.isAdmin && CMS_STATE.isEditMode) {
        e.preventDefault();
        saveAllCmsChanges(true);
      }
    }
  });

  // Prevenir navegación accidental de enlaces al hacer clic para editar botones y textos con enlace
  document.addEventListener('click', (e) => {
    if (!CMS_STATE.isAdmin || !CMS_STATE.isEditMode || document.body.classList.contains('cms-preview-mode')) return;

    const editableChild = e.target.closest ? e.target.closest('[data-cms-key]') : null;
    if (editableChild) {
      const parentLink = editableChild.closest('a');
      if (parentLink) {
        e.preventDefault();
        editableChild.focus();
        return;
      }
    }

    const wrapper = e.target.closest ? e.target.closest('.cms-image-wrapper') : null;
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

  // Advertir al usuario si intenta cerrar o recargar con cambios pendientes
  window.addEventListener('beforeunload', (e) => {
    if (CMS_STATE.isAdmin && Object.keys(CMS_STATE.modifiedItems).length > 0) {
      e.preventDefault();
      e.returnValue = 'Tiene cambios de contenido pendientes de guardar en la base de datos.';
      return e.returnValue;
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
async function saveAllCmsChanges(showFeedback = true) {
  // Asegurar que cualquier elemento marcado como modificado en el DOM esté en el payload
  document.querySelectorAll('[data-cms-key].cms-modified').forEach(el => {
    const key = el.getAttribute('data-cms-key');
    if (key && !(key in CMS_STATE.modifiedItems)) {
      CMS_STATE.modifiedItems[key] = el.innerText.trim();
    }
  });

  const keys = Object.keys(CMS_STATE.modifiedItems);
  if (keys.length === 0) {
    if (showFeedback) {
      showToast('No hay modificaciones pendientes por guardar.', 'info');
    }
    return;
  }

  const saveBtn = document.getElementById('btnAdminSaveAll');
  const statusText = document.getElementById('adminModeStatusText');
  const originalStatus = statusText ? statusText.innerText : 'Modo Edición Activo';

  if (saveBtn) {
    saveBtn.disabled = true;
    saveBtn.innerHTML = '⏳ Guardando...';
  }
  if (statusText) {
    statusText.innerText = 'Guardando cambios en base de datos...';
  }

  try {
    const res = await fetch('/api/cms/content', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ items: CMS_STATE.modifiedItems })
    });

    const data = await res.json();

    if (res.ok && data.success) {
      const backupTitle = data.backup && data.backup.title ? data.backup.title : null;
      if (showFeedback) {
        if (backupTitle) {
          showToast(`✓ Guardado. Respaldo creado: ${backupTitle}`, 'success');
        } else {
          showToast('✓ ¡Todos los cambios han sido guardados en la base de datos!', 'success');
        }
      }
      CMS_STATE.modifiedItems = {};
      updateModifiedCounter();
      document.querySelectorAll('.cms-modified').forEach(el => el.classList.remove('cms-modified'));
      if (statusText) {
        statusText.innerText = backupTitle ? `✓ ${backupTitle}` : '✓ Guardado en base de datos';
        setTimeout(() => {
          if (statusText) {
            statusText.innerText = 'Modo Edición Activo';
          }
        }, 3500);
      }
    } else {
      if (showFeedback) {
        showToast('Error al guardar: ' + (data.message || 'Desconocido'), 'error');
      }
    }
  } catch (err) {
    if (showFeedback) {
      showToast('Error de conexión al guardar cambios.', 'error');
    }
  } finally {
    if (saveBtn) {
      saveBtn.disabled = false;
      saveBtn.innerHTML = `💾 Guardar Cambios (<span id="modifiedCount">0</span>)`;
    }
  }
}

/**
 * 7. Modal de Cambio de Imagen y Logotipo con Control de Encuadre / Posición
 */
function initImageModal() {
  let modal = document.getElementById('editImageModal');
  if (!modal) {
    modal = document.createElement('div');
    modal.id = 'editImageModal';
    modal.className = 'modal-backdrop';
    modal.style.display = 'none';
    modal.innerHTML = `
      <div class="modal-dialog" style="max-width: 580px; padding: 2.2rem; background: var(--blanco); border-radius: var(--radius-xl); max-height: 90vh; overflow-y: auto;">
        <button class="modal-close-btn" id="closeImageModalBtn" style="top: 1rem; right: 1rem;">&times;</button>
        <h3 id="imageModalTitle" style="font-family: var(--font-heading); font-size: 1.4rem; color: var(--azul-dark); margin-bottom: 0.5rem;">📷 Cambiar Fotografía o Logotipo</h3>
        <p style="font-size: 0.875rem; color: var(--gris-600); margin-bottom: 1.2rem;">Ingrese la URL y ajuste el encuadre para que se vea en el punto exacto:</p>
        
        <div style="text-align: center; margin-bottom: 1.2rem; overflow: hidden; background: var(--gris-200); border-radius: var(--radius-md); max-height: 190px; display: flex; align-items: center; justify-content: center; position: relative;">
          <img id="imageModalPreview" src="" alt="Previsualización" style="width: 100%; height: 190px; object-fit: cover; object-position: 50% 50%; transition: object-position 0.15s ease, transform 0.15s ease;">
          <span style="position: absolute; bottom: 6px; right: 8px; font-size: 0.72rem; background: rgba(0,0,0,0.65); color: #fff; padding: 2px 7px; border-radius: 4px; font-family: monospace;" id="imageModalFocalBadge">50% 50%</span>
        </div>

        <form id="editImageForm">
          <div class="form-group" style="text-align: left; margin-bottom: 0.8rem;">
            <label class="form-label" for="imageUrlInput">URL de la Imagen</label>
            <input type="url" id="imageUrlInput" class="form-control" required placeholder="https://ejemplo.com/foto.jpg o enlace de Google Drive">
            <small style="display: block; margin-top: 0.35rem; color: var(--gris-600); font-size: 0.75rem;">💡 Soporta enlaces directos y de Google Drive (asegúrese de que el archivo esté compartido en "Cualquier persona con el enlace").</small>
          </div>

          <!-- Control Interactivo de Encuadre / Posición Focal -->
          <div style="background: var(--gris-100); border: 1px solid var(--gris-300); border-radius: 8px; padding: 0.85rem; margin-bottom: 1rem; text-align: left;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
              <span style="font-size: 0.82rem; font-weight: 700; color: var(--gris-800);">🎯 Ajustar Encuadre (Mover Foto):</span>
              <span style="font-size: 0.78rem; color: var(--azul); font-weight: 600;" id="modalFocalLabel">Centro</span>
            </div>

            <div style="display: flex; gap: 0.8rem; align-items: center; flex-wrap: wrap;">
              <!-- Botones direccionales 3x3 -->
              <div style="display: grid; grid-template-columns: repeat(3, 34px); gap: 4px;">
                <button type="button" class="btn btn-outline btn-sm" style="padding: 0; height: 32px; font-size: 0.85rem;" title="Arriba Izq" onclick="setModalImageFocal(0, 0, 'Arriba Izq')">↖</button>
                <button type="button" class="btn btn-outline btn-sm" style="padding: 0; height: 32px; font-size: 0.85rem;" title="Arriba Centro" onclick="setModalImageFocal(50, 0, 'Arriba Centro')">⬆</button>
                <button type="button" class="btn btn-outline btn-sm" style="padding: 0; height: 32px; font-size: 0.85rem;" title="Arriba Der" onclick="setModalImageFocal(100, 0, 'Arriba Der')">↗</button>
                <button type="button" class="btn btn-outline btn-sm" style="padding: 0; height: 32px; font-size: 0.85rem;" title="Centro Izq" onclick="setModalImageFocal(0, 50, 'Centro Izq')">⬅</button>
                <button type="button" class="btn btn-outline btn-sm" style="padding: 0; height: 32px; font-size: 0.85rem; font-weight: bold;" title="Centro" onclick="setModalImageFocal(50, 50, 'Centro')">⏺</button>
                <button type="button" class="btn btn-outline btn-sm" style="padding: 0; height: 32px; font-size: 0.85rem;" title="Centro Der" onclick="setModalImageFocal(100, 50, 'Centro Der')">➡</button>
                <button type="button" class="btn btn-outline btn-sm" style="padding: 0; height: 32px; font-size: 0.85rem;" title="Abajo Izq" onclick="setModalImageFocal(0, 100, 'Abajo Izq')">↙</button>
                <button type="button" class="btn btn-outline btn-sm" style="padding: 0; height: 32px; font-size: 0.85rem;" title="Abajo Centro" onclick="setModalImageFocal(50, 100, 'Abajo Centro')">⬇</button>
                <button type="button" class="btn btn-outline btn-sm" style="padding: 0; height: 32px; font-size: 0.85rem;" title="Abajo Der" onclick="setModalImageFocal(100, 100, 'Abajo Der')">↘</button>
              </div>

              <!-- Sliders de precisión -->
              <div style="flex: 1; min-width: 170px; display: flex; flex-direction: column; gap: 0.35rem;">
                <div style="display: flex; justify-content: space-between; font-size: 0.75rem; color: var(--gris-700);">
                  <span>↕️ Altura (Y):</span>
                  <span id="modalFocalYText">50%</span>
                </div>
                <input type="range" id="modalFocalYSlider" min="0" max="100" value="50" style="width: 100%; cursor: pointer;" oninput="onModalFocalSliderChange()">

                <div style="display: flex; justify-content: space-between; font-size: 0.75rem; color: var(--gris-700);">
                  <span>↔️ Lado (X):</span>
                  <span id="modalFocalXText">50%</span>
                </div>
                <input type="range" id="modalFocalXSlider" min="0" max="100" value="50" style="width: 100%; cursor: pointer;" oninput="onModalFocalSliderChange()">
              </div>
            </div>
          </div>

          <div style="margin-bottom: 1.2rem; text-align: left;">
            <label class="form-label">Sugerencias rápidas:</label>
            <div id="imageModalPresets" style="display: flex; gap: 0.4rem; flex-wrap: wrap;">
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

    function parseDriveImageUrl(url) {
      if (!url) return '';
      const trimmed = url.trim();
      const driveMatch = trimmed.match(/\/file\/d\/([a-zA-Z0-9_-]+)/) ||
                         trimmed.match(/id=([a-zA-Z0-9_-]+)/);
      if (driveMatch && (trimmed.includes('drive.google.com') || trimmed.includes('docs.google.com'))) {
        return `https://lh3.googleusercontent.com/d/${driveMatch[1]}`;
      }
      return trimmed;
    }

    urlInput?.addEventListener('input', () => {
      const parsed = parseDriveImageUrl(urlInput.value);
      if (parsed !== urlInput.value) {
        urlInput.value = parsed;
      }
      if (previewImg) previewImg.src = urlInput.value.trim();
    });

    urlInput?.addEventListener('change', () => {
      const parsed = parseDriveImageUrl(urlInput.value);
      if (parsed !== urlInput.value) {
        urlInput.value = parsed;
      }
      if (previewImg) previewImg.src = urlInput.value.trim();
    });

    document.getElementById('editImageForm')?.addEventListener('submit', (e) => {
      e.preventDefault();
      const newUrl = parseDriveImageUrl(urlInput.value.trim());
      const key = CMS_STATE.currentEditingImageKey;
      const xSlider = document.getElementById('modalFocalXSlider');
      const ySlider = document.getElementById('modalFocalYSlider');
      const x = xSlider ? xSlider.value : 50;
      const y = ySlider ? ySlider.value : 50;
      const positionVal = `${x}% ${y}%`;

      if (newUrl && key) {
        // Actualizar en la vista
        document.querySelectorAll(`img[data-cms-img="${key}"]`).forEach(img => {
          img.src = newUrl;
          img.style.objectPosition = positionVal;
        });

        document.querySelectorAll(`[data-cms-img="${key}"]`).forEach(el => {
          if (!el.matches('img')) {
            el.style.backgroundImage = `url('${newUrl}')`;
            el.style.backgroundPosition = positionVal;
          }
        });

        // Registrar como modificado URL y posición focal
        CMS_STATE.modifiedItems[key] = newUrl;
        CMS_STATE.modifiedItems[key + '_position'] = positionVal;
        updateModifiedCounter();
        modal.classList.remove('active');
        modal.style.display = 'none';
        showToast('✓ Imagen y encuadre actualizados en la vista. Recuerda guardar cambios.', 'info');
      }
    });
  }
}

function setModalImageFocal(x, y, label) {
  const xSlider = document.getElementById('modalFocalXSlider');
  const ySlider = document.getElementById('modalFocalYSlider');
  const xText = document.getElementById('modalFocalXText');
  const yText = document.getElementById('modalFocalYText');
  const preview = document.getElementById('imageModalPreview');
  const badge = document.getElementById('imageModalFocalBadge');
  const lbl = document.getElementById('modalFocalLabel');

  if (xSlider) xSlider.value = x;
  if (ySlider) ySlider.value = y;
  if (xText) xText.innerText = `${x}%`;
  if (yText) yText.innerText = `${y}%`;
  if (badge) badge.innerText = `${x}% ${y}%`;
  if (lbl && label) lbl.innerText = label;
  if (preview) preview.style.objectPosition = `${x}% ${y}%`;
}
window.setModalImageFocal = setModalImageFocal;

function onModalFocalSliderChange() {
  const x = document.getElementById('modalFocalXSlider')?.value || 50;
  const y = document.getElementById('modalFocalYSlider')?.value || 50;
  const preview = document.getElementById('imageModalPreview');
  const badge = document.getElementById('imageModalFocalBadge');
  const xText = document.getElementById('modalFocalXText');
  const yText = document.getElementById('modalFocalYText');
  const lbl = document.getElementById('modalFocalLabel');

  if (xText) xText.innerText = `${x}%`;
  if (yText) yText.innerText = `${y}%`;
  if (badge) badge.innerText = `${x}% ${y}%`;
  if (lbl) lbl.innerText = `Personalizado (${x}% ${y}%)`;
  if (preview) preview.style.objectPosition = `${x}% ${y}%`;
}
window.onModalFocalSliderChange = onModalFocalSliderChange;

function promptEditCmsLink(key, elementId) {
  const currentLink = CMS_STATE.modifiedItems[key] || (document.getElementById(elementId)?.getAttribute('href')) || '';
  const newLink = prompt('Ingrese el enlace oficial (URL):', currentLink);
  if (newLink !== null && newLink.trim()) {
    const el = document.getElementById(elementId);
    if (el) el.setAttribute('href', newLink.trim());
    CMS_STATE.modifiedItems[key] = newLink.trim();
    updateModifiedCounter();
    showToast('✓ Enlace actualizado en la vista. Recuerda hacer clic en "Guardar Cambios".', 'info');
  }
}
window.promptEditCmsLink = promptEditCmsLink;

function openImageEditModal(key, currentSrc) {
  CMS_STATE.currentEditingImageKey = key;
  const modal = document.getElementById('editImageModal');
  const urlInput = document.getElementById('imageUrlInput');
  const preview = document.getElementById('imageModalPreview');
  const modalTitle = document.getElementById('imageModalTitle');
  const presetsContainer = document.getElementById('imageModalPresets');

  if (urlInput) urlInput.value = currentSrc;
  if (preview) preview.src = currentSrc;

  if (key === 'header_mep_flag') {
    if (modalTitle) modalTitle.innerText = '🚩 Cambiar Bandera o Insignia Superior';
    if (presetsContainer) {
      presetsContainer.innerHTML = `
        <button type="button" class="btn btn-outline btn-sm" onclick="setImageModalPreset('/static/img/bandera_costa_rica.svg')">🇨🇷 Costa Rica</button>
        <button type="button" class="btn btn-outline btn-sm" onclick="setImageModalPreset('/static/img/bandera_limon.svg')">🟢 Bandera de Limón</button>
        <button type="button" class="btn btn-outline btn-sm" onclick="setImageModalPreset('/static/img/bandera_francia.svg')">🇫🇷 Francia (DELF)</button>
        <button type="button" class="btn btn-outline btn-sm" onclick="setImageModalPreset('https://upload.wikimedia.org/wikipedia/commons/thumb/0/07/International_Baccalaureate_Logo.svg/64px-International_Baccalaureate_Logo.svg.png')">🌐 Bachillerato IB</button>
        <button type="button" class="btn btn-outline btn-sm" onclick="setImageModalPreset('https://imgs.search.brave.com/Ly6Ar6F6AGvQFNCB_BgS9qNxglA60fHIL7u-4j1cCN8/rs:fit:860:0:0:0/g:ce/aHR0cHM6Ly93d3cu/bWVwLmdvLmNyL3Np/dGVzL2RlZmF1bHQv/ZmlsZXMvc3R5bGVz/L3Jlc3BvbnNpdmVf/MV8xXzIwMHcvcHVi/bGljL21lZGlhL2Vz/Y3Vkby1saWNlby1u/dWV2by1saW1vbi5q/cGc_aD1jMDE3OWIz/NyZpdG9rPTZJQmo1/cnFx')">🏫 Escudo MEP</button>
      `;
    }
  } else {
    if (modalTitle) modalTitle.innerText = '📷 Cambiar Fotografía o Logotipo';
    if (presetsContainer) {
      presetsContainer.innerHTML = `
        <button type="button" class="btn btn-outline btn-sm" onclick="setImageModalPreset('https://imgs.search.brave.com/Ly6Ar6F6AGvQFNCB_BgS9qNxglA60fHIL7u-4j1cCN8/rs:fit:860:0:0:0/g:ce/aHR0cHM6Ly93d3cu/bWVwLmdvLmNyL3Np/dGVzL2RlZmF1bHQv/ZmlsZXMvc3R5bGVz/L3Jlc3BvbnNpdmVf/MV8xXzIwMHcvcHVi/bGljL21lZGlhL2Vz/Y3Vkby1saWNlby1u/dWV2by1saW1vbi5q/cGc_aD1jMDE3OWIz/NyZpdG9rPTZJQmo1/cnFx')">Escudo Oficial MEP</button>
        <button type="button" class="btn btn-outline btn-sm" onclick="setImageModalPreset('https://images.unsplash.com/photo-1541339907198-e08756dedf3f?auto=format&fit=crop&w=1200&q=80')">Campus y Edificio</button>
        <button type="button" class="btn btn-outline btn-sm" onclick="setImageModalPreset('https://images.unsplash.com/photo-1523240795612-9a054b0db644?auto=format&fit=crop&w=1200&q=80')">Estudiantes</button>
      `;
    }
  }

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

/**
 * ============================================================================
 * 9. GESTIÓN DINÁMICA DE LISTAS Y TABLAS (AGREGAR / ELIMINAR ELEMENTOS)
 * ============================================================================
 */

function initDynamicListControls() {
  document.addEventListener('click', (e) => {
    if (!CMS_STATE.isAdmin || !CMS_STATE.isEditMode || document.body.classList.contains('cms-preview-mode')) return;

    // 1. Manejo del botón "+ Agregar Elemento"
    const addBtn = e.target.closest('.cms-add-item-btn');
    if (addBtn) {
      e.preventDefault();
      const listType = addBtn.getAttribute('data-cms-add-target');
      const prefix = addBtn.getAttribute('data-cms-prefix');

      let container = null;
      if (listType === 'curriculum') {
        const wrapper = addBtn.closest('.curriculum-table-wrapper');
        container = (wrapper && wrapper.querySelector('table[data-cms-list="curriculum"]')) || document.querySelector(`table[data-cms-list="curriculum"][data-cms-prefix="${prefix}"]`);
      } else {
        container = addBtn.previousElementSibling;
        if (!container || !container.hasAttribute('data-cms-list')) {
          container = addBtn.parentElement.querySelector(`[data-cms-list="${listType}"]`) || document.querySelector(`[data-cms-list="${listType}"][data-cms-prefix="${prefix}"]`);
        }
      }

      if (container) {
        handleAddDynamicItem(container, listType, prefix);
      }
      return;
    }

    // 2. Manejo del botón "✕ Eliminar Elemento"
    const deleteBtn = e.target.closest('.cms-delete-item-btn');
    if (deleteBtn) {
      e.preventDefault();
      const itemEl = deleteBtn.closest('[data-cms-item-index]');
      if (!itemEl) return;
      const container = itemEl.closest('[data-cms-list]');
      if (!container) return;

      const listType = container.getAttribute('data-cms-list');
      const prefix = container.getAttribute('data-cms-prefix');

      handleDeleteDynamicItem(itemEl, container, listType, prefix);
      return;
    }
  });
}

function handleAddDynamicItem(container, listType, prefix) {
  const isTable = listType === 'curriculum';
  const parent = isTable ? (container.querySelector('tbody') || container) : container;
  const currentItems = isTable ? parent.querySelectorAll('tr[data-cms-item-index]') : parent.querySelectorAll('[data-cms-item-index]');
  const newIndex = currentItems.length + 1;

  let newElement = null;

  if (listType === 'advantages') {
    newElement = document.createElement('div');
    newElement.className = 'advantage-item';
    newElement.setAttribute('data-cms-item-index', newIndex);
    newElement.innerHTML = `
      <span class="advantage-check-icon">✓</span>
      <p class="advantage-text cms-modified" data-cms-key="${prefix}${newIndex}" contenteditable="true" spellcheck="false">Nuevo beneficio para el estudiante...</p>
      <button type="button" class="cms-delete-item-btn" title="Eliminar este beneficio" aria-label="Eliminar beneficio">✕</button>
    `;
    parent.appendChild(newElement);
    CMS_STATE.modifiedItems[`${prefix}${newIndex}`] = "Nuevo beneficio para el estudiante...";

  } else if (listType === 'requirements') {
    newElement = document.createElement('li');
    newElement.className = 'requirement-list-item';
    newElement.setAttribute('data-cms-item-index', newIndex);
    newElement.innerHTML = `
      <span class="req-number">${newIndex}</span>
      <span class="req-text cms-modified" data-cms-key="${prefix}${newIndex}" contenteditable="true" spellcheck="false">Nuevo requisito de ingreso...</span>
      <button type="button" class="cms-delete-item-btn" title="Eliminar este requisito" aria-label="Eliminar requisito">✕</button>
    `;
    parent.appendChild(newElement);
    CMS_STATE.modifiedItems[`${prefix}${newIndex}`] = "Nuevo requisito de ingreso...";

  } else if (listType === 'curriculum') {
    newElement = document.createElement('tr');
    newElement.setAttribute('data-cms-item-index', newIndex);
    newElement.innerHTML = `
      <td class="curriculum-group-cell">
        <strong class="cms-modified" data-cms-key="${prefix}group_${newIndex}" contenteditable="true" spellcheck="false">Nuevo Grupo / Área</strong>
      </td>
      <td class="curriculum-subject-cell cms-modified" data-cms-key="${prefix}subject_${newIndex}" contenteditable="true" spellcheck="false">Nueva Asignatura y Enfoque Pedagógico</td>
      <td class="cms-td-actions">
        <button type="button" class="cms-delete-item-btn" title="Eliminar esta fila" aria-label="Eliminar fila">✕</button>
      </td>
    `;
    parent.appendChild(newElement);
    CMS_STATE.modifiedItems[`${prefix}group_${newIndex}`] = "Nuevo Grupo / Área";
    CMS_STATE.modifiedItems[`${prefix}subject_${newIndex}`] = "Nueva Asignatura y Enfoque Pedagógico";

  } else if (listType === 'pillars') {
    newElement = document.createElement('div');
    newElement.className = 'pillar-card reveal-scale';
    newElement.setAttribute('data-cms-item-index', newIndex);
    const formattedNum = String(newIndex).padStart(2, '0');
    newElement.innerHTML = `
      <div class="pillar-card-top-bar">
        <div class="pillar-number">${formattedNum}</div>
        <button type="button" class="cms-delete-item-btn" title="Eliminar este pilar" aria-label="Eliminar pilar">✕</button>
      </div>
      <h3 class="pillar-title cms-modified" data-cms-key="${prefix}${newIndex}_title" contenteditable="true" spellcheck="false">Nuevo Pilar Formativo</h3>
      <p class="pillar-desc cms-modified" data-cms-key="${prefix}${newIndex}_desc" contenteditable="true" spellcheck="false">Descripción de este pilar formativo institucional...</p>
    `;
    parent.appendChild(newElement);
    CMS_STATE.modifiedItems[`${prefix}${newIndex}_title`] = "Nuevo Pilar Formativo";
    CMS_STATE.modifiedItems[`${prefix}${newIndex}_desc`] = "Descripción de este pilar formativo institucional...";

  } else if (listType === 'features') {
    newElement = document.createElement('div');
    newElement.className = 'pathway-feature-item';
    newElement.setAttribute('data-cms-item-index', newIndex);
    newElement.innerHTML = `
      <span class="feature-icon-bullet">✓</span>
      <span class="cms-modified" data-cms-key="${prefix}${newIndex}" contenteditable="true" spellcheck="false">Nuevo pilar formativo...</span>
      <button type="button" class="cms-delete-item-btn" title="Eliminar beneficio" aria-label="Eliminar beneficio">✕</button>
    `;
    parent.appendChild(newElement);
    CMS_STATE.modifiedItems[`${prefix}${newIndex}`] = "Nuevo pilar formativo...";

  } else if (listType === 'campus') {
    newElement = document.createElement('div');
    newElement.className = 'campus-card reveal delay-100';
    newElement.setAttribute('data-cms-item-index', newIndex);
    newElement.innerHTML = `
      <div class="campus-card-top-bar" style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 1.4rem;">
        <div class="campus-icon-box cms-modified" data-cms-key="${prefix}${newIndex}_icon" contenteditable="true" spellcheck="false" title="Haga clic para editar ícono" style="margin-bottom: 0;">🏫</div>
        <button type="button" class="cms-delete-item-btn" title="Eliminar este espacio educativo" aria-label="Eliminar espacio">✕</button>
      </div>
      <h3 class="campus-card-title cms-modified" data-cms-key="${prefix}${newIndex}_title" contenteditable="true" spellcheck="false">Nuevo Espacio Educativo</h3>
      <p class="campus-card-desc cms-modified" data-cms-key="${prefix}${newIndex}_desc" contenteditable="true" spellcheck="false">Descripción de las instalaciones y recursos pedagógicos...</p>
    `;
    parent.appendChild(newElement);
    CMS_STATE.modifiedItems[`${prefix}${newIndex}_icon`] = "🏫";
    CMS_STATE.modifiedItems[`${prefix}${newIndex}_title`] = "Nuevo Espacio Educativo";
    CMS_STATE.modifiedItems[`${prefix}${newIndex}_desc`] = "Descripción de las instalaciones y recursos pedagógicos...";

  } else if (listType === 'developers') {
    newElement = document.createElement('div');
    newElement.className = 'dev-card reveal-scale';
    newElement.setAttribute('data-cms-item-index', newIndex);
    newElement.id = `devCard-${newIndex}`;
    const defaultAvatar = 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=400&q=80';
    newElement.innerHTML = `
      <button type="button" class="cms-delete-item-btn" title="Eliminar a este desarrollador" aria-label="Eliminar desarrollador">✕</button>

      <div class="dev-avatar-wrapper">
        <div class="dev-avatar-img-box cms-image-wrapper" data-cms-img="${prefix}${newIndex}_photo" title="Haga clic en modo edición para cambiar la fotografía">
          <img src="${defaultAvatar}" alt="Nuevo Desarrollador" class="dev-avatar-img" data-cms-img="${prefix}${newIndex}_photo">
        </div>
        <span class="dev-year-badge cms-modified" data-cms-key="${prefix}${newIndex}_year" contenteditable="true" spellcheck="false" title="Generación / Año">Gen 2026</span>
      </div>

      <div class="dev-info">
        <h3 class="dev-name cms-modified" data-cms-key="${prefix}${newIndex}_name" contenteditable="true" spellcheck="false">Nombre del Desarrollador</h3>
        <span class="dev-role cms-modified" data-cms-key="${prefix}${newIndex}_role" contenteditable="true" spellcheck="false">Rol / Especialidad</span>
        <p class="dev-bio cms-modified" data-cms-key="${prefix}${newIndex}_bio" contenteditable="true" spellcheck="false">Biografía breve o aportes destacados en la plataforma web...</p>

        <div class="dev-social-links">
          <!-- Se actualizarán al presionar Configurar Redes Sociales -->
        </div>

        <div class="dev-admin-links-editor">
          <button type="button" class="btn btn-outline btn-sm dev-edit-links-btn" onclick="openDevLinksModal('${newIndex}', 'Nombre del Desarrollador')">
            🔗 Configurar Redes Sociales
          </button>
          <input type="hidden" data-cms-key="${prefix}${newIndex}_github" id="devGithub-${newIndex}" value="">
          <input type="hidden" data-cms-key="${prefix}${newIndex}_linkedin" id="devLinkedin-${newIndex}" value="">
          <input type="hidden" data-cms-key="${prefix}${newIndex}_instagram" id="devInstagram-${newIndex}" value="">
          <input type="hidden" data-cms-key="${prefix}${newIndex}_email" id="devEmail-${newIndex}" value="">
        </div>
      </div>
    `;
    parent.appendChild(newElement);

    CMS_STATE.modifiedItems[`${prefix}${newIndex}_name`] = "Nombre del Desarrollador";
    CMS_STATE.modifiedItems[`${prefix}${newIndex}_role`] = "Rol / Especialidad";
    CMS_STATE.modifiedItems[`${prefix}${newIndex}_year`] = "Gen 2026";
    CMS_STATE.modifiedItems[`${prefix}${newIndex}_bio`] = "Biografía breve o aportes destacados en la plataforma web...";
    CMS_STATE.modifiedItems[`${prefix}${newIndex}_photo`] = defaultAvatar;
    CMS_STATE.modifiedItems[`${prefix}${newIndex}_github`] = "";
    CMS_STATE.modifiedItems[`${prefix}${newIndex}_linkedin`] = "";
    CMS_STATE.modifiedItems[`${prefix}${newIndex}_instagram`] = "";
    CMS_STATE.modifiedItems[`${prefix}${newIndex}_email`] = "";

    // Habilitar selección de imagen en el nuevo elemento
    const imgWrapper = newElement.querySelector('.cms-image-wrapper');
    if (imgWrapper) {
      imgWrapper.style.cursor = 'pointer';
      imgWrapper.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        const key = imgWrapper.getAttribute('data-cms-img');
        const img = imgWrapper.querySelector('img');
        openImageEditModal(key, img ? img.src : '');
      });
    }
  }

  updateModifiedCounter();
  showToast(`✓ Nuevo elemento añadido (#${newIndex}). Modifíquelo y recuerde guardar cambios.`, 'info');

  if (newElement) {
    const firstEditable = newElement.querySelector('[contenteditable="true"]');
    if (firstEditable) {
      firstEditable.focus();
    }
  }
}

function handleDeleteDynamicItem(itemEl, container, listType, prefix) {
  const isTable = listType === 'curriculum';
  const parent = isTable ? (container.querySelector('tbody') || container) : container;
  const currentItems = isTable ? parent.querySelectorAll('tr[data-cms-item-index]') : parent.querySelectorAll('[data-cms-item-index]');
  const previousCount = currentItems.length;

  itemEl.classList.add('cms-item-removing');
  setTimeout(() => {
    itemEl.remove();
    reindexDynamicList(container, listType, prefix, previousCount);
  }, 220);
}

function reindexDynamicList(container, listType, prefix, previousCount) {
  const isTable = listType === 'curriculum';
  const parent = isTable ? (container.querySelector('tbody') || container) : container;
  const remainingItems = isTable ? parent.querySelectorAll('tr[data-cms-item-index]') : parent.querySelectorAll('[data-cms-item-index]');

  remainingItems.forEach((el, idx) => {
    const newIdx = idx + 1;
    el.setAttribute('data-cms-item-index', newIdx);

    if (listType === 'advantages') {
      const p = el.querySelector('.advantage-text');
      if (p) {
        const oldKey = p.getAttribute('data-cms-key');
        const newKey = `${prefix}${newIdx}`;
        p.setAttribute('data-cms-key', newKey);
        p.classList.add('cms-modified');
        CMS_STATE.modifiedItems[newKey] = p.innerText.trim();
        if (oldKey && oldKey !== newKey && oldKey.startsWith(prefix)) {
          delete CMS_STATE.modifiedItems[oldKey];
        }
      }
    } else if (listType === 'requirements') {
      const numSpan = el.querySelector('.req-number');
      if (numSpan) numSpan.innerText = newIdx;
      const textSpan = el.querySelector('.req-text');
      if (textSpan) {
        const oldKey = textSpan.getAttribute('data-cms-key');
        const newKey = `${prefix}${newIdx}`;
        textSpan.setAttribute('data-cms-key', newKey);
        textSpan.classList.add('cms-modified');
        CMS_STATE.modifiedItems[newKey] = textSpan.innerText.trim();
        if (oldKey && oldKey !== newKey && oldKey.startsWith(prefix)) {
          delete CMS_STATE.modifiedItems[oldKey];
        }
      }
    } else if (listType === 'curriculum') {
      const grpEl = el.querySelector('.curriculum-group-cell strong');
      const subEl = el.querySelector('.curriculum-subject-cell');
      const newGrpKey = `${prefix}group_${newIdx}`;
      const newSubKey = `${prefix}subject_${newIdx}`;
      if (grpEl) {
        const oldGrpKey = grpEl.getAttribute('data-cms-key');
        grpEl.setAttribute('data-cms-key', newGrpKey);
        grpEl.classList.add('cms-modified');
        CMS_STATE.modifiedItems[newGrpKey] = grpEl.innerText.trim();
        if (oldGrpKey && oldGrpKey !== newGrpKey && oldGrpKey.startsWith(prefix)) {
          delete CMS_STATE.modifiedItems[oldGrpKey];
        }
      }
      if (subEl) {
        const oldSubKey = subEl.getAttribute('data-cms-key');
        subEl.setAttribute('data-cms-key', newSubKey);
        subEl.classList.add('cms-modified');
        CMS_STATE.modifiedItems[newSubKey] = subEl.innerText.trim();
        if (oldSubKey && oldSubKey !== newSubKey && oldSubKey.startsWith(prefix)) {
          delete CMS_STATE.modifiedItems[oldSubKey];
        }
      }
    } else if (listType === 'pillars') {
      const numEl = el.querySelector('.pillar-number');
      if (numEl) numEl.innerText = String(newIdx).padStart(2, '0');
      const titleEl = el.querySelector('.pillar-title');
      const descEl = el.querySelector('.pillar-desc');
      const newTitleKey = `${prefix}${newIdx}_title`;
      const newDescKey = `${prefix}${newIdx}_desc`;
      if (titleEl) {
        const oldTitleKey = titleEl.getAttribute('data-cms-key');
        titleEl.setAttribute('data-cms-key', newTitleKey);
        titleEl.classList.add('cms-modified');
        CMS_STATE.modifiedItems[newTitleKey] = titleEl.innerText.trim();
        if (oldTitleKey && oldTitleKey !== newTitleKey && oldTitleKey.startsWith(prefix)) {
          delete CMS_STATE.modifiedItems[oldTitleKey];
        }
      }
      if (descEl) {
        const oldDescKey = descEl.getAttribute('data-cms-key');
        descEl.setAttribute('data-cms-key', newDescKey);
        descEl.classList.add('cms-modified');
        CMS_STATE.modifiedItems[newDescKey] = descEl.innerText.trim();
        if (oldDescKey && oldDescKey !== newDescKey && oldDescKey.startsWith(prefix)) {
          delete CMS_STATE.modifiedItems[oldDescKey];
        }
      }
    } else if (listType === 'features') {
      const textSpan = el.querySelector('span[data-cms-key]');
      if (textSpan) {
        const oldKey = textSpan.getAttribute('data-cms-key');
        const newKey = `${prefix}${newIdx}`;
        textSpan.setAttribute('data-cms-key', newKey);
        textSpan.classList.add('cms-modified');
        CMS_STATE.modifiedItems[newKey] = textSpan.innerText.trim();
        if (oldKey && oldKey !== newKey && oldKey.startsWith(prefix)) {
          delete CMS_STATE.modifiedItems[oldKey];
        }
      }
    } else if (listType === 'campus') {
      const iconEl = el.querySelector('.campus-icon-box');
      const titleEl = el.querySelector('.campus-card-title');
      const descEl = el.querySelector('.campus-card-desc');
      const newIconKey = `${prefix}${newIdx}_icon`;
      const newTitleKey = `${prefix}${newIdx}_title`;
      const newDescKey = `${prefix}${newIdx}_desc`;

      if (iconEl) {
        const oldIconKey = iconEl.getAttribute('data-cms-key');
        iconEl.setAttribute('data-cms-key', newIconKey);
        iconEl.classList.add('cms-modified');
        CMS_STATE.modifiedItems[newIconKey] = iconEl.innerText.trim();
        if (oldIconKey && oldIconKey !== newIconKey && oldIconKey.startsWith(prefix)) {
          delete CMS_STATE.modifiedItems[oldIconKey];
        }
      }
      if (titleEl) {
        const oldTitleKey = titleEl.getAttribute('data-cms-key');
        titleEl.setAttribute('data-cms-key', newTitleKey);
        titleEl.classList.add('cms-modified');
        CMS_STATE.modifiedItems[newTitleKey] = titleEl.innerText.trim();
        if (oldTitleKey && oldTitleKey !== newTitleKey && oldTitleKey.startsWith(prefix)) {
          delete CMS_STATE.modifiedItems[oldTitleKey];
        }
      }
      if (descEl) {
        const oldDescKey = descEl.getAttribute('data-cms-key');
        descEl.setAttribute('data-cms-key', newDescKey);
        descEl.classList.add('cms-modified');
        CMS_STATE.modifiedItems[newDescKey] = descEl.innerText.trim();
        if (oldDescKey && oldDescKey !== newDescKey && oldDescKey.startsWith(prefix)) {
          delete CMS_STATE.modifiedItems[oldDescKey];
        }
      }
    } else if (listType === 'developers') {
      const yearEl = el.querySelector('.dev-year-badge');
      const nameEl = el.querySelector('.dev-name');
      const roleEl = el.querySelector('.dev-role');
      const bioEl = el.querySelector('.dev-bio');
      const photoBox = el.querySelector('.dev-avatar-img-box');
      const photoImg = el.querySelector('.dev-avatar-img');
      const ghInput = el.querySelector(`input[data-cms-key$="_github"]`);
      const liInput = el.querySelector(`input[data-cms-key$="_linkedin"]`);
      const igInput = el.querySelector(`input[data-cms-key$="_instagram"]`);
      const emInput = el.querySelector(`input[data-cms-key$="_email"]`);
      const editLinksBtn = el.querySelector('.dev-edit-links-btn');

      el.id = `devCard-${newIdx}`;
      if (editLinksBtn) {
        editLinksBtn.setAttribute('onclick', `openDevLinksModal('${newIdx}', '${(nameEl?.innerText || 'Desarrollador').replace(/'/g, "\\'")}')`);
      }

      if (yearEl) {
        const oldKey = yearEl.getAttribute('data-cms-key');
        const newKey = `${prefix}${newIdx}_year`;
        yearEl.setAttribute('data-cms-key', newKey);
        yearEl.classList.add('cms-modified');
        CMS_STATE.modifiedItems[newKey] = yearEl.innerText.trim();
        if (oldKey && oldKey !== newKey) delete CMS_STATE.modifiedItems[oldKey];
      }
      if (nameEl) {
        const oldKey = nameEl.getAttribute('data-cms-key');
        const newKey = `${prefix}${newIdx}_name`;
        nameEl.setAttribute('data-cms-key', newKey);
        nameEl.classList.add('cms-modified');
        CMS_STATE.modifiedItems[newKey] = nameEl.innerText.trim();
        if (oldKey && oldKey !== newKey) delete CMS_STATE.modifiedItems[oldKey];
      }
      if (roleEl) {
        const oldKey = roleEl.getAttribute('data-cms-key');
        const newKey = `${prefix}${newIdx}_role`;
        roleEl.setAttribute('data-cms-key', newKey);
        roleEl.classList.add('cms-modified');
        CMS_STATE.modifiedItems[newKey] = roleEl.innerText.trim();
        if (oldKey && oldKey !== newKey) delete CMS_STATE.modifiedItems[oldKey];
      }
      if (bioEl) {
        const oldKey = bioEl.getAttribute('data-cms-key');
        const newKey = `${prefix}${newIdx}_bio`;
        bioEl.setAttribute('data-cms-key', newKey);
        bioEl.classList.add('cms-modified');
        CMS_STATE.modifiedItems[newKey] = bioEl.innerText.trim();
        if (oldKey && oldKey !== newKey) delete CMS_STATE.modifiedItems[oldKey];
      }
      if (photoBox && photoImg) {
        const oldKey = photoBox.getAttribute('data-cms-img');
        const newKey = `${prefix}${newIdx}_photo`;
        photoBox.setAttribute('data-cms-img', newKey);
        photoImg.setAttribute('data-cms-img', newKey);
        CMS_STATE.modifiedItems[newKey] = photoImg.src;
        if (oldKey && oldKey !== newKey) delete CMS_STATE.modifiedItems[oldKey];
      }
      if (ghInput) {
        const oldKey = ghInput.getAttribute('data-cms-key');
        const newKey = `${prefix}${newIdx}_github`;
        ghInput.id = `devGithub-${newIdx}`;
        ghInput.setAttribute('data-cms-key', newKey);
        CMS_STATE.modifiedItems[newKey] = ghInput.value;
        if (oldKey && oldKey !== newKey) delete CMS_STATE.modifiedItems[oldKey];
      }
      if (liInput) {
        const oldKey = liInput.getAttribute('data-cms-key');
        const newKey = `${prefix}${newIdx}_linkedin`;
        liInput.id = `devLinkedin-${newIdx}`;
        liInput.setAttribute('data-cms-key', newKey);
        CMS_STATE.modifiedItems[newKey] = liInput.value;
        if (oldKey && oldKey !== newKey) delete CMS_STATE.modifiedItems[oldKey];
      }
      if (igInput) {
        const oldKey = igInput.getAttribute('data-cms-key');
        const newKey = `${prefix}${newIdx}_instagram`;
        igInput.id = `devInstagram-${newIdx}`;
        igInput.setAttribute('data-cms-key', newKey);
        CMS_STATE.modifiedItems[newKey] = igInput.value;
        if (oldKey && oldKey !== newKey) delete CMS_STATE.modifiedItems[oldKey];
      }
      if (emInput) {
        const oldKey = emInput.getAttribute('data-cms-key');
        const newKey = `${prefix}${newIdx}_email`;
        emInput.id = `devEmail-${newIdx}`;
        emInput.setAttribute('data-cms-key', newKey);
        CMS_STATE.modifiedItems[newKey] = emInput.value;
        if (oldKey && oldKey !== newKey) delete CMS_STATE.modifiedItems[oldKey];
      }
    }
  });

  // Limpiar en la base de datos las claves eliminadas que quedaron fuera del nuevo rango
  for (let idx = remainingItems.length + 1; idx <= previousCount; idx++) {
    if (listType === 'curriculum') {
      CMS_STATE.modifiedItems[`${prefix}group_${idx}`] = '';
      CMS_STATE.modifiedItems[`${prefix}subject_${idx}`] = '';
    } else if (listType === 'pillars') {
      CMS_STATE.modifiedItems[`${prefix}${idx}_title`] = '';
      CMS_STATE.modifiedItems[`${prefix}${idx}_desc`] = '';
    } else if (listType === 'campus') {
      CMS_STATE.modifiedItems[`${prefix}${idx}_icon`] = '';
      CMS_STATE.modifiedItems[`${prefix}${idx}_title`] = '';
      CMS_STATE.modifiedItems[`${prefix}${idx}_desc`] = '';
    } else if (listType === 'developers') {
      CMS_STATE.modifiedItems[`${prefix}${idx}_name`] = '';
      CMS_STATE.modifiedItems[`${prefix}${idx}_role`] = '';
      CMS_STATE.modifiedItems[`${prefix}${idx}_year`] = '';
      CMS_STATE.modifiedItems[`${prefix}${idx}_bio`] = '';
      CMS_STATE.modifiedItems[`${prefix}${idx}_photo`] = '';
      CMS_STATE.modifiedItems[`${prefix}${idx}_github`] = '';
      CMS_STATE.modifiedItems[`${prefix}${idx}_linkedin`] = '';
      CMS_STATE.modifiedItems[`${prefix}${idx}_instagram`] = '';
      CMS_STATE.modifiedItems[`${prefix}${idx}_email`] = '';
    } else {
      CMS_STATE.modifiedItems[`${prefix}${idx}`] = '';
    }
  }

  updateModifiedCounter();
  showToast('🗑️ Elemento eliminado. Presione "💾 Guardar Cambios" para confirmar en la base de datos.', 'info');
}

// Exponer función de adición para botones directos de interfaz
window.handleAddNewDynamicItem = function(listType, prefix) {
  const container = document.querySelector(`[data-cms-list="${listType}"][data-cms-prefix="${prefix}"]`) ||
                    document.querySelector(`[data-cms-list="${listType}"]`);
  if (container) {
    handleAddDynamicItem(container, listType, prefix);
  }
};

/**
 * ============================================================================
 * 10. CONTROL DE VISIBILIDAD DE SECCIONES (OCULTAR / MOSTRAR AL PÚBLICO)
 * ============================================================================
 */
function initVisibilityToggleControls() {
  document.addEventListener('click', (e) => {
    const toggleBtn = e.target.closest('.btn-cms-visibility-toggle');
    if (!toggleBtn) return;
    e.preventDefault();

    const targetKey = toggleBtn.getAttribute('data-cms-visibility-target');
    if (!targetKey) return;

    const currentIsHidden = toggleBtn.getAttribute('data-is-hidden') === 'true';
    const newIsHidden = !currentIsHidden;

    // Actualizar botón
    toggleBtn.setAttribute('data-is-hidden', newIsHidden ? 'true' : 'false');
    const iconSpan = toggleBtn.querySelector('.vis-icon');
    const textSpan = toggleBtn.querySelector('.vis-text');
    if (newIsHidden) {
      toggleBtn.classList.add('btn-cms-visibility-hidden');
      if (iconSpan) iconSpan.innerText = '🚫';
      if (textSpan) textSpan.innerText = 'Oculto al público';
    } else {
      toggleBtn.classList.remove('btn-cms-visibility-hidden');
      if (iconSpan) iconSpan.innerText = '👁️';
      if (textSpan) textSpan.innerText = 'Visible al público';
    }

    // Actualizar elemento contenedor con baja exposición
    const sectionEl = toggleBtn.closest('.cms-toggleable-section') || document.querySelector(`[data-cms-visibility-key="${targetKey}"]`);
    if (sectionEl) {
      if (newIsHidden) {
        sectionEl.classList.add('cms-hidden-exposure');
      } else {
        sectionEl.classList.remove('cms-hidden-exposure');
      }
      const badge = sectionEl.querySelector('.cms-hidden-exposure-badge');
      if (badge) {
        badge.style.display = newIsHidden ? 'inline-flex' : 'none';
      }
    }

    // Caso especial para formulario de contacto: ajustar panel de secretaría
    if (targetKey === 'hide_section_contacto_form') {
      const infoPanel = document.getElementById('contactInfoPanel');
      if (infoPanel) {
        if (newIsHidden) {
          infoPanel.classList.add('contact-info-preview-full');
        } else {
          infoPanel.classList.remove('contact-info-preview-full');
        }
      }
    }

    // Registrar en modificaciones pendientes
    CMS_STATE.modifiedItems[targetKey] = newIsHidden ? 'true' : 'false';
    updateModifiedCounter();

    showToast(
      newIsHidden 
        ? '🚫 Bloque marcado como OCULTO al público (baja exposición activa). Guarde cambios para aplicar.'
        : '👁️ Bloque marcado como VISIBLE al público. Guarde cambios para aplicar.',
      newIsHidden ? 'warning' : 'success'
    );
  });
}

