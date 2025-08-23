import { state } from './state.js';

const controls = {
    savePath: document.getElementById('save-path'),
    concurrentDownloads: document.getElementById('concurrent-downloads'),
    videoFormatPreset: document.getElementById('video-format-preset'),
    customVideoFormat: document.getElementById('custom-video-format'),
    audioOnly: document.getElementById('audio-only'),
    audioFormat: document.getElementById('audio-format'),
    cookieBrowser: document.getElementById('cookie-browser'),
    customArgs: document.getElementById('custom-args')
};
const audioFormatGroup = document.getElementById('audio-format-group');
const downloadListUl = document.getElementById('download-list');

export function getCurrentOptions() {
    const presetValue = controls.videoFormatPreset.value;
    // 'custom' 以外が選択されている場合は、プリセット値を使用する
    const selectedFormat = presetValue !== 'custom' ? presetValue : controls.customVideoFormat.value;

    return {
        savePath: controls.savePath.value,
        selectedFormat: selectedFormat,
        audioOnly: controls.audioOnly.checked,
        audioFormat: controls.audioFormat.value,
        cookieBrowser: controls.cookieBrowser.value,
        customArgs: controls.customArgs.value
    };
}


export function applySettings(settings) {
    const general = settings.general || {};
    const options = settings.last_options || {};
    controls.concurrentDownloads.value = general.concurrentDownloads || 1;
    controls.savePath.value = options.savePath || '';
    controls.audioOnly.checked = options.audioOnly || false;
    controls.audioFormat.value = options.audioFormat || 'best';
    controls.cookieBrowser.value = options.cookieBrowser || 'none';
    controls.customArgs.value = options.customArgs || '';
    audioFormatGroup.style.display = controls.audioOnly.checked ? 'block' : 'none';
}

export function renderQueue(queue) {
    downloadListUl.innerHTML = '';
    const queueIds = Object.keys(queue);
    const placeholderText = state.translations?.no_downloads_yet || 'No downloads yet.';
    if (queueIds.length === 0) {
        downloadListUl.innerHTML = `<li class="list-placeholder">${placeholderText}</li>`;
    } else {
        queueIds.forEach(id => downloadListUl.appendChild(createQueueItemElement(queue[id])));
    }
}

function createQueueItemElement(item) {
    const li = document.createElement('li');
    li.className = 'download-item';
    li.dataset.id = item.id;
    
    const statusKey = item.status;
    const statusText = state.translations?.[`status_${statusKey}`] || statusKey;
    const statusClass = statusKey;
    
    const isError = statusClass === 'error';
    const buttonTitle = item.status === 'downloading' ? state.translations?.button_title_cancel : state.translations?.button_title_delete;
    
    let detailsText = item.details;
    if (item.details_key) {
        detailsText = state.translations?.[item.details_key] || item.details;
    }

    li.innerHTML = `
        <button class="item-delete-btn" title="${buttonTitle}">&times;</button>
        <div class="item-info">
            <span class="item-url" title="${item.url}">${item.url}</span>
            <span class="item-status ${statusClass}">${statusText}</span>
        </div>
        <div class="details-wrapper">
            <div class="item-progress-details">${detailsText}</div>
            ${isError ? `<button class="copy-btn" title="${state.translations?.copy_error}">Copy</button>` : ''}
        </div>
        <div class="progress-bar-container"><div class="progress-bar" style="width: ${item.progress}%;"></div></div>`;
    return li;
}

export function updateQueueItem(item) {
    const li = downloadListUl.querySelector(`[data-id="${item.id}"]`);
    if (li) li.replaceWith(createQueueItemElement(item));
}

export function updateItemProgress(data) {
    const li = downloadListUl.querySelector(`[data-id="${data.id}"]`);
    if (li) {
        li.querySelector('.progress-bar').style.width = `${data.progress}%`;
        li.querySelector('.item-progress-details').textContent = data.details;
    }
}

export function populateFormatSelector(formats) {
    const select = document.getElementById('custom-video-format');
    select.innerHTML = '';
    if (formats && formats.length > 0) {
        formats.forEach(f => {
            const size = f.filesize ? `(${(f.filesize / 1024 / 1024).toFixed(2)} MB)` : '';
            const fps = f.fps ? `@ ${f.fps}fps` : '';
            const note = f.note ? `- ${f.note}` : '';
            const label = `${f.resolution}p (${f.ext}) ${fps} ${size} ${note}`;
            const opt = new Option(label.trim(), f.id);
            select.appendChild(opt);
        });
    }
}

export function showLoading(button) {
    button.disabled = true;
    button.textContent = '取得中...';
}

export function hideLoading(button) {
    button.disabled = false;
    button.textContent = 'フォーマット取得';
}

export function updateVersion(version) {
    document.getElementById('yt-dlp-version').textContent = version || 'Error';
}

export function showSaveStatus() {
    const statusSpan = document.getElementById('save-status');
    statusSpan.textContent = state.translations?.settings_saved;
    setTimeout(() => statusSpan.textContent = '', 2000);
}

export function showUpdateStatus(data) {
    const statusSpan = document.getElementById('update-status');
    let message = state.translations?.[data.message_key] || '';
    if (data.version) {
        message = message.replace('{version}', data.version);
    }
    statusSpan.textContent = message;
    document.getElementById('update-btn').disabled = data.message_key === 'update_status_updating';
    if (data.message_key !== 'update_status_updating') {
        setTimeout(() => statusSpan.textContent = '', 3000);
    }
}
