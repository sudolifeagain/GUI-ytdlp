// ファイル: static/js/state.js
// Holds the shared state for the application.
export const state = {
    settings: {},
    lang: 'ja',
    translations: {}
};

export function setSettings(newSettings) {
    state.settings = newSettings;
}

export function initializeTranslations(lang, translations) {
    state.lang = lang;
    state.translations = translations;
}
