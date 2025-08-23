import tkinter as tk
from tkinter import filedialog

def main():
    """
    Tkinterを使用してフォルダ選択ダイアログを表示し、
    選択されたパスを標準出力に出力する。
    """
    try:
        root = tk.Tk()
        root.withdraw()  # メインウィンドウを非表示にする
        
        # ★★★ 修正点: ダイアログを常に最前面に表示する設定を追加 ★★★
        root.attributes('-topmost', True)
        
        # フォルダ選択ダイアログを表示
        folder_path = filedialog.askdirectory(
            title="保存先フォルダを選択してください"
        )
        
        # 選択されたパスを標準出力に出力
        if folder_path:
            print(folder_path)
            
    except Exception as e:
        # エラーが発生した場合は標準エラー出力に書き出す
        import sys
        print(f"Error in folder selector: {e}", file=sys.stderr)
    finally:
        # Tkinterのプロセスを確実に終了させる
        if 'root' in locals() and root:
            root.destroy()

if __name__ == "__main__":
    main()
