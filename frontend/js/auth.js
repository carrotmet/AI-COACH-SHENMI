/**
 * 深觅 AI Coach - 认证管理模块
 * DeepSearch AI Coach - Authentication Module
 * 
 * 处理用户登录状态、Token管理和权限验证
 */

/**
 * 认证状态管理器
 */
class AuthManager {
    constructor() {
        this.currentUser = null;
        this.isAuthenticated = false;
        this.listeners = [];
    }

    /**
     * 初始化认证状态
     */
    async init() {
        const token = localStorage.getItem('access_token');
        if (token) {
            try {
                await this.fetchUserInfo();
                this.isAuthenticated = true;
                this.notifyListeners();
            } catch (error) {
                console.error('初始化认证状态失败:', error);
                this.logout();
            }
        }
    }

    /**
     * 用户注册
     * @param {string} email - 邮箱
     * @param {string} password - 密码
     * @param {string} nickname - 昵称
     * @returns {Promise<object>} 注册结果
     */
    async register(email, password, nickname) {
        try {
            const data = await api.auth.register(email, password, nickname);
            
            // 保存 Token
            localStorage.setItem('access_token', data.access_token);
            localStorage.setItem('refresh_token', data.refresh_token);
            
            // 设置用户信息
            this.currentUser = {
                userId: data.user_id,
                email: data.email,
                nickname: data.nickname,
                createdAt: data.created_at
            };
            this.isAuthenticated = true;
            
            this.notifyListeners();
            
            return { success: true, data };
        } catch (error) {
            console.error('注册失败:', error);
            return { 
                success: false, 
                error: error.message || '注册失败，请稍后重试'
            };
        }
    }

    /**
     * 用户登录
     * @param {string} email - 邮箱
     * @param {string} password - 密码
     * @returns {Promise<object>} 登录结果
     */
    async login(email, password) {
        try {
            const data = await api.auth.login(email, password);
            
            // 保存 Token
            localStorage.setItem('access_token', data.access_token);
            localStorage.setItem('refresh_token', data.refresh_token);
            
            // 设置用户信息
            this.currentUser = {
                userId: data.user_id,
                email: data.email,
                nickname: data.nickname
            };
            this.isAuthenticated = true;
            
            this.notifyListeners();
            
            return { success: true, data };
        } catch (error) {
            console.error('登录失败:', error);
            let errorMsg = '登录失败，请稍后重试';
            
            if (error.code === 1002) {
                errorMsg = '用户不存在，请检查邮箱地址';
            } else if (error.code === 1003) {
                errorMsg = '密码错误，请重新输入';
            }
            
            return { success: false, error: errorMsg };
        }
    }

    /**
     * 用户登出
     */
    async logout() {
        try {
            // 调用登出 API
            await api.auth.logout();
        } catch (error) {
            console.error('登出 API 调用失败:', error);
        } finally {
            // 清除本地存储
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            
            // 重置状态
            this.currentUser = null;
            this.isAuthenticated = false;
            
            this.notifyListeners();
        }
    }

    /**
     * 获取用户信息
     */
    async fetchUserInfo() {
        try {
            const data = await api.user.getMe();
            this.currentUser = {
                userId: data.user_id,
                email: data.email,
                nickname: data.nickname,
                avatar: data.avatar,
                createdAt: data.created_at,
                subscription: data.subscription,
                usageStats: data.usage_stats
            };
            return this.currentUser;
        } catch (error) {
            console.error('获取用户信息失败:', error);
            throw error;
        }
    }

    /**
     * 更新用户信息
     * @param {object} data - 更新数据
     */
    async updateUserInfo(data) {
        try {
            const result = await api.user.updateMe(data);
            this.currentUser = { ...this.currentUser, ...data };
            this.notifyListeners();
            return { success: true, data: result };
        } catch (error) {
            console.error('更新用户信息失败:', error);
            return { success: false, error: error.message };
        }
    }

    /**
     * 检查是否已登录
     * @returns {boolean}
     */
    checkAuth() {
        return this.isAuthenticated && localStorage.getItem('access_token');
    }

    /**
     * 获取当前用户
     * @returns {object|null}
     */
    getUser() {
        return this.currentUser;
    }

    /**
     * 要求登录
     * @param {string} redirectUrl - 登录后跳转地址
     */
    requireAuth(redirectUrl = window.location.href) {
        if (!this.checkAuth()) {
            // 保存当前页面地址
            sessionStorage.setItem('redirect_after_login', redirectUrl);
            // 跳转到登录页
            window.location.href = '/login.html';
            return false;
        }
        return true;
    }

    /**
     * 添加状态监听器
     * @param {Function} listener - 监听器函数
     */
    addListener(listener) {
        this.listeners.push(listener);
    }

    /**
     * 移除状态监听器
     * @param {Function} listener - 监听器函数
     */
    removeListener(listener) {
        this.listeners = this.listeners.filter(l => l !== listener);
    }

    /**
     * 通知所有监听器
     */
    notifyListeners() {
        this.listeners.forEach(listener => {
            try {
                listener(this.isAuthenticated, this.currentUser);
            } catch (error) {
                console.error('监听器执行失败:', error);
            }
        });
    }
}

// 创建全局认证管理器实例
const auth = new AuthManager();

/**
 * 更新页面头部用户状态
 */
function updateHeaderUserState() {
    const userActions = document.querySelector('.header__user-actions');
    if (!userActions) return;

    if (auth.checkAuth()) {
        const user = auth.getUser();
        userActions.innerHTML = `
            <div class="header__user-menu dropdown">
                <button class="header__user-btn dropdown__trigger">
                    <span class="header__user-avatar">${user.nickname?.[0] || 'U'}</span>
                    <span class="header__user-name hidden-sm">${user.nickname}</span>
                    <svg class="icon icon--sm" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="m6 9 6 6 6-6"/>
                    </svg>
                </button>
                <div class="dropdown__menu">
                    <a href="/user/index.html" class="dropdown__item">
                        <svg class="icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                            <circle cx="12" cy="7" r="4"/>
                        </svg>
                        个人中心
                    </a>
                    <a href="/assessment/index.html" class="dropdown__item">
                        <svg class="icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M9 11l3 3L22 4"/>
                            <path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/>
                        </svg>
                        我的测评
                    </a>
                    <div class="dropdown__divider"></div>
                    <button class="dropdown__item dropdown__item--danger" onclick="auth.logout(); window.location.href='/';">
                        <svg class="icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
                            <polyline points="16 17 21 12 16 7"/>
                            <line x1="21" y1="12" x2="9" y2="12"/>
                        </svg>
                        退出登录
                    </button>
                </div>
            </div>
        `;
        
        // 初始化下拉菜单
        initDropdowns();
    } else {
        userActions.innerHTML = `
            <a href="/login.html" class="btn btn--ghost btn--md">登录</a>
            <a href="/register.html" class="btn btn--primary btn--md hidden-sm">注册</a>
        `;
    }
}

/**
 * 初始化下拉菜单
 */
function initDropdowns() {
    document.querySelectorAll('.dropdown').forEach(dropdown => {
        const trigger = dropdown.querySelector('.dropdown__trigger');
        const menu = dropdown.querySelector('.dropdown__menu');
        
        if (!trigger || !menu) return;

        trigger.addEventListener('click', (e) => {
            e.stopPropagation();
            dropdown.classList.toggle('dropdown--open');
        });

        // 点击外部关闭
        document.addEventListener('click', () => {
            dropdown.classList.remove('dropdown--open');
        });
    });
}

// 添加认证状态监听器
auth.addListener((isAuthenticated, user) => {
    updateHeaderUserState();
});

// 页面加载时初始化
document.addEventListener('DOMContentLoaded', () => {
    auth.init();
});

// 全局暴露
window.auth = auth;

// 模块导出
if (typeof module !== 'undefined' && module.exports) {
    module.exports = auth;
}
