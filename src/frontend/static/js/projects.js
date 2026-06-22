/**
 * Portfolio Projects — fetches data/projects.json and renders a CSS grid.
 * No Swiper dependency. Listens for lang changes via window.onLangChange.
 */
(function () {
  let allProjects = [];

  async function loadProjects() {
    try {
      const r = await fetch('data/projects.json');
      if (!r.ok) throw new Error('projects.json not found');
      const d = await r.json();
      allProjects = d.projects || [];
    } catch (e) {
      console.warn('projects.js:', e.message);
      allProjects = [];
    }
    renderProjects();
  }

  function renderProjects() {
    const grid = document.getElementById('work-grid');
    if (!grid) return;
    const lang = window.getCurrentLang ? window.getCurrentLang() : 'zh';
    const isZH = lang === 'zh';
    const viewLabel = isZH ? '查看' : 'View';

    if (!allProjects.length) {
      grid.innerHTML = `<p style="color:var(--muted2);font-size:14px;">載入中...</p>`;
      return;
    }

    grid.innerHTML = allProjects.map(proj => {
      const title = isZH ? proj.title_zh : proj.title_en;
      const desc  = isZH ? proj.desc_zh  : proj.desc_en;
      const tag   = (proj.tags || [])[0] || '';
      const href  = proj.githubUrl || proj.demoUrl || '#';
      const hasCover = proj.cover && proj.cover.trim();

      return `
<a href="${escHtml(href)}" target="_blank" rel="noopener" class="project-card">
  <div style="position:relative;aspect-ratio:16/9;overflow:hidden;background:repeating-linear-gradient(135deg,var(--stripe1) 0 13px,var(--stripe2) 13px 26px);">
    ${hasCover
      ? `<img src="${escHtml(proj.cover)}" alt="${escHtml(title)}" loading="lazy" style="width:100%;height:100%;object-fit:cover;display:block;">`
      : `<div style="width:100%;height:100%;display:flex;align-items:center;justify-content:center;"><span style="font-family:'JetBrains Mono',monospace;font-size:12px;color:var(--faint);">${escHtml(title)}</span></div>`
    }
    <span style="position:absolute;top:12px;left:12px;font-family:'JetBrains Mono',monospace;font-size:11px;color:var(--accentBright);background:rgba(var(--accentRGB),.85);border-radius:6px;padding:3px 9px;">${escHtml(tag)}</span>
  </div>
  <div style="padding:18px 20px 22px;">
    <h3 style="margin:0 0 8px;font-size:18px;font-weight:700;color:var(--text);">${escHtml(title)}</h3>
    <p style="margin:0 0 12px;font-size:14px;line-height:1.65;color:var(--muted2);font-weight:300;">${escHtml(desc)}</p>
    <div style="display:flex;flex-wrap:wrap;gap:6px;margin-bottom:14px;">
      ${(proj.tags || []).slice(0, 4).map(t => `<span style="font-family:'JetBrains Mono',monospace;font-size:10px;color:var(--muted2);background:var(--whiteSoft);border:1px solid var(--border);border-radius:5px;padding:2px 8px;">${escHtml(t)}</span>`).join('')}
    </div>
    <div style="display:flex;gap:10px;">
      ${proj.demoUrl ? `<a href="${escHtml(proj.demoUrl)}" target="_blank" rel="noopener" onclick="event.stopPropagation()" style="font-family:'JetBrains Mono',monospace;font-size:12px;color:var(--accentBright);font-weight:700;text-decoration:none;">Demo →</a>` : ''}
      ${proj.githubUrl ? `<a href="${escHtml(proj.githubUrl)}" target="_blank" rel="noopener" onclick="event.stopPropagation()" style="font-family:'JetBrains Mono',monospace;font-size:12px;color:var(--muted2);font-weight:600;text-decoration:none;">GitHub ↗</a>` : ''}
    </div>
  </div>
</a>`;
    }).join('');
  }

  function escHtml(s) {
    return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
  }

  document.addEventListener('DOMContentLoaded', loadProjects);
  window.renderProjects = renderProjects;
})();
