# llmops UI

基于 React + Vite + TypeScript 的前端项目，当前包含 GitHub OAuth 登录页。

## 开发

```bash
cd ui
npm install
npm run dev
```

前端默认运行在 `http://localhost:5173`。开发模式下通过 Vite 代理访问后端：

| 路径 | 默认代理目标 | 说明 |
|------|-------------|------|
| `/auth`、`/library`、`/file` 等 | `http://localhost:8888` | 本机 `uvicorn` |
| `/cos` | `http://localhost:8889` | Docker Nginx（仅 COS 代理） |

### 方式 A 本地开发（API 本机 8888）

```bash
# 1. 启动依赖 + Nginx（COS 代理占 8889，不占 8888）
docker compose up -d llmops-nginx llmops-postgres llmops-redis

# 2. 本机 API（8888）
cd api && uv run uvicorn main:app --host 0.0.0.0 --port 8888 --reload

# 3. 前端
cd ui && npm run dev
```

**注意：** 8888 只能给本机 API 用，不要同时让 Docker Nginx 占用 8888。

## 登录流程

1. 用户点击「使用 GitHub 登录」
2. 前端请求 `GET /auth/authorization_url` 获取 GitHub 授权链接
3. 跳转 GitHub 完成授权
4. GitHub 回调后端 `GET /auth/authorize?code=...`
5. 后端写入 `token` Cookie，并重定向到首页 `/`（默认 `http://localhost:5173/`）

## 页面路由

| 路径 | 说明 |
|------|------|
| `/` | 首页（登录成功后跳转） |
| `/login` | GitHub 登录页 |
| `/library` | 知识库管理（增删改查） |
| `/library/:libraryId/documents` | 知识库文档管理（上传、列表、下载、删除） |

## 环境变量

| 变量 | 说明 |
|------|------|
| `VITE_API_BASE_URL` | API 地址。开发环境留空（走代理）；生产环境填完整 API 域名 |

后端需配置：

| 变量 | 说明 |
|------|------|
| `GITHUB_CLIENT_ID` | GitHub OAuth Client ID |
| `GITHUB_CLIENT_SECRET` | GitHub OAuth Client Secret |
| `GITHUB_REDIRECT_URI` | 回调地址，需与 GitHub App 一致，如 `http://localhost:8888/auth/authorize` |
| `FRONTEND_URL` | 登录成功后跳转的前端地址，默认 `http://localhost:5173` |

## 构建

```bash
npm run build
npm run preview
```
