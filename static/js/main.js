/**
 * ============================================================================
 * LICEO DE LIMÓN MARIO BOURNE BOURNE (MEP)
 * CONTROLADOR PRINCIPAL FRONTEND: ANIMACIONES, PARALLAX Y FILTROS
 * ============================================================================
 * GUÍA RÁPIDA:
 * - Este script maneja la interactividad del sitio público.
 * - initNavbarScroll()    -> Agrega sombra a la barra al bajar la página.
 * - initParallaxHero()     -> Mueve la foto del Hero suavemente con el scroll.
 * - initScrollReveal()     -> Hace aparecer los elementos suavemente al hacer scroll.
 * - initAnimatedCounters() -> Anima los números de estadísticas.
 * - initNewsFilters()      -> Filtra noticias por categoría (IB, Francés, Regular, Institucionales).
 * ============================================================================
 */

document.addEventListener('DOMContentLoaded', () => {
  initThemeToggle();
  initNavbarScroll();
  initParallaxHero();
  initScrollReveal();
  initAnimatedCounters();
  initNewsFilters();
  initNewsModal();
  initCardCarousels();
  initIbNewsFilters();
  initContactForm();
  initMobileMenu();
  initNewsImagePositions();
  initIBInteractiveEffects();
});

function initNewsImagePositions() {
  document.querySelectorAll('.news-image[data-position]').forEach(img => {
    const pos = img.getAttribute('data-position');
    if (pos) img.style.objectPosition = pos;
  });
}

/**
 * 1. Barra de Navegación Sticky con sombra al hacer Scroll
 */
function initNavbarScroll() {
  const header = document.querySelector('.main-header');
  if (!header) return;

  window.addEventListener('scroll', () => {
    if (window.scrollY > 40) {
      header.classList.add('scrolled');
    } else {
      header.classList.remove('scrolled');
    }
  }, { passive: true });
}

/**
 * 2. Efecto Parallax en el Hero Banner
 * Desplaza la imagen de fondo a menor velocidad que el texto para crear profundidad.
 */
function initParallaxHero() {
  const heroSection = document.querySelector('.hero-section');
  const parallaxBg = document.querySelector('.hero-parallax-bg');
  
  if (!heroSection || !parallaxBg) return;

  let ticking = false;

  window.addEventListener('scroll', () => {
    if (!ticking) {
      window.requestAnimationFrame(() => {
        const scrollY = window.pageYOffset;
        const heroHeight = heroSection.offsetHeight;

        if (scrollY <= heroHeight) {
          // Factor de velocidad (0.4x)
          const translateY = scrollY * 0.4;
          parallaxBg.style.transform = `translate3d(0, ${translateY}px, 0)`;
        }
        ticking = false;
      });
      ticking = true;
    }
  }, { passive: true });
}

/**
 * 3. Scroll Reveal mediante IntersectionObserver
 * Revela suavemente las tarjetas y secciones al aparecer en pantalla.
 */
function initScrollReveal() {
  const revealElements = document.querySelectorAll('.reveal, .reveal-left, .reveal-right, .reveal-scale');
  
  if (!revealElements.length) return;

  const observerOptions = {
    root: null,
    rootMargin: '0px 0px 80px 0px',
    threshold: 0.01
  };

  const observer = new IntersectionObserver((entries, obs) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('revealed');
        obs.unobserve(entry.target); // Solo animar la primera vez
      }
    });
  }, observerOptions);

  revealElements.forEach(el => observer.observe(el));
}

/**
 * 4. Contadores Numéricos Animados
 * Cuenta progresivamente de 0 al valor final cuando las estadísticas entran al viewport.
 */
function initAnimatedCounters() {
  const statNumbers = document.querySelectorAll('.stat-number, .counter-num');
  if (!statNumbers.length) return;

  const counterObserver = new IntersectionObserver((entries, obs) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const el = entry.target;
        const targetText = el.getAttribute('data-target') || el.innerText.trim();
        const numericMatch = targetText.match(/\d+/g);

        if (numericMatch) {
          const targetNum = parseInt(numericMatch.join(''), 10);
          const hasPlus = targetText.includes('+');
          const hasPercent = targetText.includes('%');
          
          animateValue(el, 0, targetNum, 1600, hasPlus, hasPercent);
        }
        obs.unobserve(el);
      }
    });
  }, { threshold: 0.5 });

  statNumbers.forEach(num => counterObserver.observe(num));
}

function animateValue(obj, start, end, duration, hasPlus, hasPercent) {
  let startTimestamp = null;
  const step = (timestamp) => {
    if (!startTimestamp) startTimestamp = timestamp;
    const progress = Math.min((timestamp - startTimestamp) / duration, 1);
    // Suavizado cúbico
    const easeProgress = 1 - Math.pow(1 - progress, 3);
    const currentVal = Math.floor(easeProgress * (end - start) + start);
    
    let formatted = currentVal.toLocaleString('es-CR');
    if (hasPlus) formatted += '+';
    if (hasPercent) formatted += '%';
    
    obj.innerText = formatted;
    if (progress < 1) {
      window.requestAnimationFrame(step);
    }
  };
  window.requestAnimationFrame(step);
}

/**
 * 5. Filtros Jerárquicos por Categoría y Subcategoría de Noticias
 * Permite filtrar comunicados por 'Todas', 'ib', 'frances', 'regular' o 'institucionales'.
 * Inicialmente ninguna categoría está seleccionada para evitar saturación visual.
 * Al presionar una categoría se despliegan sus comunicados con animación escalonada.
 * Si se presiona nuevamente la categoría activa, se pliegan de nuevo.
 */
function initNewsFilters() {
  const filterBtns = document.querySelectorAll('.news-tab-btn');
  const newsCards = document.querySelectorAll('.news-card');
  const subfilterWrapper = document.getElementById('newsSubfilterContainer');
  const initialState = document.getElementById('newsInitialState');

  if (!filterBtns.length || !newsCards.length) return;

  // Inicialmente ninguna categoría está seleccionada
  let currentCategory = null;
  let currentSubcategory = 'all';

  // Comprobar si hay una categoría o subcategoría activa por defecto (ej. en Modo Exclusivo IB)
  const initiallyActive = document.querySelector('.news-tab-btn.active');
  if (initiallyActive) {
    currentCategory = initiallyActive.getAttribute('data-filter') || 'ib';
    currentSubcategory = initiallyActive.getAttribute('data-subfilter') || 'all';
    applyFilters();
    if (!initiallyActive.hasAttribute('data-subfilter')) {
      renderSubcategoriesForCategory(currentCategory);
    }
  } else {
    // Ocultar todas las noticias al arrancar la página
    newsCards.forEach(card => {
      card.style.display = 'none';
      card.classList.remove('news-card-deploying');
    });

    if (initialState) {
      initialState.style.display = 'flex';
    }
  }

  function applyFilters() {
    if (!currentCategory) {
      // Sin categoría activa: ocultar comunicados y mostrar estado inicial
      newsCards.forEach(card => {
        card.style.display = 'none';
        card.classList.remove('news-card-deploying');
      });
      if (initialState) {
        initialState.style.display = 'flex';
      }
      if (subfilterWrapper) {
        subfilterWrapper.style.display = 'none';
        subfilterWrapper.innerHTML = '';
      }
      return;
    }

    if (initialState) {
      initialState.style.display = 'none';
    }

    let matchCount = 0;
    newsCards.forEach(card => {
      const cardCategory = card.getAttribute('data-category');
      const cardSubcategory = (card.getAttribute('data-subcategory') || '').trim();

      const matchesCategory = (currentCategory === 'all' || cardCategory === currentCategory);
      const matchesSubcategory = (currentSubcategory === 'all' || cardSubcategory.toLowerCase() === currentSubcategory.toLowerCase());

      if (matchesCategory && matchesSubcategory) {
        card.style.display = 'flex';
        // Reiniciar animación con delay escalonado para efecto cascada
        card.classList.remove('news-card-deploying');
        void card.offsetWidth; // Forzar reflow
        card.style.animationDelay = `${matchCount * 65}ms`;
        card.classList.add('news-card-deploying');
        matchCount++;
      } else {
        card.style.display = 'none';
        card.classList.remove('news-card-deploying');
      }
    });
    if (typeof initCardCarousels === 'function') {
      setTimeout(initCardCarousels, 60);
    }
  }

  function renderSubcategoriesForCategory(category) {
    if (!subfilterWrapper) return;

    if (!category || category === 'all') {
      subfilterWrapper.style.display = 'none';
      subfilterWrapper.innerHTML = '';
      return;
    }

    // Extraer subcategorías únicas presentes en las noticias de esta categoría
    const subcats = new Set();
    newsCards.forEach(card => {
      if (card.getAttribute('data-category') === category) {
        const sub = (card.getAttribute('data-subcategory') || '').trim();
        if (sub) {
          // La subcategoría de Instagram / Redes Sociales es estrictamente exclusiva del Bachillerato Internacional (IB)
          if (category !== 'ib' && (sub.toLowerCase() === 'instagram' || sub.toLowerCase().includes('redes'))) {
            return;
          }
          subcats.add(sub);
        }
      }
    });

    if (subcats.size === 0) {
      subfilterWrapper.style.display = 'none';
      subfilterWrapper.innerHTML = '';
      return;
    }

    // Generar botones de subcategoría
    let html = `<span class="news-subfilter-label">Subcategorías:</span>`;
    html += `<button class="news-subtab-btn active" data-subfilter="all">Todas (${category.toUpperCase()})</button>`;
    
    subcats.forEach(sub => {
      let label = sub;
      if (sub.toLowerCase() === 'instagram' || sub.toLowerCase().includes('redes')) {
        label = '📸 Instagram';
      }
      html += `<button class="news-subtab-btn" data-subfilter="${sub}">${label}</button>`;
    });

    subfilterWrapper.innerHTML = html;
    subfilterWrapper.style.display = 'flex';

    // Añadir listeners a los nuevos botones de subfiltro
    subfilterWrapper.querySelectorAll('.news-subtab-btn').forEach(subBtn => {
      subBtn.addEventListener('click', () => {
        subfilterWrapper.querySelectorAll('.news-subtab-btn').forEach(b => b.classList.remove('active'));
        subBtn.classList.add('active');

        currentSubcategory = subBtn.getAttribute('data-subfilter');
        applyFilters();
      });
    });
  }

  filterBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const filterValue = btn.getAttribute('data-filter') || 'ib';
      const subVal = btn.getAttribute('data-subfilter');

      // Si se hace clic en la categoría que ya estaba activa, se deselecciona (toggle para plegar)
      if (btn.classList.contains('active')) {
        btn.classList.remove('active');
        currentCategory = null;
        currentSubcategory = 'all';
        renderSubcategoriesForCategory(null);
        applyFilters();
        return;
      }

      // Si se selecciona una nueva categoría o subcategoría directa
      filterBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');

      currentCategory = filterValue;
      if (subVal) {
        currentSubcategory = subVal;
        if (subfilterWrapper) subfilterWrapper.style.display = 'none';
      } else {
        currentSubcategory = 'all';
        renderSubcategoriesForCategory(currentCategory);
      }

      applyFilters();
    });
  });
}

/**
 * Parsea y formatea enlaces multimedia (Google Drive, YouTube, Vimeo, Instagram, Facebook, MP4 directo)
 */
function parseMediaVideoUrl(url) {
  if (!url || typeof url !== 'string') return null;
  url = url.trim();
  if (!url) return null;

  // 1. Google Drive (Compartir enlace: /file/d/ID/view o id=ID)
  const driveMatch = url.match(/(?:drive\.google\.com\/(?:file\/d\/|open\?id=)|lh3\.googleusercontent\.com\/d\/)([a-zA-Z0-9_-]{20,})/);
  if (driveMatch) {
    const fileId = driveMatch[1];
    return {
      type: 'drive',
      embedUrl: `https://drive.google.com/file/d/${fileId}/preview`,
      original: url
    };
  }

  // 2. YouTube (Enlaces normales, youtu.be, shorts o embed)
  const ytMatch = url.match(/(?:youtube\.com\/(?:watch\?v=|embed\/|shorts\/)|youtu\.be\/)([a-zA-Z0-9_-]{11})/);
  if (ytMatch) {
    const videoId = ytMatch[1];
    return {
      type: 'youtube',
      videoId: videoId,
      embedUrl: `https://www.youtube-nocookie.com/embed/${videoId}?rel=0`,
      original: url
    };
  }

  // 3. Instagram (Reels, publicaciones de video, IGTV)
  const igMatch = url.match(/instagram\.com\/(?:p|reel|tv)\/([a-zA-Z0-9_-]+)/);
  if (igMatch) {
    const shortcode = igMatch[1];
    return {
      type: 'instagram',
      shortcode: shortcode,
      embedUrl: `https://www.instagram.com/p/${shortcode}/embed/captioned/`,
      original: url
    };
  }

  // 4. Vimeo
  const vimeoMatch = url.match(/vimeo\.com\/(?:video\/)?(\d+)/);
  if (vimeoMatch) {
    const vimeoId = vimeoMatch[1];
    return {
      type: 'vimeo',
      embedUrl: `https://player.vimeo.com/video/${vimeoId}`,
      original: url
    };
  }

  // 5. Facebook Video
  if (url.includes('facebook.com') || url.includes('fb.watch')) {
    return {
      type: 'facebook',
      embedUrl: `https://www.facebook.com/plugins/video.php?href=${encodeURIComponent(url)}&show_text=false`,
      original: url
    };
  }

  // 6. Archivo directo MP4 / WebM / OGG / MOV (incluyendo CDN de Curator u otros)
  if (/\.(mp4|webm|ogg|mov)(\?.*)?$/i.test(url) || url.includes('.mp4') || url.includes('.webm')) {
    return {
      type: 'direct',
      videoUrl: url,
      original: url
    };
  }

  // 7. Enlace web genérico
  if (url.startsWith('https://') || url.startsWith('http://')) {
    return {
      type: 'generic',
      embedUrl: url,
      original: url
    };
  }

  return null;
}

/**
 * 6. Modal para Lectura de Noticias Completas y Reproducción de Videos
 */
function initNewsModal() {
  const modal = document.getElementById('newsDetailModal');
  if (!modal) return;

  const modalVideo = document.getElementById('modalNewsVideoContainer');
  const modalGallery = document.getElementById('modalNewsGalleryContainer');
  const modalGalleryImg = document.getElementById('modalNewsGalleryImage');
  const modalGalleryCounter = document.getElementById('modalGalleryCounter');
  const modalGalleryDots = document.getElementById('modalGalleryDots');
  const prevBtn = document.getElementById('modalGalleryPrevBtn');
  const nextBtn = document.getElementById('modalGalleryNextBtn');
  const mediaSwitcher = document.getElementById('modalMediaSwitcher');
  const btnShowGallery = document.getElementById('btnShowGallery');
  const btnShowVideo = document.getElementById('btnShowVideo');
  const modalGalleryTotal = document.getElementById('modalGalleryTotal');
  const modalTitle = document.getElementById('modalNewsTitle');
  const modalDate = document.getElementById('modalNewsDate');
  const modalAuthor = document.getElementById('modalNewsAuthor');
  const modalBody = document.getElementById('modalNewsBody');

  let activeModalGallery = null;
  let currentParsedVideo = null;

  function stopModalVideo() {
    if (!modalVideo) return;
    const vid = modalVideo.querySelector('video');
    if (vid) {
      vid.pause();
      vid.removeAttribute('src');
      vid.load();
    }
    modalVideo.innerHTML = '';
    modalVideo.style.display = 'none';
    modalVideo.classList.remove('is-iframe-video', 'is-ig-embed');
  }

  function renderModalVideo(parsed, autoplay = true) {
    if (!modalVideo || !parsed) return;
    stopModalVideo();

    if (parsed.type === 'direct') {
      modalVideo.classList.remove('is-iframe-video', 'is-ig-embed');
      modalVideo.innerHTML = `
        <video controls ${autoplay ? 'autoplay' : ''} playsinline preload="metadata" style="width:100%; height:100%; max-height:520px; object-fit:contain; background:#000; border-radius: var(--radius-xl) var(--radius-xl) 0 0; display:block;">
          <source src="${parsed.videoUrl}">
          Su navegador no soporta reproducción de video HTML5.
        </video>
      `;
    } else if (parsed.type === 'instagram') {
      modalVideo.classList.remove('is-iframe-video');
      modalVideo.classList.add('is-ig-embed');
      modalVideo.innerHTML = `
        <iframe src="${parsed.embedUrl}"
                allow="autoplay; fullscreen; picture-in-picture; encrypted-media" 
                allowfullscreen
                style="width:100%; height:540px; border:none; background:#000;">
        </iframe>
      `;
    } else {
      modalVideo.classList.add('is-iframe-video');
      modalVideo.classList.remove('is-ig-embed');
      let embedSrc = parsed.embedUrl;
      if (autoplay && embedSrc.indexOf('autoplay=') === -1) {
        embedSrc += (embedSrc.indexOf('?') === -1 ? '?' : '&') + 'autoplay=1';
      }
      modalVideo.innerHTML = `
        <iframe src="${embedSrc}" 
                allow="autoplay; fullscreen; picture-in-picture; accelerometer; clipboard-write; encrypted-media; gyroscope" 
                allowfullscreen
                style="position:absolute; top:0; left:0; width:100%; height:100%; border:none; background:#000;">
        </iframe>
      `;
    }
    modalVideo.style.display = 'block';
  }

  function openNewsModal(card, defaultTab = null) {
    if (!card) return;

    // 1. Detener inmediatamente cualquier video que se esté reproduciendo en tarjetas
    document.querySelectorAll('.news-card.is-playing-video').forEach(c => stopVideoInCard(c));

    // 2. Extraer datos del comunicado
    const title = card.querySelector('.news-title')?.innerText.trim() || 'Comunicado Oficial';
    const date = card.querySelector('.news-meta-date')?.innerText.trim() || '';
    const author = card.querySelector('.news-meta-author')?.innerText.trim() || 'Liceo de Limón MEP';
    const videoUrl = card.getAttribute('data-video-url') || '';
    const socialUrl = card.getAttribute('data-social-url') || '';

    // Contenido
    const fullContentElem = card.querySelector('.news-full-content');
    const rawContent = (fullContentElem ? fullContentElem.innerText : card.getAttribute('data-content')) || card.querySelector('.news-summary')?.innerText.trim() || '';

    // Galería de fotos
    let galleryImages = [];
    const galleryScript = card.querySelector('.news-gallery-json');
    if (galleryScript && galleryScript.textContent) {
      try {
        const parsed = JSON.parse(galleryScript.textContent);
        if (Array.isArray(parsed) && parsed.length > 0) {
          galleryImages = parsed.filter(Boolean);
        }
      } catch (e) {}
    }
    if (galleryImages.length === 0) {
      const rawGallery = card.getAttribute('data-gallery');
      if (rawGallery) {
        try {
          const parsed = JSON.parse(rawGallery);
          if (Array.isArray(parsed) && parsed.length > 0) {
            galleryImages = parsed.filter(Boolean);
          }
        } catch (e) {}
      }
    }

    // Imagen de respaldo si no hay fotos en galería
    const imgEl = card.querySelector('.news-image');
    const fallbackImg = imgEl ? imgEl.getAttribute('src') : '';
    if (galleryImages.length === 0 && fallbackImg) {
      galleryImages = [fallbackImg];
    }

    currentParsedVideo = parseMediaVideoUrl(videoUrl);

    const hasVideo = !!currentParsedVideo;
    const hasMultiplePhotos = galleryImages.length > 1;
    const hasAnyPhotos = galleryImages.length > 0;

    // 3. Sincronizar índice inicial del carrusel con la tarjeta
    let cardIdx = parseInt(card.dataset.carouselIdx, 10);
    if (isNaN(cardIdx) || cardIdx < 0 || cardIdx >= galleryImages.length) {
      cardIdx = 0;
    }
    let currentGalleryIdx = cardIdx;

    // 4. Controlador de actualización visual del carrusel en el modal
    const updateGalleryView = (newIdx) => {
      if (galleryImages.length === 0) return;
      currentGalleryIdx = (newIdx + galleryImages.length) % galleryImages.length;
      card.dataset.carouselIdx = currentGalleryIdx;

      if (modalGalleryImg) {
        modalGalleryImg.style.opacity = '0';
        const imgObj = new Image();
        imgObj.src = galleryImages[currentGalleryIdx];
        imgObj.onload = () => {
          modalGalleryImg.src = galleryImages[currentGalleryIdx];
          modalGalleryImg.style.opacity = '1';
        };
        imgObj.onerror = () => {
          modalGalleryImg.src = galleryImages[currentGalleryIdx];
          modalGalleryImg.style.opacity = '1';
        };
        if (imgObj.complete) {
          modalGalleryImg.src = galleryImages[currentGalleryIdx];
          modalGalleryImg.style.opacity = '1';
        }
      }

      if (modalGalleryCounter) {
        modalGalleryCounter.innerText = `${currentGalleryIdx + 1} / ${galleryImages.length}`;
      }

      if (modalGalleryDots) {
        const dots = modalGalleryDots.querySelectorAll('.gallery-dot');
        dots.forEach((dot, idx) => {
          dot.classList.toggle('active', idx === currentGalleryIdx);
        });
      }

      // Precargar imágenes adyacentes para una transición instantánea
      if (galleryImages.length > 1) {
        const nextImg = new Image();
        nextImg.src = galleryImages[(currentGalleryIdx + 1) % galleryImages.length];
        const prevImg = new Image();
        prevImg.src = galleryImages[(currentGalleryIdx - 1 + galleryImages.length) % galleryImages.length];
      }
    };

    // 5. Configurar botones y controles de la galería
    if (hasMultiplePhotos) {
      if (prevBtn) prevBtn.style.display = 'flex';
      if (nextBtn) nextBtn.style.display = 'flex';
      if (modalGalleryCounter) modalGalleryCounter.style.display = 'block';

      if (modalGalleryDots) {
        modalGalleryDots.innerHTML = '';
        if (galleryImages.length <= 15) {
          modalGalleryDots.style.display = 'flex';
          galleryImages.forEach((_, idx) => {
            const dot = document.createElement('button');
            dot.type = 'button';
            dot.className = `gallery-dot ${idx === currentGalleryIdx ? 'active' : ''}`;
            dot.setAttribute('aria-label', `Ir a foto ${idx + 1}`);
            dot.onclick = (ev) => {
              ev.stopPropagation();
              updateGalleryView(idx);
            };
            modalGalleryDots.appendChild(dot);
          });
        } else {
          modalGalleryDots.style.display = 'none';
        }
      }

      if (prevBtn) {
        prevBtn.onclick = (ev) => {
          ev.stopPropagation();
          updateGalleryView(currentGalleryIdx - 1);
        };
      }
      if (nextBtn) {
        nextBtn.onclick = (ev) => {
          ev.stopPropagation();
          updateGalleryView(currentGalleryIdx + 1);
        };
      }

      activeModalGallery = {
        next: () => updateGalleryView(currentGalleryIdx + 1),
        prev: () => updateGalleryView(currentGalleryIdx - 1)
      };
    } else {
      if (prevBtn) prevBtn.style.display = 'none';
      if (nextBtn) nextBtn.style.display = 'none';
      if (modalGalleryCounter) modalGalleryCounter.style.display = 'none';
      if (modalGalleryDots) modalGalleryDots.style.display = 'none';
      activeModalGallery = null;
    }

    if (hasAnyPhotos) {
      updateGalleryView(currentGalleryIdx);
    }

    // 6. Gestionar Selector de Medios (Coexistencia de Video y Fotos)
    const showGalleryTab = () => {
      stopModalVideo();
      if (modalGallery) modalGallery.style.display = 'flex';
      if (btnShowGallery) btnShowGallery.className = 'btn btn-sm btn-azul';
      if (btnShowVideo) btnShowVideo.className = 'btn btn-sm btn-outline';
    };

    const showVideoTab = () => {
      if (modalGallery) modalGallery.style.display = 'none';
      renderModalVideo(currentParsedVideo, true);
      if (btnShowVideo) btnShowVideo.className = 'btn btn-sm btn-azul';
      if (btnShowGallery) btnShowGallery.className = 'btn btn-sm btn-outline';
    };

    if (hasVideo && hasAnyPhotos) {
      if (mediaSwitcher) {
        mediaSwitcher.style.display = 'flex';
        if (modalGalleryTotal) modalGalleryTotal.innerText = galleryImages.length;
        if (btnShowGallery) btnShowGallery.onclick = showGalleryTab;
        if (btnShowVideo) btnShowVideo.onclick = showVideoTab;
      }

      if (defaultTab === 'video') {
        showVideoTab();
      } else {
        showGalleryTab();
      }
    } else if (hasVideo) {
      if (mediaSwitcher) mediaSwitcher.style.display = 'none';
      if (modalGallery) modalGallery.style.display = 'none';
      renderModalVideo(currentParsedVideo, true);
    } else if (hasAnyPhotos) {
      if (mediaSwitcher) mediaSwitcher.style.display = 'none';
      stopModalVideo();
      if (modalGallery) modalGallery.style.display = 'flex';
    } else {
      if (mediaSwitcher) mediaSwitcher.style.display = 'none';
      stopModalVideo();
      if (modalGallery) modalGallery.style.display = 'none';
    }

    // 7. Llenar textos y contenido de la noticia
    if (modalTitle) modalTitle.innerText = title;
    if (modalDate) modalDate.innerText = date;
    if (modalAuthor) modalAuthor.innerText = author;

    if (modalBody) {
      let bodyHtml = rawContent
        .split(/\n{2,}/)
        .filter(p => p.trim())
        .map(p => `<p style="margin-bottom: 1.15rem; line-height: 1.8; color: var(--gris-700); font-size: 1.02rem;">${p.trim().replace(/\n/g, '<br>')}</p>`)
        .join('');

      if (!bodyHtml.trim()) {
        bodyHtml = `<p style="margin-bottom: 1.15rem; line-height: 1.8; color: var(--gris-700); font-size: 1.02rem;">${title}</p>`;
      }

      if (socialUrl) {
        const isIg = socialUrl.includes('instagram.com');
        const isFb = socialUrl.includes('facebook.com');
        const btnText = isIg ? '📸 Ver Publicación Oficial en Instagram' : (isFb ? '👥 Ver Publicación Oficial en Facebook' : '🔗 Ver Publicación en Red Social');
        const btnClass = isIg ? 'link-ig' : 'link-fb';
        bodyHtml += `
          <div style="margin-top: 1.8rem; padding-top: 1.2rem; border-top: 1px solid var(--gris-200); display: flex; justify-content: flex-start;">
            <a href="${socialUrl}" target="_blank" rel="noopener noreferrer" class="btn-news-social-link ${btnClass}" style="font-size: 0.92rem; padding: 0.6rem 1.3rem;">
              <span>${btnText}</span> ↗
            </a>
          </div>
        `;
      }

      modalBody.innerHTML = bodyHtml;
    }

    // 8. Desplegar el modal con animación suave
    modal.style.display = 'flex';
    void modal.offsetWidth;
    modal.classList.add('active');
    document.body.style.overflow = 'hidden';
  }

  function closeNewsModal() {
    modal.classList.remove('active');
    document.body.style.overflow = '';
    stopModalVideo();
    activeModalGallery = null;

    setTimeout(() => {
      if (!modal.classList.contains('active')) {
        modal.style.display = 'none';
      }
    }, 300);
  }

  // Reproducción instantánea directa dentro de la tarjeta (inline)
  function playVideoInCard(card) {
    if (!card) return;
    const videoUrl = card.getAttribute('data-video-url');
    if (!videoUrl) {
      openNewsModal(card);
      return;
    }

    const container = card.querySelector('.news-image-container');
    if (!container) return;

    if (container.querySelector('.inline-video-frame')) return;

    const parsed = parseMediaVideoUrl(videoUrl);
    if (!parsed) {
      openNewsModal(card);
      return;
    }

    document.querySelectorAll('.news-card.is-playing-video').forEach(c => {
      if (c !== card) stopVideoInCard(c);
    });

    if (!container.dataset.originalHtml) {
      container.dataset.originalHtml = container.innerHTML;
    }

    let videoMarkup = '';
    if (parsed.type === 'direct') {
      videoMarkup = `
        <video class="inline-video-frame" controls autoplay playsinline style="width:100%; height:100%; object-fit:contain; background:#000;">
          <source src="${parsed.videoUrl}">
          Su navegador no soporta reproducción de video.
        </video>
      `;
    } else {
      let embedSrc = parsed.embedUrl;
      if (embedSrc.indexOf('autoplay=') === -1) {
        embedSrc += (embedSrc.indexOf('?') === -1 ? '?' : '&') + 'autoplay=1';
      }
      videoMarkup = `
        <iframe class="inline-video-frame" 
                src="${embedSrc}" 
                allow="autoplay; fullscreen; picture-in-picture; accelerometer; clipboard-write; encrypted-media; gyroscope" 
                allowfullscreen
                style="width:100%; height:100%; border:none; background:#000;">
        </iframe>
      `;
    }

    card.classList.add('is-playing-video');
    container.innerHTML = `
      ${videoMarkup}
      <button type="button" class="btn-close-inline-video" title="Detener video y restaurar imagen" aria-label="Cerrar video">
        ✕
      </button>
    `;

    const closeBtn = container.querySelector('.btn-close-inline-video');
    closeBtn?.addEventListener('click', (ev) => {
      ev.preventDefault();
      ev.stopPropagation();
      stopVideoInCard(card);
    });
  }

  function stopVideoInCard(card) {
    if (!card) return;
    const container = card.querySelector('.news-image-container');
    if (container && container.dataset.originalHtml) {
      container.innerHTML = container.dataset.originalHtml;
    }
    card.classList.remove('is-playing-video');
  }

  // Delegación de eventos para clics en tarjetas, videos, carruseles y lectura
  document.addEventListener('click', (e) => {
    // 1. Clic directo en la insignia '▶ Video' o en el botón flotante de Play
    const videoTrigger = e.target.closest('.news-video-badge, .news-play-btn');
    if (videoTrigger) {
      e.preventDefault();
      e.stopPropagation();
      const card = videoTrigger.closest('.news-card');
      openNewsModal(card, 'video');
      return;
    }

    // 2. Clic en las flechas del carrusel en la tarjeta (Feed)
    if (e.target.closest('.card-gallery-nav-btn')) {
      return;
    }

    // 3. Clic en el botón para cerrar video inline en tarjeta
    if (e.target.closest('.btn-close-inline-video')) {
      return;
    }

    // 4. Clic en el contenedor de imagen de la noticia -> abre modal
    const imgContainer = e.target.closest('.news-image-container');
    if (imgContainer) {
      const card = imgContainer.closest('.news-card');
      if (card) {
        e.preventDefault();
        openNewsModal(card);
        return;
      }
    }

    // 5. Clic en 'Leer Comunicado Completo' o en el título de la noticia
    const readBtn = e.target.closest('.btn-read-more');
    const titleLink = e.target.closest('.news-title');
    if (readBtn || titleLink) {
      e.preventDefault();
      const card = (readBtn || titleLink).closest('.news-card');
      openNewsModal(card);
      return;
    }

    // 6. Botón de cerrar o clic en el fondo oscuro del modal
    if (e.target === modal || e.target.closest('#closeNewsModalBtn')) {
      e.preventDefault();
      closeNewsModal();
    }
  });

  // Cerrar con Escape y navegación con teclas de flecha
  document.addEventListener('keydown', (e) => {
    if (modal.classList.contains('active')) {
      if (e.key === 'Escape') {
        closeNewsModal();
      } else if ((e.key === 'ArrowRight' || e.key === 'Right') && activeModalGallery) {
        activeModalGallery.next();
      } else if ((e.key === 'ArrowLeft' || e.key === 'Left') && activeModalGallery) {
        activeModalGallery.prev();
      }
    }
  });

  // Gestos táctiles de deslizamiento (Swipe) en móvil para el carrusel del modal
  let touchStartX = 0;
  if (modalGallery) {
    modalGallery.addEventListener('touchstart', (e) => {
      touchStartX = e.changedTouches[0].screenX;
    }, { passive: true });
    modalGallery.addEventListener('touchend', (e) => {
      const touchEndX = e.changedTouches[0].screenX;
      const diff = touchStartX - touchEndX;
      if (Math.abs(diff) > 40 && activeModalGallery) {
        if (diff > 0) {
          activeModalGallery.next();
        } else {
          activeModalGallery.prev();
        }
      }
    }, { passive: true });
  }
}

/**
 * 6.0 Carrusel de Fotos Directo en las Tarjetas de Noticias (Feed)
 */
function initCardCarousels() {
  document.addEventListener('click', (e) => {
    const prevBtn = e.target.closest('.card-gallery-prev');
    const nextBtn = e.target.closest('.card-gallery-next');
    if (!prevBtn && !nextBtn) return;

    e.preventDefault();
    e.stopPropagation();
    const card = (prevBtn || nextBtn).closest('.news-card');
    if (!card) return;

    let images = [];
    const galleryScript = card.querySelector('.news-gallery-json');
    if (galleryScript && galleryScript.textContent) {
      try {
        const parsed = JSON.parse(galleryScript.textContent);
        if (Array.isArray(parsed) && parsed.length > 0) images = parsed.filter(Boolean);
      } catch (err) {}
    }
    if (images.length === 0) {
      const rawGallery = card.getAttribute('data-gallery');
      if (rawGallery) {
        try {
          const parsed = JSON.parse(rawGallery);
          if (Array.isArray(parsed) && parsed.length > 0) images = parsed.filter(Boolean);
        } catch (err) {}
      }
    }
    if (images.length <= 1) return;

    let currentIdx = parseInt(card.dataset.carouselIdx, 10);
    if (isNaN(currentIdx)) currentIdx = 0;

    const delta = prevBtn ? -1 : 1;
    currentIdx = (currentIdx + delta + images.length) % images.length;
    card.dataset.carouselIdx = currentIdx;

    const imgElem = card.querySelector('.news-image');
    const counterElem = card.querySelector('.card-gallery-counter');

    if (imgElem) {
      imgElem.style.opacity = '0.35';
      const imgObj = new Image();
      imgObj.src = images[currentIdx];
      imgObj.onload = () => {
        imgElem.src = images[currentIdx];
        imgElem.style.opacity = '1';
      };
      imgObj.onerror = () => {
        imgElem.src = images[currentIdx];
        imgElem.style.opacity = '1';
      };
      if (imgObj.complete) {
        imgElem.src = images[currentIdx];
        imgElem.style.opacity = '1';
      }
    }

    if (counterElem) {
      counterElem.innerText = `${currentIdx + 1} / ${images.length}`;
    }
  });

  // Inicializar contadores iniciales en las tarjetas
  document.querySelectorAll('.news-card').forEach(card => {
    let images = [];
    const galleryScript = card.querySelector('.news-gallery-json');
    if (galleryScript && galleryScript.textContent) {
      try {
        const parsed = JSON.parse(galleryScript.textContent);
        if (Array.isArray(parsed)) images = parsed.filter(Boolean);
      } catch (err) {}
    }
    if (images.length === 0) {
      const rawGallery = card.getAttribute('data-gallery');
      if (rawGallery) {
        try {
          const parsed = JSON.parse(rawGallery);
          if (Array.isArray(parsed)) images = parsed.filter(Boolean);
        } catch (err) {}
      }
    }
    if (images.length > 1) {
      const counterElem = card.querySelector('.card-gallery-counter');
      if (counterElem) {
        counterElem.innerText = `1 / ${images.length}`;
      }
      card.dataset.carouselIdx = '0';
    }
  });
}

/**
 * 6.1 Filtros Dinámicos para Noticias IB en /modalidad/ib
 */
function initIbNewsFilters() {
  const container = document.getElementById('ibNewsGridContainer');
  if (!container) return;

  const subfilterBtns = document.querySelectorAll('.ib-subfilter-btn');
  const cards = container.querySelectorAll('.news-card');

  // Asegurar que las tarjetas iniciales de noticias IB sean completamente visibles
  cards.forEach(card => {
    card.classList.add('revealed');
  });

  subfilterBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      subfilterBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');

      const filter = (btn.getAttribute('data-subfilter') || 'all').toLowerCase().trim();

      cards.forEach(card => {
        const subcat = (card.getAttribute('data-subcategory') || '').toLowerCase().trim();
        const hasSocial = Boolean(card.querySelector('.btn-news-social-link') || card.getAttribute('data-social-url'));
        if (filter === 'all' || subcat.includes(filter) || (filter === 'redes sociales' && (subcat.includes('redes') || hasSocial)) || (filter === 'instagram' && (subcat.includes('insta') || hasSocial)) || (filter === 'general' && !subcat)) {
          card.style.display = 'flex';
          card.classList.add('revealed');
        } else {
          card.style.display = 'none';
        }
      });
      if (typeof initCardCarousels === 'function') {
        setTimeout(initCardCarousels, 60);
      }
    });
  });
}

/**
 * 7. Formulario de Contacto / Admisión (Envío a Base de Datos)
 */
function initContactForm() {
  const form = document.getElementById('institutionalContactForm');
  if (!form) return;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const name = document.getElementById('contactName')?.value.trim() || '';
    const email = document.getElementById('contactEmail')?.value.trim() || '';
    const phone = document.getElementById('contactPhone')?.value.trim() || '';
    const areaSelect = document.getElementById('contactArea');
    const area = areaSelect ? areaSelect.options[areaSelect.selectedIndex].text : 'General';
    const message = document.getElementById('contactMessage')?.value.trim() || '';

    const submitBtn = form.querySelector('button[type="submit"]');
    const originalText = submitBtn.innerHTML;

    submitBtn.innerHTML = '<span>Enviando consulta al Liceo...</span>';
    submitBtn.disabled = true;

    try {
      const res = await fetch('/api/contact/submit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, email, phone, area, message })
      });

      const data = await res.json();

      if (res.ok && data.success) {
        submitBtn.innerHTML = '✓ ¡Consulta Enviada con Éxito!';
        submitBtn.style.background = '#10b981';
        alert('✓ Su consulta ha sido enviada con éxito a la secretaría del Liceo de Limón (MEP). El personal administrativo la revisará en el panel.');
        form.reset();
      } else {
        alert('Error al enviar consulta: ' + (data.message || 'Intente nuevamente'));
      }
    } catch (err) {
      alert('Error de conexión al enviar consulta.');
    } finally {
      setTimeout(() => {
        submitBtn.innerHTML = originalText;
        submitBtn.style.background = '';
        submitBtn.disabled = false;
      }, 3000);
    }
  });
}

/**
 * 8. Menú Móvil Hamburguesa (Responsive Drawer)
 */
function initMobileMenu() {
  const toggleBtn = document.getElementById('mobileNavToggle');
  const navMenu = document.getElementById('navMenu') || document.querySelector('.nav-menu');
  if (!toggleBtn || !navMenu) return;

  const toggle = (forceClose = false) => {
    const shouldOpen = forceClose ? false : !navMenu.classList.contains('mobile-open');
    navMenu.classList.toggle('mobile-open', shouldOpen);
    toggleBtn.classList.toggle('active', shouldOpen);
    toggleBtn.setAttribute('aria-expanded', shouldOpen ? 'true' : 'false');
    document.body.classList.toggle('mobile-menu-open', shouldOpen);
  };

  toggleBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    toggle();
  });

  // Cerrar al hacer clic en enlaces del menú
  navMenu.querySelectorAll('.nav-link, .btn').forEach(link => {
    link.addEventListener('click', () => {
      toggle(true);
    });
  });

  // Cerrar al hacer clic fuera del menú
  document.addEventListener('click', (e) => {
    if (navMenu.classList.contains('mobile-open') && !navMenu.contains(e.target) && !toggleBtn.contains(e.target)) {
      toggle(true);
    }
  });

  // Cerrar al presionar la tecla Escape
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && navMenu.classList.contains('mobile-open')) {
      toggle(true);
    }
  });

  // Cerrar si la pantalla se redimensiona a más de 992px
  window.addEventListener('resize', () => {
    if (window.innerWidth > 992 && navMenu.classList.contains('mobile-open')) {
      toggle(true);
    }
  });
}

/**
 * 9. Alternancia de Modo Claro y Modo Oscuro (Dark / Light Theme Toggle)
 */
function initThemeToggle() {
  const savedTheme = localStorage.getItem('liceo_theme');
  const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
  const currentTheme = savedTheme || (prefersDark ? 'dark' : 'light');

  // Aplicar tema en el elemento raíz <html>
  document.documentElement.setAttribute('data-theme', currentTheme);

  // Vincular botones de cambio de tema
  const toggleBtns = document.querySelectorAll('.theme-toggle-btn');
  toggleBtns.forEach(btn => {
    btn.setAttribute('aria-label', currentTheme === 'dark' ? 'Cambiar a modo claro' : 'Cambiar a modo oscuro');
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      const activeTheme = document.documentElement.getAttribute('data-theme') === 'dark' ? 'dark' : 'light';
      const newTheme = activeTheme === 'dark' ? 'light' : 'dark';
      document.documentElement.setAttribute('data-theme', newTheme);
      localStorage.setItem('liceo_theme', newTheme);
      toggleBtns.forEach(b => {
        b.setAttribute('aria-label', newTheme === 'dark' ? 'Cambiar a modo claro' : 'Cambiar a modo oscuro');
      });
      window.dispatchEvent(new CustomEvent('themeChanged', { detail: { theme: newTheme } }));
    });
  });
}

/**
 * 10. Efectos Visuales e Interactividad 3D Avanzada para IB
 */
function initIBInteractiveEffects() {
  const isIBPage = document.body.classList.contains('theme-ib');
  
  // Elementos con experiencia y profundidad 3D
  const ibSelectors = [
    '.ib-accreditation-card',
    '.ib-hello-banner-card',
    '.ib-stat-item',
    '.ib-triad-card',
    '.ib-coordination-card',
    '.ib-coord-item',
    '.social-card'
  ];
  
  if (isIBPage) {
    ibSelectors.push(
      '.advantage-item',
      '.pillar-card',
      '.curriculum-card',
      '.requirements-box',
      '.highlight-stat-box',
      '.modality-contact-card',
      '#ibNewsGridContainer .news-card',
      '.ib-coordination-card',
      '.ib-coord-item'
    );
  }

  const ibCards = document.querySelectorAll(ibSelectors.join(', '));
  ibCards.forEach(card => {
    card.classList.add('ib-card-3d');

    card.addEventListener('mousemove', (e) => {
      const rect = card.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      const centerX = rect.width / 2;
      const centerY = rect.height / 2;
      
      const rotateX = ((y - centerY) / centerY) * -6;
      const rotateY = ((x - centerX) / centerX) * 6;
      
      card.style.transform = `perspective(1000px) rotateX(${rotateX.toFixed(2)}deg) rotateY(${rotateY.toFixed(2)}deg) translateY(-8px) scale3d(1.015, 1.015, 1.015)`;

      const glareX = ((x / rect.width) * 100).toFixed(1);
      const glareY = ((y / rect.height) * 100).toFixed(1);
      card.style.setProperty('--glare-x', `${glareX}%`);
      card.style.setProperty('--glare-y', `${glareY}%`);
      card.style.setProperty('--glare-opacity', '1');
    });

    card.addEventListener('mouseleave', () => {
      card.style.transform = '';
      card.style.setProperty('--glare-opacity', '0');
    });
  });
}

