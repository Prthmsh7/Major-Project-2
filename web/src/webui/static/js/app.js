/**
 * app.js — Coverage Optimizer form logic
 * (Form is now at /app, landing at /)
 * Lenis + animations handled by lenis-scroll.js (loaded separately)
 */

// Guard: only run on /app page
if (document.getElementById('runForm')) {
  const form       = document.getElementById('runForm');
  const statusBar  = document.getElementById('statusBar');
  const statusMsg  = document.getElementById('statusMsg');
  const spinner    = document.getElementById('spinner');
  const progressFill = document.getElementById('progressFill');
  const progressWrap = document.getElementById('progressWrap');
  const runBtn     = document.getElementById('runBtn');

  function setStatus(msg, type = '') {
    if (statusBar)  statusBar.style.display = 'flex';
    if (statusMsg)  { statusMsg.textContent = msg; statusMsg.className = 'status-message ' + type; }
    if (spinner)    spinner.style.display = type === 'error' ? 'none' : 'block';
  }

  function poll(taskId) {
    if (progressWrap) progressWrap.style.display = 'block';
    const timer = setInterval(async () => {
      const r = await fetch('/api/tasks/' + taskId);
      const d = await r.json();
      setStatus('Status: ' + d.status + ' (' + (d.progress || 0) + '%)');
      if (progressFill) progressFill.style.width = (d.progress || 0) + '%';
      if (d.status === 'completed') {
        clearInterval(timer);
        setStatus('Complete! Redirecting…', 'success');
        setTimeout(() => window.location.href = '/results/' + taskId, 600);
      }
      if (d.status === 'error') {
        clearInterval(timer);
        setStatus('Error: ' + (d.error || 'Unknown error'), 'error');
        if (runBtn) runBtn.disabled = false;
      }
    }, 1200);
  }

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    if (runBtn) runBtn.disabled = true;
    setStatus('Starting optimizer…');
    const fd  = new FormData(form);
    const res = await fetch('/api/tasks', { method: 'POST', body: fd });
    const data = await res.json();
    if (!res.ok) {
      setStatus(data.error || 'Failed to start task.', 'error');
      if (runBtn) runBtn.disabled = false;
      return;
    }
    poll(data.task_id);
  });
}
