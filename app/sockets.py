import uuid
import threading
import subprocess
from flask_socketio import emit
from . import socketio, ytdlp_handler, settings_handler
from .ytdlp_handler import active_processes

download_queue = {}
queue_lock = threading.Lock()

def run_download_process(item_id):
    """個別のダウンロードプロセスを実行する"""
    with queue_lock:
        item = download_queue.get(item_id)
        if not item: 
            return
        item['status'] = 'downloading'
        socketio.emit('item_update', {'item': item})

    command = ytdlp_handler.build_download_command(item)
    
    process = None
    try:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
                                 text=True, encoding='utf-8', errors='ignore', 
                                 creationflags=subprocess.CREATE_NO_WINDOW)
        with queue_lock:
            active_processes[item_id] = process
        
        # 標準出力から進捗を読み取り
        for line in iter(process.stdout.readline, ''):
            progress_data = ytdlp_handler.parse_progress(line)
            if progress_data:
                item.update(progress_data)
                socketio.emit('download_progress', {'id': item_id, 'progress': item['progress'], 'details': item['details']})
        
        process.wait()
        
        # ダウンロード完了後の処理
        with queue_lock:
            if item_id not in download_queue: 
                return
            if process.returncode == 0:
                item.update({'status': 'completed', 'progress': 100, 'details_key': 'details_completed'})
            elif item.get('status') == 'cancelled':
                item.update({'details_key': 'details_cancelled'})
            else:
                item.update({'status': 'error', 'details': process.stderr.read().strip().split('\n')[-1]})

    except Exception as e:
        with queue_lock:
            if item_id in download_queue:
                item.update({'status': 'error', 'details': str(e)})
    finally:
        with queue_lock:
            active_processes.pop(item_id, None)
        socketio.emit('item_update', {'item': item})
        socketio.start_background_task(target=start_next_download)

def start_next_download():
    """次のダウンロードを開始する"""
    with queue_lock:
        max_downloads = settings_handler.get_setting('general', {}).get('concurrentDownloads', 1)
        downloading_count = sum(1 for item in download_queue.values() if item['status'] == 'downloading')
        if downloading_count >= max_downloads: 
            return
        
        waiting_item = next((item for item in download_queue.values() if item['status'] == 'waiting'), None)
        if waiting_item:
            socketio.start_background_task(target=run_download_process, item_id=waiting_item['id'])

@socketio.on('connect')
def handle_connect(auth):
    emit('version_info', {'version': ytdlp_handler.get_yt_dlp_version()})
    emit('queue_update', {'queue': download_queue})
    emit('settings_loaded', {'settings': settings_handler.app_settings})

@socketio.on('add_to_queue')
def handle_add_to_queue(data):
    """ダウンロードキューに追加"""
    urls, options = data.get('urls', []), data.get('options', {})
    with queue_lock:
        for url in urls:
            item_id = str(uuid.uuid4())
            download_queue[item_id] = {
                'id': item_id, 'url': url, 'status': 'waiting',
                'progress': 0, 'details': '', 'options': options
            }
    emit('queue_update', {'queue': download_queue}, broadcast=True)
    socketio.start_background_task(target=start_next_download)

@socketio.on('save_settings')
def handle_save_settings(data):
    """設定の保存"""
    settings_handler.save_settings(data.get('settings', {}))
    emit('settings_saved', {'message_key': 'settings_saved'})
    start_next_download()

@socketio.on('update_yt_dlp')
def handle_update_yt_dlp():
    """yt-dlpのアップデート"""
    emit('update_status', {'message_key': 'update_status_updating'})
    if ytdlp_handler.download_yt_dlp(force_update=True):
        new_version = ytdlp_handler.get_yt_dlp_version()
        emit('update_status', {'message_key': 'update_status_complete', 'version': new_version})
        emit('version_info', {'version': new_version})
    else:
        emit('update_status', {'message_key': 'update_status_failed'})

@socketio.on('remove_item')
def handle_remove_item(data):
    """ダウンロードアイテムの削除/キャンセル"""
    item_id = data.get('id')
    with queue_lock:
        if item_id in download_queue:
            item = download_queue[item_id]
            if item['status'] == 'downloading':
                process = active_processes.pop(item_id, None)
                if process:
                    process.terminate()
                    item['status'] = 'cancelled'
            download_queue.pop(item_id, None)
    emit('queue_update', {'queue': download_queue}, broadcast=True)
    start_next_download()

@socketio.on('clear_queue')
def handle_clear_queue():
    """完了済み/エラーアイテムをクリア"""
    with queue_lock:
        ids_to_remove = [item_id for item_id, item in download_queue.items() if item['status'] != 'downloading']
        for item_id in ids_to_remove:
            download_queue.pop(item_id, None)
    emit('queue_update', {'queue': download_queue}, broadcast=True)
