# Puzzle Hub / Auth

Auth 提供了一个身份认证中心，负责账号注册、登录与管理员授权。

- 签发基于 RS256 非对称加密的 JWT。
- 提供标准的 JWKS 端点广播公钥。

## 部署

确保你已经安装了 [uv](https://github.com/astral-sh/uv)。

```bash
cd src/Auth
uv sync
uv run uvicorn main:app --reload
```
