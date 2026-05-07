/**
 * ResumeMate 響應式增強 JavaScript 🚀
 *
 * 提供進階響應式功能，包括響應式圖片載入、
 * 手勢支援、性能監控和設備適配等
 */

class ResponsiveEnhancer {
  /**
   * 初始化響應式增強器
   */
  constructor() {
    this.breakpoints = {
      xs: 0,
      sm: 640,
      md: 768,
      lg: 1024,
      xl: 1280,
      "2xl": 1536,
    };

    this.currentBreakpoint = this.getCurrentBreakpoint();
    this.isTouch = this.detectTouch();
    this.reducedMotion = this.detectReducedMotion();
    this.connectionSpeed = this.detectConnection();

    // 性能監控
    this.performanceMetrics = {
      loadTime: 0,
      interactionLatency: [],
      imageLoadTimes: [],
    };

    this.init();
  }

  /**
   * 初始化所有響應式功能
   */
  init() {
    this.setupResizeListener();
    this.setupImageLazyLoading();
    this.setupTouchGestures();
    this.setupPerformanceMonitoring();
    this.setupAccessibilityFeatures();
    this.setupMobileOptimizations();
    this.setupAdaptiveFeatures();

    // DOM 載入完成後執行
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", () => {
        this.onDOMReady();
      });
    } else {
      this.onDOMReady();
    }
  }

  /**
   * DOM 準備就緒後執行的功能
   */
  onDOMReady() {
    this.optimizeInitialLoad();
    this.setupDeviceSpecificFeatures();
    this.preloadCriticalResources();
    this.measureLoadPerformance();
  }

  // ===========================================
  // 📱 斷點檢測和響應
  // ===========================================

  /**
   * 獲取當前斷點
   */
  getCurrentBreakpoint() {
    const width = window.innerWidth;

    if (width >= this.breakpoints["2xl"]) return "2xl";
    if (width >= this.breakpoints.xl) return "xl";
    if (width >= this.breakpoints.lg) return "lg";
    if (width >= this.breakpoints.md) return "md";
    if (width >= this.breakpoints.sm) return "sm";
    return "xs";
  }

  /**
   * 設置視窗大小改變監聽器
   */
  setupResizeListener() {
    let resizeTimer;

    window.addEventListener("resize", () => {
      // 防抖處理，避免過度觸發
      clearTimeout(resizeTimer);
      resizeTimer = setTimeout(() => {
        const newBreakpoint = this.getCurrentBreakpoint();

        if (newBreakpoint !== this.currentBreakpoint) {
          this.onBreakpointChange(this.currentBreakpoint, newBreakpoint);
          this.currentBreakpoint = newBreakpoint;
        }

        this.onResize();
      }, 250);
    });
  }

  /**
   * 斷點改變時的處理
   */
  onBreakpointChange(oldBreakpoint, newBreakpoint) {
    // 更新 CSS 自定義屬性
    document.documentElement.style.setProperty(
      "--current-breakpoint",
      newBreakpoint,
    );

    // 觸發自定義事件
    window.dispatchEvent(
      new CustomEvent("breakpointChange", {
        detail: { oldBreakpoint, newBreakpoint },
      }),
    );

    // 執行斷點特定的優化
    this.optimizeForBreakpoint(newBreakpoint);
  }

  /**
   * 視窗大小改變時的處理
   */
  onResize() {
    // 更新視窗高度 CSS 變數（解決移動端視窗高度問題）
    document.documentElement.style.setProperty(
      "--vh",
      `${window.innerHeight * 0.01}px`,
    );

    // 重新計算佈局相關元素
    this.recalculateLayout();
  }

  // ===========================================
  // 🖼️ 圖片懶載入和優化
  // ===========================================

  /**
   * 設置圖片懶載入
   */
  setupImageLazyLoading() {
    // 使用 Intersection Observer 實現懶載入
    if ("IntersectionObserver" in window) {
      this.imageObserver = new IntersectionObserver(
        (entries) => {
          entries.forEach((entry) => {
            if (entry.isIntersecting) {
              this.loadImage(entry.target);
              this.imageObserver.unobserve(entry.target);
            }
          });
        },
        {
          rootMargin: "50px 0px",
          threshold: 0.1,
        },
      );

      // 觀察所有懶載入圖片
      document.querySelectorAll('img[loading="lazy"]').forEach((img) => {
        this.imageObserver.observe(img);
      });
    }
  }

  /**
   * 載入圖片
   */
  loadImage(img) {
    const startTime = performance.now();

    img.addEventListener("load", () => {
      img.classList.add("loaded");

      // 記錄載入時間
      const loadTime = performance.now() - startTime;
      this.performanceMetrics.imageLoadTimes.push(loadTime);
    });

    img.addEventListener("error", () => {
      console.error(`❌ Image failed to load: ${img.src}`);
      // 可以設置備用圖片
      img.src = "/static/images/placeholder.jpg";
    });

    // 根據連接速度調整圖片品質
    if (img.dataset.src) {
      img.src = this.optimizeImageUrl(img.dataset.src);
    }
  }

  /**
   * 根據網路狀況優化圖片 URL
   */
  optimizeImageUrl(originalUrl) {
    if (this.connectionSpeed === "slow") {
      // 慢速連接時載入低品質版本
      return originalUrl.replace(/\.(jpg|jpeg|png)$/i, "_low.$1");
    } else if (
      this.currentBreakpoint === "xs" ||
      this.currentBreakpoint === "sm"
    ) {
      // 小螢幕載入較小尺寸
      return originalUrl.replace(/\.(jpg|jpeg|png)$/i, "_mobile.$1");
    }
    return originalUrl;
  }

  // ===========================================
  // 👆 觸控和手勢支援
  // ===========================================

  /**
   * 檢測觸控能力
   */
  detectTouch() {
    return "ontouchstart" in window || navigator.maxTouchPoints > 0;
  }

  /**
   * 設置觸控手勢
   */
  setupTouchGestures() {
    if (!this.isTouch) return;

    let touchStartX = 0;
    let touchStartY = 0;

    document.addEventListener(
      "touchstart",
      (e) => {
        touchStartX = e.touches[0].clientX;
        touchStartY = e.touches[0].clientY;
      },
      { passive: true },
    );

    document.addEventListener(
      "touchmove",
      (e) => {
        if (!touchStartX || !touchStartY) return;

        const touchEndX = e.touches[0].clientX;
        const touchEndY = e.touches[0].clientY;
        const diffX = touchStartX - touchEndX;
        const diffY = touchStartY - touchEndY;

        // 水平滑動檢測
        if (Math.abs(diffX) > Math.abs(diffY) && Math.abs(diffX) > 50) {
          if (diffX > 0) {
            // 向左滑動
            this.onSwipeLeft();
          } else {
            // 向右滑動
            this.onSwipeRight();
          }
        }
      },
      { passive: true },
    );

    document.addEventListener(
      "touchend",
      () => {
        touchStartX = 0;
        touchStartY = 0;
      },
      { passive: true },
    );
  }

  /**
   * 左滑處理
   */
  onSwipeLeft() {
    // 可以用來切換到下一個區段或關閉側邊選單
    window.dispatchEvent(new CustomEvent("swipeLeft"));
  }

  /**
   * 右滑處理
   */
  onSwipeRight() {
    // 可以用來返回上一個區段或開啟側邊選單
    window.dispatchEvent(new CustomEvent("swipeRight"));
  }

  // ===========================================
  // ⚡ 性能監控和優化
  // ===========================================

  /**
   * 設置性能監控
   */
  setupPerformanceMonitoring() {
    // 監控首次內容繪製
    if ("PerformanceObserver" in window) {
      const observer = new PerformanceObserver((list) => {
        list.getEntries().forEach((entry) => {
          if (entry.name === "first-contentful-paint") {
            void entry;
          }
        });
      });

      observer.observe({ entryTypes: ["paint"] });
    }

    // 監控互動延遲
    ["click", "touchstart", "keydown"].forEach((eventType) => {
      document.addEventListener(
        eventType,
        (e) => {
          const startTime = performance.now();

          requestAnimationFrame(() => {
            const latency = performance.now() - startTime;
            this.performanceMetrics.interactionLatency.push(latency);

            if (latency > 100) {
              console.warn(
                `⚠️ High interaction latency: ${latency.toFixed(2)}ms`,
              );
            }
          });
        },
        { passive: true },
      );
    });
  }

  /**
   * 測量載入性能
   */
  measureLoadPerformance() {
    window.addEventListener("load", () => {
      const loadTime = performance.now();
      this.performanceMetrics.loadTime = loadTime;

      // 如果載入時間過長，啟用性能模式
      if (loadTime > 3000) {
        this.enablePerformanceMode();
      }
    });
  }

  /**
   * 啟用性能模式
   */
  enablePerformanceMode() {
    document.body.classList.add("performance-mode");

    // 減少動畫和過場效果
    document.documentElement.style.setProperty("--transition-fast", "0.1s");
    document.documentElement.style.setProperty("--transition-normal", "0.15s");
    document.documentElement.style.setProperty("--transition-slow", "0.2s");
  }

  // ===========================================
  // ♿ 無障礙功能
  // ===========================================

  /**
   * 檢測是否偏好減少動畫
   */
  detectReducedMotion() {
    return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  }

  /**
   * 設置無障礙功能
   */
  setupAccessibilityFeatures() {
    // 監聽減少動畫偏好變化
    const motionQuery = window.matchMedia("(prefers-reduced-motion: reduce)");
    motionQuery.addListener((e) => {
      this.reducedMotion = e.matches;
      this.updateMotionPreferences();
    });

    // 鍵盤導航支援
    this.setupKeyboardNavigation();

    // 焦點管理
    this.setupFocusManagement();
  }

  /**
   * 更新動畫偏好設定
   */
  updateMotionPreferences() {
    if (this.reducedMotion) {
      document.body.classList.add("reduce-motion");
    } else {
      document.body.classList.remove("reduce-motion");
    }
  }

  /**
   * 設置鍵盤導航
   */
  setupKeyboardNavigation() {
    document.addEventListener("keydown", (e) => {
      // Escape 鍵關閉模態框或選單
      if (e.key === "Escape") {
        this.closeAllModals();
      }

      // Tab 鍵導航優化
      if (e.key === "Tab") {
        document.body.classList.add("keyboard-navigation");
      }
    });

    // 滑鼠點擊時移除鍵盤導航樣式
    document.addEventListener("mousedown", () => {
      document.body.classList.remove("keyboard-navigation");
    });
  }

  /**
   * 設置焦點管理
   */
  setupFocusManagement() {
    // 確保互動元素都有適當的 tabindex
    const interactiveElements = document.querySelectorAll(
      "a, button, input, textarea, select, [tabindex]",
    );

    interactiveElements.forEach((element) => {
      if (!element.hasAttribute("tabindex") && element.tabIndex === -1) {
        element.tabIndex = 0;
      }
    });
  }

  // ===========================================
  // 📱 行動裝置優化
  // ===========================================

  /**
   * 設置行動裝置優化
   */
  setupMobileOptimizations() {
    if (this.currentBreakpoint === "xs" || this.currentBreakpoint === "sm") {
      this.enableMobileOptimizations();
    }
  }

  /**
   * 啟用行動裝置優化
   */
  enableMobileOptimizations() {
    // 防止縮放
    const viewport = document.querySelector('meta[name="viewport"]');
    if (viewport) {
      viewport.setAttribute(
        "content",
        "width=device-width, initial-scale=1.0, user-scalable=no",
      );
    }

    // 隱藏位址列（iOS Safari）
    if (this.isTouch && /iPhone|iPad/.test(navigator.userAgent)) {
      window.addEventListener("load", () => {
        setTimeout(() => {
          window.scrollTo(0, 1);
        }, 100);
      });
    }

    // 改善觸控回應
    document.body.style.touchAction = "manipulation";
  }

  // ===========================================
  // 🔧 適應性功能
  // ===========================================

  /**
   * 檢測網路連接速度
   */
  detectConnection() {
    if ("connection" in navigator) {
      const connection = navigator.connection;

      if (
        connection.effectiveType === "slow-2g" ||
        connection.effectiveType === "2g"
      ) {
        return "slow";
      } else if (connection.effectiveType === "3g") {
        return "medium";
      } else {
        return "fast";
      }
    }

    return "unknown";
  }

  /**
   * 設置適應性功能
   */
  setupAdaptiveFeatures() {
    // 根據網路狀況調整功能
    this.adaptToConnection();

    // 根據設備效能調整功能
    this.adaptToPerformance();
  }

  /**
   * 根據網路狀況適應
   */
  adaptToConnection() {
    if (this.connectionSpeed === "slow") {
      // 延遲載入非關鍵資源
      this.delayNonCriticalResources();

      // 減少動畫效果
      document.body.classList.add("low-bandwidth");
    }
  }

  /**
   * 根據效能適應
   */
  adaptToPerformance() {
    // 簡單的效能檢測
    const start = performance.now();

    // 執行一些計算密集的操作
    for (let i = 0; i < 100000; i++) {
      Math.random();
    }

    const duration = performance.now() - start;

    if (duration > 10) {
      this.enablePerformanceMode();
    }
  }

  // ===========================================
  // 🎯 設備特定功能
  // ===========================================

  /**
   * 設置設備特定功能
   */
  setupDeviceSpecificFeatures() {
    const userAgent = navigator.userAgent;

    // iOS 特定優化
    if (/iPhone|iPad/.test(userAgent)) {
      this.setupIOSOptimizations();
    }

    // Android 特定優化
    if (/Android/.test(userAgent)) {
      this.setupAndroidOptimizations();
    }

    // 桌面特定優化
    if (!this.isTouch) {
      this.setupDesktopOptimizations();
    }
  }

  /**
   * iOS 優化
   */
  setupIOSOptimizations() {
    document.body.classList.add("ios-device");

    // 修復 iOS Safari 的 100vh 問題
    const setVH = () => {
      const vh = window.innerHeight * 0.01;
      document.documentElement.style.setProperty("--vh", `${vh}px`);
    };

    setVH();
    window.addEventListener("resize", setVH);
  }

  /**
   * Android 優化
   */
  setupAndroidOptimizations() {
    document.body.classList.add("android-device");

    // Android 特定的觸控優化
    document.addEventListener("touchstart", () => {}, { passive: true });
  }

  /**
   * 桌面優化
   */
  setupDesktopOptimizations() {
    document.body.classList.add("desktop-device");

    // 滑鼠懸停效果
    this.enableHoverEffects();
  }

  // ===========================================
  // 🚀 工具方法
  // ===========================================

  /**
   * 重新計算佈局
   */
  recalculateLayout() {
    // 觸發重新佈局事件
    window.dispatchEvent(new CustomEvent("layoutRecalculate"));
  }

  /**
   * 關閉所有模態框
   */
  closeAllModals() {
    const modals = document.querySelectorAll(".modal.active, .overlay.active");
    modals.forEach((modal) => {
      modal.classList.remove("active");
    });
  }

  /**
   * 延遲載入非關鍵資源
   */
  delayNonCriticalResources() {
    // 延遲載入裝飾性圖片
    const decorativeImages = document.querySelectorAll("img[data-decorative]");
    decorativeImages.forEach((img) => {
      img.style.display = "none";
    });
  }

  /**
   * 預載入關鍵資源
   */
  preloadCriticalResources() {
    // 預載入關鍵 CSS
    const criticalCSS = document.querySelector(
      'link[rel="preload"][as="style"]',
    );
    if (criticalCSS && this.connectionSpeed !== "slow") {
      const link = document.createElement("link");
      link.rel = "stylesheet";
      link.href = criticalCSS.href;
      document.head.appendChild(link);
    }
  }

  /**
   * 啟用懸停效果
   */
  enableHoverEffects() {
    const hoverElements = document.querySelectorAll("[data-hover]");
    hoverElements.forEach((element) => {
      element.classList.add("hover-enabled");
    });
  }

  /**
   * 斷點特定優化
   */
  optimizeForBreakpoint(breakpoint) {
    switch (breakpoint) {
      case "xs":
      case "sm":
        this.enableMobileOptimizations();
        break;
      case "md":
      case "lg":
        this.enableTabletOptimizations();
        break;
      case "xl":
      case "2xl":
        this.enableDesktopOptimizations();
        break;
    }
  }

  /**
   * 平板優化
   */
  enableTabletOptimizations() {
    document.body.classList.add("tablet-optimized");

    // 平板特定的觸控和鍵盤混合使用優化
    this.setupHybridInput();
  }

  /**
   * 混合輸入支援
   */
  setupHybridInput() {
    // 同時支援觸控和鍵盤/滑鼠輸入
    let lastInputType = "";

    document.addEventListener("touchstart", () => {
      if (lastInputType !== "touch") {
        document.body.classList.add("touch-input");
        document.body.classList.remove("mouse-input");
        lastInputType = "touch";
      }
    });

    document.addEventListener("mousedown", () => {
      if (lastInputType !== "mouse") {
        document.body.classList.add("mouse-input");
        document.body.classList.remove("touch-input");
        lastInputType = "mouse";
      }
    });
  }

  /**
   * 優化初始載入
   */
  optimizeInitialLoad() {
    // 移除載入動畫
    const loader = document.querySelector(".loader");
    if (loader) {
      setTimeout(() => {
        loader.style.opacity = "0";
        setTimeout(() => {
          loader.remove();
        }, 300);
      }, 500);
    }

    // 逐步顯示內容
    this.revealContent();
  }

  /**
   * 逐步顯示內容
   */
  revealContent() {
    const sections = document.querySelectorAll(".fade-in-section");
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-visible");
          }
        });
      },
      {
        threshold: 0.1,
        rootMargin: "0px 0px -50px 0px",
      },
    );

    sections.forEach((section) => {
      observer.observe(section);
    });
  }

  /**
   * 獲取性能報告
   */
  getPerformanceReport() {
    const avgInteractionLatency =
      this.performanceMetrics.interactionLatency.length > 0
        ? this.performanceMetrics.interactionLatency.reduce((a, b) => a + b) /
          this.performanceMetrics.interactionLatency.length
        : 0;

    const avgImageLoadTime =
      this.performanceMetrics.imageLoadTimes.length > 0
        ? this.performanceMetrics.imageLoadTimes.reduce((a, b) => a + b) /
          this.performanceMetrics.imageLoadTimes.length
        : 0;

    return {
      loadTime: this.performanceMetrics.loadTime,
      avgInteractionLatency,
      avgImageLoadTime,
      breakpoint: this.currentBreakpoint,
      connectionSpeed: this.connectionSpeed,
      isTouch: this.isTouch,
      reducedMotion: this.reducedMotion,
    };
  }
}

// 自動初始化
let responsiveEnhancer;

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", () => {
    responsiveEnhancer = new ResponsiveEnhancer();
  });
} else {
  responsiveEnhancer = new ResponsiveEnhancer();
}

// 全域存取
window.ResponsiveEnhancer = ResponsiveEnhancer;
window.responsiveEnhancer = responsiveEnhancer;
