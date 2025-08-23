## activate venv

python -m venv venv

pip install Flask Flask-SocketIO requests

source venv/Scripts/activate

python main.py


/GUI-ytdlp
│
├── app/
│   ├── __init__.py
│   ├── views.py
│   ├── sockets.py
│   ├── ytdlp_handler.py
│   └── settings_handler.py
│
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       ├── main.js
│       ├── ui.js
│       ├── socket.js
│       ├── api.js
│       └── state.js
│
├── templates/
│   └── index.html
│
├── tools/
│
├── run.py
├── folder_selector.py
└── settings.json