document.addEventListener('DOMContentLoaded', function() {
    initializeSidebar();
    initializeDrawer();
    initializeMobileMenu();
    initializeThemeToggle();
    initializeFullscreenToggle();
    initializeTimeFilter();
    initializeCommandPalette();
});

function initializeSidebar() {
    const sidebar = document.getElementById('corporateSidebar');
    const collapseBtn = document.getElementById('sidebarCollapseBtn');

    if (!sidebar || !collapseBtn) return;

    const savedState = localStorage.getItem('sidebarCollapsed');
    if (savedState === 'true') {
        sidebar.classList.add('collapsed');
    }

    collapseBtn.addEventListener('click', function() {
        sidebar.classList.toggle('collapsed');
        const isCollapsed = sidebar.classList.contains('collapsed');
        localStorage.setItem('sidebarCollapsed', isCollapsed);

        const mainContent = document.querySelector('.main-content');
        if (mainContent) {
            if (isCollapsed) {
                mainContent.style.marginLeft = '80px';
            } else {
                mainContent.style.marginLeft = '260px';
            }
        }
    });

    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => {
        item.addEventListener('click', function() {
            navItems.forEach(nav => nav.classList.remove('active'));
            this.classList.add('active');
        });
    });
}

function initializeDrawer() {
    const drawer = document.getElementById('settingsDrawer');
    const overlay = document.getElementById('settingsDrawerOverlay');

    if (!drawer || !overlay) return;

    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && drawer.classList.contains('active')) {
            closeSettingsDrawer();
        }
    });
}

function openSettingsDrawer() {
    const drawer = document.getElementById('settingsDrawer');
    const overlay = document.getElementById('settingsDrawerOverlay');

    if (drawer && overlay) {
        drawer.classList.add('active');
        overlay.classList.add('active');
        document.body.style.overflow = 'hidden';
    }
}

function closeSettingsDrawer() {
    const drawer = document.getElementById('settingsDrawer');
    const overlay = document.getElementById('settingsDrawerOverlay');

    if (drawer && overlay) {
        drawer.classList.remove('active');
        overlay.classList.remove('active');
        document.body.style.overflow = '';
    }
}

function initializeMobileMenu() {
    const mobileToggle = document.getElementById('mobileMenuToggle');
    const sidebar = document.getElementById('corporateSidebar');
    
    if (!mobileToggle || !sidebar) return;
    
    mobileToggle.addEventListener('click', function() {
        sidebar.classList.toggle('mobile-open');
    });
    
    document.addEventListener('click', function(e) {
        if (window.innerWidth <= 768) {
            if (!sidebar.contains(e.target) && !mobileToggle.contains(e.target)) {
                sidebar.classList.remove('mobile-open');
            }
        }
    });
}

function toggleMobileSidebar() {
    const sidebar = document.getElementById('corporateSidebar');
    if (sidebar) {
        sidebar.classList.toggle('mobile-open');
    }
}

function initializeThemeToggle() {
    const themeSwitch = document.getElementById('themeToggleSwitch');

    if (!themeSwitch) return;

    const isDark = document.documentElement.getAttribute('data-theme') === 'dark' ||
                   !document.documentElement.hasAttribute('data-theme');

    if (isDark) {
        themeSwitch.classList.add('active');
    } else {
        themeSwitch.classList.remove('active');
    }
}

function toggleThemeDrawer() {
    const themeSwitch = document.getElementById('themeToggleSwitch');

    if (!themeSwitch) return;

    themeSwitch.classList.toggle('active');

    if (typeof toggleTheme === 'function') {
        toggleTheme();
    } else {
        const html = document.documentElement;
        const currentTheme = html.getAttribute('data-theme');

        if (currentTheme === 'light') {
            html.setAttribute('data-theme', 'dark');
            localStorage.setItem('theme', 'dark');
        } else {
            html.setAttribute('data-theme', 'light');
            localStorage.setItem('theme', 'light');
        }
    }
}

window.addEventListener('resize', function() {
    const sidebar = document.getElementById('corporateSidebar');
    const mainContent = document.querySelector('.main-content');

    if (!sidebar || !mainContent) return;

    if (window.innerWidth > 768) {
        sidebar.classList.remove('mobile-open');

        if (sidebar.classList.contains('collapsed')) {
            mainContent.style.marginLeft = '80px';
        } else {
            mainContent.style.marginLeft = '260px';
        }
    } else {
        mainContent.style.marginLeft = '0';
    }
});

document.addEventListener('DOMContentLoaded', function() {
    const sidebar = document.getElementById('corporateSidebar');
    const mainContent = document.querySelector('.main-content');

    if (sidebar && mainContent) {
        sidebar.style.transition = 'width 0.3s ease, transform 0.3s ease';
        mainContent.style.transition = 'margin-left 0.3s ease';

        if (window.innerWidth > 768) {
            if (sidebar.classList.contains('collapsed')) {
                mainContent.style.marginLeft = '80px';
            } else {
                mainContent.style.marginLeft = '260px';
            }
        }
    }
});

document.addEventListener('DOMContentLoaded', function() {
    const sidebar = document.getElementById('corporateSidebar');
    const navItems = document.querySelectorAll('.nav-item[data-tooltip]');
    
    if (!sidebar) return;
    
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.attributeName === 'class') {
                const isCollapsed = sidebar.classList.contains('collapsed');
                navItems.forEach(item => {
                    if (isCollapsed) {
                        item.setAttribute('data-tooltip', item.querySelector('.nav-item-text').textContent);
                    } else {
                        item.removeAttribute('data-tooltip');
                    }
                });
            }
        });
    });

    observer.observe(sidebar, { attributes: true });
});

document.addEventListener('DOMContentLoaded', function() {
    const navItems = document.querySelectorAll('.nav-item');

    navItems.forEach(item => {
        item.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                this.click();
            }
        });

        if (!item.getAttribute('role')) {
            item.setAttribute('role', 'button');
        }
        if (!item.getAttribute('tabindex')) {
            item.setAttribute('tabindex', '0');
        }
    });
});

let resizeTimeout;
window.addEventListener('resize', function() {
    clearTimeout(resizeTimeout);
    resizeTimeout = setTimeout(function() {
        const sidebar = document.getElementById('corporateSidebar');
        const mainContent = document.querySelector('.main-content');

        if (!sidebar || !mainContent) return;

        if (window.innerWidth > 768) {
            sidebar.classList.remove('mobile-open');

            if (sidebar.classList.contains('collapsed')) {
                mainContent.style.marginLeft = '80px';
            } else {
                mainContent.style.marginLeft = '260px';
            }
        } else {
            mainContent.style.marginLeft = '0';
        }
    }, 100);
});

function initializeFullscreenToggle() {
    const fullscreenToggle = document.getElementById('fullscreenToggle');
    const fullscreenStatus = document.getElementById('fullscreenStatus');

    if (!fullscreenToggle || !fullscreenStatus) return;

    document.addEventListener('fullscreenchange', function() {
        if (document.fullscreenElement) {
            fullscreenToggle.classList.add('active');
            fullscreenStatus.textContent = 'Ativado';
            fullscreenToggle.querySelector('.fullscreen-toggle-label i').className = 'fas fa-compress';
        } else {
            fullscreenToggle.classList.remove('active');
            fullscreenStatus.textContent = 'Desativado';
            fullscreenToggle.querySelector('.fullscreen-toggle-label i').className = 'fas fa-expand';
        }
    });
}

function toggleFullscreen() {
    if (!document.fullscreenElement) {
        document.documentElement.requestFullscreen().catch(function(err) {
        });
    } else {
        if (document.exitFullscreen) {
            document.exitFullscreen();
        }
    }
}


function initializeTimeFilter() {
    const filterButtons = document.querySelectorAll('.time-filter-btn');

    filterButtons.forEach(function(btn) {
        btn.addEventListener('click', function() {
            filterButtons.forEach(function(b) {
                b.classList.remove('active');
            });

            this.classList.add('active');

            const period = this.getAttribute('data-period');
            filterPeriod(period);
        });
    });
}

function filterPeriod(period) {
    const filterButtons = document.querySelectorAll('.time-filter-btn');

    filterButtons.forEach(function(btn) {
        btn.classList.remove('active');
        if (btn.getAttribute('data-period') === period) {
            btn.classList.add('active');
        }
    });

    const dashboard = document.querySelector('.page-wrapper');
    if (dashboard) {
        dashboard.style.opacity = '0.7';
        setTimeout(function() {
            dashboard.style.opacity = '1';
        }, 200);
    }
}

function initializeCommandPalette() {
    const overlay = document.getElementById('commandPaletteOverlay');
    const searchInput = document.getElementById('commandPaletteSearch');
    const paletteItems = document.querySelectorAll('.command-palette-item');
    let selectedIndex = 0;

    if (!overlay || !searchInput) return;

    document.addEventListener('keydown', function(e) {
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            openCommandPalette();
        }

        if (overlay.classList.contains('active')) {
            if (e.key === 'Escape') {
                closeCommandPalette();
            } else if (e.key === 'ArrowDown') {
                e.preventDefault();
                selectedIndex = (selectedIndex + 1) % paletteItems.length;
                updateSelectedPaletteItem(paletteItems, selectedIndex);
            } else if (e.key === 'ArrowUp') {
                e.preventDefault();
                selectedIndex = (selectedIndex - 1 + paletteItems.length) % paletteItems.length;
                updateSelectedPaletteItem(paletteItems, selectedIndex);
            } else if (e.key === 'Enter') {
                e.preventDefault();
                const selectedItem = paletteItems[selectedIndex];
                if (selectedItem) {
                    selectedItem.click();
                }
            }
        }
    });

    searchInput.addEventListener('input', function() {
        const query = this.value.toLowerCase();
        paletteItems.forEach(function(item) {
            const title = item.querySelector('.command-palette-item-title').textContent.toLowerCase();
            const subtitle = item.querySelector('.command-palette-item-subtitle').textContent.toLowerCase();
            const matches = title.includes(query) || subtitle.includes(query);
            item.style.display = matches ? 'flex' : 'none';
        });
    });
}

function openCommandPalette() {
    const overlay = document.getElementById('commandPaletteOverlay');
    const searchInput = document.getElementById('commandPaletteSearch');

    if (overlay && searchInput) {
        overlay.classList.add('active');
        searchInput.value = '';
        searchInput.focus();

        const paletteItems = document.querySelectorAll('.command-palette-item');
        paletteItems.forEach(function(item) {
            item.style.display = 'flex';
            item.classList.remove('selected');
        });

        if (paletteItems.length > 0) {
            paletteItems[0].classList.add('selected');
        }
    }
}

function closeCommandPalette(event) {
    const overlay = document.getElementById('commandPaletteOverlay');

    if (overlay) {
        overlay.classList.remove('active');
    }
}

function updateSelectedPaletteItem(items, selectedIndex) {
    items.forEach(function(item, index) {
        item.classList.remove('selected');
        if (index === selectedIndex) {
            item.classList.add('selected');
            item.scrollIntoView({ block: 'nearest' });
        }
    });
}