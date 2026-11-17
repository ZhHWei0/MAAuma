# MaaUma

基于 [MaaFramework](https://github.com/MaaXYZ/MaaFramework) 的赛马娘自动化项目骨架。

当前版本包含六个任务模块：进入主界面、社团签到、团队竞技场、日常赛事安排、限时售卖购买、领取奖励。进入主界面、社团签到已按流程文档建立；日常赛事的金币和协助积分分支均已接入到参赛后关闭结果，再接入日常传奇赛事并查找、校验和点击目标角色卡片，传奇赛事已接入选人、参赛、关闭结果和限时售卖弹窗检查；团队竞技场已接入按对手选项循环参赛和结果弹窗处理。尚未提供的识图模板、OCR 文案和点击坐标保留占位，拿到实际截图后逐项替换。

## 目录

```text
assets/
  interface.json                 # Maa ProjectInterface V2
  agent/                         # 数字比较辅助程序及依赖清单
  resource/
    pipeline/                    # 任务流水线 JSON
    image/                       # 模板图
    model/ocr/                   # 必需的 OCR 模型（本地准备）
docs/
  resource-placeholders.md       # 占位资源清单
scripts/
  sync-framework.ps1             # 更新本地 MaaFramework 参考源码
  install-agent.ps1              # 为源项目或 MFA 创建独立 Agent 环境
```

## 使用方式

进入日常赛事和日常传奇赛事列表后，先在 `[607, 10, 86, 32]` 识别入场券：日常赛事为 `0/3` 时跳过并继续传奇赛事，传奇赛事为 `0/1` 时结束任务；有余票才继续选择关卡。

团队竞技场已接入循环参赛，任务设置“选着对战对手”提供 1／2／3，默认 1；每轮确认缩短版开启，跳过结果动画，处理限时售卖和奖励弹窗后再次参赛。点击“团队赛事”或“再次参赛”后若检测到“竞技值不足”，点击“否”，再点击退出位置并正常结束任务（首次进入使用固定坐标，再次参赛使用其定位向右偏移 300 像素），详见 [团队竞技场](docs/team-arena.md)。

大任务“限时售卖购买”先点击主页，再进入商店中的“限时特卖”，识别并点击“全部选择”和“确定”。日常赛事结束后已优先检查并取消限时特卖弹窗；传奇赛事结束也已接入检查，团队竞技场每场结果后也已接入检查。区域和节点见 [限时售卖](docs/limited-shop.md)。

大任务“领取奖励”提供“奖励箱”和“任务奖励”两个独立开关，默认均开启。先返回主页，再按所选项识别图标并一键领取；两项全部关闭则直接结束。区域和流程见 [领取奖励](docs/rewards.md)。

1. 准备一套完整的 OCR 模型，用 `scripts/install-ocr.ps1 -ModelDirectory '模型目录'` 安装。确认 `assets/resource/model/ocr/` 内有 `det.onnx`、`rec.onnx`、`keys.txt`，详见该目录的 README。
2. 将 `assets/` 内的 `interface.json`、整个 `resource/` 和 `agent/` 目录复制到赛马娘专用的 MFAAvalonia 程序目录，让 `interface.json` 与 `MFAAvalonia.exe` 同级。模型必须一起部署，`agent/.venv/` 不要复制，应在目标目录独立安装（见下文）。
3. 连接 Android 模拟器。当前识别坐标按短边 720 的竖屏 720x1280 配置，宽高比例不同需调整 ROI。
4. 在 `assets/resource/pipeline/` 中替换游戏包名和 `TODO_` OCR 文案，按 `docs/resource-placeholders.md` 补齐图片、坐标，并把修改同步到测试目录。
5. 准备下方 Agent 环境后重启 MFA，先单独运行“进入主界面”，再测试“社团签到”或“日常赛事安排”。内部“日常赛事”设置选择“金币”时进入月光奖并筛选英里，选择“协助积分”时进入木星杯并筛选中距离；其余流程共用，参赛后关闭结果，再进入日常传奇赛事。传奇赛事已接到参赛后关闭结果、检查限时售卖弹窗，团队竞技场已接入循环参赛。

数字比较需要保存上一次 OCR 结果，因此使用 MaaFramework 官方 Agent 扩展。准备 Python 3.9+（64 位），在项目根目录运行：

```powershell
.\scripts\install-agent.ps1 -ProjectDirectory 'D:\MAA_ZDH\MFAAvalonia-v2.15.2-win-x64' -PythonExecutable '你的Python完整路径\python.exe'
```

省略 `-ProjectDirectory` 则安装到源项目的 `assets/agent/.venv/`。目前 `maafw` 固定为 `5.12.2`，其 Windows 安装包内含配套的 Agent 二进制，与现有 MFA 的框架版本一致；更新框架时需要一并调整 `assets/agent/requirements.txt`。MFA 根据 `interface.json` 自动启动该环境，无需手工启动 Agent。辅助逻辑日志写入运行目录的 `debug/maauma-agent.log`。虚拟环境不提交 GitHub，其他电脑需要重新安装。

“社团签到”的任务配置提供“捐赠请求跑鞋”单选项，可选择短距离、英里、中距离、长距离或泥地跑鞋，默认短距离跑鞋。修改后识别并点击对应的道具名称，再在 `[351, 769, 331, 131]` 内识别“确定”并点击。配置由 `interface.json` 声明，更新时要与资源一并复制到 MFA 程序目录并重启前端；已有任务未显示新选项时，移除后重新添加“社团签到”。进入社团后直接处理上次奖励或捐赠请求，详见资源清单。

“日常赛事安排”内的“日常传奇赛事”提供 46 个角色单选项，仅显示角色名称，默认神鹰，包含两个不同版本的目白麦昆。清单与头像素材命名见 `docs/daily-legend-characters.md`，对应关系保存于 `assets/agent/daily_legend_characters.json`。46 张绿幕头像已接入：在指定列表区域寻找头像，分数达到 0.95 直接点击；0.85～0.95 时，按相对偏移校验同一卡片的名字或比赛文字，任一项通过即可点击；低于 0.85 不点击；查找前复位滑动三次、等待 1 秒；未找到则滑动 5 秒、等待 1 秒后再次识别，查找限时 50 秒（复位不计入）。更新后需同步 `agent/` 内的 `.py`、映射 JSON、资源和接口文件，并重启 MFA。

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

传奇赛事流程已接到关闭比赛结果和检查限时售卖弹窗：选卡后点击关卡，OCR 记录短距离、长距离、英里、中距离四个距离之一，按对应距离筛选选人，随后沿用日常赛事的点击三次、参赛、等待 5 秒和关闭结果操作。详见 [传奇赛事](docs/daily-legend-characters.md)。

临时选卡测试大任务已删除，重启 MFA 后移除队列中已有的旧测试项。

MFA v2.15.2 下拉框搜索未筛选的问题已定位为前端列表虚拟化与筛选逻辑冲突，提供版本限定的本地兼容补丁。角色选择只保留角色下拉框，直接使用下拉框内置搜索。安装、恢复及验证说明见 [下拉框搜索修复](docs/mfa-dropdown-search-fix.md)。
