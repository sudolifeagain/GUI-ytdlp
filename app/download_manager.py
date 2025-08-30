import uuid
import threading
import subprocess
from datetime import datetime
from flask_socketio import emit
from . import socketio
from .ytdlp_handler import build_download_command, parse_progress, active_processes
from .live_handler import LiveHandler
from .playlist_handler import PlaylistHandler

class DownloadManager:
    """ダウンロード管理クラス"""
    
    def __init__(self):
        self.download_queue = {}
        self.queue_lock = threading.Lock()

    def add_to_queue(self, urls, options):
        """ダウンロードキューに追加"""
        with self.queue_lock:
            for url in urls:
                item_id = str(uuid.uuid4())
                
                # URL種別を判定
                from .content_analyzer import ContentAnalyzer
                content_type = ContentAnalyzer.detect_content_type(url)
                
                self.download_queue[item_id] = {
                    'id': item_id,
                    'url': url,
                    'status': 'waiting',
                    'progress': 0,
                    'details': '',
                    'options': options,
                    'content_type': content_type,
                    'created_at': datetime.now().isoformat()
                }
                
                # ライブ配信の場合は特別な処理
                if content_type == 'live':
                    self._handle_live_download(item_id)
        
        socketio.emit('queue_update', {'queue': self.download_queue}, broadcast=True)
        self.start_next_download()

    def _handle_live_download(self, item_id):
        """ライブ配信の特別処理"""
        item = self.download_queue.get(item_id)
        if not item:
            return
        
        # ライブ配信の状態をチェック
        live_status = LiveHandler.check_live_status(item['url'])
        item['live_info'] = live_status
        
        live_mode = item['options'].get('liveMode', 'wait')
        
        if not live_status.get('is_live') and live_mode == 'wait':
            item['status'] = 'waiting_for_live'
            item['details'] = 'ライブ配信開始を待機中...'

    def run_download_process(self, item_id):
        """個別のダウンロードプロセスを実行"""
        with self.queue_lock:
            item = self.download_queue.get(item_id)
            if not item:
                return
            
            # ライブ配信待機状態の場合はスキップ
            if item['status'] == 'waiting_for_live':
                return
            
            item['status'] = 'downloading'
            socketio.emit('item_update', {'item': item})

        # コンテンツタイプに応じてコマンドを選択
        if item.get('content_type') == 'live':
            command = LiveHandler.build_live_download_command(item)
        else:
            command = build_download_command(item)
        
        process = None
        try:
            process = subprocess.Popen(
                command, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                text=True, 
                encoding='utf-8', 
                errors='ignore',
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            with self.queue_lock:
                active_processes[item_id] = process
            
            # 標準出力から進捗を読み取り
            for line in iter(process.stdout.readline, ''):
                progress_data = parse_progress(line)
                if progress_data:
                    item.update(progress_data)
                    socketio.emit('download_progress', {
                        'id': item_id, 
                        'progress': item['progress'], 
                        'details': item['details']
                    })
            
            process.wait()
            
            # ダウンロード完了後の処理
            with self.queue_lock:
                if item_id not in self.download_queue:
                    return
                if process.returncode == 0:
                    item.update({
                        'status': 'completed', 
                        'progress': 100, 
                        'details_key': 'details_completed'
                    })
                elif item.get('status') == 'cancelled':
                    item.update({'details_key': 'details_cancelled'})
                else:
                    stderr_output = process.stderr.read().strip()
                    item.update({
                        'status': 'error', 
                        'details': stderr_output.split('\n')[-1] if stderr_output else 'Unknown error'
                    })

        except Exception as e:
            with self.queue_lock:
                if item_id in self.download_queue:
                    item.update({'status': 'error', 'details': str(e)})
        finally:
            with self.queue_lock:
                active_processes.pop(item_id, None)
            socketio.emit('item_update', {'item': item})
            self.start_next_download()

    def start_next_download(self):
        """次のダウンロードを開始"""
        with self.queue_lock:
            from .settings_handler import get_setting
            max_downloads = get_setting('general', {}).get('concurrentDownloads', 1)
            downloading_count = sum(1 for item in self.download_queue.values() if item['status'] == 'downloading')
            
            if downloading_count >= max_downloads:
                return
            
            waiting_item = next(
                (item for item in self.download_queue.values() if item['status'] == 'waiting'), 
                None
            )
            if waiting_item:
                socketio.start_background_task(
                    target=self.run_download_process, 
                    item_id=waiting_item['id']
                )

    def remove_item(self, item_id):
        """ダウンロードアイテムの削除/キャンセル"""
        with self.queue_lock:
            if item_id in self.download_queue:
                item = self.download_queue[item_id]
                if item['status'] == 'downloading':
                    process = active_processes.pop(item_id, None)
                    if process:
                        process.terminate()
                        item['status'] = 'cancelled'
                self.download_queue.pop(item_id, None)

    def clear_completed(self):
        """完了済み/エラーアイテムをクリア"""
        with self.queue_lock:
            ids_to_remove = [
                item_id for item_id, item in self.download_queue.items() 
                if item['status'] not in ['downloading', 'waiting', 'waiting_for_live']
            ]
            for item_id in ids_to_remove:
                self.download_queue.pop(item_id, None)