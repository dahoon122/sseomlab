"""오프라인(목업 CSV + 규칙기반) 공간 파이프라인 테스트."""

from sseomlab import pipeline


def _records():
    return pipeline.build_records(csv_path="data/sample_candidates.csv", dry_run=False)


def test_wedding_halls_excluded():
    names = {r.place.name for r in _records()}
    assert "제이드웨딩컨벤션" not in names      # 웨딩홀 제외
    assert "부산하우스웨딩하우스" not in names   # 하우스웨딩 제외


def test_susumilso_is_strong_candidate():
    recs = {r.place.name: r for r in _records()}
    assert "수수밀소" in recs
    s = recs["수수밀소"].score
    assert s.grade.value in ("A", "B")
    assert s.dolsang_conversion_score >= 60


def test_priorities_are_unique_and_sorted():
    recs = _records()
    prios = sorted(r.contact_priority for r in recs)
    assert prios == list(range(1, len(recs) + 1))
    # 우선순위 1은 종합점수 최고
    top = min(recs, key=lambda r: r.contact_priority)
    assert top.score.composite_score == max(r.score.composite_score for r in recs)


def test_a_grade_counts_by_region():
    counts = pipeline.a_grade_counts_by_region(_records())
    assert sum(counts.values()) >= 1
