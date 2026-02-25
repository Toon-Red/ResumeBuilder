"""Tests for the JD keyword extraction and scoring engine."""

import pytest

from server.jd_analyzer import (
    ExtractedKeyword,
    analyze_jd,
    extract_keywords,
    score_keywords,
)


class TestExtractKeywords:
    """Tests for keyword extraction from JD text."""

    def test_extracts_programming_languages(self):
        jd = "We need someone proficient in Python, Java, and TypeScript."
        keywords = extract_keywords(jd)
        names = {k.text for k in keywords}
        assert "python" in names
        assert "java" in names
        assert "typescript" in names

    def test_java_does_not_match_javascript(self):
        jd = "Must know JavaScript and TypeScript."
        keywords = extract_keywords(jd)
        names = {k.text for k in keywords}
        assert "javascript" in names
        # "java" should NOT match from "JavaScript"
        assert "java" not in names

    def test_extracts_tools_and_frameworks(self):
        jd = "Experience with Docker, Kubernetes, and AWS required. CI/CD pipeline management."
        keywords = extract_keywords(jd)
        names = {k.text for k in keywords}
        assert "docker" in names
        assert "kubernetes" in names
        assert "aws" in names

    def test_extracts_soft_skills(self):
        jd = "Strong leadership and communication skills. Cross-functional team collaboration."
        keywords = extract_keywords(jd)
        names = {k.text for k in keywords}
        assert "leadership" in names
        assert "communication" in names

    def test_extracts_certifications(self):
        jd = "AWS Certified Solutions Architect preferred. PMP certification a plus."
        keywords = extract_keywords(jd)
        names = {k.text for k in keywords}
        assert "aws certified" in names
        assert "pmp" in names

    def test_extracts_acronyms(self):
        jd = "Knowledge of REST APIs and SOAP protocols. Experience with ETL pipelines."
        keywords = extract_keywords(jd)
        texts = {k.text for k in keywords}
        assert "REST" in texts or "rest" in {k.text.lower() for k in keywords}
        assert "ETL" in texts

    def test_extracts_capitalized_multiword_terms(self):
        jd = "Experience in Machine Learning and Data Engineering."
        keywords = extract_keywords(jd)
        texts = {k.text for k in keywords}
        assert "Machine Learning" in texts or "machine learning" in {k.text.lower() for k in keywords}

    def test_extracts_experience_requirement(self):
        jd = "5+ years of software development experience required."
        keywords = extract_keywords(jd)
        cats = {k.category for k in keywords}
        assert "requirements" in cats

    def test_empty_text_returns_empty(self):
        assert extract_keywords("") == []
        assert extract_keywords("   ") == []

    def test_no_duplicates(self):
        jd = "Python Python Python. We really need Python."
        keywords = extract_keywords(jd)
        python_matches = [k for k in keywords if k.text == "python"]
        assert len(python_matches) == 1

    def test_categories_are_correct(self):
        jd = "Python, Docker, leadership, AWS Certified"
        keywords = extract_keywords(jd)
        by_text = {k.text: k.category for k in keywords}
        assert by_text.get("python") == "languages"
        assert by_text.get("docker") == "tools"
        assert by_text.get("leadership") == "soft_skills"
        assert by_text.get("aws certified") == "certifications"


class TestScoreKeywords:
    """Tests for scoring keywords against resume text."""

    def test_perfect_score(self):
        keywords = [
            ExtractedKeyword(text="python", category="languages"),
            ExtractedKeyword(text="docker", category="tools"),
        ]
        resume = "Experienced with Python and Docker containerization."
        result = score_keywords(keywords, resume)
        assert result.score == 100.0
        assert result.matched_count == 2
        assert all(k.matched for k in result.keywords)

    def test_zero_score(self):
        keywords = [
            ExtractedKeyword(text="rust", category="languages"),
            ExtractedKeyword(text="kubernetes", category="tools"),
        ]
        resume = "Experienced with Python and Docker."
        result = score_keywords(keywords, resume)
        assert result.score == 0.0
        assert result.matched_count == 0

    def test_partial_score(self):
        keywords = [
            ExtractedKeyword(text="python", category="languages"),
            ExtractedKeyword(text="rust", category="languages"),
        ]
        resume = "Python developer with 5 years experience."
        result = score_keywords(keywords, resume)
        assert result.score == 50.0
        assert result.matched_count == 1

    def test_empty_keywords(self):
        result = score_keywords([], "Some resume text.")
        assert result.score == 0.0
        assert result.total_keywords == 0

    def test_case_insensitive(self):
        keywords = [
            ExtractedKeyword(text="AWS", category="tools"),
        ]
        resume = "Deployed applications on aws cloud infrastructure."
        result = score_keywords(keywords, resume)
        assert result.matched_count == 1


class TestAnalyzeJD:
    """Integration tests for the full analyze pipeline."""

    def test_full_pipeline(self):
        jd = "Looking for a Python developer with Docker and AWS experience. Must have leadership skills."
        resume = "Python developer. Built Docker containers. Deployed to AWS. Led a team of 5."

        result = analyze_jd(jd, resume)
        assert result.total_keywords > 0
        assert result.matched_count > 0
        assert 0 <= result.score <= 100

    def test_to_dict(self):
        jd = "Need Python and Docker skills."
        resume = "Python expert."
        result = analyze_jd(jd, resume)
        d = result.to_dict()

        assert "score" in d
        assert "total_keywords" in d
        assert "matched_count" in d
        assert "keywords" in d
        assert isinstance(d["keywords"], list)
        if d["keywords"]:
            kw = d["keywords"][0]
            assert "text" in kw
            assert "category" in kw
            assert "matched" in kw

    def test_robotics_keywords(self):
        jd = "Experience with ROS2, PLC programming, and SCADA systems. CODESYS preferred."
        resume = "Programmed PLCs using CODESYS. Built ROS2 nodes for robot navigation. Designed SCADA HMI."

        result = analyze_jd(jd, resume)
        matched_texts = {k.text for k in result.keywords if k.matched}
        assert "codesys" in matched_texts or "CODESYS" in matched_texts or any(
            "codesys" in t.lower() for t in matched_texts
        )
