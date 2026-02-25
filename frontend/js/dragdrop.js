/**
 * SortableJS integration for drag-and-drop.
 * Active panels: reorder within, accept drops from repertoire.
 * Repertoire panels: clone-drag to active (doesn't remove from library).
 */
const DragDrop = {
    _activeSortables: [],
    _repSortables: [],

    initActive() {
        // Destroy old instances
        this._activeSortables.forEach(s => s.destroy());
        this._activeSortables = [];

        // Section-level sorting
        const activeTree = document.getElementById('active-tree');
        if (activeTree) {
            this._activeSortables.push(
                new Sortable(activeTree, {
                    group: 'sections',
                    animation: 150,
                    handle: '.tree-section-header',
                    draggable: '.tree-section',
                    onEnd: (evt) => {
                        const sectionId = evt.item.dataset.sectionId;
                        App.reorder('section', sectionId, null, evt.newIndex);
                    },
                })
            );
        }

        // Title-level sorting within each section
        document.querySelectorAll('#active-tree .tree-section-body').forEach(body => {
            const sectionId = body.dataset.sectionId;
            this._activeSortables.push(
                new Sortable(body, {
                    group: { name: 'titles', pull: true, put: true },
                    animation: 150,
                    draggable: '.tree-title',
                    onEnd: (evt) => {
                        const titleId = evt.item.dataset.titleId;
                        App.reorder('title', titleId, sectionId, evt.newIndex);
                    },
                    onAdd: (evt) => {
                        const titleId = evt.item.dataset.titleId;
                        // Clone from repertoire - need to add via API
                        if (evt.from.closest('#panel-vault')) {
                            evt.item.remove();
                            App.addActiveTitle(sectionId, titleId);
                        }
                    },
                })
            );
        });

        // Item-level sorting within each title
        document.querySelectorAll('#active-tree .tree-items').forEach(container => {
            const titleId = container.dataset.titleId;
            this._activeSortables.push(
                new Sortable(container, {
                    group: { name: 'items', pull: true, put: true },
                    animation: 150,
                    draggable: '.tree-item',
                    onEnd: (evt) => {
                        const itemId = evt.item.dataset.itemId;
                        App.reorder('item', itemId, titleId, evt.newIndex);
                    },
                    onAdd: (evt) => {
                        const itemId = evt.item.dataset.itemId;
                        if (evt.from.closest('#panel-vault')) {
                            evt.item.remove();
                            const sectionId = container.dataset.sectionId;
                            App.addActiveItem(titleId, itemId, sectionId);
                        }
                    },
                })
            );
        });
    },

    initVault() {
        this._repSortables.forEach(s => s.destroy());
        this._repSortables = [];

        // Titles in vault - clone mode
        document.querySelectorAll('#vault-tree .tree-section-body').forEach(body => {
            this._repSortables.push(
                new Sortable(body, {
                    group: { name: 'titles', pull: 'clone', put: false },
                    animation: 150,
                    sort: false,
                    draggable: '.tree-title',
                })
            );
        });

        // Items in vault - clone mode
        document.querySelectorAll('#vault-tree .tree-items').forEach(container => {
            this._repSortables.push(
                new Sortable(container, {
                    group: { name: 'items', pull: 'clone', put: false },
                    animation: 150,
                    sort: false,
                    draggable: '.tree-item',
                })
            );
        });
    },
};
