/**
 * ResumeMate 前端主要 JavaScript 功能
 * 此類負責初始化頁面互動、語言切換、動畫效果、聊天範例、通知提示等功能。
 */

class ResumeMateFrontend {
  /**
   * 建構函式，初始化預設語言並執行初始化流程。
   */
  constructor() {
    this.currentLang = "zh-TW";
    this.init();
  }

  /**
   * 初始化所有前端互動功能，包括語言切換、平滑滾動、聊天範例、動畫效果。
   */
  init() {
    this.setupLanguageToggle();
    this.setupSmoothScrolling();
    this.setupChatExamples();
    this.setupAnimations();
  }

  /**
   * 設定語言切換按鈕的事件監聽器。
   * 點擊後會呼叫 toggleLanguage 方法切換語言。
   */
  setupLanguageToggle() {
    const langToggle = document.getElementById("lang-toggle");

    if (langToggle) {
      langToggle.addEventListener("click", () => {
        this.toggleLanguage();
      });
    }
  }

  /**
   * 切換目前語言，並更新相關 UI 元素與本地儲存。
   * 會同步更新 HTML lang 屬性與所有多語言元素的內容。
   */
  toggleLanguage() {
    this.currentLang = this.currentLang === "zh-TW" ? "en" : "zh-TW";

    // 更新語言切換按鈕文字
    const langToggle = document.getElementById("lang-toggle");
    if (langToggle) {
      langToggle.textContent = this.currentLang === "zh-TW" ? "EN" : "中";
    }

    // 更新所有具有 data-zh 與 data-en 屬性的元素文字
    const elements = document.querySelectorAll("[data-zh][data-en]");
    elements.forEach((element) => {
      const text =
        this.currentLang === "zh-TW"
          ? element.getAttribute("data-zh")
          : element.getAttribute("data-en");

      if (text) {
        element.textContent = text;
      }
    });

    // 設定 HTML 文件的語言屬性
    document.documentElement.lang = this.currentLang;

    // 儲存語言設定到 localStorage
    localStorage.setItem("preferred-language", this.currentLang);
  }

  /**
   * 載入本地儲存的語言偏好設定，若與目前語言不同則切換語言。
   */
  loadLanguagePreference() {
    const savedLang = localStorage.getItem("preferred-language");
    if (savedLang && savedLang !== this.currentLang) {
      this.toggleLanguage();
    }
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
    console.log("發送問題到聊天:", question);

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
          entry.target.style.opacity = "1";
          entry.target.style.transform = "translateY(0)";
        }
      });
    }, observerOptions);

    animatedElements.forEach((element) => {
      element.style.opacity = "0";
      element.style.transform = "translateY(30px)";
      element.style.transition = "opacity 0.6s ease, transform 0.6s ease";
      observer.observe(element);
    });
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
   * 檢查 Gradio 聊天服務是否運行中，回傳布林值。
   * @returns {Promise<boolean>} - 是否可連線
   */
  async checkGradioStatus() {
    try {
      await fetch("http://localhost:7860/", {
        method: "HEAD",
        mode: "no-cors",
      });
      return true;
    } catch (error) {
      console.warn("Gradio 服務無法連接:", error);
      return false;
    }
  }

  /**
   * 根據 Gradio 服務狀態，更新聊天 iframe 的顯示內容。
   * 若服務未啟動則顯示替代提示。
   */
  async updateChatStatus() {
    const iframe = document.querySelector('iframe[src*="7860"]');
    const isGradioRunning = await this.checkGradioStatus();

    if (!isGradioRunning && iframe) {
      // 如果 Gradio 未運行，顯示替代內容
      const container = iframe.parentElement;
      container.innerHTML = `
                <div class="flex items-center justify-center h-full bg-gray-800 rounded-lg">
                    <div class="text-center">
                        <div class="text-4xl mb-4">🤖</div>
                        <h3 class="text-xl font-bold mb-2 text-yellow-400">AI 聊天服務暫時離線</h3>
                        <p class="text-gray-300 mb-4">請稍後再試，或透過其他方式聯繫我</p>
                        <div class="flex flex-col space-y-2">
                            <span class="text-sm text-gray-400">服務啟動指令：</span>
                            <code class="bg-gray-700 px-3 py-1 rounded text-sm">python app.py</code>
                        </div>
                    </div>
                </div>
            `;
    }
  }
}

// 當 DOM 內容載入完成後，初始化 ResumeMateFrontend 並執行語言與聊天服務狀態檢查。
document.addEventListener("DOMContentLoaded", () => {
  const app = new ResumeMateFrontend();

  // 載入語言設定
  app.loadLanguagePreference();

  // 檢查聊天服務狀態
  // app.updateChatStatus();

  // 定期檢查服務狀態（可選）
  // setInterval(() => app.updateChatStatus(), 30000);
});
