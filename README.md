<!-- markdownlint-disable MD033 MD041 -->
<div align="center">

# MaaUma

**赛马娘日常小助手**

图像识别与模拟操作，帮助完成每天的赛事、社团请求和奖励领取。<br>
由 [MaaFramework](https://github.com/MaaXYZ/MaaFramework) 驱动，使用 [MFAAvalonia](https://github.com/MaaXYZ/MFAAvalonia) 作为操作界面。

[下载 Windows 版](https://github.com/ZhHWei0/wuma/releases) · [新手上路](docs/quick-start.md) · [功能介绍](docs/introduction.md) · [问题反馈](https://github.com/ZhHWei0/wuma/issues)

<img alt="平台 Windows x64" src="https://img.shields.io/badge/Platform-Windows%20x64-0078D4?logo=windows&logoColor=white">
<img alt="框架 MaaFramework" src="https://img.shields.io/badge/Framework-MaaFramework-00A98F">
<a href="LICENSE"><img alt="许可 MIT" src="https://img.shields.io/badge/License-MIT-blue"></a>

</div>

## 功能列表

- **进入主界面**：启动游戏，处理跳过动画、公告等进入流程。
- **社团签到**：处理上次捐赠奖励、发起跑鞋请求，支持五种跑鞋选择；已有进行中的请求时自动结束本次任务。
- **团队竞技场**：按所选对手循环参赛，自动处理比赛结果，竞技值不足时结束。
- **日常赛事安排**：日常赛事可选金币或协助积分；日常传奇赛事支持 46 个角色选项，自动查找卡片、筛选选人并参赛，无入场券时跳过对应部分。
- **限时售卖购买**：进入限时特卖，全部选择并确认。
- **领取奖励**：奖励箱、任务奖励可独立开关，默认全部开启。

赛事流程会检查并取消限时特卖弹窗，购买操作由独立任务执行。各任务的配置和适用情况见 [功能介绍](docs/introduction.md)。

## 下载与使用

1. 前往 [Releases](https://github.com/ZhHWei0/wuma/releases)，下载 **`MaaUma-v…-win-x64.zip`** 并完整解压。
2. 打开 Android 模拟器，双击解压目录中的 **`Start MaaUma.cmd`**。
3. 在前端连接模拟器，选择任务并配置，首次使用先运行“进入主界面”。

便携包已包含前端、.NET、Python Agent、OCR 模型和任务资源。GitHub 自动生成的 **Source code** 是源码；首个 Release 公开前，下载页暂时没有成品。

目前适配 **Windows x64、简体中文游戏界面、9:16 竖屏模拟器**，识别坐标按 720×1280 归一化。其他画面比例或语言需要适配。

## 使用说明

- [新手上路](docs/quick-start.md)：下载、启动和连接模拟器。
- [功能介绍](docs/introduction.md)：任务设置、运行环境和赛事流程。
- [常见问题](docs/faq.md)：更新、资源加载和识别问题。
- [团队竞技场](docs/team-arena.md) · [日常传奇赛事与角色清单](docs/daily-legend-characters.md)
- [限时售卖](docs/limited-shop.md) · [领取奖励](docs/rewards.md)

遇到问题时，可在 [Issues](https://github.com/ZhHWei0/wuma/issues) 中附上任务名称、失败截图和 MFA 导出的日志。Agent 相关问题请同时附上 `debug/maauma-agent.log`。

## 开发相关

- [本地打包、GitHub 发布与源码调试](docs/release.md)
- [资源与识别规则适配记录](docs/resource-placeholders.md)
- [MFA v2.15.2 下拉框搜索修复](docs/mfa-dropdown-search-fix.md)
- [第三方组件与许可](docs/third-party.md)

任务流程位于 `assets/resource/pipeline/`，前端配置位于 `assets/interface.json`，选卡与数字判断等辅助逻辑位于 `assets/agent/`。打包脚本会生成 Windows ZIP，并验证包内运行时、资源加载和 Agent 连接。

## 鸣谢

- [MaaFramework](https://github.com/MaaXYZ/MaaFramework)：自动化框架。
- [MFAAvalonia](https://github.com/MaaXYZ/MFAAvalonia)：通用图形前端。
- [MaaCommonAssets](https://github.com/MaaXYZ/MaaCommonAssets) 与 [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR)：OCR 模型与识别能力。
- [M9A](https://github.com/MAA1999/M9A)：发布打包与项目文档的参考。

项目代码采用 [MIT License](LICENSE)。第三方组件遵循各自许可，游戏相关图像素材的权利归其原权利方所有。
