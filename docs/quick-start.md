# MaaUma 快速开始

1. 从 [GitHub Releases](https://github.com/ZhHWei0/wuma/releases) 下载 `MaaUma-v…-win-x64.zip`，完整解压到自己的目录。请下载 Windows ZIP 成品，GitHub 的 “Source code” 是源码。
2. 启动安装有简体中文版赛马娘（包名 `com.bilibili.umamusu`）的 Android 模拟器。游戏画面使用 9:16 竖屏，首次登录可先手动完成。
3. 在解压目录双击 **Start MaaUma.cmd**。它会为前端使用包内的 .NET；Python、OCR 模型和项目资源也已随包提供。
4. 在 MFAAvalonia 的连接设置中检测并选择模拟器。未检测到时，使用模拟器自带的 `adb.exe`，填写该实例的 ADB 地址和端口。不同模拟器与多开实例的端口可能不同。
5. 先运行“进入主界面”，然后添加所需任务。任务设置可选择跑鞋、竞技场对手、日常赛事奖励类别和传奇赛事角色；领取奖励的两个开关默认都开启。

程序打开失败并提示缺少 `VCRUNTIME`、`MSVCP` 等系统库时，安装 Microsoft 的 [Visual C++ x64 Redistributable](https://aka.ms/vs/17/release/vc_redist.x64.exe)，再运行启动脚本。已安装该系统组件的电脑无需重复安装。

升级时建议将新版本解压到新目录。遇到任务识别问题时，请提供任务名、失败截图及 MFA 导出的日志；如有关 Agent，另请附上 `debug/maauma-agent.log`。
