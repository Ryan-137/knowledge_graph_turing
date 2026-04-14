from __future__ import annotations


NOISE_TAGS = {
    "script",
    "style",
    "noscript",
    "svg",
    "img",
    "picture",
    "video",
    "audio",
    "canvas",
    "iframe",
    "form",
    "button",
    "input",
    "select",
    "option",
    "textarea",
}

NOISE_KEYWORDS = {
    "nav",
    "menu",
    "footer",
    "header",
    "breadcrumb",
    "cookie",
    "consent",
    "newsletter",
    "subscribe",
    "search",
    "social",
    "share",
    "related",
    "sidebar",
    "comment",
    "login",
    "signup",
    "advert",
    "promo",
    "banner",
    "toolbar",
    "pagination",
    "popup",
    "modal",
}

CONTENT_SELECTORS = (
    "article",
    "main",
    "[role='main']",
    ".article",
    ".article-content",
    ".article-body",
    ".entry-content",
    ".post-content",
    ".page-content",
    ".story-body",
    ".node-content",
    ".content",
    "#content",
    "#main-content",
    "#main",
)

BLOCK_TAGS = ("h1", "h2", "h3", "p", "li", "blockquote")
PROTECTED_CONTENT_TAGS = {"html", "body", "main", "article"}
