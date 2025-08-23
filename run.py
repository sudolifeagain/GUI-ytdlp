# ファイル: run.py
from app import create_app

app, socketio = create_app()

if __name__ == '__main__':
    socketio.run(app, debug=True, host='127.0.0.1', port=5000)
