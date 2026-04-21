# openclaw-skills

这是一个用于 **OpenClaw skills 开发** 的 Python 项目骨架（页面状态检查骨架 v1，含最小真实检查）。

## 当前项目进展说明

当前已提供一个“**更接近真实执行器的本地骨架版本**”，入口为 `skills/aba_fetch/main.py`。

这个版本的目标是：
- 保持低风险前提下，把纯展示文案升级为可执行的步骤化流程。
- 在结构上支持页面状态检查：
  - `check_browser_open()`：检查浏览器是否已打开（最小真实实现：进程检查）
  - `check_amazon_page()`：检查当前是否在 Amazon 页面（占位实现）
  - `check_aba_page_ready()`：检查是否大致位于 ABA 页面（占位实现）
- 保留后续关键环节占位：导出动作、导出文件解析、飞书写入。

## 当前阶段能力说明

当前版本可以：
- 运行一个 6 步执行器风格流程（3 个状态检查 + 3 个业务占位步骤）。
- 在每一步输出统一的状态码和 PASS/FAIL 结果。
- 在检查不通过时提前终止，并给出终止原因。
- 真实检查本机是否存在常见浏览器进程（Chrome / Edge）：
  - Windows 下使用 `tasklist` 检查 `chrome.exe` / `msedge.exe`
  - 非 Windows 环境下使用 `ps` 进行兼容性检查（便于本地开发与测试）
- 在代码结构上为后续替换成真实逻辑预留清晰入口。

## 当前版本不能做什么

当前版本**不能**：
- 真实抓取 ABA 数据。
- 自动控制浏览器（不做浏览器自动化）。
- 自动登录 Amazon（不处理账号密码、验证码）。
- 调用真实飞书接口写入数据。
- 解析真实导出文件。
- 做批量店铺并发处理。

换句话说：现在是“页面状态检查骨架版”，不是“生产可用版”。

## 真实能力 vs 占位能力（当前版本）

- 真实能力：
  - 浏览器是否已打开：真实进程检查（Chrome / Edge）。
- 占位能力：
  - Amazon 页面判定（`check_amazon_page()`）。
  - ABA 页面就绪判定（`check_aba_page_ready()`）。
  - 导出、解析、飞书写入步骤。

## 目录结构

```text
openclaw-skills/
  README.md
  pyproject.toml
  requirements.txt
  .env.example
  skills/
    __init__.py
    aba_fetch/
      __init__.py
      README.md
      config.example.json
      main.py
    common/
      __init__.py
      utils.py
  docs/
    skill-spec.md
    feishu-fields.md
    next-step-plan.md
  tests/
    test_demo.py
```

## 快速开始

1. （可选）创建并激活虚拟环境
2. 安装依赖：

```bash
pip install -r requirements.txt
```

3. 运行演示：

```bash
python skills/aba_fetch/main.py
```

或使用模块方式运行：

```bash
python -m skills.aba_fetch.main
```

4. 运行测试：

```bash
pytest
```

## Windows / PowerShell 运行注意事项

为了在 Windows PowerShell 下获得更稳定的输出与测试结果，脚本持续避免使用容易触发编码问题的特殊字符。默认可直接运行：

```powershell
python -m skills.aba_fetch.main
pytest -q
```

如你的终端仍出现中文乱码或编码异常，可临时启用 UTF-8 模式后再运行：

```powershell
$env:PYTHONUTF8="1"
python -m skills.aba_fetch.main
pytest -q
```

## 说明

- `skills/aba_fetch/main.py` 当前是“页面状态检查骨架 v1”。
- 后续开发顺序可参考：`docs/next-step-plan.md`。
