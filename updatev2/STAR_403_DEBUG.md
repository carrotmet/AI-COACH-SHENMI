# 星图模块 403 Forbidden 问题诊断

## 问题描述
访问星图页面时出现 403 Forbidden 错误

## 可能原因及排查步骤

### 1. 认证问题（最可能原因）

#### 症状
- 用户未登录或token已过期
- 返回的错误码是 1002 (FORBIDDEN) 或 1001 (UNAUTHORIZED)

#### 排查方法
1. 检查浏览器开发者工具 Network 标签页
2. 查看 `/api/v1/star/graph` 请求的响应状态码
3. 检查请求头中是否包含 `Authorization: Bearer xxx`

#### 解决方案
- 已在前端添加自动跳转登录页逻辑
- 确保登录后跳转回星图页面

### 2. Nginx 配置问题

#### 排查方法
```bash
# 检查nginx配置语法
nginx -t

# 查看nginx错误日志
tail -f /var/log/nginx/error.log

# 检查后端服务是否可达
curl http://backend:8080/api/v1/star/graph
```

#### 解决方案
nginx配置看起来正确，`/api/` 路径已正确代理到后端。

### 3. 后端路由问题

#### 排查方法
```bash
# 检查后端是否加载了star路由
curl -H "Authorization: Bearer YOUR_TOKEN" \
     http://localhost:8080/api/v1/star/graph
```

#### 可能的修复
1. 确保 `main.py` 中注册了 `star_router`
2. 确保 `routers/__init__.py` 导出了 `star_router`

### 4. 用户状态问题

#### 症状
- 用户状态不是 `active`
- 使用了 `require_active_user` 而不是 `get_current_user`

#### 排查方法
```sql
-- 检查用户状态
SELECT id, username, status FROM users WHERE id = ?;
```

#### 解决方案
- star路由使用的是 `get_current_user`，不检查用户状态
- 如果用户被禁用，需要联系管理员

### 5. CORS 问题

#### 症状
- 浏览器控制台显示 CORS 错误
- 预检请求 (OPTIONS) 失败

#### 解决方案
- 后端已配置 `allow_origins=["*"]`
- 确保请求头中包含正确的 `Content-Type` 和 `Accept`

## 已应用的修复

### 前端修复
1. ✅ 修复了 `star.js` 中的响应处理逻辑
   - 移除了错误的 `response.code !== 200` 检查
   - 添加了 401/403 错误处理

2. ✅ 添加了 `starAPI` 到 `api.js`
   - `api.star.getGraph(depth)`
   - `api.star.getNodeDetail(nodeId)`
   - `api.star.expandNode(nodeId)`

3. ✅ 改进了错误提示
   - 401错误 → 提示登录并跳转
   - 403错误 → 提示重新登录
   - 无测评数据 → 显示空状态引导

### 后端检查
1. ✅ `main.py` 已注册 `star_router`
2. ✅ `routers/__init__.py` 已导出 `star_router`
3. ✅ `star.py` 路由使用 `get_current_user` 依赖

## 测试步骤

1. **未登录测试**
   - 清除浏览器localStorage中的token
   - 访问星图页面
   - 预期：跳转到登录页

2. **已登录无测评测试**
   - 登录账号
   - 确保该账号没有完成过VIA测评
   - 访问星图页面
   - 预期：显示空状态，引导去测评

3. **已登录有测评测试**
   - 登录账号
   - 完成VIA测评
   - 访问星图页面
   - 预期：正常显示星图

## 日志排查

### 查看后端日志
```bash
# Docker部署
docker logs shenmi4-backend

# 本地部署
cd backend && python main.py
```

### 查看nginx日志
```bash
tail -f /var/log/nginx/access.log | grep star
tail -f /var/log/nginx/error.log
```

## 如果问题仍然存在

1. 打开浏览器开发者工具 (F12)
2. 切换到 Network 标签页
3. 刷新星图页面
4. 找到 `/api/v1/star/graph` 请求
5. 截图或复制以下信息：
   - 请求URL
   - 请求头 (Request Headers)
   - 响应状态码
   - 响应内容 (Response)
6. 检查后端日志中的对应请求记录
