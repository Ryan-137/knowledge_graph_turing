from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from src.preprocess import run_document_preprocess, run_sentence_preprocess


DEFAULT_SOURCES = "configs/sources.yaml"
DEFAULT_DOCUMENTS = "data/processed/documents.json"
DEFAULT_DOCUMENT_REPORT = "data/processed/document_preprocess_report.json"
DEFAULT_SENTENCES = "data/processed/sentences.json"
DEFAULT_SENTENCE_REPORT = "data/processed/sentence_preprocess_report.json"


def _resolve_path(repo_root: Path, path_value: str) -> Path:
    path = Path(path_value)
    if path.is_absolute():
        return path
    return repo_root / path


def _build_preprocess_parser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    preprocess_parser = subparsers.add_parser(
        "preprocess",
        help="执行预处理流程。",
        description="执行文档级、句子级或全量预处理流程。",
    )
    preprocess_parser.add_argument(
        "stage",
        nargs="?",
        choices=("documents", "sentences", "all"),
        default="all",
        help="要执行的预处理阶段，默认执行全量流程。",
    )
    preprocess_parser.add_argument(
        "--sources",
        default=DEFAULT_SOURCES,
        help="来源登记文件路径。",
    )
    preprocess_parser.add_argument(
        "--documents",
        default=DEFAULT_DOCUMENTS,
        help="文档级预处理结果路径。",
    )
    preprocess_parser.add_argument(
        "--document-report",
        default=DEFAULT_DOCUMENT_REPORT,
        help="文档级预处理报告路径。",
    )
    preprocess_parser.add_argument(
        "--sentences",
        default=DEFAULT_SENTENCES,
        help="句子级预处理结果路径。",
    )
    preprocess_parser.add_argument(
        "--sentence-report",
        default=DEFAULT_SENTENCE_REPORT,
        help="句子级预处理报告路径。",
    )
    preprocess_parser.add_argument(
        "--strict",
        action="store_true",
        help="只要存在错误就返回失败。",
    )
    preprocess_parser.set_defaults(handler=_handle_preprocess)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="knowledge_graph 项目主入口。")
    subparsers = parser.add_subparsers(dest="command")
    _build_preprocess_parser(subparsers)
    return parser


def _run_document_stage(args: argparse.Namespace, repo_root: Path) -> None:
    document_count, error_count = run_document_preprocess(
        repo_root=repo_root,
        config_path=_resolve_path(repo_root, args.sources),
        output_path=_resolve_path(repo_root, args.documents),
        report_path=_resolve_path(repo_root, args.document_report),
        strict=args.strict,
    )
    print(f"文档级预处理完成：成功 {document_count} 个，错误 {error_count} 个。")
    print(f"documents.json: {_resolve_path(repo_root, args.documents).as_posix()}")
    print(f"report.json: {_resolve_path(repo_root, args.document_report).as_posix()}")


def _run_sentence_stage(args: argparse.Namespace, repo_root: Path) -> None:
    sentence_count, error_count = run_sentence_preprocess(
        documents_path=_resolve_path(repo_root, args.documents),
        output_path=_resolve_path(repo_root, args.sentences),
        report_path=_resolve_path(repo_root, args.sentence_report),
        strict=args.strict,
    )
    print(f"句子级预处理完成：成功 {sentence_count} 条，错误 {error_count} 条。")
    print(f"sentences.json: {_resolve_path(repo_root, args.sentences).as_posix()}")
    print(f"report.json: {_resolve_path(repo_root, args.sentence_report).as_posix()}")


def _handle_preprocess(args: argparse.Namespace, repo_root: Path) -> int:
    if args.stage in {"documents", "all"}:
        _run_document_stage(args, repo_root)

    if args.stage in {"sentences", "all"}:
        _run_sentence_stage(args, repo_root)

    return 0


def main(argv: Sequence[str] | None = None, repo_root: Path | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    actual_repo_root = repo_root or Path(__file__).resolve().parent.parent

    if not getattr(args, "command", None):
        parser.print_help()
        return 1

    handler = getattr(args, "handler", None)
    if handler is None:
        parser.print_help()
        return 1

    return handler(args, actual_repo_root)
