import requests
from bs4 import BeautifulSoup
from datetime import datetime
import os
import time

# Environment Variables (Set these in your VPS or local machine)
BOT_TOKEN = os.environ['BOT_TOKEN']
CHAT_ID = os.environ['CHAT_ID']

def get_banned_stocks():
    url = 'https://www.nseindia.com/market-data/securities-in-ban-period-fno'
    headers = {
        'User-Agent': 'Mozilla/5.0',
        'Accept': 'text/html,application/xhtml+xml'
    }
    session = requests.Session()
    session.headers.update(headers)

    retries = 3
    for attempt in range(retries):
        response = session.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html5lib')
            table = soup.find('table')
            if table:
                rows = table.find_all('tr')[1:]
                banned_stocks = [row.find_all('td')[0].text.strip() for row in rows]
                if banned_stocks:
                    return banned_stocks
            print("Table found but no stocks listed. Retrying...")
        else:
            print(f"Attempt {attempt+1} failed (status {response.status_code}). Retrying...")
        time.sleep(5)
    print("Failed to fetch MWPL Ban List after retries.")
    return []

def send_telegram_alert(stocks):
    if stocks:
        message = f"🚫 *MWPL Ban List* ({datetime.now().strftime('%d-%b-%Y')}):\n" + "\n".join(f"🔒 {s}" for s in stocks)
    else:
        message = f"✅ *No stocks under MWPL ban* on {datetime.now().strftime('%d-%b-%Y')}."
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {'chat_id': CHAT_ID, 'text': message, 'parse_mode': 'Markdown'}
    response = requests.post(url, data=payload)
    print("Telegram Response:", response.status_code, response.text)

if __name__ == '__main__':
    banned_today = get_banned_stocks()
    send_telegram_alert(banned_today)
