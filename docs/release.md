# Windows 便携包打包与发布

打包参照 [M9A 的发行流程](https://github.com/MAA1999/M9A/blob/main/.github/workflows/release.yml)：把前端、任务资源和运行时装入同一个 ZIP，让用户解压后直接运行。当前仅构建 Windows x64。

## 本地打包

在 Windows x64 上使用 Python 3.12，在仓库根目录运行：

```powershell
python -X utf8 scripts/build-release.py --version v0.1.0
```

省略 `--version` 会读取 `assets/interface.json` 中的版本。脚本自动下载锁定的官方 MFA、.NET、嵌入式 Python、Agent wheels、中文 OCR 模型，按 `scripts/release-dependencies.json` 校验后缓存到 `build/release-cache/`。不需要事先安装 MFA、准备模型或安装 Python 依赖。可通过 `--cache` 和 `--output` 更改目录。

输出为 `dist/MaaUma-v0.1.0-win-x64.zip` 和同名 `.sha256`。测试从 ZIP 解压到新的路径，使用包内 Python 和前端的 MaaFramework 加载项目资源、连接包内 Agent 并检查自定义动作；不启动游戏或模拟器。包内含 [快速开始](quick-start.md) 和 [第三方声明](third-party.md)。

## GitHub 发布

1. 提交并推送项目变更到 GitHub（包括 `.github/workflows/release.yml`）。
2. 可在 **Actions → Build Windows package → Run workflow** 手动打包预览，从本次运行的 Artifacts 下载。仅需要首发时，也可直接把本地打包的 ZIP 和 SHA256 上传到 Release 草稿。
3. 正式发版时在所需提交上创建并推送版本标签，例如：

   ```powershell
   git tag v0.1.0
   git push origin v0.1.0
   ```

4. 工作流会构建 ZIP 并创建 **Draft Release**。核对版本、压缩包和说明后，在 Releases 中点击 **Publish release**。用户只需要下载 ZIP 成品，GitHub 自动生成的 “Source code” 是源码。

## 日常开发

如果使用已有的 MFA 环境调试，可将 `assets/interface.json`、`assets/resource/` 与 `assets/agent/` 的源码复制到 MFA 程序目录，先按 [OCR 模型说明](../assets/resource/model/ocr/README.md) 准备模型，再在目标目录安装 Agent 环境。不要跨目录复制 `.venv`。

```powershell
.\scripts\install-agent.ps1 -ProjectDirectory 'D:\MFAAvalonia' -PythonExecutable 'C:\Python312\python.exe'
```

改动流程后同步对应资源到调试目录并重启前端。仅需参考 MaaFramework 源码时才运行 `scripts/sync-framework.ps1`；它不更新前端或业务资源。打包时从官方 ZIP 重新生成，独立于日常调试目录。
