# 深觅 AI Coach - UI 设计规范文档

## 概述

本文档定义了"深觅 AI Coach"系统的完整视觉设计规范，包括色彩系统、字体规范、组件库和页面设计指南。

### 设计理念

- **温暖**：使用暖色调和低饱和度色彩，营造舒适、安全的用户体验
- **专业**：清晰的视觉层次和一致的组件设计，传达专业性和可信度
- **成长**：通过渐变和动态元素，象征用户的成长旅程
- **可信赖**：简洁的设计语言和友好的交互，建立用户信任

### 目标用户

- **Z世代**（1995-2009年出生）：数字原住民，追求个性化和自我表达
- **α世代**（2010年后出生）：与AI共同成长，注重体验和情感连接

---

## 1. 色彩系统

### 1.1 主色调

#### Primary - 深海蓝
代表信任、深度、专业

| Token | Hex | 用途 |
|-------|-----|------|
| `--primary-50` | #f0f7ff | 极浅背景 |
| `--primary-100` | #e0effe | 浅色背景 |
| `--primary-200` | #bae0fd | 悬停状态 |
| `--primary-300` | #7ccbfd | 边框强调 |
| `--primary-400` | #36b3fa | 次要元素 |
| `--primary-500` | #0c9aed | 默认主色 |
| `--primary-600` | #027fcf | **主要按钮** |
| `--primary-700` | #0467a8 | 悬停状态 |
| `--primary-800` | #0a558b | 深色文字 |
| `--primary-900` | #0f4873 | 标题文字 |
| `--primary-950` | #0a2d4d | 最深色 |

#### Secondary - 墨绿色
代表成长、平衡、自然

| Token | Hex | 用途 |
|-------|-----|------|
| `--secondary-500` | #22c55e | 成功强调 |
| `--secondary-600` | #16a34a | **次要按钮** |
| `--secondary-700` | #15803d | 悬停状态 |

#### Accent - 珊瑚橙
代表温暖、活力、行动召唤

| Token | Hex | 用途 |
|-------|-----|------|
| `--accent-500` | #f97316 | **CTA按钮** |
| `--accent-600` | #ea580c | 悬停状态 |

### 1.2 中性色

#### 灰度色板

| Token | Hex | 用途 |
|-------|-----|------|
| `--gray-50` | #f8fafc | 页面背景 |
| `--gray-100` | #f1f5f9 | 卡片背景 |
| `--gray-200` | #e2e8f0 | 边框浅色 |
| `--gray-300` | #cbd5e1 | 边框默认 |
| `--gray-400` | #94a3b8 | 禁用文字 |
| `--gray-500` | #64748b | 次要文字 |
| `--gray-600` | #475569 | 正文文字 |
| `--gray-700` | #334155 | 标题文字 |
| `--gray-800` | #1e293b | 深色标题 |
| `--gray-900` | #0f172a | 主要文字 |

#### 暖灰色（推荐用于背景）

| Token | Hex | 用途 |
|-------|-----|------|
| `--warm-gray-50` | #fafaf9 | **页面主背景** |
| `--warm-gray-100` | #f5f5f4 | 次级背景 |
| `--warm-gray-200` | #e7e5e4 | 边框 |

### 1.3 功能色

| 类型 | 颜色 | 背景色 | 用途 |
|------|------|--------|------|
| Success | #22c55e | #f0fdf4 | 成功状态、完成提示 |
| Warning | #f59e0b | #fffbeb | 警告状态、注意事项 |
| Error | #ef4444 | #fef2f2 | 错误状态、验证失败 |
| Info | #3b82f6 | #eff6ff | 信息提示、说明文字 |

### 1.4 主题变量

```css
/* 主要颜色 */
--color-primary: var(--primary-600);      /* 主按钮、链接 */
--color-primary-hover: var(--primary-700); /* 悬停状态 */
--color-primary-light: var(--primary-100); /* 浅色背景 */

/* 背景色 */
--bg-primary: var(--warm-gray-50);   /* 页面背景 */
--bg-secondary: var(--white);         /* 卡片背景 */
--bg-tertiary: var(--warm-gray-100);  /* 次级背景 */

/* 文字色 */
--text-primary: var(--gray-900);     /* 主要文字 */
--text-secondary: var(--gray-600);   /* 次要文字 */
--text-muted: var(--gray-500);       /* 辅助文字 */
--text-inverse: var(--white);        /* 反色文字 */

/* 边框色 */
--border-light: var(--gray-200);     /* 浅色边框 */
--border-medium: var(--gray-300);    /* 默认边框 */
```

---

## 2. 字体系统

### 2.1 字体家族

```css
--font-family-primary: 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif;
--font-family-secondary: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
--font-family-mono: 'SF Mono', 'Monaco', 'Fira Code', monospace;
```

### 2.2 字体大小

使用 1.125 比例尺（Major Second）

| Token | 大小 | 用途 |
|-------|------|------|
| `--font-size-2xs` | 10px | 极小标签 |
| `--font-size-xs` | 12px | 辅助文字、标签 |
| `--font-size-sm` | 14px | 正文小字 |
| `--font-size-base` | 16px | **默认正文** |
| `--font-size-lg` | 18px | 大正文 |
| `--font-size-xl` | 20px | 小标题 |
| `--font-size-2xl` | 24px | 区块标题 |
| `--font-size-3xl` | 30px | 页面标题 |
| `--font-size-4xl` | 36px | 大标题 |
| `--font-size-5xl` | 48px | 英雄区标题 |

### 2.3 行高

| Token | 值 | 用途 |
|-------|-----|------|
| `--line-height-tight` | 1.25 | 标题 |
| `--line-height-snug` | 1.375 | 小标题 |
| `--line-height-normal` | 1.5 | **正文** |
| `--line-height-relaxed` | 1.625 | 长文本 |
| `--line-height-loose` | 2 | 宽松排版 |

### 2.4 字重

| Token | 值 | 用途 |
|-------|-----|------|
| `--font-weight-normal` | 400 | 正文 |
| `--font-weight-medium` | 500 | 强调文字 |
| `--font-weight-semibold` | 600 | 小标题 |
| `--font-weight-bold` | 700 | 标题 |

### 2.5 排版规范

#### 标题样式

| 级别 | 大小 | 字重 | 行高 | 用途 |
|------|------|------|------|------|
| H1 | 36px | Bold | 1.25 | 页面主标题 |
| H2 | 30px | Bold | 1.25 | 区块标题 |
| H3 | 24px | Semibold | 1.375 | 小节标题 |
| H4 | 20px | Semibold | 1.375 | 卡片标题 |
| H5 | 18px | Semibold | 1.375 | 列表标题 |
| H6 | 16px | Semibold | 1.5 | 小标题 |

#### 正文样式

| 级别 | 大小 | 行高 | 用途 |
|------|------|------|------|
| text-xl | 20px | 1.625 | 引导文字 |
| text-lg | 18px | 1.625 | 大正文 |
| text-base | 16px | 1.5 | **默认正文** |
| text-sm | 14px | 1.5 | 辅助文字 |
| text-xs | 12px | 1.5 | 标签、说明 |

---

## 3. 间距系统

### 3.1 基础间距（4px 网格）

| Token | 值 | 用途 |
|-------|-----|------|
| `--space-1` | 4px | 极小间距 |
| `--space-2` | 8px | 紧凑间距 |
| `--space-3` | 12px | 小组件内边距 |
| `--space-4` | 16px | **默认间距** |
| `--space-5` | 20px | 中等间距 |
| `--space-6` | 24px | 大间距 |
| `--space-8` | 32px | 区块间距 |
| `--space-10` | 40px | 大区块间距 |
| `--space-12` | 48px | 页面间距 |

### 3.2 组件间距

| 组件 | 内边距 | 外边距 |
|------|--------|--------|
| 卡片 | 16-24px | 16px |
| 按钮 | 8-16px 水平 | 0 |
| 输入框 | 12-16px | 8px |
| 列表项 | 12-16px | 0 |

---

## 4. 圆角系统

| Token | 值 | 用途 |
|-------|-----|------|
| `--radius-sm` | 4px | 小元素 |
| `--radius-md` | 6px | 输入框 |
| `--radius-lg` | 8px | **默认圆角** |
| `--radius-xl` | 12px | 卡片 |
| `--radius-2xl` | 16px | 大卡片 |
| `--radius-full` | 9999px | 圆形元素 |

---

## 5. 阴影系统

| Token | 阴影 | 用途 |
|-------|------|------|
| `--shadow-xs` | 0 1px 2px rgba(0,0,0,0.05) | 微阴影 |
| `--shadow-sm` | 0 1px 3px rgba(0,0,0,0.1) | **默认阴影** |
| `--shadow-md` | 0 4px 6px rgba(0,0,0,0.1) | 卡片悬停 |
| `--shadow-lg` | 0 10px 15px rgba(0,0,0,0.1) | 弹窗 |
| `--shadow-xl` | 0 20px 25px rgba(0,0,0,0.1) | 模态框 |

---

## 6. 组件库

### 6.1 按钮系统

#### 按钮类型

| 类型 | 类名 | 用途 |
|------|------|------|
| Primary | `.btn--primary` | 主要操作 |
| Secondary | `.btn--secondary` | 次要操作 |
| Outline | `.btn--outline` | 轮廓按钮 |
| Ghost | `.btn--ghost` | 幽灵按钮 |
| Text | `.btn--text` | 文字按钮 |
| Accent | `.btn--accent` | CTA按钮 |

#### 按钮尺寸

| 尺寸 | 类名 | 高度 | 内边距 |
|------|------|------|--------|
| Small | `.btn--sm` | 32px | 8px 12px |
| Medium | `.btn--md` | 40px | 8px 16px |
| Large | `.btn--lg` | 48px | 12px 24px |

#### 按钮状态

- 默认：正常显示
- Hover：背景加深，轻微上移
- Active：按下效果
- Disabled：透明度50%，禁用光标
- Loading：显示加载动画

### 6.2 表单组件

#### 输入框

```html
<input class="form-control form-control--md" type="text" placeholder="请输入">
```

状态：
- 默认：边框 `--border-medium`
- Hover：边框加深
- Focus：主色边框 + 阴影
- Error：红色边框
- Disabled：灰色背景

#### 滑块（评估量表用）

```html
<input class="slider" type="range" min="1" max="5" value="3">
```

### 6.3 卡片组件

#### 基础卡片

```html
<div class="card">
  <div class="card__header">标题</div>
  <div class="card__body">内容</div>
  <div class="card__footer">操作</div>
</div>
```

#### 聊天消息卡片

```html
<div class="message-card message-card--ai">
  <div class="message-card__avatar">AI</div>
  <div class="message-card__content">消息内容</div>
</div>
```

### 6.4 导航组件

#### 顶部导航

```html
<header class="header">
  <div class="header__logo">深觅</div>
  <nav class="header__nav">
    <a class="header__nav-link header__nav-link--active" href="#">首页</a>
  </nav>
  <div class="header__actions">
    <!-- 用户操作 -->
  </div>
</header>
```

#### 标签切换

```html
<div class="tabs">
  <button class="tab tab--active">全部</button>
  <button class="tab">待完成</button>
  <button class="tab">已完成</button>
</div>
```

### 6.5 反馈组件

#### Toast 轻提示

```html
<div class="toast toast--success">
  <span class="toast__icon">✓</span>
  <div class="toast__content">
    <div class="toast__title">成功</div>
    <div class="toast__message">操作已完成</div>
  </div>
</div>
```

类型：success、warning、error、info

#### Modal 弹窗

```html
<div class="modal-overlay modal-overlay--open">
  <div class="modal">
    <div class="modal__header">
      <h3 class="modal__title">标题</h3>
      <button class="modal__close">×</button>
    </div>
    <div class="modal__body">内容</div>
    <div class="modal__footer">
      <button class="btn btn--ghost">取消</button>
      <button class="btn btn--primary">确认</button>
    </div>
  </div>
</div>
```

---

## 7. 响应式断点

| 断点 | 宽度 | 设备 |
|------|------|------|
| sm | 640px | 大手机 |
| md | 768px | 平板 |
| lg | 1024px | 小桌面 |
| xl | 1280px | 桌面 |
| 2xl | 1536px | 大桌面 |

### 移动端优先原则

1. 基础样式针对移动端
2. 使用 `min-width` 媒体查询向上适配
3. 关键断点：768px（平板）、1024px（桌面）

---

## 8. 无障碍设计

### 8.1 色彩对比度

- 正文文字与背景对比度 ≥ 4.5:1
- 大文字（18px+）对比度 ≥ 3:1
- 交互元素对比度 ≥ 3:1

### 8.2 焦点样式

```css
:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}
```

### 8.3 减少动画

```css
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
```

---

## 9. 深色模式

### 9.1 自动切换

```css
@media (prefers-color-scheme: dark) {
  :root {
    --bg-primary: var(--gray-950);
    --bg-secondary: var(--gray-900);
    --text-primary: var(--gray-100);
    --text-secondary: var(--gray-400);
  }
}
```

### 9.2 手动切换

添加 `.dark-mode` 类到 body 元素

---

## 10. 文件结构

```
frontend/styles/
├── variables.css    # CSS 变量定义
├── base.css         # 基础样式和重置
├── components.css   # 组件样式
└── layout.css       # 布局样式
```

### 使用方式

```html
<link rel="stylesheet" href="styles/variables.css">
<link rel="stylesheet" href="styles/base.css">
<link rel="stylesheet" href="styles/components.css">
<link rel="stylesheet" href="styles/layout.css">
```

---

## 11. 设计原则总结

1. **一致性**：使用设计系统中的变量和组件
2. **简洁性**：避免过度装饰，保持界面清爽
3. **可读性**：确保文字清晰易读
4. **响应性**：适配各种屏幕尺寸
5. **无障碍**：考虑所有用户的需求
6. **性能**：优化动画和过渡效果

---

*文档版本：1.0*
*最后更新：2024年*
