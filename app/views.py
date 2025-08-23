# ファイル: app/views.py
from flask import render_template, request, jsonify, Blueprint
import subprocess
import os
from . import ytdlp_handler, settings_handler
from .translations import translations

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index(): 
    lang = 'ja'
    accept_language = request.headers.get('Accept-Language')
    if accept_language and accept_language.lower().startswith('en'):
        lang = 'en'
    
    show_welcome = settings_handler.get_setting('general', {}).get('showWelcomeNotice', True)
    
    return render_template('index.html', t=translations[lang], lang=lang, show_welcome_notice=show_welcome)

@main_bp.route('/api/formats', methods=['POST'])
def get_formats_api():
    """動画URLから利用可能なフォーマット一覧を取得するAPI"""
    url = request.json.get('url')
    if not url:
        return jsonify({'success': False, 'error': 'URL is required'}), 400
    
    result = ytdlp_handler.get_available_formats(url)
    return jsonify(result)

@main_bp.route('/select-folder', methods=['POST'])
def select_folder():
    import sys
    import os
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    try:
        result = subprocess.run([sys.executable, os.path.join(BASE_DIR, 'folder_selector.py')], capture_output=True, text=True, check=True, encoding='utf-8')
        return {'folder_path': result.stdout.strip()}
    except Exception as e:
        print(f"Error opening folder dialog: {e}")
        return {'folder_path': ''}

@main_bp.route('/open-folder', methods=['POST'])
def open_folder():
    path = request.get_json().get('path')
    if path and os.path.isdir(path):
        try:
            os.startfile(path)
            return {'status': 'OK'}
        except Exception as e:
            return {'status': 'Error', 'message': str(e)}, 500
    return {'status': 'Error', 'message': 'Path not found'}, 400
