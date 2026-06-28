import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv

from security_agent.application.generate_report import GenerateSecurityReport
from security_agent.application.prompt_builder import PromptBuilder
from security_agent.application.semantic_retriever import SemanticRetriever
from security_agent.infrastructure.file_security_repository import FileSecurityDataRepository
from security_agent.infrastructure.mimoe_embedding_client import MimoeEmbeddingClient
from security_agent.infrastructure.mimoe_llm_client import MimoeLLMClient

load_dotenv()

_DEFAULT_DATA_DIR = Path(__file__).parent.parent.parent / "data"
_DEFAULT_TOP_K    = 5


def _parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="security-agent",
        description="Security Anomaly Report Agent — powered by mimOE",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            '  python -m src.security_agent.main "Were there any after-hours intrusions?"\n'
            '  python -m src.security_agent.main "Summarize all critical alarms" --top-k 10\n'
        ),
    )
    parser.add_argument(
        "query",
        help="Security question or investigation prompt",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=_DEFAULT_TOP_K,
        metavar="N",
        help=f"Number of relevant documents to retrieve (default: {_DEFAULT_TOP_K})",
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=_DEFAULT_DATA_DIR,
        metavar="PATH",
        help=f"Path to data directory (default: {_DEFAULT_DATA_DIR})",
    )
    return parser.parse_args(argv)


def _build_use_case(data_dir: Path) -> GenerateSecurityReport:
    embedding_client = MimoeEmbeddingClient()
    return GenerateSecurityReport(
        repository=FileSecurityDataRepository(data_dir=data_dir),
        retriever=SemanticRetriever(embedding_client=embedding_client),
        prompt_builder=PromptBuilder(),
        llm_client=MimoeLLMClient(),
    )


def main(argv=None) -> None:
    args = _parse_args(argv)

    print(f"\nQuery : {args.query}")
    print(f"Top-K : {args.top_k}")
    print(f"Data  : {args.data_dir}\n")
    print("Embedding documents and retrieving context...")

    try:
        use_case = _build_use_case(args.data_dir)
        report   = use_case.execute(query=args.query, top_k=args.top_k)
    except RuntimeError as exc:
        print(f"\nError: {exc}", file=sys.stderr)
        sys.exit(1)

    print("\n" + "=" * 60)
    print(report)
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
