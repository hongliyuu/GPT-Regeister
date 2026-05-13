# -*- coding: utf-8 -*-
"""
代理池配置

每次注册随机抽取一个代理，保证不同 sid 之间彼此独立，避免风控关联。

协议说明：
    - http:// / https://   HTTP(S) 代理
    - socks5://            SOCKS5（DNS 本地解析，可能泄漏）
    - socks5h://           SOCKS5（DNS 在代理端解析，推荐，避免 DNS-IP 错配）
"""
import random


# Cliproxy 新加坡节点。未带 sid 的地址由服务端自行轮换，带 sid 的地址用于并发时分散会话。
# 统一用 socks5h://（DNS 在代理端解析），避免本地 DNS 错配导致 TLS WRONG_VERSION_NUMBER。
PROXY_POOL = [
    "http://qcfvn17921-region-US-sid-BtvQrhNf-t-5:ujgdlt5p@us.lajiaohttp.net:2000",
    "http://qcfvn17921-region-US-sid-nwA5sPzj-t-5:ujgdlt5p@us.lajiaohttp.net:2000",
    "http://qcfvn17921-region-US-sid-zRmcM5JD-t-5:ujgdlt5p@us.lajiaohttp.net:2000",
    "http://qcfvn17921-region-US-sid-5nC7cSWw-t-5:ujgdlt5p@us.lajiaohttp.net:2000",
    "http://qcfvn17921-region-US-sid-bZ9nCKj2-t-5:ujgdlt5p@us.lajiaohttp.net:2000",
    "http://qcfvn17921-region-US-sid-3VbzuVJN-t-5:ujgdlt5p@us.lajiaohttp.net:2000",
    "http://qcfvn17921-region-US-sid-UjhLMLsq-t-5:ujgdlt5p@us.lajiaohttp.net:2000",
    "http://qcfvn17921-region-US-sid-ZxZVXkGB-t-5:ujgdlt5p@us.lajiaohttp.net:2000",
    "http://qcfvn17921-region-US-sid-5q3mvEgz-t-5:ujgdlt5p@us.lajiaohttp.net:2000",
    "http://qcfvn17921-region-US-sid-9vYYGjYX-t-5:ujgdlt5p@us.lajiaohttp.net:2000",
    "http://qcfvn17921-region-US-sid-eBKapB5b-t-5:ujgdlt5p@us.lajiaohttp.net:2000",
    "http://qcfvn17921-region-US-sid-2Fuxy7aN-t-5:ujgdlt5p@us.lajiaohttp.net:2000",
    "http://qcfvn17921-region-US-sid-RBLvna5s-t-5:ujgdlt5p@us.lajiaohttp.net:2000",
    "http://qcfvn17921-region-US-sid-8fRmMmw1-t-5:ujgdlt5p@us.lajiaohttp.net:2000",
    "http://qcfvn17921-region-US-sid-3ww65Gfx-t-5:ujgdlt5p@us.lajiaohttp.net:2000",
    "http://qcfvn17921-region-US-sid-xg12Vs8n-t-5:ujgdlt5p@us.lajiaohttp.net:2000",
    "http://qcfvn17921-region-US-sid-Cq19XJPF-t-5:ujgdlt5p@us.lajiaohttp.net:2000",
    "http://qcfvn17921-region-US-sid-1B2WLpvX-t-5:ujgdlt5p@us.lajiaohttp.net:2000",
    "http://qcfvn17921-region-US-sid-iVbMtMFu-t-5:ujgdlt5p@us.lajiaohttp.net:2000",
    "http://qcfvn17921-region-US-sid-NUi1t5X6-t-5:ujgdlt5p@us.lajiaohttp.net:2000",
]


def pick_proxy() -> str:
    """从代理池中随机抽取一个代理 URL；池为空时返回空串（即不使用代理）。"""
    return random.choice(PROXY_POOL) if PROXY_POOL else ""


# 兼容入口：默认每次进程启动随机选一个，作为本次注册全程的固定代理
PROXY = pick_proxy()
