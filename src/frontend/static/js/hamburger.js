/**
 * 漢堡菜單切換邏輯
 * 處理行動裝置上的導航菜單開/關
 */

document.addEventListener("DOMContentLoaded", () => {
    const hamburgerBtn = document.getElementById("hamburger-btn");
    const mobileMenu = document.getElementById("mobile-menu");

    if (!hamburgerBtn || !mobileMenu) {
        console.warn("Hamburger menu elements not found");
        return;
    }

    /**
     * 切換菜單狀態
     */
    function toggleMenu() {
        const isOpen = hamburgerBtn.classList.contains("active");

        if (isOpen) {
            closeMenu();
        } else {
            openMenu();
        }
    }

    /**
     * 打開菜單
     */
    function openMenu() {
        hamburgerBtn.classList.add("active");
        hamburgerBtn.setAttribute("aria-expanded", "true");
        mobileMenu.classList.remove("hidden");
        document.body.classList.add("menu-open");
    }

    /**
     * 關閉菜單
     */
    function closeMenu() {
        hamburgerBtn.classList.remove("active");
        hamburgerBtn.setAttribute("aria-expanded", "false");
        mobileMenu.classList.add("hidden");
        document.body.classList.remove("menu-open");
    }

    /**
     * 當點擊菜單連結時關閉菜單
     */
    function closeMenuOnLinkClick() {
        const menuLinks = mobileMenu.querySelectorAll("a");
        menuLinks.forEach((link) => {
            link.addEventListener("click", () => {
                // 延遲關閉，允許導航完成
                setTimeout(closeMenu, 150);
            });
        });
    }

    /**
     * 當點擊漢堡按鈕時切換菜單
     */
    hamburgerBtn.addEventListener("click", toggleMenu);

    /**
     * 當點擊菜單外時關閉菜單
     */
    document.addEventListener("click", (event) => {
        const isMenuOpen = hamburgerBtn.classList.contains("active");

        if (
            isMenuOpen &&
            !hamburgerBtn.contains(event.target) &&
            !mobileMenu.contains(event.target)
        ) {
            closeMenu();
        }
    });

    /**
     * 處理視窗大小變化 (從行動到桌面)
     */
    window.addEventListener("resize", () => {
        if (window.innerWidth >= 768) {
            closeMenu();
        }
    });

    // 初始化菜單連結點擊處理
    closeMenuOnLinkClick();

    /**
     * 支援鍵盤導航
     * ESC 鍵關閉菜單
     */
    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape") {
            closeMenu();
        }
    });

    // 監聽多語言系統的變化，更新菜單連結內容
    if (window.multilingualManager) {
        window.multilingualManager.addObserver((event) => {
            if (event === "languageChanged") {
                // 菜單連結會透過現有的多語言系統自動更新
                // 無需額外處理
            }
        });
    }
});
