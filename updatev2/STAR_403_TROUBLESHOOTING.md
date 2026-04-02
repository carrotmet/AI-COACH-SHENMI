# 星图403错误 - 完整排查指南

## 快速诊断

### 浏览器端诊断
在星图页面打开浏览器控制台(F12)，粘贴以下代码：

```javascript
fetch('/api/v1/star/graph?depth=3', {
    headers: { 'Authorization': `Bearer ${localStorage.getItem('access_token')}` }
}).then(r => r.json()).then(d => console.log(d))
```

**预期正常响应：**
```json
{
    "code": 200,
    "message": "请求成功",
    "data": { "nodes": [...], "edges": [...] }
}
```

**如果出现403，查看 `data.message` 获取详细原因**

---

## 403错误的具体原因及解决方案

### 原因1: 用户未登录 (最常见)

**症状:**
- 浏览器控制台显示401/403
- localStorage中没有 `access_token`

**验证:**
```javascript
localStorage.getItem('access_token')  // 返回null
```

**解决:**
前端已自动处理，会跳转到登录页。

---

### 原因2: Token过期

**症状:**
- Token存在但已过期
- 后端日志显示 "Token已过期"

**验证:**
```javascript
const token = localStorage.getItem('access_token');
const payload = JSON.parse(atob(token.split('.')[1]));
console.log(new Date(payload.exp * 1000));  // 过期时间
```

**解决:**
- 前端已配置自动刷新token
- 如刷新失败，会跳转登录页
- 手动清除token重新登录:
```javascript
localStorage.clear();
location.href = '/login.html';
```

---

### 原因3: 用户状态非active

**症状:**
- Token有效但返回403
- 后端日志显示 "用户账户未激活"

**数据库验证:**
```sql
SELECT id, username, status FROM users WHERE id = ?;
-- status 应该是 'active'
```

**解决:**
需要管理员在数据库中更新用户状态：
```sql
UPDATE users SET status = 'active' WHERE id = ?;
```

---

### 原因4: 后端路由未正确注册

**症状:**
- 返回404而非403（如果nginx正确配置）
- 或者返回nginx的403页面

**验证:**
```bash
# 检查后端路由
grep "star_router" backend/main.py
grep "star" backend/routers/__init__.py
```

**解决:**
确保以下文件正确修改：
- `backend/main.py` - 导入并注册star_router
- `backend/routers/__init__.py` - 导出star_router

---

### 原因5: Nginx配置问题

**症状:**
- 静态文件正常，API返回403
- 返回nginx的403错误页面（不是JSON）

**验证:**
```bash
# 检查nginx配置
grep "location /api/" nginx.conf

# 检查后端是否可访问
curl http://localhost:8080/api/v1/star/graph
```

**解决:**
nginx配置应包含：
```nginx
location /api/ {
    proxy_pass http://backend_servers;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header Authorization $http_authorization;  # 关键！
}
```

---

## 修复状态汇总

### 已完成的修复

| 文件 | 修复内容 |
|------|----------|
| `backend/routers/star.py` | 使用 `success_response()` 统一响应格式 |
| `backend/routers/star.py` | 修正 `current_user` 字典访问方式 |
| `frontend/js/api.js` | 添加 `starAPI` 对象 |
| `frontend/star/star.js` | 修复响应处理，添加401/403错误处理 |
| `frontend/star/index.html` | 添加调试脚本引用 |

### 需要后端重启

修改后端代码后，需要重启后端服务才能生效：

```bash
# Docker部署
docker restart shenmi4-backend

# 或使用docker-compose
docker-compose restart backend

# 本地部署
cd backend && python main.py
```

---

## 验证步骤

1. **登录账号**
   - 访问 `/login.html`
   - 使用有效账号登录

2. **检查token**
   - 浏览器F12 → Application → Local Storage
   - 确认有 `access_token` 和 `refresh_token`

3. **访问星图**
   - 访问 `/star/index.html`
   - 观察是否还有403错误

4. **如仍有问题**
   - 在星图URL后添加 `#debug`：`/star/index.html#debug`
   - 打开控制台查看诊断输出
   - 复制错误信息给开发者

---

## 联系信息

如果以上步骤无法解决问题，请提供：
1. 浏览器控制台完整输出
2. 后端日志相关片段
3. 用户ID和登录账号
