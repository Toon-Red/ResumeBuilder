"""Tests for JD scraper — HTML extraction only, no network calls."""

import pytest

from server.jd_scraper import extract_jd_text


# --- Sample HTML fixtures ---

JD_CLASS_HTML = """
<html><body>
<div class="header">Company Inc</div>
<div class="job-description">
    <h2>Software Engineer</h2>
    <p>We are looking for a skilled Python developer with experience in
    FastAPI, Docker, and AWS. The ideal candidate will have 3+ years of
    experience building scalable web applications.</p>
    <ul>
        <li>Design and implement RESTful APIs</li>
        <li>Write unit and integration tests</li>
        <li>Collaborate with cross-functional teams</li>
    </ul>
    <p>Requirements: Bachelor's degree in Computer Science, strong
    problem-solving skills, and experience with CI/CD pipelines.</p>
</div>
<div class="footer">Apply now</div>
</body></html>
"""

JD_ID_HTML = """
<html><body>
<div id="job-description">
    <h3>Data Analyst</h3>
    <p>Join our analytics team. Must know SQL, Python, Tableau, and have
    experience with large datasets. Strong communication skills required.
    We use Snowflake and dbt for our data pipeline.</p>
</div>
</body></html>
"""

JD_CAMELCASE_HTML = """
<html><body>
<div class="jobDescription">
    <p>Senior React Developer needed. Must have TypeScript, Redux,
    GraphQL experience. 5+ years building modern web applications.
    Experience with Node.js backend development is a plus.</p>
</div>
</body></html>
"""

JD_ARTICLE_HTML = """
<html><body>
<article class="job-posting-content">
    <p>DevOps Engineer role. Looking for someone with Kubernetes,
    Terraform, Jenkins, and Linux administration experience.
    Must be comfortable with infrastructure as code.</p>
</article>
</body></html>
"""

FALLBACK_HTML = """
<html><body>
<div class="main-content">
    <div class="some-random-container">
        <p>This is a paragraph with not much content.</p>
    </div>
    <div class="big-text-block">
        <p>Machine Learning Engineer. We need someone who can build and
        deploy ML models at scale. Experience with PyTorch, TensorFlow,
        scikit-learn required. Must understand distributed computing and
        have worked with large language models. Strong background in
        statistics and linear algebra.</p>
    </div>
</div>
</body></html>
"""

MINIMAL_HTML = """
<html><body>
<p>Short</p>
</body></html>
"""


class TestExtractJDText:
    """Test extract_jd_text with various HTML structures."""

    def test_class_based_selector(self):
        text = extract_jd_text(JD_CLASS_HTML)
        assert "Python developer" in text
        assert "FastAPI" in text
        assert "RESTful APIs" in text
        assert len(text) > 100

    def test_id_based_selector(self):
        text = extract_jd_text(JD_ID_HTML)
        assert "Data Analyst" in text
        assert "SQL" in text
        assert "Snowflake" in text

    def test_camelcase_class(self):
        text = extract_jd_text(JD_CAMELCASE_HTML)
        assert "React Developer" in text
        assert "TypeScript" in text

    def test_article_selector(self):
        text = extract_jd_text(JD_ARTICLE_HTML)
        assert "DevOps Engineer" in text
        assert "Kubernetes" in text

    def test_fallback_largest_block(self):
        text = extract_jd_text(FALLBACK_HTML)
        assert "Machine Learning" in text
        assert "PyTorch" in text

    def test_minimal_returns_empty(self):
        text = extract_jd_text(MINIMAL_HTML)
        assert text == ""

    def test_whitespace_normalized(self):
        text = extract_jd_text(JD_CLASS_HTML)
        assert "  " not in text  # No double spaces

    def test_list_items_preserved(self):
        text = extract_jd_text(JD_CLASS_HTML)
        # Bullet list items should be present
        assert "Design and implement" in text
        assert "Write unit" in text

    def test_empty_html(self):
        text = extract_jd_text("<html><body></body></html>")
        assert text == ""

    def test_nested_jd_container(self):
        html_str = """
        <html><body>
        <div class="wrapper">
            <section class="description">
                <p>Full stack engineer needed with Java, Spring Boot,
                React, PostgreSQL. Must have experience with microservices
                architecture and containerization with Docker.</p>
            </section>
        </div>
        </body></html>
        """
        text = extract_jd_text(html_str)
        assert "Java" in text
        assert "Spring Boot" in text
