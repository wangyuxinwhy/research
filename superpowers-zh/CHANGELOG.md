# 更新日志

## [5.0.5] - 2026-03-17

### 修复

- **头脑风暴服务器 ESM 修复**：将 `server.js` 重命名为 `server.cjs`，使头脑风暴服务器在 Node.js 22+ 上能正确启动——此前根目录 `package.json` 中的 `"type": "module"` 会导致 `require()` 调用失败。（[PR #784](https://github.com/obra/superpowers/pull/784)，由 @sarbojitrana 提交，修复 [#774](https://github.com/obra/superpowers/issues/774)、[#780](https://github.com/obra/superpowers/issues/780)、[#783](https://github.com/obra/superpowers/issues/783)）
- **头脑风暴服务器在 Windows 上的 owner-PID 问题**：在 Windows/MSYS2 上跳过 `BRAINSTORM_OWNER_PID` 生命周期监控，因为该环境下 PID 命名空间对 Node.js 不可见。此修复防止服务器在 60 秒后自行终止。30 分钟空闲超时仍作为安全保障机制保留。（[#770](https://github.com/obra/superpowers/issues/770)，文档来自 [PR #768](https://github.com/obra/superpowers/pull/768)，由 @lucasyhzhu-debug 提交）
- **stop-server.sh 可靠性提升**：在报告成功前验证服务器进程是否已真正终止。等待最多 2 秒进行优雅关闭，若无效则升级为 `SIGKILL`，如果进程仍然存活则报告失败。（[#723](https://github.com/obra/superpowers/issues/723)）

### 变更

- **执行交接**：在计划编写完成后，恢复用户在子代理驱动开发（subagent-driven-development）和执行计划（executing-plans）之间的选择权。推荐使用子代理驱动方式，但不再强制要求。（回退 `5e51c3e`）
