
# ファイル: app/__init__.py
from flask import Flask
from flask_socketio import SocketIO

socketio = SocketIO(async_mode='threading')

def create_app():
    """Flaskアプリケーションを生成して返すファクトリ関数"""
    app = Flask(__name__, template_folder='../templates', static_folder='../static')
    app.config['SECRET_KEY'] = 'your_secret_key'

    socketio.init_app(app)

    # --- ★★★ ここからが修正点 ★★★ ---
    # viewsで定義したBlueprintをアプリケーションに登録
    from .views import main_bp
    app.register_blueprint(main_bp)
    # --- ★★★ ここまでが修正点 ★★★ ---

    with app.app_context():
        # 他モジュールのインポートと初期化
        from . import sockets
        from . import ytdlp_handler
        from . import settings_handler
        
        ytdlp_handler.setup_directories()
        ytdlp_handler.download_yt_dlp()
        settings_handler.load_settings()

    return app, socketio
