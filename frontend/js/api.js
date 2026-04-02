/**
 * 深觅 AI Coach - API 封装模块
 * DeepSearch AI Coach - API Module
 * 
 * 封装所有后端 API 调用，统一处理请求和响应
 */

// API 基础配置
const API_CONFIG = {
    BASE_URL: '/api/v1',
    TIMEOUT: 30000,
    RETRY_COUNT: 3,
    RETRY_DELAY: 1000
};

/**
 * API 错误类
 */
class APIError extends Error {
    constructor(message, code, status, detail = null) {
        super(message);
        this.name = 'APIError';
        this.code = code;
        this.status = status;
        this.detail = detail;
    }
}

/**
 * 获取认证Token
 * @returns {string|null} Access Token
 */
function getAccessToken() {
    return localStorage.getItem('access_token');
}

/**
 * 获取刷新Token
 * @returns {string|null} Refresh Token
 */
function getRefreshToken() {
    return localStorage.getItem('refresh_token');
}

/**
 * 设置Token
 * @param {string} accessToken - Access Token
 * @param {string} refreshToken - Refresh Token
 */
function setTokens(accessToken, refreshToken) {
    localStorage.setItem('access_token', accessToken);
    localStorage.setItem('refresh_token', refreshToken);
}

/**
 * 清除Token
 */
function clearTokens() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
}

/**
 * 刷新 Access Token
 * @returns {Promise<string>} 新的 Access Token
 */
async function refreshAccessToken() {
    const refreshToken = getRefreshToken();
    if (!refreshToken) {
        throw new APIError('未登录', 1006, 401);
    }

    try {
        const response = await fetch(`${API_CONFIG.BASE_URL}/auth/refresh`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ refresh_token: refreshToken })
        });

        const data = await response.json();

        if (data.code === 200) {
            setTokens(data.data.access_token, data.data.refresh_token);
            return data.data.access_token;
        } else {
            clearTokens();
            throw new APIError(data.message, data.code, response.status);
        }
    } catch (error) {
        clearTokens();
        throw error;
    }
}

/**
 * 发送 HTTP 请求
 * @param {string} url - 请求路径
 * @param {object} options - 请求选项
 * @param {boolean} retry - 是否重试
 * @returns {Promise<any>} 响应数据
 */
async function request(url, options = {}, retry = true) {
    const fullUrl = url.startsWith('http') ? url : `${API_CONFIG.BASE_URL}${url}`;
    
    // 默认请求配置
    const defaultOptions = {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
    };

    // 合并配置
    const config = { ...defaultOptions, ...options };
    
    // 添加认证头
    const token = getAccessToken();
    if (token) {
        config.headers['Authorization'] = `Bearer ${token}`;
    }

    // 处理请求体
    if (config.body && typeof config.body === 'object' && !(config.body instanceof FormData)) {
        config.body = JSON.stringify(config.body);
    }

    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), API_CONFIG.TIMEOUT);
        config.signal = controller.signal;

        const response = await fetch(fullUrl, config);
        clearTimeout(timeoutId);

        // 处理 401 错误，尝试刷新 Token
        if (response.status === 401 && retry) {
            try {
                const newToken = await refreshAccessToken();
                config.headers['Authorization'] = `Bearer ${newToken}`;
                const retryResponse = await fetch(fullUrl, config);
                const retryData = await retryResponse.json();
                return handleResponse(retryData, retryResponse);
            } catch (refreshError) {
                // 刷新失败，跳转到登录页
                window.location.href = '/login.html';
                throw refreshError;
            }
        }

        const data = await response.json();
        return handleResponse(data, response);

    } catch (error) {
        if (error.name === 'AbortError') {
            throw new APIError('请求超时，请稍后重试', -1, 0);
        }
        throw error;
    }
}

/**
 * 处理响应数据
 * @param {object} data - 响应数据
 * @param {Response} response - 响应对象
 * @returns {any} 处理后的数据
 */
function handleResponse(data, response) {
    // 调试日志：记录API响应
    if (data && typeof data.code === 'number' && data.code !== 200 && data.code !== 201) {
        console.error('[API错误] 响应:', {
            code: data.code,
            message: data.message,
            detail: data.detail,
            status: response.status,
            url: response.url
        });
    }
    
    // 统一响应格式: {code, message, data}
    if (data && typeof data.code === 'number') {
        if (response.ok && (data.code === 200 || data.code === 201)) {
            return data.data;
        }
        throw new APIError(
            data.message || '请求失败',
            data.code,
            response.status,
            data.detail
        );
    }
    
    // 直接返回模型格式 (如 assessments 接口)
    if (response.ok) {
        return data;
    }

    throw new APIError(
        data.message || '请求失败',
        data.code || -1,
        response.status,
        data.detail
    );
}

// ============================================
// 认证相关 API
// ============================================

const authAPI = {
    /**
     * 用户注册
     * @param {string} email - 邮箱
     * @param {string} password - 密码
     * @param {string} nickname - 昵称
     * @returns {Promise<object>} 注册结果
     */
    register(email, password, nickname) {
        return request('/auth/register', {
            method: 'POST',
            body: { email, password, nickname }
        });
    },

    /**
     * 用户登录
     * @param {string} email - 邮箱
     * @param {string} password - 密码
     * @returns {Promise<object>} 登录结果
     */
    login(email, password) {
        return request('/auth/login', {
            method: 'POST',
            body: { email, password }
        });
    },

    /**
     * 用户登出
     * @returns {Promise<object>} 登出结果
     */
    logout() {
        return request('/auth/logout', {
            method: 'POST'
        });
    },

    /**
     * 刷新 Token
     * @returns {Promise<object>} 刷新结果
     */
    refresh() {
        return request('/auth/refresh', {
            method: 'POST',
            body: { refresh_token: getRefreshToken() }
        });
    }
};

// ============================================
// 用户相关 API
// ============================================

const userAPI = {
    /**
     * 获取当前用户信息
     * @returns {Promise<object>} 用户信息
     */
    getMe() {
        return request('/users/me');
    },

    /**
     * 更新用户信息
     * @param {object} data - 更新数据
     * @returns {Promise<object>} 更新结果
     */
    updateMe(data) {
        return request('/users/me', {
            method: 'PUT',
            body: data
        });
    },

    /**
     * 修改密码
     * @param {string} oldPassword - 旧密码
     * @param {string} newPassword - 新密码
     * @returns {Promise<object>} 修改结果
     */
    changePassword(oldPassword, newPassword) {
        return request('/users/me/password', {
            method: 'PUT',
            body: { old_password: oldPassword, new_password: newPassword }
        });
    },

    /**
     * 获取用户测评历史
     * @param {number} page - 页码
     * @param {number} limit - 每页数量
     * @returns {Promise<object>} 测评历史
     */
    getAssessments(page = 1, limit = 10) {
        return request(`/users/me/assessments?page=${page}&limit=${limit}`);
    },

    /**
     * 获取用户对话历史
     * @param {number} page - 页码
     * @param {number} limit - 每页数量
     * @returns {Promise<object>} 对话历史
     */
    getConversations(page = 1, limit = 10) {
        return request(`/users/me/conversations?page=${page}&limit=${limit}`);
    }
};

// ============================================
// 测评相关 API
// ============================================

const assessmentAPI = {
    /**
     * 创建测评
     * @param {string} type - 测评类型 (via_strengths/via_strengths_full)
     * @param {string} language - 语言
     * @returns {Promise<object>} 测评信息
     */
    create(type = 'via_strengths', language = 'zh') {
        return request('/assessments', {
            method: 'POST',
            body: { type, language }
        });
    },

    /**
     * 获取测评题目
     * @param {string} assessmentId - 测评ID
     * @returns {Promise<object>} 题目信息
     */
    getQuestions(assessmentId) {
        return request(`/assessments/${assessmentId}/questions`);
    },

    /**
     * 提交答案
     * @param {string} assessmentId - 测评ID
     * @param {number} questionId - 题目ID
     * @param {number} score - 得分 1-5
     * @returns {Promise<object>} 提交结果
     */
    submitAnswer(assessmentId, questionId, score) {
        return request(`/assessments/${assessmentId}/answers`, {
            method: 'POST',
            body: { question_id: questionId, score }
        });
    },

    /**
     * 获取测评进度
     * @param {string} assessmentId - 测评ID
     * @returns {Promise<object>} 进度信息
     */
    getProgress(assessmentId) {
        return request(`/assessments/${assessmentId}/progress`);
    },

    /**
     * 获取测评结果
     * @param {string} assessmentId - 测评ID
     * @returns {Promise<object>} 测评结果
     */
    getResult(assessmentId) {
        return request(`/assessments/${assessmentId}/result`);
    },

    /**
     * 删除测评
     * @param {string} assessmentId - 测评ID
     * @returns {Promise<object>} 删除结果
     */
    delete(assessmentId) {
        return request(`/assessments/${assessmentId}`, {
            method: 'DELETE'
        });
    }
};

// ============================================
// 对话相关 API
// ============================================

const conversationAPI = {
    /**
     * 创建对话
     * @param {string} title - 对话标题
     * @param {object} context - 对话上下文
     * @returns {Promise<object>} 对话信息
     */
    create(title = '', context = {}) {
        return request('/conversations', {
            method: 'POST',
            body: { title, context }
        });
    },

    /**
     * 获取对话列表
     * @returns {Promise<Array>} 对话列表
     */
    getList() {
        return request('/conversations');
    },

    /**
     * 获取对话详情
     * @param {string} conversationId - 对话ID
     * @returns {Promise<object>} 对话详情
     */
    getDetail(conversationId) {
        return request(`/conversations/${conversationId}`);
    },

    /**
     * 删除对话
     * @param {string} conversationId - 对话ID
     * @returns {Promise<object>} 删除结果
     */
    delete(conversationId) {
        return request(`/conversations/${conversationId}`, {
            method: 'DELETE'
        });
    },

    /**
     * 发送消息
     * @param {string} conversationId - 对话ID
     * @param {string} content - 消息内容
     * @returns {Promise<object>} 消息结果
     */
    sendMessage(conversationId, content) {
        return request(`/conversations/${conversationId}/messages`, {
            method: 'POST',
            body: { content }
        });
    },

    /**
     * 获取消息列表
     * @param {string} conversationId - 对话ID
     * @returns {Promise<Array>} 消息列表
     */
    getMessages(conversationId) {
        return request(`/conversations/${conversationId}/messages`);
    },

    /**
     * 获取对话限制
     * @returns {Promise<object>} 限制信息
     */
    getLimits() {
        return request('/conversations/limits');
    }
};

// ============================================
// 订阅相关 API
// ============================================

const subscriptionAPI = {
    /**
     * 获取套餐列表
     * @returns {Promise<Array>} 套餐列表
     */
    getPlans() {
        return request('/subscriptions/plans');
    },

    /**
     * 获取当前订阅
     * @returns {Promise<object>} 订阅信息
     */
    getCurrent() {
        return request('/subscriptions/current');
    },

    /**
     * 创建订单
     * @param {string} planId - 套餐ID
     * @param {string} period - 周期
     * @returns {Promise<object>} 订单信息
     */
    createOrder(planId, period = 'monthly') {
        return request('/subscriptions/orders', {
            method: 'POST',
            body: { plan_id: planId, period }
        });
    },

    /**
     * 查询订单
     * @param {string} orderId - 订单ID
     * @returns {Promise<object>} 订单信息
     */
    getOrder(orderId) {
        return request(`/subscriptions/orders/${orderId}`);
    },

    /**
     * 取消订阅
     * @returns {Promise<object>} 取消结果
     */
    cancel() {
        return request('/subscriptions/cancel', {
            method: 'POST'
        });
    }
};

// ============================================
// 星图相关 API
// ============================================

const starAPI = {
    /**
     * 获取星图数据
     * @param {number} depth - 展开深度 1-4
     * @returns {Promise<object>} 星图数据
     */
    getGraph(depth = 3) {
        return request(`/star/graph?depth=${depth}`);
    },

    /**
     * 获取节点详情
     * @param {string} nodeId - 节点ID
     * @returns {Promise<object>} 节点详情
     */
    getNodeDetail(nodeId) {
        return request(`/star/node/${nodeId}`);
    },

    /**
     * 展开子节点
     * @param {string} nodeId - 节点ID
     * @returns {Promise<object>} 子节点数据
     */
    expandNode(nodeId) {
        return request(`/star/node/${nodeId}/expand`, {
            method: 'POST'
        });
    }
};

// ============================================
// 记忆系统相关 API
// ============================================

const memoryAPI = {
    /**
     * 语义搜索记忆（RAI Badge "回忆中"阶段调用）
     * @param {string} query - 搜索查询
     * @param {number} limit - 返回数量
     * @param {string} memoryType - 筛选类型: goal/preference/fact/event
     * @returns {Promise<object>} 搜索结果
     */
    search(query, limit = 5, memoryType = null) {
        const params = new URLSearchParams({ query, limit: String(limit) });
        if (memoryType) params.append('memory_type', memoryType);
        return request(`/memories/search?${params}`);
    },

    /**
     * 获取全部记忆
     * @param {number} limit - 每页数量
     * @param {number} offset - 偏移量
     * @returns {Promise<Array>} 记忆列表
     */
    getAll(limit = 20, offset = 0) {
        return request(`/memories/all?limit=${limit}&offset=${offset}`);
    },

    /**
     * 删除记忆
     * @param {string} memoryId - 记忆ID
     * @returns {Promise<object>} 删除结果
     */
    delete(memoryId) {
        return request(`/memories/${memoryId}`, { method: 'DELETE' });
    },

    /**
     * 同步记忆到星图（L2→L3）
     * @param {Array<string>} memoryIds - 指定记忆ID列表，为空则同步全部
     * @returns {Promise<object>} 同步结果
     */
    syncToStar(memoryIds = null) {
        return request('/memories/sync-to-star', {
            method: 'POST',
            body: { memory_ids: memoryIds }
        });
    },

    /**
     * 创建对话组（日记功能）
     * @param {object} data - 组数据
     * @param {string} data.title - 标题
     * @param {string} data.description - 描述
     * @param {Array<string>} data.tags - 标签列表
     * @param {Array<number>} data.conversationIds - 对话ID列表
     * @param {string} data.summary - AI摘要
     * @returns {Promise<object>} 创建结果
     */
    createGroup(data) {
        return request('/memories/groups', {
            method: 'POST',
            body: {
                title: data.title,
                description: data.description || '',
                tags: data.tags || [],
                conversation_ids: data.conversationIds || [],
                summary: data.summary || ''
            }
        });
    },

    /**
     * 获取对话组列表（日记列表）
     * @param {string} tag - 按标签筛选
     * @returns {Promise<Array>} 对话组列表
     */
    getGroups(tag = null) {
        const url = tag ? `/memories/groups?tag=${tag}` : '/memories/groups';
        return request(url);
    },

    /**
     * 获取对话组详情
     * @param {number} groupId - 组ID
     * @returns {Promise<object>} 组详情
     */
    getGroupDetail(groupId) {
        return request(`/memories/groups/${groupId}`);
    },

    /**
     * 更新对话组
     * @param {number} groupId - 组ID
     * @param {object} data - 更新数据
     * @returns {Promise<object>} 更新结果
     */
    updateGroup(groupId, data) {
        return request(`/memories/groups/${groupId}`, {
            method: 'PUT',
            body: data
        });
    },

    /**
     * 删除对话组
     * @param {number} groupId - 组ID
     * @returns {Promise<object>} 删除结果
     */
    deleteGroup(groupId) {
        return request(`/memories/groups/${groupId}`, { method: 'DELETE' });
    }
};

// ============================================
// 导出 API 对象
// ============================================

const api = {
    config: API_CONFIG,
    auth: authAPI,
    user: userAPI,
    assessment: assessmentAPI,
    conversation: conversationAPI,
    subscription: subscriptionAPI,
    star: starAPI,
    memory: memoryAPI,
    request,
    setTokens,
    clearTokens,
    getAccessToken,
    getRefreshToken
};

// 全局暴露
window.api = api;
window.APIError = APIError;

// 模块导出
if (typeof module !== 'undefined' && module.exports) {
    module.exports = api;
}
