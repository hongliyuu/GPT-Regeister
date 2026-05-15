# GPT-Regeister

ChatGPT / OpenAI 账号注册工具，支持 GUI 配置、IMAP / Outlook OAuth 自动取邮箱验证码、批量注册、注册结果归档和可选 2FA。

## 快速开始

```powershell
pip install -r requirements.txt
python .\run_gui.py
```

推荐通过 GUI 修改配置。保存后会写入项目根目录的 `config.yaml`，CLI 也读取同一个配置文件。

## 运行命令

```powershell
python .\main.py -n 1 --workers 1 --continue-on-fail --verbose
python .\main.py -n 10 --workers 3 --continue-on-fail
```

参数：

| 参数 | 说明 |
| --- | --- |
| `-n`, `--count` | 注册数量 |
| `--workers` | 并发线程数，手动模式只能为 1 |
| `--delay` | 任务提交/注册间隔秒数 |
| `--continue-on-fail` | 单个账号失败后继续 |
| `--verbose` | 输出详细日志 |

## 打包 EXE

项目提供 Windows 打包脚本：

```powershell
.\build_exe.ps1
```

脚本会自动完成：

- 检查 `gui/openai.ico` 是否存在
- 安装缺失的 `pyinstaller`
- 清理旧的 `build/`、`dist/` 和 `GPT-Regeister.spec`
- 使用 GUI 入口 `run_gui.py` 打包
- 将依赖和资源放在 exe 同级根目录，不生成 `_internal`
- 生成文件夹和 zip 压缩包

打包产物：

```text
dist/GPT-Regeister/GPT-Regeister.exe
dist/GPT-Regeister.zip
```

打包后的目录结构会类似：

```text
dist/GPT-Regeister/
├─ GPT-Regeister.exe
├─ gui/
│  └─ openai.ico
├─ sentinel/
├─ node/
├─ PySide6/
├─ python*.dll
└─ 其他运行依赖
```

`config.yaml`、`accounts_viewer.html`、账号数据库和归档文件由程序运行时自动生成，不随安装包内置。

如需手动执行打包命令：

```powershell
pyinstaller `
  --noconfirm `
  --clean `
  --windowed `
  --name GPT-Regeister `
  --contents-directory . `
  --icon gui\openai.ico `
  --add-data "gui\openai.ico;gui" `
  --add-data "sentinel;sentinel" `
  --add-data "node;node" `
  run_gui.py
```

## 核心配置

### 注册信息

```yaml
register:
  email: ''
  name: ''
  birthday: '2000-01-01'
  runs: 1
```

- `email` 留空时，从邮箱账号池自动领取邮箱
- `name` 留空时，自动生成英文显示名
- 批量注册时建议保持 `email` 为空

### IMAP 邮箱

```yaml
email:
  provider: imap
  imap:
    login_email: user@example.com
    login_password: password
    host: imap.example.com
    port: 993
    ssl: true
    mailbox: INBOX
    alias_mode: full_random
    alias_domain_mode: default
    alias_domain: ''
    alias_random_length: 6
    alias_separator: ''
```

多邮箱账号池：

```yaml
email:
  provider: imap
  imap:
    accounts:
      - email: user1@example.com
        password: password1
        host: imap.example.com
        port: 993
        ssl: true
      - email: user2@example.com
        password: password2
        host: imap.example.com
        port: 993
        ssl: true
```

### Outlook OAuth 邮箱

```yaml
email:
  provider: outlook_oauth
  outlook:
    api_base: https://mail.chatai.codes
    accounts:
      - email: example@outlook.com
        password: password
        client_id: client-id
        refresh_token: refresh-token
```

### 手动模式

```yaml
email:
  provider: manual
register:
  email: example@example.com
  name: Example User
```

手动模式需要在注册过程中输入邮箱验证码，不支持多线程注册。

### OTP

```yaml
email:
  otp:
    poll_interval: 3
    max_wait: 90
    settle_seconds: 5
```

### 代理

```yaml
proxy:
  pool:
    - http://user:password@host:port
```

### 2FA

```yaml
twofa:
  enabled: false
```

## 输出文件

| 路径 | 说明 |
| --- | --- |
| `accounts/` | 每次运行生成的批次归档目录 |
| `用于注册的邮箱.json` | Outlook 账号池状态 |
| `注册成功的邮箱.json` | 成功账号汇总 |
| `注册成功的邮箱.txt` | 成功邮箱汇总 |
| `注册成功的token.txt` | access token 汇总 |

## 常见问题

### 没有可用账号

检查：

- `email.provider` 是否正确
- `email.imap.login_email` / `email.imap.login_password` 是否填写
- `email.imap.accounts` 或 `email.outlook.accounts` 是否有账号

### OTP 超时

检查邮箱配置、refresh token、IMAP 服务和代理；必要时增大：

```yaml
email:
  otp:
    max_wait: 180
```

### 多线程报错

多线程不能使用 `manual`，请改用：

```yaml
email:
  provider: imap
```

或：

```yaml
email:
  provider: outlook_oauth
```
