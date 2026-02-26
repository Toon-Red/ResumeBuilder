/**
 * Tree rendering for sections/titles/items.
 * Renders both the Active panel (with reorder/remove buttons) and
 * the Repertoire panel (with add buttons).
 */
const Tree = {
    /**
     * Render the active resume tree.
     */
    renderActive(data, container) {
        container.innerHTML = '';
        const sections = data.sections || [];

        document.getElementById('active-empty').classList.toggle('hidden', sections.length > 0);

        sections.forEach((section, sIdx) => {
            const sectionEl = this._createSection(section, 'active', sIdx, sections.length);
            container.appendChild(sectionEl);
        });

        DragDrop.initActive();
    },

    /**
     * Render the vault (repertoire) tree.
     */
    renderVault(data, container) {
        container.innerHTML = '';
        const sections = data.sections || [];

        document.getElementById('vault-empty').classList.toggle('hidden', sections.length > 0);

        sections.forEach(section => {
            const sectionEl = this._createSection(section, 'vault');
            container.appendChild(sectionEl);
        });

        DragDrop.initVault();
    },

    _createSection(section, mode, index, total) {
        const el = document.createElement('div');
        el.className = 'tree-section';
        el.dataset.sectionId = section.id;
        if (section.commented) el.classList.add('commented');

        const header = document.createElement('div');
        header.className = 'tree-section-header';

        if (mode === 'active') {
            header.appendChild(this._reorderBtns('section', section.id, null, index, total));
        }

        const nameSpan = document.createElement('span');
        nameSpan.className = 'section-name';
        nameSpan.textContent = section.name;
        nameSpan.title = `Type: ${section.section_type || 'standard'}`;
        header.appendChild(nameSpan);

        if (mode === 'active') {
            const removeBtn = document.createElement('button');
            removeBtn.className = 'btn-remove';
            removeBtn.textContent = '\u2212';
            removeBtn.title = 'Remove from active';
            removeBtn.onclick = (e) => {
                e.stopPropagation();
                App.removeActiveSection(section.id);
            };
            header.appendChild(removeBtn);
        } else {
            const addBtn = document.createElement('button');
            addBtn.className = 'btn-add';
            addBtn.textContent = '+';
            addBtn.title = 'Add to active resume';
            addBtn.onclick = (e) => {
                e.stopPropagation();
                App.addActiveSection(section.id);
            };
            header.appendChild(addBtn);
        }

        el.appendChild(header);

        const body = document.createElement('div');
        body.className = 'tree-section-body';
        body.dataset.sectionId = section.id;

        const titles = section.titles || [];
        titles.forEach((title, tIdx) => {
            const titleEl = this._createTitle(title, section.id, mode, tIdx, titles.length);
            body.appendChild(titleEl);
        });

        el.appendChild(body);
        return el;
    },

    _createTitle(title, sectionId, mode, index, total) {
        const el = document.createElement('div');
        el.className = 'tree-title';
        el.dataset.titleId = title.id;
        el.dataset.sectionId = sectionId;
        if (title.tweaked) el.classList.add('tweaked');
        if (title.commented) el.classList.add('commented');

        const header = document.createElement('div');
        header.className = 'tree-title-header';

        if (mode === 'active') {
            header.appendChild(this._reorderBtns('title', title.id, sectionId, index, total));
        }

        const textSpan = document.createElement('span');
        textSpan.className = 'title-text';
        // Strip LaTeX formatting for display
        textSpan.textContent = this._cleanLatex(title.arg1 || '(untitled)');
        textSpan.title = title.arg3 || '';
        header.appendChild(textSpan);

        if (title.tweaked) {
            const icon = document.createElement('span');
            icon.className = 'tweak-icon';
            icon.textContent = '\u270f';
            icon.title = 'Has tweaks applied';
            header.appendChild(icon);
        }

        const dateSpan = document.createElement('span');
        dateSpan.className = 'title-date';
        dateSpan.textContent = this._cleanLatex(title.arg2 || '');
        header.appendChild(dateSpan);

        if (mode === 'active' && title.tweaked) {
            const saveBtn = document.createElement('button');
            saveBtn.className = 'btn-save';
            saveBtn.textContent = '\ud83d\udcbe';
            saveBtn.title = 'Save tweak to vault';
            saveBtn.onclick = async (e) => {
                e.stopPropagation();
                await API.commitTweak(title.id);
                App.refresh();
                App.showStatus('Saved to vault');
            };
            header.appendChild(saveBtn);
        }

        if (mode === 'active') {
            const removeBtn = document.createElement('button');
            removeBtn.className = 'btn-remove';
            removeBtn.textContent = '\u2212';
            removeBtn.title = 'Remove from active';
            removeBtn.onclick = (e) => {
                e.stopPropagation();
                App.removeActiveTitle(sectionId, title.id);
            };
            header.appendChild(removeBtn);
        } else {
            const addBtn = document.createElement('button');
            addBtn.className = 'btn-add';
            addBtn.textContent = '+';
            addBtn.title = 'Add to active resume';
            addBtn.onclick = (e) => {
                e.stopPropagation();
                App.addActiveTitle(sectionId, title.id);
            };
            header.appendChild(addBtn);

            // History button (vault only)
            const histBtn = document.createElement('button');
            histBtn.className = 'btn-history';
            histBtn.textContent = '\u29d6';
            histBtn.title = 'Version history';
            histBtn.onclick = (e) => {
                e.stopPropagation();
                History.showTitleHistory(title.id, title.arg1 || '', histBtn);
            };
            header.appendChild(histBtn);
        }

        // Branch label badge
        if (title.branch_label) {
            const badge = document.createElement('span');
            badge.className = 'branch-badge';
            badge.textContent = title.branch_label;
            header.insertBefore(badge, header.querySelector('.title-date'));
        }

        // Double-click to edit title
        header.addEventListener('dblclick', () => {
            Editor.editTitle(title.id, sectionId, title);
        });

        el.appendChild(header);

        const items = title.items || [];
        if (items.length > 0) {
            const itemsContainer = document.createElement('div');
            itemsContainer.className = 'tree-items';
            itemsContainer.dataset.titleId = title.id;
            itemsContainer.dataset.sectionId = sectionId;

            items.forEach((item, iIdx) => {
                const itemEl = this._createItem(item, title.id, sectionId, mode, iIdx, items.length);
                itemsContainer.appendChild(itemEl);
            });

            el.appendChild(itemsContainer);
        }

        return el;
    },

    _createItem(item, titleId, sectionId, mode, index, total) {
        const el = document.createElement('div');
        el.className = 'tree-item';
        el.dataset.itemId = item.id;
        el.dataset.titleId = titleId;
        el.dataset.sectionId = sectionId;
        if (item.tweaked) el.classList.add('tweaked');
        if (item.commented) el.classList.add('commented');

        if (mode === 'active') {
            el.appendChild(this._reorderBtns('item', item.id, titleId, index, total));
        }

        const bullet = document.createElement('span');
        bullet.className = 'item-bullet';
        bullet.textContent = '\u2022';
        el.appendChild(bullet);

        if (item.tweaked) {
            const icon = document.createElement('span');
            icon.className = 'tweak-icon';
            icon.textContent = '\u270f';
            icon.title = 'Tweaked text';
            el.appendChild(icon);
        }

        const textSpan = document.createElement('span');
        textSpan.className = 'item-text';
        textSpan.textContent = this._cleanLatex(item.text || '');
        el.appendChild(textSpan);

        if (mode === 'active' && item.tweaked) {
            const saveBtn = document.createElement('button');
            saveBtn.className = 'btn-save';
            saveBtn.textContent = '\ud83d\udcbe';
            saveBtn.title = 'Save tweak to vault';
            saveBtn.onclick = async (e) => {
                e.stopPropagation();
                await API.commitTweak(item.id);
                App.refresh();
                App.showStatus('Saved to vault');
            };
            el.appendChild(saveBtn);
        }

        if (mode === 'active') {
            const removeBtn = document.createElement('button');
            removeBtn.className = 'btn-remove';
            removeBtn.textContent = '\u2212';
            removeBtn.title = 'Remove from active';
            removeBtn.onclick = (e) => {
                e.stopPropagation();
                App.removeActiveItem(titleId, item.id);
            };
            el.appendChild(removeBtn);
        } else {
            const addBtn = document.createElement('button');
            addBtn.className = 'btn-add';
            addBtn.textContent = '+';
            addBtn.title = 'Add to active resume';
            addBtn.onclick = (e) => {
                e.stopPropagation();
                App.addActiveItem(titleId, item.id, sectionId);
            };
            el.appendChild(addBtn);

            // History button (vault only)
            const histBtn = document.createElement('button');
            histBtn.className = 'btn-history';
            histBtn.textContent = '\u29d6';
            histBtn.title = 'Version history';
            histBtn.onclick = (e) => {
                e.stopPropagation();
                History.showItemHistory(item.id, item.text || '', histBtn);
            };
            el.appendChild(histBtn);
        }

        // Branch label badge
        if (item.branch_label) {
            const badge = document.createElement('span');
            badge.className = 'branch-badge';
            badge.textContent = item.branch_label;
            el.insertBefore(badge, el.querySelector('.item-text'));
        }

        // Double-click to edit
        el.addEventListener('dblclick', () => {
            Editor.editItem(item.id, titleId, item);
        });

        return el;
    },

    _reorderBtns(type, id, parentId, index, total) {
        const container = document.createElement('div');
        container.className = 'reorder-btns';

        const upBtn = document.createElement('button');
        upBtn.className = 'btn-icon';
        upBtn.textContent = '\u25b2';
        upBtn.disabled = index === 0;
        upBtn.onclick = (e) => {
            e.stopPropagation();
            App.reorder(type, id, parentId, index - 1);
        };

        const downBtn = document.createElement('button');
        downBtn.className = 'btn-icon';
        downBtn.textContent = '\u25bc';
        downBtn.disabled = index >= total - 1;
        downBtn.onclick = (e) => {
            e.stopPropagation();
            App.reorder(type, id, parentId, index + 1);
        };

        container.appendChild(upBtn);
        container.appendChild(downBtn);
        return container;
    },

    _cleanLatex(text) {
        return text
            // Remove icon/spacing commands (PDF-only)
            .replace(/\\seticon\{[^}]*\}/g, '')
            .replace(/\\quad/g, '')
            .replace(/\\qquad/g, '')
            .replace(/\\hfill/g, '')
            .replace(/\\vspace\{[^}]*\}/g, '')
            .replace(/\\hspace\{[^}]*\}/g, '')
            // Remove font style commands
            .replace(/\\scshape\b/g, '')
            .replace(/\\Huge\b/g, '')
            .replace(/\\huge\b/g, '')
            .replace(/\\LARGE\b/g, '')
            .replace(/\\Large\b/g, '')
            .replace(/\\large\b/g, '')
            .replace(/\\small\b/g, '')
            .replace(/\\footnotesize\b/g, '')
            .replace(/\\normalsize\b/g, '')
            // Unwrap formatting commands (keep inner text)
            .replace(/\\textbf\{([^}]*)\}/g, '$1')
            .replace(/\\emph\{([^}]*)\}/g, '$1')
            .replace(/\\textit\{([^}]*)\}/g, '$1')
            .replace(/\\textsc\{([^}]*)\}/g, '$1')
            .replace(/\\href\{[^}]*\}\{([^}]*)\}/g, '$1')
            .replace(/\\underline\{([^}]*)\}/g, '$1')
            // Symbols and escapes
            .replace(/\$\|?\$\s*/g, ' | ')
            .replace(/\\\\/g, '')
            .replace(/\\%/g, '%')
            .replace(/\\&/g, '&')
            .replace(/\\#/g, '#')
            // Strip remaining braces
            .replace(/\{|\}/g, '')
            .replace(/\s+/g, ' ')
            .trim();
    },
};
