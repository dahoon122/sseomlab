"""CLI 진입점.

예시:
  python -m sseomlab run --region 대구 --region 경북 --out data/output/대구경북.xlsx
  python -m sseomlab run --dry-run        # 외부 API 없이 배선 검증
"""

from __future__ import annotations

import typer

from sseomlab.pipeline import run as run_pipeline

app = typer.Typer(help="웨딩/돌상 전환 가능 숨은 공간 발굴 시스템")


@app.callback()
def _main() -> None:
    """sseomlab CLI. 하위 명령으로 `run` 을 사용하세요."""


@app.command()
def run(
    region: list[str] = typer.Option(None, help="대상 지역 (반복 지정). 미지정 시 전체"),
    space_type: list[str] = typer.Option(None, help="공간 유형 (반복 지정). 미지정 시 전체"),
    out: str = typer.Option("data/output/sseomlab_result.xlsx", help="엑셀 출력 경로"),
    limit: int = typer.Option(None, help="처리 장소 수 제한 (테스트용)"),
    dry_run: bool = typer.Option(False, "--dry-run", help="외부 API 없이 가짜 데이터로 실행"),
):
    """발굴 파이프라인 실행."""
    path = run_pipeline(
        regions=region or None,
        space_types=space_type or None,
        out_path=out,
        dry_run=dry_run,
        limit=limit,
    )
    typer.echo(f"완료: {path}")


if __name__ == "__main__":
    app()
