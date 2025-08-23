
// ファイル: static/js/socket.js
// Manages all WebSocket communication with the server.
import { renderQueue, updateQueueItem, updateItemProgress, applySettings, showUpdateStatus, showSaveStatus, updateVersion } from './ui.js';
import { setSettings } from './state.js';

let socket;

export function connect() {
    socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port);

    socket.on('connect', () => console.log('Successfully connected.'));
    socket.on('version_info', (data) => updateVersion(data.version));
    socket.on('queue_update', (data) => renderQueue(data.queue));
    socket.on('item_update', (data) => updateQueueItem(data.item));
    socket.on('download_progress', (data) => updateItemProgress(data));
    
    socket.on('settings_loaded', (data) => {
        setSettings(data.settings);
        applySettings(data.settings);
    });

    socket.on('settings_saved', (data) => showSaveStatus());
    socket.on('update_status', (data) => showUpdateStatus(data));
}

export function addToQueue(urls, options) {
    socket.emit('add_to_queue', { urls, options });
}

export function saveSettings(settings) {
    socket.emit('save_settings', { settings });
}

export function updateYtDlp() {
    socket.emit('update_yt_dlp');
}

export function removeItem(itemId) {
    socket.emit('remove_item', { id: itemId });
}

export function clearQueue() {
    socket.emit('clear_queue');
}