# 为 Codex 安装 Superpowers

通过原生技能发现机制在 Codex 中启用 superpowers 技能。只需克隆仓库并创建符号链接。

## 前置要求

- Git

## 安装

1. **克隆 superpowers 仓库：**
   ```bash
   git clone https://github.com/obra/superpowers.git ~/.codex/superpowers
   ```

2. **创建技能符号链接：**
   ```bash
   mkdir -p ~/.agents/skills
   ln -s ~/.codex/superpowers/skills ~/.agents/skills/superpowers
   ```

   **Windows（PowerShell）：**
   ```powershell
   New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.agents\skills"
   cmd /c mklink /J "$env:USERPROFILE\.agents\skills\superpowers" "$env:USERPROFILE\.codex\superpowers\skills"
   ```

3. **重启 Codex**（退出并重新启动 CLI）以发现技能。

## 从旧版引导方式迁移

如果你在原生技能发现机制之前就安装了 superpowers，需要：

1. **更新仓库：**
   ```bash
   cd ~/.codex/superpowers && git pull
   ```

2. **创建技能符号链接**（上面的第 2 步）—— 这是新的发现机制。

3. **移除旧的引导代码块** —— 从 `~/.codex/AGENTS.md` 中删除任何引用 `superpowers-codex bootstrap` 的代码块，它们不再需要了。

4. **重启 Codex。**

## 验证

```bash
ls -la ~/.agents/skills/superpowers
```

你应该能看到一个符号链接（Windows 上为联结点）指向你的 superpowers 技能目录。

## 更新

```bash
cd ~/.codex/superpowers && git pull
```

技能通过符号链接即时更新。

## 卸载

```bash
rm ~/.agents/skills/superpowers
```

可选：删除克隆的仓库：`rm -rf ~/.codex/superpowers`。
