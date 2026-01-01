// admin/js/main.js

// 1. Initialize Theme IMMEDIATELY
const html = document.documentElement;
const savedTheme = localStorage.getItem('theme');
const systemDark = window.matchMedia('(prefers-color-scheme: dark)').matches;

if (savedTheme === 'dark' || (!savedTheme && systemDark)) {
    html.classList.add('dark');
} else {
    html.classList.remove('dark');
}

document.addEventListener("DOMContentLoaded", function () {
    // Re-apply theme
    const savedTheme = localStorage.getItem('theme');
    const systemDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    if (savedTheme === 'dark' || (!savedTheme && systemDark)) {
        document.documentElement.classList.add('dark');
    } else {
        document.documentElement.classList.remove('dark');
    }

    // Load Sidebar
    const sidebarContainer = document.getElementById("sidebar-container");
    if (sidebarContainer) {
        fetch('components/sidebar.html')
            .then(response => response.text())
            .then(data => {
                sidebarContainer.innerHTML = data;
                // Once sidebar is loaded, check current route to highlight
                // We dispatch or call check manually. 
                // However, Router.init() calls handleLocation which dispatches 'routeChanged'.
                // If Router.init() happened BEFORE sidebar load, event might be missed.
                // So we listen, but also try to highlight immediately if Router already set.
                
                // Better approach: Init Router AFTER sidebar is ready? 
                // Or just listen to event.
                
                // Logout Logic
                const logoutBtn = document.getElementById('logout-btn');
                if (logoutBtn) {
                    logoutBtn.addEventListener('click', (e) => {
                        e.preventDefault();
                        if (confirm('Bạn có chắc muốn đăng xuất?')) {
                            localStorage.removeItem('token');
                            window.location.href = '../login.html';
                        }
                    });
                }
            })
            .catch(error => console.error('Lỗi tải sidebar:', error));
    }

    // Load Topbar
    const topbarContainer = document.getElementById("topbar-container");
    if (topbarContainer) {
        fetch('components/topbar.html')
            .then(response => response.text())
            .then(data => {
                topbarContainer.innerHTML = data;
                initTopbarLogic();
            })
            .catch(error => console.error('Lỗi tải topbar:', error));
    }

    // Initialize Router if available
    if (window.Router) {
        window.Router.init();
    }
});

// Listen to Router Changes for Sidebar Highlight
window.addEventListener('routeChanged', (e) => {
    const pageObj = e.detail; 
    // pageObj.path is like 'bots' or 'index.html'
    
    // Normalize logic
    let page = pageObj.path;
    if (page === 'dashboard.html' || page === 'dashboard' || page === '' || page === 'index.html') {
        page = 'index';
    }
    
    highlightActiveMenu(page);
});


function initTopbarLogic() {
    // --- THEME SWITCHER UI UPDATE ---
    const themeToggle = document.getElementById('theme-toggle');
    const themeIcon = document.getElementById('theme-icon');
    
    // Update Icon based on current state
    if (html.classList.contains('dark') && themeIcon) {
        themeIcon.classList.replace('ph-moon', 'ph-sun');
    }

    // Toggle Event
    if (themeToggle && themeIcon) {
        themeToggle.addEventListener('click', () => {
            html.classList.toggle('dark');
            const isDark = html.classList.contains('dark');
            
            // Update Icon
            if (isDark) {
                themeIcon.classList.replace('ph-moon', 'ph-sun');
                localStorage.setItem('theme', 'dark');
            } else {
                themeIcon.classList.replace('ph-sun', 'ph-moon');
                localStorage.setItem('theme', 'light');
            }
        });
    }

    // --- LANGUAGE SWITCHER ---
    const langToggle = document.getElementById('lang-toggle');
    const langCheckbox = document.getElementById('lang-checkbox');

    // 1. Initial State
    let currentLang = localStorage.getItem('lang') || 'vi'; // Default to vietnamese
    if (langCheckbox) {
        langCheckbox.checked = (currentLang === 'en');
        updateLanguage(currentLang);
    }

    // 2. Toggle Event
    if (langCheckbox) {
        const updateFlag = (isEn) => {
            const flagIcon = document.getElementById('flag-icon');
            if (flagIcon) {
                flagIcon.src = isEn ? 'https://flagcdn.com/w40/us.png' : 'https://flagcdn.com/w40/vn.png';
                flagIcon.alt = isEn ? 'US' : 'VN';
            }
        };

        updateFlag(langCheckbox.checked);

        langCheckbox.addEventListener('change', (e) => {
            const isEn = e.target.checked;
            const newLang = isEn ? 'en' : 'vi';
            localStorage.setItem('lang', newLang);
            updateLanguage(newLang);
            updateFlag(isEn);
        });
    }
}

// Global Translation Function
function updateLanguage(lang) {
    if (typeof translations === 'undefined') {
        return;
    }

    const t = translations[lang];
    if (!t) return;

    const elements = document.querySelectorAll('[data-i18n]');
    elements.forEach(el => {
        const key = el.getAttribute('data-i18n');
        if (t[key]) {
            if (el.tagName === 'INPUT' && el.getAttribute('placeholder')) {
                el.placeholder = t[key];
            } else {
                el.innerText = t[key];
            }
        }
    });

    window.dispatchEvent(new CustomEvent('languageChanged', { detail: { lang } }));
}

function highlightActiveMenu(pageName) {
    // Reset all
    const links = document.querySelectorAll('#sidebar-menu a');
    links.forEach(link => {
        link.classList.remove('bg-blue-50', 'text-blue-600', 'font-medium');
        link.classList.add('text-gray-500');
        const i = link.querySelector('i');
        if(i) {
            i.classList.remove('ph-fill');
            i.classList.add('ph');
        }
    });

    // Highlight specific
    // Match data-page exactly (e.g. "bots" or "index")
    const activeLink = document.querySelector(`a[data-page="${pageName}"]`);

    if (activeLink) {
        activeLink.classList.remove('text-gray-500');
        activeLink.classList.add('bg-blue-50', 'text-blue-600', 'font-medium');

        const icon = activeLink.querySelector('i');
        if (icon) {
            icon.classList.remove('ph');
            icon.classList.add('ph-fill');
        }
    }
}