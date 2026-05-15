# PDF 功能箱

一个面向 Windows 桌面的便携式 PDF 工具箱。

目标：

- 双击运行，弹出功能面板
- 不要求用户额外安装 Python
- 功能模块可持续扩展

当前已规划：

- PDF 签名移除
- PDF 转 Word
- 扫描版 PDF 转文字

## 当前结构

```text
app.py
pdf_toolbox/
  app.py
  models.py
  registry.py
  services/
  tools/
  ui/
build.bat
requirements.txt
```

说明：

- `ui/` 放主窗口和整体布局
- `tools/` 放每个功能的独立面板
- `services/` 放实际业务逻辑
- `registry.py` 负责功能注册，后续增加新功能时只需要新增模块并注册

## 当前功能

### PDF 签名移除

支持：

- 选择一个或多个 PDF 文件
- 或指定一个输入目录批量处理
- 选择输出目录
- 选择是否保留签名图案，默认保留
- 手动点击执行

说明：

- 当前实现针对 PDF 表单中的签名字段（signature widget）
- 若勾选“保留签名图案”，会尽量保留签名区域的可视痕迹
- 不同来源 PDF 的签名结构可能不同，后续可继续增强兼容性

## 本地运行

```powershell
python app.py
```

如果提示缺少依赖：

```powershell
python -m pip install -r requirements.txt
```

## 打包为免安装 exe

```powershell
build.bat
```

打包成功后，可直接双击：

```text
dist\pdf-toolbox.exe
```

## 后续扩展方式

新增一个功能时，建议：

1. 在 `pdf_toolbox/tools/` 下新增一个面板类
2. 在 `pdf_toolbox/services/` 下实现对应处理逻辑
3. 在 `pdf_toolbox/ui/main_window.py` 的 `TOOLS` 中注册

这样主程序不需要大改。
