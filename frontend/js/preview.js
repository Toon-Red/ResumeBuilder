/**
 * PDF preview panel - always visible on the right side.
 */
const Preview = {
    _iframe: null,

    init() {
        this._iframe = document.getElementById('pdf-iframe');
    },

    refresh() {
        // Cache-bust the PDF URL
        this._iframe.src = API.getPreviewUrl() + '?t=' + Date.now();
    },

    clear() {
        this._iframe.src = '';
    },
};
