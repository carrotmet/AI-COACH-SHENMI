/**
 * 深觅 AI Coach - 对话模块 (V2 改造版)
 * 
 * V2 新增功能：
 * 1. RAI Badge - 实时意图识别可视化
 * 2. 角色化回复 - 根据情绪/意图切换AI风格
 * 3. 快捷操作栏 - 情境化快捷操作
 * 4. 增强对话列表 - 日期分组、搜索
 */

/**
 * 检查并处理来自星图的探索建议
 * 在chat页面加载时调用
 */
async function handlePendingExplorePrompt() {
    const pendingPrompt = localStorage.getItem('pending_explore_prompt');
    const timestamp = localStorage.getItem('pending_explore_timestamp');

    // 清理过期的prompt（超过5分钟）
    if (timestamp && Date.now() - parseInt(timestamp) > 5 * 60 * 1000) {
        localStorage.removeItem('pending_explore_prompt');
        localStorage.removeItem('pending_explore_timestamp');
        return false;
    }

    if (pendingPrompt) {
        // 清理localStorage
        localStorage.removeItem('pending_explore_prompt');
        localStorage.removeItem('pending_explore_timestamp');

        console.log('[探索建议] 准备创建对话并发送消息:', pendingPrompt.substring(0, 50) + '...');

        // 创建新对话
        const createResult = await chatManager.createConversation('探索建议对话');
        if (!createResult.success) {
            console.error('[探索建议] 创建对话失败:', createResult.error);
            showToast('创建对话失败，请重试', 'error');
            return false;
        }

        console.log('[探索建议] 对话创建成功:', createResult.data);

        // 等待页面渲染完成，同时给服务器处理时间
        await new Promise(r => setTimeout(r, 500));

        // 尝试发送消息，带重试逻辑
        let sendResult;
        let retryCount = 0;
        const maxRetries = 3;

        while (retryCount < maxRetries) {
            try {
                console.log(`[探索建议] 尝试发送消息 (第${retryCount + 1}次)`);
                sendResult = await chatManager.sendMessage(pendingPrompt);

                if (sendResult.success) {
                    console.log('[探索建议] 消息发送成功');
                    return true;
                } else {
                    console.error('[探索建议] 发送消息失败:', sendResult.error);
                    // 如果是最后一次重试，显示错误
                    if (retryCount === maxRetries - 1) {
                        showToast('发送消息失败: ' + (sendResult.error || '未知错误'), 'error');
                        return false;
                    }
                }
            } catch (error) {
                console.error('[探索建议] 发送消息异常:', error);
                if (retryCount === maxRetries - 1) {
                    showToast('发送消息异常: ' + (error.message || '未知错误'), 'error');
                    return false;
                }
            }

            retryCount++;
            // 等待后重试
            await new Promise(r => setTimeout(r, 1000 * retryCount));
        }

        return false;
    }

    return false;
}

// 暴露到全局
window.handlePendingExplorePrompt = handlePendingExplorePrompt;

/**
 * 对话管理器 V2
 */
class ChatManager {
    constructor() {
        this.currentConversation = null;
        this.messages = [];
        this.isLoading = false;
        this.listeners = [];
        this.currentIntent = null;      // 当前意图
        this.currentRole = 'companion'; // 当前角色 (companion/explorer/mentor/coach/partner)
        this.allConversations = [];     // 缓存所有对话用于搜索
    }

    /**
     * 创建新对话
     */
    async createConversation(title = '新对话', context = {}) {
        try {
            const data = await api.conversation.create(title, context);
            console.log('API返回的创建对话数据:', data);
            
            // handleResponse已经提取了data字段，直接使用
            if (!data) {
                throw new Error('API返回数据为空');
            }
            
            if (!data.conversation_id && !data.id) {
                console.error('API返回数据缺少对话ID:', data);
                throw new Error('API返回数据缺少对话ID');
            }
            
            this.currentConversation = {
                id: data.conversation_id || data.id,
                title: data.title || title,
                createdAt: data.created_at || new Date().toISOString()
            };
            this.messages = [];
            this.currentIntent = null;
            this.currentRole = 'companion';
            this.notifyListeners('conversationCreated', this.currentConversation);
            return { success: true, data: this.currentConversation };
        } catch (error) {
            console.error('创建对话失败:', error);
            return { success: false, error: error.message || '创建对话失败' };
        }
    }

    /**
     * 加载对话列表
     */
    async loadConversations() {
        try {
            const data = await api.conversation.getList();
            console.log('API返回的对话列表数据:', data);
            
            // handleResponse已经提取了data字段
            // 对话列表返回格式: {items: [...], total, page, limit}
            let conversations = [];
            
            if (data && typeof data === 'object') {
                if (Array.isArray(data)) {
                    // 直接是数组
                    conversations = data;
                } else if (data.items && Array.isArray(data.items)) {
                    // 分页格式
                    conversations = data.items;
                } else {
                    console.warn('未知的对话列表格式:', data);
                }
            }
            
            this.allConversations = conversations;
            return { success: true, data: this.allConversations };
        } catch (error) {
            console.error('加载对话列表失败:', error);
            // 返回空列表，避免UI一直加载
            this.allConversations = [];
            return { success: true, data: [], error: error.message || '加载对话列表失败' };
        }
    }

    /**
     * 搜索对话
     */
    searchConversations(query) {
        if (!query || !this.allConversations.length) return this.allConversations;
        
        const lowerQuery = query.toLowerCase();
        return this.allConversations.filter(conv => 
            conv.title?.toLowerCase().includes(lowerQuery)
        );
    }

    /**
     * 加载对话消息
     */
    async loadMessages(conversationId) {
        try {
            const data = await api.conversation.getMessages(conversationId);
            this.messages = data || [];
            this.notifyListeners('messagesLoaded', this.messages);
            return { success: true, data: this.messages };
        } catch (error) {
            console.error('加载消息失败:', error);
            return { success: false, error: error.message || '加载消息失败' };
        }
    }

    /**
     * 发送消息 (V2 增强版)
     */
    async sendMessage(content) {
        if (!this.currentConversation) {
            const createResult = await this.createConversation();
            if (!createResult.success) return createResult;
        }

        if (!content.trim()) {
            return { success: false, error: '消息内容不能为空' };
        }

        this.isLoading = true;
        this.notifyListeners('loadingStart');

        // 显示RAI处理状态
        this.notifyListeners('raiProcessing', { stage: 'understanding', text: '理解中...' });

        try {
            // 添加用户消息
            const userMessage = {
                role: 'user',
                content: content,
                created_at: new Date().toISOString()
            };
            this.messages.push(userMessage);
            this.notifyListeners('messageAdded', userMessage);

            // 模拟RAI处理阶段 (前端展示用)
            await this.simulateRAIStages();

            // 调用 API
            const data = await api.conversation.sendMessage(
                this.currentConversation.id,
                content
            );

            // 解析意图和角色
            const parsedIntent = this.parseIntent(data.ai_message.content, content);
            const detectedRole = this.detectRole(parsedIntent, content);
            this.currentIntent = parsedIntent;
            this.currentRole = detectedRole;

            // 添加 AI 回复
            const aiMessage = {
                role: 'assistant',
                content: data.ai_message.content,
                emotion_tag: data.ai_message.emotion_tag,
                tokens_used: data.ai_message.tokens_used,
                model: data.ai_message.model,
                intent: parsedIntent,
                role: detectedRole,
                created_at: data.ai_message.created_at || new Date().toISOString()
            };
            this.messages.push(aiMessage);
            this.notifyListeners('messageAdded', aiMessage);
            this.notifyListeners('intentDetected', { intent: parsedIntent, role: detectedRole });

            this.isLoading = false;
            this.notifyListeners('loadingEnd');

            return { success: true, data: aiMessage };
        } catch (error) {
            this.isLoading = false;
            this.notifyListeners('loadingEnd');
            console.error('发送消息失败:', error);
            // 返回更详细的错误信息
            return { 
                success: false, 
                error: error.message || '发送消息失败',
                code: error.code,
                status: error.status,
                detail: error.detail
            };
        }
    }

    /**
     * 模拟RAI处理阶段 (前端视觉效果)
     */
    async simulateRAIStages() {
        const stages = [
            { stage: 'understanding', text: '理解中...', delay: 300 },
            { stage: 'recalling', text: '回忆中...', delay: 400 },
            { stage: 'thinking', text: '思考中...', delay: 500 }
        ];

        for (const s of stages) {
            await new Promise(r => setTimeout(r, s.delay));
            this.notifyListeners('raiProcessing', s);
        }
    }

    /**
     * 解析意图 (前端规则版) - 优化版
     * 优先分析用户输入，不再混合AI回复内容
     */
    parseIntent(aiContent, userContent) {
        // 优先只分析用户输入，更准确地识别真实意图
        const userText = (userContent || '').toLowerCase().trim();
        const aiText = (aiContent || '').toLowerCase();
        
        // 意图关键词映射 - 按优先级排序（更具体的意图优先）
        const intentMap = [
            { 
                type: '自我探索', 
                keywords: ['优势', '擅长', '能力', '性格', '我是谁', '适合', '测评', '报告', 'top5', '回顾', '结果', '发现'], 
                confidence: 0.90,
                priority: 1  // 最高优先级
            },
            { 
                type: '目标设定', 
                keywords: ['目标', '计划', '打算', '希望', '梦想', '规划'], 
                confidence: 0.85,
                priority: 2
            },
            { 
                type: '行动计划', 
                keywords: ['做', '执行', '开始', '步骤', '安排', '时间', '行动', '怎么做'], 
                confidence: 0.82,
                priority: 3
            },
            { 
                type: '知识获取', 
                keywords: ['什么是', '为什么', '怎么', '如何', '方法', '技巧', '建议'], 
                confidence: 0.78,
                priority: 4
            },
            { 
                type: '情绪表达', 
                keywords: ['焦虑', '压力', '难过', '开心', '担心', '害怕', '累', '烦', '痛苦', '沮丧'], 
                confidence: 0.75,
                priority: 5
            }
        ];

        // 第一步：只在用户输入中匹配
        let bestIntent = null;
        let maxScore = 0;
        let matchedKeywords = [];

        for (const intent of intentMap) {
            const matches = intent.keywords.filter(kw => userText.includes(kw));
            if (matches.length > 0) {
                // 计算匹配得分：匹配词数 * 优先级权重
                const score = matches.length * (10 - intent.priority);
                if (score > maxScore) {
                    maxScore = score;
                    bestIntent = intent;
                    matchedKeywords = matches;
                }
            }
        }

        // 如果用户输入有明确匹配，直接返回
        if (bestIntent) {
            return {
                category: bestIntent.type,
                confidence: bestIntent.confidence,
                keywords: matchedKeywords
            };
        }

        // 第二步：如果用户输入无明确匹配，才参考AI回复
        const fullText = userText + ' ' + aiText;
        for (const intent of intentMap) {
            const matches = intent.keywords.filter(kw => fullText.includes(kw));
            if (matches.length > 0) {
                return {
                    category: intent.type,
                    confidence: intent.confidence * 0.8, // 参考AI回复时降低置信度
                    keywords: matches
                };
            }
        }

        return { category: '通用对话', confidence: 0.60, keywords: [] };
    }

    /**
     * 检测角色 (基于意图和情绪)
     */
    detectRole(intent, userContent) {
        const text = userContent.toLowerCase();
        
        // 情绪检测 - 优先判断
        const emotions = {
            companion: ['难过', '伤心', '压力大', '焦虑', '害怕', '担心', '烦', '累', '痛苦'],
            coach: ['目标', '计划', '行动', '执行', '步骤', '达成', '实现'],
            mentor: ['学习', '方法', '技巧', '建议', '推荐', '知识', '技能'],
            explorer: ['为什么', '我是谁', '意义', '价值', '适合', '人生'],
            partner: ['一起', '讨论', '想法', '创意', '好玩', '试试']
        };

        for (const [role, keywords] of Object.entries(emotions)) {
            if (keywords.some(kw => text.includes(kw))) return role;
        }

        // 基于意图默认映射
        const roleMap = {
            '情绪表达': 'companion',
            '目标设定': 'coach',
            '行动计划': 'coach',
            '知识获取': 'mentor',
            '自我探索': 'explorer'
        };

        return roleMap[intent?.category] || 'companion';
    }

    /**
     * 获取快捷操作建议 (V2增强)
     */
    getQuickActions(intent, content) {
        const text = content.toLowerCase();
        const actions = [];

        // 情绪支持场景
        if (text.includes('焦虑') || text.includes('压力') || text.includes('紧张')) {
            actions.push({ text: '试试呼吸练习', icon: '🧘', action: 'breathing' });
            actions.push({ text: '情绪日记', icon: '📝', action: 'mood_journal' });
            actions.push({ text: '聊聊情绪', icon: '💬', action: 'chat_emotion' });
        }
        else if (text.includes('难过') || text.includes('伤心') || text.includes('不开心')) {
            actions.push({ text: '倾诉一下', icon: '💭', action: 'vent' });
            actions.push({ text: '积极练习', icon: '✨', action: 'positive' });
        }
        // 目标规划场景
        else if (text.includes('目标') || text.includes('计划') || text.includes('规划')) {
            actions.push({ text: '制定具体计划', icon: '📋', action: 'create_plan' });
            actions.push({ text: '查看我的星图', icon: '⭐', action: 'view_star' });
            actions.push({ text: '分解任务', icon: '🔨', action: 'breakdown' });
        }
        // 自我探索场景
        else if (text.includes('优势') || text.includes('擅长') || text.includes('能力')) {
            actions.push({ text: '回顾测评结果', icon: '📊', action: 'view_assessment' });
            actions.push({ text: 'Top5优势解读', icon: '🏆', action: 'top5_strengths' });
        }
        // 学习成长场景
        else if (text.includes('学习') || text.includes('技能') || text.includes('提升')) {
            actions.push({ text: '推荐资源', icon: '📚', action: 'resources' });
            actions.push({ text: '制定学习路径', icon: '🗺️', action: 'learning_path' });
        }
        // 职业发展场景
        else if (text.includes('工作') || text.includes('职业') || text.includes('升职')) {
            actions.push({ text: '职业规划建议', icon: '🎯', action: 'career_advice' });
            actions.push({ text: '优势应用', icon: '💪', action: 'strength_apply' });
        }

        // 默认操作
        if (actions.length === 0) {
            actions.push({ text: '深入探讨', icon: '🔍', action: 'explore' });
            actions.push({ text: '制定计划', icon: '📝', action: 'plan' });
            actions.push({ text: '回顾星图', icon: '⭐', action: 'star_map' });
        }

        return actions.slice(0, 3); // 最多返回3个
    }

    /**
     * 删除对话
     */
    async deleteConversation(conversationId) {
        try {
            await api.conversation.delete(conversationId);
            if (this.currentConversation?.id === conversationId) {
                this.currentConversation = null;
                this.messages = [];
            }
            // 从缓存中移除
            this.allConversations = this.allConversations.filter(c => c.conversation_id !== conversationId);
            this.notifyListeners('conversationDeleted', conversationId);
            return { success: true };
        } catch (error) {
            console.error('删除对话失败:', error);
            return { success: false, error: error.message || '删除对话失败' };
        }
    }

    getCurrentConversation() { return this.currentConversation; }
    getMessages() { return this.messages; }
    isLoadingMessages() { return this.isLoading; }
    getCurrentIntent() { return this.currentIntent; }
    getCurrentRole() { return this.currentRole; }

    addListener(listener) { this.listeners.push(listener); }
    removeListener(listener) { this.listeners = this.listeners.filter(l => l !== listener); }

    notifyListeners(event, data) {
        this.listeners.forEach(listener => {
            try { listener(event, data); } catch (error) { console.error('监听器执行失败:', error); }
        });
    }
}

// 创建全局实例
const chatManager = new ChatManager();

/**
 * ==================== V2 UI 组件 ====================
 */

/**
 * 渲染RAI处理状态条
 */
function renderRAIStatus(stage, text) {
    const container = document.getElementById('raiStatusContainer');
    if (!container) return;

    const stageNames = {
        understanding: '理解中',
        recalling: '回忆中',
        thinking: '思考中'
    };

    container.innerHTML = `
        <div class="rai-status rai-status--${stage}">
            <div class="rai-status__dots">
                <span class="${stage === 'understanding' ? 'active' : ''}"></span>
                <span class="${stage === 'recalling' ? 'active' : ''}"></span>
                <span class="${stage === 'thinking' ? 'active' : ''}"></span>
            </div>
            <span class="rai-status__text">${stageNames[stage] || text}...</span>
        </div>
    `;
    container.style.display = 'flex';
}

/**
 * 隐藏RAI状态
 */
function hideRAIStatus() {
    const container = document.getElementById('raiStatusContainer');
    if (container) container.style.display = 'none';
}

/**
 * 渲染意图Badge
 */
function renderIntentBadge(intent) {
    if (!intent) return '';
    
    const intentColors = {
        '情绪表达': '#FF6B9D',
        '目标设定': '#4A90D9',
        '自我探索': '#9B59B6',
        '知识获取': '#50C878',
        '行动计划': '#FF8C42',
        '通用对话': '#95A5A6'
    };

    const color = intentColors[intent.category] || '#4A90D9';
    
    return `
        <div class="intent-badge" style="--intent-color: ${color}" onclick="toggleIntentDetail(this)">
            <span class="intent-badge__dot" style="background: ${color}"></span>
            <span class="intent-badge__text">${intent.category}</span>
            <span class="intent-badge__confidence">${Math.round(intent.confidence * 100)}%</span>
        </div>
        <div class="intent-detail" style="display: none;">
            <div class="intent-detail__item">
                <span>检测关键词:</span>
                <span>${intent.keywords?.join(', ') || '无'}</span>
            </div>
        </div>
    `;
}

/**
 * 切换意图详情显示
 */
function toggleIntentDetail(badge) {
    const detail = badge.nextElementSibling;
    if (detail) {
        detail.style.display = detail.style.display === 'none' ? 'block' : 'none';
    }
}

/**
 * 渲染快捷操作栏
 */
function renderQuickActions(actions) {
    const container = document.getElementById('quickActionsContainer');
    if (!container || !actions || actions.length === 0) {
        if (container) container.style.display = 'none';
        return;
    }

    container.innerHTML = actions.map(action => `
        <button class="quick-action-chip" onclick="handleQuickAction('${action.action}', '${action.text}')">
            <span class="quick-action-chip__icon">${action.icon}</span>
            <span>${action.text}</span>
        </button>
    `).join('');

    container.style.display = 'flex';
}

/**
 * 处理快捷操作
 */
function handleQuickAction(action, text) {
    const input = document.getElementById('messageInput');
    if (input) {
        input.value = text;
        sendMessage();
    }
}

/**
 * 渲染消息 V2 (带意图和角色)
 */
function renderMessage(message, container) {
    const isUser = message.role === 'user';
    const messageEl = document.createElement('div');
    messageEl.className = `message ${isUser ? 'message--user' : 'message--ai'}`;
    
    // V2: 角色样式
    const roleClass = !isUser && message.role ? `message--role-${message.role}` : '';
    if (roleClass) messageEl.classList.add(roleClass);

    const time = formatDate(message.created_at, 'HH:mm');
    
    // V2: 意图Badge (仅AI消息)
    const intentBadge = !isUser && message.intent ? renderIntentBadge(message.intent) : '';
    
    // V2: 快捷操作 (仅AI消息且是最后一条)
    let quickActions = '';
    if (!isUser && message.intent) {
        const actions = chatManager.getQuickActions(message.intent, message.content);
        quickActions = `
            <div class="message__actions">
                ${actions.map(a => `
                    <button class="message-action-chip" onclick="handleQuickAction('${a.action}', '${a.text}')">
                        ${a.icon} ${a.text}
                    </button>
                `).join('')}
            </div>
        `;
    }

    messageEl.innerHTML = `
        <div class="message__avatar">
            ${isUser ? '我' : getRoleLabel(message.role)}
        </div>
        <div class="message__content">
            ${intentBadge}
            <div class="message__bubble">
                ${escapeHtml(message.content).replace(/\n/g, '<br>')}
            </div>
            ${quickActions}
            <div class="message__time">${time}</div>
        </div>
    `;
    
    container.appendChild(messageEl);
    container.scrollTop = container.scrollHeight;
}

/**
 * 获取角色标签
 */
function getRoleLabel(role) {
    const labels = {
        companion: '🤗',
        coach: '🎯',
        mentor: '📚',
        explorer: '🔍',
        partner: '🤝'
    };
    return labels[role] || 'AI';
}

/**
 * 渲染加载中的消息 V2
 */
function renderLoadingMessage(container) {
    const loadingEl = document.createElement('div');
    loadingEl.className = 'message message--ai message--loading';
    loadingEl.id = 'loadingMessage';
    loadingEl.innerHTML = `
        <div class="message__avatar">AI</div>
        <div class="message__content">
            <div class="message__bubble">
                <div class="typing-indicator">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
            </div>
        </div>
    `;
    container.appendChild(loadingEl);
    container.scrollTop = container.scrollHeight;
    return loadingEl;
}

/**
 * 渲染对话列表 V2 (带日期分组)
 */
function renderConversationList(conversations, container) {
    // 防御性检查：确保conversations是数组
    if (!Array.isArray(conversations)) {
        console.error('renderConversationList: conversations不是数组', conversations);
        container.innerHTML = `
            <div class="empty-conversations">
                <p>加载失败，请刷新重试</p>
            </div>
        `;
        return;
    }
    
    if (conversations.length === 0) {
        container.innerHTML = `
            <div class="empty-conversations">
                <p>暂无对话记录</p>
            </div>
        `;
        return;
    }

    // V2: 按日期分组
    const grouped = groupConversationsByDate(conversations);
    
    container.innerHTML = Object.entries(grouped).map(([dateLabel, items]) => `
        <div class="conversation-group">
            <div class="conversation-group__label">${dateLabel}</div>
            ${items.map(conv => `
                <div class="conversation-item" data-id="${conv.conversation_id}">
                    <div class="conversation-item__icon">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
                        </svg>
                    </div>
                    <div class="conversation-item__content">
                        <div class="conversation-item__title">${escapeHtml(conv.title)}</div>
                        <div class="conversation-item__meta">
                            ${conv.message_count || 0} 条消息 · ${getRelativeTime(conv.updated_at || conv.created_at)}
                        </div>
                    </div>
                    <button class="conversation-item__delete" onclick="deleteConversation('${conv.conversation_id}', event)">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <polyline points="3 6 5 6 21 6"/>
                            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
                        </svg>
                    </button>
                </div>
            `).join('')}
        </div>
    `).join('');

    // 绑定点击事件
    container.querySelectorAll('.conversation-item').forEach(item => {
        item.addEventListener('click', () => {
            const conversationId = item.dataset.id;
            loadConversation(conversationId);
        });
    });
}

/**
 * 按日期分组对话
 */
function groupConversationsByDate(conversations) {
    const groups = {};
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const yesterday = new Date(today - 86400000);

    conversations.forEach(conv => {
        const date = new Date(conv.updated_at || conv.created_at);
        const dateKey = new Date(date.getFullYear(), date.getMonth(), date.getDate());
        
        let label;
        if (dateKey.getTime() === today.getTime()) {
            label = '今天';
        } else if (dateKey.getTime() === yesterday.getTime()) {
            label = '昨天';
        } else if (now - dateKey < 7 * 86400000) {
            label = '本周';
        } else if (now - dateKey < 30 * 86400000) {
            label = '本月';
        } else {
            label = `${date.getFullYear()}年${date.getMonth() + 1}月`;
        }

        if (!groups[label]) groups[label] = [];
        groups[label].push(conv);
    });

    return groups;
}

/**
 * 加载对话
 */
async function loadConversation(conversationId) {
    const result = await chatManager.loadMessages(conversationId);
    if (result.success) {
        const container = document.getElementById('messagesContainer');
        if (container) {
            container.innerHTML = '';
            result.data.forEach(msg => renderMessage(msg, container));
        }
        
        chatManager.currentConversation = { id: conversationId };
        
        document.querySelectorAll('.conversation-item').forEach(item => {
            item.classList.toggle('conversation-item--active', item.dataset.id === conversationId);
        });

        // V2: 隐藏欢迎消息
        const welcome = document.querySelector('.chat-welcome');
        if (welcome) welcome.style.display = 'none';
    }
}

/**
 * 删除对话
 */
async function deleteConversation(conversationId, event) {
    event.stopPropagation();
    if (!confirm('确定要删除这个对话吗？')) return;

    const result = await chatManager.deleteConversation(conversationId);
    if (result.success) {
        showToast('对话已删除', 'success');
        loadConversationList();
    } else {
        showToast(result.error, 'error');
    }
}

/**
 * 加载对话列表
 */
async function loadConversationList() {
    const container = document.getElementById('conversationList');
    if (!container) return;

    // 显示加载中
    container.innerHTML = `
        <div class="loading-conversations">
            <div class="loading-spinner"></div>
        </div>
    `;

    try {
        const result = await chatManager.loadConversations();
        if (result.success) {
            renderConversationList(result.data, container);
        } else {
            container.innerHTML = `
                <div class="empty-conversations">
                    <p>加载失败: ${result.error || '未知错误'}</p>
                    <button onclick="loadConversationList()" style="margin-top: 8px; padding: 6px 12px; background: var(--color-primary); color: white; border: none; border-radius: 6px; cursor: pointer;">重试</button>
                </div>
            `;
        }
    } catch (error) {
        console.error('加载对话列表异常:', error);
        container.innerHTML = `
            <div class="empty-conversations">
                <p>加载失败: ${error.message || '未知错误'}</p>
                <button onclick="loadConversationList()" style="margin-top: 8px; padding: 6px 12px; background: var(--color-primary); color: white; border: none; border-radius: 6px; cursor: pointer;">重试</button>
            </div>
        `;
    }
}

/**
 * 工具函数
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatDate(dateStr, format = 'HH:mm') {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    if (format === 'HH:mm') {
        return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
    }
    return date.toLocaleString('zh-CN');
}

function getRelativeTime(dateStr) {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    const now = new Date();
    const diff = now - date;
    
    if (diff < 60000) return '刚刚';
    if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`;
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`;
    if (diff < 7 * 86400000) return `${Math.floor(diff / 86400000)}天前`;
    return date.toLocaleDateString('zh-CN');
}

function showToast(message, type = 'info') {
    // 简单的toast实现，可以扩展
    console.log(`[${type}] ${message}`);
}

// 全局暴露
window.chatManager = chatManager;
window.renderMessage = renderMessage;
window.renderConversationList = renderConversationList;
window.renderLoadingMessage = renderLoadingMessage;
window.renderRAIStatus = renderRAIStatus;
window.hideRAIStatus = hideRAIStatus;
window.renderQuickActions = renderQuickActions;
window.handleQuickAction = handleQuickAction;
window.toggleIntentDetail = toggleIntentDetail;
window.loadConversation = loadConversation;
window.deleteConversation = deleteConversation;
window.loadConversationList = loadConversationList;

// 模块导出
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        ChatManager,
        chatManager,
        renderMessage,
        renderConversationList,
        renderLoadingMessage,
        renderRAIStatus,
        hideRAIStatus,
        renderQuickActions
    };
}
