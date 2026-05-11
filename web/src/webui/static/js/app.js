const form = document.getElementById('runForm');
const statusEl = document.getElementById('status');
const inputMode = document.getElementById('inputMode');
const uploadSection = document.getElementById('uploadSection');
const editorSection = document.getElementById('editorSection');
const fileInput = document.getElementById('fileInput');

function syncMode() {
  const editor = inputMode.value === 'editor';
  uploadSection.style.display = editor ? 'none' : 'block';
  editorSection.style.display = editor ? 'block' : 'none';
  fileInput.required = !editor;
}
inputMode.addEventListener('change', syncMode);
syncMode();

function poll(taskId) {
  const timer = setInterval(async () => {
    const r = await fetch(`/api/tasks/${taskId}`);
    const d = await r.json();
    statusEl.textContent = `Status: ${d.status} (${d.progress}%)`;
    if (d.status === 'completed') {
      clearInterval(timer);
      window.location.href = `/results/${taskId}`;
    }
    if (d.status === 'error') {
      clearInterval(timer);
      statusEl.textContent = `Error: ${d.error}`;
    }
  }, 1200);
}

form.addEventListener('submit', async (e) => {
  e.preventDefault();
  statusEl.textContent = 'Starting...';
  const fd = new FormData(form);
  const res = await fetch('/api/tasks', { method: 'POST', body: fd });
  const data = await res.json();
  if (!res.ok) {
    statusEl.textContent = data.error || 'Failed';
    return;
  }
  poll(data.task_id);
});
