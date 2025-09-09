import requests
import re
import os

# --- Telegram Bot Settings ---
BOT_TOKEN = os.environ.get("BOT_TOKEN", "<PUT_YOUR_BOT_TOKEN_HERE>")
CHAT_IDS = [
    os.environ.get("CHAT_ID", "979202747"),        # your chat id
    os.environ.get("FRIEND_CHAT_ID", "1617807992") # friend's chat id
]

# --- Chartink Screener Settings ---
# Replace with your screener slug (the part after /screener/ in the URL)
# Example: if your screener URL is https://chartink.com/screener/my-breakout-stocks
# then set SCREENER_SLUG = "my-breakout-stocks"
SCREENER_SLUG = "test-screener"  

def fetch_chartink_results():
    session = requests.Session()
    headers = {
        "User-Agent": "Mozilla/5.0",
        "X-Requested-With": "XMLHttpRequest"
    }

    # Step 1: Visit screener page to get CSRF + cookies
    screener_url = f"https://chartink.com/screener/f-f-1hr-swing"
    r = session.get(screener_url, headers=headers)
    token_match = re.search(r'<meta name="csrf-token" content="(.*?)"', r.text)
    if not token_match:
        return ["Error: Could not find CSRF token"]
    csrf_token = token_match.group(1)

    # Step 2: Update headers with CSRF token
    session.headers.update({"X-CSRF-TOKEN": csrf_token})

    # Step 3: Screener request (your scan clause stays here)
    payload = {
        "scan_clause": '( {33489} ( [=1] 30 minute low < [=-1] 30 minute close and [=1] 1 hour close > 1 day ago high and [=1] 1 hour "close - 1 candle ago close / 1 candle ago close * 100" < 2 and [=1] 1 hour "close - 1 candle ago close / 1 candle ago close * 100" > 1 ) )'
    }

    try:
        resp = session.post("https://chartink.com/screener/process", data=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        results = data.get("data", [])
        if not results:
            return ["⚠️ No stocks matched your screener"]

        # Build table
        table_lines = []
        table_lines.append("SYMBOL     PRICE     CHANGE%")
        table_lines.append("--------------------------------")

        total_price = 0.0
        weighted_change = 0.0

        for stock in results:
            symbol = stock.get("nsecode", "N/A")
            price = float(stock.get("close", 0.0) or 0.0)
            change = float(stock.get("per_chg", 0.0) or 0.0)

            total_price += price
            weighted_change += price * change

            table_lines.append(f"{symbol:<10} {price:<9.2f} {change:+.2f}%")

        total_change = weighted_change / total_price if total_price else 0.0
        table_lines.append("--------------------------------")
        table_lines.append(f"{'TOTAL':<10} {total_price:<9.2f} {total_change:+.2f}%")

        return table_lines

    except Exception as e:
        response_text = resp.text[:200] if 'resp' in locals() else "No response"
        return [f"Error: {e}\nResponse: {response_text}"]

def send_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    for chat_id in CHAT_IDS:
        try:
            requests.post(url, data={"chat_id": chat_id, "text": text, "parse_mode": "HTML"})
            print(f"✅ Message sent to {chat_id}")
        except Exception as e:
            print(f"❌ Telegram send failed for {chat_id}: {e}")

if __name__ == "__main__":
    stocks = fetch_chartink_results()
    if stocks and not stocks[0].startswith("Error"):
        table = "<pre>\n" + "\n".join(stocks) + "\n</pre>"
        message = "📊 <b>Chartink Screener Results</b>\n" + table
    else:
        message = "\n".join(stocks)
    send_message(message)
