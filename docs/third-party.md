# 随 MaaUma Windows ZIP 分发的组件

- **MFAAvalonia v2.15.2**（GPL-3.0）：本包使用上游原版 Windows x64 二进制，原版许可见 `licenses/MFAAvalonia-LICENSE.txt`。[上游发布及对应源码下载](https://github.com/MaaXYZ/MFAAvalonia/releases/tag/v2.15.2) · [对应源码树](https://github.com/MaaXYZ/MFAAvalonia/tree/v2.15.2)。许可适用于 MFAAvalonia 本身，MaaUma 任务配置和 Agent 单独提供。
- **MaaFramework／maafw 及 MaaAgentBinary**：来自 MFAAvalonia 和 [PyPI maafw](https://pypi.org/project/MaaFw/5.12.2/)、[MaaAgentBinary](https://pypi.org/project/MaaAgentBinary/1.0.1/)；保留 Python 包中的许可证。参见 [MaaFramework 源码](https://github.com/MaaXYZ/MaaFramework)。
- **OCR**：使用 [MaaCommonAssets 的 PP-OCRv4 中文模型与字典](https://github.com/MaaXYZ/MaaCommonAssets/tree/dabcd4681ac990dc4361de26416d986abd80e4aa/OCR/ppocr_v4/zh_cn)，源自 [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR)，上游说明及许可见该项目与 `licenses/MaaCommonAssets-LICENSE.txt`。
- **Python 3.12**：来自 [Python 官方嵌入式发行包](https://www.python.org/downloads/release/python-31210/)，许可见 `python/LICENSE.txt`。NumPy 与 StrEnum 许可保留在对应的 `python/packages/*.dist-info` 目录。
- **Microsoft .NET Runtime 10**：来自 [.NET 官方运行时](https://dotnet.microsoft.com/download/dotnet/10.0)，许可及第三方声明见 `dotnet/`。

各个下载文件的版本、来源和校验值见 MaaUma 源码中的 `scripts/release-dependencies.json`。
