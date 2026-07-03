# HeatGrid Ops Design System

## 1. Atmosphere & Identity

조용한 운영 관제실이다. 첫 화면은 당장 처리할 카드, 근거, 비용, 리플레이 시계만 남기고 장식은 배제한다. 시그니처는 어두운 무광 표면 위에 위험도 색이 작은 신호처럼 떠 있는 구조다.

## 2. Color

| Role | Token | Dark | Usage |
|---|---|---|---|
| Surface/base | --surface-base | #101418 | Page background |
| Surface/panel | --surface-panel | #171d24 | Panels |
| Surface/raised | --surface-raised | #202832 | Repeated items |
| Text/primary | --text-primary | #edf2f7 | Main text |
| Text/secondary | --text-secondary | #9aa7b7 | Metadata |
| Border/default | --border-default | #2b3644 | Dividers |
| Accent/primary | --accent-primary | #43b3ae | Active controls |
| Status/urgent | --status-urgent | #e85d4f | Critical |
| Status/high | --status-high | #f49b45 | High |
| Status/medium | --status-medium | #f0c75e | Medium |
| Status/low | --status-low | #5d94d6 | Low |
| Status/ok | --status-ok | #69b578 | Normal |

## 3. Typography

Primary: `Segoe UI`, `Malgun Gothic`, system sans-serif. Mono: `Cascadia Mono`, `Consolas`, monospace.

| Level | Size | Weight | Line Height | Usage |
|---|---:|---:|---:|---|
| Page title | 22px | 700 | 1.25 | Header |
| Section | 16px | 700 | 1.35 | Panel headings |
| Body | 14px | 400 | 1.55 | Default |
| Caption | 12px | 600 | 1.35 | Labels |

## 4. Spacing & Layout

Base unit is 4px. Page padding is 16px mobile, 20px desktop. Dense panels use 12px internal gaps, large dashboard columns use 16px gaps. Breakpoints: 720px and 1120px.

## 5. Components

### Shell
- Structure: top status bar, tab row, two-column work area, detail drawer.
- States: loading, empty, disconnected.
- Accessibility: `main`, `nav`, clear button labels.

### Priority Card
- Structure: tier stripe, substation id, score, four action buttons, compact evidence.
- Variants: urgent, high, medium, low, monitor.
- States: hover raises border color, focus outline uses accent.

### Metric Panel
- Structure: heading, value, trend or note.
- States: empty and stale data note.

### Table List
- Structure: sticky header, compact rows, status chip.
- States: selected, hover, empty.

### Operator Strip
- Structure: selected-card next judgment, one primary follow-up action, compact metadata.
- States: default, API error, disabled while generating.

### RAG Chat
- Structure: selected-card context, quick prompt chips, chat log, collapsible evidence cards.
- States: empty, generating, answer with sources, error.

### Replay Control
- Structure: live clock, date-time input, scenario selector, seek, play/pause, next tick.
- States: stopped, running, busy while generating cards, scenario source empty/error.
- Interaction: date input snaps to the nearest available scenario time; scenario selection generates that time's cards immediately.

## 6. Motion & Interaction

Motion is limited to affordance: hover border shifts and button press translation. No decorative looping animation except the replay/live signal pulse while the clock is running.

## 7. Depth & Surface

Depth strategy is mixed: tonal shifts define panels and 1px borders define interactive or repeated elements. Shadows are not used for layout separation.
