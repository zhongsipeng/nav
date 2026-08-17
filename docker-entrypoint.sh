#!/bin/sh
# =============================================================
# docker-entrypoint.sh
# 在启动主进程前完成目录初始化与权限检查
# 由 Dockerfile ENTRYPOINT 调用，已切换为 appuser
# =============================================================
set -e

echo "[entrypoint] 当前用户: $(whoami) (uid=$(id -u))"
echo "[entrypoint] 工作目录: $(pwd)"

# ----- 1. 确保可写目录存在（卷挂载空目录时自动补全子结构） -----
for dir in "$INSTANCE_PATH" "$FILE_PATH" "$LOG_PATH" "$WEB_FOLDER" \
           "$FILE_PATH/upload" "$FILE_PATH/temp" "$FILE_PATH/template"; do
    if [ -n "$dir" ] && [ ! -d "$dir" ]; then
        echo "[entrypoint] 创建目录: $dir"
        mkdir -p "$dir" 2>/dev/null || {
            echo "[entrypoint] 警告: 无法创建 $dir（可能是只读卷挂载点），跳过"
        }
    fi
done

# ----- 2. SQLite 数据库目录（从 SQLALCHEMY_DATABASE_URI 推导） -----
# 形如 sqlite:////app/db/database.db → /app/db
DB_DIR=$(echo "$SQLALCHEMY_DATABASE_URI" | sed -n 's|^sqlite:///||p' | xargs dirname 2>/dev/null || true)
if [ -n "$DB_DIR" ] && [ "$DB_DIR" != "." ] && [ ! -d "$DB_DIR" ]; then
    echo "[entrypoint] 创建数据库目录: $DB_DIR"
    mkdir -p "$DB_DIR" 2>/dev/null || echo "[entrypoint] 警告: 无法创建 $DB_DIR，跳过"
fi

echo "[entrypoint] 初始化完成，启动主进程: $@"
exec "$@"
