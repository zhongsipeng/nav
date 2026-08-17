"""应用入口模块

启动 Flask 开发服务器，监听所有网络接口的 5000 端口。
生产环境建议使用 gunicorn 或 uWSGI 部署。
"""

from src.app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
