import argparse
import hashlib
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

from bs4 import BeautifulSoup

try:
    from pypdf import PdfReader  # type: ignore
except ImportError:
    PdfReader = None

try:
    from PyPDF2 import PdfReader as LegacyPdfReader  # type: ignore
except ImportError:
    LegacyPdfReader = None


SUPPORTED_SUFFIXES = {".html", ".htm", ".txt", ".md", ".pdf"}
TEXTUAL_SUFFIXES = {".html", ".htm", ".txt", ".md"}
SKIP_DIR_MARKERS = ("_files",)
MIN_SENTENCE_LENGTH = 6
MAX_LINE_SYMBOL_RATIO = 0.35

COMMON_CONTENT_SELECTORS = [
    "article",
    "main",
    "[role='main']",
    ".article",
    ".article-content",
    ".article__content",
    ".content",
    ".content-main",
    ".post-content",
    ".entry-content",
    ".rich_text",
    ".RichText",
    ".WikiText",
    ".lemmaWgt-lemmaTitle",
    ".main-content",
]

NOISE_PATTERNS = [
    re.compile(r"^\s*$"),
    re.compile(r"^https?://", re.IGNORECASE),
    re.compile(r"^(var|let|const)\s+[A-Za-z0-9_$]+\s*=", re.IGNORECASE),
    re.compile(r"^[.#]?[A-Za-z0-9_-]+\s*\{"),
    re.compile(r"^@(?:media|font-face|keyframes)\b", re.IGNORECASE),
    re.compile(r"^(function\s*\(|!function\s*\()", re.IGNORECASE),
    re.compile(r"^\d+\s*$"),
    re.compile(r"^(登录|注册|分享|收藏|点赞|评论|上一篇|下一篇)$"),
]

SENTENCE_PUNCTUATION = "。！？!?；;：:."


@dataclass
class DocumentRecord:
    doc_id: str
    title: str
    source_path: str
    source_type: str
    clean_text: str
    sentences: list[str]
    char_count: int


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Preprocess source files for the Turing knowledge graph.")
    parser.add_argument(
        "--input-dir",
        default="source",
        help="Directory that contains raw source files. Default: source",
    )
    parser.add_argument(
        "--output-dir",
        default="preprocessed",
        help="Directory for cleaned output. Default: preprocessed",
    )
    return parser


def list_source_files(input_dir: Path) -> list[Path]:
    files: list[Path] = []
    for path in input_dir.rglob("*"):
        if not path.is_file():
            continue
        if any(marker in part for marker in SKIP_DIR_MARKERS for part in path.parts):
            continue
        if path.suffix.lower() in SUPPORTED_SUFFIXES:
            files.append(path)
    return sorted(files)


def slugify(name: str) -> str:
    normalized = re.sub(r"[\\/:*?\"<>|]+", " ", name)
    normalized = re.sub(r"\s+", "_", normalized.strip())
    return normalized or "document"


def make_doc_id(path: Path) -> str:
    digest = hashlib.md5(str(path).encode("utf-8")).hexdigest()[:8]
    return f"{slugify(path.stem)[:40]}_{digest}"


def read_text_file(path: Path) -> str:
    for encoding in ("utf-8", "utf-8-sig", "gb18030", "latin-1"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return path.read_text(encoding="utf-8", errors="ignore")


def remove_non_content_tags(soup: BeautifulSoup) -> None:
    for tag in soup.find_all(
        [
            "script",
            "style",
            "noscript",
            "svg",
            "form",
            "button",
            "header",
            "footer",
            "nav",
            "aside",
            "iframe",
        ]
    ):
        tag.decompose()


def text_density_score(element) -> float:
    text = element.get_text(" ", strip=True)
    if len(text) < 80:
        return 0.0

    paragraphs = len(element.find_all(["p", "li"]))
    headers = len(element.find_all(["h1", "h2", "h3"]))
    links = len(element.find_all("a"))
    link_text_length = sum(len(link.get_text(" ", strip=True)) for link in element.find_all("a"))
    link_density = link_text_length / max(len(text), 1)

    return len(text) + paragraphs * 120 + headers * 40 - links * 25 - link_density * 400


def choose_best_container(soup: BeautifulSoup):
    for selector in COMMON_CONTENT_SELECTORS:
        node = soup.select_one(selector)
        if node and len(node.get_text(" ", strip=True)) >= 120:
            return node

    candidates = soup.find_all(["article", "main", "section", "div", "body"])
    if not candidates:
        return soup

    return max(candidates, key=text_density_score)


def extract_title(soup: BeautifulSoup, fallback: str) -> str:
    if soup.title and soup.title.get_text(strip=True):
        return normalize_title(soup.title.get_text(" ", strip=True))

    for meta_key in ("og:title", "twitter:title"):
        meta = soup.find("meta", attrs={"property": meta_key}) or soup.find("meta", attrs={"name": meta_key})
        if meta and meta.get("content"):
            return normalize_title(str(meta["content"]))

    first_heading = soup.find(["h1", "h2"])
    if first_heading and first_heading.get_text(strip=True):
        return normalize_title(first_heading.get_text(" ", strip=True))

    return normalize_title(fallback)


def get_meta_content(soup: BeautifulSoup, *names: str) -> str:
    for name in names:
        meta = soup.find("meta", attrs={"name": name}) or soup.find("meta", attrs={"property": name})
        if meta and meta.get("content"):
            return clean_inline_text(str(meta["content"]))
    return ""


def extract_site_name(soup: BeautifulSoup) -> str:
    return get_meta_content(soup, "og:site_name")


def normalize_title(value: str) -> str:
    value = clean_inline_text(value)
    value = re.sub(r"\s*[-_|]\s*(BBC News|知乎|百度百科|Wikiwand|The Guardian)\s*$", "", value, flags=re.IGNORECASE)
    return value


def gather_candidate_lines(container) -> list[str]:
    lines: list[str] = []
    block_tags = ["h1", "h2", "h3", "h4", "p", "li", "blockquote"]

    for node in container.find_all(block_tags):
        text = node.get_text(" ", strip=True)
        cleaned = clean_inline_text(text)
        if cleaned:
            lines.append(cleaned)

    if not lines:
        text = container.get_text("\n", strip=True)
        lines.extend(clean_inline_text(line) for line in text.splitlines())

    return lines


def clean_inline_text(text: str) -> str:
    text = text.replace("\xa0", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def is_noise_line(line: str) -> bool:
    if any(pattern.search(line) for pattern in NOISE_PATTERNS):
        return True

    if len(line) < 2:
        return True

    letters = sum(char.isalnum() for char in line)
    symbols = sum(not char.isalnum() and not char.isspace() for char in line)
    if line and symbols / max(len(line), 1) > MAX_LINE_SYMBOL_RATIO and letters < 12:
        return True

    if line.count("{") > 0 or line.count("}") > 0:
        return True

    if re.search(r"\.(js|css|png|jpg|jpeg|webp|svg)(\b|$)", line, re.IGNORECASE):
        return True

    return False


def deduplicate_lines(lines: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []

    for line in lines:
        normalized = re.sub(r"\s+", " ", line).strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        result.append(normalized)

    return result


def clean_lines(lines: list[str]) -> list[str]:
    cleaned = [line for line in lines if not is_noise_line(line)]
    cleaned = deduplicate_lines(cleaned)
    cleaned = [line for line in cleaned if not is_heading_noise(line)]
    return trim_non_content_edges(cleaned)


def has_sentence_punctuation(line: str) -> bool:
    return any(mark in line for mark in SENTENCE_PUNCTUATION)


def is_reference_line(line: str) -> bool:
    return bool(re.match(r"^\d+\s+.+(?:引用日期|出版社|新闻|Government|University)", line))


def is_heading_noise(line: str) -> bool:
    if has_sentence_punctuation(line):
        return False

    if re.search(r"[《》“”\"'()（）]", line):
        return False

    if re.search(r"\d{4}", line):
        return False

    compact = line.replace(" ", "")
    if len(compact) <= 6:
        return True

    groups = [group for group in line.split(" ") if group]
    if len(groups) >= 3 and all(len(group) <= 8 for group in groups):
        return True

    return False


def is_paragraph_like(line: str) -> bool:
    return len(line) >= 25 and has_sentence_punctuation(line)


def trim_non_content_edges(lines: list[str]) -> list[str]:
    if not lines:
        return []

    trimmed = list(lines)
    reference_index = next((idx for idx, line in enumerate(trimmed) if is_reference_line(line)), None)
    if reference_index is not None and reference_index > 2:
        trimmed = trimmed[:reference_index]

    if len(trimmed) <= 2:
        return trimmed

    first_paragraph_index = next(
        (idx for idx, line in enumerate(trimmed[1:], start=1) if is_paragraph_like(line)),
        None,
    )

    if first_paragraph_index and first_paragraph_index > 2:
        leading_lines = trimmed[1:first_paragraph_index]
        if leading_lines and all(not is_paragraph_like(line) for line in leading_lines):
            trimmed = [trimmed[0]] + trimmed[first_paragraph_index:]

    return trimmed


def split_sentences(text: str) -> list[str]:
    normalized = text
    normalized = re.sub(r"(\.{3,})", r"\1\n", normalized)
    normalized = re.sub(r"([。！？!?；;])", r"\1\n", normalized)
    normalized = re.sub(r"([.])\s+(?=[A-Z0-9\"'])", r"\1\n", normalized)

    sentences: list[str] = []
    for part in normalized.splitlines():
        part = clean_inline_text(part)
        if len(part) >= MIN_SENTENCE_LENGTH:
            sentences.append(part)

    return deduplicate_lines(sentences)


def extract_baike_text(soup: BeautifulSoup, fallback: str) -> tuple[str, str]:
    title = extract_title(soup, fallback=fallback)
    description = get_meta_content(soup, "description", "og:description")

    lines = [title]
    if description:
        lines.append(description)

    return title, "\n".join(deduplicate_lines(lines))


def extract_text_from_html(path: Path) -> tuple[str, str]:
    html = read_text_file(path)
    soup = BeautifulSoup(html, "lxml")
    remove_non_content_tags(soup)

    site_name = extract_site_name(soup)
    if site_name == "百度百科" or "百度百科" in (soup.title.get_text(" ", strip=True) if soup.title else ""):
        return extract_baike_text(soup, fallback=path.stem)

    title = extract_title(soup, fallback=path.stem)
    container = choose_best_container(soup)
    raw_lines = gather_candidate_lines(container)
    cleaned_lines = clean_lines(raw_lines)

    if title and (not cleaned_lines or cleaned_lines[0] != title):
        cleaned_lines.insert(0, title)

    return title, "\n".join(cleaned_lines)


def extract_text_from_plaintext(path: Path) -> tuple[str, str]:
    text = read_text_file(path)
    lines = [clean_inline_text(line) for line in text.splitlines()]
    cleaned_lines = clean_lines(lines)
    title = cleaned_lines[0] if cleaned_lines else path.stem
    return title, "\n".join(cleaned_lines)


def extract_text_from_pdf(path: Path) -> tuple[str, str]:
    reader_cls = PdfReader or LegacyPdfReader
    if reader_cls is None:
        title = path.stem
        message = (
            f"{title}\n"
            "[PDF extraction skipped: install pypdf or PyPDF2 to enable PDF text extraction.]"
        )
        return title, message

    reader = reader_cls(str(path))
    pages: list[str] = []
    for page in reader.pages:
        page_text = page.extract_text() or ""
        if page_text.strip():
            pages.append(page_text)

    lines = []
    for page_text in pages:
        for line in page_text.splitlines():
            cleaned = clean_inline_text(line)
            if cleaned:
                lines.append(cleaned)

    cleaned_lines = clean_lines(lines)
    title = cleaned_lines[0] if cleaned_lines else path.stem
    return title, "\n".join(cleaned_lines)


def extract_document(path: Path) -> DocumentRecord:
    suffix = path.suffix.lower()
    if suffix in {".html", ".htm"}:
        title, clean_text = extract_text_from_html(path)
        source_type = "html"
    elif suffix == ".pdf":
        title, clean_text = extract_text_from_pdf(path)
        source_type = "pdf"
    else:
        title, clean_text = extract_text_from_plaintext(path)
        source_type = "text"

    sentences = split_sentences(clean_text.replace("\n", " "))

    return DocumentRecord(
        doc_id=make_doc_id(path),
        title=title,
        source_path=str(path.as_posix()),
        source_type=source_type,
        clean_text=clean_text,
        sentences=sentences,
        char_count=len(clean_text),
    )


def write_outputs(records: list[DocumentRecord], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    text_dir = output_dir / "texts"
    text_dir.mkdir(parents=True, exist_ok=True)

    payload = [asdict(record) for record in records]
    (output_dir / "documents.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    summary = {
        "document_count": len(records),
        "total_sentences": sum(len(record.sentences) for record in records),
        "total_characters": sum(record.char_count for record in records),
    }
    (output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    for record in records:
        text_path = text_dir / f"{record.doc_id}.txt"
        text_path.write_text(record.clean_text, encoding="utf-8")


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)

    if not input_dir.exists():
        raise FileNotFoundError(f"Input directory does not exist: {input_dir}")

    source_files = list_source_files(input_dir)
    if not source_files:
        raise FileNotFoundError(f"No supported source files were found in: {input_dir}")

    records = [extract_document(path) for path in source_files]
    write_outputs(records, output_dir)

    print(f"Processed {len(records)} documents into: {output_dir}")


if __name__ == "__main__":
    main()
