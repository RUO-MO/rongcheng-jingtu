# 蓉城净途 · Web 前端

基于 **Vue 3 + Vite** 的交互式健康导航界面，负责地图渲染、起点/目的地输入、路线偏好切换、结果展示与实时导航。前端通过 REST 与 Socket.IO 调用 `python/` 后端，地图能力来自高德地图 JS API 2.0。

## 环境要求

| 依赖 | 版本 |
| --- | --- |
| Node.js | ≥ 20.19（Vite 8 要求） |
| 高德 JS API | 安全密钥 `VITE_AMAP_SECURITY_CODE`（与后端 Web 服务 Key 同一账号） |

## 快速开始

```bash
npm install
copy .env.example .env      # Windows；Linux/macOS 用 cp
# 编辑 .env，填入 VITE_AMAP_SECURITY_CODE
npm run dev                 # http://localhost:3000
```

- 中文界面：<http://localhost:3000/index.html>
- 英文界面：<http://localhost:3000/index_en.html>

开发服务器会把 `/api` 与 `/socket.io`（含 WebSocket 升级）代理到 `http://localhost:5000`，因此需先启动后端。

## 可用命令

| 命令 | 作用 |
| --- | --- |
| `npm run dev` | 启动开发服务器（端口 3000，监听 `0.0.0.0`） |
| `npm run build` | 生产构建，双入口产物输出到 `dist/` |
| `npm run preview` | 本地预览构建产物 |

## 目录结构

```
frontend/
├── index.html                 # 中文入口，注入安全密钥
├── index_en.html              # 英文入口
├── vite.config.js             # 双入口构建 + API/Socket.IO 代理
├── .env.example               # 环境变量模板
├── public/
│   ├── favicon.svg
│   └── icons.svg
└── src/
    ├── main_zh.js / main_en.js # 两套入口的挂载脚本
    ├── App.vue
    ├── components/            # HomeView 等页面组件
    ├── composables/           # useAMapStrict：地图加载与实例管理
    ├── locales/               # zh.js / en.js 文案
    ├── router/                # vue-router 配置
    └── style.css
```

## 交互状态说明

- **加载中**：地图初始化前展示骨架占位，规划请求期间按钮进入禁用态。
- **空状态**：未选择目的地时结果面板提示输入起点与目的地，不发起请求。
- **错误**：参数超限、密钥失效或后端不可达时，面板显示可读错误信息并保留用户输入。
- **成功**：展示最优访问顺序、总距离、平均 AQI、健康评分与逐站 AQI，并在地图上绘制路线。

## 常见问题

| 现象 | 排查 |
| --- | --- |
| 地图空白 / `INVALID_USER_SCODE` | `.env` 未填写 `VITE_AMAP_SECURITY_CODE`，或修改后未重启 Vite |
| 接口 404 / 连接被拒绝 | 后端未启动，或未监听 5000 端口 |
| Socket.IO 频繁重连 | 代理未配置 `ws: true`，检查 `vite.config.js` |
| 构建后刷新 404 | 部署端需将未知路由回退到 `index.html` |

完整项目说明见仓库根目录 [`README.md`](../README.md)。
