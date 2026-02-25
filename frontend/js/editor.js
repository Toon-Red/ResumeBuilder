/**
 * Inline editing + tweak UI.
 * Double-click titles/items to edit. Edits in active panel create tweaks;
 * edits in repertoire panel modify the source.
 */
const Editor = {
    _modal: null,
    _textarea: null,
    _currentEdit: null,

    init() {
        this._modal = document.getElementById('edit-modal');
        this._textarea = document.getElementById('edit-textarea');

        document.getElementById('edit-save').onclick = () => this._save();
        document.getElementById('edit-cancel').onclick = () => this._close();

        // Close on Escape
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && !this._modal.classList.contains('hidden')) {
                this._close();
            }
        });
    },

    editTitle(titleId, sectionId, titleData) {
        const isActive = !!document.querySelector(
            `#active-tree [data-title-id="${titleId}"]`
        );
        this._currentEdit = {
            type: 'title',
            id: titleId,
            sectionId,
            isActive,
            fields: {
                arg1: titleData.arg1 || '',
                arg2: titleData.arg2 || '',
                arg3: titleData.arg3 || '',
                arg4: titleData.arg4 || '',
            },
        };

        const display = [
            `Arg1 (Title): ${titleData.arg1 || ''}`,
            `Arg2 (Date): ${titleData.arg2 || ''}`,
            `Arg3 (Subtitle): ${titleData.arg3 || ''}`,
            `Arg4 (Location): ${titleData.arg4 || ''}`,
        ].join('\n');

        document.getElementById('edit-modal-title').textContent =
            isActive ? 'Edit Title (Tweak)' : 'Edit Title (Source)';
        this._textarea.value = display;
        this._textarea.rows = 6;
        this._modal.classList.remove('hidden');
        this._textarea.focus();
    },

    editItem(itemId, titleId, itemData) {
        const isActive = !!document.querySelector(
            `#active-tree [data-item-id="${itemId}"]`
        );
        this._currentEdit = {
            type: 'item',
            id: itemId,
            titleId,
            isActive,
            originalText: itemData.text || '',
        };

        document.getElementById('edit-modal-title').textContent =
            isActive ? 'Edit Item (Tweak)' : 'Edit Item (Source)';
        this._textarea.value = itemData.text || '';
        this._textarea.rows = 4;
        this._modal.classList.remove('hidden');
        this._textarea.focus();
    },

    async _save() {
        const edit = this._currentEdit;
        if (!edit) return;

        try {
            if (edit.type === 'title') {
                await this._saveTitle(edit);
            } else if (edit.type === 'item') {
                await this._saveItem(edit);
            }
            this._close();
            App.refresh();
        } catch (err) {
            App.showStatus('Error: ' + err.message, 'error');
        }
    },

    async _saveTitle(edit) {
        if (edit.isActive) {
            // Parse the textarea back into fields
            const lines = this._textarea.value.split('\n');
            for (const line of lines) {
                const match = line.match(/^Arg(\d)\s*\([^)]*\):\s*(.*)/);
                if (match) {
                    const field = `arg${match[1]}`;
                    const value = match[2].trim();
                    if (value !== edit.fields[field]) {
                        await API.setTweak(edit.id, field, value);
                    }
                }
            }
        } else {
            // Edit source
            const lines = this._textarea.value.split('\n');
            const data = {};
            for (const line of lines) {
                const match = line.match(/^Arg(\d)\s*\([^)]*\):\s*(.*)/);
                if (match) {
                    data[`arg${match[1]}`] = match[2].trim();
                }
            }
            await API.updateTitle(edit.id, data);
        }
    },

    async _saveItem(edit) {
        const newText = this._textarea.value.trim();
        if (newText === edit.originalText) return;

        if (edit.isActive) {
            await API.setTweak(edit.id, 'text', newText);
        } else {
            await API.updateItem(edit.id, newText);
        }
    },

    _close() {
        this._modal.classList.add('hidden');
        this._currentEdit = null;
    },
};
