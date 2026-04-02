# 星图模块开发实施文档

## 开发日期
2026-03-15

## 概述
根据《深潜模块V2-design.md》设计文档，完成了星图模块的开发实施，采用最小改动原则，仅需1个后端接口+前端可视化实现。

## 已完成内容

### 1. 后端实现

#### 1.1 新增文件
- `backend/routers/star.py` - 星图路由模块

#### 1.2 接口清单
| 接口 | 方法 | 描述 |
|------|------|------|
| `/api/v1/star/graph` | GET | 获取用户星图数据（节点和边） |
| `/api/v1/star/node/{node_id}` | GET | 获取节点详情 |
| `/api/v1/star/node/{node_id}/expand` | POST | 展开子节点（懒加载） |

#### 1.3 数据映射方案
- **L1 Root节点**: 用户中心节点（深海蓝 #1E3A5F）
- **L2 类别节点**: VIA 6大美德（6种颜色区分）
  - 智慧 - 天际蓝 #4A90D9
  - 勇气 - 翠绿 #50C878
  - 仁爱 - 粉红 #FF6B9D
  - 正义 - 橙色 #F39C12
  - 节制 - 紫色 #9B59B6
  - 超越 - 青色 #1ABC9C
- **L3 详情节点**: VIA 24项优势（得分映射为节点大小）
- **关系边**: belongs_to（归属关系）

#### 1.4 已修改文件
- `backend/main.py` - 注册star_router
- `backend/routers/__init__.py` - 导出star_router

### 2. 前端实现

#### 2.1 新增文件
- `frontend/star/index.html` - 星图页面
- `frontend/star/star.js` - 星图逻辑

#### 2.2 功能特性
- **力导向图**: 使用 AntV G6 4.8.0 实现
- **交互功能**:
  - 点击节点显示详情面板
  - 双击节点聚焦
  - 缩放/平移/重置视图
  - 节点悬停高亮
- **视觉元素**:
  - 6色美德图例
  - 节点大小映射得分
  - 不同形状区分节点类型
- **空状态处理**: 未测评用户引导至测评页面

#### 2.3 已修改文件（导航更新）
- `frontend/index.html` - 首页导航添加"我的星图"
- `frontend/assessment/index.html` - 测评页导航添加"我的星图"
- `frontend/chat/index.html` - 对话页侧边栏添加"我的星图"

### 3. 与已有界面交互

| 入口页面 | 交互方式 | 说明 |
|---------|---------|------|
| 首页 | 顶部导航 | 点击"我的星图"跳转 |
| 测评中心 | 顶部导航 | 完成测评后可查看星图 |
| AI对话 | 侧边栏 | 随时访问星图 |
| 星图页 | 详情面板 | 点击节点可跳转相关功能 |

## 技术栈

### 后端
- FastAPI + SQLAlchemy async
- SQLite 数据库
- Pydantic 数据验证

### 前端
- AntV G6 4.8.0（图可视化）
- 原生 HTML/JS/CSS
- 响应式设计

## 数据结构

### 节点类型 (StarNode)
```typescript
{
  id: string;           // 唯一标识
  node_type: 'root' | 'category' | 'strength' | 'insight';
  title: string;        // 显示名称
  description?: string; // 描述
  level: 1-4;          // 层级
  size: number;        // 节点大小
  color: string;       // 颜色
  shape: string;       // 形状
  score?: number;      // 得分
  rank?: number;       // 排名
  metadata: object;    // 扩展数据
}
```

### 边类型 (StarEdge)
```typescript
{
  id: string;
  source: string;      // 源节点ID
  target: string;      // 目标节点ID
  relation_type: 'belongs_to' | 'leads_to' | 'suggests' | 'relates_to';
  weight: number;      // 关系强度 0-1
  label?: string;      // 边标签
}
```

## 部署说明

1. 后端代码已就绪，重启服务即可加载新路由
2. 前端文件已创建，无需构建步骤
3. 访问路径: `/star/index.html`

## 后续优化建议

### 已知问题修复
- [x] **403 Forbidden 错误**: 已修复前端响应处理逻辑，添加401/403错误处理

### 功能优化
1. **性能优化**: 节点数量超过100时启用聚合
2. **更多交互**: 右键菜单、框选多节点
3. **AI洞察**: 基于星图生成个性化建议
4. **分享功能**: 星图截图/导出
5. **历史对比**: 展示星图变化趋势

## 问题诊断

如遇到403错误，请参考 `STAR_403_DEBUG.md` 进行排查。

## 测试检查清单

- [ ] GET /api/v1/star/graph 返回正确结构
- [ ] 有测评数据的用户显示完整星图
- [ ] 无测评数据的用户显示空状态引导
- [ ] 节点点击显示详情面板
- [ ] 图例颜色与节点一致
- [ ] 响应式布局正常
- [ ] 各页面导航可正常跳转
