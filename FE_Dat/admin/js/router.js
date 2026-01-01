/**
 * Simple Client-Side Router for Admin Dashboard (Hash-based)
 */

const Router = {
    // Map hash paths to partial files
    routes: {
        '': 'pages/dashboard.html',
        '#': 'pages/dashboard.html',
        '#dashboard': 'pages/dashboard.html',
        '#bots': 'pages/bots.html',
        '#users': 'pages/users.html',
        '#documents': 'pages/documents.html',
        '#settings': 'pages/settings.html',
        
        // Forms & Details
        '#create-bot': 'pages/create-bot.html',
        '#edit-bot': 'pages/edit-bot.html',
        '#create-user': 'pages/create-user.html',
        '#upload-document': 'pages/upload-document.html',
        '#chatbot': 'pages/chatbot.html'
    },

    contentContainer: null,

    init() {
        this.contentContainer = document.getElementById('app-content');
        if (!this.contentContainer) {
            console.error('Core content container #app-content not found');
            return;
        }

        // Listen for hash changes
        window.addEventListener('hashchange', () => {
            this.handleLocation();
        });

        // Initial Load
        this.handleLocation();
    },

    navigate(hash) {
        window.location.hash = hash;
    },

    async handleLocation() {
        // Get current hash, remove query string if any
        let hash = window.location.hash.split('?')[0];
        
        // Default to dashboard if empty
        if (!hash || hash === '') {
            hash = '#dashboard';
        }

        const route = this.routes[hash] || 'pages/dashboard.html';
        
        // Dispatch event for sidebar highlighting
        // Remove # for simpler matching
        const simpleName = hash.replace('#', '') || 'dashboard';
        window.dispatchEvent(new CustomEvent('routeChanged', { detail: { path: simpleName } }));

        try {
            this.contentContainer.innerHTML = '<div class="flex items-center justify-center h-full"><i class="ph ph-spinner animate-spin text-4xl text-primary-600"></i></div>';
            
            // Add timestamp to prevent caching
            const fetchUrl = `${route}?t=${new Date().getTime()}`;
            const response = await fetch(fetchUrl);
            
            if (!response.ok) throw new Error(`Could not load ${route} (Status: ${response.status})`);
            
            const html = await response.text();
            this.contentContainer.innerHTML = html;

            // RE-EXECUTE SCRIPTS
            this.executeScripts(this.contentContainer);

            // Re-apply translations
            if (window.updateLanguage) {
                const currentLang = localStorage.getItem('lang') || 'vi';
                window.updateLanguage(currentLang);
            }

        } catch (error) {
            console.error('Router Error:', error);
            this.contentContainer.innerHTML = `<div class="p-10 text-center text-red-500"><h3>Lỗi tải trang</h3><p>${error.message}</p></div>`;
        }
    },

    executeScripts(container) {
        const scripts = container.querySelectorAll('script');
        scripts.forEach(oldScript => {
            const newScript = document.createElement('script');
            Array.from(oldScript.attributes).forEach(attr => newScript.setAttribute(attr.name, attr.value));
            newScript.textContent = oldScript.textContent;
            oldScript.parentNode.replaceChild(newScript, oldScript);
        });
    }
};

window.Router = Router;
