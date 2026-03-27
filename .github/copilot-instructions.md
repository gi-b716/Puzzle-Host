# 项目概览：去中心化 Puzzlehunt 平台

你好！我们将一起开发一个**去中心化的 Puzzlehunt（解谜寻宝）平台**。该平台在架构上解耦为三个完全独立的部分：**Serverless 前端**、**Auth 系统（身份验证）**、**Puzzles 系统（题目与核心业务）**。

Auth 系统和 Puzzles 系统可以由不同的组织部署在任意服务器上。前端纯静态托管，用户可以在前端自行输入并连接不同的 Auth API 和 Puzzles API 网址。

## 1. 技术栈规范 (Tech Stack)

### 前端 (Frontend)
*   **包管理工具**：必须使用 `pnpm`。
*   **核心框架**：Vue 3 (必须使用 Composition API 和 `<script setup>` 语法，**绝对禁止**使用 Vue 2 的 Options API)。
*   **构建工具 & 语言**：Vite + TypeScript。
*   **路由 & 状态管理**：Vue Router + Pinia（使用 `pinia-plugin-persistedstate` 实现持久化存储）。
*   **UI & 样式**：Tailwind CSS + shadcn-vue (基于 Radix Vue 的无头组件库)。
*   **网络请求**：Axios 或原生 Fetch API（需要支持动态 BaseURL，因为不同模块的 API 地址不同）。

### 后端 (Backend - Auth & Puzzles 均适用)
*   **包管理与运行工具**：必须使用 `uv` 管理依赖和虚拟环境。
*   **核心框架**：FastAPI + Python 3.13+。
*   **数据库 & ORM**：SQLite + SQLAlchemy 2.0 (或 SQLModel)，使用 Alembic 管理迁移。
*   **认证机制**：PyJWT。必须使用**非对称加密 (RS256)**。

## 2. 核心架构与业务逻辑设计

### 模块一：Auth 系统 (Identity Provider)
*   **定位**：纯粹的身份提供者（IdP）。只负责处理用户的注册、登录，以及系统级管理员（Super Admin）的管理。
*   **输出**：验证成功后，使用 RS256 私钥签发包含 `user_id` 等基础信息的 JWT。
*   **接口**：必须提供一个公开的 JWKS 端点（如 `/.well-known/jwks.json`），用于对外广播公钥。不涉及任何具体的业务逻辑（无队伍、无题目）。

### 模块二：Puzzles 系统 (Resource Server)
*   **定位**：具体的解谜比赛服，负责题目展示、答题提交、排行榜计算，**以及组队逻辑（Teaming）**。
*   **鉴权逻辑**：通过用户提供的 Auth 系统 JWKS URL，动态拉取公钥并在本地验证 JWT 的合法性，**绝对不使用对称加密密码**，也不向 Auth 系统发起实时验证请求。
*   **动态配置**：系统必须是“纯动态配置”的。管理员信任的 Auth 系统 URL、题目内容、信任 IP 等，全生存于 SQLite 数据库中，通过 API 动态修改，不需要修改本地配置文件或重启服务。

### 模块三：Serverless 前端 (SPA)
*   **连接管理**：用户可以在页面上输入 Auth API 和 Puzzles API 的地址。这些历史连接信息保存在本地（基于 Pinia 持久化），支持导出为 JSON 或从本地加载。
*   **管理后台 (Admin Panel)**：没有独立的后端渲染管理页面。Admin 面板集成在前端 SPA 中。通过路由懒加载和后端的 API 角色校验（依赖注入）来保证安全。当拥有 `is_admin` 权限的用户登录后，前端渲染管理界面。

## 3. AI 编程助手的行为准则 (Rules for AI)

在后续生成代码时，请严格遵守以下原则：
1.  **Vue 代码规范**：只写 `<script setup lang="ts">`。样式优先使用 Tailwind CSS 类名，需要复杂交互组件时优先使用 `shadcn-vue` 规范的代码。不写传统的 `.css` 类名绑定。
2.  **FastAPI 代码规范**：所有 I/O 密集型操作（如请求 JWKS）考虑异步，依赖注入（`Depends`）要职责单一。所有配置项（包括第三方 Auth 接口地址）设计为查库获取，而非从 `.env` 读取。
3.  **安全性**：永远假设前端是不安全的。即使前端隐藏了 Admin 面板入口，FastAPI 的所有 `/api/admin/*` 路由都必须进行严格的 JWT 角色校验。
4.  **去中心化思维**：在写代码时时刻牢记：Puzzles 系统的代码里不能包含对某个特定 Auth 系统的强耦合，它必须能够通过修改数据库里的 JWKS URL 随时切换信任的 Auth 服务器。

请回复“收到”，并在接下来的对话中默认应用上述所有上下文。
