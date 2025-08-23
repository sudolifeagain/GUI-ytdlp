import os
import subprocess
import requests
import json
import uuid
import re
import threading
import sys
import shlex
from flask import Flask, render_template, send_from_directory, request
from flask_socketio import SocketIO, emit

# --- アプリケーションの基本設定 ---
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
socketio = SocketIO(app, async_mode='threading')

# --- グローバル変数・定数 ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TOOLS_DIR = os.path.join(BASE_DIR, 'tools')
DOWNLOADS_DIR = os.path.join(BASE_DIR, 'downloads')
SETTINGS_FILE = os.path.join(BASE_DIR, 'settings.json')
YT_DLP_PATH = os.path.join(TOOLS_DIR, 'yt-dlp.exe')
YT_DLP_LATEST_RELEASE_URL = 'https://api.github.com/repos/yt-dlp/yt-dlp/releases/latest'

# --- 共有データ ---
download_queue = {}
app_settings = {}
active_processes = {}
queue_lock = threading.Lock()
max_concurrent_downloads = 1

# --- 多言語対応 ---
translations = {
    "ja": {
        "update_button": "Update", "control_panel": "コントロールパネル", "video_url_label": "動画URL (1行に1つ):",
        "main": "メイン", "video": "映像", "audio": "音声", "other": "その他",
        "save_path_label": "保存先フォルダ:", "browse": "参照...", "open": "開く",
        "concurrent_downloads_label": "同時ダウンロード数:", "video_format_label": "映像フォーマット:",
        "best_quality_mp4": "最高品質 (mp4)", "best_quality_webm": "最高品質 (webm)",
        "audio_only_label": "音声のみダウンロード", "audio_format_label": "音声フォーマット:",
        "best_quality_original": "最高音質 (元の形式)", "cookie_browser_label": "Cookieを使用するブラウザ:",
        "not_used": "使用しない", "chrome_not_recommended": "Chrome (非推奨)",
        "custom_args_label": "カスタム引数:", "save_settings_button": "現在の設定を保存",
        "add_to_queue_button": "キューに追加", "download_queue_title": "ダウンロードキュー",
        "clear_completed_button": "完了/エラーをクリア", "no_downloads_yet": "まだダウンロードはありません。",
        "cookie_help_title": "Cookie機能について",
        "cookie_help_p1": "ログインが必要な動画をダウンロードするための機能です。",
        "cookie_help_li1": "✅ <strong>Firefox:</strong> 開発環境で動作確認済みです。最も推奨されます。",
        "cookie_help_li2": "⚠️ <strong>Chrome (Edge, Brave等):</strong> ご利用のWindows環境によっては、暗号化解除(DPAPI)のエラーで失敗することがあります。非推奨です。",
        "cookie_help_close": "(このウィンドウの外側をクリックするか、Escキーで閉じます)",
        "welcome_title": "ようこそ！", "welcome_p1": "このツールをご利用いただきありがとうございます。",
        "welcome_disclaimer": "【免責事項】",
        "welcome_li1": "このツールは、個人的な利用および教育目的でのみ使用してください。",
        "welcome_li2": "ダウンロードするコンテンツの著作権および利用規約を遵守する責任は、すべて利用者にあります。",
        "welcome_li3": "著作権保護されたコンテンツの無断ダウンロードは違法となる可能性があります。",
        "welcome_li4": "本ツールの使用によって生じたいかなる問題についても、開発者は一切の責任を負いません。",
        "dont_show_again": "再度表示しない", "close": "閉じる",
        "status_waiting": "待機中", "status_downloading": "ダウンロード中", "status_completed": "完了", "status_error": "エラー", "status_cancelled": "キャンセル済み",
        "details_completed": "ダウンロードが完了しました。", "details_cancelled": "ダウンロードがキャンセルされました。",
        "settings_saved": "保存しました！", "alert_enter_url": "URLを入力してください。",
        "button_title_cancel": "キャンセル", "button_title_delete": "削除", "copy_error": "エラーをコピー", "copied": "✅",
        "update_status_updating": "アップデート中...", "update_status_complete": "アップデート完了！ (Ver: {version})", "update_status_failed": "アップデートに失敗しました。"
    },
    "en": {
        "update_button": "Update", "control_panel": "Control Panel", "video_url_label": "Video URL (one per line):",
        "main": "Main", "video": "Video", "audio": "Audio", "other": "Other",
        "save_path_label": "Save to folder:", "browse": "Browse...", "open": "Open",
        "concurrent_downloads_label": "Concurrent downloads:", "video_format_label": "Video Format:",
        "best_quality_mp4": "Best Quality (mp4)", "best_quality_webm": "Best Quality (webm)",
        "audio_only_label": "Download audio only", "audio_format_label": "Audio Format:",
        "best_quality_original": "Best Quality (original)", "cookie_browser_label": "Browser for cookies:",
        "not_used": "Do not use", "chrome_not_recommended": "Chrome (not recommended)",
        "custom_args_label": "Custom Arguments:", "save_settings_button": "Save Current Settings",
        "add_to_queue_button": "Add to Queue", "download_queue_title": "Download Queue",
        "clear_completed_button": "Clear Completed/Errors", "no_downloads_yet": "No downloads yet.",
        "cookie_help_title": "About the Cookie Feature",
        "cookie_help_p1": "This feature is for downloading videos that require a login.",
        "cookie_help_li1": "✅ <strong>Firefox:</strong> Confirmed working in the development environment. Highly recommended.",
        "cookie_help_li2": "⚠️ <strong>Chrome (Edge, Brave, etc.):</strong> May fail with a decryption (DPAPI) error depending on your Windows environment. Not recommended.",
        "cookie_help_close": "(Click outside this window or press Esc to close)",
        "welcome_title": "Welcome!", "welcome_p1": "Thank you for using this tool.",
        "welcome_disclaimer": "【Disclaimer】",
        "welcome_li1": "This tool should be used for personal and educational purposes only.",
        "welcome_li2": "The user is solely responsible for complying with the copyright and terms of use of the content to be downloaded.",
        "welcome_li3": "Unauthorized downloading of copyrighted content may be illegal in your country.",
        "welcome_li4": "The developer assumes no responsibility for any legal issues arising from the use of this tool.",
        "dont_show_again": "Do not show again", "close": "Close",
        "status_waiting": "Waiting", "status_downloading": "Downloading", "status_completed": "Completed", "status_error": "Error", "status_cancelled": "Cancelled",
        "details_completed": "Download completed.", "details_cancelled": "Download was cancelled.",
        "settings_saved": "Settings saved!", "alert_enter_url": "Please enter a URL.",
        "button_title_cancel": "Cancel", "button_title_delete": "Delete", "copy_error": "Copy error", "copied": "✅",
        "update_status_updating": "Updating...", "update_status_complete": "Update complete! (Ver: {version})", "update_status_failed": "Update failed."
    }
}

# --- 設定管理 ---
def load_settings():
    global app_settings, max_concurrent_downloads
    try:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                app_settings = json.load(f)
        else:
            app_settings = {
                "general": {"concurrentDownloads": 1, "showWelcomeNotice": True},
                "last_options": {"savePath": DOWNLOADS_DIR}
            }
            save_settings()
        max_concurrent_downloads = app_settings.get('general', {}).get('concurrentDownloads', 1)
    except Exception as e: print(f"Error loading settings: {e}")

def save_settings():
    try:
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(app_settings, f, indent=4)
    except Exception as e: print(f"Error saving settings: {e}")

# --- yt-dlp管理 ---
def download_yt_dlp(force_update=False):
    if not force_update and os.path.exists(YT_DLP_PATH): return True
    if force_update and os.path.exists(YT_DLP_PATH):
        try: os.remove(YT_DLP_PATH)
        except OSError: return False
    print("Downloading yt-dlp.exe...")
    try:
        response = requests.get(YT_DLP_LATEST_RELEASE_URL, timeout=15)
        response.raise_for_status()
        asset_url = next((asset['browser_download_url'] for asset in response.json().get('assets', []) if asset['name'] == 'yt-dlp.exe'), None)
        if not asset_url: return False
        with requests.get(asset_url, stream=True) as r:
            r.raise_for_status()
            with open(YT_DLP_PATH, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192): f.write(chunk)
        return True
    except Exception as e: 
        print(f"Error downloading yt-dlp: {e}")
        return False

def get_yt_dlp_version():
    if not os.path.exists(YT_DLP_PATH): return "Not Found"
    try:
        result = subprocess.run([YT_DLP_PATH, '--version'], capture_output=True, text=True, check=True, timeout=10, creationflags=subprocess.CREATE_NO_WINDOW)
        return result.stdout.strip()
    except Exception: return "Error"

# --- ダウンロード処理 ---
def parse_progress(line):
    match = re.search(r'\[download\]\s+([\d\.]+)% of\s+~?(.+?)\s+at\s+(.+?)\s+ETA\s+(.+)', line)
    if match:
        return {'progress': float(match.group(1)), 'details': f"of {match.group(2)} at {match.group(3)} ETA {match.group(4)}"}
    return None

def run_download_process(item_id):
    with queue_lock:
        item = download_queue.get(item_id)
        if not item: return
        item['status'] = 'downloading'
        socketio.emit('item_update', {'item': item})

    options = item.get('options', {})
    save_path = options.get('savePath', DOWNLOADS_DIR)
    output_template = os.path.join(save_path, '%(title)s.%(ext)s')
    
    command = [YT_DLP_PATH, item['url'], '--progress', '-o', output_template, '--windows-filenames']
    custom_args_str = options.get('customArgs', '')
    
    if options.get('audioOnly'):
        command.extend(['-x', '--audio-format', options.get('audioFormat', 'best'), '-f', 'bestaudio/best'])
    elif options.get('videoFormat'):
        command.extend(['-f', options.get('videoFormat')])
    
    custom_args_list = shlex.split(custom_args_str)
    has_custom_cookie_arg = any(arg.lstrip('-') in ('cookies', 'cookies-from-browser') for arg in custom_args_list)
    if not has_custom_cookie_arg and options.get('cookieBrowser') != 'none':
        command.extend(['--cookies-from-browser', options.get('cookieBrowser')])
    command.extend(custom_args_list)
    
    process = None
    try:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8', errors='ignore', creationflags=subprocess.CREATE_NO_WINDOW)
        with queue_lock:
            active_processes[item_id] = process
        
        for line in iter(process.stdout.readline, ''):
            progress_data = parse_progress(line)
            if progress_data:
                item.update(progress_data)
                socketio.emit('download_progress', {'id': item_id, 'progress': item['progress'], 'details': item['details']})
        process.wait()
        
        with queue_lock:
            if item_id not in download_queue: return
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
    with queue_lock:
        downloading_count = sum(1 for item in download_queue.values() if item['status'] == 'downloading')
        if downloading_count >= max_concurrent_downloads: return
        waiting_item = next((item for item in download_queue.values() if item['status'] == 'waiting'), None)
        if waiting_item:
            socketio.start_background_task(target=run_download_process, item_id=waiting_item['id'])

# --- ルーティング ---
@app.route('/')
def index(): 
    lang = 'ja'
    accept_language = request.headers.get('Accept-Language')
    if accept_language and accept_language.lower().startswith('en'):
        lang = 'en'
    
    # --- ★★★ ここからが修正点 ★★★ ---
    if not app_settings:
        load_settings()
    show_welcome = app_settings.get('general', {}).get('showWelcomeNotice', True)
    
    return render_template('index.html', t=translations[lang], lang=lang, show_welcome_notice=show_welcome)
    # --- ★★★ ここまでが修正点 ★★★ ---

@app.route('/select-folder', methods=['POST'])
def select_folder():
    try:
        result = subprocess.run([sys.executable, os.path.join(BASE_DIR, 'folder_selector.py')], capture_output=True, text=True, check=True, encoding='utf-8')
        return {'folder_path': result.stdout.strip()}
    except Exception as e:
        print(f"Error opening folder dialog: {e}")
        return {'folder_path': ''}

@app.route('/open-folder', methods=['POST'])
def open_folder():
    path = request.get_json().get('path')
    if path and os.path.isdir(path):
        try:
            os.startfile(path)
            return {'status': 'OK'}
        except Exception as e:
            return {'status': 'Error', 'message': str(e)}, 500
    return {'status': 'Error', 'message': 'Path not found'}, 400

# --- WebSocketイベント ---
@socketio.on('connect')
def handle_connect():
    emit('version_info', {'version': get_yt_dlp_version()})
    emit('queue_update', {'queue': download_queue})
    emit('settings_loaded', {'settings': app_settings})

@socketio.on('add_to_queue')
def handle_add_to_queue(data):
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
    global app_settings, max_concurrent_downloads
    app_settings = data.get('settings', {})
    max_concurrent_downloads = app_settings.get('general', {}).get('concurrentDownloads', 1)
    save_settings()
    emit('settings_saved', {'message_key': 'settings_saved'})
    start_next_download()

@socketio.on('update_yt_dlp')
def handle_update_yt_dlp():
    emit('update_status', {'message_key': 'update_status_updating'})
    if download_yt_dlp(force_update=True):
        new_version = get_yt_dlp_version()
        emit('update_status', {'message_key': 'update_status_complete', 'version': new_version})
        emit('version_info', {'version': new_version})
    else:
        emit('update_status', {'message_key': 'update_status_failed'})

@socketio.on('remove_item')
def handle_remove_item(data):
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
    with queue_lock:
        ids_to_remove = [item_id for item_id, item in download_queue.items() if item['status'] != 'downloading']
        for item_id in ids_to_remove:
            download_queue.pop(item_id, None)
    emit('queue_update', {'queue': download_queue}, broadcast=True)

# --- メイン処理 ---
def setup_directories():
    for dir_path in [TOOLS_DIR, DOWNLOADS_DIR]:
        if not os.path.exists(dir_path): os.makedirs(dir_path)

if __name__ == '__main__':
    setup_directories()
    download_yt_dlp()
    load_settings()
    socketio.run(app, debug=True, host='127.0.0.1', port=5000)
