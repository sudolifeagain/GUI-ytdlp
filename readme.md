# GUI-ytdlp

yt-dlpのWebインターフェースを提供するFlask/Socket.IOベースのアプリケーション

## ファイル構造

```
/GUI-ytdlp
├── app/                    # メインアプリケーション
│   ├── __init__.py        # Flaskアプリファクトリ
│   ├── views.py           # HTTP APIエンドポイント
│   ├── sockets.py         # WebSocket通信ハンドラー
│   ├── ytdlp_handler.py   # yt-dlp操作・フォーマット処理
│   ├── settings_handler.py # 設定管理
│   └── translations.py    # 多言語対応
│
├── static/                # 静的ファイル
│   ├── css/
│   │   └── style.css     # メインスタイル
│   └── js/               # モジュラーJavaScript
│       ├── main.js       # エントリーポイント
│       ├── ui.js         # UI操作・レンダリング
│       ├── socket.js     # WebSocket通信
│       ├── api.js        # HTTP API通信
│       └── state.js      # アプリケーション状態管理
│
├── templates/
│   └── index.html        # メインテンプレート
│
├── tools/                # 外部ツール（自動ダウンロード）
├── downloads/            # ダウンロードファイル保存先
├── venv/                 # Python仮想環境
│
├── run.py                # アプリケーション起動スクリプト
├── folder_selector.py    # フォルダ選択ダイアログ
└── settings.json         # ユーザー設定ファイル
```

## セットアップ

### 1. 仮想環境の作成・有効化
```bash
python -m venv venv
venv\Scripts\activate  # Windows
```

### 2. 依存関係のインストール
```bash
pip install Flask Flask-SocketIO requests yt-dlp
```

### 3. 起動
```bash
python run.py
```

<http://127.0.0.1:5000> にアクセス

## 主要機能

- 動画・音声ダウンロード（YouTube等対応サイト）
- リアルタイム進捗表示
- 並列ダウンロード
- 詳細フォーマット選択
- Cookie対応（ログイン必要動画）
- 多言語対応（日本語・英語）

## トラブルシューティング

### フォーマット取得エラー
- フォーマット取得で利用可能な選択肢を確認
- 音声のみダウンロードを試す

### Cookie関連エラー
- ChromeからFirefoxに変更（推奨）
- Cookie設定の「?」ボタンで詳細情報を確認

