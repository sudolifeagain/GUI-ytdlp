document.addEventListener('DOMContentLoaded', () => {
    // T (translations) and LANG are defined in a <script> tag within index.html
    const socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port);

    // --- DOM Element Selections ---
    const ytDlpVersionSpan = document.getElementById('yt-dlp-version');
    const updateBtn = document.getElementById('update-btn');
    const updateStatusSpan = document.getElementById('update-status');
    const videoUrlsTextarea = document.getElementById('video-urls');
    const addToQueueBtn = document.getElementById('add-to-queue-btn');
    const downloadListUl = document.getElementById('download-list');
    const saveSettingsBtn = document.getElementById('save-settings-btn');
    const saveStatusSpan = document.getElementById('save-status');
    const cookieHelpBtn = document.getElementById('cookie-help-btn');
    const cookieHelpModal = document.getElementById('cookie-help-modal');
    const openFolderBtn = document.getElementById('open-folder-btn');
    const clearQueueBtn = document.getElementById('clear-queue-btn');
    const welcomeModal = document.getElementById('welcome-modal');
    const closeWelcomeBtn = document.getElementById('close-welcome-btn');
    const dontShowAgainBtn = document.getElementById('dont-show-again-btn');

    // --- UI Control Elements ---
    const controls = {
        savePath: document.getElementById('save-path'),
        concurrentDownloads: document.getElementById('concurrent-downloads'),
        videoFormat: document.getElementById('video-format'),
        audioOnly: document.getElementById('audio-only'),
        audioFormat: document.getElementById('audio-format'),
        cookieBrowser: document.getElementById('cookie-browser'),
        customArgs: document.getElementById('custom-args')
    };
    const audioFormatGroup = document.getElementById('audio-format-group');
    let currentSettings = {};

    // Show welcome modal immediately on page load if required
    if (welcomeModal.classList.contains('show-on-load')) {
        welcomeModal.style.display = 'flex';
    }

    // --- WebSocket Event Listeners ---
    socket.on('connect', () => console.log('Successfully connected.'));
    socket.on('version_info', (data) => ytDlpVersionSpan.textContent = data.version || 'Error');
    socket.on('queue_update', (data) => renderQueue(data.queue));
    socket.on('item_update', (data) => updateQueueItem(data.item));
    socket.on('download_progress', (data) => updateItemProgress(data));
    
    socket.on('settings_loaded', (data) => {
        currentSettings = data.settings;
        applySettings(currentSettings);
    });

    socket.on('settings_saved', (data) => {
        saveStatusSpan.textContent = T[data.message_key];
        setTimeout(() => saveStatusSpan.textContent = '', 2000);
    });

    socket.on('update_status', (data) => {
        let message = T[data.message_key] || '';
        if (data.version) {
            message = message.replace('{version}', data.version);
        }
        updateStatusSpan.textContent = message;
        updateBtn.disabled = data.message_key === 'update_status_updating';
        if (data.message_key !== 'update_status_updating') {
            setTimeout(() => updateStatusSpan.textContent = '', 3000);
        }
    });

    // --- UI Event Listeners ---
    document.querySelector('.tab-buttons').addEventListener('click', (e) => {
        if (e.target.classList.contains('tab-button')) {
            document.querySelectorAll('.tab-button').forEach(btn => btn.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
            e.target.classList.add('active');
            document.getElementById(e.target.dataset.tab).classList.add('active');
        }
    });
    document.getElementById('browse-btn').addEventListener('click', async () => {
        const response = await fetch('/select-folder', { method: 'POST' });
        const data = await response.json();
        if (data.folder_path) controls.savePath.value = data.folder_path;
    });
    openFolderBtn.addEventListener('click', async () => {
        if (controls.savePath.value) {
            await fetch('/open-folder', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ path: controls.savePath.value }),
            });
        }
    });
    controls.audioOnly.addEventListener('change', () => {
        audioFormatGroup.style.display = controls.audioOnly.checked ? 'block' : 'none';
    });
    updateBtn.addEventListener('click', () => socket.emit('update_yt_dlp'));
    saveSettingsBtn.addEventListener('click', () => {
        currentSettings.general.concurrentDownloads = parseInt(controls.concurrentDownloads.value, 10);
        currentSettings.last_options = {
            savePath: controls.savePath.value, videoFormat: controls.videoFormat.value,
            audioOnly: controls.audioOnly.checked, audioFormat: controls.audioFormat.value,
            cookieBrowser: controls.cookieBrowser.value, customArgs: controls.customArgs.value
        };
        socket.emit('save_settings', { settings: currentSettings });
    });
    addToQueueBtn.addEventListener('click', () => {
        const urls = videoUrlsTextarea.value.split('\n').map(url => url.trim()).filter(url => url);
        if (urls.length > 0) {
            const options = {
                savePath: controls.savePath.value, videoFormat: controls.videoFormat.value,
                audioOnly: controls.audioOnly.checked, audioFormat: controls.audioFormat.value,
                cookieBrowser: controls.cookieBrowser.value, customArgs: controls.customArgs.value
            };
            socket.emit('add_to_queue', { urls, options });
            videoUrlsTextarea.value = '';
        } else {
            alert(T.alert_enter_url);
        }
    });
    downloadListUl.addEventListener('click', (e) => {
        const copyBtn = e.target.closest('.copy-btn');
        const deleteBtn = e.target.closest('.item-delete-btn');

        if (copyBtn) {
            const errorText = copyBtn.closest('.download-item').querySelector('.item-progress-details').textContent;
            navigator.clipboard.writeText(errorText).then(() => {
                copyBtn.textContent = T.copied;
                setTimeout(() => { copyBtn.textContent = 'Copy'; }, 1500);
            });
        } else if (deleteBtn) {
            const itemId = deleteBtn.closest('.download-item').dataset.id;
            socket.emit('remove_item', { id: itemId });
        }
    });
    clearQueueBtn.addEventListener('click', () => socket.emit('clear_queue'));
    
    // --- Modal Event Listeners ---
    const closeModal = (modal) => modal.style.display = 'none';
    cookieHelpBtn.addEventListener('click', () => { cookieHelpModal.style.display = 'flex'; });
    cookieHelpModal.addEventListener('click', (e) => { if (e.target === cookieHelpModal) closeModal(cookieHelpModal); });
    
    closeWelcomeBtn.addEventListener('click', () => closeModal(welcomeModal));
    welcomeModal.addEventListener('click', (e) => { if (e.target === welcomeModal) closeModal(welcomeModal); });
    dontShowAgainBtn.addEventListener('click', () => {
        if (currentSettings.general) {
            currentSettings.general.showWelcomeNotice = false;
        }
        socket.emit('save_settings', { settings: currentSettings });
        closeModal(welcomeModal);
    });
    window.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            closeModal(cookieHelpModal);
            closeModal(welcomeModal);
        }
    });

    // --- Helper Functions ---
    function applySettings(settings) {
        currentSettings = settings;
        const general = settings.general || {};
        const options = settings.last_options || {};
        controls.concurrentDownloads.value = general.concurrentDownloads || 1;
        controls.savePath.value = options.savePath || '';
        controls.videoFormat.value = options.videoFormat || 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best';
        controls.audioOnly.checked = options.audioOnly || false;
        controls.audioFormat.value = options.audioFormat || 'best';
        controls.cookieBrowser.value = options.cookieBrowser || 'none';
        controls.customArgs.value = options.customArgs || '';
        audioFormatGroup.style.display = controls.audioOnly.checked ? 'block' : 'none';
    }
    function renderQueue(queue) {
        downloadListUl.innerHTML = '';
        const queueIds = Object.keys(queue);
        if (queueIds.length === 0) {
            downloadListUl.innerHTML = `<li class="list-placeholder">${T.no_downloads_yet}</li>`;
        } else {
            queueIds.forEach(id => downloadListUl.appendChild(createQueueItemElement(queue[id])));
        }
    }
    function createQueueItemElement(item) {
        const li = document.createElement('li');
        li.className = 'download-item';
        li.dataset.id = item.id;
        
        const statusKey = item.status;
        const statusText = T[`status_${statusKey}`] || statusKey;
        const statusClass = statusKey;
        
        const isError = statusClass === 'error';
        const buttonTitle = item.status === 'downloading' ? T.button_title_cancel : T.button_title_delete;
        
        let detailsText = item.details;
        if (item.details_key) {
            detailsText = T[item.details_key] || item.details;
        }

        li.innerHTML = `
            <button class="item-delete-btn" title="${buttonTitle}">&times;</button>
            <div class="item-info">
                <span class="item-url" title="${item.url}">${item.url}</span>
                <span class="item-status ${statusClass}">${statusText}</span>
            </div>
            <div class="details-wrapper">
                <div class="item-progress-details">${detailsText}</div>
                ${isError ? `<button class="copy-btn" title="${T.copy_error}">Copy</button>` : ''}
            </div>
            <div class="progress-bar-container"><div class="progress-bar" style="width: ${item.progress}%;"></div></div>`;
        return li;
    }
    function updateQueueItem(item) {
        const li = downloadListUl.querySelector(`[data-id="${item.id}"]`);
        if (li) li.replaceWith(createQueueItemElement(item));
    }
    function updateItemProgress(data) {
        const li = downloadListUl.querySelector(`[data-id="${data.id}"]`);
        if (li) {
            li.querySelector('.progress-bar').style.width = `${data.progress}%`;
            li.querySelector('.item-progress-details').textContent = data.details;
        }
    }
});
