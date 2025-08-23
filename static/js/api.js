// HTTP API通信を管理するモジュール（WebSocket以外）
export async function fetchFormats(url) {
    try {
        const cookieBrowser = document.getElementById('cookie-browser')?.value || 'none';
        
        const response = await fetch('/api/formats', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ 
                url: url,
                cookieBrowser: cookieBrowser 
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('Error fetching formats:', error);
        return { success: false, error: error.message };
    }
}

export async function selectFolder() {
    try {
        const response = await fetch('/select-folder', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        return data.folder_path || '';
    } catch (error) {
        console.error('Error selecting folder:', error);
        return '';
    }
}

export async function openFolder(path) {
    if (!path) return;
    
    try {
        const response = await fetch('/open-folder', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ path: path })
        });
        
        if (!response.ok) {
            console.error('Failed to open folder');
        }
    } catch (error) {
        console.error('Error opening folder:', error);
    }
}