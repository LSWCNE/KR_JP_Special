// 한국어 / 일본어 UI 전환 (간단한 클라이언트 사이드 i18n)

const I18N = {
  ko: {
    "nav.brand": "한일문화교류 MVP",
    "nav.chat": "AI 채팅",
    "nav.admin": "관리자",
    "nav.survey": "설문 참여",
    "nav.logout": "로그아웃",
    "lang.toggle": "日本語",

    "admin_login.title": "관리자 로그인",
    "admin_login.password_label": "비밀번호",
    "admin_login.submit_btn": "로그인",

    "chat.title": "한일 문화교류 AI 채팅",
    "chat.subtitle": "구글 폼으로 수집한 한국·일본 학생들의 실제 설문 응답을 근거로, 질문에 답하고 콘텐츠를 추천해드립니다.",
    "chat.category_label": "카테고리 선택",
    "chat.category_all": "전체",
    "chat.category_hint_all": "카테고리를 선택하면 해당 주제 질문에만 집중해서 답변합니다.",
    "chat.category_hint_selected": "'{category}' 카테고리가 선택되었습니다. 이 주제와 관련된 질문만 답변할 수 있어요.",
    "chat.placeholder": "질문을 입력하세요",
    "chat.send": "전송",
    "chat.generating": "답변을 생성하는 중...",
    "chat.error_prefix": "오류: ",
    "chat.example_prefix": "예시: ",

    "admin.title": "데이터 관리 대시보드",
    "admin.subtitle": "구글 시트 동기화 상태와 응답 통계를 확인하고, 채팅 카테고리를 관리합니다.",
    "admin.sheet_section_title": "구글 시트 연동",
    "admin.csv_label": "웹에 게시(CSV) URL",
    "admin.save_btn": "URL 저장",
    "admin.survey_url_section_title": "설문 참여 링크 (홈 화면 버튼)",
    "admin.survey_url_label": "설문조사 페이지 URL (구글 폼)",
    "admin.categories_section_title": "채팅 카테고리 관리",
    "admin.categories_hint": "카테고리를 추가/삭제하고 이름·예시 질문을 수정할 수 있습니다. 카테고리는 설문 데이터를 걸러내지 않고, AI에게 \"이 주제 위주로 답하라\"고 안내하는 용도로만 쓰입니다.",
    "admin.cat_th_key": "key (영문/숫자, 예: pet)",
    "admin.cat_th_ko": "한국어 이름",
    "admin.cat_th_ja": "일본어 이름",
    "admin.cat_th_example_ko": "예시 질문(한국어)",
    "admin.cat_th_example_ja": "예시 질문(일본어)",
    "admin.cat_add_btn": "카테고리 추가",
    "admin.cat_save_btn": "카테고리 저장",
    "admin.sync_btn": "지금 동기화",
    "admin.no_sync_yet": "아직 동기화한 적이 없습니다.",
    "admin.last_sync_prefix": "마지막 동기화: ",
    "admin.url_saved": "URL이 저장되었습니다. '지금 동기화'를 눌러주세요.",
    "admin.syncing": "동기화 중...",
    "admin.sync_done": "동기화 완료: 현재 시트 기준 {new}건 반영 (중복 {duplicates}건 제외, CSV 총 {total}행). 이전 응답은 모두 교체되었습니다.",
    "admin.question_counts_title": "문항별 응답 건수",
    "admin.stat_total": "전체 응답",
    "admin.stat_kr": "한국(KR)",
    "admin.stat_jp": "일본(JP)",
    "admin.stat_unknown": "국적 미판별",
    "admin.stat_low_confidence": "검토 필요(낮은 신뢰도)",
    "admin.stat_excluded": "제외 처리됨",
  },
  ja: {
    "nav.brand": "日韓文化交流 MVP",
    "nav.chat": "AIチャット",
    "nav.admin": "管理者",
    "nav.survey": "アンケート参加",
    "nav.logout": "ログアウト",
    "lang.toggle": "한국어",

    "admin_login.title": "管理者ログイン",
    "admin_login.password_label": "パスワード",
    "admin_login.submit_btn": "ログイン",

    "chat.title": "日韓文化交流 AIチャット",
    "chat.subtitle": "Googleフォームで収集した韓国・日本の学生たちの実際のアンケート回答をもとに、質問に答えたりコンテンツをおすすめします。",
    "chat.category_label": "カテゴリーを選択",
    "chat.category_all": "すべて",
    "chat.category_hint_all": "カテゴリーを選ぶと、そのテーマの質問だけに集中して回答します。",
    "chat.category_hint_selected": "「{category}」カテゴリーが選択されています。このテーマに関する質問のみお答えできます。",
    "chat.placeholder": "質問を入力してください",
    "chat.send": "送信",
    "chat.generating": "回答を作成しています...",
    "chat.error_prefix": "エラー: ",
    "chat.example_prefix": "例: ",

    "admin.title": "データ管理ダッシュボード",
    "admin.subtitle": "Googleスプレッドシートの同期状況と回答統計を確認し、チャットカテゴリーを管理します。",
    "admin.sheet_section_title": "Googleスプレッドシート連携",
    "admin.csv_label": "ウェブに公開(CSV)のURL",
    "admin.save_btn": "URLを保存",
    "admin.survey_url_section_title": "アンケート参加リンク(ホーム画面のボタン)",
    "admin.survey_url_label": "アンケートページURL(Googleフォーム)",
    "admin.categories_section_title": "チャットカテゴリー管理",
    "admin.categories_hint": "カテゴリーを追加・削除したり、名前・例文を編集できます。カテゴリーはアンケートデータを絞り込むものではなく、AIに「このテーマ中心に答えて」と伝えるためだけに使われます。",
    "admin.cat_th_key": "key(英数字、例: pet)",
    "admin.cat_th_ko": "韓国語名",
    "admin.cat_th_ja": "日本語名",
    "admin.cat_th_example_ko": "例文(韓国語)",
    "admin.cat_th_example_ja": "例文(日本語)",
    "admin.cat_add_btn": "カテゴリーを追加",
    "admin.cat_save_btn": "カテゴリーを保存",
    "admin.sync_btn": "今すぐ同期",
    "admin.no_sync_yet": "まだ同期されていません。",
    "admin.last_sync_prefix": "最終同期: ",
    "admin.url_saved": "URLが保存されました。「今すぐ同期」を押してください。",
    "admin.syncing": "同期中...",
    "admin.sync_done": "同期完了: 現在のシート基準で{new}件を反映(重複{duplicates}件を除外、CSV合計{total}行)。以前の回答はすべて置き換えられました。",
    "admin.question_counts_title": "設問別の回答件数",
    "admin.stat_total": "全体の回答数",
    "admin.stat_kr": "韓国(KR)",
    "admin.stat_jp": "日本(JP)",
    "admin.stat_unknown": "国籍未判定",
    "admin.stat_low_confidence": "要確認(信頼度低)",
    "admin.stat_excluded": "除外済み",
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
