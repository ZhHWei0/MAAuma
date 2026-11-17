# MFA v2.15.2 下拉框搜索修复

已用该版本原装 `SukiUI.dll` 和完整的 46 个角色复现：搜索框只遍历已生成的 `ComboBoxItem` 修改可见性，但默认面板为 `VirtualizingStackPanel`。隐藏当前项会继续生成未经筛选的新项，因此输入中文后仍显示不匹配的角色。弹出层查找和中文角色配置本身没有出错。

本地兼容补丁仅在 `ComboBoxExtensions.OnCanSearchChanged` 启用搜索时，将面板设为 `FuncTemplate<Panel>(() => new StackPanel())`。这让全部角色参与原有的筛选逻辑，保留 `ItemsSource`、对象身份和原选项索引，避免筛选后点击角色却执行另一个角色的问题。影响该 MFA 中启用了搜索的下拉框；这类较短列表会一次生成所有选项。

补丁工具源码为 `scripts/mfa-search-fix/PatchSearch.cs`。通过 Mono.Cecil 修改指定方法，不重新编译或更换整套 MFA。只接受原装 SHA256 为 `E025C9F5138F1751039F56FBDAB0F2746A99A131C7846A21B12E321B647BFD2D` 的 `SukiUI.dll`，其他版本会拒绝修改。

退出 MFA 后，在项目根目录运行：

```powershell
.\scripts\fix-mfa-dropdown-search.ps1 -MfaDirectory 'D:\MAA_ZDH\MFAAvalonia-v2.15.2-win-x64'
```

需要 .NET SDK 8 或以上，以及 Mono.Cecil 0.11.x。脚本默认从当前用户的 NuGet 缓存读取 Mono.Cecil，也可以通过 `-CecilPath` 指定 DLL。`-BuildOnly` 只在项目 `debug/mfa-search-patch` 生成补丁，不修改安装目录。

脚本把原文件备份到 MFA 的 `backup/MaaUma-search-fix/SukiUI.dll`。需要恢复时退出 MFA 并运行：

```powershell
.\scripts\fix-mfa-dropdown-search.ps1 -MfaDirectory 'D:\MAA_ZDH\MFAAvalonia-v2.15.2-win-x64' -Restore
```

MFA 更新可能覆盖此兼容补丁；其他版本需要重新核对，不能直接套用。本项目资源包本身不包含修改后的前端二进制。

验证使用实际 SukiUI 模板和完整角色集合：全部 46 个角色的精确搜索、部分名字搜索、多结果、无结果、清空搜索、筛选后原始选择索引，以及关闭再打开恢复列表均通过。未运行游戏任务或识别测试。额外的“角色名输入（可选）”已移除，角色选择只保留原角色下拉框及其内置搜索，临时选卡测试大任务已删除。
