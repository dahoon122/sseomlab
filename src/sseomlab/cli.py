"""CLI 진입점 — 제이드컴퍼니 내부 의사결정 시스템.

예시:
  python -m sseomlab run --region 대구 --region 경북     # 공간 발굴 + 컨셉 제안서
  python -m sseomlab run --dry-run                       # 외부 API 없이 배선 검증
  python -m sseomlab forecast --dry-run                  # 돌잔치 수요·매출 예측 + 광고타이밍
"""

from __future__ import annotations

import typer

from sseomlab import pipeline
from sseomlab.demand.pipeline import run as run_forecast
from sseomlab.pipeline import run as run_pipeline

app = typer.Typer(help="제이드컴퍼니 웨딩/돌잔치 사업 분석 시스템 (공간 발굴 + 수요예측 + 컨셉 제안)")


@app.callback()
def _main() -> None:
    """sseomlab CLI. 하위 명령으로 `run` 을 사용하세요."""


@app.command()
def run(
    region: list[str] = typer.Option(None, help="대상 지역 (반복 지정). 미지정 시 전체"),
    space_type: list[str] = typer.Option(None, help="공간 유형 (반복 지정). 미지정 시 전체"),
    source: str = typer.Option("auto", help="수집원: auto | csv(목업) | naver(실제, 네이버 키 필요)"),
    scoring: str = typer.Option("heuristic", help="점수: heuristic(키 불필요) | llm(Claude 키 필요)"),
    out: str = typer.Option("data/output/sseomlab_result.xlsx", help="점수표 엑셀 경로"),
    proposal_out: str = typer.Option("data/output/sseomlab_proposals.xlsx", help="컨셉 제안서(12필드) 엑셀 경로"),
    limit: int = typer.Option(None, help="처리 장소 수 제한 (테스트용)"),
    dry_run: bool = typer.Option(False, "--dry-run", help="외부 API 없이 가짜 데이터로 실행"),
):
    """공간 발굴 → 점수화 → 컨셉 제안서 생성.

    예) 네이버 키만으로 실제 수집:  run --source naver --region 대구
    """
    path = run_pipeline(
        regions=region or None,
        space_types=space_type or None,
        source=source,
        scoring=scoring,
        out_path=out,
        proposal_path=proposal_out,
        dry_run=dry_run,
        limit=limit,
    )
    typer.echo(f"완료: 점수표 {path}, 제안서 {proposal_out}")


@app.command()
def forecast(
    region: list[str] = typer.Option(None, help="대상 지역 (반복 지정). 미지정 시 전체"),
    actuals: str = typer.Option("data/jade_actuals.csv", help="제이드 실적 CSV (있으면 전환율 보정)"),
    out: str = typer.Option("data/output/demand_forecast.xlsx", help="수요예측 엑셀 경로"),
    dry_run: bool = typer.Option(False, "--dry-run", help="KOSIS 없이 합성 출생데이터로 실행"),
):
    """출생아 수 기반 12개월 뒤 돌잔치 수요·매출 예측 + 광고 투입 시점 추천."""
    path = run_forecast(
        regions=region or None,
        actuals_csv=actuals,
        out_path=out,
        dry_run=dry_run,
    )
    typer.echo(f"완료: {path}")


@app.command()
def intel(
    region: list[str] = typer.Option(None, help="대상 지역 (반복 지정). 미지정 시 전체"),
    csv_in: str = typer.Option("data/sample_candidates.csv", help="공간 후보 CSV (목업)"),
    dry_run: bool = typer.Option(True, "--dry-run/--live", help="기본 목업 모드 (키 불필요)"),
):
    """[통합] 공간 발굴 + 수요/공급/기회 리포트를 한 번에 생성하는 시장 인텔리전스 실행."""
    # 1) 공간 발굴 → 점수표/제안서/공간DB
    records = pipeline.build_records(
        regions=region or None, csv_path=None if not dry_run else csv_in, dry_run=dry_run
    )
    pipeline.run(regions=region or None, csv_path=None if not dry_run else csv_in, dry_run=dry_run)
    counts = pipeline.a_grade_counts_by_region(records)

    # 2) 수요·매출·공급부족·기회 리포트 (A등급 발굴 수 연동)
    run_forecast(regions=region or None, a_grade_counts=counts, dry_run=dry_run)

    typer.echo(
        f"완료: 공간 {len(records)}건 분석, A등급 {sum(counts.values())}건. "
        "결과는 data/output/ (점수표·제안서·공간DB·영업키트·수요예측·공급부족·지역별기회)"
    )


if __name__ == "__main__":
    app()
