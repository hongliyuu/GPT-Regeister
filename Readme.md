# GPT-Regeister 使用教程

本项目是一个基于 Python 的 ChatGPT / OpenAI 账号注册流程工具。程序入口为 `main.py`，支持 Outlook 邮箱账号池、自动收取邮箱 OTP、批量注册、并发注册、注册结果归档以及可选 2FA 设置。

## 目录

- [功能概览](#功能概览)
- [项目结构](#项目结构)
- [环境准备](#环境准备)
- [邮箱账号池配置](#邮箱账号池配置)
- [基础配置](#基础配置)
- [运行命令](#运行命令)
- [输出文件说明](#输出文件说明)
- [常见使用场景](#常见使用场景)
- [常见问题](#常见问题)
- [相关链接](#相关链接)

## 功能概览

- 自动执行 ChatGPT / OpenAI 注册流程
- 支持 Outlook 邮箱池自动领取邮箱
- 支持自动读取邮箱中的 6 位 OTP 验证码
- 支持单账号注册、批量注册和多线程并发注册
- 支持失败后继续执行后续任务
- 支持详细日志模式，便于排查问题
- 注册成功后自动保存邮箱、access token、账号 JSON 信息
- 可选注册后自动开启 2FA（TOTP）
- 每次运行会生成独立批次归档目录，方便复制和管理结果

## 项目结构

```text
GPT-Regeister/
├── main.py                    # CLI 入口，负责串联完整注册流程
├── requirements.txt           # Python 依赖列表
├── Readme.md                  # 使用说明文档
├── 用于注册的邮箱.txt          # Outlook 邮箱素材输入文件
├── 用于注册的邮箱.json         # Outlook 邮箱池状态文件，程序自动维护
├── config/                    # 配置目录
│   ├── register.py            # 注册默认信息：邮箱、名称、生日
│   ├── email.py               # Outlook 邮箱池和 OTP 轮询配置
│   ├── proxy.py               # 代理池配置
│   ├── twofa.py               # 2FA 开关
│   ├── browser.py             # 浏览器指纹和请求超时配置
│   └── openai_protocol.py     # OpenAI OAuth / Sentinel 固定参数
├── core/                      # 核心逻辑目录
│   ├── registration_service.py # 注册服务封装
│   ├── chatgpt_auth.py         # ChatGPT 认证前置流程
│   ├── openai_auth.py          # OpenAI Auth 注册流程
│   ├── outlook_client.py       # Outlook 邮箱池和 OTP 获取
│   ├── account_export.py       # 注册成功账号保存和批次归档
│   ├── db.py                   # 本地 JSON/TXT 数据持久化
│   ├── session.py              # HTTP 会话、代理、请求封装
│   └── flow_trigger.py         # 注册成功后的 flow 触发逻辑
└── sentinel/                  # Sentinel 相关脚本
    ├── sdk.js
    └── sentinel-runner.js
```

运行后可能新增以下文件或目录：

```text
accounts/                     # 每次运行的批次归档目录
注册成功的邮箱.json             # 注册成功账号完整状态，程序自动维护
注册成功的邮箱.txt              # 注册成功邮箱素材汇总
注册成功的token.txt             # 注册成功 access token 汇总
注册任务.json                   # 任务状态文件，程序自动维护
注册日志/                       # 日志目录，若相关功能触发会生成
```

## 环境准备

### 1. 安装 Python

建议使用 Python 3.10 或更高版本。

查看 Python 是否可用：

```powershell
python --version
```

### 2. 安装依赖

在项目根目录执行：

```powershell
pip install -r requirements.txt
```

当前依赖包括：

- `curl_cffi`：模拟浏览器请求
- `pyotp`：生成和处理 TOTP 2FA
- `flask`：保留给 Web / 服务入口相关能力

## 邮箱账号池配置

程序默认使用 Outlook 邮箱账号池，并自动读取 OTP 验证码。

### 1. 准备邮箱素材

编辑项目根目录下的 `用于注册的邮箱.txt`，每行放一个 Outlook 邮箱账号，格式如下：

```text
email----password----clientId----refreshToken
```

示例：

```text
example@outlook.com----邮箱密码----client-id----refresh-token
```

注意：

- 每行一个邮箱账号
- 分隔符必须是 `----`
- 程序运行前会自动把新增邮箱导入到 `用于注册的邮箱.json`
- 已使用、失败、可用等状态由程序自动维护

### 2. 获取 Refresh Token

可使用以下页面获取 Outlook 邮箱的 Refresh Token：

```text
https://ms-mail-api.arick.top/token.html
```

### 3. 查看 Outlook client_id

可在 Azure 门户查看应用的 client_id：

```text
https://portal.azure.com/#view/Microsoft_AAD_IAM/ActiveDirectoryMenuBlade/~/Overview
```

## 基础配置

### 注册信息配置

文件：`config/register.py`

常用配置：

```python
REGISTER_EMAIL = ""
REGISTER_NAME = ""
REGISTER_BIRTHDAY = "2000-01-01"
```

说明：

- `REGISTER_EMAIL` 留空时，程序会从 Outlook 邮箱池自动领取邮箱
- `REGISTER_NAME` 留空时，程序会自动生成英文显示名
- `REGISTER_BIRTHDAY` 默认为 `2000-01-01`，格式必须是 `YYYY-MM-DD`
- 批量注册时建议保持 `REGISTER_EMAIL = ""`，否则固定邮箱不适合批量任务

### 邮箱服务配置

文件：`config/email.py`

常用配置：

```python
USE_EMAIL_SERVICE = True
OUTLOOK_ACCOUNTS_FILE = "用于注册的邮箱.txt"
OUTLOOK_API_BASE = "https://mail.chatai.codes"
OTP_POLL_INTERVAL = 3
OTP_MAX_WAIT = 90
OTP_SETTLE_SECONDS = 5
```

说明：

- `USE_EMAIL_SERVICE = True`：自动从邮箱池领取邮箱，并自动收取 OTP
- `USE_EMAIL_SERVICE = False`：手动输入邮箱和验证码
- 多线程注册必须启用 `USE_EMAIL_SERVICE = True`

### 代理配置

文件：`config/proxy.py`

代理池配置在 `PROXY_POOL` 中：

```python
PROXY_POOL = [
    "socks5h://user:password@host:port",
]
```

说明：

- 代理池为空时，程序不使用代理
- 支持 `http://`、`https://`、`socks5://`、`socks5h://`
- 推荐使用 `socks5h://`，DNS 在代理端解析，能减少 DNS 与代理 IP 不一致的问题
- 并发注册时建议准备多个独立代理会话，降低关联风险

### 2FA 配置

文件：`config/twofa.py`

```python
ENABLE_2FA = False
```

说明：

- `False`：注册成功后只保存邮箱和 access token
- `True`：注册成功后自动设置 TOTP 2FA，并保存 `totp_secret`
- 开启 2FA 会额外触发一次邮箱 OTP 验证

## 运行命令

所有命令都在项目根目录执行。

### 单次注册

```powershell
python .\main.py
```

等价于：

```powershell
python .\main.py -n 1 --workers 1
```

### 单次测试并显示详细日志

首次运行或排查问题时推荐使用：

```powershell
python .\main.py -n 1 --workers 1 --continue-on-fail --verbose
```

### 批量串行注册

连续注册 10 个账号，每次只跑 1 个：

```powershell
python .\main.py -n 10 --workers 1 --continue-on-fail
```

### 批量并发注册

目标注册 10 个账号，同时开启 3 个线程：

```powershell
python .\main.py -n 10 --workers 3 --continue-on-fail
```

### 批量并发并显示详细日志

```powershell
python .\main.py -n 10 --workers 3 --continue-on-fail --verbose
```

### 设置任务间隔

串行模式下，每个账号结束后等待 5 秒再继续：

```powershell
python .\main.py -n 10 --workers 1 --delay 5 --continue-on-fail
```

并发模式下，`--delay` 表示提交任务之间的错峰间隔：

```powershell
python .\main.py -n 10 --workers 3 --delay 2 --continue-on-fail
```

## CLI 参数说明

| 参数 | 默认值 | 说明 |
| --- | --- | --- |
| `-n`, `--count` | `1` | 目标注册数量 |
| `--workers` | `1` | 并发线程数，`1` 表示串行 |
| `--delay` | `0` | 注册间隔秒数；并发模式下表示提交任务的错峰间隔 |
| `--continue-on-fail` | 关闭 | 单个账号失败后继续执行后续任务 |
| `--verbose` | 关闭 | 输出详细步骤日志和错误堆栈 |

## 输出文件说明

### 批次归档目录

每次运行都会在 `accounts/` 下创建一个批次目录，目录名类似：

```text
accounts/20260513-10个-3线程/
```

目录内包含：

| 文件 | 说明 |
| --- | --- |
| `注册成功的邮箱.txt` | 每行一个注册成功的邮箱素材 |
| `注册成功的token.txt` | 每行一个 access token |
| `注册成功整行.txt` | 邮箱素材 + token + 可选 TOTP secret，便于整行复制 |
| `注册成功账号.json` | 本批次完整账号信息，包括邮箱、token、代理、session 信息等 |

### 根目录状态文件

| 文件 | 说明 |
| --- | --- |
| `用于注册的邮箱.txt` | 邮箱素材输入文件 |
| `用于注册的邮箱.json` | 邮箱池状态文件，记录 available、used、failed 等状态 |
| `注册成功的邮箱.json` | 所有注册成功账号的完整状态汇总 |
| `注册成功的邮箱.txt` | 所有注册成功邮箱汇总 |
| `注册成功的token.txt` | 所有注册成功 token 汇总 |

## 常见使用场景

### 场景 1：第一次测试流程

1. 在 `用于注册的邮箱.txt` 中放入 1 个 Outlook 邮箱素材
2. 确认 `config/email.py` 中 `USE_EMAIL_SERVICE = True`
3. 确认 `config/register.py` 中 `REGISTER_EMAIL = ""`
4. 执行：

```powershell
python .\main.py -n 1 --workers 1 --continue-on-fail --verbose
```

5. 查看 `accounts/` 下最新批次目录中的结果文件

### 场景 2：批量注册 10 个账号

1. 在 `用于注册的邮箱.txt` 中准备至少 10 个可用邮箱素材
2. 根据需要在 `config/proxy.py` 中配置代理池
3. 执行：

```powershell
python .\main.py -n 10 --workers 3 --continue-on-fail
```

4. 注册完成后查看 `accounts/日期-10个-3线程/`

### 场景 3：手动输入邮箱和 OTP

1. 修改 `config/email.py`：

```python
USE_EMAIL_SERVICE = False
```

2. 执行单线程命令：

```powershell
python .\main.py -n 1 --workers 1 --verbose
```

3. 按终端提示输入邮箱、显示名和验证码

注意：手动模式不支持多线程注册。

### 场景 4：注册成功后开启 2FA

1. 修改 `config/twofa.py`：

```python
ENABLE_2FA = True
```

2. 确认邮箱账号池可以正常收取 OTP
3. 执行注册命令
4. 成功后在批次 JSON 或整行文件中查看 `totp_secret`

## 常见问题

### 1. 提示 Outlook 账号池没有可用账号

检查：

- `用于注册的邮箱.txt` 是否有新邮箱素材
- 每行格式是否为 `email----password----clientId----refreshToken`
- `用于注册的邮箱.json` 中邮箱状态是否都已经是 `used` 或 `failed`

处理方式：

- 追加新的邮箱素材到 `用于注册的邮箱.txt`
- 重新运行程序，程序会自动导入新增邮箱

### 2. 批量注册时报固定邮箱不适合批量

原因：`config/register.py` 中配置了固定的 `REGISTER_EMAIL`。

批量注册时请保持：

```python
REGISTER_EMAIL = ""
```

让程序从 Outlook 邮箱池自动领取邮箱。

### 3. 多线程注册时报需要启用 Outlook 自动取件

多线程模式不能人工输入验证码，因此需要：

```python
USE_EMAIL_SERVICE = True
```

如果必须手动输入验证码，请使用：

```powershell
python .\main.py -n 1 --workers 1
```

### 4. OTP 获取超时

可能原因：

- 邮箱素材不可用
- refresh token 失效
- 邮件服务接口异常
- OTP 邮件到达较慢

可尝试：

- 使用 `--verbose` 查看详细日志
- 检查邮箱素材和 refresh token
- 适当增大 `config/email.py` 中的 `OTP_MAX_WAIT`

### 5. 代理相关错误

可检查：

- 代理 URL 格式是否正确
- 代理账号密码是否有效
- 代理协议是否与服务商一致
- 并发时是否多个线程共用同一个代理会话

推荐优先使用：

```text
socks5h://user:password@host:port
```

## 推荐运行顺序

首次使用建议按下面顺序执行：

```powershell
pip install -r requirements.txt
python .\main.py -n 1 --workers 1 --continue-on-fail --verbose
python .\main.py -n 10 --workers 3 --continue-on-fail
```

先用单账号详细日志确认邮箱、OTP、代理和注册流程都正常，再进行批量并发。

## 相关链接

- 获取 Outlook Refresh Token：`https://ms-mail-api.arick.top/token.html`
- 查看 Outlook client_id：`https://portal.azure.com/#view/Microsoft_AAD_IAM/ActiveDirectoryMenuBlade/~/Overview`
