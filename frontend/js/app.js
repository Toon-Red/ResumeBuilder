/**
 * Main application - initialization, event handlers, state management.
 */
const App = {
    async init() {
        Editor.init();
        Preview.init();
        Vault.init();
        JD.init();
        History.init();

        document.getElementById('btn-import').onclick = () => this.importTex();
        document.getElementById('btn-compile').onclick = () => this.compile();
        document.getElementById('btn-export-pdf').onclick = () => this.exportPdf();
        document.getElementById('btn-save').onclick = () => this.save();
        document.getElementById('update-dismiss').onclick = () => {
            document.getElementById('update-banner').style.display = 'none';
        };

        // Ctrl+S saves PDF to Downloads
        document.addEventListener('keydown', (e) => {
            if ((e.ctrlKey || e.metaKey) && e.key === 's') {
                e.preventDefault();
                this.save();
            }
        });

        await this.refresh();
        this.checkForAppUpdate();
    },

    async refresh() {
        try {
            const [repertoire, active] = await Promise.all([
                API.getRepertoire(),
                API.getActive(),
            ]);

            Tree.renderVault(repertoire, document.getElementById('vault-tree'));
            Tree.renderActive(active, document.getElementById('active-tree'));
        } catch (err) {
            // Likely no data yet - that's ok
            console.log('Initial load:', err.message);
        }
    },

    async importTex() {
        this.showStatus('Importing...', '');
        try {
            const result = await API.importTex();
            this.showStatus(
                `Imported ${result.sections} sections, ${result.titles} titles, ${result.items} items`,
                'success'
            );
            await this.refresh();
        } catch (err) {
            this.showStatus('Import failed: ' + err.message, 'error');
        }
    },

    async compile() {
        this.showStatus('Compiling...', '');
        try {
            const result = await API.compile();
            if (result.success) {
                this.showStatus('PDF compiled successfully', 'success');
                Preview.refresh();
            } else {
                this.showStatus('Compile failed: ' + (result.error || 'Unknown error'), 'error');
                console.error('Compile log:', result.log);
            }
        } catch (err) {
            this.showStatus('Compile error: ' + err.message, 'error');
        }
    },

    async exportPdf() {
        this.showStatus('Compiling and downloading...', '');
        try {
            await API.exportPdf();
            this.showStatus('PDF downloaded', 'success');
        } catch (err) {
            this.showStatus('Export failed: ' + err.message, 'error');
        }
    },

    async save() {
        try {
            const result = await API.savePdf();
            if (result.ok) {
                this.showStatus('Saved to ' + result.path, 'success');
            } else {
                this.showStatus('Save failed: ' + (result.detail || 'Unknown error'), 'error');
            }
        } catch (err) {
            this.showStatus('Save error: ' + err.message, 'error');
        }
    },

    // --- Active resume mutations ---

    async addActiveSection(sectionId) {
        try {
            await API.addActiveSection(sectionId);
            // Also add all non-commented titles and items
            const rep = await API.getRepertoire();
            const section = rep.sections.find(s => s.id === sectionId);
            if (section) {
                for (const title of section.titles) {
                    if (!title.commented) {
                        await API.addActiveTitle(sectionId, title.id);
                        for (const item of title.items) {
                            if (!item.commented) {
                                await API.addActiveItem(title.id, item.id);
                            }
                        }
                    }
                }
            }
            await this.refresh();
        } catch (err) {
            this.showStatus('Error: ' + err.message, 'error');
        }
    },

    async removeActiveSection(sectionId) {
        try {
            await API.removeActiveSection(sectionId);
            await this.refresh();
        } catch (err) {
            this.showStatus('Error: ' + err.message, 'error');
        }
    },

    async addActiveTitle(sectionId, titleId) {
        try {
            await API.addActiveTitle(sectionId, titleId);
            // Also add all non-commented items
            const rep = await API.getRepertoire();
            for (const section of rep.sections) {
                const title = section.titles.find(t => t.id === titleId);
                if (title) {
                    for (const item of title.items) {
                        if (!item.commented) {
                            await API.addActiveItem(titleId, item.id);
                        }
                    }
                    break;
                }
            }
            await this.refresh();
        } catch (err) {
            this.showStatus('Error: ' + err.message, 'error');
        }
    },

    async removeActiveTitle(sectionId, titleId) {
        try {
            await API.removeActiveTitle(sectionId, titleId);
            await this.refresh();
        } catch (err) {
            this.showStatus('Error: ' + err.message, 'error');
        }
    },

    async addActiveItem(titleId, itemId, sectionId) {
        try {
            await API.addActiveItem(titleId, itemId);
            await this.refresh();
        } catch (err) {
            this.showStatus('Error: ' + err.message, 'error');
        }
    },

    async removeActiveItem(titleId, itemId) {
        try {
            await API.removeActiveItem(titleId, itemId);
            await this.refresh();
        } catch (err) {
            this.showStatus('Error: ' + err.message, 'error');
        }
    },

    async reorder(type, id, parentId, newIndex) {
        try {
            if (type === 'section') {
                await API.reorderSections(id, newIndex);
            } else if (type === 'title') {
                await API.reorderTitles(parentId, id, newIndex);
            } else if (type === 'item') {
                await API.reorderItems(parentId, id, newIndex);
            }
            await this.refresh();
        } catch (err) {
            this.showStatus('Reorder failed: ' + err.message, 'error');
        }
    },

    showStatus(msg, type) {
        const el = document.getElementById('status-msg');
        el.textContent = msg;
        el.className = 'status-msg' + (type ? ' ' + type : '');
        if (type === 'success') {
            setTimeout(() => { el.textContent = ''; }, 3000);
        }
    },

    // --- Update management ---

    _updateInfo: null,

    async checkForAppUpdate() {
        try {
            const data = await API.checkForUpdate();
            if (data.staged) {
                this._showUpdateBanner(
                    `Update v${data.staged_version} ready to install`,
                    'Restart Now', () => this.applyAppUpdate()
                );
            } else if (data.update_available) {
                this._updateInfo = data;
                this._showUpdateBanner(
                    `Update available: v${data.latest_version}`,
                    'Download', () => this.downloadAppUpdate()
                );
            }
        } catch (err) {
            // Silently ignore — update check is best-effort
            console.log('Update check skipped:', err.message);
        }
    },

    async downloadAppUpdate() {
        if (!this._updateInfo || !this._updateInfo.exe_url) return;
        try {
            await API.downloadUpdate(this._updateInfo.exe_url, this._updateInfo.latest_version);
            this._showUpdateBanner('Downloading update...', null, null);
            this._pollDownload();
        } catch (err) {
            this._showUpdateBanner('Download failed: ' + err.message, null, null);
        }
    },

    _pollDownload() {
        const poll = async () => {
            try {
                const status = await API.getUpdateStatus();
                if (status.downloading) {
                    const pct = status.progress >= 0 ? ` ${status.progress}%` : '';
                    this._showUpdateBanner(`Downloading update...${pct}`, null, null);
                    setTimeout(poll, 1000);
                } else if (status.error) {
                    this._showUpdateBanner('Download failed: ' + status.error, null, null);
                } else if (status.staged) {
                    this._showUpdateBanner(
                        `Update v${status.staged_version} ready to install`,
                        'Restart Now', () => this.applyAppUpdate()
                    );
                }
            } catch (err) {
                console.error('Poll error:', err);
            }
        };
        setTimeout(poll, 1000);
    },

    async applyAppUpdate() {
        try {
            await API.applyUpdate();
        } catch (err) {
            // App may have exited already — that's expected
        }
    },

    _showUpdateBanner(text, btnLabel, btnAction) {
        const banner = document.getElementById('update-banner');
        const textEl = document.getElementById('update-text');
        const btn = document.getElementById('update-action-btn');
        textEl.textContent = text;
        banner.style.display = 'flex';
        if (btnLabel && btnAction) {
            btn.textContent = btnLabel;
            btn.style.display = '';
            btn.onclick = btnAction;
        } else {
            btn.style.display = 'none';
        }
    },
};

// Boot
document.addEventListener('DOMContentLoaded', () => App.init());
