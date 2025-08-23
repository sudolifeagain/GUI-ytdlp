import tkinter as tk
from tkinter import filedialog

def main():
    """Tkinterを使用してフォルダ選択ダイアログを表示し、選択されたパスを標準出力に出力する"""
    try:
        root = tk.Tk()
        root.withdraw()  # メインウィンドウを非表示にする
        root.attributes('-topmost', True)  # ダイアログを最前面に表示
        
        # フォルダ選択ダイアログを表示
        folder_path = filedialog.askdirectory(title="保存先フォルダを選択してください")
        
        # 選択されたパスを標準出力に出力
        if folder_path:
            print(folder_path)
            
    except Exception as e:
        import sys
        print(f"Error in folder selector: {e}", file=sys.stderr)
    finally:
        if 'root' in locals() and root:
            root.destroy()

if __name__ == "__main__":
    main()
