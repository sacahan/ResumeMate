/**
 * Infographics Hub — renders data/infographics.json into the Content Hub tab.
 * Calls window.openLightboxUrl(url, alt) for lightbox display.
 */
(function () {
  let allImages = [];
  let loaded = false;

  async function loadHub() {
    if (loaded) { renderHub(); return; }
    try {
      const r = await fetch('data/infographics.json');
      if (!r.ok) throw new Error('infographics.json not found');
      const d = await r.json();
      allImages = d.images || [];
      loaded = true;
    } catch (e) {
      console.warn('infographics-hub.js:', e.message);
      allImages = [];
      loaded = true;
    }
    renderHub();
  }

  function renderHub() {
    const container = document.getElementById('hub-infographics');
    if (!container) return;
    const lang = window.getCurrentLang ? window.getCurrentLang() : 'zh';
    const isZH = lang === 'zh';
    const viewAllLabel = isZH ? '查看全部資訊圖表 →' : 'View all infographics →';

    if (!allImages.length) {
      container.innerHTML = `<p style="color:var(--muted2);font-size:14px;">${isZH ? '暫無圖表' : 'No infographics yet'}</p>`;
      return;
    }

    const [featured, ...rest] = allImages;
    const smallCards = rest.slice(0, 6);

    const fTitle = isZH ? featured.title_zh : featured.title_en;
    const fTag   = (featured.tags || [])[0] || 'Featured';

    const featuredHtml = `
<div class="chart-card-featured" onclick="window.openLightboxUrl('${esc(featured.url)}','${esc(fTitle)}')" style="cursor:pointer;">
  <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;">
    <span style="font-family:'JetBrains Mono',monospace;font-size:11px;color:var(--accentBright);background:rgba(var(--accentRGB),.12);border-radius:6px;padding:3px 9px;">${esc(fTag)}</span>
    <span style="font-family:'JetBrains Mono',monospace;font-size:10px;color:var(--faint);">Featured</span>
  </div>
  <h3 style="margin:0 0 16px;font-size:20px;font-weight:700;color:var(--text);line-height:1.35;">${esc(fTitle)}</h3>
  <div style="flex:1;min-height:200px;border-radius:12px;overflow:hidden;">
    <img src="${esc(featured.thumbnail || featured.url)}" alt="${esc(fTitle)}" loading="lazy" style="width:100%;height:100%;object-fit:cover;display:block;">
  </div>
</div>`;

    const smallHtml = smallCards.map(img => {
      const title = isZH ? img.title_zh : img.title_en;
      const tag   = (img.tags || [])[0] || '';
      return `
<div class="chart-card" onclick="window.openLightboxUrl('${esc(img.url)}','${esc(title)}')" style="cursor:pointer;">
  <span style="font-family:'JetBrains Mono',monospace;font-size:11px;color:var(--accentBright);background:rgba(var(--accentRGB),.12);border-radius:6px;padding:3px 9px;">${esc(tag)}</span>
  <h3 style="margin:10px 0 12px;font-size:15px;font-weight:700;color:var(--text);line-height:1.3;">${esc(title)}</h3>
  <div style="flex:1;min-height:100px;border-radius:10px;overflow:hidden;">
    <img src="${esc(img.thumbnail || img.url)}" alt="${esc(title)}" loading="lazy" style="width:100%;height:100%;object-fit:cover;display:block;">
  </div>
</div>`;
    }).join('');

    container.innerHTML = `
<div style="display:grid;grid-template-columns:1.4fr 1fr;grid-template-rows:auto auto;gap:22px;">
  ${featuredHtml}
  <div style="display:contents;">${smallHtml}</div>
</div>
<div style="text-align:center;margin-top:30px;">
  <a href="infographics.html" style="display:inline-flex;align-items:center;gap:8px;padding:12px 24px;border-radius:11px;background:var(--whiteSoft);border:1px solid var(--border2);color:var(--text);font-weight:600;font-size:14px;text-decoration:none;transition:border-color .2s;" onmouseover="this.style.borderColor='rgba(var(--accentRGB),.4)'" onmouseout="this.style.borderColor='var(--border2)'">${viewAllLabel}</a>
</div>`;
  }

  function esc(s) {
    return String(s || '').replace(/'/g, '&#39;').replace(/"/g, '&quot;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
  }

  window.loadInfographicsHub = loadHub;
  window.renderInfographicsHub = renderHub;
})();
