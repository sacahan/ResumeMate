/**
 * Portfolio Projects Loader
 * Fetches data from GitHub API and populates the portfolio swiper.
 */

document.addEventListener("DOMContentLoaded", () => {
  const GITHUB_USERNAME = "sacahan";
  const API_URL = `https://api.github.com/users/${GITHUB_USERNAME}/repos?sort=updated&per_page=100`;

  // Static project data for existing projects or overrides
  const STATIC_PROJECTS = {
    ResumeMate: {
      cover: "static/images/resume_mate_cover.png",
      tags: ["OpenAI Agent", "RAG", "Gradio", "ChromaDB"],
      demoUrl: "https://www.brianhan.cc/",
      githubUrl: "https://github.com/sacahan/ResumeMate",
      zh: {
        title: "ResumeMate",
        desc: "ResumeMate 是一個基於 AI 的簡歷代理平台，協助使用者優化職涯發展與履歷撰寫。",
      },
      en: {
        title: "ResumeMate",
        desc: "ResumeMate is an AI-powered resume agent platform helping users optimize career growth and resume writing.",
      },
    },
    TrailTag: {
      cover: "static/images/trail_tag_cover.png",
      tags: ["CrewAI", "Gradio", "Chrome Extension", "Redis", "FastAPI"],
      demoUrl: "https://www.youtube.com/watch?v=DzmGJXYH4-g",
      githubUrl: "https://github.com/sacahan/TrailTag",
      zh: {
        title: "TrailTag",
        desc: "AI 驅動的工具，可自動偵測 YouTube 影片中提到的位置並即時標記座標與 Chrome 擴充功能整合。",
      },
      en: {
        title: "TrailTag",
        desc: "AI-powered tool that detects locations in YouTube videos and tags coordinates in real-time with Chrome Extension.",
      },
    },
    CSCFlow: {
      cover: "static/images/csc_flow_cover.png",
      tags: ["Python", "Typescript", "HTML", "Shell", "Docker"],
      demoUrl: "https://flow.brianhan.cc/",
      githubUrl: "https://github.com/sacahan/cscflow",
      zh: {
        title: "CSCFlow",
        desc: "針對台灣公共運動中心的即時人流監控與分析系統，提供歷史與當下流量視覺化。",
      },
      en: {
        title: "CSCFlow",
        desc: "Real-time traffic monitoring and analytics system for public sports centers in Taiwan with visualization.",
      },
    },
    CasualTrader: {
      cover: "static/images/casual_trader_cover.png",
      tags: ["Python", "OpenAI SDK", "MCP", "Trading"],
      demoUrl: "https://trader.brianhan.cc/",
      githubUrl: "https://github.com/sacahan/CasualTrader",
      zh: {
        title: "CasualTrader",
        desc: "台股 AI 交易模擬平台，結合 OpenAI Agent SDK 與 MCP 核心，實現從研發到執行的全自動化。",
      },
      en: {
        title: "CasualTrader",
        desc: "AI trading simulation platform for Taiwan stocks with OpenAI Agent SDK & MCP, automating research to execution.",
      },
    },
    CasualMarket: {
      cover: "static/images/casual_market_cover.png",
      tags: ["TypeScript", "MCP Server", "Finance API", "Taiwan Stock"],
      demoUrl: "https://trader.brianhan.cc/",
      githubUrl: "https://github.com/sacahan/CasualMarket",
      zh: {
        title: "CasualMarket",
        desc: "功能完整的台股交易 Model Context Protocol (MCP) Server，提供即時股價、財務分析與 K 線視覺化接口。",
      },
      en: {
        title: "CasualMarket",
        desc: "Comprehensive Taiwan Stock Model Context Protocol (MCP) Server for real-time prices and financial analysis.",
      },
    },
    SpecPilot: {
      cover: "static/images/spec_pilot_cover.png",
      tags: [
        "TypeScript",
        "LLM",
        "Spec-Driven Development",
        "MCP",
        "Redis",
        "FastAPI",
        "SDD",
      ],
      githubUrl: "https://github.com/sacahan/SpecPilot",
      zh: {
        title: "SpecPilot",
        desc: "專案規範管理 MCP 伺服器，將自然語言需求轉化為結構化規格並追蹤進度，提升開發協作效率。",
      },
      en: {
        title: "SpecPilot",
        desc: "MCP server for project specification management, converting natural language into structured requirements.",
      },
    },
    YTSearch: {
      cover: "static/images/yt_search_cover.png",
      tags: ["Python", "FastAPI", "Web Scraping", "MCP"],
      githubUrl: "https://github.com/sacahan/YTSearch",
      zh: {
        title: "YTSearch",
        desc: "高效且零成本的 YouTube 影片搜尋 API，支援 MCP 協定，為 AI 助手提供強大的影片與頻道檢索能力。",
      },
      en: {
        title: "YTSearch",
        desc: "Zero-cost YouTube video search API with MCP support, enhancing AI assistants with video and channel retrieval.",
      },
    },
    MarkdownVault: {
      cover: "static/images/markdown_vault_cover.png",
      tags: ["Python", "ChromaDB", "RAG", "Markdown"],
      githubUrl: "https://github.com/sacahan/MarkdownVault",
      zh: {
        title: "MarkdownVault",
        desc: "將 Markdown 知識庫轉換為向量並存儲於本地 Chroma 資料庫，支援語意搜尋與 RAG 提示詞整合。",
      },
      en: {
        title: "MarkdownVault",
        desc: "Converts Markdown to vectors in local Chroma database, supporting semantic search and RAG prompts.",
      },
    },
    MediaGrabber: {
      cover: "static/images/media_grabber_cover.png",
      tags: ["Python", "yt-dlp", "FFmpeg", "Downloader", "GUI"],
      demoUrl: "https://media.brianhan.cc/",
      githubUrl: "https://github.com/sacahan/MediaGrabber",
      zh: {
        title: "MediaGrabber",
        desc: "支援 YouTube、Facebook 與 Instagram 的簡約高效媒體下載器，支援多種解析度與格式選擇。",
      },
      en: {
        title: "MediaGrabber",
        desc: "Simple and elegant media downloader for Youtube, Facebook, and Instagram with multiple format support.",
      },
    },
  };

  // Default covers with premium mesh-like gradients
  const DEFAULT_COVERS = [
    "radial-gradient(at 0% 0%, #1e3a8a 0%, transparent 50%), radial-gradient(at 100% 0%, #3b82f6 0%, transparent 50%), radial-gradient(at 50% 100%, #172554 0%, transparent 50%), #0f172a",
    "radial-gradient(at 0% 0%, #5b21b6 0%, transparent 50%), radial-gradient(at 100% 0%, #8b5cf6 0%, transparent 50%), radial-gradient(at 50% 100%, #2e1065 0%, transparent 50%), #0f172a",
    "radial-gradient(at 0% 0%, #064e3b 0%, transparent 50%), radial-gradient(at 100% 0%, #10b981 0%, transparent 50%), radial-gradient(at 50% 100%, #022c22 0%, transparent 50%), #0f172a",
    "radial-gradient(at 0% 0%, #7c2d12 0%, transparent 50%), radial-gradient(at 100% 0%, #f97316 0%, transparent 50%), radial-gradient(at 50% 100%, #431407 0%, transparent 50%), #0f172a",
    "radial-gradient(at 0% 0%, #701a75 0%, transparent 50%), radial-gradient(at 100% 0%, #d946ef 0%, transparent 50%), radial-gradient(at 50% 100%, #4a044e 0%, transparent 50%), #0f172a",
    "radial-gradient(at 0% 0%, #164e63 0%, transparent 50%), radial-gradient(at 100% 0%, #06b6d4 0%, transparent 50%), radial-gradient(at 50% 100%, #083344 0%, transparent 50%), #0f172a",
  ];

  async function fetchGitHubRepos() {
    try {
      const response = await fetch(API_URL);
      if (!response.ok) throw new Error("Failed to fetch GitHub data");
      const repos = await response.json();

      // Show all public repos that are NOT forks,
      // OR specific forks that are mentioned in STATIC_PROJECTS
      return repos.filter((repo) => !repo.fork || STATIC_PROJECTS[repo.name]);
    } catch (error) {
      console.error("Error fetching repos:", error);
      // Fallback to static list if API fails
      return Object.keys(STATIC_PROJECTS).map((name) => ({
        name,
        description: STATIC_PROJECTS[name].en.desc,
        html_url: `https://github.com/sacahan/${name}`,
        homepage: "",
        topics: [],
        language: "AI",
      }));
    }
  }

  function createProjectCard(repo, index) {
    const staticData = STATIC_PROJECTS[repo.name] || {};
    // Check current language from MultilingualManager if available
    const currentLang =
      window.multilingualManager?.currentLanguage ||
      document.documentElement.lang ||
      "zh-TW";
    const isZH = currentLang.startsWith("zh");

    const title =
      (isZH ? staticData.zh?.title : staticData.en?.title) || repo.name;
    const desc =
      (isZH ? staticData.zh?.desc : staticData.en?.desc) ||
      repo.description ||
      "Project description soon...";
    const coverStyle = staticData.cover
      ? `background-image: url('${staticData.cover}')`
      : `background: ${DEFAULT_COVERS[index % DEFAULT_COVERS.length]}`;

    // Determine demo and GitHub URLs from static data or repo data
    const demoUrl = staticData.demoUrl || repo.homepage || null;
    const githubUrl =
      staticData.githubUrl !== undefined ? staticData.githubUrl : repo.html_url;

    const demoLink = demoUrl
      ? `
            <a href="${demoUrl}" target="_blank" class="px-4 py-2 bg-blue-600/80 hover:bg-blue-600 text-white rounded-lg text-sm transition-colors flex items-center gap-2">
                <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" /></svg>
                Demo
            </a>`
      : "";

    const githubLink = githubUrl
      ? `
            <a href="${githubUrl}" target="_blank" class="px-4 py-2 glass-effect hover:bg-white/10 text-white rounded-lg text-sm transition-all duration-300 flex items-center gap-2 border border-white/10 hover:border-white/20">
                <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 24 24"><path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.205 11.385.6.113.82-.258.82-.577 0-.285-.01-1.04-.015-2.04-3.338.724-4.042-1.61-4.042-1.61C4.422 18.07 3.633 17.7 3.633 17.7c-1.087-.744.084-.729.084-.729 1.205.084 1.838 1.236 1.838 1.236 1.07 1.835 2.809 1.305 3.495.998.108-.776.417-1.305.76-1.605-2.665-.3-5.466-1.332-5.466-5.93 0-1.31.465-2.38 1.235-3.22-.135-.303-.54-1.523.105-3.176 0 0 1.005-.322 3.3 1.23.96-.267 1.98-.399 3-.405 1.02.006 2.04.138 3 .405 2.28-1.552 3.285-1.23 3.285-1.23.645 1.653.24 2.873.12 3.176.765.84 1.23 1.91 1.23 3.22 0 4.61-2.805 5.625-5.475 5.92.43.372.823 1.102.823 2.222 0 1.606-.015 2.896-.015 3.286 0 .315.21.69.825.57C20.565 21.795 24 17.298 24 12c0-6.627-5.373-12-12-12z"/></svg>
                GitHub
            </a>`
      : "";

    const tagsHtml = (
      staticData.tags ||
      (repo.topics?.length ? repo.topics : [repo.language || "Project"])
    )
      .slice(0, 5)
      .map(
        (tag) =>
          `<span class="tag-badge text-[10px] uppercase font-bold tracking-wider">${tag}</span>`,
      )
      .join("");

    return `
            <div class="swiper-slide h-auto opacity-0 transition-opacity duration-500" data-project-slide>
                <div class="group relative overflow-hidden rounded-xl glass-card h-full flex flex-col transform backdrop-blur-sm">
                    <!-- Image/Cover Area -->
                    <div class="relative h-48 overflow-hidden bg-gray-900/50">
                        <div class="absolute inset-0 bg-cover bg-center transition-transform duration-700 group-hover:scale-110" style="${coverStyle}"></div>
                        <div class="absolute inset-0 bg-gradient-to-t from-gray-900 via-gray-900/40 to-transparent"></div>
                    </div>

                    <!-- Content Area -->
                    <div class="p-6 flex-grow flex flex-col">
                        <h3 class="text-xl font-bold text-white mb-2 group-hover:text-orange-400 transition-colors duration-300">
                            ${title}
                        </h3>
                        <div class="flex flex-wrap gap-2 mb-4">
                            ${tagsHtml}
                        </div>
                        <p class="text-gray-400 text-sm mb-6 flex-grow line-clamp-3 leading-relaxed">
                            ${desc}
                        </p>

                        <!-- Links -->
                        <div class="flex gap-3 mt-auto">
                            ${demoLink}
                            ${githubLink}
                        </div>
                    </div>
                </div>
            </div>
        `;
  }

  async function initPortfolio() {
    const container = document.getElementById("portfolio-container");
    if (!container) return;

    // Show loading skeleton or spinner
    container.innerHTML = `
      <div class="swiper-slide flex justify-center items-center py-20 w-full col-span-full">
        <div class="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-orange-500"></div>
      </div>
    `;

    const repos = await fetchGitHubRepos();
    container.innerHTML = "";

    repos.forEach((repo, index) => {
      const cardHtml = createProjectCard(repo, index);
      container.insertAdjacentHTML("beforeend", cardHtml);
    });

    // Initialize Swiper with a check
    if (typeof Swiper === "undefined") {
      console.warn("Swiper is not loaded yet. Retrying in 100ms...");
      setTimeout(initSwiper, 100);
      return;
    }

    function initSwiper() {
      const portfolioSwiper = new Swiper(".portfolio-swiper", {
        slidesPerView: 1,
        spaceBetween: 24,
        loop: repos.length > 3,
        grabCursor: true,
        centeredSlides: false,
        watchSlidesProgress: true,
        pagination: {
          el: ".swiper-pagination",
          clickable: true,
          dynamicBullets: true,
        },
        navigation: {
          nextEl: ".swiper-button-next",
          prevEl: ".swiper-button-prev",
        },
        breakpoints: {
          640: {
            slidesPerView: 2,
          },
          1024: {
            slidesPerView: 3,
          },
        },
        autoplay: {
          delay: 5000,
          disableOnInteraction: false,
          pauseOnMouseEnter: true,
        },
        on: {
          init: function () {
            setTimeout(() => {
              document
                .querySelectorAll("[data-project-slide]")
                .forEach((slide) => {
                  slide.classList.remove("opacity-0");
                });
              this.update();
            }, 300);
          },
        },
      });

      // Listen to language changes from MultilingualManager
      if (window.multilingualManager) {
        window.multilingualManager.addObserver((event, data) => {
          if (event === "languageChanged") {
            container.innerHTML = "";
            repos.forEach((repo, index) => {
              const cardHtml = createProjectCard(repo, index);
              container.insertAdjacentHTML("beforeend", cardHtml);
            });
            portfolioSwiper.update();
            // Re-fade in
            setTimeout(() => {
              document
                .querySelectorAll("[data-project-slide]")
                .forEach((slide) => {
                  slide.classList.remove("opacity-0");
                });
            }, 100);
          }
        });
      }
    }

    initSwiper();
  }

  initPortfolio();
});
