// アプリケーションの共有状態を管理するモジュール
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
