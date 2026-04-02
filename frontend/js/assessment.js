/**
 * 深觅 AI Coach - 测评模块
 * DeepSearch AI Coach - Assessment Module
 * 
 * 处理测评流程、题目展示、答案收集和结果展示
 */

/**
 * 测评管理器
 */
class AssessmentManager {
    constructor() {
        this.currentAssessment = null;
        this.questions = [];
        this.answers = {};
        this.currentQuestionIndex = 0;
        this.listeners = [];
    }

    /**
     * 开始新测评
     * @param {string} type - 测评类型 (via_strengths/via_strengths_full)
     * @returns {Promise<object>} 测评信息
     */
    async startAssessment(type = 'via_strengths') {
        try {
            const data = await api.assessment.create(type);
            this.currentAssessment = {
                id: data.assessment_id,
                type: data.type,
                totalQuestions: data.total_questions,
                currentQuestion: data.current_question,
                status: data.status
            };
            this.answers = {};
            this.currentQuestionIndex = 0;
            
            // 保存到本地存储
            this.saveProgress();
            
            return { success: true, data: this.currentAssessment };
        } catch (error) {
            console.error('创建测评失败:', error);
            return { 
                success: false, 
                error: error.message || '创建测评失败，请稍后重试'
            };
        }
    }

    /**
     * 获取题目
     * @param {string} assessmentId - 测评ID
     * @returns {Promise<object>} 题目信息
     */
    async getQuestion(assessmentId) {
        try {
            const data = await api.assessment.getQuestions(assessmentId);
            this.currentQuestionIndex = data.current_question - 1;
            return { success: true, data: data.question };
        } catch (error) {
            console.error('获取题目失败:', error);
            return { 
                success: false, 
                error: error.message || '获取题目失败'
            };
        }
    }

    /**
     * 提交答案
     * @param {string} answer - 答案
     * @returns {Promise<object>} 提交结果
     */
    async submitAnswer(answer) {
        if (!this.currentAssessment) {
            return { success: false, error: '测评未开始' };
        }

        try {
            const questionId = this.currentQuestionIndex + 1;
            const data = await api.assessment.submitAnswer(
                this.currentAssessment.id,
                questionId,
                answer
            );

            // 保存答案
            this.answers[questionId] = answer;
            this.saveProgress();

            // 更新当前题目
            this.currentQuestionIndex = data.current_question - 1;
            this.currentAssessment.currentQuestion = data.current_question;

            // 通知监听器
            this.notifyListeners('answerSubmitted', {
                questionId,
                answer,
                progress: this.getProgress()
            });

            return { 
                success: true, 
                data: {
                    isCompleted: data.is_completed,
                    nextQuestion: data.next_question,
                    resultUrl: data.result_url
                }
            };
        } catch (error) {
            console.error('提交答案失败:', error);
            return { 
                success: false, 
                error: error.message || '提交答案失败'
            };
        }
    }

    /**
     * 获取测评进度
     * @returns {object} 进度信息
     */
    getProgress() {
        if (!this.currentAssessment) return null;

        return {
            current: this.currentQuestionIndex + 1,
            total: this.currentAssessment.totalQuestions,
            percent: Math.round(((this.currentQuestionIndex + 1) / this.currentAssessment.totalQuestions) * 100),
            answeredCount: Object.keys(this.answers).length
        };
    }

    /**
     * 获取测评结果
     * @returns {Promise<object>} 测评结果
     */
    async getResult() {
        if (!this.currentAssessment) {
            return { success: false, error: '测评未开始' };
        }

        try {
            const data = await api.assessment.getResult(this.currentAssessment.id);
            return { success: true, data };
        } catch (error) {
            console.error('获取测评结果失败:', error);
            return { 
                success: false, 
                error: error.message || '获取测评结果失败'
            };
        }
    }

    /**
     * 保存进度到本地存储
     */
    saveProgress() {
        if (this.currentAssessment) {
            localStorage.setItem('assessment_progress', JSON.stringify({
                assessment: this.currentAssessment,
                answers: this.answers,
                currentIndex: this.currentQuestionIndex,
                timestamp: Date.now()
            }));
        }
    }

    /**
     * 从本地存储恢复进度
     * @returns {boolean} 是否成功恢复
     */
    restoreProgress() {
        const saved = localStorage.getItem('assessment_progress');
        if (!saved) return false;

        try {
            const data = JSON.parse(saved);
            // 检查是否超过24小时
            if (Date.now() - data.timestamp > 24 * 60 * 60 * 1000) {
                localStorage.removeItem('assessment_progress');
                return false;
            }

            this.currentAssessment = data.assessment;
            this.answers = data.answers || {};
            this.currentQuestionIndex = data.currentIndex || 0;
            return true;
        } catch (e) {
            console.error('恢复进度失败:', e);
            return false;
        }
    }

    /**
     * 清除进度
     */
    clearProgress() {
        this.currentAssessment = null;
        this.questions = [];
        this.answers = {};
        this.currentQuestionIndex = 0;
        localStorage.removeItem('assessment_progress');
    }

    /**
     * 添加事件监听器
     * @param {Function} listener - 监听器函数
     */
    addListener(listener) {
        this.listeners.push(listener);
    }

    /**
     * 移除事件监听器
     * @param {Function} listener - 监听器函数
     */
    removeListener(listener) {
        this.listeners = this.listeners.filter(l => l !== listener);
    }

    /**
     * 通知所有监听器
     * @param {string} event - 事件类型
     * @param {*} data - 事件数据
     */
    notifyListeners(event, data) {
        this.listeners.forEach(listener => {
            try {
                listener(event, data);
            } catch (error) {
                console.error('监听器执行失败:', error);
            }
        });
    }
}

// 创建全局测评管理器实例
const assessmentManager = new AssessmentManager();

/**
 * 渲染题目
 * @param {object} question - 题目数据
 * @param {number} current - 当前题号
 * @param {number} total - 总题数
 */
function renderQuestion(question, current, total) {
    const container = document.getElementById('questionContainer');
    if (!container) return;

    const progress = Math.round((current / total) * 100);

    container.innerHTML = `
        <div class="question-card">
            <div class="question-card__number">题目 ${current} / ${total}</div>
            <h2 class="question-card__text">${question.text}</h2>
            <div class="options-list">
                ${question.options.map((option, index) => `
                    <label class="option-item" data-option="${option.id}">
                        <span class="option-item__radio"></span>
                        <span class="option-item__text">${option.text}</span>
                    </label>
                `).join('')}
            </div>
        </div>
    `;

    // 更新进度条
    updateProgressBar(progress);

    // 绑定选项点击事件
    container.querySelectorAll('.option-item').forEach(item => {
        item.addEventListener('click', async () => {
            // 移除其他选中状态
            container.querySelectorAll('.option-item').forEach(i => {
                i.classList.remove('option-item--selected');
            });
            // 添加当前选中状态
            item.classList.add('option-item--selected');

            // 获取答案
            const answer = item.dataset.option;

            // 禁用选项，防止重复点击
            container.querySelectorAll('.option-item').forEach(i => {
                i.style.pointerEvents = 'none';
            });

            // 提交答案
            const result = await assessmentManager.submitAnswer(answer);

            if (result.success) {
                if (result.data.isCompleted) {
                    // 测评完成，跳转到结果页
                    showToast('测评完成！', 'success');
                    setTimeout(() => {
                        window.location.href = `/assessment/result.html?id=${assessmentManager.currentAssessment.id}`;
                    }, 1000);
                } else {
                    // 显示下一题
                    renderQuestion(result.data.nextQuestion, current + 1, total);
                }
            } else {
                showToast(result.error, 'error');
                // 恢复选项可点击
                container.querySelectorAll('.option-item').forEach(i => {
                    i.style.pointerEvents = '';
                });
            }
        });
    });
}

/**
 * 更新进度条
 * @param {number} percent - 进度百分比
 */
function updateProgressBar(percent) {
    const progressBar = document.getElementById('progressBar');
    const progressText = document.getElementById('progressText');
    
    if (progressBar) {
        progressBar.style.width = percent + '%';
    }
    if (progressText) {
        progressText.textContent = percent + '%';
    }
}

/**
 * 渲染测评结果
 * @param {object} result - 测评结果数据
 */
function renderResult(result) {
    const container = document.getElementById('resultContainer');
    if (!container) return;

    const topStrengths = result.top_strengths || [];
    const recommendations = result.recommendations || [];

    container.innerHTML = `
        <div class="result-header">
            <div class="result-score">
                <span class="result-score__value">${topStrengths[0]?.score || 0}</span>
                <span class="result-score__label">最高优势得分</span>
            </div>
            <h1 class="result-title">您的 Top5 优势</h1>
            <p class="result-subtitle">基于 VIA 性格优势理论测评结果</p>
        </div>

        <div class="strengths-list">
            ${topStrengths.map((strength, index) => `
                <div class="strength-item" data-animate="fade-up" data-animate-delay="${index * 100}">
                    <div class="strength-item__rank">${strength.rank}</div>
                    <div class="strength-item__content">
                        <h3 class="strength-item__name">${strength.name}</h3>
                        <p class="strength-item__description">${strength.description}</p>
                        <div class="strength-item__score">
                            <div class="strength-item__bar" style="--score: ${strength.score}%">
                                <div class="strength-item__fill"></div>
                            </div>
                            <span class="strength-item__score-value">${strength.score}</span>
                        </div>
                    </div>
                </div>
            `).join('')}
        </div>

        <div class="recommendations-section" data-animate="fade-up" data-animate-delay="500">
            <h2 class="section-title">发展建议</h2>
            <ul class="recommendations-list">
                ${recommendations.map(rec => `
                    <li class="recommendation-item">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
                            <polyline points="22 4 12 14.01 9 11.01"/>
                        </svg>
                        ${rec}
                    </li>
                `).join('')}
            </ul>
        </div>

        <div class="result-actions" data-animate="fade-up" data-animate-delay="600">
            <a href="/chat/index.html" class="btn btn--primary btn--lg">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
                </svg>
                与 AI 教练对话
            </a>
            <button class="btn btn--outline btn--lg" onclick="shareResult()">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="18" cy="5" r="3"/>
                    <circle cx="6" cy="12" r="3"/>
                    <circle cx="18" cy="19" r="3"/>
                    <line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/>
                    <line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/>
                </svg>
                分享结果
            </button>
        </div>
    `;

    // 触发动画
    initScrollAnimations();
}

/**
 * 分享结果
 */
async function shareResult() {
    const shareData = {
        title: '我的 VIA 优势测评结果 - 深觅 AI Coach',
        text: `我在深觅完成了 VIA 优势测评，发现了自己的核心优势！`,
        url: window.location.href
    };

    await shareContent(shareData);
}

/**
 * 渲染测评卡片列表
 * @param {Array} assessments - 测评列表
 */
function renderAssessmentCards(assessments) {
    const container = document.getElementById('assessmentList');
    if (!container) return;

    if (assessments.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                    <path d="M9 11l3 3L22 4"/>
                    <path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/>
                </svg>
                <p>还没有测评记录</p>
                <a href="/assessment/test.html" class="btn btn--primary">开始首次测评</a>
            </div>
        `;
        return;
    }

    container.innerHTML = assessments.map(assessment => `
        <div class="assessment-history-card">
            <div class="assessment-history-card__icon">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M9 11l3 3L22 4"/>
                    <path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/>
                </svg>
            </div>
            <div class="assessment-history-card__content">
                <h3 class="assessment-history-card__title">VIA 优势测评</h3>
                <p class="assessment-history-card__date">
                    ${formatDate(assessment.created_at, 'YYYY年MM月DD日')}
                </p>
            </div>
            <div class="assessment-history-card__status">
                ${assessment.status === 'completed' 
                    ? `<span class="badge badge--success">已完成</span>`
                    : `<span class="badge badge--warning">进行中</span>`
                }
            </div>
            <a href="/assessment/result.html?id=${assessment.assessment_id}" class="assessment-history-card__link">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="9 18 15 12 9 6"/>
                </svg>
            </a>
        </div>
    `).join('');
}

// 全局暴露
window.assessmentManager = assessmentManager;
window.renderQuestion = renderQuestion;
window.renderResult = renderResult;
window.shareResult = shareResult;
window.renderAssessmentCards = renderAssessmentCards;

// 模块导出
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        AssessmentManager,
        assessmentManager,
        renderQuestion,
        renderResult,
        shareResult,
        renderAssessmentCards
    };
}
