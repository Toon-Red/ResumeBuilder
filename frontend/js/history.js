/**
 * Per-entry version history popover with diff display,
 * restore, and branch (experimental edit) capabilities.
 */
const History = {
    _popover: null,

    init() {
        // Create the popover element once
        this._popover = document.createElement('div');
        this._popover.className = 'history-popover hidden';
        this._popover.id = 'history-popover';
        document.body.appendChild(this._popover);

        // Close on outside click
        document.addEventListener('click', (e) => {
            if (!this._popover.contains(e.target) &&
                !e.target.classList.contains('btn-history')) {
                this.close();
            }
        });
    },

    close() {
        this._popover.classList.add('hidden');
    },

    async showItemHistory(itemId, currentText, anchorEl) {
        try {
            const data = await API.getItemHistory(itemId);
            this._render(
                data.versions, currentText, 'text',
                itemId, 'item', anchorEl
            );
        } catch (err) {
            App.showStatus('History: ' + err.message, 'error');
        }
    },

    async showTitleHistory(titleId, currentArg1, anchorEl) {
        try {
            const data = await API.getTitleHistory(titleId);
            this._render(
                data.versions, currentArg1, 'arg1',
                titleId, 'title', anchorEl
            );
        } catch (err) {
            App.showStatus('History: ' + err.message, 'error');
        }
    },

    _render(versions, currentText, textField, entryId, entryType, anchorEl) {
        const pop = this._popover;
        pop.innerHTML = '';

        // Header
        const header = document.createElement('div');
        header.className = 'history-header';
        header.innerHTML = `<strong>History</strong> <span class="history-count">${versions.length} version${versions.length !== 1 ? 's' : ''}</span>`;
        pop.appendChild(header);

        if (versions.length === 0) {
            const empty = document.createElement('div');
            empty.className = 'history-empty';
            empty.textContent = 'No previous versions yet. Edit this entry to create history.';
            pop.appendChild(empty);
        } else {
            const list = document.createElement('div');
            list.className = 'history-list';

            versions.slice().reverse().forEach((v) => {
                const row = document.createElement('div');
                row.className = 'history-row';

                const oldText = v.data[textField] || '';
                const ts = new Date(v.timestamp).toLocaleString();
                const label = v.label ? ` (${v.label})` : '';

                // Timestamp + label
                const meta = document.createElement('div');
                meta.className = 'history-meta';
                meta.textContent = ts + label;
                row.appendChild(meta);

                // Diff
                const diff = document.createElement('div');
                diff.className = 'history-diff';
                diff.innerHTML = this._wordDiff(oldText, currentText);
                row.appendChild(diff);

                // Restore button
                const restoreBtn = document.createElement('button');
                restoreBtn.className = 'btn btn-small';
                restoreBtn.textContent = 'Restore';
                restoreBtn.onclick = async () => {
                    try {
                        if (entryType === 'item') {
                            await API.restoreItem(entryId, v.index);
                        } else {
                            await API.restoreTitle(entryId, v.index);
                        }
                        this.close();
                        App.refresh();
                        App.showStatus('Restored to version', 'success');
                    } catch (err) {
                        App.showStatus('Restore failed: ' + err.message, 'error');
                    }
                };
                row.appendChild(restoreBtn);

                list.appendChild(row);
            });

            pop.appendChild(list);
        }

        // Branch button
        const branchBtn = document.createElement('button');
        branchBtn.className = 'btn btn-small history-branch-btn';
        branchBtn.textContent = 'Branch (experimental copy)';
        branchBtn.onclick = async () => {
            try {
                if (entryType === 'item') {
                    await API.branchItem(entryId, 'experimental');
                } else {
                    await API.branchTitle(entryId, 'experimental');
                }
                this.close();
                App.refresh();
                App.showStatus('Branch created', 'success');
            } catch (err) {
                App.showStatus('Branch failed: ' + err.message, 'error');
            }
        };
        pop.appendChild(branchBtn);

        // Position the popover near the anchor element, clamped to viewport
        pop.classList.remove('hidden');
        const rect = anchorEl.getBoundingClientRect();
        const popRect = pop.getBoundingClientRect();
        const pad = 8;

        let top = rect.bottom + 4;
        let left = rect.left - 100;

        // Clamp bottom edge
        if (top + popRect.height > window.innerHeight - pad) {
            top = rect.top - popRect.height - 4;
        }
        // If still off the top, pin to top
        if (top < pad) {
            top = pad;
        }
        // Clamp right edge
        if (left + popRect.width > window.innerWidth - pad) {
            left = window.innerWidth - popRect.width - pad;
        }
        // Clamp left edge
        if (left < pad) {
            left = pad;
        }

        pop.style.top = top + 'px';
        pop.style.left = left + 'px';
    },

    /**
     * Simple word-level diff. Returns HTML with <del> and <ins> tags.
     */
    _wordDiff(oldText, newText) {
        const oldWords = oldText.split(/\s+/).filter(Boolean);
        const newWords = newText.split(/\s+/).filter(Boolean);

        // Simple LCS-based diff
        const parts = [];
        let oi = 0, ni = 0;
        while (oi < oldWords.length || ni < newWords.length) {
            if (oi < oldWords.length && ni < newWords.length &&
                oldWords[oi] === newWords[ni]) {
                parts.push(oldWords[oi]);
                oi++; ni++;
            } else if (ni < newWords.length &&
                (oi >= oldWords.length || !oldWords.slice(oi).includes(newWords[ni]))) {
                parts.push(`<ins>${newWords[ni]}</ins>`);
                ni++;
            } else {
                parts.push(`<del>${oldWords[oi]}</del>`);
                oi++;
            }
        }
        return parts.join(' ') || '<em>empty</em>';
    },
};
