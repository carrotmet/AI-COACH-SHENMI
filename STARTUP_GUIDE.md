# 深觅 AI Coach - 启动指南

## 项目启动脚本使用说明

本项目提供了多个 Windows 批处理脚本来方便地启动和停止服务。

---

## 可用脚本

### 1. `start_project.bat` - 生产模式启动

用于生产环境或日常使用的启动脚本。

**特点：**
- 自动检查并初始化数据库（仅在首次运行时）
- 在后台最小化窗口运行服务
- 所有日志保存到 `logs/` 目录
- 按任意键即可停止所有服务

**使用方法：**
```batch
双击运行 start_project.bat
```

**访问地址：**
- 前端页面: http://localhost:3001
- 后端API: http://localhost:8081
- API文档: http://localhost:8081/docs

---

### 2. `start_dev.bat` - 开发模式启动

用于开发调试的启动脚本。

**特点：**
- 后端服务开启热重载（代码修改后自动重启）
- 服务运行在前台窗口，方便查看实时日志
- 每个服务运行在独立的命令行窗口中

**使用方法：**
```batch
双击运行 start_dev.bat
```

---

### 3. `stop_project.bat` - 停止服务

用于停止所有正在运行的服务。

**使用方法：**
```batch
双击运行 stop_project.bat
```

---

## 手动启动（高级用户）

如果你需要更细粒度的控制，可以手动启动服务：

### 1. 初始化数据库

```batch
cd backend
..\.venv\Scripts\python -c "from database.connection import init_db; import asyncio; asyncio.run(init_db())"
```

### 2. 启动后端服务

```batch
cd backend
..\.venv\Scripts\python main.py
```

或使用 uvicorn：
```batch
cd backend
..\.venv\Scripts\python -m uvicorn main:app --reload --host 0.0.0.0 --port 8080
```

### 3. 启动前端服务

```batch
cd frontend
..\.venv\Scripts\python -m http.server 3000
```

或使用 npm（如果已安装 Node.js）：
```batch
cd frontend
npm start
```

---

## 故障排查

### 问题1: "虚拟环境不存在"

**解决方案：**
```batch
python -m venv .venv
.venv\Scripts\pip install -r backend\requirements.txt
```

### 问题2: 端口被占用

**解决方案：**
1. 检查占用端口的进程：
   ```batch
   netstat -ano | findstr :8080
   netstat -ano | findstr :3000
   ```

2. 在任务管理器中结束对应进程，或修改启动端口：
   - 后端：修改 `backend/main.py` 中的 `PORT` 环境变量
   - 前端：修改启动命令中的端口号

### 问题3: 数据库初始化失败

**解决方案：**
1. 检查 `data/` 目录是否存在且有写入权限
2. 手动删除 `data/ai_coach.db` 文件后重新启动
3. 查看日志文件 `logs/backend.log` 获取详细错误信息

### 问题4: 前端页面无法访问后端API

**解决方案：**
1. 确认后端服务已正常启动：访问 http://localhost:8081/health
2. 检查浏览器控制台是否有 CORS 错误
3. 确认 `backend/main.py` 中的 CORS 配置正确

---

## 项目结构

```
.
├── backend/           # 后端代码 (FastAPI)
│   ├── main.py       # 主入口
│   ├── database/     # 数据库模块
│   ├── routers/      # API路由
│   ├── services/     # 业务服务
│   └── ...
├── frontend/         # 前端代码
│   ├── index.html    # 首页
│   ├── js/           # JavaScript文件
│   └── styles/       # CSS样式
├── data/             # 数据文件 (SQLite数据库)
├── logs/             # 日志文件
├── .venv/            # Python虚拟环境
├── start_project.bat # 生产启动脚本
├── start_dev.bat     # 开发启动脚本
└── stop_project.bat  # 停止服务脚本
```

---

## 注意事项

1. **首次运行**：脚本会自动初始化数据库，请确保 `data/` 目录存在且有写入权限
2. **环境变量**：可以在项目根目录创建 `.env` 文件来配置环境变量
3. **日志查看**：生产模式下日志保存在 `logs/` 目录，开发模式下直接显示在控制台
4. **安全提示**：生产环境请修改默认的 JWT 密钥和数据库配置

---

## 技术支持

如有问题，请参考：
- 项目文档：`doc/` 目录
- API文档：启动后访问 http://localhost:8081/docs
- 日志文件：`logs/` 目录
