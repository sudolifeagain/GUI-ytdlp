import { initializeTranslations, state } from './state.js';
import * as socket from './socket.js';
import * as ui from './ui.js';
import * as api from './api.js';

document.addEventListener('DOMContentLoaded', () => {
    initializeTranslations(window.LANG, window.T);
    socket.connect();

    // DOM Element Selections
    const getFormatsBtn = document.getElementById('get-formats-btn');
    const videoUrlsTextarea = document.getElementById('video-urls');
    const videoFormatPreset = document.getElementById('video-format-preset');
    const customFormatSelector = document.getElementById('custom-format-selector');
    const addToQueueBtn = document.getElementById('add-to-queue-btn');
    const saveSettingsBtn = document.getElementById('save-settings-btn');
    const downloadListUl = document.getElementById('download-list');
    const clearQueueBtn = document.getElementById('clear-queue-btn');
    const updateBtn = document.getElementById('update-btn');
    const browseBtn = document.getElementById('browse-btn');
    const openFolderBtn = document.getElementById('open-folder-btn');
    const audioOnlyCheckbox = document.getElementById('audio-only');
    const tabButtonsContainer = document.querySelector('.tab-buttons');
    const welcomeModal = document.getElementById('welcome-modal');
    const dontShowAgainBtn = document.getElementById('dont-show-again-btn');
    const cookieHelpBtn = document.getElementById('cookie-help-btn');
    const cookieHelpModal = document.getElementById('cookie-help-modal');

    // Event Listeners
    videoUrlsTextarea.addEventListener('input', () => {
        const urls = videoUrlsTextarea.value.trim().split('\n').filter(url => url.trim());
        getFormatsBtn.disabled = urls.length !== 1;
    });

    getFormatsBtn.addEventListener('click', async () => {
        const url = videoUrlsTextarea.value.trim();
        ui.showLoading(getFormatsBtn);
        const result = await api.fetchFormats(url);
        ui.hideLoading(getFormatsBtn);
        if (result.success) {
            ui.populateFormatSelector(result.formats);
            videoFormatPreset.value = 'custom';
            customFormatSelector.style.display = 'block';
        } else {
            alert('Error: ' + result.error);
        }
    });

    videoFormatPreset.addEventListener('change', () => {
        customFormatSelector.style.display = videoFormatPreset.value === 'custom' ? 'block' : 'none';
    });
    
    addToQueueBtn.addEventListener('click', () => {
        const urls = videoUrlsTextarea.value.split('\n').map(url => url.trim()).filter(url => url);
        if (urls.length > 0) {
            const options = ui.getCurrentOptions();
            socket.addToQueue(urls, options);
            videoUrlsTextarea.value = '';
            getFormatsBtn.disabled = true;
        } else {
            alert(state.translations.alert_enter_url);
        }
    });

    saveSettingsBtn.addEventListener('click', () => {
        const currentSettings = state.settings;
        currentSettings.general.concurrentDownloads = parseInt(document.getElementById('concurrent-downloads').value, 10);
        currentSettings.last_options = ui.getCurrentOptions();
        socket.saveSettings(currentSettings);
    });
    
    downloadListUl.addEventListener('click', (e) => {
        const copyBtn = e.target.closest('.copy-btn');
        const deleteBtn = e.target.closest('.item-delete-btn');
        if (copyBtn) {
            const errorText = copyBtn.closest('.download-item').querySelector('.item-progress-details').textContent;
            navigator.clipboard.writeText(errorText).then(() => {
                copyBtn.textContent = state.translations.copied;
                setTimeout(() => { copyBtn.textContent = 'Copy'; }, 1500);
            });
        } else if (deleteBtn) {
            const itemId = deleteBtn.closest('.download-item').dataset.id;
            socket.removeItem(itemId);
        }
    });

    clearQueueBtn.addEventListener('click', () => socket.clearQueue());
    updateBtn.addEventListener('click', () => socket.updateYtDlp());
    
    browseBtn.addEventListener('click', async () => {
        const path = await api.selectFolder();
        if (path) document.getElementById('save-path').value = path;
    });
    openFolderBtn.addEventListener('click', () => api.openFolder(document.getElementById('save-path').value));

    audioOnlyCheckbox.addEventListener('change', () => {
        document.getElementById('audio-format-group').style.display = audioOnlyCheckbox.checked ? 'block' : 'none';
    });

    tabButtonsContainer.addEventListener('click', (e) => {
        if (e.target.classList.contains('tab-button')) {
            document.querySelectorAll('.tab-button').forEach(btn => btn.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
            e.target.classList.add('active');
            document.getElementById(e.target.dataset.tab).classList.add('active');
        }
    });

    // --- Modal Logic ---
    const closeModal = (modal) => modal.style.display = 'none';
    
    cookieHelpBtn.addEventListener('click', () => { cookieHelpModal.style.display = 'flex'; });
    cookieHelpModal.addEventListener('click', (e) => { if (e.target === cookieHelpModal) closeModal(cookieHelpModal); });
    
    document.getElementById('close-welcome-btn').addEventListener('click', () => closeModal(welcomeModal));
    welcomeModal.addEventListener('click', (e) => { if (e.target === welcomeModal) closeModal(welcomeModal); });
    
    dontShowAgainBtn.addEventListener('click', () => {
        const currentSettings = state.settings;
        if (currentSettings.general) {
            currentSettings.general.showWelcomeNotice = false;
        }
        socket.saveSettings(currentSettings);
        closeModal(welcomeModal);
    });

    window.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            closeModal(cookieHelpModal);
            closeModal(welcomeModal);
        }
    });
});
