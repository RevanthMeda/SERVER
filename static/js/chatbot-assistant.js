(function () {
    const root = document.getElementById('cully-assistant-root');
    if (!root) {
        return;
    }

    const panel = root.querySelector('.assistant-panel');
    const launcher = root.querySelector('.assistant-launcher');
    const statusLabel = root.querySelector('.assistant-status');
    const messagesContainer = root.querySelector('[data-assistant-messages]');
    const form = root.querySelector('[data-assistant-form]');
    const input = form ? form.querySelector('.assistant-input') : null;
    const sendButton = form ? form.querySelector('.assistant-form-button--primary') : null;
    const researchButton = root.querySelector('[data-assistant-research]');
    const dropzone = root.querySelector('[data-assistant-dropzone]');
    const fileInput = root.querySelector('.assistant-file-input');
    const hintButtons = root.querySelectorAll('[data-assistant-hint]');
    const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');

    const endpoints = {
        start: root.dataset.assistantStart,
        message: root.dataset.assistantMessage,
        reset: root.dataset.assistantReset,
        upload: root.dataset.assistantUpload,
        document: root.dataset.assistantDocument
    };

    let conversationBootstrapped = false;
    let busy = false;

    function togglePanel(forceOpen) {
        const shouldOpen = typeof forceOpen === 'boolean' ? forceOpen : panel.hidden;
        if (shouldOpen) {
            openPanel();
        } else {
            closePanel();
        }
    }

    function openPanel() {
        if (!panel.hidden) {
            return;
        }
        panel.hidden = false;
        requestAnimationFrame(() => {
            panel.classList.add('is-open');
        });
        launcher.setAttribute('aria-expanded', 'true');
        if (!conversationBootstrapped) {
            bootstrapConversation();
        }
    }

    function closePanel() {
        panel.classList.remove('is-open');
        launcher.setAttribute('aria-expanded', 'false');
        setTimeout(() => {
            if (!panel.classList.contains('is-open')) {
                panel.hidden = true;
            }
        }, 260);
    }

    function showToast(message, tone = 'info') {
        const existing = root.querySelector('.assistant-toast');
        if (existing) {
            existing.remove();
        }
        const toast = document.createElement('div');
        toast.className = 'assistant-toast';
        if (tone === 'warning') {
            toast.style.background = 'rgba(255, 193, 7, 0.92)';
            toast.style.color = '#231b02';
        }
        if (tone === 'error') {
            toast.style.background = 'rgba(239, 83, 80, 0.92)';
            toast.style.color = '#ffffff';
        }
        toast.textContent = message;
        root.appendChild(toast);
        setTimeout(() => toast.remove(), 4200);
    }

    function createMessageElement(role, text, options = {}) {
        const wrapper = document.createElement('div');
        wrapper.className = `assistant-message assistant-message--${role}`;

        const avatar = document.createElement('div');
        avatar.className = 'assistant-message-avatar';
        avatar.innerHTML = role === 'user' ? '<i class="fas fa-user"></i>' : '<i class="fas fa-robot"></i>';

        const bubble = document.createElement('div');
        bubble.className = 'assistant-message-content';
        if (options.highlight) {
            bubble.style.borderColor = 'rgba(0, 229, 255, 0.45)';
        }
        fillParagraphs(bubble, text);

        if (options.meta && Array.isArray(options.meta)) {
            options.meta.forEach((line) => {
                const metaLine = document.createElement('small');
                metaLine.textContent = line;
                bubble.appendChild(metaLine);
            });
        }

        wrapper.appendChild(avatar);
        wrapper.appendChild(bubble);
        return wrapper;
    }

    function fillParagraphs(container, text) {
        if (typeof text !== 'string') {
            text = String(text || '');
        }
        const parts = text.split(/\n{2,}/);
        parts.forEach((block, index) => {
            const paragraph = document.createElement('p');
            paragraph.textContent = block.replace(/\n/g, ' ');
            container.appendChild(paragraph);
            if (index !== parts.length - 1) {
                container.appendChild(document.createElement('br'));
            }
        });
    }

    function appendMessage(role, text, options) {
        const element = createMessageElement(role, text, options);
        messagesContainer.appendChild(element);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    function setBusy(state) {
        busy = state;
        if (!sendButton) {
            return;
        }
        if (state) {
            sendButton.disabled = true;
            sendButton.classList.add('is-loading');
        } else {
            sendButton.disabled = false;
            sendButton.classList.remove('is-loading');
        }
    }

    async function bootstrapConversation() {
        try {
            const payload = await requestJSON(endpoints.start, { method: 'POST' });
            conversationBootstrapped = true;
            renderAssistantPayload(payload, { headline: 'Let me orchestrate the workflow for you.' });
        } catch (error) {
            showToast(error.message || 'Failed to initialise assistant.', 'error');
        }
    }

    async function requestJSON(url, options = {}) {
        const headers = Object.assign({}, options.headers || {});
        if (!headers['Content-Type'] && !headers['content-type']) {
            headers['Content-Type'] = 'application/json';
        }
        if (csrfToken) {
            headers['X-CSRFToken'] = csrfToken;
        }
        const fetchOptions = Object.assign({}, options, {
            credentials: 'same-origin',
            headers
        });
        const response = await fetch(url, fetchOptions);
        if (!response.ok) {
            const text = await response.text();
            throw new Error(text || response.statusText);
        }
        return response.json();
    }

    function updateStatus(payload) {
        if (!statusLabel) {
            return;
        }
        if (payload.completed) {
            statusLabel.textContent = 'Automation ready – review & publish when you are.';
            return;
        }
        if (payload.pending_fields && payload.pending_fields.length) {
            const nextLabel = formatFieldLabel(payload.field);
            statusLabel.textContent = `Collecting ${nextLabel}. ${payload.pending_fields.length} step(s) remain.`;
            return;
        }
        statusLabel.textContent = 'Preparing orchestration steps…';
    }

    function formatFieldLabel(field) {
        if (!field) {
            return 'details';
        }
        return field.replace(/_/g, ' ').toLowerCase();
    }

    function renderAssistantPayload(payload, options = {}) {
        if (!payload) {
            return;
        }

        if (options.headline) {
            appendMessage('bot', options.headline);
        }

        if (payload.messages && Array.isArray(payload.messages)) {
            payload.messages.forEach((message) => appendMessage('bot', message));
        }

        if (payload.errors && Array.isArray(payload.errors) && payload.errors.length) {
            payload.errors.forEach((message) => appendMessage('bot', message, { highlight: true }));
            showToast(payload.errors[0], 'error');
        }

        if (payload.warnings && Array.isArray(payload.warnings) && payload.warnings.length) {
            payload.warnings.forEach((warning) => appendMessage('bot', warning));
            showToast(payload.warnings[0], 'warning');
        }

        if (payload.command) {
            handleCommand(payload.command);
        }

        if (payload.completed) {
            appendMessage('bot', 'All critical inputs are locked in. I can push them into the form when you open it.');
        } else if (payload.question) {
            const meta = [];
            if (payload.help_text) {
                meta.push(payload.help_text);
            }
            appendMessage('bot', payload.question, { meta });
        }

        if (payload.collected) {
            const preview = summariseCollected(payload.collected, payload.pending_fields || []);
            if (preview) {
                appendMessage('bot', preview);
            }
        }

        updateStatus(payload);
    }

    function summariseCollected(collected, pending) {
        const keys = Object.keys(collected || {}).filter((key) => collected[key]);
        if (!keys.length) {
            return '';
        }
        const summary = keys.slice(0, 3).map((key) => `${formatFieldLabel(key)} ? ${collected[key]}`);
        let text = `Captured ${keys.length} field${keys.length > 1 ? 's' : ''}: ${summary.join('; ')}`;
        if (pending && pending.length) {
            text += `. Pending: ${pending.map(formatFieldLabel).join(', ')}`;
        }
        return text;
    }

    function handleCommand(command) {
        if (!command || typeof command !== 'object') {
            return;
        }
        if (command.type === 'document_fetch') {
            if (command.success && command.download_url) {
                appendMessage('bot', 'Download ready. Tap to open the generated report.', {
                    meta: [command.download_url]
                });
            } else if (command.error) {
                showToast(command.error, 'error');
            }
        }
        if (command.type === 'summary') {
            const pending = command.pending_fields || [];
            const text = pending.length
                ? `Still missing ${pending.length} item${pending.length > 1 ? 's' : ''}.`
                : 'Everything is captured.';
            appendMessage('bot', text);
        }
    }

    async function submitMessage(mode = 'default') {
        if (!form || !input) {
            return;
        }
        const raw = (input.value || '').trim();
        if (!raw || busy) {
            return;
        }
        appendMessage('user', raw);
        input.value = '';
        setBusy(true);
        try {
            const payload = await requestJSON(endpoints.message, {
                method: 'POST',
                body: JSON.stringify({ message: raw, mode })
            });
            renderAssistantPayload(payload);
        } catch (error) {
            showToast(error.message || 'Assistant unavailable.', 'error');
        } finally {
            setBusy(false);
        }
    }

    async function resetConversation() {
        setBusy(true);
        try {
            const payload = await requestJSON(endpoints.reset, { method: 'POST' });
            messagesContainer.innerHTML = '';
            appendMessage('bot', 'Starting fresh. Let’s re-align.');
            renderAssistantPayload(payload);
        } catch (error) {
            showToast(error.message || 'Unable to reset.', 'error');
        } finally {
            setBusy(false);
        }
    }

    async function uploadFiles(fileList) {
        if (!fileList || !fileList.length || busy) {
            return;
        }
        const files = Array.from(fileList);
        const formData = new FormData();
        files.forEach((file) => formData.append('files', file));
        appendMessage('user', `Uploading ${files.length} file${files.length > 1 ? 's' : ''} for analysis.`);
        setBusy(true);
        try {
            const headers = {};
            if (csrfToken) {
                headers['X-CSRFToken'] = csrfToken;
            }
            const response = await fetch(endpoints.upload, {
                method: 'POST',
                body: formData,
                credentials: 'same-origin',
                headers
            });
            if (!response.ok) {
                throw new Error('Upload failed.');
            }
            const payload = await response.json();
            renderAssistantPayload(payload);
        } catch (error) {
            showToast(error.message || 'File ingestion failed.', 'error');
        } finally {
            if (fileInput) {
                fileInput.value = '';
            }
            setBusy(false);
        }
    }

    function bindEvents() {
        launcher.addEventListener('click', () => togglePanel());
        root.querySelector('[data-assistant-close]')?.addEventListener('click', closePanel);
        root.querySelector('[data-assistant-reset]')?.addEventListener('click', resetConversation);

        form?.addEventListener('submit', (event) => {
            event.preventDefault();
            submitMessage('default');
        });

        researchButton?.addEventListener('click', () => {
            if (!input) {
                return;
            }
            if (!input.value.trim()) {
                input.placeholder = 'Describe what you want me to research…';
                input.focus();
                return;
            }
            submitMessage('research');
        });

        hintButtons.forEach((button) => {
            button.addEventListener('click', () => {
                if (!input) {
                    return;
                }
                input.value = button.dataset.assistantHint || '';
                input.focus();
            });
        });

        if (fileInput) {
            fileInput.addEventListener('change', (event) => {
                const target = event.target;
                if (target.files && target.files.length) {
                    uploadFiles(target.files);
                }
            });
        }

        if (dropzone) {
            ['dragenter', 'dragover'].forEach((type) => {
                dropzone.addEventListener(type, (event) => {
                    event.preventDefault();
                    event.stopPropagation();
                    dropzone.classList.add('is-active');
                });
            });
            ['dragleave', 'drop'].forEach((type) => {
                dropzone.addEventListener(type, (event) => {
                    event.preventDefault();
                    event.stopPropagation();
                    dropzone.classList.remove('is-active');
                });
            });
            dropzone.addEventListener('drop', (event) => {
                if (event.dataTransfer?.files?.length) {
                    uploadFiles(event.dataTransfer.files);
                }
            });
        }

        document.addEventListener('keydown', (event) => {
            if (event.key === 'Escape' && panel.classList.contains('is-open')) {
                closePanel();
            }
        });
    }

    bindEvents();
})();