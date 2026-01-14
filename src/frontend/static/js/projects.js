/**
 * Portfolio Projects Loader
 * Fetches data from projects.json (primary) or GitHub API (fallback).
 */

document.addEventListener("DOMContentLoaded", () => {
  const GITHUB_USERNAME = "sacahan";
  const GITHUB_API_URL = `https://api.github.com/users/${GITHUB_USERNAME}/repos?sort=updated&per_page=100`;
  const PROJECTS_JSON_URL = "./data/projects.json";

  // Default covers with premium mesh-like gradients
  const DEFAULT_COVERS = [
    "radial-gradient(at 0% 0%, #1e3a8a 0%, transparent 50%), radial-gradient(at 100% 0%, #3b82f6 0%, transparent 50%), radial-gradient(at 50% 100%, #172554 0%, transparent 50%), #0f172a",
    "radial-gradient(at 0% 0%, #5b21b6 0%, transparent 50%), radial-gradient(at 100% 0%, #8b5cf6 0%, transparent 50%), radial-gradient(at 50% 100%, #2e1065 0%, transparent 50%), #0f172a",
    "radial-gradient(at 0% 0%, #064e3b 0%, transparent 50%), radial-gradient(at 100% 0%, #10b981 0%, transparent 50%), radial-gradient(at 50% 100%, #022c22 0%, transparent 50%), #0f172a",
    "radial-gradient(at 0% 0%, #7c2d12 0%, transparent 50%), radial-gradient(at 100% 0%, #f97316 0%, transparent 50%), radial-gradient(at 50% 100%, #431407 0%, transparent 50%), #0f172a",
    "radial-gradient(at 0% 0%, #701a75 0%, transparent 50%), radial-gradient(at 100% 0%, #d946ef 0%, transparent 50%), radial-gradient(at 50% 100%, #4a044e 0%, transparent 50%), #0f172a",
    "radial-gradient(at 0% 0%, #164e63 0%, transparent 50%), radial-gradient(at 100% 0%, #06b6d4 0%, transparent 50%), radial-gradient(at 50% 100%, #083344 0%, transparent 50%), #0f172a",
  ];

  /**
   * Fetch projects from projects.json
   */
  async function fetchProjectsJSON() {
    try {
      const response = await fetch(PROJECTS_JSON_URL);
      if (!response.ok) throw new Error("Failed to fetch projects.json");
      const data = await response.json();

      // Convert ProjectItem format to repo format
      return (data.projects || []).map(proj => ({
        name: proj.id,
        description: proj.desc_en || "",
        html_url: proj.githubUrl || `https://github.com/sacahan/${proj.id}`,
        homepage: proj.demoUrl || "",
        topics: proj.tags || [],
        // Custom fields for projects.json data
        _customData: {
          cover: proj.cover,
          zh: {
            title: proj.title_zh,
            desc: proj.desc_zh
          },
          en: {
            title: proj.title_en,
            desc: proj.desc_en
          },
          demoUrl: proj.demoUrl,
          githubUrl: proj.githubUrl,
          tags: proj.tags
        }
      }));
    } catch (error) {
      console.error("Error fetching projects.json:", error);
      return [];
    }
  }

  /**
   * Fallback: Fetch from GitHub API
   */
  async function fetchGitHubRepos() {
    try {
      const response = await fetch(GITHUB_API_URL);
      if (!response.ok) throw new Error("Failed to fetch GitHub data");
      const repos = await response.json();
      return repos.filter((repo) => !repo.fork);
    } catch (error) {
      console.error("Error fetching repos from GitHub:", error);
      return [];
    }
  }

  /**
   * Get project data with projects.json as primary source
   */
  async function fetchProjects() {
    const projectsJsonData = await fetchProjectsJSON();

    // If projects.json has data, use it exclusively
    if (projectsJsonData.length > 0) {
      return projectsJsonData;
    }

    // Fallback to GitHub API if projects.json is empty
    console.log("projects.json is empty, falling back to GitHub API");
    return fetchGitHubRepos();
  }

  function createProjectCard(repo, index) {
    const customData = repo._customData || {};

    // Check current language from MultilingualManager if available
    const currentLang =
      window.multilingualManager?.currentLanguage ||
      document.documentElement.lang ||
      "zh-TW";
    const isZH = currentLang.startsWith("zh");

    const title =
      (isZH ? customData.zh?.title : customData.en?.title) || repo.name;
    const desc =
      (isZH ? customData.zh?.desc : customData.en?.desc) ||
      repo.description ||
      "Project description soon...";

    const coverStyle = customData.cover
      ? `background-image: url('${customData.cover}')`
      : `background: ${DEFAULT_COVERS[index % DEFAULT_COVERS.length]}`;

    // Use URLs from projects.json or GitHub
    const demoUrl = customData.demoUrl || repo.homepage || null;
    const githubUrl = customData.githubUrl || repo.html_url;

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

    const tagsHtml = (customData.tags || repo.topics || [repo.language || "Project"])
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

    const repos = await fetchProjects();
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
