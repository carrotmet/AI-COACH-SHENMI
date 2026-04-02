/**
 * 深觅 AI Coach - 主逻辑模块
 * DeepSearch AI Coach - Main Module
 * 
 * 处理全局交互、导航和通用功能
 */

// ============================================
// 1. 移动端导航菜单
// ============================================

/**
 * 初始化移动端菜单
 */
function initMobileMenu() {
    const menuToggle = document.querySelector('.header__menu-toggle');
    const mobileMenu = document.querySelector('.mobile-menu');
    const menuClose = document.querySelector('.mobile-menu__close');
    const menuOverlay = document.querySelector('.mobile-menu__overlay');

    if (!menuToggle || !mobileMenu) return;

    // 打开菜单
    menuToggle.addEventListener('click', () => {
        mobileMenu.classList.add('mobile-menu--open');
        document.body.style.overflow = 'hidden';
    });

    // 关闭菜单
    const closeMenu = () => {
        mobileMenu.classList.remove('mobile-menu--open');
        document.body.style.overflow = '';
    };

    if (menuClose) menuClose.addEventListener('click', closeMenu);
    if (menuOverlay) menuOverlay.addEventListener('click', closeMenu);

    // 点击菜单项后关闭
    mobileMenu.querySelectorAll('a').forEach(link => {
        link.addEventListener('click', closeMenu);
    });
}

// ============================================
// 2. 滚动效果
// ============================================

/**
 * 初始化滚动效果
 */
function initScrollEffects() {
    const header = document.querySelector('.header');
    if (!header) return;

    let lastScrollY = 0;
    let ticking = false;

    const updateHeader = () => {
        const scrollY = window.scrollY;

        // 添加/移除滚动样式
        if (scrollY > 10) {
            header.classList.add('header--scrolled');
        } else {
            header.classList.remove('header--scrolled');
        }

        // 隐藏/显示头部（向下滚动隐藏，向上滚动显示）
        if (scrollY > lastScrollY && scrollY > 100) {
            header.classList.add('header--hidden');
        } else {
            header.classList.remove('header--hidden');
        }

        lastScrollY = scrollY;
        ticking = false;
    };

    window.addEventListener('scroll', () => {
        if (!ticking) {
            requestAnimationFrame(updateHeader);
            ticking = true;
        }
    }, { passive: true });
}

// ============================================
// 3. 平滑滚动
// ============================================

/**
 * 初始化平滑滚动
 */
function initSmoothScroll() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            const targetId = this.getAttribute('href');
            if (targetId === '#') return;

            const targetElement = document.querySelector(targetId);
            if (targetElement) {
                e.preventDefault();
                targetElement.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
}

// ============================================
// 4. 动画效果
// ============================================

/**
 * 初始化滚动动画
 */
function initScrollAnimations() {
    const animatedElements = document.querySelectorAll('[data-animate]');
    
    if (animatedElements.length === 0) return;

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const element = entry.target;
                const animation = element.dataset.animate;
                const delay = element.dataset.animateDelay || 0;

                setTimeout(() => {
                    element.classList.add(`animate--${animation}`);
                    element.classList.add('animate--visible');
                }, delay);

                observer.unobserve(element);
            }
        });
    }, {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    });

    animatedElements.forEach(el => observer.observe(el));
}

// ============================================
// 5. 表单交互
// ============================================

/**
 * 初始化表单交互
 */
function initFormInteractions() {
    // 输入框焦点效果
    document.querySelectorAll('.form-control').forEach(input => {
        const formGroup = input.closest('.form-group');
        if (!formGroup) return;

        input.addEventListener('focus', () => {
            formGroup.classList.add('form-group--focused');
        });

        input.addEventListener('blur', () => {
            formGroup.classList.remove('form-group--focused');
        });
    });

    // 密码可见性切换
    document.querySelectorAll('.password-toggle').forEach(toggle => {
        toggle.addEventListener('click', () => {
            const input = toggle.previousElementSibling;
            const type = input.type === 'password' ? 'text' : 'password';
            input.type = type;
            toggle.classList.toggle('password-toggle--visible');
        });
    });
}

// ============================================
// 6. 模态框
// ============================================

/**
 * 显示模态框
 * @param {string} id - 模态框ID
 */
function showModal(id) {
    const modal = document.getElementById(id);
    if (modal) {
        modal.classList.add('modal--open');
        document.body.style.overflow = 'hidden';
    }
}

/**
 * 隐藏模态框
 * @param {string} id - 模态框ID
 */
function hideModal(id) {
    const modal = document.getElementById(id);
    if (modal) {
        modal.classList.remove('modal--open');
        document.body.style.overflow = '';
    }
}

/**
 * 初始化模态框
 */
function initModals() {
    // 关闭按钮
    document.querySelectorAll('.modal__close, .modal__overlay').forEach(el => {
        el.addEventListener('click', (e) => {
            const modal = e.target.closest('.modal-container');
            if (modal) {
                modal.classList.remove('modal--open');
                document.body.style.overflow = '';
            }
        });
    });

    // ESC 键关闭
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            document.querySelectorAll('.modal--open').forEach(modal => {
                modal.classList.remove('modal--open');
            });
            document.body.style.overflow = '';
        }
    });
}

// ============================================
// 7. 标签页切换
// ============================================

/**
 * 初始化标签页
 */
function initTabs() {
    document.querySelectorAll('.tabs').forEach(tabsContainer => {
        const tabs = tabsContainer.querySelectorAll('.tab');
        const tabPanels = document.querySelectorAll(`[data-tabs="${tabsContainer.dataset.tabGroup}"]`);

        tabs.forEach(tab => {
            tab.addEventListener('click', () => {
                // 移除所有活动状态
                tabs.forEach(t => t.classList.remove('tab--active'));
                tabPanels.forEach(p => p.classList.remove('tab-panel--active'));

                // 添加当前活动状态
                tab.classList.add('tab--active');
                const targetPanel = document.querySelector(tab.dataset.target);
                if (targetPanel) {
                    targetPanel.classList.add('tab-panel--active');
                }
            });
        });
    });
}

// ============================================
// 8. 主题切换
// ============================================

/**
 * 初始化主题切换
 */
function initThemeToggle() {
    const themeToggle = document.querySelector('.theme-toggle');
    if (!themeToggle) return;

    // 检查系统偏好
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    const savedTheme = localStorage.getItem('theme');
    
    if (savedTheme === 'dark' || (!savedTheme && prefersDark)) {
        document.body.classList.add('dark-mode');
    }

    themeToggle.addEventListener('click', () => {
        document.body.classList.toggle('dark-mode');
        const isDark = document.body.classList.contains('dark-mode');
        localStorage.setItem('theme', isDark ? 'dark' : 'light');
    });
}

// ============================================
// 9. 懒加载图片
// ============================================

/**
 * 初始化图片懒加载
 */
function initLazyLoad() {
    const lazyImages = document.querySelectorAll('img[data-src]');
    
    if (lazyImages.length === 0) return;

    const imageObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.dataset.src;
                img.removeAttribute('data-src');
                imageObserver.unobserve(img);
            }
        });
    });

    lazyImages.forEach(img => imageObserver.observe(img));
}

// ============================================
// 10. 工具函数
// ============================================

/**
 * 复制文本到剪贴板
 * @param {string} text - 要复制的文本
 */
async function copyToClipboard(text) {
    try {
        await navigator.clipboard.writeText(text);
        showToast('已复制到剪贴板', 'success');
    } catch (err) {
        // 降级方案
        const textarea = document.createElement('textarea');
        textarea.value = text;
        textarea.style.position = 'fixed';
        textarea.style.opacity = '0';
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand('copy');
        document.body.removeChild(textarea);
        showToast('已复制到剪贴板', 'success');
    }
}

/**
 * 分享内容
 * @param {object} data - 分享数据
 */
async function shareContent(data) {
    if (navigator.share) {
        try {
            await navigator.share(data);
        } catch (err) {
            if (err.name !== 'AbortError') {
                console.error('分享失败:', err);
            }
        }
    } else {
        // 降级：复制链接
        copyToClipboard(data.url || window.location.href);
    }
}

// ============================================
// 11. 页面加载完成后初始化
// ============================================

document.addEventListener('DOMContentLoaded', () => {
    initMobileMenu();
    initScrollEffects();
    initSmoothScroll();
    initScrollAnimations();
    initFormInteractions();
    initModals();
    initTabs();
    initThemeToggle();
    initLazyLoad();
});

// ============================================
// 12. 导出全局函数
// ============================================

window.showModal = showModal;
window.hideModal = hideModal;
window.copyToClipboard = copyToClipboard;
window.shareContent = shareContent;

// 模块导出
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        initMobileMenu,
        initScrollEffects,
        initSmoothScroll,
        initScrollAnimations,
        initFormInteractions,
        initModals,
        initTabs,
        initThemeToggle,
        initLazyLoad,
        showModal,
        hideModal,
        copyToClipboard,
        shareContent
    };
}
