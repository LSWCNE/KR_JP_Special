// 한국어 / 일본어 UI 전환 (간단한 클라이언트 사이드 i18n)

const I18N = {
  ko: {
    "nav.brand": "한일문화교류 MVP",
    "nav.chat": "AI 채팅",
    "nav.admin": "관리자",
    "lang.toggle": "日本語",

    "chat.title": "한일 문화교류 AI 채팅",
    "chat.subtitle": "구글 폼으로 수집한 한국·일본 학생들의 실제 설문 응답을 근거로, 질문에 답하고 콘텐츠를 추천해드립니다.",
    "chat.category_label": "카테고리 선택",
    "chat.category_all": "전체",
    "chat.category_hint_all": "카테고리를 선택하면 해당 주제 질문에만 집중해서 답변합니다.",
    "chat.category_hint_selected": "'{category}' 카테고리가 선택되었습니다. 이 주제와 관련된 질문만 답변할 수 있어요.",
    "chat.placeholder": "질문을 입력하세요",
    "chat.send": "전송",
    "chat.hint": "예시: \"일본 학생들이 좋아하는 한국 음식은?\" · \"한국 학생들에게 인기있는 일본 애니는?\" · \"일본인에게 추천할 만한 한국 여행지 알려줘\" · \"요즘 유행하는 애니메이션 추천해줘\"",
    "chat.generating": "답변을 생성하는 중...",
    "chat.error_prefix": "오류: ",

    "admin.title": "데이터 관리 대시보드",
    "admin.subtitle": "구글 시트 동기화 상태와 응답 국적 자동 판별 결과를 점검·보정합니다.",
    "admin.sheet_section_title": "구글 시트 연동",
    "admin.csv_label": "웹에 게시(CSV) URL",
    "admin.save_btn": "URL 저장",
    "admin.sync_btn": "지금 동기화",
    "admin.no_sync_yet": "아직 동기화한 적이 없습니다.",
    "admin.last_sync_prefix": "마지막 동기화: ",
    "admin.url_saved": "URL이 저장되었습니다. '지금 동기화'를 눌러주세요.",
    "admin.syncing": "동기화 중...",
    "admin.sync_done": "동기화 완료: 신규 {new}건, 기존 {skipped}건 (CSV 총 {total}행)",
    "admin.question_counts_title": "문항별 응답 건수",
    "admin.review_title": "국적 판별 검토가 필요한 응답",
    "admin.review_checkbox_label": "검토 필요 응답만 보기 (미판별 또는 낮은 신뢰도)",
    "admin.th_id": "ID",
    "admin.th_nationality": "국적",
    "admin.th_confidence": "신뢰도",
    "admin.th_preview": "미리보기",
    "admin.th_submitted_at": "제출시각",
    "admin.th_correction": "보정",
    "admin.select_default": "국적 변경",
    "admin.select_kr": "한국(KR)",
    "admin.select_jp": "일본(JP)",
    "admin.select_unknown": "미판별",
    "admin.manual_tag": "(수동)",
    "admin.exclude_btn": "제외",
    "admin.unexclude_btn": "제외해제",
    "admin.no_review_needed": "검토가 필요한 응답이 없습니다.",
    "admin.ai_log_title": "최근 AI 질의 로그",
    "admin.no_ai_log": "아직 AI 질의 기록이 없습니다.",
    "admin.stat_total": "전체 응답",
    "admin.stat_kr": "한국(KR)",
    "admin.stat_jp": "일본(JP)",
    "admin.stat_unknown": "국적 미판별",
    "admin.stat_low_confidence": "검토 필요(낮은 신뢰도)",
    "admin.stat_excluded": "제외 처리됨",

    "badge.kr": "한국",
    "badge.jp": "일본",
    "badge.unknown": "미판별",
  },
  ja: {
    "nav.brand": "日韓文化交流 MVP",
    "nav.chat": "AIチャット",
    "nav.admin": "管理者",
    "lang.toggle": "한국어",

    "chat.title": "日韓文化交流 AIチャット",
    "chat.subtitle": "Googleフォームで収集した韓国・日本の学生たちの実際のアンケート回答をもとに、質問に答えたりコンテンツをおすすめします。",
    "chat.category_label": "カテゴリーを選択",
    "chat.category_all": "すべて",
    "chat.category_hint_all": "カテゴリーを選ぶと、そのテーマの質問だけに集中して回答します。",
    "chat.category_hint_selected": "「{category}」カテゴリーが選択されています。このテーマに関する質問のみお答えできます。",
    "chat.placeholder": "質問を入力してください",
    "chat.send": "送信",
    "chat.hint": "例:「日本の学生が好きな韓国料理は?」・「韓国の学生に人気の日本のアニメは?」・「日本人におすすめの韓国の旅行先を教えて」・「最近流行っているアニメを教えて」",
    "chat.generating": "回答を作成しています...",
    "chat.error_prefix": "エラー: ",

    "admin.title": "データ管理ダッシュボード",
    "admin.subtitle": "Googleスプレッドシートの同期状況と、回答の国籍自動判定結果を確認・修正します。",
    "admin.sheet_section_title": "Googleスプレッドシート連携",
    "admin.csv_label": "ウェブに公開(CSV)のURL",
    "admin.save_btn": "URLを保存",
    "admin.sync_btn": "今すぐ同期",
    "admin.no_sync_yet": "まだ同期されていません。",
    "admin.last_sync_prefix": "最終同期: ",
    "admin.url_saved": "URLが保存されました。「今すぐ同期」を押してください。",
    "admin.syncing": "同期中...",
    "admin.sync_done": "同期完了: 新規{new}件、既存{skipped}件(CSV合計{total}行)",
    "admin.question_counts_title": "設問別の回答件数",
    "admin.review_title": "国籍判定の確認が必要な回答",
    "admin.review_checkbox_label": "確認が必要な回答のみ表示(未判定または信頼度が低いもの)",
    "admin.th_id": "ID",
    "admin.th_nationality": "国籍",
    "admin.th_confidence": "信頼度",
    "admin.th_preview": "プレビュー",
    "admin.th_submitted_at": "送信日時",
    "admin.th_correction": "修正",
    "admin.select_default": "国籍を変更",
    "admin.select_kr": "韓国(KR)",
    "admin.select_jp": "日本(JP)",
    "admin.select_unknown": "未判定",
    "admin.manual_tag": "(手動)",
    "admin.exclude_btn": "除外",
    "admin.unexclude_btn": "除外解除",
    "admin.no_review_needed": "確認が必要な回答はありません。",
    "admin.ai_log_title": "最近のAI質問ログ",
    "admin.no_ai_log": "まだAIへの質問履歴がありません。",
    "admin.stat_total": "全体の回答数",
    "admin.stat_kr": "韓国(KR)",
    "admin.stat_jp": "日本(JP)",
    "admin.stat_unknown": "国籍未判定",
    "admin.stat_low_confidence": "要確認(信頼度低)",
    "admin.stat_excluded": "除外済み",

    "badge.kr": "韓国",
    "badge.jp": "日本",
    "badge.unknown": "未判定",
  },
};

function getLang() {
  return localStorage.getItem("kj_lang") || "ko";
}

function setLang(lang) {
  localStorage.setItem("kj_lang", lang);
  applyI18n();
  document.documentElement.lang = lang;
  const event = new CustomEvent("kj-lang-changed", { detail: { lang } });
  document.dispatchEvent(event);
}

function t(key, params) {
  const lang = getLang();
  let text = (I18N[lang] && I18N[lang][key]) || (I18N.ko[key]) || key;
  if (params) {
    for (const [k, v] of Object.entries(params)) {
      text = text.replace(new RegExp(`{${k}}`, "g"), v);
    }
  }
  return text;
}

function applyI18n() {
  const lang = getLang();
  document.querySelectorAll("[data-i18n]").forEach(el => {
    el.textContent = t(el.getAttribute("data-i18n"));
  });
  document.querySelectorAll("[data-i18n-placeholder]").forEach(el => {
    el.placeholder = t(el.getAttribute("data-i18n-placeholder"));
  });
  document.querySelectorAll("[data-i18n-title]").forEach(el => {
    el.title = t(el.getAttribute("data-i18n-title"));
  });
  const toggleBtn = document.getElementById("lang-toggle-btn");
  if (toggleBtn) toggleBtn.textContent = t("lang.toggle");
}

document.addEventListener("DOMContentLoaded", () => {
  document.documentElement.lang = getLang();
  applyI18n();
  const toggleBtn = document.getElementById("lang-toggle-btn");
  if (toggleBtn) {
    toggleBtn.addEventListener("click", () => {
      setLang(getLang() === "ko" ? "ja" : "ko");
    });
  }
});
