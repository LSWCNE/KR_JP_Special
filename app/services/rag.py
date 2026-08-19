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
from app.services import sheet_sync

try:
    import anthropic
except ImportError:  # pragma: no cover
    anthropic = None

CLAUDE_MODEL = os.environ.get("CLAUDE_MODEL", "claude-sonnet-4-5-20250929")

# 응답 데이터가 너무 커지면 컨텍스트가 비대해지므로 국적별 상한을 둔다.
MAX_RESPONSES_PER_NATIONALITY = 150

# 채팅 화면의 카테고리(이름/예시 질문)는 관리자 페이지에서 자유롭게 추가/삭제/수정할 수
# 있도록 AppSetting에 JSON 목록으로 저장한다. 카테고리는 설문 문항을 걸러내는 용도가
# 아니라 Claude에게 "지금 이 주제에 집중해서 답하라"고 안내하는 용도로만 쓰이므로(아래
# CATEGORY_SYSTEM_EXTRA 참고), 문항 매칭 키워드 같은 별도 설정이 필요 없다.
CATEGORIES_SETTING_KEY = "chat_categories"

DEFAULT_CATEGORIES = [
    {
        "key": "movie", "ko": "영화", "ja": "映画",
        "example_ko": "일본 학생들이 좋아하는 한국 영화가 뭐야?",
        "example_ja": "日本の学生が好きな韓国映画は?",
    },
    {
        "key": "music", "ko": "음악", "ja": "音楽",
        "example_ko": "한국 학생들에게 인기있는 일본 음악은?",
        "example_ja": "韓国の学生に人気の日本の音楽は?",
    },
    {
        "key": "hobby", "ko": "취미", "ja": "趣味",
        "example_ko": "", "example_ja": "",
    },
    {
        "key": "food", "ko": "음식", "ja": "料理",
        "example_ko": "일본 학생들이 좋아하는 한국 음식은?",
        "example_ja": "日本の学生が好きな韓国料理は?",
    },
    {
        "key": "travel", "ko": "여행", "ja": "旅行",
        "example_ko": "일본인에게 추천할 만한 한국 여행지 알려줘",
        "example_ja": "日本人におすすめの韓国の旅行先を教えて",
    },
    {
        "key": "anime", "ko": "애니메이션", "ja": "アニメ",
        "example_ko": "요즘 유행하는 애니메이션 추천해줘",
        "example_ja": "最近流行っているアニメを教えて",
    },
]


def load_categories_list(db: Session) -> list[dict]:
    """관리자가 저장한 카테고리 목록(순서 보존)을 불러오고, 없으면 기본값을 반환."""
    raw = sheet_sync.get_setting(db, CATEGORIES_SETTING_KEY)
    if raw:
        try:
            data = json.loads(raw)
            if isinstance(data, list) and data:
                return data
        except (json.JSONDecodeError, TypeError):
            pass
    return DEFAULT_CATEGORIES


def save_categories_list(db: Session, categories: list[dict]) -> None:
    sheet_sync.set_setting(db, CATEGORIES_SETTING_KEY, json.dumps(categories, ensure_ascii=False))


def load_categories(db: Session) -> dict[str, dict]:
    """key -> 카테고리 정보 dict (라벨 조회용)."""
    return {c["key"]: c for c in load_categories_list(db) if c.get("key")}


def build_response_context(db: Session, category: str | None = None) -> dict:
    """국적별 응답 건수와, 문항별로 정리된 원문 답변 목록을 구성.

    category는 문항 데이터를 걸러내지 않는다 (카테고리에 키워드가 없으므로 항상 전체
    문항을 포함) - 대신 시스템 프롬프트에 카테고리 라벨을 전달해 Claude가 해당 주제
    위주로 답하도록 안내하는 데만 쓰인다.
    """
    categories = load_categories(db)
    category = category if category in categories else None

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
        "category": category,
        "category_labels": {"ko": categories[category]["ko"], "ja": categories[category]["ja"]} if category else None,
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

CATEGORY_SYSTEM_EXTRA = {
    "ko": (
        "[최우선 규칙 - 아래의 다른 모든 지침보다 먼저 적용하세요]\n"
        "지금 사용자는 '{category_label}' 카테고리를 선택한 상태입니다. 답변을 작성하기 전에 "
        "사용자의 질문이 '{category_label}' 주제와 명확히 관련되어 있는지부터 판단하세요.\n"
        "- 관련이 있는 경우: <survey_data>에서 '{category_label}' 주제와 관련된 항목만 근거로 삼아, "
        "아래 지침에 따라 답변하세요.\n"
        "- 관련이 없는 경우(다른 카테고리 주제, 설문과 무관한 잡담, 일반 지식 질문 등): 아래 지침을 "
        "따르지 말고 다른 내용은 절대 덧붙이지 말고 정확히 다음 문장으로만 답변하세요: "
        "\"이 카테고리에서는 '{category_label}' 관련 질문만 답변할 수 있어요. 다른 주제가 궁금하시면 "
        "해당 카테고리를 선택해주세요.\"\n\n"
    ),
    "ja": (
        "[最優先ルール - 以下の他のすべての指示より先に適用してください]\n"
        "ユーザーは現在「{category_label}」カテゴリーを選択しています。回答を作成する前に、"
        "ユーザーの質問が「{category_label}」というテーマと明確に関連しているかをまず判断してください。\n"
        "- 関連している場合: <survey_data>の中から「{category_label}」に関連する項目だけを根拠にし、"
        "以下の指示に従って回答してください。\n"
        "- 関連していない場合(他のカテゴリーの話題、アンケートと無関係な雑談、一般知識の質問など): "
        "以下の指示には従わず、他の内容を一切付け加えず、正確に次の文だけで回答してください: "
        "「このカテゴリーでは「{category_label}」に関する質問にのみお答えできます。他のテーマが気になる"
        "場合は該当するカテゴリーを選択してください。」\n\n"
    ),
}

MUSIC_SYSTEM_EXTRA = {
    "ko": (
        "\n12. 음악을 추천할 때는 먼저 <survey_data>에서 실제로 언급된 곡/아티스트를 추천하고, "
        "이어서 그 아티스트의 다른 곡 중 설문에는 없지만 당신이 알고 있는 곡을 1~2개 추가로 추천하세요. "
        "이 추가 추천은 반드시 \"(AI 추가 추천, 설문 데이터에는 없음)\"이라고 표시해 설문 근거와 구분하세요."
    ),
    "ja": (
        "\n12. 音楽をおすすめする際は、まず<survey_data>で実際に挙げられている曲・アーティストをおすすめし、"
        "続けてそのアーティストの他の曲の中で、アンケートには出てこないがあなたが知っている曲を1〜2曲追加でおすすめしてください。"
        "この追加のおすすめには必ず「(AIによる追加おすすめ、アンケートデータにはありません)」と明記し、"
        "アンケート根拠のものと区別してください。"
    ),
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


def _build_system_prompt(lang: str, category: str | None, category_label: str | None) -> str:
    prompt = SYSTEM_PROMPTS[lang]
    if category and category_label:
        prompt = CATEGORY_SYSTEM_EXTRA[lang].format(category_label=category_label) + prompt
        if category == "music":
            prompt += MUSIC_SYSTEM_EXTRA[lang]
    return prompt


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
    category_label = (context.get("category_labels") or {}).get(lang)
    try:
        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=800,
            system=_build_system_prompt(lang, context.get("category"), category_label),
            messages=[{"role": "user", "content": user_content}],
        )
        return response.content[0].text
    except Exception as e:  # noqa: BLE001
        return _msg(lang, "api_error", e=e)
