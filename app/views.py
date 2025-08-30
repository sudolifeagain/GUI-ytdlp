from flask import render_template, request, jsonify, Blueprint
import subprocess
import os
from . import ytdlp_handler, settings_handler
from .translations import translations
from .content_analyzer import ContentAnalyzer

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index(): 
    # ブラウザの言語設定から言語を判定
    lang = 'ja'
    accept_language = request.headers.get('Accept-Language')
    if accept_language and accept_language.lower().startswith('en'):
        lang = 'en'
    
    show_welcome = settings_handler.get_setting('general', {}).get('showWelcomeNotice', True)
    
    return render_template('index.html', t=translations[lang], lang=lang, show_welcome_notice=show_welcome)

@main_bp.route('/api/analyze-url', methods=['POST'])
def analyze_url_api():
    """URLを分析して種類と詳細情報を取得"""
    data = request.json
    url = data.get('url')
    cookie_browser = data.get('cookieBrowser', 'none')
    
    if not url:
        return jsonify({'success': False, 'error': 'URL is required'}), 400
    
    result = ContentAnalyzer.analyze_url(url, cookie_browser)
    return jsonify(result)

@main_bp.route('/api/formats', methods=['POST'])
def get_formats_api():
    """動画URLから利用可能なフォーマット一覧を取得するAPI"""
    data = request.json
    url = data.get('url')
    cookie_browser = data.get('cookieBrowser', 'none')
    
    if not url:
        return jsonify({'success': False, 'error': 'URL is required'}), 400
    
    # コンテンツタイプに応じた処理
    content_type = ContentAnalyzer.detect_content_type(url)
    
    if content_type == 'live':
        from .live_handler import LiveHandler
        result = LiveHandler.get_live_formats(url, cookie_browser)
    else:
        result = ytdlp_handler.get_available_formats(url, cookie_browser)
    
    return jsonify(result)

@main_bp.route('/select-folder', methods=['POST'])
def select_folder():
    """フォルダ選択ダイアログを開く"""
    import sys
    import os
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    try:
        result = subprocess.run([sys.executable, os.path.join(BASE_DIR, 'folder_selector.py')], 
                              capture_output=True, text=True, check=True, encoding='utf-8')
        return {'folder_path': result.stdout.strip()}
    except Exception as e:
        print(f"Error opening folder dialog: {e}")
        return {'folder_path': ''}

@main_bp.route('/open-folder', methods=['POST'])
def open_folder():
    """指定されたフォルダをエクスプローラーで開く"""
    path = request.get_json().get('path')
    if path and os.path.isdir(path):
        try:
            # Windowsでフォルダの内部を最前面で開く
            subprocess.Popen(['explorer', path], shell=True)
            return {'status': 'OK'}
        except Exception as e:
            # フォールバック: 通常の方法で開く
            try:
                os.startfile(path)
                return {'status': 'OK'}
            except Exception as fallback_error:
                return {'status': 'Error', 'message': str(fallback_error)}, 500
    return {'status': 'Error', 'message': 'Path not found'}, 400
