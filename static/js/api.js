
// ファイル: static/js/api.js
// Handles API communication other than WebSockets.
export async function fetchFormats(url) {
    try {
        const response = await fetch('/api/formats', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url })
        });
        if (!response.ok) {
            // 404などのエラーレスポンスを処理
            return { success: false, error: `Server returned ${response.status}` };
        }
        return await response.json();
    } catch (error) {
        console.error('Error fetching formats:', error);
        return { success: false, error: 'Failed to connect to the server.' };
    }
}

export async function selectFolder() {
    const response = await fetch('/select-folder', { method: 'POST' });
    const data = await response.json();
    return data.folder_path;
}

export async function openFolder(path) {
    await fetch('/open-folder', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path: path }),
    });
}