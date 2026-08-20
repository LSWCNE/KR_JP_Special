// 공통 유틸리티

async function api(path, options = {}) {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    let detail = res.statusText;
    try { const j = await res.json(); detail = j.detail || detail; } catch (e) {}
    throw new Error(detail);
  }
  return res.json();
}

function natBadge(nat) {
  if (nat === "KR") return `<span class="badge kr">${t("badge.kr")}</span>`;
  if (nat === "JP") return `<span class="badge jp">${t("badge.jp")}</span>`;
  return `<span class="badge flag">${t("badge.unknown")}</span>`;
}

// 간단한 마크다운 -> HTML 변환 (AI 답변 등 신뢰할 수 없는 텍스트에 사용, XSS 방지를 위해 먼저 이스케이프 후 변환)
function escapeHtml(str) {
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

async function loadSurveyLink() {
  const link = document.getElementById("survey-link");
  if (!link) return;
  try {
    const { survey_form_url } = await api("/api/ai/survey-url");
    link.href = survey_form_url || "#";
    link.style.display = survey_form_url ? "" : "none";
  } catch (e) {
    // 설문 링크는 부가 기능이므로 실패해도 조용히 무시
  }
}

document.addEventListener("DOMContentLoaded", loadSurveyLink);
// 다른 탭(예: 관리자 페이지)에서 URL을 바꾼 뒤 이 탭으로 돌아왔을 때도
// 새로고침 없이 최신 값을 반영하도록, 탭이 다시 보일 때마다 재조회한다.
document.addEventListener("visibilitychange", () => {
  if (document.visibilityState === "visible") loadSurveyLink();
});

function renderMarkdown(text) {
  const escaped = escapeHtml(text || "");
  const lines = escaped.split("\n");
  const htmlLines = [];
  let listItems = null;

  const flushList = () => {
    if (listItems) {
      htmlLines.push(`<ul>${listItems.join("")}</ul>`);
      listItems = null;
    }
  };

  const inline = (line) => line
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
    .replace(/(?<!\*)\*([^*]+)\*(?!\*)/g, "<em>$1</em>")
    .replace(/\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>');

  for (const rawLine of lines) {
    const line = rawLine.trim();
    const bullet = line.match(/^[-*]\s+(.*)$/);
    if (bullet) {
      if (!listItems) listItems = [];
      listItems.push(`<li>${inline(bullet[1])}</li>`);
      continue;
    }
    flushList();
    if (!line) {
      htmlLines.push("<br>");
    } else {
      htmlLines.push(`<p>${inline(line)}</p>`);
    }
  }
  flushList();
  return htmlLines.join("");
}
