/**
 * Infographics Gallery Module
 * Handles gallery display, filtering, and full-page lightbox view with keyboard navigation
 */

class InfographicsGallery {
  constructor(options = {}) {
    this.containerId = options.containerId || "infographics-container";
    this.dataUrl = options.dataUrl || "data/infographics.json";
    this.images = [];
    this.filteredImages = [];
    this.currentIndex = 0;
    this.activeTag = null;
    this.lightboxOpen = false;

    this.init();
  }

  async init() {
    await this.loadData();
    this.renderFilterTags();
    this.renderGallery();
    this.createLightbox();
    this.bindEvents();
  }

  async loadData() {
    const container = document.getElementById(this.containerId);
    if (!container) return;

    container.innerHTML = `
      <div class="infographic-loading">
        <div class="spinner"></div>
      </div>
    `;

    try {
      const response = await fetch(this.dataUrl);
      if (!response.ok) throw new Error("Failed to load infographics data");
      const data = await response.json();
      this.images = data.images || [];
      this.filteredImages = [...this.images];
    } catch (error) {
      console.error("Error loading infographics:", error);
      this.images = [];
      this.filteredImages = [];
    }
  }

  getAllTags() {
    const tagSet = new Set();
    this.images.forEach((img) => {
      (img.tags || []).forEach((tag) => tagSet.add(tag));
    });
    return Array.from(tagSet).sort();
  }

  renderFilterTags() {
    const container = document.getElementById(this.containerId);
    if (!container) return;

    const tags = this.getAllTags();
    if (tags.length === 0) return;

    const currentLang = this.getCurrentLanguage();
    const isZH = currentLang.startsWith("zh");

    const allLabel = isZH ? "全部" : "All";

    const filterHtml = `
      <div class="filter-tags-container" id="infographic-filters">
        <button class="filter-tag active" data-tag="">
          ${allLabel}
        </button>
        ${tags.map((tag) => `<button class="filter-tag" data-tag="${tag}">${tag}</button>`).join("")}
      </div>
    `;

    container.insertAdjacentHTML("beforeend", filterHtml);
  }

  renderGallery() {
    const container = document.getElementById(this.containerId);
    if (!container) return;

    // Remove loading state
    const loading = container.querySelector(".infographic-loading");
    if (loading) loading.remove();

    // Check if gallery grid exists, if not create it
    let gallery = container.querySelector(".infographics-grid");
    if (!gallery) {
      gallery = document.createElement("div");
      gallery.className = "infographics-grid";
      container.appendChild(gallery);
    }

    if (this.filteredImages.length === 0) {
      const currentLang = this.getCurrentLanguage();
      const isZH = currentLang.startsWith("zh");
      gallery.innerHTML = `
        <div class="infographic-empty col-span-full">
          <svg class="infographic-empty-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>
          <p>${isZH ? "尚無圖表內容" : "No infographics available"}</p>
        </div>
      `;
      return;
    }

    gallery.innerHTML = this.filteredImages
      .map((img, index) => this.createCardHtml(img, index))
      .join("");
  }

  createCardHtml(img, index) {
    const currentLang = this.getCurrentLanguage();
    const isZH = currentLang.startsWith("zh");

    const title = (isZH ? img.title_zh : img.title_en) || img.title || "";
    const thumbnailUrl = img.thumbnail || img.url;
    const tagsHtml = (img.tags || [])
      .slice(0, 3)
      .map((tag) => `<span class="infographic-tag">${tag}</span>`)
      .join("");

    return `
      <article
        class="infographic-card"
        data-index="${index}"
        tabindex="0"
        role="button"
        aria-label="${title}"
      >
        <div class="infographic-thumbnail">
          <img
            src="${thumbnailUrl}"
            alt="${title}"
            loading="lazy"
          />
        </div>
        <div class="infographic-info">
          <h3 class="infographic-title">${title}</h3>
          <div class="infographic-tags">${tagsHtml}</div>
        </div>
      </article>
    `;
  }

  createLightbox() {
    // Remove existing lightbox if any
    const existing = document.getElementById("infographic-lightbox");
    if (existing) existing.remove();

    const currentLang = this.getCurrentLanguage();
    const isZH = currentLang.startsWith("zh");

    const lightboxHtml = `
      <div id="infographic-lightbox" class="lightbox-overlay" role="dialog" aria-modal="true" aria-label="${isZH ? "圖表檢視" : "Infographic Viewer"}">
        <header class="lightbox-header">
          <h2 class="lightbox-title" id="lightbox-title"></h2>
          <button class="lightbox-close" aria-label="${isZH ? "關閉" : "Close"}">
            <svg width="20" height="20" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </header>

        <div class="lightbox-content">
          <button class="lightbox-nav prev" aria-label="${isZH ? "上一張" : "Previous"}">
            <svg width="24" height="24" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
            </svg>
          </button>

          <div class="lightbox-image-container">
            <img id="lightbox-image" class="lightbox-image" src="" alt="" />
          </div>

          <button class="lightbox-nav next" aria-label="${isZH ? "下一張" : "Next"}">
            <svg width="24" height="24" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
            </svg>
          </button>
        </div>

        <footer class="lightbox-footer">
          <div class="lightbox-tags" id="lightbox-tags"></div>
          <div class="lightbox-counter" id="lightbox-counter"></div>
          <div class="keyboard-hint">
            <span><kbd>←</kbd> ${isZH ? "上一張" : "Previous"}</span>
            <span><kbd>→</kbd> ${isZH ? "下一張" : "Next"}</span>
            <span><kbd>Esc</kbd> ${isZH ? "關閉" : "Close"}</span>
          </div>
        </footer>
      </div>
    `;

    document.body.insertAdjacentHTML("beforeend", lightboxHtml);
  }

  bindEvents() {
    // Filter tag clicks
    document.addEventListener("click", (e) => {
      const filterTag = e.target.closest(".filter-tag");
      if (filterTag && filterTag.closest("#infographic-filters")) {
        this.handleFilterClick(filterTag);
      }
    });

    // Gallery card clicks
    document.addEventListener("click", (e) => {
      const card = e.target.closest(".infographic-card");
      if (card) {
        const index = parseInt(card.dataset.index, 10);
        this.openLightbox(index);
      }
    });

    // Gallery card keyboard activation
    document.addEventListener("keydown", (e) => {
      const card = e.target.closest(".infographic-card");
      if (card && (e.key === "Enter" || e.key === " ")) {
        e.preventDefault();
        const index = parseInt(card.dataset.index, 10);
        this.openLightbox(index);
      }
    });

    // Lightbox events
    const lightbox = document.getElementById("infographic-lightbox");
    if (lightbox) {
      // Close button
      lightbox
        .querySelector(".lightbox-close")
        .addEventListener("click", () => this.closeLightbox());

      // Navigation buttons
      lightbox
        .querySelector(".lightbox-nav.prev")
        .addEventListener("click", () => this.navigate(-1));
      lightbox
        .querySelector(".lightbox-nav.next")
        .addEventListener("click", () => this.navigate(1));

      // Click outside to close
      lightbox.addEventListener("click", (e) => {
        if (
          e.target === lightbox ||
          e.target.classList.contains("lightbox-content")
        ) {
          this.closeLightbox();
        }
      });
    }

    // Global keyboard events
    document.addEventListener("keydown", (e) => this.handleKeydown(e));

    // Language change observer
    if (window.multilingualManager) {
      window.multilingualManager.addObserver((event) => {
        if (event === "languageChanged") {
          this.renderGallery();
          this.createLightbox();
          if (this.lightboxOpen) {
            this.updateLightboxContent();
          }
        }
      });
    }
  }

  handleFilterClick(filterTag) {
    const tag = filterTag.dataset.tag;

    // Update active state
    document
      .querySelectorAll("#infographic-filters .filter-tag")
      .forEach((btn) => {
        btn.classList.remove("active");
      });
    filterTag.classList.add("active");

    // Filter images
    this.activeTag = tag || null;
    if (this.activeTag) {
      this.filteredImages = this.images.filter((img) =>
        (img.tags || []).includes(this.activeTag),
      );
    } else {
      this.filteredImages = [...this.images];
    }

    this.renderGallery();
  }

  handleKeydown(e) {
    if (!this.lightboxOpen) return;

    switch (e.key) {
      case "Escape":
        this.closeLightbox();
        break;
      case "ArrowLeft":
        e.preventDefault();
        this.navigate(-1);
        break;
      case "ArrowRight":
        e.preventDefault();
        this.navigate(1);
        break;
    }
  }

  openLightbox(index) {
    this.currentIndex = index;
    this.lightboxOpen = true;

    const lightbox = document.getElementById("infographic-lightbox");
    if (lightbox) {
      lightbox.classList.add("active");
      document.body.style.overflow = "hidden";
      this.updateLightboxContent();
    }
  }

  closeLightbox() {
    this.lightboxOpen = false;

    const lightbox = document.getElementById("infographic-lightbox");
    if (lightbox) {
      lightbox.classList.remove("active");
      document.body.style.overflow = "";
    }
  }

  navigate(direction) {
    const newIndex = this.currentIndex + direction;

    if (newIndex < 0) {
      this.currentIndex = this.filteredImages.length - 1;
    } else if (newIndex >= this.filteredImages.length) {
      this.currentIndex = 0;
    } else {
      this.currentIndex = newIndex;
    }

    this.updateLightboxContent();
  }

  updateLightboxContent() {
    const img = this.filteredImages[this.currentIndex];
    if (!img) return;

    const currentLang = this.getCurrentLanguage();
    const isZH = currentLang.startsWith("zh");

    const title = (isZH ? img.title_zh : img.title_en) || img.title || "";

    // Update title
    const titleEl = document.getElementById("lightbox-title");
    if (titleEl) titleEl.textContent = title;

    // Update image
    const imageEl = document.getElementById("lightbox-image");
    if (imageEl) {
      imageEl.src = img.url;
      imageEl.alt = title;
    }

    // Update tags
    const tagsEl = document.getElementById("lightbox-tags");
    if (tagsEl) {
      tagsEl.innerHTML = (img.tags || [])
        .map((tag) => `<span class="infographic-tag">${tag}</span>`)
        .join("");
    }

    // Update counter
    const counterEl = document.getElementById("lightbox-counter");
    if (counterEl) {
      counterEl.textContent = `${this.currentIndex + 1} / ${this.filteredImages.length}`;
    }
  }

  getCurrentLanguage() {
    return (
      window.multilingualManager?.currentLanguage ||
      document.documentElement.lang ||
      "zh-TW"
    );
  }
}

// Auto-initialize on DOM ready
document.addEventListener("DOMContentLoaded", () => {
  const container = document.getElementById("infographics-container");
  if (container) {
    window.infographicsGallery = new InfographicsGallery();
  }
});
