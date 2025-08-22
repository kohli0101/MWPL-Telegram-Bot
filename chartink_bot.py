import requests, json, os
from datetime import datetime, timedelta

# ============= CONFIG =============
SCREENER_URL = "https://chartink.com/screener/process"
SCREENER_PAYLOAD = {"scan_clause": "(paste_your_screener_scan_here)"}
BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
RESULTS_FILE = "results.json"
# ==================================

def ist_now():
    return datetime.utcnow() + timedelta(hours=5, minutes=30)

def load_results():
    if os.path.exists(RESULTS_FILE):
        with open(RESULTS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_results(data):
    with open(RESULTS_FILE, "w") as f:
        json.dump(data, f, indent=2)

def fetch_stocks():
    # Get CSRF token
    session = requests.Session()
    home = session.get("https://chartink.com")
    csrf = session.cookies.get("XSRF-TOKEN")

    headers = {
        "X-Requested-With": "XMLHttpRequest",
        "Referer": "https://chartink.com/screener",
        "X-CSRF-TOKEN": csrf
    }
    res = session.post(SCREENER_URL, data=SCREENER_PAYLOAD, headers=headers)
    res.raise_for_status()
    return res.json()["data"]

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"}
    requests.post(url, data=payload)

def build_table(results, slots):
    # Prepare header
    table = "<b>📊 Chartink Screener</b>\n\n"
    header = ["Stock"] + slots
    rows = [header]

    all_stocks = set()
    for slot in slots:
        all_stocks.update(results.get(slot, {}).keys())

    for stock in sorted(all_stocks):
        row = [stock]
        for slot in slots:
            data = results.get(slot, {}).get(stock, {})
            if data:
                row.append(f"{data['per_chg']}% ({data['close']})")
            else:
                row.append("-")
        rows.append(row)

    # Format as monospaced table
    col_widths = [max(len(str(cell)) for cell in col) for col in zip(*rows)]
    for row in rows:
        line = "  ".join(str(cell).ljust(w) for cell, w in zip(row, col_widths))
        table += f"<pre>{line}</pre>\n"

    return table

def main():
    now = ist_now()
    time_str = now.strftime("%H:%M")

    # Reset every day at 09:15
    if time_str == "09:15":
        save_results({})
        return

    # Identify slot
    slot_map = {"10:30": "10:30AM", "12:30": "12:30PM", "15:15": "03:15PM"}
    slot = slot_map.get(time_str)
    if not slot:
        print("Not a scheduled run:", time_str)
        return

    # Load past results
    results = load_results()

    # Fetch new stocks
    data = fetch_stocks()
    slot_data = {d["nsecode"]: {"close": d["close"], "per_chg": d["per_chg"]} for d in data}
    results[slot] = slot_data
    save_results(results)

    # Decide which slots to show
    slots_to_show = [s for s in ["10:30AM", "12:30PM", "03:15PM"] if s in results]
    msg = build_table(results, slots_to_show)
    send_telegram(msg)

if __name__ == "__main__":
    main()
