const path = require("path");
const pptxgen = require("pptxgenjs");

const IMG = (name) => path.join(__dirname, "images", name);

const INK = "152238";
const MUTED = "5F6878";
const PANEL = "F6F8FB";
const BORDER = "D6DDE8";
const ACCENT = "0F766E";     // teal - decision / merge / recommendation
const ACCENT_L = "2DD4BF";   // light teal for dark bg
const SUPPORT = "2563EB";    // blue - card / server
const WARNING = "D97706";    // orange - caution / false alarm
const WHITE = "FFFFFF";

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.333 x 7.5 in
pres.author = "jiyang";
pres.title = "HeatGridAgent - ML 모델 · Agent · 서버/프론트 구조";

const PAGE_W = 13.333;
const MARGIN = 0.6;
const CONTENT_W = PAGE_W - MARGIN * 2;

function badge(slide, num, opts = {}) {
  const { x = MARGIN, y = 0.5, dark = false } = opts;
  slide.addShape(pres.shapes.OVAL, {
    x, y, w: 0.5, h: 0.5,
    fill: { color: dark ? ACCENT_L : ACCENT },
    line: { type: "none" },
  });
  slide.addText(num, {
    x, y, w: 0.5, h: 0.5, align: "center", valign: "middle",
    fontFace: "Calibri", fontSize: 18, bold: true,
    color: dark ? INK : WHITE, margin: 0,
  });
}

function sectionHeader(slide, num, title, subtitle) {
  badge(slide, num);
  slide.addText(title, {
    x: MARGIN + 0.72, y: 0.42, w: CONTENT_W - 0.72, h: 0.6,
    fontFace: "Calibri", fontSize: 26, bold: true, color: INK, margin: 0, valign: "middle",
  });
  if (subtitle) {
    slide.addText(subtitle, {
      x: MARGIN + 0.72, y: 0.98, w: CONTENT_W - 0.72, h: 0.4,
      fontFace: "Calibri", fontSize: 13, color: MUTED, margin: 0,
    });
  }
}

function footerNote(slide, text) {
  slide.addText(text, {
    x: MARGIN, y: 7.08, w: CONTENT_W, h: 0.3,
    fontFace: "Calibri", fontSize: 9.5, color: MUTED, margin: 0,
  });
}

const TABLE_BORDER = { pt: 0.75, color: BORDER };
function headerCell(text) {
  return { text, options: { fill: { color: "EAF2F1" }, color: INK, bold: true, fontSize: 11.5, valign: "middle" } };
}
function bodyCell(text, opts = {}) {
  return { text, options: { fontSize: 10.5, color: INK, valign: "top", ...opts } };
}

// ---------------------------------------------------------------
// Slide 1 — Title
// ---------------------------------------------------------------
{
  const slide = pres.addSlide();
  slide.background = { color: INK };
  slide.addText("HeatGridAgent", {
    x: MARGIN, y: 2.55, w: CONTENT_W, h: 1.0,
    fontFace: "Calibri", fontSize: 46, bold: true, color: WHITE, margin: 0,
  });
  slide.addText("ML 모델 · Agent · 서버/프론트 구조", {
    x: MARGIN, y: 3.55, w: CONTENT_W, h: 0.7,
    fontFace: "Calibri", fontSize: 24, color: ACCENT_L, margin: 0,
  });
  slide.addText("2026-07-04 팀 회의 자료", {
    x: MARGIN, y: 4.35, w: CONTENT_W, h: 0.4,
    fontFace: "Calibri", fontSize: 14, color: "9AA5B5", margin: 0,
  });
  slide.addText(
    "자동 감지 에이전트가 만든 우선순위 카드를, 운영 보조 LLM 에이전트가 설명·문서화한다.",
    {
      x: MARGIN, y: 5.6, w: CONTENT_W - 1.5, h: 0.6,
      fontFace: "Calibri", fontSize: 13, italic: true, color: "C7D2E0", margin: 0,
    }
  );
}

// ---------------------------------------------------------------
// Slide 2 — 목차
// ---------------------------------------------------------------
{
  const slide = pres.addSlide();
  slide.background = { color: WHITE };
  slide.addText("목차", {
    x: MARGIN, y: 0.5, w: CONTENT_W, h: 0.7,
    fontFace: "Calibri", fontSize: 30, bold: true, color: INK, margin: 0,
  });
  const items = [
    ["01", "ML 모델", "문제 정의, 선정 기준, 선택된 모델, 병합 구조, 최종 선택 이유"],
    ["02", "Agent", "자동 감지 에이전트 -> 운영 보조 LLM 에이전트, DB 구성, 산출물 4종"],
    ["03", "서버 및 프론트", "ML/Agent 결과를 운영자가 반복 확인하는 서비스 표면 (제안)"],
  ];
  let y = 1.8;
  for (const [num, title, desc] of items) {
    badge(slide, num, { x: MARGIN, y });
    slide.addText(title, {
      x: MARGIN + 0.75, y: y - 0.06, w: 4.2, h: 0.6,
      fontFace: "Calibri", fontSize: 20, bold: true, color: INK, margin: 0, valign: "middle",
    });
    slide.addText(desc, {
      x: MARGIN + 5.1, y: y - 0.06, w: CONTENT_W - 5.1, h: 0.6,
      fontFace: "Calibri", fontSize: 13, color: MUTED, margin: 0, valign: "middle",
    });
    y += 1.55;
  }
  footerNote(slide, "근거: Notion(ML- 모델 선정 및 병합 / 보조자료 데이터_jiyang / Why Agent?), 11_신운영서비스 구현 확인");
}

// ---------------------------------------------------------------
// Slide 3 — ML 모델: 요약 + 문제정의/선정기준
// ---------------------------------------------------------------
{
  const slide = pres.addSlide();
  slide.background = { color: WHITE };
  sectionHeader(slide, "01", "ML 모델 — 문제 정의와 선정 기준", "단일 모델이 아니라 역할 분리 모델을 Priority Engine에서 병합한다.");

  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: MARGIN, y: 1.55, w: CONTENT_W, h: 1.15, rectRadius: 0.06,
    fill: { color: PANEL }, line: { color: BORDER, width: 0.75 },
  });
  slide.addText(
    "목표는 기계실 10분 단위 시계열을 7일 window feature로 요약해, 운영자가 먼저 봐야 할 설비와 조치 방향을 " +
    "안정적으로 고르는 것이다. AutoEncoder는 검토했지만 재구성 오차만으로 운영자가 납득할 원인 설명과 조치 문구를 " +
    "만들기 어려워 최종 구조에서 제외했다.",
    {
      x: MARGIN + 0.25, y: 1.68, w: CONTENT_W - 0.5, h: 0.9,
      fontFace: "Calibri", fontSize: 13, color: INK, margin: 0, valign: "middle", lineSpacingMultiple: 1.25,
    }
  );

  slide.addText("모델 선정 기준", {
    x: MARGIN, y: 2.95, w: CONTENT_W, h: 0.4,
    fontFace: "Calibri", fontSize: 15, bold: true, color: ACCENT, margin: 0,
  });

  const rows = [
    [headerCell("기준"), headerCell("의미")],
    [bodyCell("Window feature 적합성", { bold: true }), bodyCell("10분 원천값보다 7일 변화·품질·지속성을 반영한 feature가 운영 판단에 더 적합하다.")],
    [bodyCell("False alarm 억제", { bold: true }), bodyCell("운영 현장에서는 알림 수가 많아지는 것보다 신뢰 가능한 경보를 적게 내는 것이 중요하다.")],
    [bodyCell("Leadtime 표현", { bold: true }), bodyCell("단순 고장 여부가 아니라 0-24h, 1-3d, 3-7d 같은 대응 시간대를 함께 제공해야 한다.")],
    [bodyCell("Agent 설명 가능성", { bold: true }), bodyCell("카드·보고서·지시서로 전환할 수 있는 근거 필드와 규칙이 필요하다.")],
  ];
  slide.addTable(rows, {
    x: MARGIN, y: 3.4, w: CONTENT_W, colW: [3.0, CONTENT_W - 3.0],
    border: TABLE_BORDER, autoPage: false,
    rowH: 0.66,
  });
  footerNote(slide, "근거: 회의자료_ML모델_Agent구조.md 1장, Notion「ML- 모델 선정 및 병합」");
}

// ---------------------------------------------------------------
// Slide 4 — ML 구조도 (전체 이미지)
// ---------------------------------------------------------------
{
  const slide = pres.addSlide();
  slide.background = { color: WHITE };
  sectionHeader(slide, "01", "ML 모델 — 병합 구조도");

  const imgW = 2210, imgH = 1272;
  const maxH = 4.55;
  let w = maxH * (imgW / imgH);
  let h = maxH;
  if (w > CONTENT_W) { w = CONTENT_W; h = w * (imgH / imgW); }
  const x = (PAGE_W - w) / 2;
  slide.addImage({ path: IMG("01_ml_구조도.png"), x, y: 1.5, w, h });

  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: (PAGE_W - 8.5) / 2, y: 1.5 + h + 0.25, w: 8.5, h: 0.55, rectRadius: 0.06,
    fill: { color: INK }, line: { type: "none" },
  });
  slide.addText("priority_score  =  0.65 x current_best  +  0.35 x m1_specialist", {
    x: (PAGE_W - 8.5) / 2, y: 1.5 + h + 0.25, w: 8.5, h: 0.55, align: "center", valign: "middle",
    fontFace: "Consolas", fontSize: 14, bold: true, color: ACCENT_L, margin: 0,
  });
}

// ---------------------------------------------------------------
// Slide 5 — 선택된 모델 (핵심 모델 + Specialist 게이트)
// ---------------------------------------------------------------
{
  const slide = pres.addSlide();
  slide.background = { color: WHITE };
  sectionHeader(slide, "01", "ML 모델 — 선택된 모델과 확인 수치");

  const halfW = (CONTENT_W - 0.35) / 2;

  slide.addText("핵심 모델", {
    x: MARGIN, y: 1.5, w: halfW, h: 0.35,
    fontFace: "Calibri", fontSize: 14, bold: true, color: ACCENT, margin: 0,
  });
  const coreRows = [
    [headerCell("역할"), headerCell("모델"), headerCell("확인 수치")],
    [bodyCell("이상 감지", { bold: true }), bodyCell("Mahalanobis(LedoitWolf)\n+ IsolationForest"), bodyCell("정책: IF ratio>=0.90\nMahalanobis ratio>=1.00")],
    [bodyCell("위험 판단", { bold: true }), bodyCell("LightGBM risk binary"), bodyCell("precision 0.9483\nrecall 0.7458 / FPR 0.0129")],
    [bodyCell("발생 시점", { bold: true }), bodyCell("LightGBM leadtime\nmulticlass"), bodyCell("0-24h / 1-3d / 3-7d\n대응 시간대 구분")],
    [bodyCell("Hybrid Priority", { bold: true }), bodyCell("current_best 65%\n+ specialist 35%"), bodyCell("precision 0.8966\nrecall 0.6753 / FPR 0.0566")],
  ];
  slide.addTable(coreRows, {
    x: MARGIN, y: 1.9, w: halfW, colW: [1.35, 1.75, halfW - 3.1],
    border: TABLE_BORDER, autoPage: false, rowH: 0.72,
  });

  const rightX = MARGIN + halfW + 0.35;
  slide.addText("Specialist 게이트 4종 (M1 전용)", {
    x: rightX, y: 1.5, w: halfW, h: 0.35,
    fontFace: "Calibri", fontSize: 14, bold: true, color: ACCENT, margin: 0,
  });
  const gateRows = [
    [headerCell("게이트"), headerCell("모델"), headerCell("확인 수치")],
    [bodyCell("Fault Gate", { bold: true }), bodyCell("RandomForest\ndepth3"), bodyCell("bal.acc 0.8455\nrecall 0.8909 / FPR 0.2000")],
    [bodyCell("Task Gate", { bold: true }), bodyCell("RandomForest\ndepth3"), bodyCell("bal.acc 1.0000\nFPR 0.0000 (과최적화 의심)")],
    [bodyCell("Activity Gate", { bold: true }), bodyCell("RandomForest\ndepth3"), bodyCell("bal.acc 1.0000\nFPR 0.0000 (과최적화 의심)")],
    [bodyCell("Pre-event", { bold: true }), bodyCell("LogisticRegression"), bodyCell("bal.acc 0.8500\nrecall 0.7857 / FPR 0.0857")],
  ];
  slide.addTable(gateRows, {
    x: rightX, y: 1.9, w: halfW, colW: [1.3, 1.5, halfW - 2.8],
    border: TABLE_BORDER, autoPage: false, rowH: 0.72,
  });

  footerNote(slide, "Task/Activity Gate는 balanced accuracy 1.0000으로 window-policy 착시 가능성이 있어 추가 검증이 필요하다.");
}

// ---------------------------------------------------------------
// Slide 6 — 최종 선택 이유
// ---------------------------------------------------------------
{
  const slide = pres.addSlide();
  slide.background = { color: WHITE };
  sectionHeader(slide, "01", "ML 모델 — 최종 선택 이유");

  const reasons = [
    "ML 판단을 역할별로 나누어 이상 / 위험 / 발생 시점 / 이벤트 게이트를 각각 해석할 수 있다.",
    "Priority Engine이 최종 점수를 단일화하므로 운영 화면과 보고서는 하나의 정렬 기준을 쓸 수 있다.",
    "LLM은 모델 판단을 새로 만들지 않고, 이미 계산된 근거를 카드와 문서로 압축하므로 토큰 비용과 환각 위험을 줄인다.",
  ];
  let y = 1.75;
  reasons.forEach((text, i) => {
    slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x: MARGIN, y, w: CONTENT_W, h: 1.05, rectRadius: 0.06,
      fill: { color: PANEL }, line: { color: BORDER, width: 0.75 },
    });
    slide.addShape(pres.shapes.OVAL, {
      x: MARGIN + 0.3, y: y + 0.275, w: 0.5, h: 0.5,
      fill: { color: ACCENT }, line: { type: "none" },
    });
    slide.addText(String(i + 1), {
      x: MARGIN + 0.3, y: y + 0.275, w: 0.5, h: 0.5, align: "center", valign: "middle",
      fontFace: "Calibri", fontSize: 18, bold: true, color: WHITE, margin: 0,
    });
    slide.addText(text, {
      x: MARGIN + 1.1, y, w: CONTENT_W - 1.4, h: 1.05, valign: "middle",
      fontFace: "Calibri", fontSize: 14.5, color: INK, margin: 0, lineSpacingMultiple: 1.2,
    });
    y += 1.3;
  });
  footerNote(slide, "근거: 회의자료_ML모델_Agent구조.md — ML 모델 3절 최종 선택 이유");
}

// ---------------------------------------------------------------
// Slide 7 — Agent 전체 구성
// ---------------------------------------------------------------
{
  const slide = pres.addSlide();
  slide.background = { color: WHITE };
  sectionHeader(slide, "02", "Agent — 전체 구성", "자동 감지 에이전트의 출력이 운영 보조 LLM 에이전트의 입력이다.");

  const rows = [
    [headerCell("층"), headerCell("역할"), headerCell("출력")],
    [
      bodyCell("자동 감지\n에이전트", { bold: true, color: SUPPORT }),
      bodyCell("feature 계산, gate 실행, anomaly 실행,\nconflict resolve, priority score 계산"),
      bodyCell("agent_priority_card.csv"),
    ],
    [
      bodyCell("운영 보조\nLLM 에이전트", { bold: true, color: ACCENT }),
      bodyCell("카드 로드, 캐시 확인, DB 조회,\nRAG 검색, 근거 수집, 문서 작성"),
      bodyCell("운영 카드, 보고서,\n지시서, 관리소 알림"),
    ],
  ];
  slide.addTable(rows, {
    x: MARGIN, y: 1.75, w: CONTENT_W, colW: [2.4, 6.3, CONTENT_W - 8.7],
    border: TABLE_BORDER, autoPage: false, rowH: 1.0,
  });

  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: MARGIN, y: 4.35, w: CONTENT_W, h: 1.1, rectRadius: 0.06,
    fill: { color: PANEL }, line: { color: BORDER, width: 0.75 },
  });
  slide.addText(
    "즉, 앞단 Agent의 출력이 뒤단 LLM Agent의 입력이다. LLM은 고장 여부를 독립적으로 판단하지 않고, " +
    "카드에 들어 있는 score, level, reason, action을 운영자가 읽을 수 있는 문장으로 바꾼다.",
    {
      x: MARGIN + 0.25, y: 4.35, w: CONTENT_W - 0.5, h: 1.1, valign: "middle",
      fontFace: "Calibri", fontSize: 14, italic: true, color: INK, margin: 0, lineSpacingMultiple: 1.25,
    }
  );
}

// ---------------------------------------------------------------
// Slide 8 — DB 구성 & RAG 1차 MVP
// ---------------------------------------------------------------
{
  const slide = pres.addSlide();
  slide.background = { color: WHITE };
  sectionHeader(slide, "02", "Agent — DB 구성과 RAG 1차 MVP");

  const imgW = 2210, imgH = 1272;
  const leftW = 7.3;
  const h = leftW * (imgH / imgW);
  slide.addImage({ path: IMG("02_db_구성도.png"), x: MARGIN, y: 1.6, w: leftW, h });

  const rightX = MARGIN + leftW + 0.35;
  const rightW = CONTENT_W - leftW - 0.35;
  slide.addText("RAG 1차 MVP 자료 9종", {
    x: rightX, y: 1.5, w: rightW, h: 0.35,
    fontFace: "Calibri", fontSize: 14, bold: true, color: ACCENT, margin: 0,
  });
  const ragItems = [
    "열사용시설 기준 정보",
    "사용자 관리범위 및 책임구간",
    "공동주택 단지 목록",
    "공동주택 기본 정보",
    "공동주택 유지관리 이력",
    "ASOS 날씨",
    "특일 정보",
    "집단에너지시설 기술기준",
    "열공급시설 검사기준",
  ];
  const textRuns = [];
  ragItems.forEach((it, i) => {
    textRuns.push({ text: `${i + 1}. ${it}`, options: { breakLine: i !== ragItems.length - 1 } });
  });
  slide.addText(textRuns, {
    x: rightX, y: 1.9, w: rightW, h: 4.3,
    fontFace: "Calibri", fontSize: 12.5, color: INK, margin: 0, paraSpaceAfter: 7,
  });
  footerNote(slide, "선정 기준: 운영 해석 가능성 / 즉시 수집 가능성 / 현장 조치 연결성 / 데모 구현 비용");
}

// ---------------------------------------------------------------
// Slide 9 — Agent 구조도
// ---------------------------------------------------------------
{
  const slide = pres.addSlide();
  slide.background = { color: WHITE };
  sectionHeader(slide, "02", "Agent — 자동 감지와 LLM 에이전트 구조");

  const imgW = 2210, imgH = 1272;
  const maxH = 3.75;
  let w = maxH * (imgW / imgH);
  let h = maxH;
  if (w > CONTENT_W) { w = CONTENT_W; h = w * (imgH / imgW); }
  const x = (PAGE_W - w) / 2;
  slide.addImage({ path: IMG("03_agent_구조도.png"), x, y: 1.45, w, h });

  const capY = 1.45 + h + 0.2;
  const halfW = (CONTENT_W - 0.4) / 2;
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: MARGIN, y: capY, w: halfW, h: 0.75, rectRadius: 0.05,
    fill: { color: PANEL }, line: { color: BORDER, width: 0.75 },
  });
  slide.addText([
    { text: "OPS_GRAPH (10 노드)  ", options: { bold: true, color: SUPPORT } },
    { text: "observe -> compute_features -> run_gates -> run_anomaly -> resolve_conflicts -> score_priority -> upsert_cards -> select_top_n -> auto_brief -> record" },
  ], {
    x: MARGIN + 0.2, y: capY, w: halfW - 0.4, h: 0.75, valign: "middle",
    fontFace: "Calibri", fontSize: 9.5, color: INK, margin: 0, lineSpacingMultiple: 1.15,
  });
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: MARGIN + halfW + 0.4, y: capY, w: halfW, h: 0.75, rectRadius: 0.05,
    fill: { color: PANEL }, line: { color: BORDER, width: 0.75 },
  });
  slide.addText([
    { text: "CARD_GRAPH (5 노드)  ", options: { bold: true, color: ACCENT } },
    { text: "load_card -> check_cache -> gather_evidence -> compose -> persist" },
  ], {
    x: MARGIN + halfW + 0.6, y: capY, w: halfW - 0.4, h: 0.75, valign: "middle",
    fontFace: "Calibri", fontSize: 9.5, color: INK, margin: 0, lineSpacingMultiple: 1.15,
  });
}

// ---------------------------------------------------------------
// Slide 10 — 산출물 4종
// ---------------------------------------------------------------
{
  const slide = pres.addSlide();
  slide.background = { color: WHITE };
  sectionHeader(slide, "02", "Agent — 산출물 4종");

  const rows = [
    [headerCell("산출물"), headerCell("대상"), headerCell("핵심 내용")],
    [bodyCell("우선순위 알림 카드", { bold: true }), bodyCell("운영자"), bodyCell("score, level, why, recommended action")],
    [bodyCell("한난 내부 보고서", { bold: true }), bodyCell("내부 운영 및 회의"), bodyCell("고장 보고, 월간 요약, 연간 요약")],
    [bodyCell("정비업체 지시서", { bold: true }), bodyCell("현장 정비업체"), bodyCell("조치 항목, 확인 순서, 주의 기준")],
    [bodyCell("아파트 및 건물 관리소 알림", { bold: true }), bodyCell("관리소"), bodyCell("영향 가능성, 점검 예정, 안내 문구")],
  ];
  slide.addTable(rows, {
    x: MARGIN, y: 1.6, w: CONTENT_W, colW: [3.4, 2.7, CONTENT_W - 6.1],
    border: TABLE_BORDER, autoPage: false, rowH: 0.55,
  });

  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: MARGIN, y: 4.85, w: CONTENT_W, h: 1.1, rectRadius: 0.06,
    fill: { color: INK }, line: { type: "none" },
  });
  slide.addText(
    "Agent의 핵심 가치는 판단 압축이다. 분석은 코드와 ML이, 판단 후보는 룰과 ML이, " +
    "설명·문서화는 LLM이 담당한다 — 이 분담이 토큰 비용을 줄이면서도 운영자가 검토 가능한 형태를 유지한다.",
    {
      x: MARGIN + 0.3, y: 4.85, w: CONTENT_W - 0.6, h: 1.1, valign: "middle",
      fontFace: "Calibri", fontSize: 13, italic: true, color: ACCENT_L, margin: 0, lineSpacingMultiple: 1.25,
    }
  );
}

// ---------------------------------------------------------------
// Slide 11 — 서버 및 프론트
// ---------------------------------------------------------------
{
  const slide = pres.addSlide();
  slide.background = { color: WHITE };
  sectionHeader(slide, "03", "서버 및 프론트 — 권장 구조 (제안)");

  const imgW = 2210, imgH = 1272;
  const leftW = 6.9;
  const h = leftW * (imgH / imgW);
  slide.addImage({ path: IMG("04_서버_프론트_구조도.png"), x: MARGIN, y: 1.55, w: leftW, h });

  const rightX = MARGIN + leftW + 0.35;
  const rightW = CONTENT_W - leftW - 0.35;
  const rows = [
    [headerCell("구성"), headerCell("권장 역할")],
    [bodyCell("Scheduler", { bold: true }), bodyCell("replay tick / 주기 실행으로 OPS_GRAPH 실행")],
    [bodyCell("FastAPI Backend", { bold: true }), bodyCell("/cards, /actions, /rag, /replay, /ws 제공")],
    [bodyCell("PostgreSQL + pgvector", { bold: true }), bodyCell("agent_priority_card, agent_runs, llm_response_cache, doc_source/doc_chunks")],
    [bodyCell("LLM API 경유층", { bold: true }), bodyCell("캐시, 일일 예산, fallback template 적용")],
    [bodyCell("React Front", { bold: true }), bodyCell("운영 카드 대시보드, RAG 검색, 티켓, 실시간 WebSocket")],
  ];
  slide.addTable(rows, {
    x: rightX, y: 1.55, w: rightW, colW: [1.7, rightW - 1.7],
    border: TABLE_BORDER, autoPage: false, rowH: 0.58,
  });

  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: MARGIN, y: 1.55 + h + 0.2, w: leftW, h: 5.15 - h, rectRadius: 0.06,
    fill: { color: PANEL }, line: { color: BORDER, width: 0.75 },
  });
  slide.addText(
    "권고: 자동 감지가 카드를 만들고 LLM은 그 카드를 설명·문서화만 하는 지금 구조를 유지한 채, " +
    "서버/프론트는 카드를 빠르게 보여주고 액션으로 연결하는 데 집중한다. 우선순위 계산 로직은 프론트로 " +
    "내리지 않고 백엔드 정책 레이어에 묶어 일관성을 유지한다.",
    {
      x: MARGIN + 0.2, y: 1.55 + h + 0.2, w: leftW - 0.4, h: 5.15 - h, valign: "middle",
      fontFace: "Calibri", fontSize: 10.5, color: INK, margin: 0, lineSpacingMultiple: 1.2,
    }
  );
}

// ---------------------------------------------------------------
// Slide 12 — 회의에서 결정할 항목 (closing, dark)
// ---------------------------------------------------------------
{
  const slide = pres.addSlide();
  slide.background = { color: INK };
  slide.addText("회의에서 결정할 항목", {
    x: MARGIN, y: 0.55, w: CONTENT_W, h: 0.7,
    fontFace: "Calibri", fontSize: 28, bold: true, color: WHITE, margin: 0,
  });

  const items = [
    ["ML 기준", "Hybrid Priority를 공식 운영 점수로 사용"],
    ["Agent 범위", "LLM은 판단 생성이 아니라 설명과 문서화 담당"],
    ["RAG 1차 범위", "Notion 보조자료 9종을 MVP 기준으로 사용"],
    ["서버 우선순위", "카드 대시보드, WebSocket 업데이트, LLM 캐시, RAG 검색 순서"],
    ["남은 보완", "substation_id와 실제 단지·주소·책임구간 매핑 정교화"],
  ];
  let y = 1.55;
  for (const [k, v] of items) {
    slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x: MARGIN, y, w: CONTENT_W, h: 0.92, rectRadius: 0.05,
      fill: { color: "1E2A44" }, line: { type: "none" },
    });
    slide.addText(k, {
      x: MARGIN + 0.3, y, w: 2.6, h: 0.92, valign: "middle",
      fontFace: "Calibri", fontSize: 14, bold: true, color: ACCENT_L, margin: 0,
    });
    slide.addText(v, {
      x: MARGIN + 3.1, y, w: CONTENT_W - 3.4, h: 0.92, valign: "middle",
      fontFace: "Calibri", fontSize: 14, color: WHITE, margin: 0,
    });
    y += 1.05;
  }
}

pres.writeFile({ fileName: path.join(__dirname, "회의자료_ML모델_Agent구조.pptx") }).then(() => {
  console.log("pptx written");
});
