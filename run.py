import os
import sys
import logging
from app import create_app

def main():
    """アプリケーションのメイン実行関数"""
    try:
        # 環境変数から設定を読み込み（デフォルト値付き）
        debug = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
        host = os.getenv('FLASK_HOST', '127.0.0.1')
        port = int(os.getenv('FLASK_PORT', '5000'))
        
        # ログレベルを設定
        log_level = logging.DEBUG if debug else logging.INFO
        logging.basicConfig(level=log_level)
        
        # アプリケーションを作成
        app, socketio = create_app()
        
        # サーバーを起動
        print(f"Starting server on {host}:{port} (debug={debug})")
        socketio.run(app, debug=debug, host=host, port=port)
        
    except ImportError as e:
        print(f"Failed to import required modules: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"Invalid configuration value: {e}", file=sys.stderr)
        sys.exit(1)
    except OSError as e:
        print(f"Failed to start server (port {port} might be in use): {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
