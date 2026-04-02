/**
 * 星图页面主逻辑
 * 使用 AntV G6 实现力导向图可视化
 */

(function() {
    'use strict';

    // 全局变量
    let graph = null;
    let graphData = null;
    let selectedNode = null;

    // DOM 元素
    const elements = {
        loading: document.getElementById('loading'),
        emptyState: document.getElementById('empty-state'),
        canvas: document.getElementById('star-canvas'),
        infoBar: document.getElementById('info-bar'),
        controls: document.getElementById('controls'),
        legend: document.getElementById('legend'),
        detailPanel: document.getElementById('detail-panel'),
        detailContent: document.getElementById('detail-content'),
        btnZoomIn: document.getElementById('btn-zoom-in'),
        btnZoomOut: document.getElementById('btn-zoom-out'),
        btnReset: document.getElementById('btn-reset'),
        btnClosePanel: document.getElementById('btn-close-panel')
    };

    // 节点类型配置
    const nodeTypeConfig = {
        root: { shape: 'star', size: 80, color: '#1E3A5F' },
        category: { shape: 'hexagon', size: 60, color: '#4A90D9' },
        strength: { shape: 'circle', size: 40, color: '#87CEEB' },
        insight: { shape: 'diamond', size: 30, color: '#F39C12' }
    };

    /**
     * 初始化页面
     */
    function init() {
        checkAuth();
        bindEvents();
        loadStarGraph();
    }

    /**
     * 检查登录状态
     */
    function checkAuth() {
        const token = localStorage.getItem('access_token');
        if (!token) {
            window.location.href = '/login.html?redirect=/star/index.html';
            return false;
        }
        return true;
    }

    /**
     * 绑定事件
     */
    function bindEvents() {
        // 控制按钮
        elements.btnZoomIn.addEventListener('click', () => {
            if (graph) {
                const zoom = graph.getZoom();
                graph.zoomTo(zoom * 1.2);
            }
        });

        elements.btnZoomOut.addEventListener('click', () => {
            if (graph) {
                const zoom = graph.getZoom();
                graph.zoomTo(zoom * 0.8);
            }
        });

        elements.btnReset.addEventListener('click', () => {
            if (graph) {
                graph.fitView();
            }
        });

        elements.btnClosePanel.addEventListener('click', () => {
            elements.detailPanel.classList.add('star-detail-panel--collapsed');
            selectedNode = null;
            if (graph) {
                graph.setItemState(selectedNode, 'selected', false);
            }
        });

        // 窗口大小改变时重绘
        window.addEventListener('resize', () => {
            if (graph) {
                graph.changeSize(
                    elements.canvas.offsetWidth,
                    elements.canvas.offsetHeight
                );
            }
        });

        // 移动端菜单
        const menuToggle = document.querySelector('.header__menu-toggle');
        const mobileMenu = document.querySelector('.mobile-menu');
        const menuClose = document.querySelector('.mobile-menu__close');
        const menuOverlay = document.querySelector('.mobile-menu__overlay');

        if (menuToggle && mobileMenu) {
            menuToggle.addEventListener('click', () => {
                mobileMenu.classList.add('mobile-menu--active');
            });

            menuClose?.addEventListener('click', () => {
                mobileMenu.classList.remove('mobile-menu--active');
            });

            menuOverlay?.addEventListener('click', () => {
                mobileMenu.classList.remove('mobile-menu--active');
            });
        }
    }

    /**
     * 加载星图数据
     */
    async function loadStarGraph() {
        try {
            showLoading(true);

            const data = await api.star.getGraph(3);
            
            // 检查是否有测评数据
            if (!data.metadata?.has_assessment) {
                showEmptyState();
                return;
            }

            graphData = data;
            renderGraph(data);
            showGraphUI();

        } catch (error) {
            console.error('加载星图失败:', error);
            
            // 处理403错误 - 用户未登录或token无效
            if (error.status === 403 || error.code === 1002) {
                showError('访问被拒绝，请重新登录');
                setTimeout(() => {
                    window.location.href = '/login.html?redirect=/star/index.html';
                }, 2000);
                return;
            }
            
            // 处理401错误 - 未授权
            if (error.status === 401 || error.code === 1001) {
                showError('请先登录');
                setTimeout(() => {
                    window.location.href = '/login.html?redirect=/star/index.html';
                }, 2000);
                return;
            }
            
            if (error.message?.includes('请先完成') || error.message?.includes('测评')) {
                showEmptyState();
            } else {
                showError(error.message || '加载星图失败，请稍后重试');
            }
        } finally {
            showLoading(false);
        }
    }

    /**
     * 渲染星图
     */
    function renderGraph(data) {
        const { nodes, edges } = data;

        // 准备 G6 数据格式
        const g6Nodes = nodes.map(node => ({
            id: node.id,
            type: getG6NodeType(node.node_type),
            label: node.title,
            size: node.size || 40,
            style: {
                fill: node.color || '#4A90D9',
                stroke: '#fff',
                lineWidth: 2,
                cursor: 'pointer'
            },
            labelCfg: {
                position: 'bottom',
                offset: 8,
                style: {
                    fill: '#1A1A2E',
                    fontSize: 12,
                    fontWeight: node.level <= 2 ? 600 : 400
                }
            },
            // 原始数据
            data: node
        }));

        const g6Edges = edges.map(edge => ({
            source: edge.source,
            target: edge.target,
            style: {
                stroke: '#c5c5c5',
                lineWidth: 1 + edge.weight * 2,
                opacity: 0.6,
                endArrow: {
                    path: G6.Arrow.triangle(6, 8, 0),
                    fill: '#c5c5c5'
                }
            },
            data: edge
        }));

        // 初始化 G6 图
        graph = new G6.Graph({
            container: 'star-canvas',
            width: elements.canvas.offsetWidth,
            height: elements.canvas.offsetHeight,
            modes: {
                default: ['drag-canvas', 'zoom-canvas', 'drag-node']
            },
            layout: {
                type: 'force2',
                preventOverlap: true,
                nodeSpacing: 50,
                edgeDistance: 100,
                linkDistance: 120,
                nodeStrength: -100,
                edgeStrength: 0.2,
                center: [elements.canvas.offsetWidth / 2, elements.canvas.offsetHeight / 2]
            },
            defaultNode: {
                // 不设置 style.fill，让每个节点的颜色独立设置
                style: {
                    stroke: '#fff',
                    lineWidth: 2,
                    shadowColor: 'rgba(0,0,0,0.1)',
                    shadowBlur: 10,
                    shadowOffsetX: 0,
                    shadowOffsetY: 4
                }
            },
            defaultEdge: {
                style: {
                    opacity: 0.4
                }
            },
            nodeStateStyles: {
                selected: {
                    stroke: '#1E3A5F',
                    lineWidth: 3,
                    shadowBlur: 20,
                    shadowColor: 'rgba(30, 58, 95, 0.3)'
                },
                hover: {
                    stroke: '#4A90D9',
                    lineWidth: 2
                },
                highlight: {
                    stroke: '#FFD700',
                    lineWidth: 4,
                    shadowBlur: 30,
                    shadowColor: 'rgba(255, 215, 0, 0.5)'
                },
                dim: {
                    opacity: 0.2
                }
            }
        });

        // 加载数据
        graph.data({
            nodes: g6Nodes,
            edges: g6Edges
        });

        graph.render();

        // 绑定节点点击事件
        graph.on('node:click', (evt) => {
            const { item } = evt;
            const nodeData = item.getModel().data;
            handleNodeClick(nodeData, item);
        });

        graph.on('node:mouseenter', (evt) => {
            const { item } = evt;
            graph.setItemState(item, 'hover', true);
        });

        graph.on('node:mouseleave', (evt) => {
            const { item } = evt;
            graph.setItemState(item, 'hover', false);
        });

        // 双击聚焦节点
        graph.on('node:dblclick', (evt) => {
            const { item } = evt;
            graph.focusItem(item, true, {
                duration: 300,
                easing: 'easeCubic'
            });
        });

        // 初始适配视图
        setTimeout(() => {
            graph.fitView(20);
        }, 500);
    }

    /**
     * 获取 G6 节点类型
     */
    function getG6NodeType(nodeType) {
        const typeMap = {
            'root': 'star',
            'category': 'hexagon',
            'strength': 'circle',
            'insight': 'diamond'
        };
        return typeMap[nodeType] || 'circle';
    }

    /**
     * 处理节点点击
     */
    function handleNodeClick(nodeData, graphItem) {
        selectedNode = graphItem;

        // 高亮选中节点
        graph.getNodes().forEach(node => {
            graph.setItemState(node, 'selected', false);
        });
        graph.setItemState(graphItem, 'selected', true);

        // 显示详情面板
        showNodeDetail(nodeData);
        elements.detailPanel.classList.remove('star-detail-panel--collapsed');
    }

    /**
     * 显示节点详情
     */
    function showNodeDetail(node) {
        const { node_type, title, description, score, rank, metadata, color } = node;

        // 构建类型标签
        const typeLabels = {
            'root': '我的星图',
            'category': '美德类别',
            'strength': '性格优势',
            'insight': 'AI洞察'
        };

        // 构建图标
        const icons = {
            'root': '✨',
            'category': '🎯',
            'strength': '💪',
            'insight': '💡'
        };

        // 构建分数显示
        let scoreHtml = '';
        if (score !== null && score !== undefined) {
            scoreHtml = `
                <div class="node-info-card__score">
                    <div class="node-info-card__score-value">${Math.round(score)}</div>
                    <div class="node-info-card__score-label">得分</div>
                </div>
            `;
        }

        // 构建排名显示
        let rankHtml = '';
        if (rank) {
            rankHtml = `<span style="margin-left: 8px; color: #F39C12;">#${rank}</span>`;
        }

        // 构建详情HTML
        const html = `
            <div class="node-info-card">
                <div class="node-info-card__header">
                    <div class="node-info-card__icon" style="background: ${color}20; color: ${color};">
                        ${icons[node_type] || '📌'}
                    </div>
                    <div class="node-info-card__title">
                        <div class="node-info-card__name">${title}${rankHtml}</div>
                        <div class="node-info-card__type">${typeLabels[node_type] || node_type}</div>
                    </div>
                    ${scoreHtml}
                </div>
                <div class="node-info-card__description">
                    ${description || '暂无描述'}
                </div>
            </div>

            ${metadata?.development_tips ? `
                <div class="node-info-card" style="margin-top: 16px;">
                    <div style="font-size: 13px; font-weight: 600; color: var(--color-text); margin-bottom: 8px;">
                        💡 发展建议
                    </div>
                    <div style="font-size: 13px; color: var(--color-text-secondary); line-height: 1.6;">
                        ${metadata.development_tips}
                    </div>
                </div>
            ` : ''}

            ${node_type === 'root' ? `
                <div class="ai-suggestions">
                    <div class="ai-suggestions__title">探索建议</div>
                    <div class="ai-suggestion-item" onclick="location.href='/assessment/index.html'">
                        查看详细测评报告
                    </div>
                    <div class="ai-suggestion-item" onclick="sendExplorePrompt('我想与AI教练探讨如何更好地应用我的性格优势到日常生活中，请帮我分析我的优势组合特点以及具体的应用场景。')">
                        与 AI 教练探讨优势应用
                    </div>
                </div>
            ` : ''}

            ${node_type === 'category' ? `
                <div class="ai-suggestions">
                    <div class="ai-suggestions__title">探索建议</div>
                    <div class="ai-suggestion-item" id="btn-expand-virtue">
                        了解${title}领域的具体优势
                    </div>
                    <div class="ai-suggestion-item" onclick="sendExplorePrompt('我想深入了解${title}这个美德领域，请帮我分析${title}包含哪些具体优势，这些优势在我的测评中表现如何，以及我如何在日常生活中更好地发挥${title}相关的优势。')">
                        探索如何在日常生活中发挥${title}
                    </div>
                </div>
            ` : ''}
        `;

        elements.detailContent.innerHTML = html;

        // 绑定"了解具体优势"按钮事件
        if (node_type === 'category') {
            const expandBtn = document.getElementById('btn-expand-virtue');
            if (expandBtn) {
                expandBtn.addEventListener('click', () => {
                    expandVirtueNodes(node.id, node.title);
                });
            }
        }
    }

    /**
     * 展开美德节点下的所有优势节点
     * @param {string} virtueNodeId - 美德节点ID
     * @param {string} virtueTitle - 美德名称
     */
    function expandVirtueNodes(virtueNodeId, virtueTitle) {
        if (!graph) return;

        // 找到该美德下的所有优势子节点
        const virtueNode = graph.findById(virtueNodeId);
        if (!virtueNode) return;

        // 获取所有边，找到以该美德为源节点的边（即美德→优势的边）
        const edges = graph.getEdges();
        const childNodes = [];

        edges.forEach(edge => {
            const source = edge.getSource();
            const target = edge.getTarget();
            if (source.getID() === virtueNodeId) {
                childNodes.push(target);
            }
        });

        if (childNodes.length === 0) {
            showToast(`暂无${virtueTitle}领域的优势数据`, 'info');
            return;
        }

        // 高亮所有子节点
        graph.getNodes().forEach(node => {
            graph.setItemState(node, 'highlight', false);
            graph.setItemState(node, 'dim', true);
        });

        // 高亮美德节点及其子节点
        graph.setItemState(virtueNode, 'dim', false);
        graph.setItemState(virtueNode, 'highlight', true);

        childNodes.forEach(node => {
            graph.setItemState(node, 'dim', false);
            graph.setItemState(node, 'highlight', true);
        });

        // 聚焦到这些节点
        if (childNodes.length > 0) {
            graph.focusItem(virtueNode, true, {
                duration: 500,
                easing: 'easeCubic'
            });
        }

        showToast(`已高亮${virtueTitle}领域的${childNodes.length}项优势`, 'success');

        // 3秒后恢复所有节点
        setTimeout(() => {
            graph.getNodes().forEach(node => {
                graph.setItemState(node, 'highlight', false);
                graph.setItemState(node, 'dim', false);
            });
        }, 3000);
    }

    /**
     * 显示加载状态
     */
    function showLoading(show) {
        elements.loading.style.display = show ? 'block' : 'none';
    }

    /**
     * 显示空状态
     */
    function showEmptyState() {
        elements.emptyState.style.display = 'block';
        elements.infoBar.style.display = 'none';
        elements.controls.style.display = 'none';
        elements.legend.style.display = 'none';
    }

    /**
     * 显示星图UI
     */
    function showGraphUI() {
        elements.infoBar.style.display = 'block';
        elements.controls.style.display = 'flex';
        elements.legend.style.display = 'block';
    }

    /**
     * 显示错误信息
     */
    function showError(message) {
        elements.detailContent.innerHTML = `
            <div class="star-empty-state">
                <div class="star-empty-state__icon">⚠️</div>
                <h2 class="star-empty-state__title">出错了</h2>
                <p class="star-empty-state__desc">${message}</p>
                <button class="btn btn--primary" onclick="location.reload()">重试</button>
            </div>
        `;
        elements.detailPanel.classList.remove('star-detail-panel--collapsed');
    }

    /**
     * 发送探索建议到AI对话
     * 将prompt存入localStorage，跳转到AI对话页面后自动发送
     * @param {string} prompt - 预设的提示词
     */
    function sendExplorePrompt(prompt) {
        // 将prompt存入localStorage，chat页面会读取并自动发送
        localStorage.setItem('pending_explore_prompt', prompt);
        localStorage.setItem('pending_explore_timestamp', Date.now());
        // 跳转到AI对话页面
        window.location.href = '/chat/index.html?source=star_explore';
    }

    // 暴露到全局，供HTML中的onclick调用
    window.sendExplorePrompt = sendExplorePrompt;

    // 启动
    document.addEventListener('DOMContentLoaded', init);

})();
