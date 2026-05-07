/**
 * 🌍 ResumeMate 多語言管理系統
 *
 * 進階多語言支援，包含動態載入、格式化、本地化及無障礙功能
 * 支援即時語言切換、文字插值、日期格式化、數字本地化等功能
 */

class MultilingualManager {
  /**
   * 初始化多語言管理器
   */
  constructor() {
    // 🌐 支援的語言配置
    this.supportedLanguages = [
      {
        code: "zh-TW",
        name: "中文(繁體)",
        nativeName: "中文",
        flag: "🇹🇼",
        direction: "ltr",
      },
      {
        code: "en",
        name: "English",
        nativeName: "English",
        flag: "🇺🇸",
        direction: "ltr",
      },
    ];

    // 🔧 配置選項
    this.config = {
      defaultLanguage: "zh-TW",
      fallbackLanguage: "en",
      storageKey: "preferred-language",
      autoDetect: true,
      cacheTimeout: 3600000, // 1 hour
      animationDuration: 300,
    };

    // 💾 內部狀態
    this.currentLanguage = this.config.defaultLanguage;
    this.languageData = new Map();
    this.loadingPromises = new Map();
    this.observers = [];
    this.isRTL = false;

    // 🚀 初始化
    this.init();
  }

  /**
   * 🎯 初始化多語言系統
   */
  async init() {
    // 偵測瀏覽器語言偏好
    if (this.config.autoDetect) {
      this.detectBrowserLanguage();
    }

    // 載入偏好語言設定
    this.loadStoredLanguage();

    // 預載入語言資料
    await this.preloadLanguages();

    // 設置DOM觀察器
    this.setupObservers();

    // 初始化無障礙功能
    this.setupAccessibility();

    // 綁定事件監聽器
    this.bindEventListeners();
  }

  /**
   * 🔍 偵測瀏覽器語言偏好
   */
  detectBrowserLanguage() {
    const browserLang = navigator.language || navigator.userLanguage;
    const supportedCodes = this.supportedLanguages.map((l) => l.code);

    // 完全匹配
    if (supportedCodes.includes(browserLang)) {
      this.currentLanguage = browserLang;
      return;
    }

    // 部分匹配（如 en-US -> en）
    const langCode = browserLang.split("-")[0];
    const partialMatch = supportedCodes.find((code) =>
      code.startsWith(langCode),
    );
    if (partialMatch) {
      this.currentLanguage = partialMatch;
    }
  }

  /**
   * 💾 載入儲存的語言偏好
   */
  loadStoredLanguage() {
    try {
      const stored = localStorage.getItem(this.config.storageKey);
      if (stored && this.isLanguageSupported(stored)) {
        this.currentLanguage = stored;
      }
    } catch (error) {
      console.warn("無法讀取語言偏好設定:", error);
    }
  }

  /**
   * 📥 預載入語言資料
   */
  async preloadLanguages() {
    const loadPromises = this.supportedLanguages.map((lang) =>
      this.loadLanguageData(lang.code),
    );

    try {
      await Promise.all(loadPromises);
    } catch (error) {
      console.error("語言資料載入失敗:", error);
    }
  }

  /**
   * 📄 載入特定語言的資料
   * @param {string} langCode - 語言代碼
   * @returns {Promise<Object>} 語言資料
   */
  async loadLanguageData(langCode) {
    // 檢查快取
    if (this.languageData.has(langCode)) {
      return this.languageData.get(langCode);
    }

    // 檢查是否正在載入
    if (this.loadingPromises.has(langCode)) {
      return this.loadingPromises.get(langCode);
    }

    // 開始載入
    const loadPromise = this.fetchLanguageData(langCode);
    this.loadingPromises.set(langCode, loadPromise);

    try {
      const data = await loadPromise;
      this.languageData.set(langCode, data);
      this.loadingPromises.delete(langCode);
      return data;
    } catch (error) {
      this.loadingPromises.delete(langCode);
      console.error(`載入語言資料失敗 (${langCode}):`, error);

      // 回退到預設語言
      if (langCode !== this.config.fallbackLanguage) {
        return this.loadLanguageData(this.config.fallbackLanguage);
      }
      throw error;
    }
  }

  /**
   * 🌐 從服務器獲取語言資料
   * @param {string} langCode - 語言代碼
   * @returns {Promise<Object>} 語言資料
   */
  async fetchLanguageData(langCode) {
    const url = `data/languages/${langCode}.json`;

    try {
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();

      // 驗證資料結構
      if (!this.validateLanguageData(data)) {
        throw new Error("語言資料格式無效");
      }

      return data;
    } catch (error) {
      console.error(`獲取語言資料失敗 (${langCode}):`, error);
      throw error;
    }
  }

  /**
   * ✅ 驗證語言資料結構
   * @param {Object} data - 語言資料
   * @returns {boolean} 是否有效
   */
  validateLanguageData(data) {
    return data && data.meta && data.meta.language && typeof data === "object";
  }

  /**
   * 🔄 切換語言
   * @param {string} langCode - 目標語言代碼
   * @param {Object} options - 選項
   * @returns {Promise<boolean>} 切換是否成功
   */
  async switchLanguage(langCode, options = {}) {
    const { animate = true, updateURL = false, skipStorage = false } = options;

    // 驗證語言代碼
    if (!this.isLanguageSupported(langCode)) {
      console.warn(`不支援的語言: ${langCode}`);
      return false;
    }

    // 避免重複切換
    if (langCode === this.currentLanguage) {
      return true;
    }

    try {
      // 顯示載入狀態
      this.showLoadingState(true);

      // 載入語言資料
      const langData = await this.loadLanguageData(langCode);

      const previousLang = this.currentLanguage;
      this.currentLanguage = langCode;

      // 更新文字方向
      this.updateTextDirection(langData.meta.direction || "ltr");

      // 更新DOM內容
      if (animate) {
        await this.animateLanguageTransition(() => {
          this.updateDOMContent(langData);
        });
      } else {
        this.updateDOMContent(langData);
      }

      // 更新HTML語言屬性
      document.documentElement.lang = langCode;

      // 儲存偏好設定
      if (!skipStorage) {
        this.saveLanguagePreference(langCode);
      }

      // 更新URL（可選）
      if (updateURL) {
        this.updateURLLanguage(langCode);
      }

      // 通知觀察者
      this.notifyObservers("languageChanged", {
        from: previousLang,
        to: langCode,
        data: langData,
      });

      // 無障礙通知
      this.announceLanguageChange(langData);
      return true;
    } catch (error) {
      console.error("語言切換失敗:", error);
      return false;
    } finally {
      this.showLoadingState(false);
    }
  }

  /**
   * 📝 更新DOM內容
   * @param {Object} langData - 語言資料
   */
  updateDOMContent(langData) {
    // 1. 更新導航元素
    this.updateNavigation(langData.navigation);

    // 2. 更新主要內容區塊
    this.updateHeroSection(langData.hero);
    this.updateAboutSection(langData.about);
    this.updateExperienceSection(langData.experience);
    this.updateSkillsSection(langData.skills);
    this.updatePortfolioSection(langData.portfolio);
    this.updateAIQASection(langData.ai_qa);
    this.updateFooter(langData.footer);

    // 3. 更新UI元素
    this.updateUIElements(langData.ui);

    // 4. 更新具備 data-zh 與 data-en 屬性的通用元素 (相容性支援)
    const elements = document.querySelectorAll("[data-zh][data-en]");
    elements.forEach((element) => {
      const text =
        this.currentLanguage === "zh-TW"
          ? element.getAttribute("data-zh")
          : element.getAttribute("data-en");

      if (text) {
        // 如果是 a 標籤且包含 icon，我們可能只想更新文字部分
        // 但大多數情況下直接覆寫即可，因為 icon 通常在 data-zh/en 中也有包含或不需要
        element.textContent = text;
      }
    });

    // 5. 更新無障礙標籤
    this.updateAriaLabels(langData.aria_labels);
  }

  /**
   * 🧭 更新導航區塊
   */
  updateNavigation(navData) {
    if (!navData) return;

    const updateElement = (selector, key) => {
      const element = document.querySelector(selector);
      if (element && navData[key]) {
        element.textContent = navData[key];
      }
    };

    updateElement('a[href="#about"]', "about");
    updateElement('a[href="#experience"]', "experience");
    updateElement('a[href="#skills"]', "skills");
    updateElement('a[href="#portfolio"]', "portfolio");
    updateElement('a[href="#chat"]', "ai_qa");
    updateElement("#lang-toggle", "language_toggle");

    if (navData.language_toggle) {
      document.querySelectorAll(".mobile-lang-toggle").forEach((button) => {
        button.textContent = navData.language_toggle;
      });
    }
  }

  /**
   * 🦸 更新英雄區塊
   */
  updateHeroSection(heroData) {
    if (!heroData) return;

    const selectors = {
      ".hero-greeting": "greeting",
      ".hero-title": "title",
      ".hero-description": "description",
      ".hero-cta-chat": "cta_chat",
      ".hero-cta-more": "cta_more",
    };

    Object.entries(selectors).forEach(([selector, key]) => {
      const element = document.querySelector(selector);
      if (element && heroData[key]) {
        element.textContent = heroData[key];
      }
    });
  }

  /**
   * 📖 更新關於我區塊
   */
  updateAboutSection(aboutData) {
    if (!aboutData) return;

    // 可以根據需要擴展更多內容更新
    const titleElement = document.querySelector("#about h2");
    if (titleElement && aboutData.title) {
      titleElement.textContent = aboutData.title;
    }
  }

  /**
   * 💼 更新經歷區塊
   */
  updateExperienceSection(expData) {
    if (!expData) return;

    const titleElement = document.querySelector("#experience h2");
    if (titleElement && expData.title) {
      titleElement.textContent = expData.title;
    }
  }

  /**
   * 🛠️ 更新技能區塊
   */
  updateSkillsSection(skillsData) {
    if (!skillsData) return;

    const titleElement = document.querySelector("#skills h2");
    if (titleElement && skillsData.title) {
      titleElement.textContent = skillsData.title;
    }
  }

  /**
   * 🎨 更新作品集區塊
   */
  updatePortfolioSection(portfolioData) {
    if (!portfolioData) return;

    const titleElement = document.querySelector("#portfolio h2");
    if (titleElement && portfolioData.title) {
      titleElement.textContent = portfolioData.title;
    }
  }

  /**
   * 🤖 更新AI問答區塊
   */
  updateAIQASection(qaData) {
    if (!qaData) return;

    const titleElement = document.querySelector("#chat h2");
    if (titleElement && qaData.title) {
      titleElement.textContent = qaData.title;
    }
  }

  /**
   * 🦶 更新頁腳
   */
  updateFooter(footerData) {
    if (!footerData) return;

    // 更新版權資訊等
    const copyrightElement = document.querySelector(".copyright");
    if (copyrightElement && footerData.copyright) {
      copyrightElement.textContent = footerData.copyright;
    }
  }

  /**
   * 🎮 更新UI元素
   */
  updateUIElements(uiData) {
    if (!uiData) return;

    // 更新常用UI文字
    document.querySelectorAll("[data-ui-key]").forEach((element) => {
      const key = element.getAttribute("data-ui-key");
      if (uiData[key]) {
        element.textContent = uiData[key];
      }
    });
  }

  /**
   * ♿ 更新無障礙標籤
   */
  updateAriaLabels(ariaData) {
    if (!ariaData) return;

    document.querySelectorAll("[data-aria-key]").forEach((element) => {
      const key = element.getAttribute("data-aria-key");
      if (ariaData[key]) {
        element.setAttribute("aria-label", ariaData[key]);
      }
    });
  }

  /**
   * 🎭 動畫語言轉換
   * @param {Function} updateCallback - 更新回調函數
   * @returns {Promise<void>}
   */
  async animateLanguageTransition(updateCallback) {
    const content = document.querySelector("main");
    if (!content) {
      updateCallback();
      return;
    }

    // 淡出效果
    content.style.transition = `opacity ${this.config.animationDuration}ms ease`;
    content.style.opacity = "0.7";

    // 等待動畫完成
    await new Promise((resolve) =>
      setTimeout(resolve, this.config.animationDuration / 2),
    );

    // 更新內容
    updateCallback();

    // 淡入效果
    content.style.opacity = "1";

    // 清理樣式
    setTimeout(() => {
      content.style.transition = "";
    }, this.config.animationDuration);
  }

  /**
   * 📐 更新文字方向
   * @param {string} direction - 文字方向 ('ltr' 或 'rtl')
   */
  updateTextDirection(direction) {
    this.isRTL = direction === "rtl";
    document.documentElement.dir = direction;
    document.body.classList.toggle("rtl", this.isRTL);
  }

  /**
   * 💾 儲存語言偏好
   * @param {string} langCode - 語言代碼
   */
  saveLanguagePreference(langCode) {
    try {
      localStorage.setItem(this.config.storageKey, langCode);
    } catch (error) {
      console.warn("無法儲存語言偏好:", error);
    }
  }

  /**
   * 🔗 更新URL語言參數
   * @param {string} langCode - 語言代碼
   */
  updateURLLanguage(langCode) {
    const url = new URL(window.location);
    url.searchParams.set("lang", langCode);
    window.history.replaceState({}, "", url);
  }

  /**
   * ⏳ 顯示載入狀態
   * @param {boolean} show - 是否顯示
   */
  showLoadingState(show) {
    const langToggle = document.getElementById("lang-toggle");
    if (langToggle) {
      if (show) {
        langToggle.classList.add("loading");
        langToggle.style.opacity = "0.6";
      } else {
        langToggle.classList.remove("loading");
        langToggle.style.opacity = "1";
      }
    }
  }

  /**
   * 📢 無障礙語言變更通知
   * @param {Object} langData - 語言資料
   */
  announceLanguageChange(langData) {
    const message =
      langData.notifications?.language_changed ||
      langData.ui?.language_switched ||
      "Language changed";

    // 建立即時通知區域
    let liveRegion = document.getElementById("language-live-region");
    if (!liveRegion) {
      liveRegion = document.createElement("div");
      liveRegion.id = "language-live-region";
      liveRegion.setAttribute("aria-live", "polite");
      liveRegion.className = "sr-only";
      document.body.appendChild(liveRegion);
    }

    liveRegion.textContent = message;
    setTimeout(() => (liveRegion.textContent = ""), 1000);
  }

  /**
   * 👂 設置DOM觀察器
   */
  setupObservers() {
    // 觀察新增的元素
    const observer = new MutationObserver((mutations) => {
      mutations.forEach((mutation) => {
        mutation.addedNodes.forEach((node) => {
          if (node.nodeType === Node.ELEMENT_NODE) {
            this.updateNewElements(node);
          }
        });
      });
    });

    observer.observe(document.body, {
      childList: true,
      subtree: true,
    });
  }

  /**
   * 🆕 更新新增的元素
   * @param {Element} element - 新增的元素
   */
  updateNewElements(element) {
    const currentData = this.languageData.get(this.currentLanguage);
    if (!currentData) return;

    // 更新新元素中的多語言屬性
    const multilingual = element.querySelectorAll(
      "[data-ui-key], [data-aria-key]",
    );
    multilingual.forEach((el) => {
      const uiKey = el.getAttribute("data-ui-key");
      const ariaKey = el.getAttribute("data-aria-key");

      if (uiKey && currentData.ui && currentData.ui[uiKey]) {
        el.textContent = currentData.ui[uiKey];
      }

      if (
        ariaKey &&
        currentData.aria_labels &&
        currentData.aria_labels[ariaKey]
      ) {
        el.setAttribute("aria-label", currentData.aria_labels[ariaKey]);
      }
    });
  }

  /**
   * ♿ 設置無障礙功能
   */
  setupAccessibility() {
    // 為語言切換按鈕添加無障礙屬性
    const langToggle = document.getElementById("lang-toggle");
    if (langToggle) {
      langToggle.setAttribute("role", "button");
      langToggle.setAttribute("tabindex", "0");

      // 鍵盤支援
      langToggle.addEventListener("keydown", (e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          this.toggleLanguage();
        }
      });
    }
  }

  /**
   * 🎯 綁定事件監聽器
   */
  bindEventListeners() {
    // 語言切換按鈕
    const langToggle = document.getElementById("lang-toggle");
    if (langToggle) {
      langToggle.addEventListener("click", () => {
        this.toggleLanguage();
      });
    }

    // 鍵盤快捷鍵 (Ctrl+Shift+L)
    document.addEventListener("keydown", (e) => {
      if (e.ctrlKey && e.shiftKey && e.key === "L") {
        e.preventDefault();
        this.toggleLanguage();
      }
    });
  }

  /**
   * 🔄 切換語言（在支援的語言間循環）
   */
  async toggleLanguage() {
    // 🛡️ 防止快速多次點擊造成衝突 (Debounce)
    const now = Date.now();
    if (this._lastToggleTime && now - this._lastToggleTime < 500) {
      console.warn("⏳ 切換頻率過快，已忽略");
      return;
    }
    this._lastToggleTime = now;

    const currentIndex = this.supportedLanguages.findIndex(
      (lang) => lang.code === this.currentLanguage,
    );

    const nextIndex = (currentIndex + 1) % this.supportedLanguages.length;
    const nextLanguage = this.supportedLanguages[nextIndex].code;

    await this.switchLanguage(nextLanguage);
  }

  /**
   * ✅ 檢查語言是否受支援
   * @param {string} langCode - 語言代碼
   * @returns {boolean} 是否支援
   */
  isLanguageSupported(langCode) {
    return this.supportedLanguages.some((lang) => lang.code === langCode);
  }

  /**
   * 📊 取得當前語言資訊
   * @returns {Object} 語言資訊
   */
  getCurrentLanguageInfo() {
    return (
      this.supportedLanguages.find(
        (lang) => lang.code === this.currentLanguage,
      ) || this.supportedLanguages[0]
    );
  }

  /**
   * 📝 文字插值
   * @param {string} template - 樣板文字
   * @param {Object} values - 插值對象
   * @returns {string} 插值後的文字
   */
  interpolate(template, values) {
    return template.replace(/\{(\w+)\}/g, (match, key) => {
      return values[key] !== undefined ? values[key] : match;
    });
  }

  /**
   * 👥 註冊觀察者
   * @param {Function} callback - 回調函數
   */
  addObserver(callback) {
    this.observers.push(callback);
  }

  /**
   * 🚫 移除觀察者
   * @param {Function} callback - 回調函數
   */
  removeObserver(callback) {
    const index = this.observers.indexOf(callback);
    if (index > -1) {
      this.observers.splice(index, 1);
    }
  }

  /**
   * 📢 通知觀察者
   * @param {string} event - 事件名稱
   * @param {any} data - 事件資料
   */
  notifyObservers(event, data) {
    this.observers.forEach((callback) => {
      try {
        callback(event, data);
      } catch (error) {
        console.error("觀察者回調錯誤:", error);
      }
    });
  }

  /**
   * 🧹 清理資源
   */
  destroy() {
    this.languageData.clear();
    this.loadingPromises.clear();
    this.observers = [];
  }
}

// 🌍 創建全域實例
window.multilingualManager = new MultilingualManager();

// 📤 導出供其他模組使用
if (typeof module !== "undefined" && module.exports) {
  module.exports = MultilingualManager;
}
