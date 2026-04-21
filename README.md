# openclaw-skills

这是一个用于 **OpenClaw skills 开发** 的 Python 项目骨架（稳定化第一版）。

## 当前项目进展说明

当前已提供一个“**可运行的流程演示版本**”，入口为 `skills/aba_fetch/main.py`。

这个演示版本的目标是：
- 让 0 代码基础同学也能直接运行并看懂主流程。
- 明确展示“人工登录后抓 ABA”的低风险方案。
- 用 5 个步骤串起完整链路（确认登录 → 确认页面 → 模拟导出 → 模拟解析 → 模拟写入飞书）。

## 当前版本不能做什么

当前版本**不能**：
- 真实抓取 ABA 数据。
- 自动控制浏览器（不做浏览器自动化）。
- 自动登录 Amazon（不处理账号密码、验证码）。
- 调用真实飞书接口写入数据。
- 处理真实导出文件内容与异常场景。

换句话说：现在是“流程演示版”，不是“生产可用版”。

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

为了在 Windows PowerShell 下获得更稳定的输出与测试结果，当前演示脚本已避免使用容易触发编码问题的 emoji 等特殊字符。默认情况下可直接运行：

```powershell
python -m skills.aba_fetch.main
pytest -q
```

如果你的终端环境仍出现中文乱码或编码异常，可临时启用 UTF-8 模式后再运行：

```powershell
$env:PYTHONUTF8="1"
python -m skills.aba_fetch.main
pytest -q
```

## 说明

- `skills/aba_fetch/main.py` 当前是“第一版可运行演示优化”。
- 后续开发顺序可参考：`docs/next-step-plan.md`。
