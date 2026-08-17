# =============================================================
# Dockerfile - nav 应用（Vue3 前端 + Flask 后端 单镜像同源部署）
# 多阶段构建：Stage1 编译前端 / Stage2 离线安装 Python 依赖 / Stage3 运行时
# =============================================================

# ===== Stage 1: 构建前端静态资源 =====
FROM node:26.7.0-alpine AS web-builder

WORKDIR /web

# 先拷 package*.json，利用层缓存（依赖不变时跳过 npm ci）
COPY web/package.json web/package-lock.json* ./
RUN npm ci --no-audit --no-fund

# 再拷源码并构建（dist 产物在 /web/dist）
COPY web/ ./
RUN npm run build


# ===== Stage 2: 在线安装 Python 依赖（PyPI） =====
FROM python:3.11-slim AS py-builder

WORKDIR /build

# 拷贝 requirements，从 PyPI 在线安装（不再依赖本地 wheelhouse 目录）
COPY server/requirements.txt ./

# 安装到 /install（便于 Stage 3 整体 COPY，避免重装）
# 使用 --prefix 替代 --target，确保 gunicorn 等可执行脚本被安装到 bin/ 子目录
RUN pip install --no-cache-dir -r requirements.txt --prefix=/install


# ===== Stage 3: 运行时镜像（最终产物） =====
FROM python:3.11-slim AS runtime

# 说明：项目使用 SQLite，无需 libpq5；tini 由 docker run --init / compose init:true 替代
# 这样可彻底移除 apt-get 步骤，避免 debian 源网络问题，同时减小镜像体积

# 创建非 root 用户（UID/GID 固定，便于宿主机挂卷对齐权限）
RUN groupadd -r -g 1000 appuser && \
    useradd  -r -u 1000 -g 1000 -m -d /home/appuser -s /sbin/nologin appuser

# ----- 2. 目录结构（可写路径，将作为卷挂载点） -----
ENV APP_HOME=/app \
    INSTANCE_PATH=/app/data \
    FILE_PATH=/app/file \
    LOG_PATH=/app/log \
    WEB_FOLDER=/app/web/dist \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR $APP_HOME

# 创建所有可写目录并一次性赋权给 appuser
RUN mkdir -p $INSTANCE_PATH $FILE_PATH $LOG_PATH \
             $FILE_PATH/upload $FILE_PATH/temp $FILE_PATH/template \
             $WEB_FOLDER \
             /app/log && \
    chown -R appuser:appuser $APP_HOME

# ----- 3. 拷贝依赖与代码（按变更频率从低到高分层，优化缓存） -----
# 依赖层（变动少）
# --prefix 模式下包在 lib/python3.11/site-packages/，脚本在 bin/
COPY --from=py-builder /install/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=py-builder /install/bin/ /usr/local/bin/

# 后端代码（src 布局：src/app 为应用包，src/app/run.py 为 gunicorn 入口）
COPY --chown=appuser:appuser server/src/ ./src/

# 前端构建产物
COPY --from=web-builder --chown=appuser:appuser /web/dist ./web/dist

# 入口脚本（仅 root 可写，appuser 可执行）
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# ----- 4. 切换非 root 用户 -----
USER appuser

# ----- 5. 暴露端口 -----
EXPOSE 5000

# ----- 6. 健康检查（Flask 路由已确认存在 /api/getCollect） -----
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request,sys; \
        urllib.request.urlopen('http://127.0.0.1:5000/api/getCollect', timeout=3)" \
        || exit 1

# ----- 7. 启动命令（信号处理由 docker --init 提供，gunicorn 生产 WSGI） -----
ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", \
     "--access-logfile", "-", "--error-logfile", "-", \
     "--worker-tmp-dir", "/tmp", \
     "src.app.run:app"]
