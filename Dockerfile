# =============================================================================
# 深寻觅 AI Coach - Dockerfile
# 多阶段构建，优化镜像大小和构建效率
# =============================================================================

# -----------------------------------------------------------------------------
# 阶段1：基础依赖构建
# -----------------------------------------------------------------------------
FROM python:3.10-slim as builder

WORKDIR /build

# 安装编译依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    build-essential \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY backend/requirements.txt .

# 创建虚拟环境并安装依赖
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# 安装Python依赖
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# -----------------------------------------------------------------------------
# 阶段2：生产镜像
# -----------------------------------------------------------------------------
FROM python:3.10-slim as production

WORKDIR /app

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    APP_ENV=production \
    PORT=8080 \
    PYTHONPATH="/app"

# 安装运行时依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    libffi8 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# 从构建阶段复制虚拟环境
COPY --from=builder /opt/venv /opt/venv

# 创建必要目录
RUN mkdir -p /app/data /app/logs /app/static /app/temp

# 复制后端代码
COPY backend/ ./

# 复制前端静态文件
COPY frontend/ ./static/

# 设置权限
RUN chmod -R 755 /app/data /app/logs /app/static /app/temp

# 暴露端口
EXPOSE 8080

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# 启动命令
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080", "--log-level", "info"]

# -----------------------------------------------------------------------------
# 阶段3：开发镜像（可选）
# -----------------------------------------------------------------------------
FROM production as development

ENV APP_ENV=development \
    DEBUG=true

# 安装开发工具
RUN apt-get update && apt-get install -y --no-install-recommends \
    vim \
    git \
    && rm -rf /var/lib/apt/lists/*

# 开发模式使用单进程和自动重载
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080", "--reload", "--log-level", "debug"]
