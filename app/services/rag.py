"""기능③④ 통합: 구글 폼 자유응답 데이터를 근거로 Claude가 질문에 답하고 추천도 함께 제공하는 RAG

설문이 전부 주관식(영화/음악/음식/여행지/애니 등 자유 서술)이라 고정된 태그 체계 대신,
국적(KR/JP)별로 원문 답변을 그대로 모아 Claude에게 넘기고, Claude가 직접 빈도/패턴을
파악해 답변·추천·설명을 생성하도록 한다. 데이터 규모가 작은 동안(수십~수백 건)은
별도 벡터 검색 없이 전체 컨텍스트를 주입하는 것으로 충분하다.

UI에서 선택한 언어(한국어/일본어)에 맞춰 Claude가 그 언어로 답변하도록 시스템 프롬프트와
폴백 안내 메시지를 언어별로 분리해뒀다.
"""
import os
import json
from collections import defaultdict

from sqlalchemy.orm import Session

from app.models import SurveyResponse

try:
    import anthropic
except ImportError:  # pragma: no cover
    anthropic = None

CLAUDE_MODEL = os.environ.get("CLAUDE_MODEL", "claude-sonnet-4-5-20250929")

# 응답 데이터가 너무 커지면 컨텍스트가 비대해지므로 국적별 상한을 둔다.
MAX_RESPONSES_PER_NATIONALITY = 150


def build_response_context(db: Session) -> dict:
    """국적별 응답 건수와, 문항별로 정리된 원문 답변 목록을 구성."""
    responses = (
        db.query(SurveyResponse)
        .filter(SurveyResponse.excluded == False)  # noqa: E712
        .order_by(SurveyResponse.id)
        .all()
    )

    counts = {"KR": 0, "JP": 0, "UNKNOWN": 0}
    # {question_header: {"KR": [answers], "JP": [answers]}}
    by_question: dict[str, dict[str, list[str]]] = defaultdict(lambda: {"KR": [], "JP": []})

    per_nat_used = {"KR": 0, "JP": 0}
    truncated = {"KR": False, "JP": False}

    for r in responses:
        counts[r.nationality] = counts.get(r.nationality, 0) + 1
        if r.nationality not in ("KR", "JP"):
            continue
        if per_nat_used[r.nationality] >= MAX_RESPONSES_PER_NATIONALITY:
            truncated[r.nationality] = True
            continue
        per_nat_used[r.nationality] += 1
        for question, answer in (r.raw_answers or {}).items():
            if answer:
                by_question[question][r.nationality].append(answer)

    return {
        "counts": counts,
        "by_question": by_question,
        "truncated": truncated,
    }


SYSTEM_PROMPTS = {
    "ko": """당신은 한일 문화교류 서비스의 AI 어시스턴트입니다.
아래 <survey_data>는 한국(KR)·일본(JP) 학생들이 실제로 응답한 설문(영화, 음악, 아티스트,
취미, 좋아하는/싫어하는 음식, 인상 깊었던 여행지, 추천하고 싶은 명소, 애니메이션,
가보고 싶은 나라, 버킷리스트 등)의 원문 응답입니다.
반드시 이 데이터에 포함된 내용만 근거로 사용자의 질문에 한국어로 답변하세요.

답변 시 반드시:
1. 설문 데이터를 내부적인 근거로 활용하되, 답변에 불필요한 통계나 분석 과정을 출력하지 마세요.
   "몇 명 중 몇 명이 언급했다", "어떤 응답자가 언급했다" 등의 상세한 근거 설명은 기본적으로 생략하세요.
2. 사용자가 추천을 요청하면 설문 데이터에서 실제로 언급된 항목 중 질문과 가장 관련성이 높은 항목을 추천하세요.
3. 추천 결과는 항목명과 짧은 설명만 제공하고, 설문 데이터를 분석하는 과정이나 근거를 장황하게 설명하지 마세요.
4. 데이터에 없는 내용은 추측하지 말고 "설문 데이터에서는 확인되지 않습니다"라고 답변하세요.
5. 질문과 관련 없는 설문 문항이나 데이터를 답변에 포함하지 마세요.
6. 답변은 최대한 간결하게 작성하세요.
7. 여행지, 음식, 영화, 음악 등 여러 항목을 추천하는 경우 다음과 같이 번호 목록으로 출력하세요.

1. 항목명 - 짧은 추천 이유
2. 항목명 - 짧은 추천 이유
3. 항목명 - 짧은 추천 이유

8. 추천 결과가 여러 개일 경우 기본적으로 3개 이내로 추천하세요.
9. 사용자가 단순히 특정 항목을 물어본 경우에는 번호 목록을 사용하지 않아도 됩니다.
10. 답변에서 "설문 데이터에 따르면", "몇 명이", "몇 명 중", "응답자들은" 등의 표현을 불필요하게 반복하지 마세요.
""",
    "ja": """あなたは日韓文化交流サービスのAIアシスタントです。
以下の<survey_data>は、韓国(KR)・日本(JP)の学生たちが実際に回答したアンケート
（映画、音楽、アーティスト、趣味、好きな/嫌いな食べ物、印象に残った旅行先、
おすすめしたい観光地、アニメ、行ってみたい国、やってみたいことなど）の原文回答です。
必ずこのデータに含まれている内容だけを根拠として、ユーザーの質問に日本語で答えてください。

回答する際は必ず:
1. アンケートデータを内部的な根拠として使用しますが、回答に不要な統計や分析過程は出力しないでください。
   「何人中何人が挙げた」「どの回答者が挙げた」などの詳しい根拠説明は基本的に省略してください。
2. ユーザーがおすすめを求めた場合は、アンケートデータに実際に含まれている項目の中から、質問に最も関連するものをおすすめしてください。
3. おすすめは項目名と短い理由だけを簡潔に示し、アンケートデータの分析過程や根拠を長く説明しないでください。
4. データにない内容は推測せず、「アンケートデータでは確認できません」と答えてください。
5. 質問と関係のない設問やデータは回答に含めないでください。
6. 回答はできるだけ簡潔にしてください。
7. 旅行先、食べ物、映画、音楽などを複数おすすめする場合は、以下のような番号リストで出力してください。

1. 項目名 - 短いおすすめ理由
2. 項目名 - 短いおすすめ理由
3. 項目名 - 短いおすすめ理由

8. 複数のおすすめを出す場合は、基本的に3つ以内にしてください。
9. ユーザーが特定の項目について質問した場合は、番号リストを使用しなくても構いません。
10. 回答では「アンケートデータによると」「何人が」「何人中」「回答者は」などの表現を不必要に繰り返さないでください。
""",
}

FALLBACK_MESSAGES = {
    "ko": {
        "no_anthropic": "anthropic 패키지가 설치되어 있지 않습니다. `pip install anthropic`을 실행해주세요.",
        "no_api_key": (
            "ANTHROPIC_API_KEY가 설정되어 있지 않습니다. 프로젝트 루트의 .env 파일에 "
            "ANTHROPIC_API_KEY=sk-ant-... 형태로 키를 추가한 뒤 서버를 다시 시작해주세요."
        ),
        "no_data": (
            "아직 분석할 설문 응답 데이터가 없습니다. 관리자 페이지(/admin)에서 구글 시트 CSV 링크를 "
            "설정하고 동기화를 실행해주세요."
        ),
        "api_error": "Claude API 호출 중 오류가 발생했습니다: {e}",
    },
    "ja": {
        "no_anthropic": "anthropicパッケージがインストールされていません。`pip install anthropic` を実行してください。",
        "no_api_key": (
            "ANTHROPIC_API_KEYが設定されていません。プロジェクトルートの.envファイルに "
            "ANTHROPIC_API_KEY=sk-ant-... の形式でキーを追加し、サーバーを再起動してください。"
        ),
        "no_data": (
            "まだ分析できるアンケート回答データがありません。管理者ページ(/admin)でGoogleスプレッドシートの"
            "CSVリンクを設定し、同期を実行してください。"
        ),
        "api_error": "Claude APIの呼び出し中にエラーが発生しました: {e}",
    },
}


def _msg(lang: str, key: str, **kwargs) -> str:
    lang = lang if lang in FALLBACK_MESSAGES else "ko"
    text = FALLBACK_MESSAGES[lang][key]
    return text.format(**kwargs) if kwargs else text


def _build_user_content(question: str, context: dict) -> str:
    counts = context["counts"]
    by_question = context["by_question"]

    lines = [
        f"한국(KR) 응답 {counts.get('KR', 0)}건, 일본(JP) 응답 {counts.get('JP', 0)}건"
        + (f", 국적 미판별 {counts.get('UNKNOWN', 0)}건" if counts.get("UNKNOWN") else "")
    ]
    if context["truncated"]["KR"] or context["truncated"]["JP"]:
        lines.append("(참고: 응답 수가 많아 일부만 표본으로 사용했습니다)")

    survey_data = {
        question_header: {
            "KR": answers.get("KR", []),
            "JP": answers.get("JP", []),
        }
        for question_header, answers in by_question.items()
    }

    return (
        f"{chr(10).join(lines)}\n\n"
        f"<survey_data>\n{json.dumps(survey_data, ensure_ascii=False, indent=2)}\n</survey_data>\n\n"
        f"질문: {question}"
    )


def call_claude(question: str, context: dict, lang: str = "ko") -> str:
    lang = lang if lang in SYSTEM_PROMPTS else "ko"

    if anthropic is None:
        return _msg(lang, "no_anthropic")

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return _msg(lang, "no_api_key")

    if context["counts"].get("KR", 0) == 0 and context["counts"].get("JP", 0) == 0:
        return _msg(lang, "no_data")

    client = anthropic.Anthropic(api_key=api_key)
    user_content = _build_user_content(question, context)
    try:
        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=800,
            system=SYSTEM_PROMPTS[lang],
            messages=[{"role": "user", "content": user_content}],
        )
        return response.content[0].text
    except Exception as e:  # noqa: BLE001
        return _msg(lang, "api_error", e=e)
