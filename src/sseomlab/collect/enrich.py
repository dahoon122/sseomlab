"""2단계 정보 보강 (스텁).

1차 수집(naver_local)은 상호/주소/카테고리 위주라 분석 신호가 부족하다.
여기서 다음을 보강한다:
  - 네이버 블로그 검색 API → 리뷰 텍스트 합본 (raw_text)
  - 홈페이지 HTML → 소개/대관 문구
  - 사진 URL 수집 → 사진 분석 입력
  - 인스타 노출도(해시태그/게시물 수) 추정

각 함수는 외부 연동 골격이며, 구현 시 ToS·rate limit 을 준수해야 한다.
인스타그램은 비공식 스크래핑이 ToS 위반이므로, 공개 검색결과 기반의
'노출 강도 추정'만 수행하고 개인정보/비공개 데이터는 수집하지 않는다.
"""

from __future__ import annotations

from sseomlab.models import Place


def enrich_with_blog_reviews(place: Place) -> Place:
    """네이버 블로그 검색 API 로 리뷰 텍스트/리뷰 수를 보강. (TODO 구현)"""
    # TODO: GET https://openapi.naver.com/v1/search/blog.json?query={name}
    #       → 본문 합쳐 place.raw_text 누적, place.blog_review_count 설정
    return place


def enrich_with_homepage(place: Place) -> Place:
    """홈페이지가 있으면 소개/대관/주차 문구를 raw_text 에 보강. (TODO 구현)"""
    # TODO: httpx + BeautifulSoup 로 본문 텍스트 추출 (robots 준수)
    return place


def enrich_with_images(place: Place, max_images: int = 4) -> Place:
    """사진 URL 을 수집해 image_urls 채움. (TODO 구현)"""
    # TODO: 공식 API/공개 이미지 한도 내 수집
    return place


def enrich(place: Place) -> Place:
    place = enrich_with_blog_reviews(place)
    place = enrich_with_homepage(place)
    place = enrich_with_images(place)
    return place
