import requests
import os

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

def fetch_chartink_results():
    session = requests.Session()

    # First, visit Chartink to grab cookies (important!)
    session.get("https://chartink.com")

    # Now send screener request with scan_clause
    payload = {
        "scan_clause": '( {33489} ( [=1] 30 minute low < [=-1] 30 minute close and [=1] 1 hour close > 1 day ago high and [=1] 1 hour "close - 1 candle ago close / 1 candle ago close * 100" < 2 and [=1] 1 hour "close - 1 candle ago close / 1 candle ago close * 100" > 1 ) )'
    }
    url = "https://chartink.com/screener/process"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://chartink.com/screener/f-f-1hr-swing"
    }

    try:
        response = session.post(url, data=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        stocks = [item["nsecode"] for item in data.get("data", [])]
        return stocks
    except Exception as e:
        return [f"Error: {e}\nResponse: {response.text[:200]}"]

def send_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": text})

if __name__ == "__main__":
    stocks = fetch_chartink_results()
    if stocks and not stocks[0].startswith("Error"):
        message = "📊 Chartink Screener Results:\n" + "\n".join(stocks)
    else:
        message = "⚠️ No stocks found or error.\n" + "\n".join(stocks)
    send_message(message)
