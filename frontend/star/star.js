/**
 * 星图页面主逻辑 (Star Map 3.0)
 * 支持用户主动构建、持久化节点管理
 */

(function() {
    'use strict';

    // ========== 全局变量 ==========
    let graph = null;
    let graphData = null;
    let selectedNode = null;
    let currentGraphId = null;      // 当前星图ID
    let tempNodes = new Map();      // 临时节点存储（id -> nodeData）
    let isConnectMode = false;      // 是否连接节点模式
    let pendingRelationType = 'relates_to';  // 待创建的关系类型
    let isLoading = false;          // 是否正在加载
    let pendingEdges = new Map();   // 临时节点的待创建边 (sourceId -> [{targetId, relationType}])

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
        btnAddNode: document.getElementById('btn-add-node'),
        btnClosePanel: document.getElementById('btn-close-panel')
    };

    // 节点类型配置
    const nodeTypeConfig = {
        root: { shape: 'star', size: 80, color: '#1E3A5F', label: '我的星图' },
        category: { shape: 'hexagon', size: 60, color: '#4A90D9', label: '美德类别' },
        strength: { shape: 'circle', size: 40, color: '#87CEEB', label: '性格优势' },
        insight: { shape: 'diamond', size: 30, color: '#F39C12', label: 'AI洞察' },
        goal: { shape: 'circle', size: 40, color: '#50C878', label: '目标' },
        task: { shape: 'rect', size: 35, color: '#95A5A6', label: '任务' }
    };

    // 节点类型选项（用于新建/编辑节点）
    const nodeTypeOptions = [
        { value: 'strength', label: '💪 性格优势', color: '#4A90D9' },
        { value: 'insight', label: '💡 AI洞察', color: '#F39C12' },
        { value: 'goal', label: '🎯 目标', color: '#50C878' },
        { value: 'task', label: '📋 任务', color: '#9B59B6' }
    ];

    // 关系类型选项
    const relationTypeOptions = [
        { value: 'belongs_to', label: '归属', desc: '子节点归属于父节点' },
        { value: 'leads_to', label: '导致', desc: '顺序关系，A导致B' },
        { value: 'suggests', label: '建议', desc: '建议或推荐关系' },
        { value: 'relates_to', label: '相关', desc: '一般关联关系' }
    ];

    // 边样式映射
    const edgeStyleMap = {
        belongs_to: { stroke: '#4A90D9', lineDash: [], label: '归属' },
        leads_to: { stroke: '#50C878', lineDash: [], label: '导致' },
        suggests: { stroke: '#F39C12', lineDash: [5, 5], label: '建议' },
        relates_to: { stroke: '#999999', lineDash: [3, 3], label: '相关' }
    };

    // ========== 初始化 ==========
    
    /**
     * 初始化页面
     */
    async function init() {
        if (!checkAuth()) return;
        
        try {
            showLoading(true);
            
            // 初始化默认星图
            await initDefaultGraph();
            
            bindEvents();
            await loadStarGraph();
        } catch (error) {
            console.error('初始化失败:', error);
            showError('初始化失败: ' + error.message);
        } finally {
            showLoading(false);
        }
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
     * 初始化默认星图
     */
    async function initDefaultGraph() {
        try {
            // 获取用户的星图列表
            const graphs = await api.star.getGraphs();
            
            // 查找默认星图
            let defaultGraph = graphs.find(g => g.is_default);
            
            if (!defaultGraph) {
                // 没有默认星图，检查是否有VIA测评数据
                try {
                    const viaGraph = await api.star.importFromVia();
                    currentGraphId = viaGraph.graph_id;
                    showToast('已从VIA测评导入星图', 'success');
                } catch (viaError) {
                    // 没有VIA数据，创建空星图
                    const newGraph = await api.star.createGraph('我的星图', 'main');
                    currentGraphId = newGraph.id;
                    showToast('已创建新星图', 'info');
                }
            } else {
                currentGraphId = defaultGraph.id;
            }
        } catch (error) {
            console.error('初始化星图失败:', error);
            throw error;
        }
    }

    // ========== 事件绑定 ==========
    
    /**
     * 绑定事件
     */
    function bindEvents() {
        console.log('[星图] 绑定事件，btnAddNode:', elements.btnAddNode);
        
        // 添加节点按钮
        if (elements.btnAddNode) {
            elements.btnAddNode.addEventListener('click', () => {
                console.log('[星图] 添加节点按钮被点击');
                showAddNodeDialog();
            });
        } else {
            console.error('[星图] 未找到添加节点按钮');
        }

        // 控制按钮
        elements.btnZoomIn?.addEventListener('click', () => {
            if (graph) {
                const zoom = graph.getZoom();
                graph.zoomTo(zoom * 1.2);
            }
        });

        elements.btnZoomOut?.addEventListener('click', () => {
            if (graph) {
                const zoom = graph.getZoom();
                graph.zoomTo(zoom * 0.8);
            }
        });

        elements.btnReset?.addEventListener('click', () => {
            if (graph) {
                graph.fitView();
            }
        });

        elements.btnClosePanel?.addEventListener('click', closeDetailPanel);

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
        bindMobileMenu();
        
        // 页面离开警告（有未保存节点时）
        window.addEventListener('beforeunload', (e) => {
            if (tempNodes.size > 0) {
                e.preventDefault();
                e.returnValue = '有未保存的节点，确定要离开吗？';
            }
        });
    }

    /**
     * 绑定移动端菜单
     */
    function bindMobileMenu() {
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

    // ========== 数据加载 ==========
    
    /**
     * 加载星图数据
     */
    async function loadStarGraph() {
        if (!currentGraphId) {
            showEmptyState();
            return;
        }

        try {
            showLoading(true);
            
            // 从数据库加载星图详情（包含持久化节点）
            const graphDetail = await api.star.getGraphDetail(currentGraphId);
            
            if (!graphDetail || !graphDetail.nodes) {
                showEmptyState();
                return;
            }
            
            graphData = graphDetail;
            
            // 清空临时节点（每次重新加载时）
            tempNodes.clear();
            updateTempNodesWarning();
            
            renderGraph(graphDetail);
            showGraphUI();

        } catch (error) {
            console.error('加载星图失败:', error);
            handleLoadError(error);
        } finally {
            showLoading(false);
        }
    }

    /**
     * 处理加载错误
     */
    function handleLoadError(error) {
        // 处理403/401错误
        if (error.status === 403 || error.status === 401 || [1001, 1002].includes(error.code)) {
            showError('登录已过期，请重新登录');
            setTimeout(() => {
                window.location.href = '/login.html?redirect=/star/index.html';
            }, 2000);
            return;
        }
        
        showError(error.message || '加载星图失败，请稍后重试');
    }

    // ========== 图形渲染 ==========
    
    /**
     * 渲染星图
     */
    function renderGraph(data) {
        const { nodes, edges } = data;
        
        // 为节点计算初始位置（如果没有）
        const canvasWidth = elements.canvas.offsetWidth;
        const canvasHeight = elements.canvas.offsetHeight;
        const centerX = canvasWidth / 2;
        const centerY = canvasHeight / 2;
        
        // 按层级分组节点
        const nodesByLevel = {};
        nodes.forEach((node, index) => {
            const level = node.level || 3;
            if (!nodesByLevel[level]) nodesByLevel[level] = [];
            nodesByLevel[level].push({ node, index });
        });
        
        // 计算节点位置
        const g6Nodes = nodes.map((node, index) => {
            const isPersisted = !tempNodes.has(node.id);
            const config = nodeTypeConfig[node.node_type] || nodeTypeConfig.goal;
            
            // 如果没有位置，根据层级计算初始位置
            let x = node.position_x;
            let y = node.position_y;
            
            if (x == null || y == null) {
                const level = node.level || 3;
                const levelNodes = nodesByLevel[level];
                const nodeIndex = levelNodes.findIndex(n => n.index === index);
                const totalInLevel = levelNodes.length;
                
                // 根据层级设置半径
                const radius = level === 1 ? 0 : level === 2 ? 150 : 300;
                
                if (level === 1) {
                    // 根节点在中心
                    x = centerX;
                    y = centerY;
                } else {
                    // 其他节点按角度分布
                    const angle = (2 * Math.PI * nodeIndex) / totalInLevel - Math.PI / 2;
                    x = centerX + radius * Math.cos(angle);
                    y = centerY + radius * Math.sin(angle);
                }
            }
            
            return {
                id: node.id,
                type: getG6NodeType(node.node_type),
                label: node.title,
                size: node.size || config.size,
                x: x,
                y: y,
                style: {
                    fill: node.color || config.color,
                    stroke: isPersisted ? '#fff' : '#999',
                    lineWidth: isPersisted ? 2 : 2,
                    lineDash: isPersisted ? null : [5, 5],
                    opacity: isPersisted ? 1 : 0.7,
                    cursor: 'pointer'
                },
                labelCfg: {
                    position: 'bottom',
                    offset: 8,
                    style: {
                        fill: isPersisted ? '#1A1A2E' : '#666',
                        fontSize: 12,
                        fontWeight: node.level <= 2 ? 600 : 400
                    }
                },
                // 原始数据
                data: node
            };
        });

        const g6Edges = edges.map(edge => ({
            source: edge.source,
            target: edge.target,
            style: {
                stroke: '#c5c5c5',
                lineWidth: 1 + (edge.weight || 0.5) * 2,
                opacity: 0.6,
                endArrow: {
                    path: G6.Arrow.triangle(6, 8, 0),
                    fill: '#c5c5c5'
                }
            },
            data: edge
        }));

        // 初始化 G6 图
        initG6Graph(g6Nodes, g6Edges);
    }

    /**
     * 初始化G6图实例
     */
    function initG6Graph(nodes, edges) {
        // 如果已存在，先销毁
        if (graph) {
            graph.destroy();
        }

        // 检查是否所有节点都有初始位置
        const hasPositions = nodes.every(n => n.x != null && n.y != null);

        graph = new G6.Graph({
            container: 'star-canvas',
            width: elements.canvas.offsetWidth,
            height: elements.canvas.offsetHeight,
            modes: {
                default: ['drag-canvas', 'zoom-canvas', 'drag-node']
            },
            // 如果节点有初始位置，不使用力导向布局
            layout: hasPositions ? undefined : {
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
                style: {
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
        graph.data({ nodes, edges });
        graph.render();

        // 绑定事件
        bindGraphEvents();

        // 初始适配视图
        setTimeout(() => {
            graph.fitView(20);
        }, 500);
    }

    /**
     * 绑定图形事件
     */
    function bindGraphEvents() {
        // 节点点击
        graph.on('node:click', (evt) => {
            const { item } = evt;
            const nodeData = item.getModel().data;
            handleNodeClick(nodeData, item);
        });

        // 节点双击 - 快速扩展
        graph.on('node:dblclick', (evt) => {
            const { item } = evt;
            const nodeData = item.getModel().data;
            const { id, node_type } = nodeData;
            
            // 根节点和美德类别节点不允许扩展
            if (node_type === 'root' || node_type === 'category') {
                showToast('根节点和美德类别不支持扩展', 'warning');
                return;
            }
            
            // 显示扩展对话框
            showExpandNodeDialog(id, nodeData);
        });

        // 鼠标悬停
        graph.on('node:mouseenter', (evt) => {
            const { item } = evt;
            graph.setItemState(item, 'hover', true);
        });

        graph.on('node:mouseleave', (evt) => {
            const { item } = evt;
            graph.setItemState(item, 'hover', false);
        });

        // 双击聚焦
        graph.on('node:dblclick', (evt) => {
            const { item } = evt;
            graph.focusItem(item, true, {
                duration: 300,
                easing: 'easeCubic'
            });
        });
        
        // 拖拽结束后保存位置
        graph.on('node:dragend', async (evt) => {
            const { item } = evt;
            const nodeData = item.getModel().data;
            const model = item.getModel();
            
            // 只保存持久化节点的位置
            if (!tempNodes.has(nodeData.id)) {
                try {
                    await api.star.moveNode(nodeData.id, model.x, model.y);
                } catch (error) {
                    console.error('保存位置失败:', error);
                }
            }
        });
    }

    /**
     * 获取 G6 节点类型
     */
    function getG6NodeType(nodeType) {
        const typeMap = {
            'root': 'star',
            'category': 'hexagon',
            'strength': 'circle',
            'insight': 'diamond',
            'goal': 'circle',
            'task': 'rect'
        };
        return typeMap[nodeType] || 'circle';
    }

    // ========== 节点交互 ==========
    
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
     * 关闭详情面板
     */
    function closeDetailPanel() {
        elements.detailPanel.classList.add('star-detail-panel--collapsed');
        if (selectedNode && graph) {
            graph.setItemState(selectedNode, 'selected', false);
        }
        selectedNode = null;
    }

    /**
     * 显示添加节点对话框
     */
    async function showAddNodeDialog() {
        console.log('[星图] 显示添加节点对话框');
        
        const nodeData = await showCreateNodeModal();
        if (!nodeData) return; // 用户取消
        
        const nodeId = 'temp_' + Date.now();
        const canvasWidth = elements.canvas.offsetWidth;
        const canvasHeight = elements.canvas.offsetHeight;
        
        // 在画布中心附近随机位置
        const x = canvasWidth / 2 + (Math.random() - 0.5) * 200;
        const y = canvasHeight / 2 + (Math.random() - 0.5) * 200;
        
        // 根据类型获取视觉配置
        const typeConfig = nodeTypeConfig[nodeData.node_type] || nodeTypeConfig.goal;
        
        const newNode = {
            id: nodeId,
            node_type: nodeData.node_type,
            title: nodeData.title,
            description: nodeData.description,
            category: nodeData.category,
            level: 3,
            size: typeConfig.size || 40,
            color: typeConfig.color || '#50C878',
            shape: typeConfig.shape || 'circle',
            x: x,
            y: y,
            is_expanded: false
        };
        
        // 添加到临时节点存储
        tempNodes.set(nodeId, newNode);
        
        // 添加到图中
        if (graph) {
            graph.addItem('node', {
                id: nodeId,
                type: typeConfig.shape || 'circle',
                label: newNode.title,
                x: x,
                y: y,
                size: newNode.size,
                style: {
                    fill: newNode.color,
                    stroke: '#999',
                    lineDash: [5, 5],
                    opacity: 0.7
                },
                labelCfg: {
                    position: 'bottom',
                    style: {
                        fill: '#666',
                        fontSize: 12
                    }
                },
                data: newNode
            });
            
            // 显示临时节点提示
            updateTempNodesWarning();
            showToast('已添加临时节点，点击保存以持久化', 'success');
            
            // 自动选中新节点
            const graphNode = graph.findById(nodeId);
            if (graphNode) {
                handleNodeClick(newNode, graphNode);
            }
        }
    }
    
    /**
     * 显示创建节点模态框
     */
    function showCreateNodeModal() {
        return new Promise((resolve) => {
            const modal = document.createElement('div');
            modal.id = 'create-node-modal';
            modal.style.cssText = `
                position: fixed;
                top: 0; left: 0; right: 0; bottom: 0;
                background: rgba(0,0,0,0.5);
                display: flex;
                align-items: center;
                justify-content: center;
                z-index: 2000;
            `;
            
            const content = document.createElement('div');
            content.style.cssText = `
                background: white;
                border-radius: 12px;
                padding: 24px;
                width: 400px;
                max-width: 90%;
                max-height: 80vh;
                overflow-y: auto;
            `;
            
            const nodeTypeOptionsHtml = nodeTypeOptions.map(opt => 
                `<option value="${opt.value}">${opt.label}</option>`
            ).join('');
            
            content.innerHTML = `
                <h3 style="margin: 0 0 20px 0; font-size: 18px; color: #333;">添加新节点</h3>
                
                <div style="margin-bottom: 16px;">
                    <label style="display: block; font-size: 13px; color: #666; margin-bottom: 6px;">节点名称 *</label>
                    <input type="text" id="new-node-title" placeholder="输入节点名称" 
                        style="width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 6px; font-size: 14px; box-sizing: border-box;">
                </div>
                
                <div style="margin-bottom: 16px;">
                    <label style="display: block; font-size: 13px; color: #666; margin-bottom: 6px;">节点描述</label>
                    <textarea id="new-node-desc" rows="3" placeholder="输入节点描述（可选）"
                        style="width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 6px; font-size: 14px; resize: vertical; box-sizing: border-box;"></textarea>
                </div>
                
                <div style="margin-bottom: 16px;">
                    <label style="display: block; font-size: 13px; color: #666; margin-bottom: 6px;">节点类型</label>
                    <select id="new-node-type" 
                        style="width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 6px; font-size: 14px; background: white;">
                        ${nodeTypeOptionsHtml}
                    </select>
                </div>
                
                <div style="margin-bottom: 20px;">
                    <label style="display: block; font-size: 13px; color: #666; margin-bottom: 6px;">归属类型 / 分类</label>
                    <input type="text" id="new-node-category" placeholder="如：学习知识、工作任务、生活记录等" 
                        style="width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 6px; font-size: 14px; box-sizing: border-box;">
                </div>
                
                <div style="display: flex; gap: 12px;">
                    <button id="cancel-create-node" style="flex: 1; padding: 12px; border: 1px solid #ddd; background: #f5f5f5; border-radius: 6px; cursor: pointer; font-size: 14px;">
                        取消
                    </button>
                    <button id="confirm-create-node" style="flex: 1; padding: 12px; border: none; background: #4A90D9; color: white; border-radius: 6px; cursor: pointer; font-size: 14px;">
                        创建节点
                    </button>
                </div>
            `;
            
            modal.appendChild(content);
            document.body.appendChild(modal);
            
            // 绑定事件
            document.getElementById('cancel-create-node').addEventListener('click', () => {
                modal.remove();
                resolve(null);
            });
            
            document.getElementById('confirm-create-node').addEventListener('click', () => {
                const title = document.getElementById('new-node-title').value.trim();
                const description = document.getElementById('new-node-desc').value.trim();
                const node_type = document.getElementById('new-node-type').value;
                const category = document.getElementById('new-node-category').value.trim();
                
                if (!title) {
                    showToast('请输入节点名称', 'error');
                    return;
                }
                
                modal.remove();
                resolve({
                    title,
                    description,
                    node_type,
                    category: category || null
                });
            });
            
            // 点击背景关闭
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    modal.remove();
                    resolve(null);
                }
            });
            
            // 自动聚焦到名称输入框
            setTimeout(() => {
                document.getElementById('new-node-title')?.focus();
            }, 100);
        });
    }
    
    /**
     * 获取节点类型标签
     */
    function getNodeTypeLabel(nodeType) {
        const labels = {
            'root': '根节点',
            'category': '类别',
            'strength': '性格优势',
            'insight': 'AI洞察',
            'goal': '目标',
            'task': '任务',
            'habit': '习惯',
            'preference': '偏好',
            'resource': '资源',
            'event': '事件'
        };
        return labels[nodeType] || nodeType;
    }

    /**
     * 显示节点详情
     */
    function showNodeDetail(node) {
        const { id, node_type, title, description, score, rank, metadata, color } = node;
        
        // 判断节点状态
        const isRootOrCategory = node_type === 'root' || node_type === 'category';
        const isPersisted = !tempNodes.has(id);
        const config = nodeTypeConfig[node_type] || { label: '节点' };

        // 构建图标
        const icons = {
            'root': '✨',
            'category': '🎯',
            'strength': '💪',
            'insight': '💡',
            'goal': '🎯',
            'task': '📋'
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
                    <div class="node-info-card__title" style="flex: 1;">
                        <input type="text" id="edit-node-title" value="${title}" 
                            style="font-size: 16px; font-weight: 600; color: var(--color-text); border: 1px solid transparent; border-bottom: 1px solid #ddd; background: transparent; width: 100%; padding: 4px 0;"
                            onfocus="this.style.borderBottom='2px solid #4A90D9'" 
                            onblur="this.style.borderBottom='1px solid #ddd'"
                        >
                        <div class="node-info-card__type" style="margin-top: 4px;">${config.label}${rankHtml}</div>
                    </div>
                    ${scoreHtml}
                </div>
                <div class="node-info-card__description" style="margin-top: 12px;">
                    <label style="font-size: 12px; color: #999; margin-bottom: 4px; display: block;">描述</label>
                    <textarea id="edit-node-desc" rows="3"
                        style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 6px; font-size: 13px; resize: vertical;"
                        placeholder="添加节点描述...">${description || ''}</textarea>
                </div>
                
                ${!isRootOrCategory ? `
                <div style="margin-top: 12px;">
                    <label style="font-size: 12px; color: #999; margin-bottom: 4px; display: block;">节点类型</label>
                    <select id="edit-node-type" style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 6px; font-size: 13px;"
                        onchange="this.style.color= this.options[this.selectedIndex].style.color">
                        ${nodeTypeOptions.map(opt => `
                            <option value="${opt.value}" ${node_type === opt.value ? 'selected' : ''} style="color: ${opt.color}">
                                ${opt.label}
                            </option>
                        `).join('')}
                    </select>
                </div>
                
                <div style="margin-top: 12px;">
                    <label style="font-size: 12px; color: #999; margin-bottom: 4px; display: block;">归属类型 / 分类</label>
                    <input type="text" id="edit-node-category" value="${node.category || ''}" 
                        placeholder="如：学习知识、工作任务、生活记录等"
                        style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 6px; font-size: 13px;"
                    >
                </div>
                ` : ''}
            </div>

            ${metadata?.development_tips ? `
                <div class="node-info-card" style="margin-top: 16px; border-left: 3px solid #F39C12;">
                    <div style="font-size: 13px; font-weight: 600; color: var(--color-text); margin-bottom: 8px; display: flex; align-items: center; gap: 6px;">
                        💡 发展建议
                    </div>
                    <div style="font-size: 13px; color: var(--color-text-secondary); line-height: 1.6; white-space: pre-wrap;">
                        ${metadata.development_tips}
                    </div>
                </div>
            ` : node_type === 'strength' ? `
                <div class="node-info-card" style="margin-top: 16px; border-left: 3px solid #e0e0e0;">
                    <div style="font-size: 13px; font-weight: 600; color: var(--color-text); margin-bottom: 8px;">
                        💡 发展建议
                    </div>
                    <div style="font-size: 13px; color: var(--color-text-secondary); line-height: 1.6;">
                        完成 VIA 测评后，AI 将为您生成个性化的发展建议。
                        <a href="/assessment/index.html" style="color: #4A90D9; text-decoration: underline; margin-left: 4px;">去测评 →</a>
                    </div>
                </div>
            ` : ''}
            
            ${metadata?.related_strengths ? `
                <div class="node-info-card" style="margin-top: 12px; border-left: 3px solid #4A90D9;">
                    <div style="font-size: 13px; font-weight: 600; color: var(--color-text); margin-bottom: 8px;">
                        🔗 关联优势
                    </div>
                    <div style="font-size: 13px; color: var(--color-text-secondary); line-height: 1.6;">
                        ${Array.isArray(metadata.related_strengths) ? metadata.related_strengths.join('、') : metadata.related_strengths}
                    </div>
                </div>
            ` : ''}

            <!-- 持久化控制区域 -->
            <div class="persistence-control" style="margin-top: 16px; padding: 12px; background: #f5f5f5; border-radius: 8px;">
                <label class="checkbox-label" style="display: flex; align-items: center; cursor: ${isRootOrCategory ? 'not-allowed' : 'pointer'}; opacity: ${isRootOrCategory ? 0.6 : 1};">
                    <input type="checkbox" id="chk-save-to-graph" 
                        ${isPersisted || isRootOrCategory ? 'checked' : ''} 
                        ${isRootOrCategory ? 'disabled' : ''}
                        style="margin-right: 8px;"
                    >
                    <span>保存到星图（下次自动加载）</span>
                </label>
                <p style="margin: 4px 0 0 24px; font-size: 12px; color: #666;">
                    ${isRootOrCategory ? '根节点和美德类别节点自动保存' : '勾选后节点将被持久化保存'}
                </p>
            </div>

            <!-- 操作按钮 -->
            <div style="margin-top: 16px; display: flex; gap: 8px; justify-content: flex-end;">
                ${!isRootOrCategory ? `
                    <button type="button" class="btn btn--danger" id="btn-delete-node" style="background: #e74c3c; color: white; border: none; padding: 8px 16px; border-radius: 6px; cursor: pointer;">删除节点</button>
                ` : ''}
                <button type="button" class="btn btn--secondary" id="btn-cancel-node" style="background: #95a5a6; color: white; border: none; padding: 8px 16px; border-radius: 6px; cursor: pointer;">取消</button>
                <button type="button" class="btn btn--primary" id="btn-save-node" style="background: #3498db; color: white; border: none; padding: 8px 16px; border-radius: 6px; cursor: pointer;">保存</button>
            </div>

            <!-- 连接节点按钮 -->
            ${!isRootOrCategory ? `
                <div style="margin-top: 16px;">
                    <button type="button" class="btn btn--secondary" id="btn-connect-node" style="background: #9b59b6; color: white; border: none; padding: 8px 16px; border-radius: 6px; cursor: pointer; width: 100%; display: flex; align-items: center; justify-content: center; gap: 6px;">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <line x1="5" y1="12" x2="19" y2="12"/>
                            <polyline points="12 5 19 12 12 19"/>
                        </svg>
                        连接到其他节点
                    </button>
                    <p style="margin-top: 8px; font-size: 12px; color: #666; text-align: center;">点击后选择要连接的目标节点</p>
                </div>
                
                <div style="margin-top: 12px;">
                    <button type="button" class="btn btn--secondary" id="btn-expand-node" style="background: #3498db; color: white; border: none; padding: 8px 16px; border-radius: 6px; cursor: pointer; width: 100%; display: flex; align-items: center; justify-content: center; gap: 6px;">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <circle cx="12" cy="12" r="10"/>
                            <line x1="12" y1="8" x2="12" y2="16"/>
                            <line x1="8" y1="12" x2="16" y2="12"/>
                        </svg>
                        扩展节点（AI生成子节点）
                    </button>
                    <p style="margin-top: 8px; font-size: 12px; color: #666; text-align: center;">双击节点也可快速扩展</p>
                </div>
            ` : ''}

            <!-- AI建议 -->
            <div class="ai-suggestions" style="margin-top: 16px;">
                <div class="ai-suggestions__title">AI 智能建议</div>
                ${node_type === 'root' ? `
                    <div class="ai-suggestion-item" onclick="location.href='/assessment/index.html'">
                        查看详细测评报告
                    </div>
                    <div class="ai-suggestion-item" onclick="sendExplorePrompt('我想与AI教练探讨如何更好地应用我的性格优势到日常生活中，请帮我分析我的优势组合特点以及具体的应用场景。')">
                        与 AI 教练探讨优势应用
                    </div>
                ` : (() => {
                    const safeTitle = title.replace(/'/g, "\\'");
                    const safeLabel = config.label.replace(/'/g, "\\'");
                    return `
                    <div class="ai-suggestion-item" onclick="sendExplorePrompt('我想深入探讨「${safeTitle}」这个${safeLabel}，请帮我分析如何更好地发展和应用它。')">
                        与 AI 教练探讨「${title}」
                    </div>
                    <div class="ai-suggestion-item" onclick="sendExplorePrompt('我想了解「${safeTitle}」与其他优势如何组合使用，请给出具体的应用场景和建议。')">
                        探讨优势组合应用
                    </div>
                    `;
                })()}
            </div>
        `;

        elements.detailContent.innerHTML = html;

        // 绑定按钮事件
        bindDetailPanelEvents(id, node);
    }

    /**
     * 绑定详情面板事件
     */
    function bindDetailPanelEvents(nodeId, nodeData) {
        // 保存按钮
        const saveBtn = document.getElementById('btn-save-node');
        if (saveBtn) {
            saveBtn.addEventListener('click', () => saveNode(nodeId, nodeData));
        }

        // 取消按钮
        const cancelBtn = document.getElementById('btn-cancel-node');
        if (cancelBtn) {
            cancelBtn.addEventListener('click', closeDetailPanel);
        }

        // 删除按钮
        const deleteBtn = document.getElementById('btn-delete-node');
        if (deleteBtn) {
            deleteBtn.addEventListener('click', () => deleteNode(nodeId));
        }
        
        // 连接节点按钮
        const connectBtn = document.getElementById('btn-connect-node');
        if (connectBtn) {
            connectBtn.addEventListener('click', () => startConnectMode(nodeId));
        }
        
        // 扩展节点按钮
        const expandBtn = document.getElementById('btn-expand-node');
        if (expandBtn) {
            expandBtn.addEventListener('click', () => showExpandNodeDialog(nodeId, nodeData));
        }
    }
    
    /**
     * 开始连接节点模式
     */
    async function startConnectMode(sourceNodeId) {
        if (!graph) return;
        
        // 1. 先选择关系类型
        const relationType = await showRelationTypeSelector();
        if (!relationType) return; // 用户取消了
        
        pendingRelationType = relationType;
        isConnectMode = true;
        
        const relationLabel = relationTypeOptions.find(opt => opt.value === relationType)?.label || '连接';
        showToast(`请选择要${relationLabel}的目标节点`, 'info');
        
        // 高亮显示可连接的节点
        graph.getNodes().forEach(node => {
            const nodeId = node.getModel().id;
            if (nodeId !== sourceNodeId) {
                graph.setItemState(node, 'highlight', true);
            } else {
                graph.setItemState(node, 'dim', true);
            }
        });
        
        // 临时绑定点击事件
        const handleConnectClick = (evt) => {
            const targetNode = evt.item;
            if (!targetNode || targetNode.getType() !== 'node') return;
            
            const targetId = targetNode.getModel().id;
            if (targetId === sourceNodeId) return;
            
            // 创建连接
            createEdge(sourceNodeId, targetId, pendingRelationType);
            
            // 退出连接模式
            exitConnectMode();
            
            // 移除临时事件监听
            graph.off('node:click', handleConnectClick);
            graph.off('canvas:click', handleCanvasClick);
        };
        
        graph.on('node:click', handleConnectClick);
        
        // 点击空白处取消
        const handleCanvasClick = (evt) => {
            if (!evt.item) {
                exitConnectMode();
                graph.off('node:click', handleConnectClick);
                graph.off('canvas:click', handleCanvasClick);
            }
        };
        
        graph.on('canvas:click', handleCanvasClick);
    }
    
    /**
     * 显示关系类型选择器
     */
    function showRelationTypeSelector() {
        return new Promise((resolve) => {
            // 创建弹窗
            const modal = document.createElement('div');
            modal.id = 'relation-type-modal';
            modal.style.cssText = `
                position: fixed;
                top: 0; left: 0; right: 0; bottom: 0;
                background: rgba(0,0,0,0.5);
                display: flex;
                align-items: center;
                justify-content: center;
                z-index: 2000;
            `;
            
            const content = document.createElement('div');
            content.style.cssText = `
                background: white;
                border-radius: 12px;
                padding: 24px;
                width: 320px;
                max-width: 90%;
            `;
            
            content.innerHTML = `
                <h3 style="margin: 0 0 16px 0; font-size: 16px;">选择关系类型</h3>
                <div style="display: flex; flex-direction: column; gap: 8px;">
                    ${relationTypeOptions.map(opt => `
                        <button class="relation-type-btn" data-type="${opt.value}"
                            style="padding: 12px; border: 1px solid #e0e0e0; border-radius: 8px; background: white; cursor: pointer; text-align: left;"
                        >
                            <div style="font-weight: 600; color: #333;">${opt.label}</div>
                            <div style="font-size: 12px; color: #999; margin-top: 2px;">${opt.desc}</div>
                        </button>
                    `).join('')}
                </div>
                <button id="cancel-relation" style="margin-top: 16px; width: 100%; padding: 10px; border: none; background: #f5f5f5; border-radius: 6px; cursor: pointer;"
                >取消</button>
            `;
            
            modal.appendChild(content);
            document.body.appendChild(modal);
            
            // 绑定按钮事件
            content.querySelectorAll('.relation-type-btn').forEach(btn => {
                btn.addEventListener('click', () => {
                    const type = btn.dataset.type;
                    modal.remove();
                    resolve(type);
                });
                // 悬停效果
                btn.addEventListener('mouseenter', () => {
                    btn.style.background = '#f5f5f5';
                    btn.style.borderColor = '#4A90D9';
                });
                btn.addEventListener('mouseleave', () => {
                    btn.style.background = 'white';
                    btn.style.borderColor = '#e0e0e0';
                });
            });
            
            document.getElementById('cancel-relation').addEventListener('click', () => {
                modal.remove();
                resolve(null);
            });
            
            // 点击背景关闭
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    modal.remove();
                    resolve(null);
                }
            });
        });
    }
    
    /**
     * 退出连接模式
     */
    function exitConnectMode() {
        isConnectMode = false;
        
        // 清除高亮
        graph.getNodes().forEach(node => {
            graph.setItemState(node, 'highlight', false);
            graph.setItemState(node, 'dim', false);
        });
    }
    
    /**
     * 创建边（连接）
     */
    async function createEdge(sourceId, targetId, relationType = 'relates_to') {
        try {
            // 检查是否已存在连接
            const existingEdges = graph.getEdges().filter(edge => {
                const model = edge.getModel();
                return (model.source === sourceId && model.target === targetId);
            });
            
            if (existingEdges.length > 0) {
                showToast('这两个节点已经连接', 'warning');
                return;
            }
            
            // 获取边样式
            const style = edgeStyleMap[relationType] || edgeStyleMap.relates_to;
            
            // 检查是否为临时节点
            const isSourceTemp = tempNodes.has(sourceId);
            const isTargetTemp = tempNodes.has(targetId);
            
            // 添加到图形
            const edgeItem = graph.addItem('edge', {
                source: sourceId,
                target: targetId,
                label: style.label,
                style: {
                    stroke: style.stroke,
                    lineWidth: 2,
                    opacity: 0.8,
                    lineDash: style.lineDash,
                    endArrow: {
                        path: G6.Arrow.triangle(6, 8, 0),
                        fill: style.stroke
                    },
                    labelCfg: {
                        position: 'middle',
                        style: {
                            fill: style.stroke,
                            fontSize: 11,
                            background: {
                                fill: '#fff',
                                padding: [2, 4],
                                radius: 4
                            }
                        }
                    }
                },
                data: {
                    relation_type: relationType,
                    isPending: isSourceTemp || isTargetTemp // 标记待持久化
                }
            });
            
            // 如果涉及临时节点，先缓存边，等节点保存后再创建
            if (isSourceTemp || isTargetTemp) {
                // 记录待创建的边
                if (!pendingEdges.has(sourceId)) pendingEdges.set(sourceId, []);
                pendingEdges.get(sourceId).push({
                    targetId,
                    relationType,
                    edgeItem
                });
                showToast('连接已创建（将在保存节点后持久化）', 'success');
                return;
            }
            
            // 双方都是持久化节点，立即保存到后端
            try {
                await api.star.createEdge(currentGraphId, {
                    source: sourceId,
                    target: targetId,
                    relation_type: relationType,
                    weight: 1.0
                });
                showToast('连接已保存', 'success');
            } catch (apiError) {
                // 后端保存失败，回滚前端显示
                graph.removeItem(edgeItem);
                console.error('保存连接失败:', apiError);
                showToast('保存连接失败: ' + apiError.message, 'error');
                return;
            }
            
            // 如果当前有选中的节点，刷新详情面板显示连接信息
            if (selectedNode) {
                const nodeId = selectedNode.getModel().id;
                const nodeData = selectedNode.getModel().data;
                showNodeDetail(nodeData);
            }
            
        } catch (error) {
            console.error('创建连接失败:', error);
            showToast('连接失败: ' + error.message, 'error');
        }
    }

    /**
     * 保存节点
     */
    async function saveNode(nodeId, nodeData) {
        const isSaveToGraph = document.getElementById('chk-save-to-graph')?.checked ?? true;

        // 读取编辑后的值
        const editedTitle = document.getElementById('edit-node-title')?.value?.trim() || nodeData.title;
        const editedDesc = document.getElementById('edit-node-desc')?.value?.trim() || nodeData.description;
        const editedType = document.getElementById('edit-node-type')?.value || nodeData.node_type;
        const editedCategory = document.getElementById('edit-node-category')?.value?.trim() || nodeData.category;

        if (isSaveToGraph) {
            try {
                // 节点已在数据库中（持久化节点），只需关闭面板
                if (!tempNodes.has(nodeId)) {
                    closeDetailPanel();
                    showToast('节点已保存', 'success');
                    return;
                }

                // 临时节点需要保存到数据库
                const nodeToSave = tempNodes.get(nodeId);
                if (!nodeToSave) {
                    showToast('节点数据丢失', 'error');
                    return;
                }

                // 使用编辑后的值
                nodeToSave.title = editedTitle;
                nodeToSave.description = editedDesc;
                nodeToSave.node_type = editedType;
                nodeToSave.category = editedCategory;

                // 根据类型更新视觉属性
                const typeConfig = nodeTypeConfig[editedType];
                if (typeConfig) {
                    nodeToSave.color = typeConfig.color;
                    nodeToSave.shape = typeConfig.shape;
                    nodeToSave.size = typeConfig.size;
                }

                const savedNode = await api.star.createNode(currentGraphId, {
                    node_type: nodeToSave.node_type,
                    title: nodeToSave.title,
                    description: nodeToSave.description,
                    category: nodeToSave.category,
                    level: nodeToSave.level,
                    parent_id: nodeToSave.parent_id,
                    size: nodeToSave.size,
                    color: nodeToSave.color,
                    shape: nodeToSave.shape,
                    score: nodeToSave.score,
                    rank: nodeToSave.rank,
                    metadata: nodeToSave.metadata,
                    position_x: nodeToSave.x,
                    position_y: nodeToSave.y
                });

                // 从临时节点移除
                tempNodes.delete(nodeId);
                
                // 更新前端节点ID
                const graphNode = graph.findById(nodeId);
                if (graphNode) {
                    const model = graphNode.getModel();
                    model.id = savedNode.id;
                    model.data.id = savedNode.id;
                    // 更新视觉属性
                    model.data.node_type = editedType;
                    model.data.color = nodeToSave.color;
                    model.style = {
                        ...model.style,
                        fill: nodeToSave.color
                    };
                    graph.updateItem(graphNode, model);
                }
                
                // 处理待创建的边（涉及此节点的连接）
                await savePendingEdges(nodeId, savedNode.id);
                
                // 更新视觉状态
                updateNodeVisualState(savedNode.id, 'persisted');
                updateTempNodesWarning();
                
                closeDetailPanel();
                showToast('节点已保存到星图', 'success');
                
            } catch (error) {
                console.error('保存节点失败:', error);
                showToast('保存失败: ' + error.message, 'error');
            }
        } else {
            // 用户取消勾选，保持为临时节点
            if (!tempNodes.has(nodeId)) {
                // 从持久化变为临时
                const graphNode = graph.findById(nodeId);
                if (graphNode) {
                    const nodeData = graphNode.getModel().data;
                    tempNodes.set(nodeId, nodeData);
                }
            }
            updateNodeVisualState(nodeId, 'temp');
            updateTempNodesWarning();
            closeDetailPanel();
        }
    }
    
    /**
     * 保存待处理的边
     */
    async function savePendingEdges(tempNodeId, persistedNodeId) {
        const edgesToCreate = pendingEdges.get(tempNodeId) || [];
        const createdEdges = [];
        
        for (const edgeInfo of edgesToCreate) {
            try {
                // 确定源节点和目标节点的持久化ID
                let sourceId = tempNodeId === edgeInfo.sourceId ? persistedNodeId : edgeInfo.sourceId;
                let targetId = tempNodeId === edgeInfo.targetId ? persistedNodeId : edgeInfo.targetId;
                
                // 如果另一端也是临时节点，跳过（等那个节点保存时再处理）
                if (tempNodes.has(edgeInfo.targetId) || tempNodes.has(edgeInfo.sourceId)) {
                    continue;
                }
                
                await api.star.createEdge(currentGraphId, {
                    source: sourceId,
                    target: targetId,
                    relation_type: edgeInfo.relationType,
                    weight: 1.0
                });
                
                createdEdges.push(edgeInfo);
            } catch (error) {
                console.error('保存连接失败:', error);
            }
        }
        
        // 从待处理列表中移除已创建的边
        if (createdEdges.length > 0) {
            pendingEdges.set(tempNodeId, edgesToCreate.filter(e => !createdEdges.includes(e)));
            if (pendingEdges.get(tempNodeId).length === 0) {
                pendingEdges.delete(tempNodeId);
            }
        }
    }

    /**
     * 删除节点
     */
    async function deleteNode(nodeId) {
        if (!confirm('确定要删除这个节点吗？子节点也会被删除。')) {
            return;
        }

        try {
            // 如果是临时节点，直接从前端移除
            if (tempNodes.has(nodeId)) {
                tempNodes.delete(nodeId);
                graph.removeItem(nodeId);
                updateTempNodesWarning();
                closeDetailPanel();
                showToast('节点已删除', 'success');
                return;
            }
            
            // 持久化节点需要调用API删除
            await api.star.deleteNode(nodeId);
            
            // 从图中移除
            graph.removeItem(nodeId);
            
            closeDetailPanel();
            showToast('节点已删除', 'success');
            
        } catch (error) {
            console.error('删除节点失败:', error);
            showToast('删除失败: ' + error.message, 'error');
        }
    }

    /**
     * 更新节点视觉状态
     */
    function updateNodeVisualState(nodeId, state) {
        const node = graph.findById(nodeId);
        if (!node) return;
        
        if (state === 'temp') {
            // 临时节点：虚线边框+半透明
            node.update({
                style: {
                    stroke: '#999',
                    lineDash: [5, 5],
                    opacity: 0.7
                },
                labelCfg: {
                    style: {
                        fill: '#666'
                    }
                }
            });
        } else {
            // 持久化节点：实线边框+不透明
            node.update({
                style: {
                    stroke: '#fff',
                    lineDash: null,
                    opacity: 1
                },
                labelCfg: {
                    style: {
                        fill: '#1A1A2E'
                    }
                }
            });
        }
    }

    // ========== 节点扩展（AI生成子节点） ==========
    
    /**
     * 显示扩展节点对话框
     */
    function showExpandNodeDialog(nodeId, nodeData) {
        const { title, node_type } = nodeData;
        
        // 创建弹窗
        const modal = document.createElement('div');
        modal.id = 'expand-node-modal';
        modal.style.cssText = `
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background: rgba(0,0,0,0.5);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 2000;
        `;
        
        const content = document.createElement('div');
        content.style.cssText = `
            background: white;
            border-radius: 12px;
            padding: 24px;
            width: 420px;
            max-width: 90%;
            max-height: 80vh;
            overflow-y: auto;
        `;
        
        content.innerHTML = `
            <h3 style="margin: 0 0 8px 0; font-size: 18px;">扩展节点</h3>
            <p style="margin: 0 0 16px 0; font-size: 13px; color: #666;">
                基于「${title}」生成相关的子节点
            </p>
            
            <div style="margin-bottom: 16px;">
                <label style="font-size: 12px; color: #999; margin-bottom: 4px; display: block;">
                    提示词（可选，留空使用默认）
                </label>
                <textarea id="expand-prompt" rows="3" 
                    style="width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 6px; font-size: 13px; resize: vertical;"
                    placeholder="例如：基于这个目标，帮我拆解成3个可执行的任务..."
                ></textarea>
            </div>
            
            <div style="background: #f8f9fa; border-radius: 8px; padding: 12px; margin-bottom: 16px;">
                <div style="font-size: 12px; color: #666; margin-bottom: 8px;">快捷提示词：</div>
                <div style="display: flex; flex-wrap: wrap; gap: 8px;">
                    ${getQuickPrompts(node_type, title).map((prompt, idx) => `
                        <button class="quick-prompt-btn" data-idx="${idx}" 
                            style="padding: 6px 12px; border: 1px solid #e0e0e0; border-radius: 4px; background: white; cursor: pointer; font-size: 12px;"
                        >${prompt.label}</button>
                    `).join('')}
                </div>
            </div>
            
            <div style="display: flex; gap: 8px;">
                <button id="cancel-expand" style="flex: 1; padding: 10px; border: none; background: #f5f5f5; border-radius: 6px; cursor: pointer;">
                    取消
                </button>
                <button id="confirm-expand" style="flex: 1; padding: 10px; border: none; background: #4A90D9; color: white; border-radius: 6px; cursor: pointer;">
                    生成子节点
                </button>
            </div>
        `;
        
        modal.appendChild(content);
        document.body.appendChild(modal);
        
        const quickPrompts = getQuickPrompts(node_type, title);
        
        // 绑定快捷提示词按钮
        content.querySelectorAll('.quick-prompt-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const idx = parseInt(btn.dataset.idx);
                document.getElementById('expand-prompt').value = quickPrompts[idx].text;
            });
        });
        
        // 取消按钮
        document.getElementById('cancel-expand').addEventListener('click', () => {
            modal.remove();
        });
        
        // 确认按钮
        document.getElementById('confirm-expand').addEventListener('click', async () => {
            const customPrompt = document.getElementById('expand-prompt').value.trim();
            modal.remove();
            await expandNodeWithAI(nodeId, nodeData, customPrompt);
        });
        
        // 点击背景关闭
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.remove();
            }
        });
    }
    
    /**
     * 获取快捷提示词
     */
    function getQuickPrompts(nodeType, title) {
        const prompts = {
            strength: [
                { label: '应用场景', text: `基于「${title}」这个性格优势，帮我生成3个具体的日常应用场景。` },
                { label: '发展建议', text: `针对「${title}」这个优势，给出3条具体的发展建议。` }
            ],
            goal: [
                { label: '拆解任务', text: `将「${title}」这个目标拆解成3-5个可执行的子任务。` },
                { label: '里程碑', text: `为「${title}」设定3个关键里程碑。` }
            ],
            insight: [
                { label: '深入分析', text: `对「${title}」这个洞察进行深入分析，生成3个相关观点。` },
                { label: '行动建议', text: `基于「${title}」这个洞察，给出3个行动建议。` }
            ],
            task: [
                { label: '细化步骤', text: `将「${title}」这个任务细化为3-5个具体步骤。` },
                { label: '所需资源', text: `完成「${title}」需要哪些资源或支持？` }
            ]
        };
        
        return prompts[nodeType] || prompts.goal;
    }
    
    /**
     * 使用AI扩展节点
     */
    async function expandNodeWithAI(nodeId, nodeData, customPrompt) {
        const { title, node_type } = nodeData;
        
        showLoading(true);
        showToast('正在生成子节点建议...', 'info');
        
        try {
            // 构建默认提示词
            const defaultPrompt = `基于「${title}」这个${nodeTypeConfig[node_type]?.label || '节点'}，生成3个相关的子节点建议。

请以JSON数组格式返回，每个节点包含：
- title: 节点标题（简洁，不超过10个字）
- description: 节点描述（一句话说明）
- type: 节点类型（strength/insight/goal/task）

示例格式：
[
  {"title": "子节点1", "description": "描述1", "type": "task"},
  {"title": "子节点2", "description": "描述2", "type": "task"}
]`;

            const prompt = customPrompt || defaultPrompt;
            
            // 调用对话API
            const response = await api.chat.sendMessage({
                message: prompt,
                context: {
                    action: 'expand_node',
                    node_title: title,
                    node_type: node_type
                }
            });
            
            // 解析AI返回的JSON
            const suggestions = parseAISuggestions(response.content);
            
            if (suggestions.length === 0) {
                showToast('未能解析AI建议，请重试', 'error');
                return;
            }
            
            // 显示建议列表供用户确认
            showSuggestionsConfirmDialog(nodeId, nodeData, suggestions);
            
        } catch (error) {
            console.error('扩展节点失败:', error);
            showToast('生成失败: ' + error.message, 'error');
        } finally {
            showLoading(false);
        }
    }
    
    /**
     * 解析AI建议
     */
    function parseAISuggestions(content) {
        try {
            // 尝试提取JSON数组
            const jsonMatch = content.match(/\[[\s\S]*\]/);
            if (jsonMatch) {
                const parsed = JSON.parse(jsonMatch[0]);
                if (Array.isArray(parsed) && parsed.length > 0) {
                    return parsed.filter(item => item.title).map(item => ({
                        title: item.title,
                        description: item.description || '',
                        type: ['strength', 'insight', 'goal', 'task'].includes(item.type) ? item.type : 'insight'
                    }));
                }
            }
        } catch (e) {
            console.error('解析AI建议失败:', e);
        }
        
        // 如果JSON解析失败，尝试按行解析
        const lines = content.split('\n').filter(l => l.trim());
        const suggestions = [];
        
        for (const line of lines) {
            // 匹配 "1. 标题 - 描述" 或 "- 标题: 描述" 格式
            const match = line.match(/^(?:\d+[.\-]\s*|[\-\*]\s*)([^:\-]+)[:\-\s]*(.*)$/);
            if (match) {
                suggestions.push({
                    title: match[1].trim().substring(0, 20),
                    description: match[2].trim(),
                    type: 'insight'
                });
            }
        }
        
        return suggestions.slice(0, 5); // 最多返回5个
    }
    
    /**
     * 显示建议确认对话框
     */
    function showSuggestionsConfirmDialog(parentNodeId, parentNodeData, suggestions) {
        const modal = document.createElement('div');
        modal.id = 'confirm-suggestions-modal';
        modal.style.cssText = `
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background: rgba(0,0,0,0.5);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 2000;
        `;
        
        const content = document.createElement('div');
        content.style.cssText = `
            background: white;
            border-radius: 12px;
            padding: 24px;
            width: 480px;
            max-width: 90%;
            max-height: 80vh;
            overflow-y: auto;
        `;
        
        content.innerHTML = `
            <h3 style="margin: 0 0 16px 0; font-size: 18px;">确认生成的子节点</h3>
            <p style="margin: 0 0 16px 0; font-size: 13px; color: #666;">
                勾选要添加的节点：
            </p>
            
            <div style="display: flex; flex-direction: column; gap: 8px; margin-bottom: 16px;">
                ${suggestions.map((s, idx) => `
                    <label style="display: flex; align-items: start; gap: 8px; padding: 12px; border: 1px solid #e0e0e0; border-radius: 8px; cursor: pointer;"
                        onmouseenter="this.style.background='#f8f9fa'" onmouseleave="this.style.background='white'"
                    >
                        <input type="checkbox" class="suggestion-checkbox" data-idx="${idx}" checked 
                            style="margin-top: 2px;"
                        >
                        <div style="flex: 1;">
                            <div style="font-weight: 600; font-size: 14px; margin-bottom: 2px;">${s.title}</div>
                            <div style="font-size: 12px; color: #666;">${s.description || '暂无描述'}</div>
                            <div style="font-size: 11px; color: #4A90D9; margin-top: 4px;">
                                ${nodeTypeOptions.find(opt => opt.value === s.type)?.label || '💡 AI洞察'}
                            </div>
                        </div>
                    </label>
                `).join('')}
            </div>
            
            <div style="display: flex; gap: 8px;">
                <button id="cancel-suggestions" style="flex: 1; padding: 10px; border: none; background: #f5f5f5; border-radius: 6px; cursor: pointer;">
                    取消
                </button>
                <button id="confirm-suggestions" style="flex: 1; padding: 10px; border: none; background: #4A90D9; color: white; border-radius: 6px; cursor: pointer;">
                    添加选中节点
                </button>
            </div>
        `;
        
        modal.appendChild(content);
        document.body.appendChild(modal);
        
        // 取消按钮
        document.getElementById('cancel-suggestions').addEventListener('click', () => {
            modal.remove();
        });
        
        // 确认按钮
        document.getElementById('confirm-suggestions').addEventListener('click', async () => {
            const checkedBoxes = content.querySelectorAll('.suggestion-checkbox:checked');
            const selectedIndices = Array.from(checkedBoxes).map(cb => parseInt(cb.dataset.idx));
            const selectedSuggestions = selectedIndices.map(idx => suggestions[idx]);
            
            modal.remove();
            
            if (selectedSuggestions.length > 0) {
                await createChildNodes(parentNodeId, parentNodeData, selectedSuggestions);
            }
        });
        
        // 点击背景关闭
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.remove();
            }
        });
    }
    
    /**
     * 创建子节点
     */
    async function createChildNodes(parentNodeId, parentNodeData, suggestions) {
        showLoading(true);
        showToast(`正在创建 ${suggestions.length} 个子节点...`, 'info');
        
        try {
            const canvasWidth = elements.canvas.offsetWidth;
            const canvasHeight = elements.canvas.offsetHeight;
            const centerX = canvasWidth / 2;
            const centerY = canvasHeight / 2;
            
            // 计算子节点位置（围绕父节点呈扇形分布）
            const angleStep = (2 * Math.PI) / (suggestions.length + 1);
            const radius = 120;
            
            for (let i = 0; i < suggestions.length; i++) {
                const suggestion = suggestions[i];
                const angle = -Math.PI / 2 + angleStep * (i + 1);
                
                const x = centerX + radius * Math.cos(angle);
                const y = centerY + radius * Math.sin(angle);
                
                // 创建子节点数据
                const typeConfig = nodeTypeConfig[suggestion.type] || nodeTypeConfig.insight;
                const nodeId = 'temp_' + Date.now() + '_' + i;
                
                const newNode = {
                    id: nodeId,
                    node_type: suggestion.type,
                    title: suggestion.title,
                    description: suggestion.description,
                    level: (parentNodeData.level || 1) + 1,
                    parent_id: parentNodeId,
                    size: typeConfig.size,
                    color: typeConfig.color,
                    shape: typeConfig.shape,
                    x: x,
                    y: y,
                    is_expanded: false
                };
                
                // 添加到临时节点存储
                tempNodes.set(nodeId, newNode);
                
                // 添加到图中
                graph.addItem('node', {
                    id: nodeId,
                    type: typeConfig.shape,
                    label: newNode.title,
                    x: x,
                    y: y,
                    size: typeConfig.size,
                    style: {
                        fill: typeConfig.color,
                        stroke: '#999',
                        lineDash: [5, 5],
                        opacity: 0.7
                    },
                    labelCfg: {
                        position: 'bottom',
                        style: {
                            fill: '#666',
                            fontSize: 12
                        }
                    },
                    data: newNode
                });
                
                // 创建与父节点的连接（belongs_to 关系）
                const edgeStyle = edgeStyleMap.belongs_to;
                graph.addItem('edge', {
                    source: parentNodeId,
                    target: nodeId,
                    label: edgeStyle.label,
                    style: {
                        stroke: edgeStyle.stroke,
                        lineWidth: 2,
                        opacity: 0.8,
                        lineDash: edgeStyle.lineDash,
                        endArrow: {
                            path: G6.Arrow.triangle(6, 8, 0),
                            fill: edgeStyle.stroke
                        }
                    },
                    data: {
                        relation_type: 'belongs_to',
                        isPending: true
                    }
                });
                
                // 记录待创建的边
                if (!pendingEdges.has(nodeId)) pendingEdges.set(nodeId, []);
                pendingEdges.get(nodeId).push({
                    targetId: parentNodeId,
                    relationType: 'belongs_to'
                });
            }
            
            // 更新父节点展开状态
            await api.star.expandNodeState(parentNodeId);
            
            // 更新临时节点警告
            updateTempNodesWarning();
            
            showToast(`已创建 ${suggestions.length} 个子节点（临时状态）`, 'success');
            
        } catch (error) {
            console.error('创建子节点失败:', error);
            showToast('创建失败: ' + error.message, 'error');
        } finally {
            showLoading(false);
        }
    }

    // ========== 临时节点管理 ==========
    
    /**
     * 更新临时节点警告
     */
    function updateTempNodesWarning() {
        // 检查是否已存在警告元素
        let warningEl = document.getElementById('temp-nodes-warning');
        
        if (tempNodes.size > 0) {
            if (!warningEl) {
                warningEl = document.createElement('div');
                warningEl.id = 'temp-nodes-warning';
                warningEl.style.cssText = `
                    position: fixed;
                    bottom: 20px;
                    left: 50%;
                    transform: translateX(-50%);
                    background: #fff3cd;
                    border: 1px solid #ffc107;
                    border-radius: 8px;
                    padding: 12px 20px;
                    display: flex;
                    align-items: center;
                    gap: 12px;
                    z-index: 1000;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                `;
                document.body.appendChild(warningEl);
            }
            
            warningEl.innerHTML = `
                <span style="font-size: 18px;">⚠️</span>
                <span style="font-size: 14px; color: #856404;">
                    有 <strong>${tempNodes.size}</strong> 个未保存的节点
                </span>
                <button id="btn-save-all-temp" style="
                    background: #ffc107;
                    color: #856404;
                    border: none;
                    padding: 6px 12px;
                    border-radius: 4px;
                    cursor: pointer;
                    font-size: 13px;
                ">全部保存</button>
            `;
            
            // 绑定保存全部按钮
            document.getElementById('btn-save-all-temp')?.addEventListener('click', saveAllTempNodes);
            
        } else if (warningEl) {
            warningEl.remove();
        }
    }

    /**
     * 保存所有临时节点
     */
    async function saveAllTempNodes() {
        if (tempNodes.size === 0) return;
        
        let saved = 0;
        let failed = 0;
        
        for (const [nodeId, nodeData] of tempNodes) {
            try {
                await api.star.createNode(currentGraphId, {
                    node_type: nodeData.node_type,
                    title: nodeData.title,
                    description: nodeData.description,
                    category: nodeData.category,
                    level: nodeData.level,
                    parent_id: nodeData.parent_id,
                    size: nodeData.size,
                    color: nodeData.color,
                    shape: nodeData.shape,
                    score: nodeData.score,
                    rank: nodeData.rank,
                    metadata: nodeData.metadata,
                    position_x: nodeData.x,
                    position_y: nodeData.y
                });
                
                tempNodes.delete(nodeId);
                updateNodeVisualState(nodeId, 'persisted');
                saved++;
                
            } catch (error) {
                console.error(`保存节点 ${nodeId} 失败:`, error);
                failed++;
            }
        }
        
        updateTempNodesWarning();
        
        if (failed === 0) {
            showToast(`成功保存 ${saved} 个节点`, 'success');
        } else {
            showToast(`保存完成: ${saved} 成功, ${failed} 失败`, 'warning');
        }
        
        // 重新加载星图以同步数据
        await loadStarGraph();
    }

    // ========== 辅助功能 ==========
    
    /**
     * 展开美德节点
     */
    async function expandVirtueNodes(virtueNodeId, virtueTitle) {
        if (!graph) return;

        try {
            // 调用API展开节点
            const result = await api.star.expandNodeState(virtueNodeId);
            
            // 高亮显示
            const virtueNode = graph.findById(virtueNodeId);
            if (!virtueNode) return;

            graph.getNodes().forEach(node => {
                graph.setItemState(node, 'highlight', false);
                graph.setItemState(node, 'dim', true);
            });

            graph.setItemState(virtueNode, 'dim', false);
            graph.setItemState(virtueNode, 'highlight', true);

            // 获取子节点并高亮
            const edges = graph.getEdges();
            const childNodes = [];

            edges.forEach(edge => {
                const source = edge.getSource();
                const target = edge.getTarget();
                if (source.getID() === virtueNodeId) {
                    childNodes.push(target);
                    graph.setItemState(target, 'dim', false);
                    graph.setItemState(target, 'highlight', true);
                }
            });

            graph.focusItem(virtueNode, true, {
                duration: 500,
                easing: 'easeCubic'
            });

            showToast(`已展开${virtueTitle}领域的${childNodes.length}项优势`, 'success');

            setTimeout(() => {
                graph.getNodes().forEach(node => {
                    graph.setItemState(node, 'highlight', false);
                    graph.setItemState(node, 'dim', false);
                });
            }, 3000);
            
        } catch (error) {
            console.error('展开节点失败:', error);
            showToast('展开失败: ' + error.message, 'error');
        }
    }

    /**
     * 发送探索建议到AI对话
     */
    function sendExplorePrompt(prompt) {
        localStorage.setItem('pending_explore_prompt', prompt);
        localStorage.setItem('pending_explore_timestamp', Date.now());
        window.location.href = '/chat/index.html?source=star_explore';
    }

    // ========== UI控制 ==========
    
    function showLoading(show) {
        isLoading = show;
        if (elements.loading) {
            elements.loading.style.display = show ? 'block' : 'none';
        }
    }

    function showEmptyState() {
        if (elements.emptyState) elements.emptyState.style.display = 'block';
        if (elements.infoBar) elements.infoBar.style.display = 'none';
        if (elements.controls) elements.controls.style.display = 'none';
        if (elements.legend) elements.legend.style.display = 'none';
    }

    function showGraphUI() {
        if (elements.emptyState) elements.emptyState.style.display = 'none';
        if (elements.infoBar) elements.infoBar.style.display = 'block';
        if (elements.controls) elements.controls.style.display = 'flex';
        if (elements.legend) elements.legend.style.display = 'block';
    }

    function showError(message) {
        if (elements.detailContent) {
            elements.detailContent.innerHTML = `
                <div class="star-empty-state">
                    <div class="star-empty-state__icon">⚠️</div>
                    <h2 class="star-empty-state__title">出错了</h2>
                    <p class="star-empty-state__desc">${message}</p>
                    <button class="btn btn--primary" onclick="location.reload()">重试</button>
                </div>
            `;
        }
        if (elements.detailPanel) {
            elements.detailPanel.classList.remove('star-detail-panel--collapsed');
        }
    }

    /**
     * 显示Toast提示
     */
    function showToast(message, type = 'info') {
        // 检查是否已有toast
        let toast = document.getElementById('star-toast');
        if (toast) {
            toast.remove();
        }

        toast = document.createElement('div');
        toast.id = 'star-toast';
        
        const colors = {
            success: '#27ae60',
            error: '#e74c3c',
            warning: '#f39c12',
            info: '#3498db'
        };

        toast.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: ${colors[type] || colors.info};
            color: white;
            padding: 12px 20px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.2);
            z-index: 10000;
            font-size: 14px;
            animation: slideIn 0.3s ease;
        `;
        toast.textContent = message;

        // 添加动画样式
        if (!document.getElementById('toast-style')) {
            const style = document.createElement('style');
            style.id = 'toast-style';
            style.textContent = `
                @keyframes slideIn {
                    from { transform: translateX(100%); opacity: 0; }
                    to { transform: translateX(0); opacity: 1; }
                }
            `;
            document.head.appendChild(style);
        }

        document.body.appendChild(toast);

        setTimeout(() => {
            toast.style.animation = 'slideIn 0.3s ease reverse';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }

    // ========== 全局暴露 ==========
    
    window.sendExplorePrompt = sendExplorePrompt;
    window.starMap3 = {
        refresh: loadStarGraph,
        getCurrentGraphId: () => currentGraphId,
        getTempNodes: () => tempNodes
    };

    // 启动
    document.addEventListener('DOMContentLoaded', init);

})();
