# Puzzle Hub / Puzzles

Puzzles 提供了具体的解谜比赛服，负责题目展示、答题提交、排行榜以及组队逻辑。

- 通过配置 Auth 系统的 JWKS URL，动态拉取公钥并本地验证 JWT，实现与 Auth 系统的解耦。
- 所有系统设置、题目数据、信任的 Auth 节点均存储于 SQLite，通过 Admin API 动态修改，无需改动代码或环境变量。

## 部署

确保你已经安装了 [uv](https://github.com/astral-sh/uv)。

```bash
cd src/Puzzles
uv sync
uv run uvicorn main:app --reload
```
