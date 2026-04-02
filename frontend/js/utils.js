/**
 * 深觅 AI Coach - 工具函数模块
 * DeepSearch AI Coach - Utilities Module
 */

// ============================================
// 1. 日期时间工具
// ============================================

/**
 * 格式化日期
 * @param {string|Date} date - 日期字符串或Date对象
 * @param {string} format - 格式模板 (default: 'YYYY-MM-DD')
 * @returns {string} 格式化后的日期字符串
 */
function formatDate(date, format = 'YYYY-MM-DD') {
    const d = new Date(date);
    const year = d.getFullYear();
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    const hours = String(d.getHours()).padStart(2, '0');
    const minutes = String(d.getMinutes()).padStart(2, '0');
    const seconds = String(d.getSeconds()).padStart(2, '0');

    return format
        .replace('YYYY', year)
        .replace('MM', month)
        .replace('DD', day)
        .replace('HH', hours)
        .replace('mm', minutes)
        .replace('ss', seconds);
}

/**
 * 获取相对时间描述
 * @param {string|Date} date - 日期
 * @returns {string} 相对时间描述
 */
function getRelativeTime(date) {
    const now = new Date();
    const target = new Date(date);
    const diff = now - target;
    const seconds = Math.floor(diff / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);

    if (seconds < 60) return '刚刚';
    if (minutes < 60) return `${minutes}分钟前`;
    if (hours < 24) return `${hours}小时前`;
    if (days < 7) return `${days}天前`;
    return formatDate(date);
}

// ============================================
// 2. 数据验证工具
// ============================================

/**
 * 验证邮箱格式
 * @param {string} email - 邮箱地址
 * @returns {boolean} 是否有效
 */
function isValidEmail(email) {
    const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return regex.test(email);
}

/**
 * 验证密码强度
 * @param {string} password - 密码
 * @returns {object} 验证结果
 */
function validatePassword(password) {
    const result = {
        valid: false,
        strength: 0,
        message: '',
        checks: {
            length: password.length >= 6 && password.length <= 20,
            hasNumber: /\d/.test(password),
            hasLower: /[a-z]/.test(password),
            hasUpper: /[A-Z]/.test(password),
            hasSpecial: /[!@#$%^&*(),.?":{}|<>]/.test(password)
        }
    };

    // 计算强度
    result.strength = Object.values(result.checks).filter(Boolean).length;

    if (!result.checks.length) {
        result.message = '密码长度应为6-20位';
    } else if (result.strength < 2) {
        result.message = '密码强度较弱，建议包含数字和字母';
    } else if (result.strength < 4) {
        result.message = '密码强度中等';
        result.valid = true;
    } else {
        result.message = '密码强度强';
        result.valid = true;
    }

    return result;
}

/**
 * 验证手机号
 * @param {string} phone - 手机号
 * @returns {boolean} 是否有效
 */
function isValidPhone(phone) {
    const regex = /^1[3-9]\d{9}$/;
    return regex.test(phone);
}

// ============================================
// 3. 表单验证工具
// ============================================

/**
 * 表单验证器
 */
class FormValidator {
    constructor(form) {
        this.form = form;
        this.errors = {};
    }

    /**
     * 添加验证规则
     * @param {string} field - 字段名
     * @param {Array} rules - 验证规则数组
     */
    addRules(field, rules) {
        this.rules = this.rules || {};
        this.rules[field] = rules;
    }

    /**
     * 验证单个字段
     * @param {string} field - 字段名
     * @param {*} value - 字段值
     * @returns {string|null} 错误信息或null
     */
    validateField(field, value) {
        const rules = this.rules?.[field];
        if (!rules) return null;

        for (const rule of rules) {
            const error = this.checkRule(value, rule);
            if (error) return error;
        }
        return null;
    }

    /**
     * 检查规则
     * @param {*} value - 值
     * @param {object} rule - 规则对象
     * @returns {string|null} 错误信息
     */
    checkRule(value, rule) {
        switch (rule.type) {
            case 'required':
                if (!value || (typeof value === 'string' && !value.trim())) {
                    return rule.message || '此项为必填项';
                }
                break;
            case 'email':
                if (value && !isValidEmail(value)) {
                    return rule.message || '请输入有效的邮箱地址';
                }
                break;
            case 'min':
                if (value && value.length < rule.value) {
                    return rule.message || `最少需要${rule.value}个字符`;
                }
                break;
            case 'max':
                if (value && value.length > rule.value) {
                    return rule.message || `最多${rule.value}个字符`;
                }
                break;
            case 'pattern':
                if (value && !rule.value.test(value)) {
                    return rule.message || '格式不正确';
                }
                break;
            case 'match':
                const matchValue = this.form.querySelector(`[name="${rule.field}"]`)?.value;
                if (value !== matchValue) {
                    return rule.message || '两次输入不一致';
                }
                break;
        }
        return null;
    }

    /**
     * 验证整个表单
     * @returns {boolean} 是否通过验证
     */
    validate() {
        this.errors = {};
        let isValid = true;

        for (const field in this.rules) {
            const input = this.form.querySelector(`[name="${field}"]`);
            if (input) {
                const error = this.validateField(field, input.value);
                if (error) {
                    this.errors[field] = error;
                    isValid = false;
                }
            }
        }

        return isValid;
    }

    /**
     * 显示错误信息
     * @param {string} field - 字段名
     * @param {string} message - 错误信息
     */
    showError(field, message) {
        const input = this.form.querySelector(`[name="${field}"]`);
        if (!input) return;

        // 添加错误样式
        input.classList.add('form-control--error');

        // 查找或创建错误提示元素
        let errorEl = input.parentElement.querySelector('.form-error');
        if (!errorEl) {
            errorEl = document.createElement('div');
            errorEl.className = 'form-error';
            input.parentElement.appendChild(errorEl);
        }
        errorEl.textContent = message;
    }

    /**
     * 清除错误信息
     * @param {string} field - 字段名
     */
    clearError(field) {
        const input = this.form.querySelector(`[name="${field}"]`);
        if (!input) return;

        input.classList.remove('form-control--error');
        const errorEl = input.parentElement.querySelector('.form-error');
        if (errorEl) {
            errorEl.remove();
        }
    }

    /**
     * 清除所有错误
     */
    clearAllErrors() {
        for (const field in this.errors) {
            this.clearError(field);
        }
        this.errors = {};
    }
}

// ============================================
// 4. UI 辅助函数
// ============================================

/**
 * 显示 Toast 提示
 * @param {string} message - 消息内容
 * @param {string} type - 类型: success, warning, error, info
 * @param {number} duration - 显示时长(毫秒)
 */
function showToast(message, type = 'info', duration = 3000) {
    // 创建或获取 toast 容器
    let container = document.querySelector('.toast-container');
    if (!container) {
        container = document.createElement('div');
        container.className = 'toast-container';
        document.body.appendChild(container);
    }

    // 创建 toast 元素
    const toast = document.createElement('div');
    toast.className = `toast toast--${type}`;

    // 图标
    const icons = {
        success: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 6L9 17l-5-5"/></svg>',
        warning: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/></svg>',
        error: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M15 9l-6 6m0-6l6 6"/></svg>',
        info: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4m0-4h.01"/></svg>'
    };

    toast.innerHTML = `
        <span class="toast__icon">${icons[type]}</span>
        <div class="toast__content">
            <div class="toast__message">${message}</div>
        </div>
        <button class="toast__close" onclick="this.parentElement.remove()">×</button>
    `;

    container.appendChild(toast);

    // 自动移除
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(-20px)';
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

/**
 * 显示加载状态
 * @param {HTMLElement} element - 目标元素
 * @param {boolean} loading - 是否加载中
 */
function setLoading(element, loading) {
    if (loading) {
        element.classList.add('btn--loading');
        element.disabled = true;
    } else {
        element.classList.remove('btn--loading');
        element.disabled = false;
    }
}

/**
 * 防抖函数
 * @param {Function} fn - 目标函数
 * @param {number} delay - 延迟时间
 * @returns {Function} 防抖后的函数
 */
function debounce(fn, delay = 300) {
    let timer = null;
    return function (...args) {
        clearTimeout(timer);
        timer = setTimeout(() => fn.apply(this, args), delay);
    };
}

/**
 * 节流函数
 * @param {Function} fn - 目标函数
 * @param {number} limit - 限制时间
 * @returns {Function} 节流后的函数
 */
function throttle(fn, limit = 300) {
    let inThrottle;
    return function (...args) {
        if (!inThrottle) {
            fn.apply(this, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// ============================================
// 5. 本地存储工具
// ============================================

/**
 * 本地存储封装
 */
const storage = {
    /**
     * 设置值
     * @param {string} key - 键
     * @param {*} value - 值
     */
    set(key, value) {
        try {
            localStorage.setItem(key, JSON.stringify(value));
        } catch (e) {
            console.error('Storage set error:', e);
        }
    },

    /**
     * 获取值
     * @param {string} key - 键
     * @param {*} defaultValue - 默认值
     * @returns {*} 存储的值
     */
    get(key, defaultValue = null) {
        try {
            const item = localStorage.getItem(key);
            return item ? JSON.parse(item) : defaultValue;
        } catch (e) {
            console.error('Storage get error:', e);
            return defaultValue;
        }
    },

    /**
     * 删除值
     * @param {string} key - 键
     */
    remove(key) {
        try {
            localStorage.removeItem(key);
        } catch (e) {
            console.error('Storage remove error:', e);
        }
    },

    /**
     * 清空存储
     */
    clear() {
        try {
            localStorage.clear();
        } catch (e) {
            console.error('Storage clear error:', e);
        }
    }
};

// ============================================
// 6. 其他工具函数
// ============================================

/**
 * 生成唯一ID
 * @returns {string} 唯一ID
 */
function generateId() {
    return Date.now().toString(36) + Math.random().toString(36).substr(2);
}

/**
 * 深拷贝对象
 * @param {*} obj - 目标对象
 * @returns {*} 拷贝后的对象
 */
function deepClone(obj) {
    if (obj === null || typeof obj !== 'object') return obj;
    if (obj instanceof Date) return new Date(obj);
    if (obj instanceof Array) return obj.map(item => deepClone(item));
    if (obj instanceof Object) {
        const cloned = {};
        for (const key in obj) {
            if (obj.hasOwnProperty(key)) {
                cloned[key] = deepClone(obj[key]);
            }
        }
        return cloned;
    }
}

/**
 * 截断文本
 * @param {string} text - 原文本
 * @param {number} maxLength - 最大长度
 * @param {string} suffix - 后缀
 * @returns {string} 截断后的文本
 */
function truncateText(text, maxLength = 100, suffix = '...') {
    if (!text || text.length <= maxLength) return text;
    return text.substring(0, maxLength).trim() + suffix;
}

/**
 * 导出模块
 */
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        formatDate,
        getRelativeTime,
        isValidEmail,
        validatePassword,
        isValidPhone,
        FormValidator,
        showToast,
        setLoading,
        debounce,
        throttle,
        storage,
        generateId,
        deepClone,
        truncateText
    };
}
