import re
import yt_dlp
from datetime import datetime

class ContentAnalyzer:
    """URLからコンテンツの種類を判定・分析するクラス"""
    
    LIVE_PATTERNS = [
        r'youtube\.com/live/',
        r'youtube\.com/watch\?.*v=.*&.*t=.*',
        r'youtu\.be/.*\?.*t=.*'
    ]
    
    PLAYLIST_PATTERNS = [
        r'youtube\.com/playlist\?list=',
        r'youtube\.com/watch\?.*list=',
        r'youtube\.com/@.*/playlists',
        r'youtube\.com/c/.*/playlists'
    ]

    @classmethod
    def detect_content_type(cls, url):
        """URLからコンテンツタイプを判定"""
        for pattern in cls.LIVE_PATTERNS:
            if re.search(pattern, url, re.IGNORECASE):
                return 'live'
        
        for pattern in cls.PLAYLIST_PATTERNS:
            if re.search(pattern, url, re.IGNORECASE):
                return 'playlist'
        
        return 'single'

    @classmethod
    def analyze_url(cls, url, cookie_browser='none'):
        """URLを分析して詳細情報を取得"""
        content_type = cls.detect_content_type(url)
        
        result = {
            'success': True,
            'url': url,
            'content_type': content_type,
            'analyzed_at': datetime.now().isoformat()
        }
        
        try:
            if content_type == 'live':
                from .live_handler import LiveHandler
                live_info = LiveHandler.check_live_status(url, cookie_browser)
                result.update(live_info)
            elif content_type == 'playlist':
                from .playlist_handler import PlaylistHandler
                playlist_info = PlaylistHandler.get_playlist_info(url, cookie_browser)
                result.update(playlist_info)
            else:
                from .ytdlp_handler import get_available_formats
                format_info = get_available_formats(url, cookie_browser)
                result.update(format_info)
                
        except Exception as e:
            result.update({'success': False, 'error': str(e)})
        
        return result