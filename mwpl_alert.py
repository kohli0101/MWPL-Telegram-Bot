import requests
from bs4 import BeautifulSoup
import time

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
        resp = session.get(url)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, 'html5lib')
            # Try both table and div list fallback
            table = soup.find('table')
            if table:
                return [row.find_all('td')[0].text.strip() for row in table.find_all('tr')[1:]]
            ul = soup.find('ul', class_='ban-list')
            if ul:
                return [li.text.strip() for li in ul.find_all('li')]
        print(f"Attempt {attempt+1} failed (status {resp.status_code}), retrying…")
        time.sleep(5)
    return []
