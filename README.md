# openclaw-skills

这是一个用于 **OpenClaw skills 开发** 的 Python 项目骨架。

当前主线：**人工登录后抓 ABA 的低风险本地工具**。

## 当前版本新增的真实能力（v2）

入口：`skills/aba_fetch/main.py`

本版本新增了一个最小可执行的真实动作：
- 尝试连接本地浏览器调试端口（CDP）
- 尝试读取当前页面信息（标题 / URL）
- 将真实读取结果打印到终端

> 仍坚持低风险约束：
> - 不自动登录
> - 不处理账号密码
> - 不处理验证码
> - 不做真实 ABA 抓取
> - 不接飞书

## 功能边界

### 已实现
- 真实检查本机是否存在 Chrome / Edge 进程。
- 真实连接浏览器调试端点（`/json/list`）。
- 从页面目标里读取并打印 `title` 与 `url`。

### 尚未实现
- 自动点击 ABA 导出。
- 读取真实导出文件并结构化解析。
- 飞书写入。

## 运行前准备（Windows）

### 1) 手动启动浏览器并打开你要读取的页面

请**手动登录**到目标网站（如 Amazon），并停留在你想读取的页面。

### 2) 使用调试端口启动浏览器（关键）

请关闭已打开的 Chrome / Edge 后，使用 PowerShell 启动一个带调试端口的实例。

#### Chrome 示例

```powershell
& "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="C:\tmp\chrome-cdp-profile"
```

#### Edge 示例

```powershell
& "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" --remote-debugging-port=9222 --user-data-dir="C:\tmp\edge-cdp-profile"
```

> 说明：`--user-data-dir` 用于隔离调试实例的用户数据，减少与日常浏览器会话冲突。

## 在 Windows PowerShell 下执行

### 1) 安装依赖

```powershell
pip install -r requirements.txt
```

### 2) 运行演示脚本

```powershell
python -m skills.aba_fetch.main
```

### 3) 运行测试

```powershell
pytest -q
```

## 运行结果解读

- 若看到 `PAGE_INFO_READ_OK`，说明已真实读取到页面信息。
- 若看到 `PAGE_INFO_READ_FAILED`，通常是浏览器没有用调试端口启动，或端口被占用。

## 目录结构

```text
openclaw-skills/
  README.md
  pyproject.toml
  requirements.txt
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
