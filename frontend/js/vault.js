/**
 * Vault panel — drag-to-snap tiling (like Linux window snapping).
 * Drag the header to move, release near edges/corners to snap into dock position.
 * Release in center to free-float.
 */
const Vault = {
    _panel: null,
    _header: null,
    _preview: null,
    _storageKey: 'resume-builder-vault-dock',
    _dragging: false,
    _offsetX: 0,
    _offsetY: 0,
    _EDGE: 0.20, // 20% threshold for snap zones

    init() {
        this._panel = document.getElementById('panel-vault');
        this._header = this._panel.querySelector('.vault-header');
        this._preview = document.getElementById('snap-preview');

        document.getElementById('btn-toggle-vault').onclick = () => this.toggle();
        document.getElementById('btn-close-vault').onclick = () => this.hide();

        // Drag handlers on header
        this._header.addEventListener('mousedown', (e) => this._onMouseDown(e));
        document.addEventListener('mousemove', (e) => this._onMouseMove(e));
        document.addEventListener('mouseup', (e) => this._onMouseUp(e));

        // Restore saved position
        this._restorePosition();
    },

    toggle() {
        this._panel.classList.toggle('visible');
    },

    show() {
        this._panel.classList.add('visible');
    },

    hide() {
        this._panel.classList.remove('visible');
    },

    // --- Drag handlers ---

    _onMouseDown(e) {
        // Don't drag if clicking a button or interactive element
        if (e.target.closest('button')) return;
        e.preventDefault();

        this._dragging = true;
        const rect = this._panel.getBoundingClientRect();
        this._offsetX = e.clientX - rect.left;
        this._offsetY = e.clientY - rect.top;

        // Switch to free-position mode for dragging
        this._panel.classList.add('vault-dragging');
        this._panel.style.left = rect.left + 'px';
        this._panel.style.top = rect.top + 'px';
        this._panel.style.width = '380px';
        this._panel.style.height = '300px';
        this._panel.style.right = 'auto';
        this._panel.style.bottom = 'auto';
        // Remove any dock class while dragging
        this._clearDockClasses();
    },

    _onMouseMove(e) {
        if (!this._dragging) return;
        e.preventDefault();

        // Move panel to cursor
        this._panel.style.left = (e.clientX - this._offsetX) + 'px';
        this._panel.style.top = (e.clientY - this._offsetY) + 'px';

        // Show snap preview
        const zone = this._detectZone(e.clientX, e.clientY);
        this._showPreview(zone);
    },

    _onMouseUp(e) {
        if (!this._dragging) return;
        this._dragging = false;
        this._hidePreview();
        this._panel.classList.remove('vault-dragging');

        const zone = this._detectZone(e.clientX, e.clientY);

        if (zone === 'float') {
            // Keep at current position
            const left = parseInt(this._panel.style.left);
            const top = parseInt(this._panel.style.top);
            this._applyFloat(left, top);
            this._savePosition({ mode: 'float', left, top });
        } else {
            // Snap to dock zone
            this._clearInlineStyles();
            this._applyDock(zone);
            this._savePosition({ mode: zone });
        }
    },

    // --- Snap zone detection ---

    _detectZone(x, y) {
        const w = window.innerWidth;
        const h = window.innerHeight;
        const ex = this._EDGE;

        const nearLeft = x < w * ex;
        const nearRight = x > w * (1 - ex);
        const nearTop = y < h * ex;
        const nearBottom = y > h * (1 - ex);

        // Corners first (both axes near edge)
        if (nearTop && nearLeft) return 'top-left';
        if (nearTop && nearRight) return 'top-right';
        if (nearBottom && nearLeft) return 'bottom-left';
        if (nearBottom && nearRight) return 'bottom-right';

        // Edges
        if (nearRight) return 'right';
        if (nearLeft) return 'left';
        if (nearBottom) return 'bottom';
        if (nearTop) return 'top';

        return 'float';
    },

    // --- Snap preview overlay ---

    _showPreview(zone) {
        if (zone === 'float') {
            this._hidePreview();
            return;
        }
        const p = this._preview;
        p.style.display = 'block';

        // Position the preview to show where the panel will snap
        const positions = {
            'right':        { top: '0', left: '60%', right: '0', bottom: '0', width: '40%', height: '100%' },
            'left':         { top: '0', left: '0', right: '60%', bottom: '0', width: '40%', height: '100%' },
            'bottom':       { top: '55%', left: '0', right: '0', bottom: '0', width: '100%', height: '45%' },
            'top':          { top: '49px', left: '0', right: '0', bottom: '55%', width: '100%', height: '45%' },
            'top-left':     { top: '49px', left: '0', right: '50%', bottom: '50%', width: '50%', height: 'calc(50% - 49px)' },
            'top-right':    { top: '49px', left: '50%', right: '0', bottom: '50%', width: '50%', height: 'calc(50% - 49px)' },
            'bottom-left':  { top: '50%', left: '0', right: '50%', bottom: '0', width: '50%', height: '50%' },
            'bottom-right': { top: '50%', left: '50%', right: '0', bottom: '0', width: '50%', height: '50%' },
        };

        const pos = positions[zone];
        if (pos) {
            Object.assign(p.style, {
                top: pos.top, left: pos.left, width: pos.width, height: pos.height,
                right: 'auto', bottom: 'auto',
            });
        }
    },

    _hidePreview() {
        this._preview.style.display = 'none';
    },

    // --- Apply dock/float ---

    _applyDock(zone) {
        this._clearDockClasses();
        this._panel.classList.add(`dock-${zone}`);
    },

    _applyFloat(left, top) {
        this._clearDockClasses();
        this._panel.classList.add('dock-float');
        const w = 380;
        const h = window.innerHeight * 0.5;
        const pad = 8;
        left = Math.max(pad, Math.min(left, window.innerWidth - w - pad));
        top = Math.max(pad, Math.min(top, window.innerHeight - h - pad));
        this._panel.style.left = left + 'px';
        this._panel.style.top = top + 'px';
        this._panel.style.width = w + 'px';
        this._panel.style.height = '50vh';
        this._panel.style.right = 'auto';
        this._panel.style.bottom = 'auto';
    },

    _clearDockClasses() {
        this._panel.className = this._panel.className.replace(/\bdock-\S+/g, '').trim();
        if (!this._panel.classList.contains('vault-panel')) {
            this._panel.classList.add('vault-panel');
        }
        if (!this._panel.classList.contains('visible')) {
            this._panel.classList.add('visible');
        }
    },

    _clearInlineStyles() {
        this._panel.style.left = '';
        this._panel.style.top = '';
        this._panel.style.width = '';
        this._panel.style.height = '';
        this._panel.style.right = '';
        this._panel.style.bottom = '';
    },

    // --- Persistence ---

    _savePosition(pos) {
        localStorage.setItem(this._storageKey, JSON.stringify(pos));
    },

    _restorePosition() {
        const raw = localStorage.getItem(this._storageKey);
        if (!raw) {
            this._applyDock('right');
            return;
        }
        try {
            const pos = JSON.parse(raw);
            if (pos.mode === 'float') {
                this._applyFloat(pos.left, pos.top);
            } else {
                this._applyDock(pos.mode);
            }
        } catch {
            this._applyDock('right');
        }
    },
};
