"""Job Description keyword extraction and ATS match scoring.

Extracts keywords from JD text using built-in dictionaries and regex
patterns, then scores them against the active resume content.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


# ============================================================
# Built-in keyword dictionaries
# ============================================================

PROGRAMMING_LANGUAGES = {
    "python", "java", "javascript", "typescript", "c++", "c#", "go", "golang",
    "rust", "ruby", "php", "swift", "kotlin", "scala", "r", "matlab",
    "perl", "lua", "dart", "elixir", "haskell", "clojure", "groovy",
    "objective-c", "assembly", "fortran", "cobol", "sql", "plsql",
    "bash", "powershell", "shell", "vba", "vb.net",
}

TOOLS_AND_FRAMEWORKS = {
    "react", "angular", "vue", "svelte", "next.js", "nuxt", "express",
    "django", "flask", "fastapi", "spring", "spring boot", "rails",
    "node.js", "nodejs", ".net", "asp.net",
    "docker", "kubernetes", "k8s", "terraform", "ansible", "puppet", "chef",
    "jenkins", "github actions", "gitlab ci", "circleci", "travis ci",
    "aws", "azure", "gcp", "google cloud", "heroku", "vercel", "netlify",
    "linux", "unix", "windows server",
    "git", "github", "gitlab", "bitbucket", "svn",
    "postgresql", "mysql", "mongodb", "redis", "elasticsearch",
    "dynamodb", "cassandra", "sqlite", "oracle", "sql server",
    "kafka", "rabbitmq", "celery", "airflow",
    "graphql", "rest", "restful", "grpc", "soap",
    "webpack", "vite", "babel", "eslint", "prettier",
    "pytest", "jest", "mocha", "selenium", "cypress", "playwright",
    "pandas", "numpy", "scikit-learn", "tensorflow", "pytorch", "keras",
    "opencv", "spark", "hadoop", "databricks", "snowflake",
    "tableau", "power bi", "grafana", "prometheus",
    "jira", "confluence", "slack", "figma", "sketch",
    "s3", "ec2", "lambda", "ecs", "eks", "rds", "sqs", "sns",
    "cloudformation", "cdk", "sam",
    "nginx", "apache", "traefik", "haproxy",
    "oauth", "jwt", "saml", "openid",
    "ci/cd", "devops", "mlops", "dataops",
    "ros", "ros2", "gazebo", "rviz",
    "plc", "scada", "hmi", "opc ua", "modbus",
    "codesys", "twincat", "siemens", "allen-bradley", "rockwell",
    "agile", "scrum", "kanban", "waterfall", "safe",
}

SOFT_SKILLS = {
    "leadership", "communication", "teamwork", "collaboration",
    "problem-solving", "problem solving", "critical thinking",
    "project management", "time management", "mentoring",
    "cross-functional", "stakeholder management", "presentation",
    "analytical", "detail-oriented", "detail oriented",
    "self-motivated", "self-starter", "initiative",
    "adaptability", "flexibility", "multitasking",
}

CERTIFICATIONS = {
    "aws certified", "azure certified", "gcp certified",
    "cka", "ckad", "cks",
    "pmp", "prince2", "csm", "safe agilist",
    "cissp", "ceh", "comptia", "security+", "network+",
    "ccna", "ccnp", "ccie",
    "pe", "eit", "fe exam",
    "six sigma", "lean", "green belt", "black belt",
}

EDUCATION_KEYWORDS = {
    "bachelor", "master", "phd", "doctorate", "mba",
    "computer science", "electrical engineering", "mechanical engineering",
    "software engineering", "data science", "machine learning",
    "information technology", "mathematics", "statistics", "physics",
}


@dataclass
class ExtractedKeyword:
    """A keyword extracted from the JD."""
    text: str
    category: str
    matched: bool = False


@dataclass
class JDAnalysisResult:
    """Result of analyzing a job description against a resume."""
    score: float = 0.0
    total_keywords: int = 0
    matched_count: int = 0
    keywords: list[ExtractedKeyword] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "score": round(self.score, 1),
            "total_keywords": self.total_keywords,
            "matched_count": self.matched_count,
            "keywords": [
                {"text": k.text, "category": k.category, "matched": k.matched}
                for k in self.keywords
            ],
        }


def extract_keywords(jd_text: str) -> list[ExtractedKeyword]:
    """Extract keywords from job description text.

    Uses dictionary matching + regex patterns for acronyms and
    capitalized multi-word terms.
    """
    text_lower = jd_text.lower()
    found: dict[str, ExtractedKeyword] = {}

    # Dictionary matching with word boundaries
    for keyword in PROGRAMMING_LANGUAGES:
        if _word_match(keyword, text_lower):
            found[keyword] = ExtractedKeyword(text=keyword, category="languages")

    for keyword in TOOLS_AND_FRAMEWORKS:
        if _word_match(keyword, text_lower):
            found[keyword] = ExtractedKeyword(text=keyword, category="tools")

    for keyword in SOFT_SKILLS:
        if _word_match(keyword, text_lower):
            found[keyword] = ExtractedKeyword(text=keyword, category="soft_skills")

    for keyword in CERTIFICATIONS:
        if _word_match(keyword, text_lower):
            found[keyword] = ExtractedKeyword(text=keyword, category="certifications")

    for keyword in EDUCATION_KEYWORDS:
        if _word_match(keyword, text_lower):
            found[keyword] = ExtractedKeyword(text=keyword, category="education")

    # Regex: acronyms (3+ uppercase letters, e.g. AWS, CI/CD, REST)
    for match in re.finditer(r'\b([A-Z][A-Z/]{2,})\b', jd_text):
        acronym = match.group(1)
        key = acronym.lower()
        if key not in found and key not in _SKIP_ACRONYMS:
            found[key] = ExtractedKeyword(text=acronym, category="acronyms")

    # Regex: capitalized multi-word terms (e.g. "Machine Learning", "Data Engineering")
    for match in re.finditer(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b', jd_text):
        term = match.group(1)
        key = term.lower()
        if key not in found and key not in _SKIP_TERMS:
            found[key] = ExtractedKeyword(text=term, category="concepts")

    # Experience level patterns (e.g. "5+ years", "3-5 years")
    exp_match = re.search(r'(\d+\+?\s*[-–]?\s*\d*\s*years?)', jd_text, re.IGNORECASE)
    if exp_match:
        found["_experience"] = ExtractedKeyword(
            text=exp_match.group(1).strip(), category="requirements"
        )

    return list(found.values())


def score_keywords(
    keywords: list[ExtractedKeyword],
    resume_text: str,
) -> JDAnalysisResult:
    """Score extracted keywords against resume text content.

    Returns match percentage and per-keyword match status.
    """
    resume_lower = resume_text.lower()

    for kw in keywords:
        search_term = kw.text.lower()
        if _word_match(search_term, resume_lower):
            kw.matched = True

    total = len(keywords)
    matched = sum(1 for k in keywords if k.matched)
    score = (matched / total * 100) if total > 0 else 0.0

    return JDAnalysisResult(
        score=score,
        total_keywords=total,
        matched_count=matched,
        keywords=keywords,
    )


def analyze_jd(jd_text: str, resume_text: str) -> JDAnalysisResult:
    """Full pipeline: extract keywords from JD, score against resume."""
    keywords = extract_keywords(jd_text)
    return score_keywords(keywords, resume_text)


def _word_match(keyword: str, text: str) -> bool:
    """Check if keyword appears as a whole word in text.

    Uses word boundary matching to prevent 'java' matching 'javascript'.
    Handles special chars in keywords like 'c++', 'c#', '.net'.
    """
    escaped = re.escape(keyword)
    pattern = r'(?:^|[\s,;(./])' + escaped + r'(?:[\s,;).:/]|$)'
    return bool(re.search(pattern, text))


# Common words to skip in acronym/term extraction
_SKIP_ACRONYMS = {
    "the", "and", "for", "are", "you", "our", "will", "can", "has",
    "not", "all", "but", "who", "how", "may", "its", "etc",
}

_SKIP_TERMS = {
    "the", "this", "that", "these", "those",
    "monday", "tuesday", "wednesday", "thursday", "friday",
    "saturday", "sunday",
    "january", "february", "march", "april", "may", "june",
    "july", "august", "september", "october", "november", "december",
    "united states", "new york", "san francisco", "los angeles",
}
