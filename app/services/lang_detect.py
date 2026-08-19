"""응답 텍스트의 문자 구성(한글/가나/한자)으로 국적(한국/일본)을 자동 판별하는 유틸리티.

이 설문은 국적을 직접 묻지 않고, "한국인은 한국어로, 일본인은 일본어로 답변했다"는
전제로 운영되었기 때문에 응답 텍스트 자체의 스크립트(한글 vs 가나)로 국적을 추정한다.
100% 정확할 수 없으므로 admin 페이지에서 수동 보정이 가능하도록 confidence와
manual override 플래그를 함께 반환/저장한다.
"""
import re

HANGUL_RE = re.compile(r"[가-힣ᄀ-ᇿ㄰-㆏]")
KANA_RE = re.compile(r"[぀-ゟ゠-ヿ]")  # 히라가나 + 가타카나
KANJI_RE = re.compile(r"[一-鿿]")  # 한자/칸지 공용 범위 (모호하므로 가중치 낮게)


def classify_nationality(text: str) -> tuple[str, float]:
    """반환: (nationality, confidence) — nationality는 'KR' | 'JP' | 'UNKNOWN'"""
    if not text:
        return "UNKNOWN", 0.0

    hangul_count = len(HANGUL_RE.findall(text))
    kana_count = len(KANA_RE.findall(text))
    kanji_count = len(KANJI_RE.findall(text))

    kr_score = hangul_count
    # 가나는 일본어의 결정적 신호. 한자는 한국어 텍스트에도 드물게 섞이므로 가중치를 낮춤.
    jp_score = kana_count * 1.5 + kanji_count * 0.3

    total = kr_score + jp_score
    if total == 0:
        return "UNKNOWN", 0.0

    if kr_score >= jp_score:
        nationality = "KR"
    else:
        nationality = "JP"

    confidence = abs(kr_score - jp_score) / total
    return nationality, round(confidence, 2)


def classify_response_row(answers: dict) -> tuple[str, float]:
    """13개 문항 답변 전체를 합쳐서 국적을 판별 (개별 답변 하나보다 훨씬 안정적)."""
    combined = " ".join(str(v) for v in answers.values() if v)
    return classify_nationality(combined)
