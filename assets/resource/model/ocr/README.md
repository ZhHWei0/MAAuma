# OCR 模型

本项目使用 OCR，运行时此目录必须同时包含以下三个文件：

```text
det.onnx
rec.onnx
keys.txt
```

仅有此 README 会导致 MaaFramework 报 `model file not found`，进而导致整个资源包加载失败。

从 MaaCommonAssets 或已安装的 MaaFramework 工具包取得一套完整的模型，不要混用不同版本的识别模型和字典。在项目根目录执行：

```powershell
.\scripts\install-ocr.ps1 -ModelDirectory '包含这三个文件的目录'
```

部署到 MFAAvalonia 时，也必须把这三个文件一起复制到程序的 `resource/model/ocr/`。模型与字典属于本地运行依赖，已通过 `.gitignore` 排除；从 GitHub 克隆项目后需要重新准备。

本地测试使用 MFAToolsPlus 附带的 PP-OCRv4 中文模型。来源：[PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR) / [MaaCommonAssets](https://github.com/MaaXYZ/MaaCommonAssets)。
