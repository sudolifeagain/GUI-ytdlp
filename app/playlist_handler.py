import yt_dlp
from typing import Dict, List, Any

class PlaylistHandler:
    """プレイリスト処理専用クラス"""
    
    @classmethod
    def get_playlist_info(cls, url, cookie_browser='none', max_entries=100):
        """プレイリスト情報を取得"""
        ydl_opts = {
            'quiet': True,
            'skip_download': True,
            'extract_flat': True,
            'playlistend': max_entries
        }
        
        if cookie_browser != 'none':
            ydl_opts['cookiesfrombrowser'] = (cookie_browser,)
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                entries = info.get('entries', [])
                processed_entries = []
                
                for i, entry in enumerate(entries):
                    if i >= max_entries:
                        break
                    
                    processed_entries.append({
                        'title': entry.get('title', f'動画 {i+1}'),
                        'url': entry.get('url', entry.get('webpage_url', '')),
                        'duration': entry.get('duration'),
                        'id': entry.get('id', ''),
                        'uploader': entry.get('uploader', ''),
                        'view_count': entry.get('view_count'),
                        'upload_date': entry.get('upload_date')
                    })
                
                return {
                    'success': True,
                    'title': info.get('title', 'プレイリスト'),
                    'uploader': info.get('uploader', '不明'),
                    'entry_count': len(processed_entries),
                    'total_entries': info.get('playlist_count', len(processed_entries)),
                    'entries': processed_entries,
                    'description': info.get('description', '')[:200] + '...' if info.get('description') else ''
                }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @classmethod
    def filter_playlist_entries(cls, entries: List[Dict], selected_ids: List[str]) -> List[Dict]:
        """選択されたエントリのみをフィルタリング"""
        if not selected_ids:
            return entries
        
        return [entry for entry in entries if entry.get('id') in selected_ids]

    @classmethod
    def build_playlist_download_options(cls, item):
        """プレイリストダウンロード用のオプションを構築"""
        options = item.get('options', {})
        
        # 基本オプション
        playlist_options = options.copy()
        
        # プレイリスト特有の設定
        if item.get('playlist_mode') == 'selected':
            # 選択された動画のみダウンロード
            selected_entries = item.get('selected_entries', [])
            if selected_entries:
                playlist_options['playlist_items'] = ','.join([str(i+1) for i, entry in enumerate(item.get('all_entries', [])) if entry.get('id') in selected_entries])
        
        return playlist_options