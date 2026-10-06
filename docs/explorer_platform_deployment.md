# 当前算力平台部署

启动或在容器重启后恢复：

```bash
cd /path/to/SafeLens
bash scripts/start_explorer_platform.sh
```

服务默认使用仓库 `.venv`；也可以通过 `SAFELENS_PYTHON` 指向已有 Python 环境。
脚本通过 `PYTHONPATH` 运行当前仓库源码和已打包前端。

访问链路：平台 30000 入口 → 平台的 `ws-proxy.js` → `127.0.0.1:7860`。
在平台提供的 30000 端口基础链接后追加 `/V1/__proxy/7860/`。保留末尾斜杠，
前端资源与 API 均相对该路径解析。

进程是脱离终端的后台进程；容器重启后需要重新执行脚本。
脚本复用正常运行的服务，端口占用但健康检查失败时会报错。

- 日志：`outputs/platform/explorer.log`
- 服务 PID：`outputs/platform/explorer.pid`
- 运行数据：`outputs/local-explorer`
- 可覆盖设置：`SAFELENS_PYTHON`、`SAFELENS_PORT`、`SAFELENS_ARTIFACT_ROOT`、
  `SAFELENS_PLATFORM_HOME`、`SAFELENS_NODE`、`SAFELENS_PLATFORM_PROXY`

当前安装用于启动可视化与 API；模型任务还取决于共享环境中的可选依赖和本地模型。
现有反代不提供 Explorer 登录认证，入口访问控制沿用平台设置。

验证：反代首页、HTML 引用的 JS/CSS、`api/health`、`api/runs`、
`api/prompt/options`、`api/datasets` 均返回 HTTP 200；重复运行启动脚本成功。
