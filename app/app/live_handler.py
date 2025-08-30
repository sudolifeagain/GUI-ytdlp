import yt_dlp
import os
from .ytdlp_handler import YT_DLP_PATH, DOWNLOADS_DIR

class LiveHandler:
    """YouTube Live配信処理専用クラス"""
    
    @classmethod
    def check_live_status(cls, url, cookie_browser='none'):
        """ライブ配信の状態をチェック"""
        ydl_opts = {
            'quiet': True,
            'skip_download': True,
            'extract_flat': True
        }
        
        if cookie_browser != 'none':
            ydl_opts['cookiesfrombrowser'] = (cookie_browser,)
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                return {
                    'is_live': info.get('is_live', False),
                    'was_live': info.get('was_live', False),
                    'live_status': info.get('live_status'),
                    'title': info.get('title', ''),
                    'duration': info.get('duration'),
                    'start_time': info.get('release_timestamp'),
                    'uploader': info.get('uploader', ''),
                    'description': info.get('description', '')[:200] + '...' if info.get('description', '') else ''
                }
        except Exception as e:
            return {'error': str(e)}

    @classmethod
    def build_live_download_command(cls, item):
        """ライブ配信用のダウンロードコマンドを構築"""
        options = item.get('options', {})
        save_path = options.get('savePath', DOWNLOADS_DIR)
        
        # ライブ配信用の特別なテンプレート
        output_template = os.path.join(save_path, '%(title)s_%(upload_date)s_%(id)s.%(ext)s')
        
        command = [
            YT_DLP_PATH, item['url'], 
            '--progress',
            '-o', output_template,
            '--windows-filenames',
        ]
        
        # ライブ配信モードに応じた設定
        live_mode = options.get('liveMode', 'wait')
        if live_mode == 'wait':
            command.extend(['--live-from-start', '--wait-for-video', '30'])
        elif live_mode == 'now':
            command.append('--no-wait-for-video')
        elif live_mode == 'safe':
            command.extend(['-f', 'best[height<=720]', '--live-from-start'])
        
        # その他のオプション
        if options.get('selectedFormat') and live_mode != 'safe':
            command.extend(['-f', options.get('selectedFormat')])
        
        return command

    @classmethod
    def get_live_formats(cls, url, cookie_browser='none'):
        """ライブ配信の利用可能フォーマットを取得"""
        # 基本的には通常の動画と同じだが、ライブ特有の制限を考慮
        from .ytdlp_handler import get_available_formats
        result = get_available_formats(url, cookie_browser)
        
        if result.get('success'):
            # ライブ配信では一部フォーマットが制限される場合がある
            formats = result.get('formats', [])
            live_compatible_formats = []
            
            for fmt in formats:
                # 高解像度は不安定になりやすいので警告を追加
                if fmt.get('resolution', '').startswith(('1080', '1440', '2160')):
                    fmt['note'] = fmt.get('note', '') + ' [ライブでは不安定になる可能性あり]'
                live_compatible_formats.append(fmt)
            
            result['formats'] = live_compatible_formats
        
        return result