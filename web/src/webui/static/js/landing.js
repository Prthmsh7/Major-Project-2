/**
 * Landing Page Animations — Coverage Optimizer
 * Typewriter, orb, floating badges, section reveals
 */
document.addEventListener('DOMContentLoaded', () => {

  // ── Typewriter ──────────────────────────────────────────────
  const phrases = [
    'AI-Powered C++ Coverage.',
    'LLM-Generated Test Inputs.',
    'Maximum Code Coverage.',
    'Mutation Testing. Automated.',
  ];
  const tw = document.getElementById('typewriter');
  if (tw) {
    let pi = 0, ci = 0, deleting = false;
    function tick() {
      const current = phrases[pi];
      if (!deleting) {
        tw.textContent = current.slice(0, ++ci);
        if (ci === current.length) { deleting = true; setTimeout(tick, 1800); return; }
      } else {
        tw.textContent = current.slice(0, --ci);
        if (ci === 0) { deleting = false; pi = (pi + 1) % phrases.length; }
      }
      setTimeout(tick, deleting ? 42 : 72);
    }
    tick();
  }

  // ── Hero orb mouse parallax ─────────────────────────────────
  const orb = document.getElementById('heroOrb');
  if (orb) {
    document.addEventListener('mousemove', (e) => {
      const dx = (e.clientX / window.innerWidth  - 0.5) * 24;
      const dy = (e.clientY / window.innerHeight - 0.5) * 24;
      orb.style.transform = `translate(${dx}px, ${dy}px)`;
    });
  }

  // ── Floating badges subtle animation ───────────────────────
  document.querySelectorAll('.float-badge').forEach((b, i) => {
    b.style.animationDelay = `${i * 0.6}s`;
  });

  // ── Hero entrance stagger ───────────────────────────────────
  const heroItems = document.querySelectorAll('.hero-animate');
  heroItems.forEach((el, i) => {
    el.style.opacity = '0';
    el.style.transform = 'translateY(30px)';
    setTimeout(() => {
      el.style.transition = 'opacity 0.7s cubic-bezier(0.16,1,0.3,1), transform 0.7s cubic-bezier(0.16,1,0.3,1)';
      el.style.opacity = '1';
      el.style.transform = 'translateY(0)';
    }, 200 + i * 120);
  });

  // ── Drag-over dropzone ──────────────────────────────────────
  document.querySelectorAll('.dropzone').forEach(dz => {
    dz.addEventListener('dragover', e => { e.preventDefault(); dz.classList.add('drag-over'); });
    dz.addEventListener('dragleave', ()  => dz.classList.remove('drag-over'));
    dz.addEventListener('drop', e => { e.preventDefault(); dz.classList.remove('drag-over'); });
    dz.addEventListener('click', () => dz.querySelector('input[type=file]')?.click());
  });

  // ── Cursor glow (desktop only) ──────────────────────────────
  if (window.innerWidth > 768) {
    const cursor = document.createElement('div');
    cursor.id = 'cursor-glow';
    Object.assign(cursor.style, {
      position: 'fixed', pointerEvents: 'none', zIndex: '9999',
      width: '300px', height: '300px',
      borderRadius: '50%',
      background: 'radial-gradient(circle, rgba(99,102,241,0.12) 0%, transparent 70%)',
      transform: 'translate(-50%, -50%)',
      transition: 'left 0.12s ease, top 0.12s ease',
    });
    document.body.appendChild(cursor);
    document.addEventListener('mousemove', e => {
      cursor.style.left = e.clientX + 'px';
      cursor.style.top  = e.clientY + 'px';
    });
  }
});
