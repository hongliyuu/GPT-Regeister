# -*- coding: utf-8 -*-
"""
本地资料生成器。

用于生成符合基础格式校验的 Visa 卡资料、姓名和账单地址。
卡号只满足 Visa 前缀与 Luhn 校验，不代表真实账户。
"""
import random
from datetime import datetime

FIRST_NAMES = [
    "James", "John", "Robert", "Michael", "William",
    "Mary", "Patricia", "Jennifer", "Linda", "Elizabeth",
    "David", "Richard", "Joseph", "Thomas", "Charles",
    "Barbara", "Susan", "Jessica", "Sarah", "Karen",
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones",
    "Garcia", "Miller", "Davis", "Rodriguez", "Martinez",
    "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
]

US_LOCATIONS = [
    {"state": "CA", "city": "Los Angeles", "postal_prefix": "900"},
    {"state": "CA", "city": "San Francisco", "postal_prefix": "941"},
    {"state": "NY", "city": "New York", "postal_prefix": "100"},
    {"state": "TX", "city": "Austin", "postal_prefix": "733"},
    {"state": "FL", "city": "Miami", "postal_prefix": "331"},
    {"state": "WA", "city": "Seattle", "postal_prefix": "981"},
    {"state": "IL", "city": "Chicago", "postal_prefix": "606"},
]

STREET_NAMES = [
    "Main", "Oak", "Pine", "Maple", "Cedar",
    "Sunset", "Washington", "Lake", "Hill", "Park",
]

STREET_SUFFIXES = ["St", "Ave", "Blvd", "Rd", "Dr", "Ln"]


def luhn_check_digit(number_without_check: str) -> str:
    """计算 Luhn 校验位。"""
    total = 0
    reversed_digits = number_without_check[::-1]

    for index, char in enumerate(reversed_digits):
        digit = int(char)
        if index % 2 == 0:
            digit *= 2
            if digit > 9:
                digit -= 9
        total += digit

    return str((10 - total % 10) % 10)


def generate_visa_number() -> str:
    """生成 16 位 Visa 格式卡号。"""
    body = "4" + "".join(str(random.randint(0, 9)) for _ in range(14))
    return body + luhn_check_digit(body)


def generate_expiry_parts(min_years: int = 1, max_years: int = 6) -> dict:
    """生成未来有效期，返回适配不同表单的拆分字段。"""
    now = datetime.now()
    month = random.randint(1, 12)
    year = random.randint(now.year + min_years, now.year + max_years)
    return {
        "month": f"{month:02d}",
        "year": str(year),
        "year_short": str(year)[-2:],
        "display": f"{month:02d}/{str(year)[-2:]}",
    }


def generate_cvv() -> str:
    """生成 Visa 常用的 3 位 CVV。"""
    return f"{random.randint(0, 999):03d}"


def generate_name() -> dict:
    """生成英文姓名。"""
    first = random.choice(FIRST_NAMES)
    last = random.choice(LAST_NAMES)
    return {
        "first_name": first,
        "last_name": last,
        "full_name": f"{first} {last}",
    }


def generate_us_address() -> dict:
    """生成美国账单地址格式资料。"""
    location = random.choice(US_LOCATIONS)
    street_number = random.randint(100, 9999)
    street_name = random.choice(STREET_NAMES)
    street_suffix = random.choice(STREET_SUFFIXES)
    postal_code = location["postal_prefix"] + f"{random.randint(0, 99):02d}"
    phone = f"+1 {random.randint(200, 999)} 555 {random.randint(0, 9999):04d}"
    return {
        "country": "US",
        "country_name": "United States",
        "state": location["state"],
        "city": location["city"],
        "street": f"{street_number} {street_name} {street_suffix}",
        "postal_code": postal_code,
        "phone": phone,
    }


def generate_visa_profile() -> dict:
    """生成完整 Visa 卡资料、持卡人姓名和账单地址。"""
    name = generate_name()
    expiry = generate_expiry_parts()
    address = generate_us_address()
    return {
        "card": {
            "brand": "Visa",
            "number": generate_visa_number(),
            "expiry": expiry["display"],
            "expiry_month": expiry["month"],
            "expiry_year": expiry["year"],
            "expiry_year_short": expiry["year_short"],
            "cvv": generate_cvv(),
        },
        "holder": name,
        "billing_address": address,
    }


if __name__ == "__main__":
    import json

    print(json.dumps(generate_visa_profile(), indent=2, ensure_ascii=False))
