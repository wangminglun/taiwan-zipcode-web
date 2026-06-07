#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
台灣郵遞區號小幫手
使用 zip5.5432.tw API 查詢 6 碼（3+3）郵遞區號
用法：
    python zipcode.py                      # 互動模式
    python zipcode.py 台北市信義區信義路五段7號  # 單次查詢
    python zipcode.py -f addresses.txt     # 批次查詢
"""

import sys
import time
import json
import argparse
import urllib.request
import urllib.parse

from address_en import address_to_english


API_URL = "https://zip5.5432.tw/zip5json.py"


def query_zipcode(address: str) -> dict:
    """
    呼叫 zip5.5432.tw API 查詢郵遞區號
    回傳 dict，包含 zipcode5（5碼）與 zipcode6（6碼）
    """
    encoded = urllib.parse.quote(address)
    url = f"{API_URL}?adrs={encoded}"

    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (zipcode-helper/1.0)"}
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            raw = resp.read().decode("utf-8")
            data = json.loads(raw)
            return data
    except urllib.error.URLError as e:
        raise ConnectionError(f"網路錯誤：{e.reason}") from e
    except json.JSONDecodeError as e:
        raise ValueError(f"API 回傳格式錯誤：{e}") from e


def parse_result(address: str, data: dict) -> dict:
    """
    解析 API 結果，優先回傳 6 碼（3+3），次之 5 碼（3+2）
    """
    zip6 = data.get("zipcode6", "").strip()
    zip5 = data.get("zipcode", "").strip()
    matched_addr = data.get("new_adrs6", data.get("new_adrs", "")).strip()

    # 移除地址前面夾帶的郵遞區號（須先確認 zip6/zip5 非空，避免空字串永遠符合 startswith）
    if matched_addr and zip6 and matched_addr.startswith(zip6):
        matched_addr = matched_addr[len(zip6):].strip()
    elif matched_addr and zip5 and matched_addr.startswith(zip5):
        matched_addr = matched_addr[len(zip5):].strip()

    return {
        "input": address,
        "zipcode6": zip6,
        "zipcode5": zip5,
        "matched_address": matched_addr,
    }


def format_output(result: dict, verbose: bool = False) -> str:
    """格式化輸出"""
    z6 = result["zipcode6"]
    z5 = result["zipcode5"]
    addr = result["input"]

    if z6:
        zipcode = z6
        label = "6碼（3+3）"
    elif z5:
        zipcode = z5
        label = "5碼（3+2）"
    else:
        return f"❌  查無結果：{addr}"

    lines = [f"📮  郵遞區號：{zipcode}  ({label})"]
    if verbose:
        lines.append(f"📍  輸入地址：{addr}")
        if result["matched_address"]:
            lines.append(f"✅  比對地址：{result['matched_address']}")
        # 英文地址書寫順序由小範圍到大範圍（號碼 → 路 → 區 → 市），與中文順序相反
        english = address_to_english(result["matched_address"] or addr)
        if english:
            lines.append(f"🌐  英文地址：{english}")
    return "\n".join(lines)


def interactive_mode():
    """互動模式：持續查詢直到使用者輸入 q"""
    print("=" * 50)
    print("  台灣郵遞區號小幫手（輸入 q 離開）")
    print("  資料來源：https://zip5.5432.tw")
    print("=" * 50)

    while True:
        try:
            address = input("\n請輸入地址：").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n👋  掰掰！")
            break

        if not address:
            continue
        if address.lower() in ("q", "quit", "exit", "離開"):
            print("👋  掰掰！")
            break

        try:
            data = query_zipcode(address)
            result = parse_result(address, data)
            print(format_output(result, verbose=True))
        except (ConnectionError, ValueError) as e:
            print(f"⚠️  查詢失敗：{e}")


def batch_mode(filepath: str):
    """批次模式：從檔案逐行讀取地址並查詢"""
    try:
        with open(filepath, encoding="utf-8") as f:
            addresses = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"❌  找不到檔案：{filepath}")
        sys.exit(1)

    print(f"共 {len(addresses)} 筆地址，開始查詢...\n")

    for i, address in enumerate(addresses, 1):
        try:
            data = query_zipcode(address)
            result = parse_result(address, data)
            zipcode = result["zipcode6"] or result["zipcode5"] or "查無結果"
            print(f"{i:>4}. {zipcode}  {address}")
        except (ConnectionError, ValueError) as e:
            print(f"{i:>4}. ❌ 查詢失敗  {address}  ({e})")

        # 每次查詢間隔 2 秒，遵守 API 使用規範
        if i < len(addresses):
            time.sleep(2)

    print("\n✅  批次查詢完成")


def single_mode(address: str):
    """單次查詢模式"""
    try:
        data = query_zipcode(address)
        result = parse_result(address, data)
        print(format_output(result, verbose=True))
    except (ConnectionError, ValueError) as e:
        print(f"⚠️  查詢失敗：{e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="台灣郵遞區號查詢小幫手（使用 zip5.5432.tw API）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
範例：
  python zipcode.py                          # 互動模式
  python zipcode.py 台北市信義區信義路五段7號    # 單次查詢
  python zipcode.py -f addresses.txt         # 批次查詢
        """
    )
    parser.add_argument(
        "address",
        nargs="?",
        help="要查詢的地址（省略則進入互動模式）"
    )
    parser.add_argument(
        "-f", "--file",
        metavar="FILE",
        help="批次查詢：從文字檔讀取地址（每行一筆）"
    )

    args = parser.parse_args()

    if args.file:
        batch_mode(args.file)
    elif args.address:
        single_mode(args.address)
    else:
        interactive_mode()


if __name__ == "__main__":
    main()

