"""파이프라인 전 단계에서 공유하는 데이터 모델 (Pydantic).

수집(Place) → 분석(PlaceAnalysis) → 점수(PlaceScore) → 출력(PlaceRecord)
순으로 정보가 누적된다.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class SpaceType(str, Enum):
    정원카페 = "정원카페"
    한옥카페 = "한옥카페"
    브런치카페 = "브런치카페"
    독채식당 = "독채식당"
    베이커리카페 = "베이커리카페"
    오션뷰카페 = "오션뷰카페"
    숲속카페 = "숲속카페"
    복합문화공간 = "복합문화공간"
    기타 = "기타"


class Grade(str, Enum):
    A = "A"
    B = "B"
    C = "C"
    D = "D"


# --- 1단계: 수집 결과 ---------------------------------------------------------
class Place(BaseModel):
    """수집기에서 나오는 원천 장소 데이터."""

    source: str = Field(description="수집 출처 (naver_local, naver_blog 등)")
    place_id: Optional[str] = None
    name: str
    category: Optional[str] = None
    region: Optional[str] = None
    sub_area: Optional[str] = None
    address: Optional[str] = None
    road_address: Optional[str] = None
    phone: Optional[str] = None
    homepage: Optional[str] = None
    naver_place_url: Optional[str] = None
    instagram_url: Optional[str] = None
    naver_review_count: Optional[int] = None
    blog_review_count: Optional[int] = None
    image_urls: list[str] = Field(default_factory=list)
    raw_text: str = Field(default="", description="블로그/리뷰/소개 등 분석용 합본 텍스트")
    search_keyword: Optional[str] = None


# --- 2~3단계: 분석 결과 -------------------------------------------------------
class PlaceAnalysis(BaseModel):
    """텍스트/사진 분석 + 제외 판정 결과."""

    exclude: bool = False
    exclude_reason: str = ""
    space_type: SpaceType = SpaceType.기타

    # 사진 분석에서 추출한 정성 신호
    has_garden: bool = False
    has_yard: bool = False
    has_terrace: bool = False
    has_hanok: bool = False
    has_ocean_view: bool = False
    has_forest: bool = False
    has_large_window: bool = False  # 통창
    has_private_room: bool = False
    estimated_capacity: Optional[int] = None
    parking_likelihood: float = Field(default=0.0, ge=0, le=1)

    # 행사 운영 적합성 신호 (사진/데이터 분석)
    accessibility: float = Field(default=0.5, ge=0, le=1, description="접근성(교통/도심거리)")
    outdoor_usable: bool = False           # 야외 활용 가능
    rain_alternative: bool = False         # 우천 대체 실내 공간
    photo_potential: float = Field(default=0.5, ge=0, le=1, description="사진 촬영 포텐셜")
    private_event_possible: bool = False   # 프라이빗 단독 행사 가능

    # 노출/전문화 신호
    instagram_exposure: float = Field(default=0.0, ge=0, le=1, description="0=약함,1=과노출")
    wedding_mention_level: float = Field(default=0.0, ge=0, le=1, description="0=없음,1=많음")
    is_franchise: bool = False
    rental_signal: bool = False
    weekday_idle_likelihood: float = Field(default=0.0, ge=0, le=1)

    notes: str = ""


# --- 4~5단계: 점수 -----------------------------------------------------------
class PlaceScore(BaseModel):
    hidden_space_score: int = Field(ge=0, le=100)
    wedding_conversion_score: int = Field(ge=0, le=100)
    dolsang_conversion_score: int = Field(ge=0, le=100)
    collaboration_probability: int = Field(ge=0, le=100)
    composite_score: float = Field(ge=0, le=100, description="우선순위용 종합 점수")
    grade: Grade
    recommended_offer: str = ""


# --- 최종 출력 레코드 ---------------------------------------------------------
class PlaceRecord(BaseModel):
    """엑셀/구글시트 한 행에 대응하는 통합 레코드."""

    place: Place
    analysis: PlaceAnalysis
    score: PlaceScore
    contact_priority: int = Field(description="1이 가장 먼저 연락")
