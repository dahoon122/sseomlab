"""공간 발굴 파이프라인 오케스트레이션.

수집 → 1차 제외필터 → 정보보강 → 판정/점수 → 우선순위 → 엑셀/CSV + 컨셉 제안서

모드:
  - csv_path 지정 또는 dry_run=True → CSV 입력 + 규칙기반(heuristic) 분석/점수 (키 불필요, MVP 기본)
  - 그 외 → 네이버 수집 + Claude 판정 (API 키 필요)
"""

from __future__ import annotations

from pathlib import Path

from sseomlab.analyze import exclusion
from sseomlab.analyze import heuristic as heuristic_analyze
from sseomlab.collect import csv_source, enrich, naver_local
from sseomlab.concept import recommender
from sseomlab.export import csv_out, excel, proposal_excel, sales_excel
from sseomlab.models import PlaceRecord
from sseomlab.sales import generator as sales_gen
from sseomlab.score import heuristic as heuristic_score
from sseomlab.score import scorer


def _assign_priority(records: list[PlaceRecord]) -> list[PlaceRecord]:
    """종합점수 내림차순으로 연락 우선순위(1..N) 부여."""
    ranked = sorted(records, key=lambda r: r.score.composite_score, reverse=True)
    for i, r in enumerate(ranked, start=1):
        r.contact_priority = i
    return ranked


def build_records(
    regions: list[str] | None = None,
    space_types: list[str] | None = None,
    csv_path: str | Path | None = None,
    source: str = "auto",        # auto | csv | naver
    scoring: str = "heuristic",  # heuristic(키 불필요) | llm(Claude 키 필요)
    dry_run: bool = False,
    limit: int | None = None,
) -> list[PlaceRecord]:
    """수집 → 제외필터 → 분석/점수 → 우선순위. 출력 전 단계 레코드를 반환.

    데이터 소스와 점수 방식을 분리:
      - source=naver + scoring=heuristic → 네이버 키만으로 실제 공간 수집·점수 (Claude 불필요)
      - source=csv (목업) → 키 없이 데모
      - scoring=llm → Claude 정밀 판정 (ANTHROPIC_API_KEY 필요)
    """
    if source == "auto":
        source = "csv" if (dry_run or csv_path is not None) else "naver"

    # 1) 수집
    if source == "csv":
        places = csv_source.load(csv_path or csv_source.DEFAULT_SAMPLE)
    else:
        places = naver_local.collect(regions, space_types)
    if regions:
        places = [p for p in places if p.region in regions]
    if limit:
        places = places[:limit]

    records: list[PlaceRecord] = []
    for place in places:
        # 2) 규칙 기반 1차 제외
        scr = exclusion.screen(place)
        if scr.exclude:
            continue

        # 3) 분석 + 점수
        if scoring == "llm":
            place = enrich.enrich(place)
            analysis, score = scorer.score_place(place, scr.soft_hits)
        else:
            analysis = heuristic_analyze.analyze(place)
            score = heuristic_score.score(place, analysis, scr.soft_hits)

        if analysis.exclude:
            continue
        records.append(PlaceRecord(place=place, analysis=analysis, score=score, contact_priority=0))

    # 4) 우선순위
    return _assign_priority(records)


def a_grade_counts_by_region(records: list[PlaceRecord]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for r in records:
        if r.score.grade.value == "A" and r.place.region:
            counts[r.place.region] = counts.get(r.place.region, 0) + 1
    return counts


def run(
    regions: list[str] | None = None,
    space_types: list[str] | None = None,
    out_path: str | Path = "data/output/sseomlab_result.xlsx",
    proposal_path: str | Path | None = "data/output/sseomlab_proposals.xlsx",
    csv_path: str | Path | None = None,
    source: str = "auto",
    scoring: str = "heuristic",
    dry_run: bool = False,
    limit: int | None = None,
) -> Path:
    use_llm = scoring == "llm"
    records = build_records(regions, space_types, csv_path, source, scoring, dry_run, limit)

    # 5) 출력: 점수표(xlsx+csv) + 컨셉 제안서(12필드, xlsx+csv) + A등급 공간 DB
    out = excel.export(records, out_path)
    csv_out.export_space_db(records, Path(out_path).with_suffix(".csv"))
    csv_out.export_a_grade(records, Path(out_path).with_name("space_db_A등급.csv"))
    if proposal_path:
        proposals = [recommender.build_proposal(r, claude_refine=use_llm) for r in records]
        proposal_excel.export(proposals, proposal_path)
        csv_out.export_proposals(proposals, Path(proposal_path).with_suffix(".csv"))

        # 6) 영업 키트 (공간별 DM/전화스크립트/상품/객단가/연락시점)
        kits = [
            sales_gen.build_sales_kit(r, p, claude_refine=use_llm)
            for r, p in zip(records, proposals)
        ]
        out_dir = Path(out_path).parent
        sales_excel.export(kits, out_dir / "영업키트.xlsx")
        csv_out.export_sales(kits, out_dir / "영업키트.csv")
    return out
