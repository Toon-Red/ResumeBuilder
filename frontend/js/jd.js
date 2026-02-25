/**
 * Job Description import and ATS keyword analysis UI.
 */
const JD = {
    _modal: null,
    _textarea: null,
    _resultsPanel: null,
    _resultsBody: null,

    init() {
        this._modal = document.getElementById('jd-modal');
        this._textarea = document.getElementById('jd-textarea');
        this._resultsPanel = document.getElementById('jd-results');
        this._resultsBody = document.getElementById('jd-results-body');

        this._urlInput = document.getElementById('jd-url-input');

        document.getElementById('btn-import-jd').onclick = () => this._showModal();
        document.getElementById('jd-analyze').onclick = () => this._analyze();
        document.getElementById('jd-cancel').onclick = () => this._hideModal();
        document.getElementById('jd-fetch').onclick = () => this._fetchUrl();
        document.getElementById('jd-clear').onclick = () => this._clear();
        document.getElementById('jd-close-results').onclick = () => this._hideResults();

        // Close modal on Escape
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && !this._modal.classList.contains('hidden')) {
                this._hideModal();
            }
        });
    },

    _showModal() {
        this._modal.classList.remove('hidden');
        this._textarea.focus();
    },

    _hideModal() {
        this._modal.classList.add('hidden');
    },

    async _analyze() {
        const text = this._textarea.value.trim();
        if (!text) {
            App.showStatus('Paste a job description first', 'error');
            return;
        }

        App.showStatus('Analyzing JD...', '');
        try {
            const result = await API.analyzeJD(text);
            this._hideModal();
            this._renderResults(result);
            App.showStatus('JD analysis complete', 'success');
        } catch (err) {
            App.showStatus('Analysis failed: ' + err.message, 'error');
        }
    },

    async _fetchUrl() {
        const url = this._urlInput.value.trim();
        if (!url) {
            App.showStatus('Enter a URL first', 'error');
            return;
        }

        App.showStatus('Fetching job posting...', '');
        try {
            const result = await API.scrapeJD(url);
            this._textarea.value = result.extracted_text || '';
            this._hideModal();
            this._renderResults(result);
            App.showStatus('JD fetched and analyzed', 'success');
        } catch (err) {
            App.showStatus('Fetch failed: ' + err.message, 'error');
        }
    },

    async _clear() {
        try {
            await API.clearJD();
            this._hideResults();
        } catch (err) {
            console.error('Clear JD error:', err);
        }
    },

    _hideResults() {
        this._resultsPanel.classList.add('hidden');
    },

    _renderResults(data) {
        this._resultsBody.innerHTML = '';

        // Score display
        const scoreDiv = document.createElement('div');
        const scoreLevel = data.score >= 70 ? 'high' : data.score >= 40 ? 'mid' : 'low';
        scoreDiv.className = `jd-score score-${scoreLevel}`;
        scoreDiv.innerHTML = `
            <div class="jd-score-value">${data.score}%</div>
            <div class="jd-score-label">${data.matched_count} of ${data.total_keywords} keywords matched</div>
        `;
        this._resultsBody.appendChild(scoreDiv);

        // Group keywords by category
        const groups = {};
        for (const kw of data.keywords) {
            if (!groups[kw.category]) groups[kw.category] = [];
            groups[kw.category].push(kw);
        }

        // Category display names
        const categoryNames = {
            languages: 'Programming Languages',
            tools: 'Tools & Frameworks',
            soft_skills: 'Soft Skills',
            certifications: 'Certifications',
            education: 'Education',
            acronyms: 'Technical Acronyms',
            concepts: 'Key Concepts',
            requirements: 'Requirements',
        };

        // Render each category
        for (const [cat, keywords] of Object.entries(groups)) {
            const catDiv = document.createElement('div');
            catDiv.className = 'jd-category';

            const nameDiv = document.createElement('div');
            nameDiv.className = 'jd-category-name';
            nameDiv.textContent = categoryNames[cat] || cat;
            catDiv.appendChild(nameDiv);

            const tagsDiv = document.createElement('div');
            tagsDiv.className = 'jd-tags';

            // Sort: matched first, then missing
            keywords.sort((a, b) => (b.matched ? 1 : 0) - (a.matched ? 1 : 0));

            for (const kw of keywords) {
                const tag = document.createElement('span');
                tag.className = `jd-tag ${kw.matched ? 'matched' : 'missing'}`;
                tag.textContent = kw.text;
                tagsDiv.appendChild(tag);
            }

            catDiv.appendChild(tagsDiv);
            this._resultsBody.appendChild(catDiv);
        }

        this._resultsPanel.classList.remove('hidden');
    },
};
