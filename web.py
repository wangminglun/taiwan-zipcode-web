#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
台灣郵遞區號小幫手 - 網頁版（本機伺服器）
重用 main.py 的查詢邏輯，提供網頁介面，方便用瀏覽器（含手機）使用、分享連結。

用法：
    uv run web.py
然後在瀏覽器開啟 http://127.0.0.1:5000
"""

import os

from flask import Flask, jsonify, render_template_string, request

from address_en import address_to_english
from main import query_zipcode, parse_result

app = Flask(__name__)

PAGE = """
<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>台灣郵遞區號小幫手</title>
<meta property="og:title" content="台灣郵遞區號查詢小幫手 📮" />
<meta property="og:description" content="輸入地址秒查 6 碼郵遞區號！簡單、快速、沒廣告，快點進來試試看吧！" />
<meta property="og:image" content="{{ og_image }}" />
<meta property="og:url" content="{{ og_url }}" />
<meta property="og:type" content="website" />
<style>
  :root {
    --primary: #2563eb;
    --primary-dark: #1d4ed8;
    --ink: #1e293b;
    --muted: #64748b;
    --border: #e2e8f0;
    --bg-card: #ffffff;
  }
  * { box-sizing: border-box; }
  body {
    font-family: "Microsoft JhengHei", "Segoe UI", sans-serif;
    margin: 0;
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 24px;
    background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 50%, #ede9fe 100%);
    color: var(--ink);
  }
  .card {
    width: 100%;
    max-width: 480px;
    background: var(--bg-card);
    border-radius: 16px;
    box-shadow: 0 10px 40px rgba(30, 41, 59, 0.12);
    padding: 32px;
  }
  h1 {
    font-size: 1.5em;
    margin: 0 0 4px;
    text-align: center;
  }
  .subtitle {
    text-align: center;
    color: var(--muted);
    font-size: 0.85em;
    margin: 0 0 24px;
  }
  .search-row {
    display: flex;
    gap: 8px;
  }
  #address {
    flex: 1;
    min-width: 0;
    padding: 12px 14px;
    font-size: 1em;
    border: 1px solid var(--border);
    border-radius: 10px;
    outline: none;
    transition: border-color 0.15s, box-shadow 0.15s;
  }
  #address:focus {
    border-color: var(--primary);
    box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.15);
  }
  button {
    padding: 12px 22px;
    font-size: 1em;
    font-weight: 600;
    color: #fff;
    background: var(--primary);
    border: none;
    border-radius: 10px;
    cursor: pointer;
    transition: background 0.15s, transform 0.05s;
    white-space: nowrap;
  }
  button:hover { background: var(--primary-dark); }
  button:active { transform: scale(0.97); }
  button:disabled { background: #93c5fd; cursor: default; }

  #result { margin-top: 20px; min-height: 1px; }
  .placeholder { color: var(--muted); font-size: 0.9em; text-align: center; padding: 12px 0; }
  .spinner {
    display: inline-block;
    width: 16px;
    height: 16px;
    border: 2px solid var(--border);
    border-top-color: var(--primary);
    border-radius: 50%;
    animation: spin 0.7s linear infinite;
    vertical-align: -3px;
    margin-right: 8px;
  }
  @keyframes spin { to { transform: rotate(360deg); } }

  .error-box {
    background: #fef2f2;
    border: 1px solid #fecaca;
    color: #b91c1c;
    border-radius: 10px;
    padding: 14px 16px;
    font-size: 0.9em;
    line-height: 1.6;
  }
  .result-list {
    display: flex;
    flex-direction: column;
    gap: 10px;
  }
  .result-item {
    display: flex;
    align-items: flex-start;
    gap: 12px;
    background: #f8fafc;
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 12px 14px;
  }
  .result-icon { font-size: 1.3em; line-height: 1.4; }
  .result-text { line-height: 1.4; }
  .result-label { font-size: 0.78em; color: var(--muted); margin-bottom: 2px; }
  .result-value { font-size: 1.05em; word-break: break-word; }
  .zipcode .result-value { font-weight: 700; color: var(--primary-dark); letter-spacing: 0.05em; }
</style>
</head>
<body>
  <div class="card">
    <h1>📮 台灣郵遞區號小幫手</h1>
    <p class="subtitle">輸入台灣地址，立即查詢 6 碼郵遞區號與英文地址</p>
    <div class="search-row">
      <input id="address" placeholder="例如：台北市信義區市府路1號" autocomplete="off">
      <button id="search-btn" onclick="lookup()">查詢</button>
    </div>
    <div id="result">
      <p class="placeholder">請輸入地址並按 Enter 或點擊查詢</p>
    </div>
  </div>

<script>
const resultEl = document.getElementById('result');
const addressEl = document.getElementById('address');
const btnEl = document.getElementById('search-btn');

function renderPlaceholder(text) {
  resultEl.innerHTML = '';
  const p = document.createElement('p');
  p.className = 'placeholder';
  p.textContent = text;
  resultEl.appendChild(p);
}

function renderLoading() {
  resultEl.innerHTML = '';
  const p = document.createElement('p');
  p.className = 'placeholder';
  const spin = document.createElement('span');
  spin.className = 'spinner';
  p.appendChild(spin);
  p.appendChild(document.createTextNode('查詢中...'));
  resultEl.appendChild(p);
}

function renderError(message) {
  resultEl.innerHTML = '';
  const box = document.createElement('div');
  box.className = 'error-box';
  box.textContent = '⚠️ ' + message;
  resultEl.appendChild(box);
}

function addResultItem(list, icon, extraClass, label, value) {
  const item = document.createElement('div');
  item.className = 'result-item' + (extraClass ? ' ' + extraClass : '');
  const iconEl = document.createElement('div');
  iconEl.className = 'result-icon';
  iconEl.textContent = icon;
  const textEl = document.createElement('div');
  textEl.className = 'result-text';
  const labelEl = document.createElement('div');
  labelEl.className = 'result-label';
  labelEl.textContent = label;
  const valueEl = document.createElement('div');
  valueEl.className = 'result-value';
  valueEl.textContent = value;
  textEl.appendChild(labelEl);
  textEl.appendChild(valueEl);
  item.appendChild(iconEl);
  item.appendChild(textEl);
  list.appendChild(item);
}

function renderResult(data) {
  resultEl.innerHTML = '';
  const list = document.createElement('div');
  list.className = 'result-list';
  addResultItem(list, '📮', 'zipcode', '郵遞區號', data.zipcode);
  if (data.matched_address) addResultItem(list, '✅', '', '比對地址', data.matched_address);
  if (data.english_address) addResultItem(list, '🌐', '', '英文地址', data.english_address);
  resultEl.appendChild(list);
}

async function lookup() {
  const address = addressEl.value.trim();
  if (!address) return;
  btnEl.disabled = true;
  renderLoading();
  try {
    const res = await fetch('/api/lookup?address=' + encodeURIComponent(address));
    const data = await res.json();
    if (data.error) {
      renderError(data.error);
    } else {
      renderResult(data);
    }
  } catch (e) {
    renderError('查詢失敗，請稍後再試');
  } finally {
    btnEl.disabled = false;
  }
}

addressEl.addEventListener('keydown', function (e) {
  if (e.key === 'Enter') lookup();
});
addressEl.addEventListener('input', function () {
  if (!addressEl.value.trim()) renderPlaceholder('請輸入地址並按 Enter 或點擊查詢');
});
addressEl.focus();
</script>
</body>
</html>
"""


@app.route("/")
def index():
    # og:image / og:url 需要是完整網址，依目前請求的網域動態組成，
    # 這樣本機（127.0.0.1）與部署後的正式網域都能正確顯示分享預覽。
    og_url = request.host_url.rstrip("/") + "/"
    og_image = request.host_url.rstrip("/") + "/static/preview.png"
    return render_template_string(PAGE, og_url=og_url, og_image=og_image)


@app.route("/api/lookup")
def api_lookup():
    address = request.args.get("address", "").strip()
    if not address:
        return jsonify({"error": "請提供地址"}), 400

    try:
        data = query_zipcode(address)
        result = parse_result(address, data)
    except (ConnectionError, ValueError) as e:
        return jsonify({"error": str(e)}), 502

    zipcode = result["zipcode6"] or result["zipcode5"]
    if not zipcode:
        return jsonify({"error": f"查無結果：{address}"}), 404

    # 英文地址書寫順序由小範圍到大範圍（號碼 → 路 → 區 → 市），與中文順序相反
    english_address = address_to_english(result["matched_address"] or address)

    return jsonify({
        "zipcode": zipcode,
        "matched_address": result["matched_address"],
        "english_address": english_address,
    })


def main():
    # Render（及多數雲端平台）會透過 PORT 環境變數指定對外埠號，
    # 並要求綁定 0.0.0.0 才能對外服務；本機開發則維持 127.0.0.1:5000。
    port = int(os.environ.get("PORT", 5000))
    host = "0.0.0.0" if "PORT" in os.environ else "127.0.0.1"
    app.run(host=host, port=port, debug=False)


if __name__ == "__main__":
    main()
