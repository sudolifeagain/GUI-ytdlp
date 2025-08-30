@echo off

REM 仮想環境の有効化
call venv\Scripts\activate.bat

REM アプリケーションの起動
start python run.py

REM サーバー起動待機
timeout /t 5 >nul

REM ブラウザでURLを開く
start http://127.0.0.1:5000
