# 深觅 AI Coach - 部署文档

本文档详细介绍了"深觅 AI Coach"系统的Docker部署方案，包括环境准备、部署步骤、配置说明和常见问题处理。

---

## 📋 目录

1. [系统要求](#系统要求)
2. [环境准备](#环境准备)
3. [快速部署](#快速部署)
4. [详细部署步骤](#详细部署步骤)
5. [配置说明](#配置说明)
6. [运维管理](#运维管理)
7. [常见问题](#常见问题)
8. [安全建议](#安全建议)

---

## 系统要求

### 硬件要求

| 配置项 | 最低配置 | 推荐配置 |
|--------|----------|----------|
| CPU | 2核 | 4核及以上 |
| 内存 | 4GB | 8GB及以上 |
| 磁盘 | 20GB | 50GB SSD |
| 网络 | 10Mbps | 100Mbps |

### 软件要求

| 软件 | 版本要求 | 说明 |
|------|----------|------|
| Docker | 20.10+ | 容器运行时 |
| Docker Compose | 2.0+ | 容器编排 |
| Linux | Ubuntu 20.04+ / CentOS 7+ | 推荐操作系统 |

### 端口要求

| 端口 | 用途 | 说明 |
|------|------|------|
| 80 | HTTP服务 | Nginx前端 |
| 443 | HTTPS服务 | Nginx SSL（可选） |
| 8000 | API服务 | FastAPI后端 |
| 6379 | Redis缓存 | 可选 |

---

## 环境准备

### 1. 安装Docker

**Ubuntu/Debian:**
```bash
# 更新包索引
sudo apt-get update

# 安装依赖
sudo apt-get install -y apt-transport-https ca-certificates curl gnupg lsb-release

# 添加Docker官方GPG密钥
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# 添加Docker仓库
echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# 安装Docker
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# 启动Docker
sudo systemctl start docker
sudo systemctl enable docker

# 添加用户到docker组（免sudo）
sudo usermod -aG docker $USER
newgrp docker
```

**CentOS/RHEL:**
```bash
# 安装依赖
sudo yum install -y yum-utils device-mapper-persistent-data lvm2

# 添加Docker仓库
sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo

# 安装Docker
sudo yum install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# 启动Docker
sudo systemctl start docker
sudo systemctl enable docker

# 添加用户到docker组
sudo usermod -aG docker $USER
newgrp docker
```

### 2. 验证安装

```bash
# 检查Docker版本
docker --version
docker compose version

# 运行测试容器
docker run hello-world
```

---

## 快速部署

### 一键部署

```bash
# 1. 克隆项目（或上传项目文件）
cd /opt
mkdir -p shenxunmi-ai-coach
cd shenxunmi-ai-coach

# 2. 上传项目文件到该目录
# - Dockerfile
# - docker-compose.yml
# - nginx.conf
# - start.sh
# - stop.sh
# - backend/ (后端代码)
# - frontend/ (前端代码)

# 3. 配置环境变量
cp backend/.env.example .env
vim .env  # 编辑配置

# 4. 启动服务
chmod +x start.sh stop.sh
./start.sh
```

### 访问服务

- **前端页面**: http://your-server-ip
- **API接口**: http://your-server-ip/api
- **API文档**: http://your-server-ip:8000/docs
- **健康检查**: http://your-server-ip/health

---

## 详细部署步骤

### 1. 项目结构准备

```
/mnt/okcomputer/output/
├── Dockerfile              # Docker镜像定义
├── docker-compose.yml      # Docker Compose配置
├── nginx.conf              # Nginx反向代理配置
├── start.sh                # 启动脚本
├── stop.sh                 # 停止脚本
├── .env                    # 环境变量（需创建）
├── data/                   # 数据目录（自动创建）
├── logs/                   # 日志目录（自动创建）
├── temp/                   # 临时目录（自动创建）
├── ssl/                    # SSL证书目录（可选）
├── backend/                # 后端代码
│   ├── main.py
│   ├── requirements.txt
│   └── ...
└── frontend/               # 前端代码
    ├── index.html
    └── ...
```

### 2. 环境变量配置

创建 `.env` 文件：

```bash
# 复制示例配置
cp backend/.env.example .env

# 编辑配置
vim .env
```

**关键配置项：**

```env
# ===========================================
# 安全配置（必须修改）
# ===========================================
# JWT密钥 - 生产环境必须使用强随机密钥
JWT_SECRET_KEY=your-super-secret-key-change-this-in-production

# ===========================================
# AI服务配置
# ===========================================
# OpenAI API密钥
OPENAI_API_KEY=sk-your-openai-api-key

# 可选：自定义OpenAI API基础URL
OPENAI_BASE_URL=https://api.openai.com/v1

# LLM模型选择
LLM_MODEL=gpt-4o-mini

# ===========================================
# 应用配置
# ===========================================
# 运行环境
APP_ENV=production
DEBUG=false

# 服务器配置
HOST=0.0.0.0
PORT=8000

# ===========================================
# 数据库配置
# ===========================================
DATABASE_URL=sqlite:///data/ai_coach.db

# ===========================================
# 对话限制配置
# ===========================================
FREE_DAILY_CHAT_LIMIT=3
BASIC_DAILY_CHAT_LIMIT=20
PRO_DAILY_CHAT_LIMIT=-1

# ===========================================
# 日志配置
# ===========================================
LOG_LEVEL=INFO
```

### 3. 启动服务

```bash
# 添加执行权限
chmod +x start.sh stop.sh

# 启动服务（自动构建镜像）
./start.sh

# 强制重新构建镜像
./start.sh --build

# 跳过镜像构建
./start.sh --skip-build

# 启动并显示日志
./start.sh --logs
```

### 4. 验证部署

```bash
# 检查容器状态
docker compose ps

# 查看服务日志
docker compose logs -f

# 测试API接口
curl http://localhost/health
curl http://localhost/api/v1/assessments

# 查看后端API文档
# 浏览器访问: http://your-server-ip:8000/docs
```

---

## 配置说明

### Docker Compose 配置

#### 服务说明

| 服务 | 镜像 | 端口 | 说明 |
|------|------|------|------|
| backend | 自定义构建 | 8000 | FastAPI后端服务 |
| nginx | nginx:alpine | 80/443 | 反向代理和静态文件 |
| redis | redis:7-alpine | 6379 | 缓存服务（可选） |

#### 数据持久化

```yaml
volumes:
  - ./data:/app/data      # SQLite数据库
  - ./logs:/app/logs      # 应用日志
  - ./temp:/app/temp      # 临时文件
```

#### 环境变量

所有环境变量都可以通过 `.env` 文件或 `docker-compose.yml` 中的 `environment` 部分配置。

### Nginx 配置

#### 主要功能

1. **静态文件服务**: 提供前端页面
2. **API代理**: 将 `/api/*` 请求转发到后端
3. **负载均衡**: 支持多后端实例
4. **速率限制**: 防止API滥用
5. **Gzip压缩**: 优化传输效率
6. **SSL支持**: HTTPS加密（可选）

#### 启用HTTPS

1. 准备SSL证书文件：
   ```bash
   mkdir -p ssl
   cp your-cert.pem ssl/cert.pem
   cp your-key.pem ssl/key.pem
   ```

2. 编辑 `nginx.conf`，取消HTTPS相关配置的注释

3. 重启服务：
   ```bash
   ./stop.sh
   ./start.sh
   ```

---

## 运维管理

### 常用命令

```bash
# 查看服务状态
docker compose ps

# 查看日志
docker compose logs -f           # 所有服务
docker compose logs -f backend   # 仅后端
docker compose logs -f nginx     # 仅Nginx

# 重启服务
docker compose restart
docker compose restart backend   # 仅重启后端

# 进入容器
docker compose exec backend bash
docker compose exec nginx sh

# 查看资源使用
docker stats

# 更新部署
docker compose pull
docker compose up -d
```

### 日志管理

#### 日志位置

| 日志类型 | 位置 | 说明 |
|----------|------|------|
| 应用日志 | `./logs/app.log` | 后端应用日志 |
| Nginx访问日志 | `./logs/nginx/access.log` | HTTP访问日志 |
| Nginx错误日志 | `./logs/nginx/error.log` | HTTP错误日志 |
| Docker日志 | `docker compose logs` | 容器标准输出 |

#### 日志轮转

Docker自动进行日志轮转，配置在 `docker-compose.yml`：

```yaml
logging:
  driver: "json-file"
  options:
    max-size: "100m"
    max-file: "3"
```

### 备份与恢复

#### 数据库备份

```bash
# 备份SQLite数据库
cp data/ai_coach.db backup/ai_coach_$(date +%Y%m%d_%H%M%S).db

# 自动备份脚本
#!/bin/bash
BACKUP_DIR="/opt/backups/ai-coach"
mkdir -p $BACKUP_DIR
cp data/ai_coach.db $BACKUP_DIR/ai_coach_$(date +%Y%m%d_%H%M%S).db
find $BACKUP_DIR -name "*.db" -mtime +30 -delete
```

#### 数据恢复

```bash
# 停止服务
./stop.sh

# 恢复数据库
cp backup/ai_coach_20240115_120000.db data/ai_coach.db

# 启动服务
./start.sh
```

### 监控与告警

#### 健康检查

```bash
# 检查服务健康状态
curl -f http://localhost/health || echo "服务异常"

# 添加到crontab定时检查
*/5 * * * * curl -f http://localhost/health || docker compose restart
```

#### 资源监控

```bash
# 查看容器资源使用
docker stats --no-stream

# 查看磁盘使用
docker system df
```

---

## 常见问题

### 1. 端口冲突

**问题**: 启动时报端口已被占用

**解决**:
```bash
# 查找占用端口的进程
sudo netstat -tulpn | grep :80
sudo lsof -i :80

# 停止占用进程或修改docker-compose.yml中的端口映射
```

### 2. 权限问题

**问题**: Docker命令需要sudo

**解决**:
```bash
# 添加用户到docker组
sudo usermod -aG docker $USER
newgrp docker

# 重新登录生效
```

### 3. 镜像构建失败

**问题**: 构建Docker镜像时出错

**解决**:
```bash
# 清理构建缓存
docker builder prune -f

# 重新构建
./start.sh --build

# 查看详细构建日志
docker compose build --no-cache --progress=plain
```

### 4. 数据库连接失败

**问题**: 应用无法连接数据库

**解决**:
```bash
# 检查数据目录权限
ls -la data/
chmod 755 data

# 检查数据库文件
ls -la data/ai_coach.db
```

### 5. AI服务调用失败

**问题**: AI对话功能无法使用

**解决**:
```bash
# 检查API密钥配置
cat .env | grep OPENAI_API_KEY

# 测试API连通性
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"

# 查看后端日志
docker compose logs backend | grep -i error
```

### 6. 内存不足

**问题**: 容器因内存不足被杀死

**解决**:
```bash
# 查看内存使用
free -h
docker stats --no-stream

# 限制容器内存（docker-compose.yml）
services:
  backend:
    deploy:
      resources:
        limits:
          memory: 1G
```

### 7. 服务启动超时

**问题**: 服务启动时间过长或超时

**解决**:
```bash
# 查看详细日志
docker compose logs -f

# 检查依赖服务状态
docker compose ps

# 单独启动服务排查
docker compose up backend
```

---

## 安全建议

### 1. 环境变量安全

- 生产环境必须使用强随机JWT密钥
- API密钥不要提交到代码仓库
- 使用 `.env` 文件管理敏感配置
- 限制 `.env` 文件权限：`chmod 600 .env`

### 2. 网络安全

- 生产环境启用HTTPS
- 配置防火墙，仅开放必要端口
- 使用强密码和密钥认证
- 定期更新系统和依赖

### 3. 容器安全

- 使用非root用户运行容器
- 定期更新基础镜像
- 扫描镜像漏洞
- 限制容器资源使用

### 4. 数据安全

- 定期备份数据库
- 加密敏感数据
- 实施访问控制
- 记录审计日志

---

## 附录

### 环境变量完整列表

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| APP_ENV | production | 运行环境 |
| DEBUG | false | 调试模式 |
| HOST | 0.0.0.0 | 监听地址 |
| PORT | 8000 | 服务端口 |
| DATABASE_URL | sqlite:///data/ai_coach.db | 数据库连接 |
| JWT_SECRET_KEY | - | JWT密钥（必填） |
| JWT_ALGORITHM | HS256 | JWT算法 |
| OPENAI_API_KEY | - | OpenAI API密钥 |
| LLM_MODEL | gpt-4o-mini | LLM模型 |
| LOG_LEVEL | INFO | 日志级别 |

### 更新日志

| 版本 | 日期 | 说明 |
|------|------|------|
| 1.0.0 | 2024-01 | 初始版本 |

---

## 技术支持

如有问题，请通过以下方式获取帮助：

1. 查看项目文档
2. 检查服务日志
3. 提交Issue

---

**文档版本**: v1.0.0  
**最后更新**: 2024年
