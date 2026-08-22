# Nav 个人书签导航系统(智能起始页) 

基于 **Vue3 + Flask + SQLite** 的本地导航收藏系统：支持树形文件夹/书签管理、拖拽排序、书签导入导出、网站图标抓取，并提供 **Docker 部署**与 **Windows 单文件桌面应用**（exe）两种交付形态。

![](https://github.com/zhongsipeng/PicGo/raw/main/img/navdemo.gif)

## 功能特性

- 收藏树管理：文件夹与书签的新增、编辑、删除、拖拽排序
- 书签导入 / 导出（Netscape HTML 格式，兼容浏览器）
- 自动抓取网站 favicon 作为书签图标
- 桌面版：单实例（重复双击不重复启动）、pywebview 原生窗口、双击直接启动


## 目录结构

```text
nav/
├── server/                        # Flask 后端（Python src 布局）
│   ├── src/app/                   # 应用代码（api / service / repository / model / core）
│   ├── test/                      # pytest 测试
│   ├── desktop_launcher.py        # 桌面版启动入口（PyInstaller 打包）
│   ├── build_exe.bat              # 一键打包 NavApp.exe
│   ├── requirements.txt           # 服务端 / Docker 依赖
│   ├── requirements-desktop.txt   # 桌面版专用依赖（不进入 Docker）
│   └── configs/.env               # 本地可选配置（gitignore）
├── web/                           # Vue3 + Vite 前端
│   ├── src/                       # 前端源码
│   └── dist/                      # 构建产物（由后端直接托管）
├── Dockerfile                     # 多阶段构建（前端 + Python 依赖 + 运行时）
├── docker-compose.yml
└── docker-entrypoint.sh
```

## 本地开发

前置：Python 3.12+、Node.js 18+。

后端（提供 API）：

```sh
cd server
python -m venv .venv
.venv\Scripts\activate        # Windows；Linux/macOS 用 source .venv/bin/activate
pip install -r requirements.txt
python src/app/run.py         # http://127.0.0.1:5000
```

前端（Vite 开发服务器，已配置 `/api` 代理到 5000 端口）：

```sh
cd web
npm install
npm run dev
```

构建前端产物（后端托管 `web/dist`，Docker 与桌面版均使用该产物）：

```sh
cd web && npm run build
```

本地路径等可选配置写在 `server/configs/.env`（例如 `WEB_FOLDER`、`DEBUG`），也可用环境变量覆盖。

## 测试

```sh
cd server
pytest
```

## Docker 部署

```sh
docker compose build -t nav:1.0 .
docker compose up -d
```

- 访问：`http://localhost:${HOST_PORT:-5000}`
- 数据：SQLite 持久化到宿主机 `./data/db`
- 健康检查：`/api/getCollect`
- 生产 WSGI：`gunicorn -w 4 "src.app.run:app"`（在容器内执行）

## 桌面版 exe（Windows）

```sh
cd server
build_exe.bat
```

产物：`server/dist/NavApp.exe`（单文件，含前端、图标与 pywebview 原生窗口）。

- 双击启动：自动绑定端口（默认 5000，可用 `NAV_PORT` 覆盖）并弹出应用窗口
- 单实例：运行中再次双击不会重复启动
- 退出：关闭窗口，或点击页面右上角“退出”按钮
- 测试/自动化开关：`NAV_NO_WINDOW=1`（不创建窗口，仅启动本地服务）
- 依赖：需系统已安装 WebView2 运行时（Windows 10/11 通常自带）

## 配置项（环境变量）

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `INSTANCE_PATH` | `server/data` | 实例目录（SQLite 等） |
| `FILE_PATH` | `server/file` | 上传与临时文件目录 |
| `LOG_PATH` | `server/log` | 日志目录 |
| `WEB_FOLDER` | `configs/.env` 指定 | 前端静态目录（生产用 `web/dist`） |
| `SQLALCHEMY_DATABASE_URI` | `sqlite:///database.db` | SQLite 连接串（Docker 指向挂载卷） |
| `NAV_PORT` | `5000` | 桌面版端口 |
| `NAV_NO_WINDOW` | 关闭 | 桌面版测试开关（不创建窗口） |
| `HOST_PORT` | `5000` | Docker 宿主端口（compose） |

## API 概览

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| POST | `/api/getCollect` | 获取收藏树 |
| POST | `/api/saveCollect` | 新增 / 编辑节点 |
| POST | `/api/batchUpdate` | 批量更新排序（px/pid） |
| POST | `/api/delCollect` | 删除节点 |
| POST | `/api/importCollect` | 导入书签 HTML |
| GET | `/api/exportCollect` | 导出书签 HTML |


## 依赖说明

- `server/requirements.txt`：服务端与 Docker 镜像依赖（Flask、SQLAlchemy、pydantic 等）。
- `server/requirements-desktop.txt`：仅桌面 exe 需要，Docker 构建不安装。
