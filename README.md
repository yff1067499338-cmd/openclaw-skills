# openclaw-skills

这是一个用于 **OpenClaw skills 开发** 的私有自动化项目骨架，面向以下场景：

- 本地自动化脚本开发与调试
- OpenClaw Skill 的模块化组织与扩展
- 飞书（Feishu/Lark）相关接口与数据表集成

## 项目目标

- 保持目录清晰、可维护，便于后续持续扩展
- 使用轻量依赖快速启动 PoC 与内部自动化任务
- 为后续接入真实业务逻辑预留文档、配置与测试结构

## 当前目录结构

```text
openclaw-skills/
  README.md
  requirements.txt
  .env.example
  skills/
    aba_fetch/
      README.md
      config.example.json
      main.py
    common/
      utils.py
  docs/
    skill-spec.md
    feishu-fields.md
  tests/
    test_demo.py
```

## 快速开始

1. 创建并激活虚拟环境（可选）
2. 安装依赖：

```bash
pip install -r requirements.txt
```

3. 复制环境变量模板并填写：

```bash
cp .env.example .env
```

4. 运行占位 Skill：

```bash
python skills/aba_fetch/main.py
```
