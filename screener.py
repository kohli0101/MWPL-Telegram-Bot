import requests
import re
import os

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

def fetch_chartink_results():
    session = requests.Session()
    headers = {"User-Agent": "Mozilla/5.0"}

    # Step 1: Get CSRF token
    r = session.get("https://chartink.com", headers=headers)
    token_match = re.search(r'<meta name="csrf-token" content="(.*?)"', r.text)
    if not token_match:
        return ["Error: Could not find CSRF token"]
    csrf_token = token_match.group(1)

    # Step 2: Screener process
    payload = {
        "_token": csrf_token,
        "scan_clause": '( {33489} ( [=1] 30 minute low < [=-1] 30 minute close and [=1] 1 hour close > 1 day ago high and [=1] 1 hour "close - 1 candle ago close / 1 candle ago close * 100" < 2 and [=1] 1 hour "close - 1 candle ago close / 1 candle ago close * 100" > 1 ) )'
    }
    url = "https://chartink.com/screener/process"
    try:
        resp = session.post(url, data=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        results = data.get("data", [])
        if not results:
            return ["⚠️ No stocks matched your screener"]

        # Build table
        table_lines = []
        table_lines.append("SYMBOL     PRICE     CHANGE%")
        table_lines.append("--------------------------------")
        for stock in results:
            symbol = stock.get("nsecode", "N/A")
            price = stock.get("close", "N/A")
            change = stock.get("per_chg", "N/A")
            # Align neatly
            table_lines.append(f"{symbol:<10} {price:<9} {change:+}%" if isinstance(change,(int,float)) else f"{symbol:<10} {price:<9} {change}")

        return table_lines
    except Exception as e:
        return [f"Error: {e}\nResponse: {resp.text[:200]}"]

def send_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": text, "parse_mode": "MarkdownV2"})

if __name__ == "__main__":
    stocks = fetch_chartink_results()
    if stocks and not stocks[0].startswith("Error"):
        # Wrap table in ``` for monospace formatting
        table = "```\n" + "\n".join(stocks) + "\n```"
        message = "📊 *Chartink Screener Results*\n" + table
    else:
        message = "\n".join(stocks)
    send_message(message)
