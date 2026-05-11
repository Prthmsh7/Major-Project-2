const form = document.getElementById('uploadForm');
const statusEl = document.getElementById('status');
const inputModeEl = document.getElementById('inputMode');
const uploadSection = document.getElementById('uploadSection');
const editorSection = document.getElementById('editorSection');
const fileInput = document.getElementById('fileInput');
const sourceCodeField = document.getElementById('sourceCode');
const monacoContainer = document.getElementById('monacoEditor');

let monacoEditor = null;

function initializeMonaco() {
  if (!monacoContainer) return;
  if (window.monaco && monacoEditor) return;

  const initialCode = `#include <iostream>\n\nint add(int a, int b) {\n  return a + b;\n}\n\nint main() {\n  std::cout << add(2, 3) << "\\n";\n  return 0;\n}\n`;

  const onReady = () => {
    monacoEditor = window.monaco.editor.create(monacoContainer, {
      value: sourceCodeField?.value || initialCode,
      language: 'cpp',
      theme: 'vs',
      automaticLayout: true,
      minimap: { enabled: false },
      fontSize: 14,
      lineNumbers: 'on',
      tabSize: 2,
      insertSpaces: true,
      wordWrap: 'on',
      scrollBeyondLastLine: false,
      roundedSelection: false,
    });
  };

  if (!window.require) {
    const script = document.createElement('script');
    script.src = 'https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.52.2/min/vs/loader.min.js';
    script.onload = () => {
      window.require.config({ paths: { vs: 'https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.52.2/min/vs' } });
      window.require(['vs/editor/editor.main'], onReady);
    };
    document.head.appendChild(script);
  } else {
    window.require.config({ paths: { vs: 'https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.52.2/min/vs' } });
    window.require(['vs/editor/editor.main'], onReady);
  }
}

function syncInputMode() {
  const isEditor = inputModeEl?.value === 'editor';
  if (uploadSection) uploadSection.style.display = isEditor ? 'none' : 'block';
  if (editorSection) editorSection.style.display = isEditor ? 'block' : 'none';
  if (fileInput) fileInput.required = !isEditor;
  if (isEditor) initializeMonaco();
}

inputModeEl?.addEventListener('change', syncInputMode);
syncInputMode();

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
  statusEl.textContent = 'Preparing and starting task...';

  const isEditor = inputModeEl?.value === 'editor';
  if (isEditor && sourceCodeField) {
    sourceCodeField.value = monacoEditor ? monacoEditor.getValue() : sourceCodeField.value;
  }

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
