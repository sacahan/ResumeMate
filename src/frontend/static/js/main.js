/**
 * ResumeMate 前端主要 JavaScript 功能
 * 此類負責初始化頁面互動、語言切換、動畫效果、聊天範例、通知提示等功能。
 * 整合響應式增強功能，提供現代化的互動體驗與效能優化。
 */

class ResumeMateFrontend {
  /**
   * 建構函式，初始化預設語言並執行初始化流程。
   */
  constructor() {
    this.currentLang = "zh-TW";
    this.interactionTimings = [];
    this.scrollPosition = 0;
    this.isReducedMotion = window.matchMedia(
      "(prefers-reduced-motion: reduce)",
    ).matches;
    this.touchStartY = 0;
    this.touchStartTime = 0;
    this.init();
  }

  /**
   * 初始化所有前端互動功能，包括語言切換、平滑滾動、聊天範例、動畫效果。
   */
  init() {
    this.setupSmoothScrolling();
    this.setupChatExamples();
    this.setupAnimations();
    this.setupAdvancedInteractions();
    this.setupPerformanceMonitoring();
    this.setupAccessibilityFeatures();
    this.setupProgressiveEnhancement();
    this.integrateMultilingualManager();
    this.setupLanguageMenuToggle();
  }

  /**
   * 設定導覽連結的平滑滾動效果，點擊錨點連結時會平滑移動到指定區塊。
   */
  setupSmoothScrolling() {
    // 導航連結的平滑滾動
    const navLinks = document.querySelectorAll('a[href^="#"]');

    navLinks.forEach((link) => {
      link.addEventListener("click", (e) => {
        e.preventDefault();

        const targetId = link.getAttribute("href").substring(1);
        const targetElement = document.getElementById(targetId);

        if (targetElement) {
          const offsetTop = targetElement.offsetTop - 80; // 考慮固定導航欄高度

          window.scrollTo({
            top: offsetTop,
            behavior: "smooth",
          });
        }
      });
    });
  }

  /**
   * 設定聊天範例按鈕的事件監聽器，點擊後將範例問題送到聊天介面。
   */
  setupChatExamples() {
    const exampleButtons = document.querySelectorAll(".chat-example");

    exampleButtons.forEach((button) => {
      button.addEventListener("click", () => {
        const question = button.textContent.trim();
        this.sendQuestionToChat(question);
      });
    });
  }

  /**
   * 發送問題到聊天介面，並顯示提示通知。
   * @param {string} question - 要發送的問題
   */
  sendQuestionToChat(question) {
    // 這裡可以實作與 Gradio iframe 的通訊
    // 由於 iframe 的跨域限制，這可能需要 postMessage API 或其他方法

    // 滾動到聊天區域
    const chatSection = document.getElementById("chat");
    if (chatSection) {
      chatSection.scrollIntoView({ behavior: "smooth" });
    }

    // 顯示提示訊息
    this.showNotification(`問題範例: "${question}"`, "info");
  }

  /**
   * 設定淡入動畫效果，當元素進入視窗時觸發動畫。
   */
  setupAnimations() {
    // 淡入動畫
    const animatedElements = document.querySelectorAll(".animate-fade-in-up");

    const observerOptions = {
      threshold: 0.1,
      rootMargin: "0px 0px -50px 0px",
    };

    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          if (this.isReducedMotion) {
            entry.target.style.opacity = "1";
            entry.target.style.transform = "none";
          } else {
            entry.target.style.opacity = "1";
            entry.target.style.transform = "translateY(0)";
            entry.target.classList.add("animation-complete");
          }
        }
      });
    }, observerOptions);

    animatedElements.forEach((element) => {
      if (!this.isReducedMotion) {
        element.style.opacity = "0";
        element.style.transform = "translateY(30px)";
        element.style.transition =
          "opacity 0.6s cubic-bezier(0.4, 0, 0.2, 1), transform 0.6s cubic-bezier(0.4, 0, 0.2, 1)";
      }
      observer.observe(element);
    });

    // 🎨 進階動畫效果
    this.setupStaggeredAnimations();
    this.setupParallaxEffects();
    this.setupHoverAnimations();
  }

  /**
   * 顯示通知訊息於畫面右上角，並自動消失。
   * @param {string} message - 訊息內容
   * @param {string} type - 訊息類型 (success, error, info, warning)
   */
  showNotification(message, type = "info") {
    // 創建通知元素
    const notification = document.createElement("div");
    notification.className = `fixed top-20 right-4 z-50 px-6 py-3 rounded-lg shadow-lg transform transition-all duration-300 translate-x-full`;

    // 根據類型設定樣式
    const typeStyles = {
      success: "bg-green-600 text-white",
      error: "bg-red-600 text-white",
      warning: "bg-yellow-600 text-white",
      info: "bg-blue-600 text-white",
    };

    notification.className += ` ${typeStyles[type] || typeStyles.info}`;
    notification.textContent = message;

    // 添加到頁面
    document.body.appendChild(notification);

    // 顯示動畫
    setTimeout(() => {
      notification.classList.remove("translate-x-full");
    }, 100);

    // 自動移除
    setTimeout(() => {
      notification.classList.add("translate-x-full");
      setTimeout(() => {
        if (notification.parentNode) {
          notification.parentNode.removeChild(notification);
        }
      }, 300);
    }, 3000);
  }

  /**
   * 🎯 設定進階互動功能，包括觸控手勢、鍵盤導航、智慧滾動。
   */
  setupAdvancedInteractions() {
    // 觸控手勢支援
    this.setupTouchGestures();

    // 智慧滾動增強
    this.setupSmartScrolling();

    // 鍵盤導航
    this.setupKeyboardNavigation();

    // 動態主題切換效果
    this.setupThemeTransitions();

    // 進度指示器
    this.setupScrollProgress();
  }

  /**
   * 🎨 設定交錯動畫效果
   */
  setupStaggeredAnimations() {
    const staggerGroups = document.querySelectorAll("[data-stagger]");

    staggerGroups.forEach((group) => {
      const children = group.children;
      const delay = parseInt(group.dataset.stagger) || 100;

      Array.from(children).forEach((child, index) => {
        if (!this.isReducedMotion) {
          child.style.animationDelay = `${index * delay}ms`;
          child.classList.add("animate-fade-in-up");
        }
      });
    });
  }

  /**
   * 🌊 設定視差滾動效果
   */
  setupParallaxEffects() {
    if (this.isReducedMotion) return;

    const parallaxElements = document.querySelectorAll("[data-parallax]");

    const updateParallax = () => {
      const scrolled = window.pageYOffset;

      parallaxElements.forEach((element) => {
        const rate = scrolled * (parseFloat(element.dataset.parallax) || 0.5);
        element.style.transform = `translateY(${rate}px)`;
      });
    };

    // 使用 requestAnimationFrame 優化效能
    let ticking = false;
    window.addEventListener(
      "scroll",
      () => {
        if (!ticking) {
          requestAnimationFrame(() => {
            updateParallax();
            ticking = false;
          });
          ticking = true;
        }
      },
      { passive: true },
    );
  }

  /**
   * ✨ 設定懸停動畫效果
   */
  setupHoverAnimations() {
    // 卡片懸停效果
    const cards = document.querySelectorAll(
      ".card, .project-card, .skill-card",
    );

    cards.forEach((card) => {
      card.addEventListener("mouseenter", (e) => {
        if (!this.isReducedMotion) {
          e.target.style.transform = "translateY(-8px) scale(1.02)";
          e.target.style.boxShadow = "0 20px 40px rgba(0,0,0,0.2)";
        }
      });

      card.addEventListener("mouseleave", (e) => {
        e.target.style.transform = "";
        e.target.style.boxShadow = "";
      });
    });

    // 按鈕波紋效果
    this.setupRippleEffect();
  }

  /**
   * 🌊 設定按鈕波紋效果
   */
  setupRippleEffect() {
    const buttons = document.querySelectorAll("button, .btn, .chat-example");

    buttons.forEach((button) => {
      button.addEventListener("click", (e) => {
        if (this.isReducedMotion) return;

        // 排除語言切換按鈕，避免事件干擾
        if (button.id === "lang-toggle") return;

        const rect = button.getBoundingClientRect();
        const size = Math.max(rect.width, rect.height);
        const x = e.clientX - rect.left - size / 2;
        const y = e.clientY - rect.top - size / 2;

        const ripple = document.createElement("span");
        ripple.style.cssText = `
          position: absolute;
          width: ${size}px;
          height: ${size}px;
          left: ${x}px;
          top: ${y}px;
          background: rgba(255,255,255,0.3);
          border-radius: 50%;
          transform: scale(0);
          animation: ripple 0.6s linear;
          pointer-events: none;
        `;

        button.style.position = "relative";
        button.style.overflow = "hidden";
        button.appendChild(ripple);

        setTimeout(() => ripple.remove(), 600);
      });
    });
  }

  /**
   * 📱 設定觸控手勢支援
   */
  setupTouchGestures() {
    // 滑動手勢導航
    document.addEventListener(
      "touchstart",
      (e) => {
        this.touchStartY = e.touches[0].clientY;
        this.touchStartTime = Date.now();
      },
      { passive: true },
    );

    document.addEventListener(
      "touchend",
      (e) => {
        const touchEndY = e.changedTouches[0].clientY;
        const touchTime = Date.now() - this.touchStartTime;
        const distance = Math.abs(touchEndY - this.touchStartY);

        // 快速滑動檢測
        if (touchTime < 300 && distance > 50) {
          const direction = touchEndY > this.touchStartY ? "down" : "up";
          this.handleSwipeGesture(direction);
        }
      },
      { passive: true },
    );
  }

  /**
   * 👆 處理滑動手勢
   */
  handleSwipeGesture(direction) {
    const sections = document.querySelectorAll("section[id]");
    const currentSection = this.getCurrentSection();
    const currentIndex = Array.from(sections).findIndex(
      (s) => s === currentSection,
    );

    if (direction === "up" && currentIndex < sections.length - 1) {
      sections[currentIndex + 1].scrollIntoView({ behavior: "smooth" });
    } else if (direction === "down" && currentIndex > 0) {
      sections[currentIndex - 1].scrollIntoView({ behavior: "smooth" });
    }
  }

  /**
   * 📍 獲取目前可見的區塊
   */
  getCurrentSection() {
    const sections = document.querySelectorAll("section[id]");
    const scrollPosition = window.scrollY + 100;

    for (const section of sections) {
      if (
        scrollPosition >= section.offsetTop &&
        scrollPosition < section.offsetTop + section.offsetHeight
      ) {
        return section;
      }
    }
    return sections[0];
  }

  /**
   * 🧠 設定智慧滾動功能
   */
  setupSmartScrolling() {
    let lastScrollY = window.scrollY;
    let scrollDirection = "down";

    window.addEventListener(
      "scroll",
      () => {
        const currentScrollY = window.scrollY;
        scrollDirection = currentScrollY > lastScrollY ? "down" : "up";
        lastScrollY = currentScrollY;

        // 更新導航欄狀態
        const navbar = document.querySelector("nav");
        if (navbar) {
          if (scrollDirection === "down" && currentScrollY > 100) {
            navbar.classList.add("navbar-hidden");
          } else {
            navbar.classList.remove("navbar-hidden");
          }
        }

        // 更新滾動進度
        this.updateScrollProgress();
      },
      { passive: true },
    );
  }

  /**
   * 📊 設定滾動進度指示器
   */
  setupScrollProgress() {
    const progressBar = document.createElement("div");
    progressBar.className =
      "fixed top-0 left-0 h-1 bg-gradient-to-r from-blue-500 to-purple-500 z-50 transition-all duration-300";
    progressBar.id = "scroll-progress";
    document.body.appendChild(progressBar);
  }

  /**
   * 📈 更新滾動進度
   */
  updateScrollProgress() {
    const progressBar = document.getElementById("scroll-progress");
    if (progressBar) {
      const scrollHeight =
        document.documentElement.scrollHeight - window.innerHeight;
      const scrolled = (window.scrollY / scrollHeight) * 100;
      progressBar.style.width = `${Math.min(scrolled, 100)}%`;
    }
  }

  /**
   * ⌨️ 設定鍵盤導航
   */
  setupKeyboardNavigation() {
    document.addEventListener("keydown", (e) => {
      // Alt + 數字鍵快速導航到區塊
      if (e.altKey && e.key >= "1" && e.key <= "9") {
        e.preventDefault();
        const sectionIndex = parseInt(e.key) - 1;
        const sections = document.querySelectorAll("section[id]");
        if (sections[sectionIndex]) {
          sections[sectionIndex].scrollIntoView({ behavior: "smooth" });
        }
      }

      // Esc 鍵關閉模態框或通知
      if (e.key === "Escape") {
        this.closeActiveModals();
      }
    });
  }

  /**
   * ❌ 關閉活躍的模態框
   */
  closeActiveModals() {
    const notifications = document.querySelectorAll(".notification");
    notifications.forEach((notification) => {
      notification.classList.add("translate-x-full");
      setTimeout(() => notification.remove(), 300);
    });
  }

  /**
   * 🎨 設定主題轉換效果
   */
  setupThemeTransitions() {
    // 為主題切換添加平滑過渡
    document.documentElement.style.transition =
      "background-color 0.3s ease, color 0.3s ease";
  }

  /**
   * 📊 設定效能監控
   */
  setupPerformanceMonitoring() {
    // 監控互動延遲
    ["click", "touchstart", "keydown"].forEach((eventType) => {
      document.addEventListener(
        eventType,
        (e) => {
          const startTime = performance.now();

          requestAnimationFrame(() => {
            const endTime = performance.now();
            const latency = endTime - startTime;

            this.interactionTimings.push({
              type: eventType,
              latency,
              timestamp: Date.now(),
            });

            // 保留最近 100 次記錄
            if (this.interactionTimings.length > 100) {
              this.interactionTimings.shift();
            }
          });
        },
        { passive: true },
      );
    });

    // 記錄頁面載入效能
    window.addEventListener("load", () => {
      const perfData = performance.getEntriesByType("navigation")[0];
      void perfData;
    });
  }

  /**
   * ♿ 設定無障礙功能
   */
  setupAccessibilityFeatures() {
    // 焦點陷阱管理
    this.setupFocusTrap();

    // 鍵盤導航指示器
    this.setupKeyboardIndicators();

    // 螢幕閱讀器支援
    this.setupScreenReaderSupport();
  }

  /**
   * 🔒 設定焦點陷阱
   */
  setupFocusTrap() {
    const focusableElements =
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])';

    document.addEventListener("keydown", (e) => {
      if (e.key === "Tab") {
        const focusable = Array.from(
          document.querySelectorAll(focusableElements),
        );
        const firstFocusable = focusable[0];
        const lastFocusable = focusable[focusable.length - 1];

        if (e.shiftKey) {
          if (document.activeElement === firstFocusable) {
            lastFocusable.focus();
            e.preventDefault();
          }
        } else {
          if (document.activeElement === lastFocusable) {
            firstFocusable.focus();
            e.preventDefault();
          }
        }
      }
    });
  }

  /**
   * ⌨️ 設定鍵盤指示器
   */
  setupKeyboardIndicators() {
    document.addEventListener("keydown", () => {
      document.body.classList.add("keyboard-navigation");
    });

    document.addEventListener("mousedown", () => {
      document.body.classList.remove("keyboard-navigation");
    });
  }

  /**
   * 🗣️ 設定螢幕閱讀器支援
   */
  setupScreenReaderSupport() {
    // 為動態內容添加 aria-live 區域
    const liveRegion = document.createElement("div");
    liveRegion.setAttribute("aria-live", "polite");
    liveRegion.setAttribute("aria-atomic", "true");
    liveRegion.className = "sr-only";
    liveRegion.id = "live-region";
    document.body.appendChild(liveRegion);
  }

  /**
   * 📢 向螢幕閱讀器宣告訊息
   */
  announceToScreenReader(message) {
    const liveRegion = document.getElementById("live-region");
    if (liveRegion) {
      liveRegion.textContent = message;
      setTimeout(() => (liveRegion.textContent = ""), 1000);
    }
  }

  /**
   * 🔄 設定漸進式增強
   */
  setupProgressiveEnhancement() {
    // 檢測瀏覽器功能並逐步啟用增強功能
    const features = {
      intersectionObserver: "IntersectionObserver" in window,
      webAnimations: "animate" in HTMLElement.prototype,
      customProperties: CSS.supports("--test", "value"),
      gridLayout: CSS.supports("display", "grid"),
    };

    // 根據支援情況啟用功能
    Object.entries(features).forEach(([feature, supported]) => {
      if (supported) {
        document.documentElement.classList.add(`supports-${feature}`);
      } else {
        console.warn(`⚠️ ${feature} 不支援，使用降級方案`);
      }
    });
  }

  /**
   * 🌍 整合進階多語言管理系統
   */
  integrateMultilingualManager() {
    // 等待多語言管理器載入
    if (window.multilingualManager) {
      // 註冊語言變更觀察者
      window.multilingualManager.addObserver((event, data) => {
        if (event === "languageChanged") {
          // 同步更新當前語言狀態
          this.currentLang = data.to;

          // 通知其他組件語言已變更
          this.notifyLanguageChange(data);

          // 更新語言相關的UI狀態
          this.updateLanguageDependentUI(data.to);
        }
      });

      // 整合現有的語言切換功能
      this.enhanceLanguageToggle();
    } else {
      // 如果多語言管理器還未載入，延遲整合
      setTimeout(() => this.integrateMultilingualManager(), 100);
    }
  }

  /**
   * 🔧 增強語言切換功能
   */
  enhanceLanguageToggle() {
    const langToggle = document.getElementById("lang-toggle");
    if (langToggle && window.multilingualManager) {
      // 語言切換事件已由 MultilingualManager 處理
      // 這裡僅添加視覺增強（如工具提示）

      // 添加視覺反饋
      langToggle.addEventListener("mouseenter", () => {
        const currentInfo = window.multilingualManager.getCurrentLanguageInfo();
        const tooltip = this.createLanguageTooltip(currentInfo);
        this.showTooltip(langToggle, tooltip);
      });

      langToggle.addEventListener("mouseleave", () => {
        this.hideTooltip();
      });
    }
  }

  /**
   * 🤝 讓手機選單可以觸發語言切換
   */
  setupLanguageMenuToggle() {
    const desktopLangToggle = document.getElementById("lang-toggle");
    const mobileLangToggle = document.querySelector(".mobile-lang-toggle");
    if (!desktopLangToggle || !mobileLangToggle) {
      return;
    }

    mobileLangToggle.addEventListener("click", () => {
      desktopLangToggle.click();
    });
  }

  /**
   * 💬 建立語言切換提示框
   * @param {Object} langInfo - 語言資訊
   * @returns {string} 提示框內容
   */
  createLanguageTooltip(langInfo) {
    const shortcut = "Ctrl+Shift+L";
    return `${langInfo.flag} ${langInfo.nativeName}\n快捷鍵: ${shortcut}`;
  }

  /**
   * 💭 顯示提示框
   * @param {Element} element - 目標元素
   * @param {string} content - 提示內容
   */
  showTooltip(element, content) {
    // 移除現有提示框
    this.hideTooltip();

    const tooltip = document.createElement("div");
    tooltip.className =
      "language-tooltip fixed z-50 px-3 py-2 text-sm bg-gray-800 text-white rounded-lg shadow-lg transform -translate-x-1/2";
    tooltip.textContent = content;
    tooltip.id = "language-tooltip";

    const rect = element.getBoundingClientRect();
    tooltip.style.left = `${rect.left + rect.width / 2}px`;
    tooltip.style.top = `${rect.bottom + 8}px`;

    document.body.appendChild(tooltip);

    // 淡入動畫
    setTimeout(() => {
      tooltip.style.opacity = "1";
      tooltip.style.transform = "translateX(-50%) translateY(0)";
    }, 10);
  }

  /**
   * 🫥 隱藏提示框
   */
  hideTooltip() {
    const existingTooltip = document.getElementById("language-tooltip");
    if (existingTooltip) {
      existingTooltip.remove();
    }
  }

  /**
   * 📢 通知語言變更
   * @param {Object} data - 語言變更資料
   */
  notifyLanguageChange(data) {
    // 使用現有的通知系統
    const message =
      data.to === "zh-TW" ? "語言已切換至中文" : "Language switched to English";
    this.showNotification(message, "info");

    // 向螢幕閱讀器宣告
    this.announceToScreenReader(message);
  }

  /**
   * 🎨 更新語言相關的UI狀態
   * @param {string} langCode - 語言代碼
   */
  updateLanguageDependentUI(langCode) {
    // 更新數字和日期格式化
    this.updateNumberFormatting(langCode);

    // 更新文字方向相關的樣式
    this.updateDirectionalStyles(langCode);

    // 更新字體偏好
    this.updateFontPreferences(langCode);
  }

  /**
   * 🔢 更新數字格式化
   * @param {string} langCode - 語言代碼
   */
  updateNumberFormatting(langCode) {
    const locale = langCode === "zh-TW" ? "zh-TW" : "en-US";

    // 更新頁面中的數字顯示
    document.querySelectorAll("[data-number]").forEach((element) => {
      const number = parseFloat(element.dataset.number);
      if (!isNaN(number)) {
        element.textContent = new Intl.NumberFormat(locale).format(number);
      }
    });

    // 更新日期顯示
    document.querySelectorAll("[data-date]").forEach((element) => {
      const dateString = element.dataset.date;
      const date = new Date(dateString);
      if (date.isValid && date.isValid()) {
        element.textContent = new Intl.DateTimeFormat(locale).format(date);
      }
    });
  }

  /**
   * ➡️ 更新方向性樣式
   * @param {string} langCode - 語言代碼
   */
  updateDirectionalStyles(langCode) {
    const isRTL = langCode === "ar" || langCode === "he"; // 未來擴展RTL語言
    document.body.classList.toggle("rtl-layout", isRTL);
  }

  /**
   * 🅰️ 更新字體偏好
   * @param {string} langCode - 語言代碼
   */
  updateFontPreferences(langCode) {
    const fontClass = langCode === "zh-TW" ? "font-chinese" : "font-english";
    document.body.className = document.body.className.replace(/font-\w+/g, "");
    document.body.classList.add(fontClass);
  }
}

// 當 DOM 內容載入完成後，初始化 ResumeMateFrontend 並執行相關檢查。
document.addEventListener("DOMContentLoaded", () => {
  const app = new ResumeMateFrontend();

  // 檢查聊天服務狀態 (可選)
  // app.updateChatStatus();
});
