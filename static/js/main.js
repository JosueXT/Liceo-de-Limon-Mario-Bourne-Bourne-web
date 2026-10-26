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
  initNavbarScroll();
  initParallaxHero();
  initScrollReveal();
  initAnimatedCounters();
  initNewsFilters();
  initNewsModal();
  initContactForm();
  initMobileMenu();
});

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
    rootMargin: '0px 0px -50px 0px',
    threshold: 0.1
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
  const statNumbers = document.querySelectorAll('.stat-number');
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
 * Permite filtrar comunicados por 'Todas', 'ib', 'frances', 'regular' o 'institucionales',
 * y además despliega subcategorías (ej: CAS, TOK, Actividades, DELF, etc.) si existen.
 */
function initNewsFilters() {
  const filterBtns = document.querySelectorAll('.news-tab-btn');
  const newsCards = document.querySelectorAll('.news-card');
  const subfilterWrapper = document.getElementById('newsSubfilterContainer');

  if (!filterBtns.length || !newsCards.length) return;

  let currentCategory = 'all';
  let currentSubcategory = 'all';

  function applyFilters() {
    newsCards.forEach(card => {
      const cardCategory = card.getAttribute('data-category');
      const cardSubcategory = (card.getAttribute('data-subcategory') || '').trim();

      const matchesCategory = (currentCategory === 'all' || cardCategory === currentCategory);
      const matchesSubcategory = (currentSubcategory === 'all' || cardSubcategory.toLowerCase() === currentSubcategory.toLowerCase());

      if (matchesCategory && matchesSubcategory) {
        card.style.display = 'flex';
        card.classList.add('fadeIn');
      } else {
        card.style.display = 'none';
      }
    });
  }

  function renderSubcategoriesForCategory(category) {
    if (!subfilterWrapper) return;

    if (category === 'all') {
      subfilterWrapper.style.display = 'none';
      subfilterWrapper.innerHTML = '';
      return;
    }

    // Extraer subcategorías únicas presentes en las noticias de esta categoría
    const subcats = new Set();
    newsCards.forEach(card => {
      if (card.getAttribute('data-category') === category) {
        const sub = (card.getAttribute('data-subcategory') || '').trim();
        if (sub) subcats.add(sub);
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
      html += `<button class="news-subtab-btn" data-subfilter="${sub}">${sub}</button>`;
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
      filterBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');

      currentCategory = btn.getAttribute('data-filter');
      currentSubcategory = 'all'; // reiniciar subcategoría al cambiar categoría

      renderSubcategoriesForCategory(currentCategory);
      applyFilters();
    });
  });
}

/**
 * 6. Modal de Lectura Completa de Comunicados
 */
function initNewsModal() {
  const modal = document.getElementById('newsDetailModal');
  if (!modal) return;

  function openNewsModal(card) {
    if (!card) return;

    const title = card.querySelector('.news-title')?.innerText.trim() || 'Comunicado Oficial';
    const date = card.querySelector('.news-meta-date')?.innerText.trim() || '';
    const author = card.querySelector('.news-meta-author')?.innerText.trim() || 'Liceo de Limón MEP';
    const imageEl = card.querySelector('.news-image');
    const imageSrc = imageEl ? imageEl.getAttribute('src') : '';
    const imagePos = (imageEl && imageEl.style.objectPosition) || card.getAttribute('data-image-position') || 'center center';
    const rawContent = card.getAttribute('data-content') || card.querySelector('.news-summary')?.innerText.trim() || '';

    const modalImg = document.getElementById('modalNewsImage');
    if (modalImg) {
      if (imageSrc) {
        modalImg.src = imageSrc;
        modalImg.style.objectPosition = imagePos;
        modalImg.style.display = 'block';
      } else {
        modalImg.style.display = 'none';
      }
    }

    const modalTitle = document.getElementById('modalNewsTitle');
    if (modalTitle) modalTitle.innerText = title;

    const modalDate = document.getElementById('modalNewsDate');
    if (modalDate) modalDate.innerText = date;

    const modalAuthor = document.getElementById('modalNewsAuthor');
    if (modalAuthor) modalAuthor.innerText = author;

    const modalBody = document.getElementById('modalNewsBody');
    if (modalBody) {
      // Reemplazar saltos de línea para mostrar párrafos con buen espaciado
      modalBody.innerHTML = rawContent
        .split('\n\n')
        .filter(p => p.trim())
        .map(p => `<p style="margin-bottom: 1.2rem; line-height: 1.8;">${p.trim()}</p>`)
        .join('');
    }

    modal.style.display = 'flex';
    // Forzar reflow para animación suave
    void modal.offsetWidth;
    modal.classList.add('active');
    document.body.style.overflow = 'hidden';
  }

  function closeNewsModal() {
    modal.classList.remove('active');
    document.body.style.overflow = '';
    setTimeout(() => {
      if (!modal.classList.contains('active')) {
        modal.style.display = 'none';
      }
    }, 300);
  }

  // Delegación de eventos para clics en 'Leer Comunicado' o en la tarjeta
  document.addEventListener('click', (e) => {
    const readBtn = e.target.closest('.btn-read-more');
    if (readBtn) {
      e.preventDefault();
      const card = readBtn.closest('.news-card');
      openNewsModal(card);
      return;
    }

    // Botón de cerrar o clic en el fondo oscuro
    if (e.target === modal || e.target.closest('#closeNewsModalBtn')) {
      e.preventDefault();
      closeNewsModal();
    }
  });

  // Cerrar con la tecla Escape
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && modal.classList.contains('active')) {
      closeNewsModal();
    }
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

