# openclaw-skills

这是一个用于 **OpenClaw skills 开发** 的 Python 项目骨架（稳定化第一版）。

## 当前阶段目标

- 提供干净、可持续迭代的目录结构
- 保持最小可运行入口，便于快速验证环境
- 不引入真实业务抓取逻辑或浏览器自动化

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
  tests/
    test_demo.py
```

## 快速开始

1. （可选）创建并激活虚拟环境
2. 安装依赖：

```bash
pip install -r requirements.txt
```

3. 运行最小入口：

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

## 说明

- `skills/aba_fetch/main.py` 当前只保留最小可运行占位逻辑。
- 当前版本不包含：
  - 真实 ABA 抓取实现
  - 浏览器自动化
  - 飞书写入逻辑
