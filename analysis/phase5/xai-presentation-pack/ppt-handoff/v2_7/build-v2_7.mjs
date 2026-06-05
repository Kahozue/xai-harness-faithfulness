import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const packDir = path.resolve(__dirname, '..');
const chartsDir = path.join(packDir, 'charts');
const tablesDir = path.join(packDir, 'tables');
const screenshotsDir = path.join(packDir, 'screenshots');
const outDir = __dirname;
const outChartsDir = path.join(outDir, 'assets', 'charts');
const outScreensDir = path.join(outDir, 'assets', 'screenshots');

const outputHtml = path.join(outDir, 'xAI-faithfulness-harness-v2_7.html');
const manifestPath = path.join(outDir, 'MANIFEST-v2_7.md');
const TOTAL_SLIDES = 28;

const dataCharts = [
  'task-suite-composition.svg',
  'trace-inventory.svg',
  'controlled-vs-benchmark.svg',
  'factorial-by-split.svg',
  'jaccard-matrix.svg',
  'factorial-contrast-bars.svg',
  'disagreement-success-scatter.svg',
  'method-consistency.svg',
  'phase3-label-summary.svg',
  'agent-card-matrix.svg',
];

const screenshots = [
  'runner-cli-execution.png',
  'claude-trace-system-prompt.png',
];

function parseCsv(text) {
  const rows = [];
  let row = [];
  let cell = '';
  let quoted = false;
  for (let i = 0; i < text.length; i += 1) {
    const ch = text[i];
    const next = text[i + 1];
    if (quoted) {
      if (ch === '"' && next === '"') {
        cell += '"';
        i += 1;
      } else if (ch === '"') {
        quoted = false;
      } else {
        cell += ch;
      }
      continue;
    }
    if (ch === '"') {
      quoted = true;
    } else if (ch === ',') {
      row.push(cell);
      cell = '';
    } else if (ch === '\n') {
      row.push(cell);
      rows.push(row);
      row = [];
      cell = '';
    } else if (ch !== '\r') {
      cell += ch;
    }
  }
  if (cell.length > 0 || row.length > 0) {
    row.push(cell);
    rows.push(row);
  }
  const [header, ...body] = rows.filter((r) => r.some((c) => c.trim() !== ''));
  return body.map((r) => Object.fromEntries(header.map((h, i) => [h, r[i] ?? ''])));
}

async function csv(name) {
  const text = await fs.readFile(path.join(tablesDir, name), 'utf8');
  return parseCsv(text);
}

function by(rows, key) {
  return Object.fromEntries(rows.map((row) => [row[key], row]));
}

function esc(value) {
  return String(value ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;');
}

function img(name, cls = 'chart-img', alt = name) {
  return `<img class="${cls}" src="assets/charts/${esc(name)}" alt="${esc(alt)}" />`;
}

function screenshot(name, alt) {
  return `<img class="screenshot-img" src="assets/screenshots/${esc(name)}" alt="${esc(alt)}" />`;
}

async function sanitizeCopiedChartText() {
  const enDash = String.fromCharCode(0x2013);
  const replacements = {
    'agent-card-matrix.svg': [
      [`0${enDash}1`, '0 to 1'],
    ],
    'trace-inventory.svg': [
      [`1${enDash}3`, '1 to 3'],
    ],
    'method-consistency.svg': [
      [`M1${enDash}M4`, 'M1 to M4'],
    ],
  };
  await Promise.all(Object.entries(replacements).map(async ([name, pairs]) => {
    const file = path.join(outChartsDir, name);
    let text = await fs.readFile(file, 'utf8');
    for (const [from, to] of pairs) text = text.replaceAll(from, to);
    await fs.writeFile(file, text, 'utf8');
  }));
}

function num(value, digits = 3) {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed.toFixed(digits) : value;
}

function pct(value, digits = 1) {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? `${(parsed * 100).toFixed(digits)}%` : value;
}

function slide(n, title, body, opts = {}) {
  const tone = 'light';
  const layout = opts.layout ?? '';
  const active = n === 1 ? ' active' : '';
  const label = `${String(n).padStart(2, '0')} ${title.replace(/<[^>]*>/g, '')}`;
  return `
    <section class="slide ${tone}${active}" data-screen-label="${esc(label)}">
      <div class="page-top">
        <span>工具路徑歸因研究</span>
        <span>${String(n).padStart(2, '0')} / ${TOTAL_SLIDES}</span>
      </div>
      <div class="slide-body ${layout}">
        ${body}
      </div>
    </section>`;
}

function table(headers, rows, classes = '') {
  return `<table class="od-table ${classes}">
    <thead><tr>${headers.map((h) => `<th>${esc(h)}</th>`).join('')}</tr></thead>
    <tbody>${rows.map((row) => `<tr>${row.map((c) => `<td>${c}</td>`).join('')}</tr>`).join('')}</tbody>
  </table>`;
}

function limitationGrid(rows) {
  return `<div class="limit-grid">
    ${rows.map(([name, consequence]) => `<div class="limit-item"><strong>${name}</strong><p>${consequence}</p></div>`).join('')}
  </div>`;
}

function pill(text, cls = '') {
  return `<span class="pill ${cls}">${esc(text)}</span>`;
}

function rawPill(html, cls = '') {
  return `<span class="pill ${cls}">${html}</span>`;
}

function stat(label, value, note = '') {
  return `<div class="metric">
    <div class="metric-value">${esc(value)}</div>
    <div class="metric-label">${esc(label)}</div>
    ${note ? `<div class="metric-note">${esc(note)}</div>` : ''}
  </div>`;
}

function statCard(label, value, note = '') {
  return `<article class="stat-card">
    <strong>${esc(value)}</strong>
    <span>${esc(label)}</span>
    ${note ? `<p>${esc(note)}</p>` : ''}
  </article>`;
}

function mechanismCards() {
  const cards = [
    {
      name: 'Claude Code',
      badge: 'rich tools',
      focus: '工具面完整，plan mode 與 TodoWrite 讓探索有明確程序。',
      rows: [
        ['Prompt', '大型 system prompt，含 20+ tool definitions'],
        ['Tools', 'Read / Edit / Bash / Glob / Grep / TodoWrite'],
        ['Planning', 'query loop + plan mode'],
        ['Memory', 'MEMORY.md + conversation state'],
      ],
    },
    {
      name: 'Codex CLI',
      badge: 'native anchor',
      focus: '外層工具少，核心原生；trace 解釋仰賴 CLI/session 可見面。',
      rows: [
        ['Prompt', 'layered base instructions'],
        ['Tools', 'exec_command / apply_patch'],
        ['Planning', 'inline commentary micro plan'],
        ['Memory', 'goals / state / sqlite memory'],
      ],
    },
    {
      name: 'OpenCode',
      badge: 'small surface',
      focus: 'tool surface 小，常以 shell/read 建立現場感，路徑容易拉長。',
      rows: [
        ['Prompt', 'metadata 可見，full prompt 未完整外露'],
        ['Tools', 'glob / read / edit / apply_patch'],
        ['Planning', 'step_start → step_finish'],
        ['Memory', 'sqlite session / part store'],
      ],
    },
    {
      name: 'Hermes',
      badge: 'memory rich',
      focus: '三層 prompt 與 memory/context affordance 讓起手策略不同。',
      rows: [
        ['Prompt', 'stable / context / volatile 三層'],
        ['Tools', 'search_files / patch / execute_code 等'],
        ['Planning', '三層 prompt + tool loop'],
        ['Memory', 'SOUL.md + USER.md / MEMORY.md + compression'],
      ],
    },
  ];
  return `<div class="mechanism-cards">
    ${cards.map((card) => `<article class="mechanism-card">
      <header><h3>${esc(card.name)}</h3>${pill(card.badge, 'accent')}</header>
      <p class="mechanism-focus">${esc(card.focus)}</p>
      <div class="mechanism-rows">
        ${card.rows.map(([label, value]) => `<div><span>${esc(label)}</span><strong>${esc(value)}</strong></div>`).join('')}
      </div>
    </article>`).join('')}
  </div>`;
}

function tradeoffCards(rows) {
  const badges = ['降低變因', '避免混讀', '交互證據', '選定 benchmark', '延後宣稱'];
  return `<div class="tradeoff-cards">
    ${rows.map(([decision, reason], i) => `<article>
      ${pill(badges[i] ?? '設計邊界', i === 0 ? 'warn' : 'accent')}
      <h3>${decision}</h3>
      <p>${reason}</p>
    </article>`).join('')}
  </div>`;
}

function envCell(cell) {
  // cell = [value, kind]; kind: 'pin' | 'default' | 'effort' | 'none'
  const [value, kind] = cell;
  if (kind === 'none') return rawPill('n/a', 'empty-pill');
  if (kind === 'zero') return rawPill(esc(value), 'empty-pill');
  if (kind === 'effort') return rawPill(esc(value), 'soft-pill');
  if (kind === 'pin') return rawPill(esc(value), 'metric-pill pinned-pill');
  return rawPill(esc(value), 'metric-pill default-pill');
}

function envMatrix(rows) {
  const headers = ['Harness', 'Provider', 'Version', 'Effort', 'Output', 'Thinking', 'Context', 'n'];
  return `<table class="od-table env matrix-table">
    <thead><tr>${headers.map((h) => `<th><span>${esc(h)}</span></th>`).join('')}</tr></thead>
    <tbody>${rows.map((row) => `<tr>
      <td>${pill(row[0], 'harness')}</td>
      <td>${pill(row[1], row[1] === 'anthropic' ? 'route-a' : 'route-b')}</td>
      <td><strong>${row[2]}</strong></td>
      <td>${pill(row[3], 'soft-pill')}</td>
      <td>${envCell(row[4])}</td>
      <td>${envCell(row[5])}</td>
      <td>${envCell(row[6])}</td>
      <td>${pill(row[7], 'metric-pill')}</td>
    </tr>`).join('')}</tbody>
  </table>`;
}

function taskReasonList() {
  const rows = [
    ['hidden test', '避免模型只學 patch 形狀，改用行為驗證。'],
    ['copy into repo', 'grader 只在評分窗口出現，降低污染。'],
    ['run pytest / unittest', '使用 deterministic test，不交給 LLM judge。'],
    ['all green = pass', '全綠才算 pass，避免部分成功灌水。'],
    ['remove grader', '評完即移除，保留 target repo 邊界。'],
  ];
  return `<div class="flow-list task-reasons">
    ${rows.map(([title, reason], i) => `<div><span>${String(i + 1).padStart(2, '0')}</span><strong>${esc(title)}</strong><p>${esc(reason)}</p></div>`).join('')}
  </div>`;
}

function taskTaxonomy() {
  const rows = [
    ['bug_fix', '修正既有函式錯誤'],
    ['add_tests', '補測試以鎖定邊界行為'],
    ['add_logging', '加入可觀測 log'],
    ['rename', '跨檔案命名一致性'],
    ['benchmark', 'Aider / Exercism 題目'],
  ];
  return `<div class="task-taxonomy">
    ${rows.map(([kind, desc]) => `<article><strong>${esc(kind)}</strong><span>4 題</span><p>${esc(desc)}</p></article>`).join('')}
  </div>`;
}

function conclusionBar(text) {
  return `<div class="conclusion-bar">${esc(text)}</div>`;
}

function contrastLabel(value) {
  return ({
    harness_same_model: '同 model 換 harness',
    mixed_harness_model: 'harness 與 route 同時改',
    model_swap_same_harness: '同 harness 換 model route',
  })[value] ?? value;
}

function factorialCards(rows) {
  return `<div class="factorial-cards">
    ${rows.map((r) => `<article>
      <h3>${esc(contrastLabel(r.contrast_family))}</h3>
      <div class="factorial-metrics">
        ${rawPill(`<strong>${num(r.mean_sequence_disagreement, 3)}</strong><span>sequence</span>`, 'metric-pill')}
        ${rawPill(`<strong>${num(r.mean_tool_set_disagreement, 3)}</strong><span>tool set</span>`, 'metric-pill')}
        ${rawPill(`<strong>${num(r.mean_success_gap, 3)}</strong><span>success gap</span>`, 'metric-pill')}
      </div>
      <p>n=${esc(r.n)}</p>
    </article>`).join('')}
  </div>`;
}

function proxyMetric(label, value) {
  return `<span class="proxy-metric"><em>${esc(label)}</em><strong>${esc(value)}</strong></span>`;
}

function agentProxyList(rows) {
  return `<div class="agent-proxy-list">
    ${rows.map((r) => `<article>
      <h3>${esc(r[0])}</h3>
      <div class="proxy-metrics">
        ${proxyMetric('Fid.', r[1])}
        ${proxyMetric('Stab.', r[2])}
        ${proxyMetric('Rob.', r[3])}
      </div>
      <p>${esc(r[4])}</p>
    </article>`).join('')}
  </div>`;
}

function limitGroups() {
  const groups = [
    ['外推範圍', '本研究只用 20 題 Python suite，結論不外推到所有 coding agent 工作。', ['Python suite', 'controlled/benchmark 分流', '專用/通用 harness']],
    ['實驗設計', '交互證據有邊界，route 與 effort 也要精準命名。', ['anchor 未完全交叉', 'model+provider route', 'effort 非完全等價']],
    ['證據來源', '可見面（prompt、工具面、tool path）支持歸因；Anthropic thinking 已擷取，OpenAI reasoning 加密。', ['Anthropic thinking 可讀', 'OpenAI reasoning 加密', 'Phase 3 高分歧選樣']],
    ['解讀語氣', '結果定位為描述性統計與案例歸因，治理卡只負責標示可用邊界。', ['agent card coverage gate', '描述性統計', 'HCI 尚未執行']],
  ];
  return `<div class="limit-groups">
    ${groups.map(([title, lead, tags], i) => `<article class="limit-group g${i + 1}">
      <span class="limit-nb">${String(i + 1).padStart(2, '0')}</span>
      <h3>${esc(title)}</h3>
      <p>${esc(lead)}</p>
      <div>${tags.map((tag) => pill(tag, i === 1 ? 'warn' : 'accent')).join('')}</div>
    </article>`).join('')}
  </div>`;
}

const zh = {
  tradeDecision: {
    'Exclude Antigravity CLI': '排除 Antigravity CLI',
    'Separate controlled and benchmark tasks': 'controlled 與 benchmark 分流',
    'Use OpenCode/Hermes as crossed interaction cells': 'OpenCode/Hermes 作為 crossed cells',
    'Use M1-M4 instead of success-only scoring': '用 M1到M4 補足 success only scoring',
    'Keep HCI human study out of XAI deck': 'HCI human study 留到下一階段',
  },
  tradeReason: {
    'Its release timing and harness maturity would add unstable variables to this baseline.': '版本時點與 harness 成熟度會把不穩定變因帶進 baseline。',
    'Benchmark rows have much lower success and different provenance.': 'benchmark rows 成功率低很多，provenance 也不同，合併讀會誤導。',
    'Claude Code and Codex are anchor cells, not fully crossed across both models.': 'Claude Code 與 Codex 是 anchor cells，兩個 model 沒有完整交叉。',
    'Success cannot identify prompt/tool/model interaction causes.': 'success 無法指出 prompt、tool、model route 的交互來源。',
    'Phase 4 metrics are evidence materials, not human response data.': 'Phase 4 metrics 是證據材料，human response 要另做實驗。',
  },
  actionFinding: {
    'Tool path diverges even when success is unchanged': '成功相同時，tool path 仍會分岔',
    'First-tool strategies differ by harness': 'first tool strategy 隨 harness 改變',
    'Benchmark failures cluster by category': 'benchmark failure 會按 task category 聚集',
    'M1-M4 agreement is partial': 'M1到M4 agreement 只有部分一致',
  },
  actionAction: {
    'Show evidence path, not only pass/fail status.': '揭露 evidence path，避免只報 pass/fail。',
    'Expose or standardize initial discovery affordances when governance matters.': '治理情境要揭露或標準化初始探索 affordance。',
    'Separate high-risk task classes and require replay inspection.': '高風險 task class 分流，並要求 replay inspection。',
    'Use confidence labels and caveats on agent cards.': 'agent card 加上 confidence label 與 caveat。',
  },
  futureStep: {
    'Run HCI human study after XAI deck': '完成 XAI deck 後執行 HCI human study',
    'Expand beyond Python toy repo': '擴到非 Python 與更大型 repo',
    'Test newer harness mechanisms separately': '新版 harness mechanism 獨立重跑',
    'Ablate /goal, memory, and plan-mode mechanisms': '拆解 /goal、memory、plan mode 開關',
    'Make agent-card governance dimensions more discriminative': '讓 agent card 治理維度更可區分',
    'Build optional HTML dashboard': '建立可選 HTML dashboard',
  },
  futureWhy: {
    'Measure clarity, trust calibration, verification choice, safety/control, and cognitive load.': '量測 clarity、trust calibration、verification choice、safety/control 與 cognitive load。',
    'Test language/framework/repository-size robustness.': '檢查語言、framework、repo size 的 robust 程度。',
    'Avoid mixing Phase 2 baseline with later harness behavior changes.': '避免 Phase 2 baseline 與後續 harness 行為改變混在一起。',
    'Separate default harness behavior from optional harness features.': '區分 default harness behavior 與 optional feature 的影響。',
    'Replace coverage-gate dimensions with visibility, patchability, and intervention-support metrics.': '把 coverage gate 換成 visibility、patchability、intervention support 等指標。',
    'Make trace/path/case inspection easier for appendix or defense.': '讓 trace、path、case inspection 更適合附錄與口試追問。',
  },
  limitationName: {
    '20-task Python suite only': '20 題 Python suite',
    'Benchmark and controlled tasks differ': 'benchmark 與 controlled 來源不同',
    'Specialized and general-purpose harnesses are mixed': '專用與通用 harness 混合比較',
    'Anchor cells are not fully crossed': 'anchor cells 未完全交叉',
    'Model effect includes provider route': 'model effect 含 provider route',
    'Reasoning effort is aligned only within each harness\' controls': 'reasoning effort 僅在各 harness 可控範圍對齊',
    'Phase 3 labels are selected high-divergence cases': 'Phase 3 labels 來自高分歧選樣',
    'M1/M2 are not uniform runtime ablations': 'M1/M2 多為可見面證據',
    'Hidden chain-of-thought omitted': 'hidden chain of thought 不進證據',
    'Agent-card actionability/governability are coverage gates': 'agent card actionability/governability 是 coverage gate',
    'Correlation and factorial summaries are descriptive': 'correlation 與 factorial summaries 採描述性解讀',
    'No HCI human responses yet': 'HCI human responses 尚未執行',
  },
  limitationConsequence: {
    'Do not generalize to all coding-agent work.': '外推到所有 coding agent 工作會過度。',
    'Interpret low benchmark success separately.': 'benchmark 的低成功率要分開解讀。',
    'Hermes is not coding-specialized in the same way Claude Code/Codex are, so comparisons need caveats.': 'Hermes 的 coding specialization 與 Claude Code/Codex 不同，比較時要帶 caveat。',
    'Interaction claims use OpenCode/Hermes overlap only.': 'interaction claim 主要依賴 OpenCode/Hermes overlap。',
    'Haiku uses Anthropic and GPT-mini uses OpenAI, so model contrasts are model+provider-route contrasts.': 'Haiku 走 Anthropic，GPT-mini 走 OpenAI；model contrast 寫作 model+provider route contrast。',
    'High effort is not a perfectly equivalent knob across Claude Code, OpenCode, Hermes, and Codex.': 'high effort 無法視為四個 harness 完全等價的控制鈕。',
    'They support explanation, not prevalence estimates.': '它們支撐 explanation，不能估全體 prevalence。',
    'They use source, dossier, captured prompt, and tool-surface evidence according to each harness\' visibility.': '依各 harness 可見度使用 source、dossier、captured prompt 與 tool surface evidence。',
    'Trace evidence uses visible tool path, prompts, metadata, and replay refs.': 'trace evidence 只使用 visible tool path、prompt、metadata 與 replay refs。',
    'Current all-1.0 values should not be treated as discriminative capability rankings.': '目前全 1.0 代表 coverage gate 通過，不能讀成 capability ranking。',
    'They do not prove broad causal independence or general agent quality.': '它們不能推出廣義因果獨立或 general agent quality。',
    'Trust/clarity/calibration claims wait for HCI phase.': 'trust、clarity、calibration claim 留到 HCI phase。',
  },
};

function tr(scope, value) {
  return zh[scope]?.[value] ?? value;
}

function pathLine(value) {
  return esc(value).replaceAll(' -&gt; ', '<span class="path-arrow">→</span>');
}

function shortModel(m) {
  if (/haiku/i.test(m)) return 'Haiku 4.5';
  if (/gpt-5\.4-mini/i.test(m)) return 'GPT-5.4-mini';
  return m;
}

function contrastZh(label) {
  return ({
    harness_main_effect: 'harness 主效應',
    model_main_effect: 'model 主效應',
    interaction: '交互',
  })[label] ?? label;
}

// 一句話「發現」：每組案例挑出後，左右兩邊各做了什麼、得到什麼（取自 hci-case-pack 實測 trace）。
const caseFindings = {
  'XAI-C01': '同題、同模型且都通過；OpenCode 需要 9 步，Hermes 只需 3 步，顯示 harness 會改變工具路徑。',
  'XAI-C02': '同為 OpenCode，換 model route 後成功率與路徑一起改變。',
  'XAI-C03': '同 Haiku 4.5 且都失敗；兩邊路徑不同，但都誤判輸出慣例。',
  'XAI-C04': '固定 Hermes，換 model route 後出現 success gap。',
  'XAI-C05': '同 OpenCode 的 benchmark 題，success gap 主要來自 model 與任務交互。',
  'XAI-C06': '同 GPT-5.4-mini 且都通過；Hermes 與 Codex 選擇不同起手工具。',
};

function caseGallery(rows) {
  return `<div class="case-gallery">
    ${rows.map((r) => `<article class="gallery-card">
      <header>
        <span class="gc-id">${esc(r.xai_case_id)}</span>
        <span class="gc-task">${esc(r.task_id)} · ${esc(r.task_category)}</span>
        ${pill(contrastZh(r.factorial_label), 'accent')}
      </header>
      <div class="gc-side">
        <span class="gc-cfg">c${esc(r.left_config)} ${esc(r.left_harness)} / ${esc(shortModel(r.left_model))}</span>
        <span class="gc-succ">${esc(r.left_success)}</span>
        <span class="gc-path">${pathLine(r.left_dominant_path)}</span>
      </div>
      <div class="gc-side">
        <span class="gc-cfg">c${esc(r.right_config)} ${esc(r.right_harness)} / ${esc(shortModel(r.right_model))}</span>
        <span class="gc-succ">${esc(r.right_success)}</span>
        <span class="gc-path">${pathLine(r.right_dominant_path)}</span>
      </div>
      <p class="gc-find">${esc(caseFindings[r.xai_case_id] ?? '')}</p>
      <div class="gc-meta">M1到M4 ${esc(r.method_agreement)} · ${esc(r.confidence)} confidence</div>
    </article>`).join('')}
  </div>`;
}

function pageTitle(kicker, title, lead = '') {
  return `
    <div>
      <p class="kicker">${esc(kicker)}</p>
      <h1 class="title">${title}</h1>
      ${lead ? `<p class="lead">${lead}</p>` : ''}
    </div>`;
}

async function main() {
  await fs.mkdir(outChartsDir, { recursive: true });
  await fs.mkdir(outScreensDir, { recursive: true });

  await Promise.all(dataCharts.map((name) => fs.copyFile(path.join(chartsDir, name), path.join(outChartsDir, name))));
  await sanitizeCopiedChartText();
  await Promise.all(screenshots.map((name) => fs.copyFile(path.join(screenshotsDir, name), path.join(outScreensDir, name))));

  const headline = by(await csv('headline-stats.csv'), 'metric');
  const overview = await csv('harness-overview.csv');
  const mechanism = await csv('harness-mechanism-comparison.csv');
  const env = await csv('environment-controls.csv');
  const tradeoffs = await csv('design-tradeoffs.csv');
  const factorial = await csv('factorial-summary.csv');
  const success = (await csv('success-association.csv'))[0];
  const caseList = await csv('case-candidates.csv');
  const cases = by(caseList, 'xai_case_id');
  const actions = await csv('action-implications.csv');
  const agentCards = await csv('agent-card-matrix.csv');
  const limitations = await csv('limitations.csv');
  const future = await csv('future-work.csv');

  const xaiC03 = cases['XAI-C03'];
  const formalTraces = `${headline.formal_trace_count.value} 條 formal trace`;
  const overallSuccess = headline.overall_success.presentation_text;
  const assocR = num(success.pearson_sequence_disagreement_vs_success_gap, 3);

  const overviewRows = overview.map((r) => [
    esc(r.harness),
    esc(r.version),
    esc(r.openness),
    esc(r.white_box_visibility).replace('restored source tree', '<mark class="leak">restored source tree</mark>'),
    esc(r.native_provider),
  ]);

  const mechanismRows = mechanism.map((r) => [
    esc(r.harness),
    esc(r.system_prompt_scale),
    esc(r.tool_count_and_kind),
    esc(r.planning_style),
    esc(r.memory_mechanism),
  ]);

  // Output/Thinking/Context 操作值與來源（VPS 原始碼/設定徹查 2026-06-05）：
  //  ✦ pin     = 實驗顯式釘死（Claude Code: CLAUDE_CODE_MAX_OUTPUT_TOKENS / MAX_THINKING_TOKENS，trace 已佐證）
  //  ○ default = harness/模型預設窗口（OpenCode 自家 model catalog：Haiku 200000/64000、GPT-5.4-mini 400000/128000；Codex model_family 258400）
  //  effort    = 以 effort/variant=high 控制推理（仍有 reasoning token 輸出，非無推理）
  //  none      = 該 harness 未暴露此數值旋鈕
  const envRows = [
    ['claude_code', 'anthropic', '2.1.88', 'high', ['64000', 'pin'], ['63999', 'pin'], ['200000', 'pin'], '60'],
    ['opencode', 'anthropic', '1.15.13', 'high', ['64000', 'default'], ['16000', 'default'], ['200000', 'default'], '60'],
    ['hermes', 'anthropic', '0.13.0', 'high', ['64000', 'default'], ['16000', 'pin'], ['200000', 'default'], '60'],
    ['opencode', 'openai', '1.15.13', 'high', ['128000', 'default'], ['high', 'effort'], ['400000', 'default'], '60'],
    ['hermes', 'openai', '0.13.0', 'high', ['128000', 'default'], ['high', 'effort'], ['400000', 'default'], '60'],
    ['codex', 'openai', '0.136.0', 'high', ['n/a', 'none'], ['high', 'effort'], ['258400', 'default'], '60'],
  ];

  // 09/27: 移除「HCI human study 留到下一階段」卡（xAI 期末不談 HCI）；新增 benchmark 選用說明卡。
  const tradeRows = [
    ['controlled 與 benchmark 分流', 'benchmark rows 成功率低很多、provenance 也不同，合併讀會誤導。'],
    ['OpenCode/Hermes 作為 crossed cells', 'Claude Code 與 Codex 只採原生、不走轉發，兩個 model 沒有完整交叉，交互訊號靠這兩格。'],
    ['用 M1到M4 補足 success only scoring', 'success 無法指出 prompt、tool、model route 的交互來源。'],
    ['採 Aider / Exercism Python benchmark', '改用 provenance backed、可在 aarch64 host 重跑的題庫，取代 SWE bench Verified，更貼近工具路徑分歧分析。'],
    ['排除 Antigravity CLI', '版本時點與 harness 成熟度會把不穩定變因帶進 baseline。'],
  ];

  const factorialRows = factorial.map((r) => [
    esc(r.contrast_family),
    num(r.mean_sequence_disagreement, 3),
    num(r.mean_tool_set_disagreement, 3),
    num(r.mean_success_gap, 3),
    esc(r.n),
  ]);

  const actionRows = actions.map((r) => [esc(tr('actionFinding', r.finding)), esc(tr('actionAction', r.action))]);
  // 26/27: 刪除「新版 harness mechanism 獨立重跑」與「建立可選 HTML dashboard」兩列。
  const futureRows = future
    .filter((r) => !['Test newer harness mechanisms separately', 'Build optional HTML dashboard'].includes(r.next_step))
    .map((r) => [esc(tr('futureStep', r.next_step)), esc(tr('futureWhy', r.why))]);
  futureRows.push([
    '計算平均 token 用量',
    '比較各 harness 與 route 的平均 token 成本，補足效率與可觀測性分析。',
  ]);
  const limitationRows = limitations.map((r) => [esc(tr('limitationName', r.limitation)), esc(tr('limitationConsequence', r.consequence))]);

  const agentCardRows = agentCards.map((r) => [
    esc(r.config_label),
    pct(r.fidelity, 1),
    pct(r.stability, 1),
    pct(r.robustness, 1),
    '0 到 1 描述性 proxy',
  ]);

  const slides = [
    slide(1, 'Cover', `
      <div class="cover-grid">
        <div>
          <p class="kicker">封面</p>
          <h1 class="cover-title">Faithfulness of the Harness</h1>
          <p class="cover-subtitle">歸因 agent 的工具路徑分歧</p>
          <p class="author-line">7114029018 陳政顯</p>
        </div>
        <div class="cover-claim">
          <div class="rule"></div>
          <p>同任務、同可控環境，只換 harness 或 model route，工具路徑就會分岔。本研究將可觀測 trace、prompt/tool 表面與 counterfactual rerun 對齊，逐項評估這些歸因的證據支持度。</p>
          <p class="small-note">pipeline-level XAI 研究</p>
        </div>
      </div>
    `, { layout: 'cover' }),

    slide(2, 'Motivation', `
      ${pageTitle('背景與動機', '成功率相同，工具路徑仍可能完全不同', 'LLM coding agent 的行為由外層 harness 共同塑形，包括 system prompt、tool schema、workflow、memory、session state 與執行限制。只看 pass/fail，會漏掉行為路徑的差異來源。')}
      <p class="case-context">同一任務要求 agent 為 <code>mean([])</code> 補上 ValueError 測試。OpenCode 與 Hermes 使用相同 Haiku 4.5 且都通過，但工具路徑從 9 步縮到 3 步，說明 pass/fail 無法呈現 harness 對行為的影響。</p>
      <div class="duo-cards">
        <article class="case-card">
          <div class="case-head"><span class="big-tag">c2 OpenCode / Haiku 4.5</span><strong>3/3 pass</strong></div>
          <p class="path-line">read → shell → read → read → plan → edit → shell → shell → plan</p>
          <p>先 shell 探查、反覆讀檔驗證；工具面小，路徑拉長到 9 步。</p>
        </article>
        <article class="case-card">
          <div class="case-head"><span class="big-tag">c3 Hermes / Haiku 4.5</span><strong>3/3 pass</strong></div>
          <p class="path-line">read → search → edit</p>
          <p>search 與 memory affordance 讓探索壓縮成 3 步。</p>
        </article>
      </div>
    `),

    slide(3, 'Faithfulness And RQ', `
      ${pageTitle('Faithfulness 定義與 RQ', 'Faithfulness 是可檢驗的歸因支持度', 'Faithfulness 指 observable evidence 是否足以支持「工具路徑分歧從何而來」的解釋；證據來自 trace、prompt/tool 表面與 counterfactual rerun。')}
      <div class="rq-grid">
        <div><strong>RQ1</strong><p>四種歸因方法（M1到M4，見研究方法頁）對同一 decision point 的歸因是否一致？</p></div>
        <div><strong>RQ2</strong><p>高 sequence disagreement 是否能作為失敗或治理觸發訊號？</p></div>
        <div><strong>RQ3</strong><p>分歧主要來自 harness、model+provider route，或兩者交互？</p></div>
        <div><strong>RQ4</strong><p>歸因結果能否濃縮成帶邊界的 agent card？</p></div>
      </div>
      <p class="rq-legend">M1 prompt 證據 · M2 工具面 affordance · M3 反事實重跑 · M4 可見 trace（完整定義見研究方法頁）</p>
      <div class="visibility-grid">
        <div><strong>Anthropic / Haiku</strong><p>thinking 可讀；Claude Code 由 claude-trace 擷取，OpenCode 與 Hermes 由 logging proxy 擷取。</p></div>
        <div><strong>OpenAI / GPT-5.4-mini</strong><p>raw reasoning 加密；本研究只使用 summary 與 token 訊號。</p></div>
      </div>
    `),

    slide(4, 'Harness Scope', `
      ${pageTitle('研究對象', 'Harness 是模型外層的決策界面', '四個研究對象橫跨閉源原生、可觀測黑箱、多 provider 與開源通用 agent；這些差異是各 harness 的產品設計選擇，也是本研究要歸因的來源。')}
      ${table(['Harness', '版本', '開放程度', '白箱可見度', 'Provider'], overviewRows, 'compact')}
    `),

    slide(5, 'Mechanism Comparison', `
      ${pageTitle('機制對照', '四個 harness 各不同', '每個 harness 給 agent 的預設環境如工具面、規劃迴圈與記憶都會改變行為路徑。')}
      ${mechanismCards()}
    `),

    slide(6, 'M1 M4 Evidence', `
      ${pageTitle('研究方法', 'M1到M4：四種互補的歸因證據', 'M1到M4 分別從靜態可見面、工具 affordance、反事實重跑與可見 trace 取證，讓每個歸因都能標出證據強弱與邊界。')}
      <div class="method-grid">
        <div><span>M1</span><h3>System prompt evidence</h3><p>原始碼、官方文檔與擷取到的 request 中的 prompt 結構。</p></div>
        <div><span>M2</span><h3>Tool-surface evidence</h3><p>工具集合、描述、可用 affordance 的差異。</p></div>
        <div><span>M3</span><h3>Behavioral counterfactual</h3><p>改寫 task input 後重跑，觀察路徑與結果位移。</p></div>
        <div><span>M4</span><h3>Planning-loop trace</h3><p>visible trace、tool-call sequence、reasoning markers。</p></div>
      </div>
      <p class="boundary">邊界：M1/M2 取自原始碼、官方文檔與工具面證據；閉源與原生工具的可 patch 程度不同。</p>
    `),

    slide(7, 'Study Design', `
      ${pageTitle('研究設計', '鎖定任務、版本、route 進行 trace', 'formal baseline 由 6 configs × 20 tasks × 3 repeats 組成；pilot 與 counterfactual 重跑只作為案例與方法證據，不計入 baseline。')}
      <div class="pipeline-row five">
        ${['6 組配置', '20 題任務', '360 條 trace', 'M1到M4 歸因', 'Agent card 收束'].map((t, i) => `<div class="pipe-step"><span>${String(i + 1).padStart(2, '0')}</span><strong>${t}</strong></div>`).join('')}
      </div>
      ${taskTaxonomy()}
      <div class="stat-band">
        ${statCard('正式 baseline', formalTraces, '6 組配置 × 20 題 × 3 repeats')}
        ${statCard('整體成功率', overallSuccess, '只計 formal baseline')}
        ${statCard('案例重跑', '20 個高分歧決策點', 'M3 反事實重跑，收束為 6 組 XAI 案例')}
      </div>
    `),

    slide(8, 'Config Grid', `
      ${pageTitle('實驗配置', '6 組配置：2 anchor 定錨、4 crossed 看交互', 'OpenCode/Hermes 同時搭 Haiku 4.5 與 GPT-5.4-mini，可觀察交互；Claude Code 與 Codex 只採原生 provider、不走轉發（reverse-proxy）。')}
      <div class="config-grid">
        <div class="blank"></div><div>Claude Code</div><div>OpenCode</div><div>Hermes</div><div>Codex</div>
        <div>Haiku 4.5<br><small>Anthropic</small></div><div class="anchor">c1 anchor</div><div class="crossed">c2 crossed</div><div class="crossed">c3 crossed</div><div class="empty">未跑</div>
        <div>GPT-5.4-mini<br><small>OpenAI</small></div><div class="empty">未跑</div><div class="crossed">c4 crossed</div><div class="crossed">c5 crossed</div><div class="anchor">c6 anchor</div>
      </div>
      <p class="boundary">邊界：anchor cells 未完全交叉；交互解讀主要依賴 OpenCode/Hermes overlap。</p>
    `),

    slide(9, 'Design Tradeoffs', `
      ${pageTitle('實驗設計', '變因決策及理由', '下列決策用來維持 task、route 與 evidence boundary 的可解釋性。')}
      ${tradeoffCards(tradeRows)}
    `),

    slide(10, 'Pipeline Detail', `
      ${pageTitle('實驗管線', '一次 run 的完整管線：乾淨 repo → trace → 評分', '流程的目的，是讓工具路徑與結果都能追溯；成功率之外，還保留足以定位差異來源的證據面。')}
      <div class="pipeline-row many">
        ${[
          ['Provision target repo', '複製受保護 repo'],
          ['Fresh HOME', '每 run 全新 HOME'],
          ['Launch harness', '釘死版本啟動'],
          ['Inject route/effort', '注入 route + high'],
          ['Capture trace', 'trace / JSONL 擷取'],
          ['Mutation guard', '改到即還原判 invalid'],
          ['Hidden pytest', '評分窗才放測試'],
          ['Normalize trace', '正規化統一 schema'],
          ['Persist audit', 'public + private 留存'],
        ].map(([t, d], i) => `<div class="pipe-step"><span>${String(i + 1).padStart(2, '0')}</span><strong>${esc(t)}</strong><p>${esc(d)}</p></div>`).join('')}
      </div>
    `),

    slide(11, 'Environment Lock', `
      ${pageTitle('環境控制', '版本、route、effort 及可觀測欄位控制', '本頁只列本次分析實際使用的控制欄位與可觀測欄位。')}
      ${envMatrix(envRows)}
      <p class="boundary">邊界：Anthropic thinking 可讀；OpenAI raw reasoning 加密。本頁只呈現可用於重現與比較的欄位。</p>
    `),

    slide(12, 'Isolation', `
      ${pageTitle('執行隔離與污染防護', '每次 run 使用全新 HOME，隔離 session、memory 與 log', '每次 run 建立 fresh HOME，不共用 session、history、memory、log；Hermes 另有 HERMES_HOME，hidden tests 僅在 grading window 出現。')}
      <div class="isolation">
        <div class="zone outer">
          <h3>Execution root</h3>
          <div class="zone-grid">
            <div class="zone"><strong>Fresh HOME</strong><span>session / history / logs isolated</span></div>
            <div class="zone"><strong>Target repo copy</strong><span>mutation guard + restore</span></div>
            <div class="zone"><strong>HERMES_HOME</strong><span>separate from production Hermes</span></div>
            <div class="zone danger"><strong>Hidden grader</strong><span>copy in, run, remove</span></div>
          </div>
        </div>
        <div class="barrier">no-touch barrier</div>
      </div>
    `),

    slide(13, 'Task Suite', `
      ${pageTitle('任務套件與評分規則', '20 題分成 5 類，每類 4 題', 'Tier 1 來自 benchmark provenance，Tier 2 是自撰受控 repo。評分採 hidden pytest / unittest，全綠才 pass。')}
      <div class="split charts-plus">
        <div class="chart-panel">${img('task-suite-composition.svg', 'chart-img contain', 'Task suite composition chart')}</div>
        ${taskReasonList()}
      </div>
    `),

    slide(14, 'Trace Schema', `
      ${pageTitle('Trace schema 與證據強度', '四家 log 正規化成同一組可比欄位，並標證據強度', 'normalized trace 對齊 identity、tool path、outcome、replay refs 與 evidence boundary；每個欄位標示 direct、source-derived、inferred 或 unknown。')}
      <div class="schema-grid">
        ${[
          ['Identity', 'config、task、repeat、route'],
          ['Tool path', 'canonical tool family + sequence'],
          ['Outcome', 'hidden grader pass/fail'],
          ['Replay refs', 'raw/private/public trace pointer'],
          ['Boundary', 'direct / source-derived / inferred / unknown'],
        ].map(([h, p]) => `<div><strong>${h}</strong><p>${p}</p></div>`).join('')}
      </div>
      <p class="boundary">原始 log 長相不同，schema 的角色是保留可比性，同時標出不可見處。</p>
    `),

    slide(15, 'Execution Screenshots', `
      ${pageTitle('執行實況', 'runner CLI 與 claude-trace 的擷取畫面', 'runner CLI 與 claude-trace 展示執行現場；公開層去敏，原始材料保留在可追溯 audit path。')}
      <div class="screenshot-grid">
        <figure><div class="screenshot-frame">${screenshot('runner-cli-execution.png', 'Runner CLI execution screenshot')}</div><figcaption>Runner CLI 執行畫面</figcaption></figure>
        <figure><div class="screenshot-frame">${screenshot('claude-trace-system-prompt.png', 'Claude trace system prompt screenshot')}</div><figcaption>claude-trace request 擷取</figcaption></figure>
      </div>
    `),

    slide(16, 'Data Scale', `
      ${pageTitle('資料規模與統計母體', '結果分析以 360 條 formal trace 為母體', 'pilot 與 counterfactual trace 不納入 baseline 統計，只作為方法檢查與案例追溯材料。')}
      <div class="split">
        <div class="chart-panel">${img('trace-inventory.svg', 'chart-img contain', 'Trace inventory chart')}</div>
        <div class="stacked-metrics">
          ${stat('正式 trace 數', formalTraces, 'baseline 統計母體')}
          ${stat('整體成功率', overallSuccess, '295 條 pass trace')}
          ${stat('案例重跑', '20 個高分歧決策點', 'M3 反事實重跑，收束 6 組案例')}
        </div>
      </div>
    `),

    slide(17, 'Controlled Benchmark Split', `
      ${pageTitle('Controlled 與 benchmark 分流', '不同來源與難度的任務需分開解讀', 'controlled 與 benchmark 的來源、難度與失敗型態不同，合併平均會降低結論可解釋性。')}
      <div class="two-charts">
        <div class="chart-panel">${img('controlled-vs-benchmark.svg', 'chart-img contain', 'Controlled versus benchmark chart')}</div>
        <div class="chart-panel">${img('factorial-by-split.svg', 'chart-img contain', 'Factorial by split chart')}</div>
      </div>
      ${conclusionBar('結論：controlled 與 benchmark 應分開報告，避免把任務難度差異誤讀為 harness 優劣。')}
    `),

    slide(18, 'RQ3 Jaccard', `
      ${pageTitle('RQ3：路徑分歧', '工具集合重疊低，代表分歧有結構', 'tool name 先 canonicalize 成 tool family，再用 Jaccard 與 sequence disagreement 觀察。Codex anchor 與其他 config 的工具集合重疊偏低，這個差異不像隨機噪音。')}
      <div class="chart-panel wide-chart">${img('jaccard-matrix.svg', 'chart-img contain', 'Jaccard matrix chart')}</div>
    `),

    slide(19, 'RQ3 Factorial', `
      ${pageTitle('RQ3：Factorial 對比', 'mixed 對比的 sequence disagreement 較高', '同 model 換 harness、同 harness 換 model+provider route、兩者同時改變，三種 contrast family 只做描述性對照；交互訊號來自 crossed cells。')}
      <div class="split">
        <div class="chart-panel">${img('factorial-contrast-bars.svg', 'chart-img contain', 'Factorial contrast chart')}</div>
        ${factorialCards(factorial)}
      </div>
    `),

    slide(20, 'RQ2 Association', `
      ${pageTitle('RQ2：分歧與成敗', '路徑分歧高，未必能直接當 failure trigger', `在 300 個 config-pair × task observation 中，sequence disagreement 與 success gap 的 Pearson r ≈ ${assocR}。治理訊號需要結合 evidence path、任務類型與 case diagnosis。`)}
      <div class="split">
        <div class="chart-panel">${img('disagreement-success-scatter.svg', 'chart-img contain', 'Disagreement success scatter chart')}</div>
        <div class="callout-panel">
          <strong>解讀</strong>
          <p>分歧本身值得被揭露；但這份 task suite 裡，單一 disagreement threshold 無法替代證據鏈。</p>
          <p class="metric-inline">r ≈ ${assocR}</p>
        </div>
      </div>
    `),

    slide(21, 'RQ1 Consistency', `
      ${pageTitle('RQ1：M1到M4 一致性', '部分案例一致，交互歸因仍是主要解釋來源', '在 20 個高分歧 decision labels 中，M1到M4 完全一致 10/20；label 分布為 harness_main_effect=6、interaction=8、model_main_effect=6。')}
      <div class="two-charts">
        <div class="chart-panel">${img('method-consistency.svg', 'chart-img contain', 'Method consistency chart')}</div>
        <div class="chart-panel">${img('phase3-label-summary.svg', 'chart-img contain', 'Phase 3 label summary chart')}</div>
      </div>
      <p class="boundary">邊界：這是 high-divergence subset，支撐解釋品質評估，不能外推成全體 prevalence。</p>
    `),

    slide(22, 'Case Gallery', `
      ${pageTitle('案例總覽', '6 組高分歧案例', '每組呈現比較配置、工具路徑、成敗與歸因標籤。')}
      ${caseGallery(caseList)}
    `),

    slide(23, 'XAI C03 Case', `
      ${pageTitle('XAI-C03 深入', 'OpenCode vs Hermes：同 Haiku 4.5、同為 0/3，路徑與輸出 convention 分岔', `${esc(xaiC03.task_id)} · ${esc(xaiC03.decision_kind)} · ${esc(xaiC03.factorial_label)} · ${esc(xaiC03.method_agreement)} agreement · high confidence`)}
      <p class="case-context">任務：修正 calckit/money.py 的 format_amount 讓負數保留負號。兩邊都修改程式，但都因輸出 convention 判讀錯誤而 0/3。</p>
      <div class="case-deep tight">
        <article class="case-card large">
          <div class="case-head"><span class="big-tag">c${esc(xaiC03.left_config)} ${esc(xaiC03.left_harness)} / Haiku 4.5</span><strong>${esc(xaiC03.left_success)}</strong></div>
          <p class="path-line">${pathLine(xaiC03.left_dominant_path)}</p>
          <p>tool surface 小，先 shell 探查、反覆 read/edit 驗證，11 步仍未過。</p>
        </article>
        <article class="case-card large">
          <div class="case-head"><span class="big-tag">c${esc(xaiC03.right_config)} ${esc(xaiC03.right_harness)} / Haiku 4.5</span><strong>${esc(xaiC03.right_success)}</strong></div>
          <p class="path-line">${pathLine(xaiC03.right_dominant_path)}</p>
          <p>三層 prompt/memory 可讀；起始策略更短，2 步就改完，但同樣誤判 convention。</p>
        </article>
      </div>
      <div class="thinking-reveal">
        <span class="tr-label">擷取到的 thinking 揭露失敗原因（pass/fail 與 tool path 都看不到）</span>
        <div class="tr-grid">
          <div><strong>hidden grader 期望</strong><code>format_amount(-12.5) == "$-12.50"</code></div>
          <div><strong>OpenCode 的 thinking（proxy 擷取）</strong><p>選定 <code>-$12.50</code> 慣例，再用「只測正數」的可見測試自我驗證、宣告完成 → 慣例選錯，0/3。原因只在擷取到的 reasoning 裡看得到。</p></div>
        </div>
      </div>
    `),

    slide(24, 'RQ4 Agent Card', `
      ${pageTitle('RQ4：Agent card 五維', 'Agent card：五維 descriptive proxy（附 caveat）', 'fidelity、stability、robustness、actionability、governability 都是此 suite 的 descriptive proxy；其中 actionability/governability 目前是 coverage gate，不能讀成能力排名。')}
      <div class="split">
        <div class="chart-panel">${img('agent-card-matrix.svg', 'chart-img contain', 'Agent card matrix chart')}</div>
        ${agentProxyList(agentCardRows)}
      </div>
    `),

    slide(25, 'Action Map', `
      ${pageTitle('從歸因到行動', '歸因結果要落到可操作的揭露與檢查', '治理重點從「報一個分數」轉向「保留 evidence path、標準化初始探索、分流高風險任務、給 agent card confidence」。')}
      ${table(['歸因發現', '治理動作'], actionRows, 'action')}
    `),

    slide(26, 'Limitations', `
      <div>
        <p class="kicker">研究限制</p>
        <h1 class="title tight-title">研究限制：外推、交叉、effort、因果語氣</h1>
        <p class="lead tight-lead">把外推範圍、交叉設計、effort 對齊與因果語氣四類限制集中列出。</p>
      </div>
      ${limitGroups()}
    `),

    slide(27, 'Future Work', `
      ${pageTitle('未來展望', '擴任務、拆機制、補 token 成本分析', '下一步會擴大任務與 repo，拆解 /goal、memory、plan mode 等機制開關，並計算平均 token 用量以補足效率分析。')}
      ${table(['下一步', '為何重要'], futureRows, 'future')}
    `),

    slide(28, 'Closing', `
      <div class="closing">
        <p class="kicker">收束</p>
        <h2>同任務下，工具路徑會因 harness 與 route 系統性分岔。</h2>
        <div class="closing-grid">
          <div><strong>01</strong><h3>工具路徑</h3><p>harness 會系統性塑造 tool path。</p></div>
          <div><strong>02</strong><h3>治理訊號</h3><p>分歧未必等於失敗，治理要看 evidence path。</p></div>
          <div><strong>03</strong><h3>證據邊界</h3><p>agent card 可以收束結果，但必須帶 confidence 與 caveat。</p></div>
        </div>
      </div>
    `, { layout: 'centered' }),
  ];

  const html = `<!doctype html>
<html lang="zh-Hant">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Faithfulness of the Harness · xAI 期末簡報 v2_7</title>
  <style>
    :root {
      --bg: #f4f5f1;
      --surface: #ffffff;
      --fg: #1e2428;
      --muted: #5b6468;
      --soft: #e9eee9;
      --border: #ccd5cf;
      --accent: #0f6d6f;
      --accent-2: #a85234;
      --dark: #20262a;
      --dark-soft: #2b3337;
      --dark-text: #f4f5f1;
      --shell: #1e2428;
      --deck-scale: 1;
      --font-display: "Noto Serif TC", "Source Han Serif TC", "Songti TC", Georgia, serif;
      --font-body: "PingFang TC", "Noto Sans TC", "Microsoft JhengHei", system-ui, sans-serif;
      --font-mono: "SF Mono", "JetBrains Mono", ui-monospace, Menlo, monospace;
    }
    * { box-sizing: border-box; }
    html, body {
      width: 100%;
      height: 100%;
      margin: 0;
      overflow: hidden;
      background: var(--shell);
      color: var(--fg);
      font-family: var(--font-body);
      -webkit-font-smoothing: antialiased;
      text-rendering: geometricPrecision;
    }
    .deck-stage {
      position: absolute;
      top: 50%;
      left: 50%;
      width: 1920px;
      height: 1080px;
      background: var(--bg);
      transform: translate(-50%, -50%) scale(var(--deck-scale));
      transform-origin: center;
      overflow: hidden;
    }
    .slide {
      position: absolute;
      inset: 0;
      display: none;
      flex-direction: column;
      padding: 58px 82px 68px;
      background: var(--bg);
      color: var(--fg);
      overflow: hidden;
    }
    .slide.active { display: flex; }
    .slide.dark { background: var(--dark); color: var(--dark-text); }
    .page-top {
      height: 34px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-family: var(--font-mono);
      font-size: 14px;
      letter-spacing: 0;
      color: var(--muted);
      border-bottom: 1px solid var(--border);
      padding-bottom: 18px;
      flex: 0 0 auto;
    }
    .dark .page-top {
      color: color-mix(in srgb, var(--dark-text) 62%, transparent);
      border-color: color-mix(in srgb, var(--dark-text) 16%, transparent);
    }
    .slide-body {
      flex: 1;
      min-height: 0;
      display: flex;
      flex-direction: column;
      justify-content: center;
      gap: 34px;
      padding-top: 34px;
    }
    .slide-body.cover { justify-content: center; }
    .slide-body.centered { align-items: center; text-align: center; }
    .kicker {
      margin: 0 0 14px;
      font-family: var(--font-mono);
      font-size: 16px;
      line-height: 1.35;
      color: var(--accent);
      letter-spacing: 0;
    }
    .dark .kicker { color: color-mix(in srgb, var(--accent) 70%, var(--dark-text)); }
    .title {
      margin: 0;
      font-family: var(--font-display);
      font-size: 58px;
      line-height: 1.12;
      letter-spacing: 0;
      font-weight: 650;
      max-width: 1120px;
    }
    .tight-title {
      font-size: 52px;
      max-width: 1320px;
    }
    .lead {
      margin: 16px 0 0;
      font-size: 27px;
      line-height: 1.55;
      max-width: 1120px;
      color: var(--muted);
      letter-spacing: 0;
    }
    .tight-lead {
      font-size: 24px;
      max-width: 1280px;
      margin-top: 12px;
    }
    .dark .lead { color: color-mix(in srgb, var(--dark-text) 76%, transparent); }
    p { margin: 0; }
    strong { font-weight: 650; }
    .small-note, .boundary {
      font-family: var(--font-mono);
      font-size: 17px;
      line-height: 1.5;
      color: var(--muted);
      letter-spacing: 0;
    }
    .boundary {
      border-top: 1px solid var(--border);
      padding-top: 16px;
      max-width: 1420px;
    }
    .dark .boundary, .dark .small-note {
      color: color-mix(in srgb, var(--dark-text) 66%, transparent);
      border-color: color-mix(in srgb, var(--dark-text) 16%, transparent);
    }
    .cover-grid {
      display: grid;
      grid-template-columns: 1.05fr 0.95fr;
      gap: 92px;
      align-items: end;
    }
    .cover-title {
      margin: 0;
      max-width: 10ch;
      font-family: var(--font-display);
      font-size: 112px;
      line-height: 1.02;
      letter-spacing: 0;
      font-weight: 720;
    }
    .cover-subtitle {
      margin-top: 28px;
      font-size: 42px;
      line-height: 1.25;
      color: var(--fg);
      font-weight: 560;
      letter-spacing: 0;
    }
    .cover-claim {
      border-left: 6px solid var(--accent);
      padding-left: 36px;
      font-size: 29px;
      line-height: 1.62;
      color: var(--fg);
    }
    .cover-claim .rule {
      width: 86px;
      height: 2px;
      background: var(--fg);
      margin-bottom: 26px;
    }
    .duo-cards, .case-deep, .two-charts, .screenshot-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 34px;
    }
    .case-card, .metric, .callout-panel, .schema-grid > div, .method-grid > div, .rq-grid > div, .zone, .flow-list > div, .closing-grid > div {
      border: 1px solid var(--border);
      border-radius: 6px;
      background: var(--surface);
    }
    .dark .case-card, .dark .metric, .dark .callout-panel, .dark .schema-grid > div, .dark .method-grid > div, .dark .rq-grid > div, .dark .zone, .dark .flow-list > div, .dark .closing-grid > div {
      border-color: color-mix(in srgb, var(--dark-text) 16%, transparent);
      background: var(--dark-soft);
    }
    .case-card {
      padding: 30px;
      min-height: 230px;
      display: flex;
      flex-direction: column;
      gap: 20px;
      font-size: 24px;
      line-height: 1.48;
    }
    .case-card.large { min-height: 320px; }
    .case-head {
      display: flex;
      justify-content: space-between;
      gap: 22px;
      align-items: center;
      font-family: var(--font-mono);
      font-size: 18px;
      color: var(--muted);
    }
    .case-head strong {
      color: var(--accent-2);
      font-size: 22px;
    }
    .dark .case-head { color: color-mix(in srgb, var(--dark-text) 66%, transparent); }
    .path-line {
      font-family: var(--font-mono);
      font-size: 21px;
      line-height: 1.55;
      color: var(--fg);
      word-break: keep-all;
    }
    .path-arrow { color: var(--accent); padding: 0 8px; }
    .dark .path-line { color: var(--dark-text); }
    .rq-grid, .method-grid, .schema-grid {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 24px;
    }
    .rq-grid > div, .method-grid > div, .schema-grid > div {
      padding: 26px;
      min-height: 190px;
    }
    .rq-grid strong, .method-grid span {
      display: block;
      font-family: var(--font-mono);
      font-size: 22px;
      color: var(--accent);
      margin-bottom: 18px;
    }
    .rq-grid p, .method-grid p, .schema-grid p {
      font-size: 22px;
      line-height: 1.48;
      color: var(--muted);
    }
    .dark .rq-grid p, .dark .method-grid p, .dark .schema-grid p { color: color-mix(in srgb, var(--dark-text) 72%, transparent); }
    .visibility-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 22px;
    }
    .visibility-grid > div {
      border: 1px solid var(--border);
      border-radius: 6px;
      background: var(--surface-strong);
      padding: 20px 22px;
    }
    .visibility-grid strong {
      display: block;
      margin-bottom: 8px;
      color: var(--accent);
      font-family: var(--font-mono);
      font-size: 18px;
    }
    .visibility-grid p {
      font-size: 20px;
      line-height: 1.42;
      color: var(--muted);
    }
    .method-grid h3, .schema-grid strong {
      display: block;
      margin: 0 0 14px;
      font-size: 25px;
      line-height: 1.24;
      color: inherit;
      letter-spacing: 0;
    }
    .od-table {
      width: 100%;
      border-collapse: collapse;
      table-layout: fixed;
      font-size: 21px;
      line-height: 1.36;
      background: transparent;
    }
    .od-table th, .od-table td {
      border-top: 1px solid var(--border);
      padding: 15px 14px;
      vertical-align: top;
      text-align: left;
    }
    .od-table th {
      font-family: var(--font-mono);
      font-size: 15px;
      color: var(--accent);
      font-weight: 650;
    }
    .od-table td { color: var(--fg); }
    .dark .od-table th, .dark .od-table td {
      border-color: color-mix(in srgb, var(--dark-text) 16%, transparent);
    }
    .dark .od-table td { color: var(--dark-text); }
    .od-table.compact td { font-size: 20px; }
    .od-table.dense td { font-size: 18px; line-height: 1.32; }
    .od-table.env td, .od-table.env th { font-size: 18px; }
    .od-table.trade td, .od-table.action td, .od-table.future td, .od-table.limits td { font-size: 23px; line-height: 1.42; }
    .od-table.mini td, .od-table.mini th { font-size: 17px; padding: 12px 10px; }
    .pipeline-row {
      display: grid;
      gap: 16px;
    }
    .pipeline-row.five { grid-template-columns: repeat(5, 1fr); }
    .pipeline-row.many { grid-template-columns: repeat(9, 1fr); }
    .pipe-step {
      border-top: 4px solid var(--accent);
      padding-top: 18px;
      min-height: 130px;
      position: relative;
    }
    .pipe-step span {
      font-family: var(--font-mono);
      color: var(--muted);
      font-size: 16px;
    }
    .pipe-step strong {
      display: block;
      margin-top: 12px;
      font-size: 24px;
      line-height: 1.22;
    }
    .metric-row {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 24px;
    }
    .metric { padding: 26px; min-height: 160px; }
    .metric-value {
      font-family: var(--font-mono);
      font-size: 46px;
      line-height: 1;
      color: var(--accent-2);
      margin-bottom: 18px;
      letter-spacing: 0;
    }
    .metric-label {
      font-size: 23px;
      font-weight: 650;
      margin-bottom: 8px;
    }
    .metric-note { font-size: 18px; color: var(--muted); line-height: 1.35; }
    .config-grid {
      display: grid;
      grid-template-columns: 220px repeat(4, 1fr);
      border: 1px solid var(--border);
      border-radius: 6px;
      overflow: hidden;
      font-size: 25px;
      line-height: 1.28;
    }
    .config-grid > div {
      min-height: 124px;
      padding: 22px;
      border-right: 1px solid var(--border);
      border-bottom: 1px solid var(--border);
      display: flex;
      flex-direction: column;
      justify-content: center;
      background: var(--surface);
      font-weight: 620;
    }
    .config-grid > div:nth-child(5n) { border-right: 0; }
    .config-grid small {
      color: var(--muted);
      font-size: 18px;
      margin-top: 8px;
    }
    .config-grid .crossed { background: color-mix(in srgb, var(--accent) 13%, var(--surface)); border-top: 4px solid var(--accent); }
    .config-grid .anchor { background: color-mix(in srgb, var(--accent-2) 14%, var(--surface)); border-top: 4px solid var(--accent-2); }
    .config-grid .empty { background: var(--soft); color: var(--muted); }
    .split {
      display: grid;
      grid-template-columns: 1.15fr 0.85fr;
      gap: 34px;
      align-items: stretch;
      min-height: 0;
    }
    .charts-plus { grid-template-columns: 1.15fr 0.85fr; }
    .chart-panel {
      border: 1px solid var(--border);
      border-radius: 6px;
      background: var(--surface);
      padding: 18px;
      min-height: 0;
      display: flex;
      align-items: center;
      justify-content: center;
      overflow: hidden;
    }
    .wide-chart { height: 720px; }
    .dark .chart-panel {
      border-color: color-mix(in srgb, var(--dark-text) 16%, transparent);
      background: var(--surface);
    }
    .chart-img {
      display: block;
      width: 100%;
      height: 100%;
      max-height: 660px;
    }
    .chart-img.contain { object-fit: contain; }
    .two-charts { min-height: 620px; }
    .flow-list {
      display: grid;
      gap: 16px;
      align-content: center;
    }
    .flow-list > div {
      padding: 23px;
      display: grid;
      grid-template-columns: 58px 1fr;
      align-items: center;
      font-size: 27px;
    }
    .flow-list span {
      font-family: var(--font-mono);
      color: var(--accent);
    }
    .isolation {
      display: grid;
      grid-template-columns: 1fr 260px;
      gap: 36px;
      align-items: stretch;
    }
    .outer {
      padding: 34px;
      background: var(--dark-soft);
    }
    .outer h3 {
      margin: 0 0 26px;
      font-size: 32px;
      font-family: var(--font-display);
      letter-spacing: 0;
    }
    .zone-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 22px;
    }
    .zone {
      padding: 28px;
      min-height: 164px;
    }
    .zone strong { display: block; font-size: 27px; margin-bottom: 12px; }
    .zone span { color: color-mix(in srgb, var(--dark-text) 72%, transparent); font-size: 21px; line-height: 1.42; }
    .zone.danger { border-color: var(--accent-2); }
    .barrier {
      border: 2px dashed var(--accent-2);
      border-radius: 6px;
      display: grid;
      place-items: center;
      font-family: var(--font-mono);
      color: var(--accent-2);
      font-size: 22px;
      text-align: center;
      padding: 24px;
    }
    .schema-grid { grid-template-columns: repeat(5, 1fr); }
    .screenshot-grid {
      min-height: 660px;
      align-items: stretch;
    }
    figure { margin: 0; display: flex; flex-direction: column; min-height: 0; gap: 12px; }
    figcaption {
      font-family: var(--font-mono);
      font-size: 16px;
      color: color-mix(in srgb, var(--dark-text) 66%, transparent);
    }
    .screenshot-frame {
      flex: 1;
      min-height: 0;
      border: 1px solid color-mix(in srgb, var(--dark-text) 16%, transparent);
      border-radius: 6px;
      background: var(--fg);
      display: grid;
      place-items: center;
      overflow: hidden;
      padding: 10px;
    }
    .screenshot-img {
      width: 100%;
      height: 100%;
      object-fit: contain;
      display: block;
    }
    .stacked-metrics {
      display: grid;
      gap: 18px;
      align-content: center;
    }
    .callout-panel {
      padding: 44px;
      font-size: 29px;
      line-height: 1.5;
      display: flex;
      flex-direction: column;
      justify-content: center;
      gap: 28px;
    }
    .callout-panel strong {
      font-family: var(--font-display);
      font-size: 42px;
      line-height: 1.18;
      letter-spacing: 0;
    }
    .metric-inline {
      font-family: var(--font-mono);
      color: var(--accent-2);
      font-size: 68px;
      line-height: 1;
    }
    .method-mini {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 18px;
    }
    .method-mini span {
      display: block;
      border-top: 3px solid var(--accent);
      padding-top: 15px;
      font-size: 21px;
      line-height: 1.35;
      color: var(--muted);
    }
    .dark .method-mini span {
      color: color-mix(in srgb, var(--dark-text) 70%, transparent);
    }
    .limit-grid {
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 10px 34px;
      border-top: 1px solid var(--border);
      padding-top: 12px;
    }
    .limit-item {
      display: grid;
      grid-template-columns: 0.8fr 1.2fr;
      gap: 22px;
      align-items: start;
      border-bottom: 1px solid var(--border);
      padding: 12px 0 13px;
      min-height: 70px;
    }
    .limit-item strong {
      font-size: 20px;
      line-height: 1.28;
      color: var(--fg);
    }
    .limit-item p {
      font-size: 19px;
      line-height: 1.34;
      color: var(--muted);
    }
    .closing {
      max-width: 1450px;
    }
    .closing h2 {
      margin: 0;
      font-family: var(--font-display);
      font-size: 68px;
      line-height: 1.16;
      font-weight: 680;
      letter-spacing: 0;
    }
    .closing-grid {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 22px;
      margin-top: 58px;
      text-align: left;
    }
    .closing-grid > div { padding: 26px; }
    .closing-grid strong {
      font-family: var(--font-mono);
      color: var(--accent);
      font-size: 28px;
    }
    .closing-grid p {
      margin-top: 14px;
      color: color-mix(in srgb, var(--dark-text) 78%, transparent);
      font-size: 23px;
      line-height: 1.44;
    }
    /* v3 visual system override: uniform report surface + stronger hierarchy. */
    :root {
      --bg: #ffffff;
      --surface: #f6f8fb;
      --surface-strong: #eef3f8;
      --fg: #182027;
      --muted: #3f4d58;
      --soft: #edf2f7;
      --border: #c6d2de;
      --accent: #36618e;
      --accent-2: #c4542e;
      --warn: #e69f00;
      --success: #009e73;
      --shell: #20262a;
    }
    .slide,
    .slide.dark {
      background: var(--bg);
      color: var(--fg);
    }
    .page-top,
    .dark .page-top {
      height: 38px;
      color: var(--muted);
      border-color: var(--border);
      font-size: 16px;
      font-weight: 700;
    }
    .slide-body {
      gap: 30px;
      padding-top: 32px;
    }
    .kicker,
    .dark .kicker {
      display: inline-flex;
      align-items: center;
      width: fit-content;
      padding: 7px 16px;
      border: 1px solid var(--border);
      border-radius: 999px;
      background: var(--surface-strong);
      color: var(--accent);
      font-family: var(--font-body);
      font-size: 20px;
      font-weight: 800;
      line-height: 1.35;
      margin-bottom: 14px;
    }
    .title {
      font-size: 56px;
      font-weight: 780;
      max-width: 1260px;
    }
    .lead,
    .dark .lead {
      color: var(--muted);
      font-weight: 520;
      font-size: 26px;
    }
    .boundary,
    .dark .boundary {
      border: 1px solid var(--border);
      border-left: 8px solid var(--accent);
      border-radius: 6px;
      padding: 16px 20px;
      background: var(--surface-strong);
      color: var(--fg);
      font-size: 22px;
      font-weight: 760;
      line-height: 1.45;
    }
    .cover-grid {
      grid-template-columns: 0.92fr 1.08fr;
      align-items: center;
      gap: 86px;
    }
    .cover-title {
      max-width: 11ch;
      font-size: 122px;
      line-height: 0.98;
    }
    .cover-subtitle {
      font-weight: 800;
      font-size: 44px;
    }
    .author-line {
      display: inline-block;
      margin-top: 32px;
      padding: 12px 20px;
      border-radius: 999px;
      background: var(--fg);
      color: var(--bg);
      font-size: 24px;
      font-weight: 800;
    }
    .cover-claim {
      border: 1px solid var(--border);
      border-left: 10px solid var(--accent);
      border-radius: 8px;
      background: var(--surface);
      padding: 44px;
      box-shadow: none;
    }
    .case-card,
    .metric,
    .callout-panel,
    .schema-grid > div,
    .method-grid > div,
    .rq-grid > div,
    .zone,
    .flow-list > div,
    .closing-grid > div,
    .dark .case-card,
    .dark .metric,
    .dark .callout-panel,
    .dark .schema-grid > div,
    .dark .method-grid > div,
    .dark .rq-grid > div,
    .dark .zone,
    .dark .flow-list > div,
    .dark .closing-grid > div {
      border-color: var(--border);
      background: var(--surface);
      color: var(--fg);
    }
    .rq-grid p,
    .method-grid p,
    .schema-grid p,
    .dark .rq-grid p,
    .dark .method-grid p,
    .dark .schema-grid p {
      color: var(--fg);
      font-weight: 560;
    }
    .case-head,
    .dark .case-head {
      color: var(--muted);
      font-weight: 760;
    }
    .path-line,
    .dark .path-line {
      color: var(--fg);
    }
    .pill {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-height: 32px;
      padding: 5px 12px;
      margin: 0 8px 8px 0;
      border: 1px solid var(--border);
      border-radius: 999px;
      background: var(--surface-strong);
      color: var(--fg);
      font-size: 16px;
      line-height: 1.2;
      font-weight: 800;
      white-space: normal;
    }
    .pill.accent {
      color: var(--accent);
      border-color: color-mix(in srgb, var(--accent) 36%, var(--border));
      background: color-mix(in srgb, var(--accent) 11%, var(--bg));
    }
    .pill.warn {
      color: #8c5a00;
      border-color: color-mix(in srgb, var(--warn) 42%, var(--border));
      background: color-mix(in srgb, var(--warn) 18%, var(--bg));
    }
    .pill.harness {
      min-width: 132px;
      color: var(--bg);
      background: var(--fg);
      border-color: var(--fg);
    }
    .pill.route-a {
      color: var(--accent);
      background: color-mix(in srgb, var(--accent) 12%, var(--bg));
    }
    .pill.route-b {
      color: var(--accent-2);
      background: color-mix(in srgb, var(--accent-2) 12%, var(--bg));
    }
    .pill.metric-pill {
      color: var(--fg);
      background: var(--bg);
    }
    .pill.empty-pill {
      color: #7d8790;
      background: #f1f3f5;
      border-style: dashed;
    }
    .pill.soft-pill {
      color: var(--muted);
      background: #eef2f7;
    }
    .mechanism-cards {
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 24px;
    }
    .mechanism-card {
      min-height: 290px;
      padding: 24px 26px;
      border: 1px solid var(--border);
      border-radius: 8px;
      background: var(--surface);
      display: grid;
      gap: 18px;
    }
    .mechanism-card header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
    }
    .mechanism-card h3 {
      margin: 0;
      font-size: 30px;
      line-height: 1.1;
    }
    .mechanism-focus {
      font-size: 22px;
      line-height: 1.42;
      color: var(--fg);
      font-weight: 700;
    }
    .mechanism-rows {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 10px 16px;
    }
    .mechanism-rows div {
      border-top: 1px solid var(--border);
      padding-top: 10px;
    }
    .mechanism-rows span {
      display: block;
      color: var(--accent);
      font-size: 15px;
      font-weight: 800;
      margin-bottom: 5px;
    }
    .mechanism-rows strong {
      display: block;
      font-size: 18px;
      line-height: 1.3;
      font-weight: 700;
    }
    .pipeline-row.five {
      grid-template-columns: repeat(5, 1fr);
    }
    .pipe-step {
      border: 1px solid var(--border);
      border-top: 6px solid var(--accent);
      border-radius: 6px;
      padding: 18px;
      background: var(--surface);
    }
    .pipe-step span {
      color: var(--accent);
      font-weight: 800;
      font-size: 18px;
    }
    .stat-band {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 22px;
      padding: 22px;
      border: 1px solid var(--border);
      border-radius: 8px;
      background: var(--surface-strong);
    }
    .task-taxonomy {
      display: grid;
      grid-template-columns: repeat(5, 1fr);
      gap: 14px;
    }
    .task-taxonomy article {
      border: 1px solid var(--border);
      border-radius: 6px;
      background: var(--surface);
      padding: 16px 18px;
      min-height: 104px;
    }
    .task-taxonomy strong {
      display: block;
      font-size: 22px;
      line-height: 1.15;
      color: var(--fg);
      margin-bottom: 8px;
    }
    .task-taxonomy span {
      display: inline-block;
      margin-bottom: 8px;
      font-family: var(--font-mono);
      color: var(--accent);
      font-size: 15px;
      font-weight: 800;
    }
    .task-taxonomy p {
      font-size: 17px;
      line-height: 1.32;
      color: var(--muted);
    }
    .stat-card {
      padding: 18px 20px;
      border-left: 6px solid var(--accent-2);
      background: var(--bg);
      border-radius: 6px;
    }
    .stat-card strong {
      display: block;
      margin-bottom: 10px;
      color: var(--accent-2);
      font-family: var(--font-mono);
      font-size: 38px;
      line-height: 1.05;
    }
    .stat-card span {
      display: block;
      color: var(--fg);
      font-size: 23px;
      font-weight: 800;
    }
    .stat-card p {
      margin-top: 8px;
      color: var(--muted);
      font-size: 18px;
      line-height: 1.32;
      font-weight: 560;
    }
    .tradeoff-cards {
      display: grid;
      grid-template-columns: 1.05fr 1fr 1fr;
      gap: 22px;
    }
    .tradeoff-cards article {
      min-height: 205px;
      padding: 24px;
      border: 1px solid var(--border);
      border-radius: 8px;
      background: var(--surface);
    }
    .tradeoff-cards article:first-child {
      grid-row: span 2;
      border-left: 8px solid var(--accent-2);
      background: color-mix(in srgb, var(--accent-2) 8%, var(--bg));
    }
    .tradeoff-cards h3 {
      margin: 8px 0 12px;
      font-size: 27px;
      line-height: 1.22;
    }
    .tradeoff-cards p {
      color: var(--muted);
      font-size: 21px;
      line-height: 1.42;
      font-weight: 560;
    }
    .od-table th {
      font-family: var(--font-body);
      font-size: 18px;
      font-weight: 800;
    }
    .matrix-table {
      border-collapse: separate;
      border-spacing: 0 10px;
    }
    .matrix-table th {
      border: 0;
      padding: 0 10px 2px;
    }
    .matrix-table th span {
      display: inline-flex;
      padding: 6px 12px;
      border-radius: 999px;
      background: var(--fg);
      color: var(--bg);
      font-size: 16px;
    }
    .matrix-table td {
      border-top: 1px solid var(--border);
      border-bottom: 1px solid var(--border);
      background: var(--surface);
      font-size: 18px;
      font-weight: 560;
    }
    .matrix-table td:first-child {
      border-left: 1px solid var(--border);
      border-radius: 8px 0 0 8px;
    }
    .matrix-table td:last-child {
      border-right: 1px solid var(--border);
      border-radius: 0 8px 8px 0;
    }
    .task-reasons > div {
      grid-template-columns: 58px 1fr;
      gap: 4px 14px;
      background: var(--surface);
    }
    .task-reasons p {
      grid-column: 2;
      color: var(--muted);
      font-size: 18px;
      line-height: 1.3;
      font-weight: 560;
    }
    figcaption {
      color: var(--muted);
      font-weight: 700;
    }
    .screenshot-frame {
      border-color: var(--border);
      background: #11151a;
    }
    .conclusion-bar {
      border: 1px solid var(--border);
      border-left: 8px solid var(--accent);
      border-radius: 6px;
      padding: 16px 22px;
      background: var(--surface-strong);
      color: var(--fg);
      font-size: 24px;
      line-height: 1.42;
      font-weight: 760;
    }
    .factorial-cards {
      display: grid;
      gap: 18px;
      align-content: center;
    }
    .factorial-cards article {
      padding: 22px;
      border: 1px solid var(--border);
      border-radius: 8px;
      background: var(--surface);
    }
    .factorial-cards h3 {
      margin: 0 0 14px;
      font-size: 26px;
    }
    .factorial-metrics {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }
    .factorial-metrics .pill {
      flex-direction: column;
      align-items: flex-start;
      min-width: 118px;
      padding: 10px 12px;
    }
    .factorial-metrics strong {
      font-size: 28px;
      line-height: 1;
      color: var(--accent-2);
    }
    .factorial-metrics span {
      margin-top: 4px;
      font-size: 13px;
      color: var(--muted);
    }
    .factorial-cards p {
      margin-top: 8px;
      color: var(--muted);
      font-weight: 700;
    }
    .callout-panel strong {
      color: var(--fg);
    }
    .metric-inline {
      color: var(--accent-2);
    }
    .method-mini span,
    .dark .method-mini span {
      color: var(--fg);
      border-top-color: var(--accent);
      font-weight: 700;
    }
    .agent-proxy-list {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 14px;
      align-content: stretch;
    }
    .agent-proxy-list article {
      padding: 14px 16px;
      border: 1px solid var(--border);
      border-radius: 8px;
      background: var(--surface);
    }
    .agent-proxy-list h3 {
      margin: 0 0 10px;
      font-size: 19px;
      line-height: 1.2;
    }
    .proxy-metrics {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 6px;
    }
    .proxy-metric {
      display: grid;
      gap: 2px;
      padding: 6px 7px;
      border: 1px solid var(--border);
      border-radius: 6px;
      background: var(--bg);
    }
    .proxy-metric em {
      color: var(--accent);
      font-size: 11px;
      font-style: normal;
      font-weight: 850;
      line-height: 1;
    }
    .proxy-metric strong {
      color: var(--fg);
      font-family: var(--font-mono);
      font-size: 14px;
      line-height: 1.05;
    }
    .agent-proxy-list p {
      margin-top: 8px;
      color: var(--muted);
      font-size: 14px;
      font-weight: 650;
      line-height: 1.25;
    }
    .limit-groups {
      display: grid;
      grid-template-columns: 1.05fr 0.95fr;
      gap: 24px;
    }
    .limit-group {
      position: relative;
      min-height: 235px;
      padding: 28px 30px;
      border: 1px solid var(--border);
      border-radius: 10px;
      background: var(--surface);
      overflow: hidden;
    }
    .limit-group::before {
      content: "";
      position: absolute;
      inset: 0 auto 0 0;
      width: 10px;
      background: var(--accent);
    }
    .limit-group.g2::before { background: var(--warn); }
    .limit-group.g3::before { background: var(--success); }
    .limit-group.g4::before { background: var(--accent-2); }
    .limit-nb {
      font-family: var(--font-mono);
      color: var(--accent);
      font-size: 18px;
      font-weight: 800;
    }
    .limit-group h3 {
      margin: 8px 0 10px;
      font-size: 34px;
      line-height: 1.05;
    }
    .limit-group p {
      color: var(--fg);
      font-size: 22px;
      line-height: 1.38;
      font-weight: 680;
      margin-bottom: 18px;
    }
    .closing {
      max-width: 1540px;
    }
    .closing h2 {
      color: var(--fg);
      font-size: 72px;
      line-height: 1.12;
    }
    .closing-grid {
      gap: 28px;
      margin-top: 58px;
    }
    .closing-grid > div {
      min-height: 220px;
      padding: 30px;
      border-top: 8px solid var(--accent);
      background: var(--surface);
    }
    .closing-grid > div:nth-child(2) { border-top-color: var(--warn); }
    .closing-grid > div:nth-child(3) { border-top-color: var(--accent-2); }
    .closing-grid strong {
      color: var(--accent);
      font-size: 44px;
    }
    .closing-grid h3 {
      margin: 14px 0 12px;
      font-size: 32px;
      line-height: 1.1;
    }
    .closing-grid p {
      color: var(--fg);
      font-size: 27px;
      font-weight: 680;
    }
    .deck-counter {
      position: fixed;
      bottom: 18px;
      left: 50%;
      transform: translateX(-50%);
      display: none;
      align-items: center;
      gap: 4px;
      background: color-mix(in srgb, var(--shell) 88%, transparent);
      color: var(--dark-text);
      padding: 5px;
      border-radius: 6px;
      border: 1px solid color-mix(in srgb, var(--dark-text) 14%, transparent);
      font: 12px/1 var(--font-mono);
      letter-spacing: 0;
      z-index: 1000;
    }
    .deck-counter button {
      width: 34px;
      height: 34px;
      background: transparent;
      color: var(--dark-text);
      border: 0;
      border-radius: 4px;
      font-size: 20px;
      line-height: 1;
      cursor: pointer;
      display: grid;
      place-items: center;
    }
    .deck-counter button:hover { background: color-mix(in srgb, var(--dark-text) 10%, transparent); }
    .deck-counter button[disabled] { opacity: 0.28; cursor: default; }
    .deck-count { padding: 0 12px; }
    .deck-count .total { color: color-mix(in srgb, var(--dark-text) 50%, transparent); }
    @media print {
      @page { size: 1920px 1080px; margin: 0; }
      html, body {
        width: 1920px !important;
        height: auto !important;
        overflow: visible !important;
        background: var(--bg) !important;
      }
      .deck-stage {
        position: static !important;
        top: auto !important;
        left: auto !important;
        transform: none !important;
        width: 1920px !important;
        height: auto !important;
        overflow: visible !important;
      }
      .slide {
        display: flex !important;
        position: relative !important;
        inset: auto !important;
        width: 1920px !important;
        height: 1080px !important;
        page-break-after: always;
        break-after: page;
      }
      .slide:last-child { page-break-after: auto; break-after: auto; }
      .deck-counter { display: none !important; }
    }
    /* v2_7 additions */
    mark.leak {
      background: color-mix(in srgb, var(--warn) 34%, transparent);
      color: #7a3c00;
      padding: 1px 5px;
      border-radius: 3px;
      font-weight: 800;
    }
    .od-table.compact th { font-size: 21px; }
    .rq-legend {
      font-family: var(--font-mono);
      font-size: 17px;
      color: var(--muted);
      font-weight: 700;
    }
    .env-legend {
      font-size: 16px;
      line-height: 1.5;
      color: var(--muted);
      font-weight: 600;
    }
    .env-legend b { color: var(--accent); font-family: var(--font-mono); }
    .cell-mark {
      font-style: normal;
      font-size: 13px;
      margin-left: 4px;
      color: var(--accent-2);
      vertical-align: super;
    }
    .cell-mark.soft { color: var(--muted); }
    .matrix-table td .pinned-pill {
      border-color: color-mix(in srgb, var(--accent-2) 45%, var(--border));
      font-weight: 800;
    }
    .matrix-table td .default-pill { background: var(--surface-strong); }
    .case-context {
      border-left: 6px solid var(--accent);
      background: var(--surface-strong);
      border-radius: 0 6px 6px 0;
      padding: 12px 18px;
      font-size: 19px;
      line-height: 1.5;
      color: var(--fg);
      font-weight: 600;
    }
    .big-tag {
      display: inline-flex;
      align-items: center;
      padding: 6px 14px;
      border-radius: 999px;
      background: var(--fg);
      color: var(--bg);
      font-family: var(--font-mono);
      font-size: 19px;
      font-weight: 800;
    }
    .pipe-step p {
      margin-top: 8px;
      font-size: 14px;
      line-height: 1.3;
      color: var(--muted);
      font-weight: 600;
    }
    .case-gallery {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 16px;
    }
    .gallery-card {
      border: 1px solid var(--border);
      border-radius: 8px;
      background: var(--surface);
      padding: 16px 18px;
      display: grid;
      gap: 8px;
      align-content: start;
    }
    .gallery-card header {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 6px 10px;
    }
    .gc-id { font-family: var(--font-mono); font-weight: 800; color: var(--accent-2); font-size: 18px; }
    .gc-task { font-family: var(--font-mono); font-size: 13px; color: var(--muted); flex: 1; min-width: 0; }
    .gc-side {
      display: grid;
      grid-template-columns: 1fr auto;
      gap: 2px 10px;
      border-top: 1px solid var(--border);
      padding-top: 7px;
    }
    .gc-cfg { font-family: var(--font-mono); font-size: 14px; font-weight: 700; color: var(--fg); }
    .gc-succ { font-family: var(--font-mono); font-size: 15px; font-weight: 800; color: var(--accent-2); }
    .gc-path { grid-column: 1 / -1; font-family: var(--font-mono); font-size: 12.5px; line-height: 1.5; color: var(--muted); word-break: break-word; }
    .gc-find { font-size: 14.5px; line-height: 1.4; color: var(--fg); font-weight: 650; }
    .gc-meta { font-family: var(--font-mono); font-size: 12px; color: var(--muted); }
    .case-deep.tight .case-card.large { min-height: 196px; }
    .thinking-reveal {
      border: 1px solid var(--border);
      border-left: 8px solid var(--accent-2);
      border-radius: 8px;
      background: color-mix(in srgb, var(--accent-2) 6%, var(--bg));
      padding: 16px 22px;
    }
    .tr-label {
      display: block;
      font-family: var(--font-mono);
      font-size: 16px;
      font-weight: 800;
      color: var(--accent-2);
      margin-bottom: 12px;
    }
    .tr-grid { display: grid; grid-template-columns: 0.85fr 1.15fr; gap: 24px; }
    .tr-grid > div { display: grid; gap: 6px; align-content: start; }
    .tr-grid strong { font-size: 18px; color: var(--fg); }
    .tr-grid p { font-size: 18px; line-height: 1.42; color: var(--fg); font-weight: 600; }
    code {
      font-family: var(--font-mono);
      font-size: 16px;
      background: var(--surface-strong);
      border: 1px solid var(--border);
      border-radius: 4px;
      padding: 2px 8px;
      color: var(--accent-2);
      font-weight: 700;
    }
  </style>
</head>
<body>
  <div class="deck-stage" id="deck-stage">
    ${slides.join('\n')}
  </div>
  <nav class="deck-counter" role="navigation" aria-label="Deck navigation">
    <button type="button" id="deck-prev" aria-label="Previous slide">‹</button>
    <span class="deck-count"><span id="deck-cur">01</span> <span class="total">/ <span id="deck-total">28</span></span></span>
    <button type="button" id="deck-next" aria-label="Next slide">›</button>
  </nav>
  <script>
    (function () {
      var root = document.documentElement;
      var slides = Array.prototype.slice.call(document.querySelectorAll('.slide'));
      var prev = document.getElementById('deck-prev');
      var next = document.getElementById('deck-next');
      var cur = document.getElementById('deck-cur');
      var total = document.getElementById('deck-total');
      var idx = 0;
      function fit() {
        var sw = window.innerWidth;
        var sh = window.innerHeight;
        if (sw <= 0 || sh <= 0) return;
        var pad = 24;
        var s = Math.min((sw - pad) / 1920, (sh - pad) / 1080);
        if (!isFinite(s) || s <= 0) s = 1;
        root.style.setProperty('--deck-scale', String(s));
      }
      function pad2(n) { return (n < 10 ? '0' : '') + n; }
      function paint() {
        slides.forEach(function (el, i) { el.classList.toggle('active', i === idx); });
        if (cur) cur.textContent = pad2(idx + 1);
        if (total) total.textContent = pad2(slides.length);
        if (prev) prev.toggleAttribute('disabled', idx <= 0);
        if (next) next.toggleAttribute('disabled', idx >= slides.length - 1);
      }
      function go(i) {
        idx = Math.max(0, Math.min(slides.length - 1, i));
        paint();
      }
      function onKey(e) {
        if (e.__deckHandled) return;
        e.__deckHandled = true;
        var t = e.target;
        if (t && (t.tagName === 'INPUT' || t.tagName === 'TEXTAREA' || t.isContentEditable)) return;
        if (e.key === 'ArrowRight' || e.key === 'PageDown' || e.key === ' ') { e.preventDefault(); go(idx + 1); }
        else if (e.key === 'ArrowLeft' || e.key === 'PageUp') { e.preventDefault(); go(idx - 1); }
        else if (e.key === 'Home') { e.preventDefault(); go(0); }
        else if (e.key === 'End') { e.preventDefault(); go(slides.length - 1); }
      }
      window.addEventListener('keydown', onKey, true);
      document.addEventListener('keydown', onKey, true);
      if (prev) prev.addEventListener('click', function () { go(idx - 1); });
      if (next) next.addEventListener('click', function () { go(idx + 1); });
      document.body.setAttribute('tabindex', '-1');
      document.body.style.outline = 'none';
      function focusDeck() { try { window.focus(); document.body.focus({ preventScroll: true }); } catch (_) {} }
      document.addEventListener('mousedown', focusDeck);
      window.addEventListener('load', focusDeck);
      window.addEventListener('resize', fit);
      if (typeof ResizeObserver === 'function') {
        try { new ResizeObserver(fit).observe(document.documentElement); } catch (_) {}
      }
      fit();
      paint();
      focusDeck();
    })();
  </script>
</body>
</html>
`;

  const manifest = `# xAI Faithfulness Harness v2_7 HTML deck

Generated: 2026-06-05 (v2_7; wording compressed for formal presentation)

Canonical entry:
- \`xAI-faithfulness-harness-v2_7.html\`

Design sources used:
- Open Design deck framework
- simple-deck skill guidance
- anti-slop, color, and typography craft notes
- x-ai design system

Hard checks designed into the build:
- 28 slides (v2 的 27 頁 + 新增「案例分析總覽」第 22 頁).
- Traditional Chinese primary copy; technical terms remain English.
- Structural slides are HTML/CSS, not pasted SVG.
- Data charts are copied from source SVG files.
- Screenshots are inserted with \`object-fit: contain\`.
- Slide 22 = 6-case gallery (case-candidates.csv); slide 23 = XAI-C03 deep dive.
- RQ recovery: RQ3 on 18/19, RQ2 on 20, RQ1 on 21, RQ4 on 24.

v2_7 修訂重點:
- Slide 02 改寫動機案例，移除需預先知道 XAI-C01 的說法。
- Slide 03 與 Slide 11 壓縮邊界文字，只保留 provider 可見度與欄位控制。
- Slide 05、07、09、11、12、13、16、17、22、27、28 改為正式簡報語氣。
- Slide 07 補上 20 題任務類型；Slide 27 加入平均 token 用量分析。
- 可見文字移除長破折號與 en dash。
`;

  await fs.writeFile(outputHtml, html, 'utf8');
  await fs.writeFile(manifestPath, manifest, 'utf8');
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
