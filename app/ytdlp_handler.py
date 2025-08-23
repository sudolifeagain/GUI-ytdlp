# ファイル: app/ytdlp_handler.py
import os
import subprocess
import requests
import re
import shlex
import yt_dlp

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS_DIR = os.path.join(BASE_DIR, 'tools')
DOWNLOADS_DIR = os.path.join(BASE_DIR, 'downloads')
YT_DLP_PATH = os.path.join(TOOLS_DIR, 'yt-dlp.exe')
YT_DLP_LATEST_RELEASE_URL = 'https://api.github.com/repos/yt-dlp/yt-dlp/releases/latest'

active_processes = {}

def setup_directories():
    for dir_path in [TOOLS_DIR, DOWNLOADS_DIR]:
        if not os.path.exists(dir_path): os.makedirs(dir_path)

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

def get_available_formats(url):
    """指定されたURLから利用可能なフォーマット一覧を取得する"""
    ydl_opts = {
        'quiet': True, 
        'skip_download': True, 
        'noplaylist': True,
        'no_warnings': True
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = []
            
            # 動画フォーマット（音声なし）を取得
            video_formats = []
            for f in info.get('formats', []):
                if (f.get('vcodec') != 'none' and f.get('acodec') == 'none'):
                    video_formats.append({
                        'id': f['format_id'],
                        'ext': f['ext'],
                        'resolution': f.get('height', 0),
                        'width': f.get('width', 0),
                        'note': f.get('format_note', ''),
                        'fps': f.get('fps'),
                        'filesize': f.get('filesize') or f.get('filesize_approx'),
                        'vbr': f.get('vbr'),
                        'format_type': 'video'
                    })
            
            # 解像度順にソート
            video_formats.sort(key=lambda x: x['resolution'], reverse=True)
            
            # 最良の音声フォーマットを取得
            audio_formats = []
            for f in info.get('formats', []):
                if (f.get('acodec') != 'none' and f.get('vcodec') == 'none'):
                    audio_formats.append({
                        'id': f['format_id'],
                        'ext': f['ext'],
                        'abr': f.get('abr'),
                        'asr': f.get('asr'),
                        'format_type': 'audio'
                    })
            
            # 音質順にソート
            audio_formats.sort(key=lambda x: x.get('abr', 0), reverse=True)
            best_audio = audio_formats[0]['id'] if audio_formats else 'bestaudio'
            
            # 表示用のフォーマットリストを作成
            for vf in video_formats:
                size_str = ""
                if vf['filesize']:
                    size_mb = vf['filesize'] / 1024 / 1024
                    size_str = f" ({size_mb:.1f}MB)"
                
                fps_str = f" @{vf['fps']}fps" if vf['fps'] else ""
                note_str = f" - {vf['note']}" if vf['note'] else ""
                
                formats.append({
                    'id': f"{vf['id']}+{best_audio}",
                    'ext': vf['ext'],
                    'resolution': f"{vf['resolution']}p",
                    'note': f"{vf['ext'].upper()}{fps_str}{size_str}{note_str}",
                    'fps': vf['fps'],
                    'filesize': vf['filesize']
                })
            
            return {'success': True, 'formats': formats}
            
    except Exception as e:
        return {'success': False, 'error': str(e)}

def parse_progress(line):
    match = re.search(r'\[download\]\s+([\d\.]+)% of\s+~?(.+?)\s+at\s+(.+?)\s+ETA\s+(.+)', line)
    if match:
        return {'progress': float(match.group(1)), 'details': f"of {match.group(2)} at {match.group(3)} ETA {match.group(4)}"}
    return None

def build_download_command(item):
    options = item.get('options', {})
    save_path = options.get('savePath', DOWNLOADS_DIR)
    output_template = os.path.join(save_path, '%(title)s.%(ext)s')
    
    command = [YT_DLP_PATH, item['url'], '--progress', '-o', output_template, '--windows-filenames']
    custom_args_str = options.get('customArgs', '')
    
    selected_format = options.get('selectedFormat')
    if selected_format and selected_format != 'custom':
        command.extend(['-f', selected_format])
    elif options.get('audioOnly'):
        command.extend(['-x', '--audio-format', options.get('audioFormat', 'best'), '-f', 'bestaudio/best'])
    
    custom_args_list = shlex.split(custom_args_str)
    has_custom_cookie_arg = any(arg.lstrip('-') in ('cookies', 'cookies-from-browser') for arg in custom_args_list)
    if not has_custom_cookie_arg and options.get('cookieBrowser') != 'none':
        command.extend(['--cookies-from-browser', options.get('cookieBrowser')])
    command.extend(custom_args_list)
    return command
