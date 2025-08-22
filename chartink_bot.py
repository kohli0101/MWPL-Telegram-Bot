import requests
import re
import os

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

def fetch_chartink_results():
    session = requests.Session()
    headers = {"User-Agent": "Mozilla/5.0"}

    # Step 1: Get CSRF token from homepage
    r = session.get("https://chartink.com", headers=headers)
    token_match = re.search(r'<meta name="csrf-token" content="(.*?)"', r.text)
    if not token_match:
        return ["Error: Could not find CSRF token"]
    csrf_token = token_match.group(1)

    # Step 2: Request screener results
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

        # Format stocks with Price + Change %
        formatted = []
        for stock in results:
            symbol = stock.get("nsecode", "N/A")
            price = stock.get("close", "N/A")
            change = stock.get("per_chg", "N/A")
            formatted.append(f"{symbol} → ₹{price} ({change}%)")

        return formatted
    except Exception as e:
        return [f"Error: {e}\nResponse: {resp.text[:200]}"]

def send_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": text})

if __name__ == "__main__":
    stocks = fetch_chartink_results()
    if stocks and not stocks[0].startswith("Error"):
        message = "📊 Chartink Screener Results:\n" + "\n".join(stocks)
    else:
        message = "\n".join(stocks)
    send_message(message)
