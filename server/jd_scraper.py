"""Job description scraper — fetch a URL and extract the JD text.

Uses httpx for HTTP requests and lxml for HTML parsing.
Falls back to largest text block if no known JD container found.
"""

from __future__ import annotations

import re

import httpx
from lxml import html


# CSS-style selectors mapped to XPath for common JD containers
_JD_XPATHS = [
    # Class-based
    '//*[contains(@class,"job-description")]',
    '//*[contains(@class,"jobDescription")]',
    '//*[contains(@class,"job_description")]',
    '//*[contains(@class,"posting-description")]',
    '//*[contains(@class,"job-details")]',
    '//*[contains(@class,"jobDetails")]',
    '//*[contains(@class,"description__text")]',
    '//*[contains(@class,"job-posting")]',
    # ID-based
    '//*[contains(@id,"job-description")]',
    '//*[contains(@id,"jobDescription")]',
    '//*[contains(@id,"job_description")]',
    '//*[contains(@id,"job-details")]',
    # Semantic
    '//article[contains(@class,"job")]',
    '//section[contains(@class,"description")]',
]

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "en-US,en;q=0.9",
}


def fetch_page(url: str, timeout: float = 15.0) -> str:
    """Fetch a web page and return raw HTML."""
    resp = httpx.get(url, headers=_HEADERS, timeout=timeout, follow_redirects=True)
    resp.raise_for_status()
    return resp.text


def extract_jd_text(page_html: str) -> str:
    """Extract job description text from HTML.

    Tries known JD container selectors first, then falls back
    to the largest text block on the page.
    """
    tree = html.fromstring(page_html)

    # Try known JD containers
    for xpath in _JD_XPATHS:
        elements = tree.xpath(xpath)
        if elements:
            text = _element_text(elements[0])
            if len(text) > 100:  # Must have meaningful content
                return text

    # Fallback: find largest div/article/section by text length
    best_text = ""
    for tag in ("div", "article", "section", "main"):
        for el in tree.xpath(f"//{tag}"):
            text = _element_text(el)
            if len(text) > len(best_text):
                best_text = text

    return best_text if len(best_text) > 50 else ""


def scrape_jd(url: str) -> str:
    """Full pipeline: fetch URL → extract JD text."""
    page_html = fetch_page(url)
    return extract_jd_text(page_html)


def _element_text(el) -> str:
    """Extract and clean text from an lxml element."""
    # Get all text content, preserving some structure
    parts = []
    for text in el.itertext():
        cleaned = text.strip()
        if cleaned:
            parts.append(cleaned)

    text = " ".join(parts)
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text)
    # Add line breaks for list items and headings
    text = re.sub(r'\s*([•·\-]\s)', r'\n\1', text)
    return text.strip()
