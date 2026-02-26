/**
 * API client - fetch wrappers for all Resume Builder endpoints.
 */
const API = {
    base: '',

    async _fetch(url, options = {}) {
        const resp = await fetch(this.base + url, {
            headers: { 'Content-Type': 'application/json', ...options.headers },
            ...options,
        });
        if (!resp.ok) {
            const err = await resp.json().catch(() => ({ detail: resp.statusText }));
            throw new Error(err.detail || resp.statusText);
        }
        return resp.json();
    },

    // Repertoire
    getRepertoire() { return this._fetch('/api/repertoire'); },

    createSection(name, sectionType = 'standard') {
        return this._fetch('/api/repertoire/sections', {
            method: 'POST', body: JSON.stringify({ name, section_type: sectionType }),
        });
    },
    updateSection(id, data) {
        return this._fetch(`/api/repertoire/sections/${id}`, {
            method: 'PUT', body: JSON.stringify(data),
        });
    },
    deleteSection(id) {
        return this._fetch(`/api/repertoire/sections/${id}`, { method: 'DELETE' });
    },

    createTitle(sectionId, data) {
        return this._fetch(`/api/repertoire/titles/${sectionId}`, {
            method: 'POST', body: JSON.stringify(data),
        });
    },
    updateTitle(id, data) {
        return this._fetch(`/api/repertoire/titles/${id}`, {
            method: 'PUT', body: JSON.stringify(data),
        });
    },
    deleteTitle(id) {
        return this._fetch(`/api/repertoire/titles/${id}`, { method: 'DELETE' });
    },

    createItem(titleId, text) {
        return this._fetch(`/api/repertoire/items/${titleId}`, {
            method: 'POST', body: JSON.stringify({ text }),
        });
    },
    updateItem(id, text) {
        return this._fetch(`/api/repertoire/items/${id}`, {
            method: 'PUT', body: JSON.stringify({ text }),
        });
    },
    deleteItem(id) {
        return this._fetch(`/api/repertoire/items/${id}`, { method: 'DELETE' });
    },

    // Active Resume
    getActive() { return this._fetch('/api/active'); },
    getActiveRaw() { return this._fetch('/api/active/raw'); },

    addActiveSection(sectionId) {
        return this._fetch('/api/active/sections', {
            method: 'POST', body: JSON.stringify({ section_id: sectionId }),
        });
    },
    removeActiveSection(sectionId) {
        return this._fetch(`/api/active/sections/${sectionId}`, { method: 'DELETE' });
    },

    addActiveTitle(sectionId, titleId) {
        return this._fetch(`/api/active/sections/${sectionId}/titles`, {
            method: 'POST', body: JSON.stringify({ title_id: titleId }),
        });
    },
    removeActiveTitle(sectionId, titleId) {
        return this._fetch(`/api/active/sections/${sectionId}/titles/${titleId}`, { method: 'DELETE' });
    },

    addActiveItem(titleId, itemId) {
        return this._fetch(`/api/active/titles/${titleId}/items`, {
            method: 'POST', body: JSON.stringify({ item_id: itemId }),
        });
    },
    removeActiveItem(titleId, itemId) {
        return this._fetch(`/api/active/titles/${titleId}/items/${itemId}`, { method: 'DELETE' });
    },

    // Reorder
    reorderSections(id, newIndex) {
        return this._fetch('/api/active/sections/reorder', {
            method: 'POST', body: JSON.stringify({ id, new_index: newIndex }),
        });
    },
    reorderTitles(sectionId, id, newIndex) {
        return this._fetch(`/api/active/sections/${sectionId}/titles/reorder`, {
            method: 'POST', body: JSON.stringify({ id, new_index: newIndex }),
        });
    },
    reorderItems(titleId, id, newIndex) {
        return this._fetch(`/api/active/titles/${titleId}/items/reorder`, {
            method: 'POST', body: JSON.stringify({ id, new_index: newIndex }),
        });
    },

    // Tweaks
    setTweak(targetId, field, value) {
        return this._fetch(`/api/active/tweaks/${targetId}`, {
            method: 'PUT', body: JSON.stringify({ field, value }),
        });
    },
    clearTweak(targetId) {
        return this._fetch(`/api/active/tweaks/${targetId}`, { method: 'DELETE' });
    },
    commitTweak(targetId) {
        return this._fetch(`/api/active/tweaks/${targetId}/commit`, { method: 'POST' });
    },
    getTweaks() { return this._fetch('/api/active/tweaks'); },

    // Compile
    compile() { return this._fetch('/api/compile', { method: 'POST' }); },
    getPreviewUrl() { return this.base + '/api/compile/preview'; },
    getTex() { return this._fetch('/api/compile/tex'); },

    // Import/Export
    importTex() { return this._fetch('/api/import/tex', { method: 'POST' }); },
    exportTex() { return this._fetch('/api/export/tex'); },

    // Tailoring
    getTailorState() { return this._fetch('/api/tailor/state'); },
    applyTailor(actions) {
        return this._fetch('/api/tailor/apply', {
            method: 'POST', body: JSON.stringify({ actions }),
        });
    },
    clearTweaks() { return this._fetch('/api/tailor/clear-tweaks', { method: 'POST' }); },

    // JD Analysis
    analyzeJD(text) {
        return this._fetch('/api/jd/analyze', {
            method: 'POST', body: JSON.stringify({ text }),
        });
    },
    getCurrentJD() { return this._fetch('/api/jd/current'); },
    clearJD() { return this._fetch('/api/jd/current', { method: 'DELETE' }); },
    scrapeJD(url) {
        return this._fetch('/api/jd/scrape', {
            method: 'POST', body: JSON.stringify({ url }),
        });
    },

    // Version History
    getItemHistory(id) { return this._fetch(`/api/repertoire/items/${id}/history`); },
    restoreItem(id, versionIndex) {
        return this._fetch(`/api/repertoire/items/${id}/restore`, {
            method: 'POST', body: JSON.stringify({ version_index: versionIndex }),
        });
    },
    branchItem(id, label) {
        return this._fetch(`/api/repertoire/items/${id}/branch`, {
            method: 'POST', body: JSON.stringify({ label }),
        });
    },
    getTitleHistory(id) { return this._fetch(`/api/repertoire/titles/${id}/history`); },
    restoreTitle(id, versionIndex) {
        return this._fetch(`/api/repertoire/titles/${id}/restore`, {
            method: 'POST', body: JSON.stringify({ version_index: versionIndex }),
        });
    },
    branchTitle(id, label) {
        return this._fetch(`/api/repertoire/titles/${id}/branch`, {
            method: 'POST', body: JSON.stringify({ label }),
        });
    },
};
