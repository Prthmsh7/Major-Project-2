const form = document.getElementById('uploadForm');
const statusEl = document.getElementById('status');

async function pollTask(taskId) {
  const timer = setInterval(async () => {
    const res = await fetch(`/api/tasks/${taskId}`);
    const data = await res.json();
    statusEl.textContent = `Status: ${data.status}, Progress: ${data.progress}%`;

    if (data.status === 'completed') {
      clearInterval(timer);
      window.location.href = `/results/${taskId}`;
    }
    if (data.status === 'error') {
      clearInterval(timer);
      statusEl.textContent = `Error: ${data.error}`;
    }
  }, 1500);
}

form?.addEventListener('submit', async (e) => {
  e.preventDefault();
  statusEl.textContent = 'Uploading and starting task...';

  const formData = new FormData(form);
  const res = await fetch('/api/tasks', {
    method: 'POST',
    body: formData,
  });

  const data = await res.json();
  if (!res.ok) {
    statusEl.textContent = data.error || 'Failed to create task.';
    return;
  }

  statusEl.textContent = `Task ${data.task_id} started.`;
  pollTask(data.task_id);
});
