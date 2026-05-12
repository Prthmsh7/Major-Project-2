/**
 * Lenis Smooth Scroll + GSAP ScrollTrigger integration
 * Coverage Optimizer — Liquid Glass UI
 */

(function () {
  /* ── Fallback: reveal elements via IntersectionObserver
     This runs immediately so content is ALWAYS visible even if CDN fails */
  function attachFallbackObserver() {
    const io = new IntersectionObserver((entries) => {
      entries.forEach(e => {
        if (e.isIntersecting) {
          e.target.classList.add('visible');
          io.unobserve(e.target);
        }
      });
    }, { threshold: 0.1 });

    document.querySelectorAll('.reveal').forEach(el => io.observe(el));

    // Stagger groups — show all children when group enters view
    document.querySelectorAll('.stagger-group').forEach(group => {
      const children = group.querySelectorAll('.stagger-item');
      // Make sure items start invisible
      children.forEach((c, i) => {
        c.style.opacity = '0';
        c.style.transform = 'translateY(40px)';
        c.style.transition = `opacity 0.6s ease ${i * 0.1}s, transform 0.6s ease ${i * 0.1}s`;
      });
      const sio = new IntersectionObserver((entries) => {
        if (entries[0].isIntersecting) {
          children.forEach(c => {
            c.style.opacity = '1';
            c.style.transform = 'translateY(0)';
          });
          sio.disconnect();
        }
      }, { threshold: 0.12 });
      sio.observe(group);
    });
  }

  // Run fallback immediately on DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', attachFallbackObserver);
  } else {
    attachFallbackObserver();
  }

  /* ── Load Lenis & GSAP from CDN ───────────────────────────── */
  function loadScript(src, cb) {
    const s = document.createElement('script');
    s.src = src;
    s.onload = cb;
    s.onerror = cb; // don't block on CDN failure
    document.head.appendChild(s);
  }

  const GSAP_CDN  = 'https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/gsap.min.js';
  const ST_CDN    = 'https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/ScrollTrigger.min.js';
  const LENIS_CDN = 'https://cdn.jsdelivr.net/npm/lenis@1.1.14/dist/lenis.min.js';

  // Two independent load chains → two onLoad calls total
  let loaded = 0;
  function onLoad() {
    loaded++;
    if (loaded === 2) initAll(); // GSAP+ST chain = 1, Lenis = 1  → total 2
  }

  loadScript(GSAP_CDN, () => loadScript(ST_CDN, onLoad));
  loadScript(LENIS_CDN, onLoad);

  /* ── Init (runs when both CDN chains finish) ──────────────── */
  function initAll() {
    if (typeof gsap === 'undefined' || typeof Lenis === 'undefined') return;

    // ── Lenis
    const lenis = new Lenis({
      lerp: 0.08,
      smoothWheel: true,
      wheelMultiplier: 0.9,
      autoRaf: false,
    });
    window.lenis = lenis;

    gsap.registerPlugin(ScrollTrigger);
    gsap.ticker.add((time) => lenis.raf(time * 1000));
    gsap.ticker.lagSmoothing(0);
    lenis.on('scroll', ScrollTrigger.update);

    // ── Upgrade .reveal to GSAP (override the CSS fallback)
    document.querySelectorAll('.reveal').forEach((el) => {
      // Reset state set by CSS
      el.style.opacity = '';
      el.style.transform = '';
      gsap.set(el, { opacity: 0, y: 40 });
      ScrollTrigger.create({
        trigger: el,
        start: 'top 88%',
        once: true,
        onEnter: () => {
          gsap.to(el, {
            opacity: 1, y: 0,
            duration: 0.75,
            ease: 'power3.out',
            delay: parseFloat(el.dataset.delay || 0),
          });
        },
      });
    });

    // ── Stagger groups
    document.querySelectorAll('.stagger-group').forEach((group) => {
      const children = group.querySelectorAll('.stagger-item');
      // Clear inline styles from fallback observer
      children.forEach(c => { c.style.opacity = ''; c.style.transform = ''; c.style.transition = ''; });
      gsap.set(children, { opacity: 0, y: 50 });
      ScrollTrigger.create({
        trigger: group,
        start: 'top 82%',
        once: true,
        onEnter: () => {
          gsap.to(children, {
            opacity: 1, y: 0,
            duration: 0.65,
            ease: 'power3.out',
            stagger: 0.10,
          });
        },
      });
    });

    // ── Parallax aurora blobs
    document.querySelectorAll('.aurora-blob').forEach((blob, i) => {
      gsap.to(blob, {
        y: (i % 2 === 0 ? -1 : 1) * 80,
        ease: 'none',
        scrollTrigger: { scrub: 1.5 },
      });
    });

    // ── Counter animation
    document.querySelectorAll('[data-count]').forEach((el) => {
      const target   = parseFloat(el.dataset.count);
      const suffix   = el.dataset.suffix || '';
      const decimals = parseInt(el.dataset.decimals || 0);
      ScrollTrigger.create({
        trigger: el,
        start: 'top 85%',
        once: true,
        onEnter: () => {
          gsap.fromTo(
            { val: 0 },
            {
              val: target, duration: 1.8, ease: 'power2.out',
              onUpdate: function () {
                el.textContent = Number(this.targets()[0].val).toFixed(decimals) + suffix;
              },
            }
          );
        },
      });
    });

    // ── Navbar hide/show
    const navbar = document.querySelector('.navbar');
    if (navbar) {
      navbar.style.transition = 'transform 0.45s cubic-bezier(0.16,1,0.3,1), opacity 0.4s ease';
      let lastY = 0;
      lenis.on('scroll', ({ scroll }) => {
        const delta = scroll - lastY;
        if (scroll < 80 || delta < 0) {
          navbar.style.transform = 'translateX(-50%) translateY(0)';
          navbar.style.opacity   = '1';
        } else {
          navbar.style.transform = 'translateX(-50%) translateY(-120%)';
          navbar.style.opacity   = '0';
        }
        lastY = scroll;
      });
    }
  }
})();
