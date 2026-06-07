#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
台灣地址轉英文地址（書寫順序：由小範圍到大範圍 —— 門牌、巷弄、路、區、市，與中文順序相反）
供 main.py（終端機版）與 gui.py（桌面版）共用。
"""

import re

from pypinyin import Style, pinyin

# 全形數字轉半形（部分地址資料庫回傳的門牌、段號等使用全形數字，如「３段」）
_FULLWIDTH_DIGITS = str.maketrans("０１２３４５６７８９", "0123456789")

# 中華郵政慣用的縣市英文名稱
_CITY_EN = {
    "臺北市": "Taipei City", "台北市": "Taipei City",
    "新北市": "New Taipei City",
    "桃園市": "Taoyuan City",
    "臺中市": "Taichung City", "台中市": "Taichung City",
    "臺南市": "Tainan City", "台南市": "Tainan City",
    "高雄市": "Kaohsiung City",
    "基隆市": "Keelung City",
    "新竹市": "Hsinchu City",
    "嘉義市": "Chiayi City",
    "新竹縣": "Hsinchu County",
    "苗栗縣": "Miaoli County",
    "彰化縣": "Changhua County",
    "南投縣": "Nantou County",
    "雲林縣": "Yunlin County",
    "嘉義縣": "Chiayi County",
    "屏東縣": "Pingtung County",
    "宜蘭縣": "Yilan County",
    "花蓮縣": "Hualien County",
    "臺東縣": "Taitung County", "台東縣": "Taitung County",
    "澎湖縣": "Penghu County",
    "金門縣": "Kinmen County",
    "連江縣": "Lienchiang County",
}

_ROAD_SUFFIX_EN = {
    "大道": "Boulevard",
    "路": "Road",
    "街": "Street",
}

_SECTION_NUMERALS = {
    "一": "1", "二": "2", "三": "3", "四": "4", "五": "5", "六": "6",
    "七": "7", "八": "8", "九": "9", "十": "10", "十一": "11", "十二": "12",
}

_ADDRESS_RE = re.compile(
    r"^(?P<city>\D+?[市縣])"
    r"(?P<district>\D+?[區鄉鎮市])"
    r"(?P<road>\D+?(?:大道|路|街))"
    r"(?:(?P<section>[一二三四五六七八九十]+|\d+)段)?"
    r"(?:(?P<lane>\d+)巷)?"
    r"(?:(?P<alley>\d+)弄)?"
    r"(?:(?P<number>\d+)號(?:之(?P<number_sub>\d+))?)?"
    r"(?:(?P<floor>\d+)樓(?:之(?P<floor_sub>\d+))?)?"
)


def _name_to_pinyin(name: str) -> str:
    """將中文名稱轉換為不帶聲調、字首大寫且不分隔音節的拼音（如「信義」→「Xinyi」）。"""
    syllables = "".join(s[0] for s in pinyin(name, style=Style.NORMAL))
    return syllables.capitalize()


def address_to_english(address: str) -> str | None:
    """將台灣地址轉換為英文書寫順序的地址：號碼 → 巷弄/段 → 路 → 區 → 市
    （由小範圍到大範圍，與中文「市區路號」由大到小的順序相反）。

    區、路（含路名、大道）採用拼音音譯，縣市則對應中華郵政慣用英文名稱。
    僅在能辨識出縣市／鄉鎮市區／路街名稱時才回傳結果，否則回傳 None。
    """
    normalized = address.replace("台", "臺").translate(_FULLWIDTH_DIGITS)
    m = _ADDRESS_RE.match(normalized)
    if not m:
        return None

    city_en = _CITY_EN.get(m.group("city"))
    if not city_en:
        return None

    district_zh = m.group("district")
    district_en = f"{_name_to_pinyin(district_zh[:-1])} District"

    road_zh = m.group("road")
    road_suffix_zh = road_zh[-2:] if road_zh.endswith("大道") else road_zh[-1]
    road_suffix_en = _ROAD_SUFFIX_EN[road_suffix_zh]
    road_en = f"{_name_to_pinyin(road_zh[:-len(road_suffix_zh)])} {road_suffix_en}"

    # 由小到大依序組成英文地址（門牌、巷弄、路段在前，行政區、縣市在後）
    parts: list[str] = []

    floor = m.group("floor")
    if floor:
        floor_en = f"{floor}F"
        if m.group("floor_sub"):
            floor_en += f"-{m.group('floor_sub')}"
        parts.append(floor_en)

    number = m.group("number")
    if number:
        number_en = f"No. {number}"
        if m.group("number_sub"):
            number_en += f"-{m.group('number_sub')}"
        parts.append(number_en)

    if m.group("alley"):
        parts.append(f"Aly. {m.group('alley')}")

    if m.group("lane"):
        parts.append(f"Ln. {m.group('lane')}")

    section = m.group("section")
    if section:
        parts.append(f"Sec. {_SECTION_NUMERALS.get(section, section)}")

    parts.append(road_en)
    parts.append(district_en)
    parts.append(city_en)

    return ", ".join(parts)
