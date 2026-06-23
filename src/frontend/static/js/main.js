/**
 * ResumeMate main.js — portfolio logic, chat, language switching.
 * AI chat calls POST /api/chat  { text, language, conversation_id }
 * Set window.CHAT_API_URL before this script to override the endpoint.
 */

// ─── Content ───────────────────────────────────────────────────────────────
const content = {
  zh: {
    brand:'韓世翔', role:'資深軟體工程師 · AI 應用開發',
    navAbout:'關於', navCareer:'職涯', navWork:'作品', navContent:'文章 & 圖表', navChat:'AI 問答',
    heroEyebrow:'AI Application Engineer',
    heroTitleA1:'打造會思考的', heroTitleA2:'AI 產品。',
    heroSubA:'我是 Brian（韓世翔），深耕全端開發逾 18 年，專精 Java 企業級應用與雲端微服務。現專注 AI Agent 驅動的企業工作流程重構，將模型能力轉化為可擴展的產品級解決方案。',
    ctaPrimary:'與我聯絡', ctaSecondary:'看我的職涯',
    stat1n:'18+', stat1l:'年開發經驗', stat2n:'80%', stat2l:'CI/CD 部署提速', stat3n:'10萬+', stat3l:'日均資料寫入',
    aboutEyebrow:'About Me', aboutTitle:'在研究與產品之間，我選擇兩者兼顧。',
    aboutP1:'深耕全端軟體開發與系統架構設計逾 18 年，專精 Java 企業級應用與雲端微服務架構，具備從需求分析、系統設計、測試到生產部署的完整開發週期實戰經驗。',
    aboutP2:'長期服務電信與金融保險產業，歷任資深工程師與技術主任，帶領團隊交付企業入口網站、核心業務系統、CI/CD 自動化及 AI 應用整合解決方案。',
    aboutP3:'工作之外積極參與開源社群與技術研討會。現階段聚焦新一代 LLM + AI Agent 框架的實作應用，期待將前沿 AI 與實際業務場景深度融合。',
    skills:['Python','Java / Spring Boot','TypeScript','React / Vue','LLM Fine-tuning','OpenAI Agent SDK','CrewAI','Docker / K8s','CI/CD','AWS / GCP'],
    careerEyebrow:'Career', careerTitle:'職涯經歷',
    jobs:[
      {period:'2024.01 — 2025.05',org:'台灣大哥大電信',role:'資深主任工程師',desc:'主導企業用戶網站架構設計與開發，整合後端 CMS 及前端分散式服務。承接資策會 ASR 專案部署多語言語音辨識平台，並參與加密貨幣與電商平台重構，建構企業級 CI/CD 與報表系統。亦擔任 AppWorks 大使導師。'},
      {period:'2016.03 — 2023.12',org:'台灣之星電信',role:'主任工程師',desc:'負責企業入口網站與多項 Portal 系統架構。設計高效能 IoT 企業管理平台，日均支援 10 萬筆以上寫入並提供 RESTful API。實作雙 11 高併發認證機制，導入 Jenkins + Docker CI/CD，上線時間縮短達 80%。'},
      {period:'2006.03 — 2016.02',org:'R&D / 外派駐點',role:'軟體工程師',desc:'參與零售、金融保險、電信等產業的企業級軟體開發，擔綱系統分析、架構設計、全端開發與資料庫建模。以 Java 為主，精通 JavaScript、SQL、PHP，協助多家企業數位轉型。'},
      {period:'2002.09 — 2004.06',org:'中原大學',role:'資訊管理研究所 碩士',desc:'研究重點為結合行動裝置與環境智慧、提升學習成效的系統平台。論文：考量環境智慧之適性化行動學習平台。'}
    ],
    workEyebrow:'Portfolio', workTitle:'精選作品', workSub:'根據個人發想開發的 AI 專案與工具，持續更新中。',
    contentEyebrow:'Content Hub', contentTitle:'文章 & 資訊圖表', contentSub:'我的思考和視覺化整理，持續更新中。',
    artTabLabel:'文章', chartTabLabel:'資訊圖表',
    articles:[
      {cat:'LLM',date:'2026.05.18',title:'從 Prompt 到 Agent：我如何設計可靠的 AI 工作流',label:'封面圖 4:3',excerpt:'談談把單次 prompt 演進成多步驟 agent 的工程取捨與心得。',read:'閱讀全文'},
      {cat:'產品',date:'2026.04.02',title:'AI 產品的「最後一哩」：上線後才是真正的開始',label:'封面圖 4:3',excerpt:'模型 demo 很驚艷，但真正的挑戰在監控、回饋與迭代。',read:'閱讀全文'},
      {cat:'MLOps',date:'2026.02.27',title:'把模型迭代週期從兩週縮短到兩天的實作筆記',label:'封面圖 4:3',excerpt:'一套讓團隊敢於快速實驗的 MLOps 流程拆解。',read:'閱讀全文'},
      {cat:'隨筆',date:'2026.01.11',title:'工程師為什麼要寫作？我的數位花園實驗',label:'封面圖 4:3',excerpt:'紀錄、整理、分享，如何讓我成為更好的工程師。',read:'閱讀全文'}
    ],
    catLabel:'分類',
    cats:[{name:'LLM / Agent',count:'12'},{name:'產品思考',count:'08'},{name:'MLOps',count:'06'},{name:'資訊圖表',count:'05'},{name:'隨筆',count:'09'}],
    subTitle:'訂閱我的筆記', subSub:'不定期寄出 AI 產品與工程的整理，不寄垃圾信。', subPlaceholder:'你的 Email', subBtn:'訂閱',
    chatEmpty:'嗨！我是韓世翔的 AI 分身。你可以問我關於他的工作經歷、技術專長或任何專案細節。',
    chatPlaceholder:'輸入你的問題…', chatSend:'送出',
    suggestions:['他最擅長什麼技術？','介紹一個代表性專案','為什麼適合 AI 產品的角色？'],
    contactEyebrow:"Let's talk", contactTitle:'一起打造些什麼吧',
    contactSub:'不論是合作、職缺，或只是想聊聊 AI 與工程，都歡迎來信或私訊。',
    contactBtn:'寄信給我',
    socials:[
      {label:'GitHub',href:'https://github.com/sacahan'},
      {label:'Telegram @sacahan',href:'https://t.me/sacahan'},
      {label:'sacahan@gmail.com',href:'mailto:sacahan@gmail.com'}
    ],
    footerNote:'Designed & built with care'
  },
  en: {
    brand:'Brian Han', role:'Senior Software Engineer · AI',
    navAbout:'About', navCareer:'Career', navWork:'Work', navContent:'Articles & Charts', navChat:'AI Chat',
    heroEyebrow:'AI Application Engineer',
    heroTitleA1:'Building AI', heroTitleA2:'that thinks.',
    heroSubA:"I'm Brian — 18+ years in full-stack development, specializing in Java enterprise apps and cloud microservices. Now focused on AI-agent-driven enterprise workflows, turning model capabilities into scalable, production-grade solutions.",
    ctaPrimary:'Get in touch', ctaSecondary:'View my career',
    stat1n:'18+', stat1l:'Years building', stat2n:'80%', stat2l:'Faster deploys', stat3n:'100K+', stat3l:'Daily writes',
    aboutEyebrow:'About Me', aboutTitle:'I refuse to choose between research and product.',
    aboutP1:'18+ years in full-stack development and system architecture, specializing in Java enterprise applications and cloud microservices, with end-to-end experience from requirements to production deployment.',
    aboutP2:'Long-time service to telecom and finance/insurance industries; held senior engineer and technical lead roles delivering enterprise portals, core business systems, CI/CD automation and AI integration solutions.',
    aboutP3:'Outside work, active in open-source communities and tech conferences. Currently focused on next-gen LLM + AI Agent frameworks, eager to fuse frontier AI with real business scenarios.',
    skills:['Python','Java / Spring Boot','TypeScript','React / Vue','LLM Fine-tuning','OpenAI Agent SDK','CrewAI','Docker / K8s','CI/CD','AWS / GCP'],
    careerEyebrow:'Career', careerTitle:'Work Experience',
    jobs:[
      {period:'2024.01 — 2025.05',org:'Taiwan Mobile',role:'Senior Lead Engineer',desc:'Led enterprise user portal architecture and development, integrating backend CMS and front-end distributed services. Deployed a multilingual ASR platform (III project), worked on crypto and e-commerce refactors, and built enterprise CI/CD and reporting. Also an AppWorks ambassador mentor.'},
      {period:'2016.03 — 2023.12',org:'T Star Telecom',role:'Lead Engineer',desc:'Owned enterprise portals and multiple Portal systems. Designed a high-performance IoT management platform supporting 100K+ daily writes with RESTful APIs, built Double-11 high-concurrency auth, and introduced Jenkins + Docker CI/CD that cut deploy time by 80%.'},
      {period:'2006.03 — 2016.02',org:'R&D / On-site',role:'Software Engineer',desc:'Delivered enterprise software for retail, finance/insurance and telecom — system analysis, architecture, full-stack and DB modeling. Java-centric, fluent in JavaScript, SQL and PHP, helping many firms with digital transformation.'},
      {period:'2002.09 — 2004.06',org:'Chung Yuan Christian Univ.',role:'M.S. Information Management',desc:'Research focused on an adaptive mobile learning platform combining mobile devices and ambient intelligence to improve learning outcomes.'}
    ],
    workEyebrow:'Portfolio', workTitle:'Selected Work', workSub:'AI projects and tools built from my own ideas — continuously updated.',
    contentEyebrow:'Content Hub', contentTitle:'Articles & Infographics', contentSub:'My thoughts and visual guides, continuously updated.',
    artTabLabel:'Articles', chartTabLabel:'Infographics',
    articles:[
      {cat:'LLM',date:'2026.05.18',title:'From Prompt to Agent: designing reliable AI workflows',label:'Cover 4:3',excerpt:'The engineering tradeoffs of evolving a single prompt into a multi-step agent.',read:'Read more'},
      {cat:'Product',date:'2026.04.02',title:'The last mile of AI products: launch is where it begins',label:'Cover 4:3',excerpt:'The demo dazzles, but the real work is monitoring, feedback and iteration.',read:'Read more'},
      {cat:'MLOps',date:'2026.02.27',title:'Notes on cutting iteration from two weeks to two days',label:'Cover 4:3',excerpt:'An MLOps setup that makes a team brave enough to experiment fast.',read:'Read more'},
      {cat:'Essay',date:'2026.01.11',title:'Why engineers should write: my digital garden experiment',label:'Cover 4:3',excerpt:'How recording, organizing and sharing makes me a better engineer.',read:'Read more'}
    ],
    catLabel:'Categories',
    cats:[{name:'LLM / Agent',count:'12'},{name:'Product',count:'08'},{name:'MLOps',count:'06'},{name:'Infographics',count:'05'},{name:'Essays',count:'09'}],
    subTitle:'Subscribe to my notes', subSub:'Occasional digests on AI products and engineering. No spam.', subPlaceholder:'Your email', subBtn:'Join',
    chatEmpty:"Hi! I'm Brian's AI twin. Ask me anything about his experience, skills, or projects.",
    chatPlaceholder:'Type your question…', chatSend:'Send',
    suggestions:['What is he best at?','Describe a signature project','Why a fit for AI product roles?'],
    contactEyebrow:"Let's talk", contactTitle:"Let's build something",
    contactSub:"Collaboration, a role, or just chatting about AI and product — I'd love to hear from you.",
    contactBtn:'Email me',
    socials:[
      {label:'GitHub',href:'https://github.com/sacahan'},
      {label:'Telegram @sacahan',href:'https://t.me/sacahan'},
      {label:'sacahan@gmail.com',href:'mailto:sacahan@gmail.com'}
    ],
    footerNote:'Designed & built with care'
  }
};

// ─── State ────────────────────────────────────────────────────────────────
let state = {
  lang: 'zh',
  contentTab: 'articles',
  messages: [],
  loading: false
};

let chatInputVal = '';
let conversationId = '';

// ─── Helpers ───────────────────────────────────────────────────────────────
function el(id) { return document.getElementById(id); }
function setText(id, text) { const e = el(id); if (e) e.textContent = text; }
function setClass(id, cls) { const e = el(id); if (e) e.className = cls; }
function escHtml(s) {
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

// ─── Public API (used by projects.js, infographics-hub.js) ────────────────
window.getCurrentLang = function() { return state.lang; };

window.openLightboxUrl = function(url, alt) {
  const img = el('lightbox-img');
  if (img) { img.src = url || ''; img.alt = alt || 'infographic'; }
  const lb = el('lightbox');
  if (lb) lb.style.display = 'flex';
  document.body.style.overflow = 'hidden';
};

// ─── Render ───────────────────────────────────────────────────────────────
function render() {
  const c = content[state.lang];

  setText('nav-brand', c.brand);
  setText('nav-about', c.navAbout);
  setText('nav-career', c.navCareer);
  setText('nav-work', c.navWork);
  setText('nav-content', c.navContent);
  setText('nav-chat', c.navChat);

  setClass('btn-zh', state.lang === 'zh' ? 'lang-active' : 'lang-inactive');
  setClass('btn-en', state.lang === 'en' ? 'lang-active' : 'lang-inactive');

  // Hero A
  setText('hero-a-eyebrow', c.heroEyebrow);
  setText('hero-a-t1', c.heroTitleA1);
  setText('hero-a-t2', c.heroTitleA2);
  setText('hero-a-sub', c.heroSubA);
  setText('cta-primary-a', c.ctaPrimary);
  setText('cta-secondary-a', c.ctaSecondary);
  setText('stat1n', c.stat1n); setText('stat1l', c.stat1l);
  setText('stat2n', c.stat2n); setText('stat2l', c.stat2l);
  setText('stat3n', c.stat3n); setText('stat3l', c.stat3l);

  // About
  setText('about-brand', c.brand);
  setText('about-role', c.role);
  setText('about-eyebrow', c.aboutEyebrow);
  setText('about-title', c.aboutTitle);
  setText('about-p1', c.aboutP1);
  setText('about-p2', c.aboutP2);
  setText('about-p3', c.aboutP3);
  el('skills-grid').innerHTML = c.skills.map(s =>
    `<span class="skill-tag">${escHtml(s)}</span>`
  ).join('');

  // Career
  setText('career-eyebrow', c.careerEyebrow);
  setText('career-title', c.careerTitle);
  el('career-list').innerHTML = c.jobs.map(j => `
<div class="career-row">
  <div>
    <div style="font-family:'JetBrains Mono',monospace;font-size:13px;color:var(--accentBright);margin-bottom:6px;">${escHtml(j.period)}</div>
    <div style="font-size:14px;color:var(--muted2);">${escHtml(j.org)}</div>
  </div>
  <div>
    <h3 style="margin:0 0 10px;font-size:22px;font-weight:700;color:var(--text);">${escHtml(j.role)}</h3>
    <p style="margin:0;font-size:15.5px;line-height:1.75;color:var(--muted);font-weight:300;max-width:640px;">${escHtml(j.desc)}</p>
  </div>
</div>`).join('');

  // Work section heading (grid is filled by projects.js)
  setText('work-eyebrow', c.workEyebrow);
  setText('work-title', c.workTitle);
  setText('work-sub', c.workSub);
  if (window.renderProjects) window.renderProjects();

  // Content Hub
  setText('content-eyebrow', c.contentEyebrow);
  setText('content-title', c.contentTitle);
  setText('content-sub', c.contentSub);

  const artActive = state.contentTab === 'articles';
  const tabArtBtn   = el('tab-art-btn');
  const tabChartBtn = el('tab-chart-btn');
  tabArtBtn.textContent   = c.artTabLabel;
  tabArtBtn.style.color   = artActive ? 'var(--text)' : 'var(--muted2)';
  tabArtBtn.style.borderBottom = artActive ? '2px solid var(--accentBright)' : '2px solid transparent';
  tabChartBtn.textContent = c.chartTabLabel;
  tabChartBtn.style.color = artActive ? 'var(--muted2)' : 'var(--text)';
  tabChartBtn.style.borderBottom = artActive ? '2px solid transparent' : '2px solid var(--accentBright)';

  el('tab-articles').style.display    = artActive ? '' : 'none';
  el('tab-infographics').style.display = artActive ? 'none' : '';

  // Articles
  el('articles-list').innerHTML = c.articles.map(a => `
<a href="#" class="article-card" onclick="return false;">
  <div style="position:relative;aspect-ratio:4/3;background:repeating-linear-gradient(135deg,var(--stripe1) 0 13px,var(--stripe2) 13px 26px);display:flex;align-items:center;justify-content:center;min-width:200px;">
    <span style="font-family:'JetBrains Mono',monospace;font-size:11px;color:var(--faint);">${escHtml(a.label)}</span>
  </div>
  <div style="padding:20px 22px 20px 0;">
    <div style="display:flex;align-items:center;gap:10px;margin-bottom:10px;">
      <span style="font-family:'JetBrains Mono',monospace;font-size:11px;color:var(--accentBright);background:rgba(var(--accentRGB),.12);border-radius:6px;padding:3px 9px;">${escHtml(a.cat)}</span>
      <span style="font-family:'JetBrains Mono',monospace;font-size:11px;color:var(--faint);">${escHtml(a.date)}</span>
    </div>
    <h3 style="margin:0 0 8px;font-size:19px;font-weight:700;line-height:1.4;color:var(--text);">${escHtml(a.title)}</h3>
    <p  style="margin:0 0 12px;font-size:14px;line-height:1.65;color:var(--muted2);font-weight:300;">${escHtml(a.excerpt)}</p>
    <span style="font-family:'JetBrains Mono',monospace;font-size:12px;color:var(--accentBright);font-weight:700;">${escHtml(a.read)} &rarr;</span>
  </div>
</a>`).join('');

  // Categories sidebar
  setText('cat-label', c.catLabel);
  el('cats-list').innerHTML = c.cats.map(cat => `
<div style="display:flex;align-items:center;justify-content:space-between;padding:9px 0;border-bottom:1px solid var(--border);">
  <span style="font-size:14px;color:var(--text2);">${escHtml(cat.name)}</span>
  <span style="font-family:'JetBrains Mono',monospace;font-size:12px;color:var(--faint);">${escHtml(cat.count)}</span>
</div>`).join('');

  // Subscribe box
  setText('sub-title', c.subTitle);
  setText('sub-sub', c.subSub);
  el('sub-input').placeholder = c.subPlaceholder;
  setText('sub-btn', c.subBtn);

  // Infographics hub (re-render on lang change)
  if (window.renderInfographicsHub) window.renderInfographicsHub();

  // Chat
  el('chat-input').placeholder = c.chatPlaceholder;
  setText('chat-send-btn', c.chatSend);
  renderChatMessages(c);
  el('chat-suggestions').innerHTML = c.suggestions.map(q => `
<button onclick="sendMessage(${JSON.stringify(q)})" style="font-size:12px;padding:6px 11px;border-radius:999px;background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.12);color:#c7cad2;cursor:pointer;font-family:'Noto Sans TC',sans-serif;transition:all .2s;" onmouseover="this.style.background='rgba(16,185,129,.14)';this.style.borderColor='rgba(16,185,129,.45)';this.style.color='#6ee7b7';" onmouseout="this.style.background='rgba(255,255,255,.05)';this.style.borderColor='rgba(255,255,255,.12)';this.style.color='#c7cad2';">${escHtml(q)}</button>
`).join('');

  // Contact
  setText('contact-eyebrow', c.contactEyebrow);
  setText('contact-title', c.contactTitle);
  setText('contact-sub', c.contactSub);
  setText('contact-btn', c.contactBtn);
  el('socials-list').innerHTML = c.socials.map(s =>
    `<a href="${escHtml(s.href)}" class="social-link">${escHtml(s.label)}</a>`
  ).join('');
  setText('footer-copy', `© 2026 ${c.brand} · ${c.role}`);
  setText('footer-note', c.footerNote);
}

function renderChatMessages(c) {
  const container = el('chat-messages');
  if (!container) return;
  if (state.messages.length === 0 && !state.loading) {
    container.innerHTML = `
<div style="margin:auto;text-align:center;color:#6b6f7b;display:flex;flex-direction:column;align-items:center;gap:10px;padding:8px;">
  <div style="font-size:28px;opacity:.7;">&#x1F4AC;</div>
  <div style="font-size:13px;max-width:260px;line-height:1.6;">${escHtml(c.chatEmpty)}</div>
</div>`;
    return;
  }
  container.innerHTML = state.messages.map(m => m.role === 'user'
    ? `<div style="align-self:flex-end;max-width:80%;padding:11px 15px;border-radius:14px 14px 4px 14px;background:linear-gradient(135deg,var(--accentGradA),var(--accentGradB));color:#0e0f13;font-size:14px;line-height:1.55;font-weight:600;white-space:pre-wrap;">${escHtml(m.text)}</div>`
    : `<div style="align-self:flex-start;max-width:88%;padding:11px 15px;border-radius:14px 14px 14px 4px;background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.08);color:#c7cad2;font-size:14px;line-height:1.65;font-weight:300;white-space:pre-wrap;">${escHtml(m.text)}</div>`
  ).join('');
  if (state.loading) {
    container.innerHTML += `
<div style="align-self:flex-start;padding:12px 16px;border-radius:14px 14px 14px 4px;background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.08);display:flex;gap:5px;">
  <span style="width:7px;height:7px;border-radius:50%;background:var(--accentBright);animation:dotty 1.2s infinite;display:block;"></span>
  <span style="width:7px;height:7px;border-radius:50%;background:var(--accentBright);animation:dotty 1.2s .2s infinite;display:block;"></span>
  <span style="width:7px;height:7px;border-radius:50%;background:var(--accentBright);animation:dotty 1.2s .4s infinite;display:block;"></span>
</div>`;
  }
  scrollChatToBottom();
}

function scrollChatToBottom() {
  requestAnimationFrame(() => {
    const c = el('chat-messages');
    if (c) c.scrollTop = c.scrollHeight;
  });
}

// ─── State setters ─────────────────────────────────────────────────────────
function setLang(lang) { state.lang = lang; render(); }
function setContentTab(tab) {
  state.contentTab = tab;
  render();
  if (tab === 'infographics' && window.loadInfographicsHub) {
    window.loadInfographicsHub();
  }
}

// ─── Lightbox ─────────────────────────────────────────────────────────────
function openLightbox() {
  el('lightbox').style.display = 'flex';
  document.body.style.overflow = 'hidden';
}
function closeLightbox() {
  el('lightbox').style.display = 'none';
  document.body.style.overflow = '';
}

// ─── Chat ─────────────────────────────────────────────────────────────────
const API_URL = window.CHAT_API_URL || '/api/chat';

function handleChatKey(e) {
  chatInputVal = e.target.value;
  if (e.key === 'Enter') sendMessage();
}

async function sendMessage(preset) {
  const q = (typeof preset === 'string' ? preset : chatInputVal).trim();
  if (!q || state.loading) return;
  const lang = state.lang;
  state.messages = [...state.messages, { role: 'user', text: q }];
  state.loading = true;
  chatInputVal = '';
  el('chat-input').value = '';
  renderChatMessages(content[lang]);
  try {
    const r = await fetch(API_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: q, language: lang === 'zh' ? 'zh-TW' : 'en', conversation_id: conversationId })
    });
    if (!r.ok) throw new Error('HTTP ' + r.status);
    const d = await r.json();
    if (d.conversation_id) conversationId = d.conversation_id;
    const answer = d.answer || d.response || d.message || '';
    state.messages = [...state.messages, { role: 'assistant', text: answer.trim() }];
  } catch {
    const demo = lang === 'zh'
      ? '（離線模式）後端未連線，實際部署後將即時回應你的問題。'
      : '(Offline mode) Backend not connected. Will respond in real-time after deployment.';
    state.messages = [...state.messages, { role: 'assistant', text: demo }];
  }
  state.loading = false;
  renderChatMessages(content[state.lang]);
}

// ─── Keyboard ──────────────────────────────────────────────────────────────
document.addEventListener('keydown', e => { if (e.key === 'Escape') closeLightbox(); });

// ─── Init ──────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', function () {
  render();
  // Pre-load infographics hub data in background
  if (window.loadInfographicsHub) window.loadInfographicsHub();
});
