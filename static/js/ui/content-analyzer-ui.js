import { formatDuration } from '../utils.js';

export class ContentAnalyzerUI {
    constructor() {
        this.resultDiv = document.getElementById('url-analysis-result');
        this.contentTypeDiv = document.getElementById('content-type-info');
        this.setupElements();
    }

    setupElements() {
        // URL解析結果表示エリアを動的に作成
        if (!this.resultDiv) {
            this.resultDiv = this.createAnalysisResultDiv();
            const urlInputArea = document.querySelector('.url-input-area');
            urlInputArea.appendChild(this.resultDiv);
        }
    }

    createAnalysisResultDiv() {
        const div = document.createElement('div');
        div.id = 'url-analysis-result';
        div.style.display = 'none';
        div.innerHTML = `
            <div id="content-type-info"></div>
            <div id="live-status-info" style="display: none;"></div>
            <div id="playlist-info" style="display: none;"></div>
        `;
        return div;
    }

    showAnalysisResult(result) {
        this.contentTypeDiv = document.getElementById('content-type-info');
        this.resultDiv.style.display = 'block';
        
        // 全ての特定UI を非表示
        document.getElementById('live-status-info').style.display = 'none';
        document.getElementById('playlist-info').style.display = 'none';
        
        if (result.content_type === 'live') {
            this.showLiveContent(result);
        } else if (result.content_type === 'playlist') {
            this.showPlaylistContent(result);
        } else {
            this.showSingleVideoContent(result);
        }
    }

    showLiveContent(result) {
        this.contentTypeDiv.innerHTML = `<strong>🔴 ライブ配信</strong>: ${result.title || 'タイトル取得中...'}`;
        
        const liveStatusDiv = document.getElementById('live-status-info');
        const statusText = result.is_live ? '配信中' : 
                          result.was_live ? '配信終了' : '配信予定';
        
        liveStatusDiv.innerHTML = `
            <h4>ライブ配信情報</h4>
            <div class="live-details">
                <p>状態: <span class="status-${result.live_status}">${statusText}</span></p>
                <p>投稿者: ${result.uploader || '不明'}</p>
                ${result.start_time ? `<p>開始予定: ${new Date(result.start_time * 1000).toLocaleString()}</p>` : ''}
                ${result.duration ? `<p>長さ: ${formatDuration(result.duration)}</p>` : ''}
                ${result.description ? `<p>説明: ${result.description}</p>` : ''}
            </div>
            <div class="live-options">
                <h5>録画オプション:</h5>
                <label>
                    <input type="radio" name="live-mode" value="wait" checked>
                    配信開始まで待機してから録画開始
                </label>
                <label>
                    <input type="radio" name="live-mode" value="now">
                    現在の状態から録画開始
                </label>
                <label>
                    <input type="radio" name="live-mode" value="safe">
                    安定モード（720p制限）
                </label>
            </div>
        `;
        
        liveStatusDiv.style.display = 'block';
    }

    showPlaylistContent(result) {
        this.contentTypeDiv.innerHTML = `<strong>📋 プレイリスト</strong>: ${result.title || 'プレイリスト'}`;
        
        const playlistDiv = document.getElementById('playlist-info');
        playlistDiv.innerHTML = `
            <h4>プレイリスト情報</h4>
            <div class="playlist-details">
                <p>投稿者: ${result.uploader || '不明'}</p>
                <p>動画数: ${result.entry_count}件 ${result.total_entries !== result.entry_count ? `（全${result.total_entries}件中）` : ''}</p>
                ${result.description ? `<p>説明: ${result.description}</p>` : ''}
            </div>
            <div class="playlist-options">
                <label>
                    <input type="checkbox" id="download-all-playlist" checked>
                    プレイリスト全体をダウンロード（<span id="playlist-count">${result.entry_count}</span>件）
                </label>
                <div id="playlist-items" style="max-height: 200px; overflow-y: auto;">
                    <!-- プレイリストアイテム一覧 -->
                </div>
            </div>
        `;
        
        this.renderPlaylistItems(result.entries || []);
        playlistDiv.style.display = 'block';
    }

    showSingleVideoContent(result) {
        this.contentTypeDiv.innerHTML = `<strong>🎬 単一動画</strong>`;
        if (result.formats) {
            // フォーマット選択UIに反映
            import('../ui.js').then(ui => {
                ui.populateFormatSelector(result.formats);
            });
        }
    }

    renderPlaylistItems(entries) {
        const container = document.getElementById('playlist-items');
        if (!container) return;
        
        container.innerHTML = '';
        
        entries.forEach((entry, index) => {
            const item = document.createElement('div');
            item.className = 'playlist-item';
            item.innerHTML = `
                <label>
                    <input type="checkbox" class="playlist-item-checkbox" value="${entry.url}" data-id="${entry.id}" checked>
                    <span class="playlist-item-title">${entry.title || `動画 ${index + 1}`}</span>
                    <div class="playlist-item-meta">
                        ${entry.duration ? `<span class="duration">${formatDuration(entry.duration)}</span>` : ''}
                        ${entry.uploader ? `<span class="uploader">by ${entry.uploader}</span>` : ''}
                        ${entry.upload_date ? `<span class="upload-date">${formatUploadDate(entry.upload_date)}</span>` : ''}
                    </div>
                </label>
            `;
            container.appendChild(item);
        });
    }

    getSelectedPlaylistItems() {
        const checkboxes = document.querySelectorAll('.playlist-item-checkbox:checked');
        return Array.from(checkboxes).map(cb => cb.value);
    }

    getCurrentLiveMode() {
        const selected = document.querySelector('input[name="live-mode"]:checked');
        return selected ? selected.value : 'wait';
    }

    hideAnalysisResult() {
        this.resultDiv.style.display = 'none';
    }
}