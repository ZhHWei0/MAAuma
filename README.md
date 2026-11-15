# MaaUma

基于 [MaaFramework](https://github.com/MaaXYZ/MaaFramework) 的赛马娘自动化项目骨架。

当前版本包含四个任务模块：进入主界面、社团签到、团队竞技场、日常赛事。进入主界面、社团签到已按流程文档建立；日常赛事金币分支已接入到点击“参赛”，协助积分及日常传奇赛事待补充；团队竞技场暂时保留占位入口。尚未提供的识图模板、OCR 文案和点击坐标保留占位，拿到实际截图后逐项替换。

## 目录

```text
assets/
  interface.json                 # Maa ProjectInterface V2
  resource/
    pipeline/                    # 任务流水线 JSON
    image/                       # 模板图
    model/ocr/                   # 必需的 OCR 模型（本地准备）
docs/
  resource-placeholders.md       # 占位资源清单
scripts/
  sync-framework.ps1             # 更新本地 MaaFramework 参考源码
```

## 使用方式

1. 准备一套完整的 OCR 模型，用 `scripts/install-ocr.ps1 -ModelDirectory '模型目录'` 安装。确认 `assets/resource/model/ocr/` 内有 `det.onnx`、`rec.onnx`、`keys.txt`，详见该目录的 README。
2. 将 `assets/` 内的 `interface.json` 和整个 `resource/` 目录复制到赛马娘专用的 MFAAvalonia 程序目录，让 `interface.json` 与 `MFAAvalonia.exe` 同级。模型必须一起部署。
3. 连接 Android 模拟器。当前识别坐标按短边 720 的竖屏 720x1280 配置，宽高比例不同需调整 ROI。
4. 在 `assets/resource/pipeline/` 中替换游戏包名和 `TODO_` OCR 文案，按 `docs/resource-placeholders.md` 补齐图片、坐标，并把修改同步到测试目录。
5. 先单独运行“进入主界面”，再测试“社团签到”。日常赛事的金币分支当前执行到点击“参赛”，协助积分及日常传奇赛事待补充，团队竞技场仍为占位入口。

“社团签到”的任务配置提供“捐赠请求跑鞋”单选项，可选择短距离、英里、中距离、长距离或泥地跑鞋，默认短距离跑鞋。修改后识别并点击对应的道具名称，再在 `[351, 769, 331, 131]` 内识别“确定”并点击。配置由 `interface.json` 声明，更新时要与资源一并复制到 MFA 程序目录并重启前端；已有任务未显示新选项时，移除后重新添加“社团签到”。社团签到的固定点击坐标仍需补齐，详见占位清单。

## MaaFramework 同步

官方框架源码已下载到本地的 `MaaFramework/` 目录，并被 `.gitignore` 排除。执行：

```powershell
.\scripts\sync-framework.ps1
```

可以从官方 GitHub API 更新本地参考源码。业务项目自身建议推送到你自己的 GitHub 仓库；拿到仓库 URL 后执行：

```powershell
git remote add origin <你的仓库地址>
git push -u origin main
```

## 免责声明

请确认自动化使用符合游戏服务条款及当地法律法规。项目只提供 MaaFramework 的任务配置骨架，不包含绕过安全验证或反作弊的功能。
