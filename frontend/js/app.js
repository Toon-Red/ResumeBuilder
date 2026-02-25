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
        document.getElementById('btn-save').onclick = () => this.save();

        await this.refresh();
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

    async save() {
        this.showStatus('Saved', 'success');
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
};

// Boot
document.addEventListener('DOMContentLoaded', () => App.init());
