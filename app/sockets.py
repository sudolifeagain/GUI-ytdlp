import uuid
import threading
import subprocess
from flask_socketio import emit
from . import socketio, ytdlp_handler, settings_handler
from .download_manager import DownloadManager

# DownloadManagerのインスタンスを作成
download_manager = DownloadManager()

@socketio.on('connect')
def handle_connect(auth):
    emit('version_info', {'version': ytdlp_handler.get_yt_dlp_version()})
    emit('queue_update', {'queue': download_manager.download_queue})
    emit('settings_loaded', {'settings': settings_handler.app_settings})

@socketio.on('add_to_queue')
def handle_add_to_queue(data):
    """ダウンロードキューに追加"""
    urls, options = data.get('urls', []), data.get('options', {})
    download_manager.add_to_queue(urls, options)
    emit('queue_update', {'queue': download_manager.download_queue}, broadcast=True)

@socketio.on('save_settings')
def handle_save_settings(data):
    """設定の保存"""
    settings_handler.save_settings(data.get('settings', {}))
    emit('settings_saved', {'message_key': 'settings_saved'})
    download_manager.start_next_download()

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
    download_manager.remove_item(item_id)
    emit('queue_update', {'queue': download_manager.download_queue}, broadcast=True)
    download_manager.start_next_download()

@socketio.on('clear_queue')
def handle_clear_queue():
    """完了済み/エラーアイテムをクリア"""
    download_manager.clear_completed()
    emit('queue_update', {'queue': download_manager.download_queue}, broadcast=True)
