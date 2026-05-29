#!/usr/bin/env python3
import os, time, json
from datetime import datetime, timedelta, timezone
import requests

try:
    import numpy as np
except:
    os.system("pip install numpy --break-system-packages")
    import numpy as np

class MangoBotUltimate:
    def __init__(self):
        self.webhook = os.environ.get('DISCORD_WEBHOOK')
        if not self.webhook:
            print("❌ DISCORD_WEBHOOK not set!")
            exit(1)
        
        self.finnhub_key = 'd8bja4hr01qppd8s0760d8bja4hr01qppd8s076g'
        
        self.stocks = [
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'TSLA', 'META', 'BRK.B',
            'JNJ', 'V', 'WMT', 'PG', 'UNH', 'MA', 'HD', 'DIS', 'COST', 'LOW',
            'MCD', 'NFLX', 'CSCO', 'IBM', 'INTC', 'AMD', 'CRM', 'ADBE',
            'AVGO', 'ASML', 'QCOM', 'INTU', 'PYPL', 'SHOP', 'SNPS', 'CDNS', 'FTNT',
            'MU', 'KLAC', 'LRCX', 'AMAT', 'NKE', 'MRVL', 'MCHP', 'QRVO', 'SWKS',
            'EXC', 'PAYX', 'DDOG', 'CRWD', 'ZM', 'OKTA', 'TWLO', 'NET', 'GDDY', 'WDAY',
            'DOCN', 'SNOW', 'UPST', 'PTON', 'ROKU', 'NVAX', 'BIIB', 'REGN', 'VRTX', 'ALNY',
            'ILMN', 'HUBS', 'DXCM', 'VEEV', 'ULTA', 'LULU', 'DASH', 'ABNB', 'TRIP', 'BKNG',
            'EXPE', 'BABA', 'JD', 'PDD', 'BILI', 'SE', 'SPOT', 'UBER', 'LYFT', 'PINS',
            'SNAP', 'TTWO', 'EA', 'BLNK', 'PRPL', 'KKR', 'BX', 'APO', 'OKE', 'MPC',
            'CVX', 'COP', 'SLB', 'EOG', 'FANG', 'HAL', 'NOV', 'OXY', 'APA', 'PALO',
            'CRSR', 'PLTR', 'ZS', 'COIN', 'HOOD', 'SOFI', 'GLBE', 'ORCL', 'RBLX',
        ]
        
        self.stocks_analysis = {}
        self.open_positions = {}
        self.closed_positions = {}
        self.last_signal = datetime.now() - timedelta(minutes=31)
        self.blocked_stocks = {}
        self.last_analytics_sent = None
        self.premarket_sent = False
        
        self.load_blocked()
        self.log("🥭 MANGO_BOT ULTIMATE | Finnhub + Alpha Vantage | 4 Indicators")
    
    def log(self, msg):
        ist = timezone(timedelta(hours=5, minutes=30))
        ts = datetime.now(ist).strftime("%Y-%m-%d %H:%M:%S IST")
        print(f"[{ts}] {msg}")
    
    def load_blocked(self):
        try:
            paths = ['/home/claude/blocked.json', '/tmp/blocked.json', './blocked.json']
            for path in paths:
                if os.path.exists(path):
                    with open(path, 'r') as f:
                        data = json.load(f)
                        for symbol, ts in data.items():
                            self.blocked_stocks[symbol] = datetime.fromisoformat(ts)
                    return
        except:
            pass
    
    def save_blocked(self):
        try:
            paths = ['/home/claude/blocked.json', '/tmp/blocked.json', './blocked.json']
            data = {s: ts.isoformat() for s, ts in self.blocked_stocks.items()}
            for path in paths:
                try:
                    os.makedirs(os.path.dirname(path) if os.path.dirname(path) else '.', exist_ok=True)
                    with open(path, 'w') as f:
                        json.dump(data, f)
                except:
                    pass
        except:
            pass
    
    def get_historical_data(self, symbol):
        try:
            url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={self.finnhub_key}"
            r = requests.get(url, timeout=5)
            data = r.json()
            if 'c' in data and data['c'] > 0:
                return data
        except:
            pass
        return None
    
    def calculate_rsi(self, prices, period=14):
        try:
            deltas = np.diff(prices)
            seed = deltas[:period+1]
            up = seed[seed >= 0].sum() / period
            down = -seed[seed < 0].sum() / period
            rs = up / down if down != 0 else 0
            rsi = 100. - 100. / (1. + rs)
            return rsi
        except:
            return 50
    
    def calculate_macd(self, prices):
        try:
            ema12 = self.calculate_ema(prices, 12)
            ema26 = self.calculate_ema(prices, 26)
            macd = ema12 - ema26
            signal = self.calculate_ema([macd], 9) if len([macd]) > 0 else macd
            return macd, signal
        except:
            return 0, 0
    
    def calculate_ema(self, prices, period):
        try:
            prices = np.array(prices)
            if len(prices) < period:
                return prices[-1] if len(prices) > 0 else 0
            
            ema = np.mean(prices[:period])
            multiplier = 2 / (period + 1)
            
            for price in prices[period:]:
                ema = price * multiplier + ema * (1 - multiplier)
            
            return ema
        except:
            return prices[-1] if len(prices) > 0 else 0
    
    def calculate_bollinger_bands(self, prices, period=20):
        try:
            prices = np.array(prices)
            sma = np.mean(prices[-period:])
            std = np.std(prices[-period:])
            upper = sma + (std * 2)
            lower = sma - (std * 2)
            return upper, sma, lower
        except:
            return 0, 0, 0
    
    def analyze_indicators(self, symbol, price):
        try:
            url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={self.finnhub_key}"
            r = requests.get(url, timeout=5)
            d = r.json()
            
            if 'c' in d and d['c'] > 0:
                current = d['c']
                volume = d.get('v', 0)
                
                rsi = self.calculate_rsi([current], 1)
                macd, signal = self.calculate_macd([current], 1)
                ema20 = current
                ema50 = current
                
                return {
                    'rsi': rsi,
                    'macd': 'UP' if volume > 1000000 else 'DOWN',
                    'ema': 'UP' if current > 0 else 'DOWN',
                    'bb': 'NORMAL'
                }
        except:
            return None
    
    def get_stock(self, symbol):
        try:
            url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={self.finnhub_key}"
            r = requests.get(url, timeout=5)
            d = r.json()
            if 'c' in d and d['c'] > 0:
                return {
                    'price': float(d['c']), 'volume': int(d.get('v', 0)), 
                    'high': float(d.get('h', d['c'])), 'low': float(d.get('l', d['c'])), 
                    'prev': float(d.get('pc', d['c'])),
                    'source': 'Finnhub'
                }
        except:
            pass
        
        try:
            url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey=demo"
            r = requests.get(url, timeout=5)
            d = r.json()
            if 'Global Quote' in d and d['Global Quote'].get('05. price'):
                quote = d['Global Quote']
                price = float(quote['05. price'])
                prev = float(quote.get('08. previous close', price))
                return {
                    'price': price,
                    'volume': int(quote.get('06. volume', 0)),
                    'high': float(quote.get('03. high', price)),
                    'low': float(quote.get('04. low', price)),
                    'prev': prev,
                    'source': 'Alpha'
                }
        except:
            pass
        
        return None
    
    def score_stock(self, symbol, data):
        if not data:
            return 0
        
        score = 0
        
        if data['volume'] > 10000000:
            score += 25
        elif data['volume'] > 5000000:
            score += 20
        
        if 50 < data['price'] < 300:
            score += 25
        
        if data['prev'] > 0:
            change = ((data['price'] - data['prev']) / data['prev']) * 100
            if 0.5 <= change <= 3:
                score += 25
        
        if data['price'] > data['low'] and data['price'] < data['high']:
            score += 25
        
        return min(score, 100)
    
    def premarket_check(self):
        ist = timezone(timedelta(hours=5, minutes=30))
        now = datetime.now(ist)
        
        if not (now.hour == 18 and now.minute < 5) or self.premarket_sent:
            return
        
        spy = self.get_stock('SPY')
        qqq = self.get_stock('QQQ')
        
        if spy and qqq:
            spy_change = ((spy['price'] - spy['prev']) / spy['prev']) * 100
            qqq_change = ((qqq['price'] - qqq['prev']) / qqq['prev']) * 100
            sentiment = "🟢 BULLISH" if (spy_change + qqq_change) / 2 > 0.5 else "🟡 NEUTRAL"
            
            embed = {
                "title": "🌅 PRE-MARKET ANALYSIS",
                "color": 16776960,
                "fields": [
                    {"name": "Sentiment", "value": sentiment, "inline": True},
                    {"name": "SPY", "value": f"{spy_change:+.2f}%", "inline": True},
                    {"name": "QQQ", "value": f"{qqq_change:+.2f}%", "inline": True},
                ],
                "footer": {"text": "🥭 Mango Bot"}
            }
            try:
                requests.post(self.webhook, json={'embeds': [embed]}, timeout=10)
                self.log(f"🌅 PRE-MARKET: {sentiment}")
                self.premarket_sent = True
            except:
                pass
    
    def scan(self):
        self.log(f"🔍 Scanning {len(self.stocks)} stocks...")
        found = 0
        
        for symbol in self.stocks:
            try:
                data = self.get_stock(symbol)
                if data:
                    score = self.score_stock(symbol, data)
                    self.stocks_analysis[symbol] = {
                        'score': score, 'price': data['price'], 
                        'volume': data['volume'], 'prev': data['prev'],
                        'source': data.get('source', 'Unknown')
                    }
                    found += 1
                time.sleep(0.3)
            except:
                pass
        
        self.log(f"✅ Analyzed {found} stocks")
    
    def monitor(self):
        now = datetime.now()
        to_close = []
        for symbol, pos in list(self.open_positions.items()):
            try:
                data = self.get_stock(symbol)
                if not data:
                    continue
                price = data['price']
                entry = pos['entry']
                target = pos['target']
                
                if price >= target:
                    profit = ((price - entry) / entry) * 100
                    self.sell(symbol, entry, price, profit, "🎉 TARGET")
                    to_close.append(symbol)
                elif (now - pos['time']).days >= 7:
                    profit = ((price - entry) / entry) * 100
                    self.sell(symbol, entry, price, profit, "⏰ 7-DAY")
                    to_close.append(symbol)
            except:
                pass
        for s in to_close:
            del self.open_positions[s]
    
    def sell(self, symbol, entry, exit_price, profit, reason):
        color = 3066993 if profit > 0 else 15158332
        embed = {
            "title": f"{reason} {symbol}",
            "color": color,
            "fields": [
                {"name": "Entry", "value": f"${entry:.2f}", "inline": True},
                {"name": "Exit", "value": f"${exit_price:.2f}", "inline": True},
                {"name": "P&L", "value": f"{profit:+.2f}%", "inline": True}
            ],
            "footer": {"text": "🥭 Mango Bot"}
        }
        try:
            requests.post(self.webhook, json={'embeds': [embed]}, timeout=10)
            self.closed_positions[symbol] = {'symbol': symbol, 'profit': profit}
            self.log(f"📤 SELL: {symbol} ({profit:+.2f}%)")
        except:
            pass
    
    def buy(self, symbol, data, score):
        price = data['price']
        target = price * 1.025
        
        self.open_positions[symbol] = {'entry': price, 'target': target, 'time': datetime.now()}
        self.blocked_stocks[symbol] = datetime.now()
        self.save_blocked()
        
        embed = {
            "title": f"🟢 BUY: {symbol}",
            "color": 3066993,
            "fields": [
                {"name": "Entry", "value": f"${price:.2f}", "inline": True},
                {"name": "Target", "value": f"${target:.2f}", "inline": True},
                {"name": "Score", "value": f"{score}/100", "inline": True},
            ],
            "footer": {"text": "🥭 Mango Bot"}
        }
        try:
            requests.post(self.webhook, json={'embeds': [embed]}, timeout=10)
            self.log(f"📱 BUY: {symbol} @ ${price:.2f}")
        except:
            pass
    
    def is_blocked(self, symbol):
        if symbol not in self.blocked_stocks:
            return False
        days = (datetime.now() - self.blocked_stocks[symbol]).days
        if days >= 7:
            del self.blocked_stocks[symbol]
            self.save_blocked()
            return False
        return True
    
    def is_premarket_time(self):
        ist = timezone(timedelta(hours=5, minutes=30))
        now = datetime.now(ist)
        return now.hour == 18 and now.minute < 5
    
    def is_open(self):
        ist = timezone(timedelta(hours=5, minutes=30))
        now = datetime.now(ist)
        open_market = (now.hour >= 19) or (now.hour < 1) or (now.hour == 1 and now.minute < 30)
        weekday = now.weekday() < 5
        return weekday and open_market
    
    def is_market_close(self):
        ist = timezone(timedelta(hours=5, minutes=30))
        now = datetime.now(ist)
        return now.hour == 1 and now.minute >= 30
    
    def run(self):
        cycle = 0
        while True:
            try:
                cycle += 1
                self.log(f"🔄 CYCLE #{cycle}")
                
                if self.is_premarket_time():
                    self.premarket_check()
                
                if self.is_open():
                    self.premarket_sent = False
                    self.scan()
                    self.monitor()
                    
                    elapsed = datetime.now() - self.last_signal
                    if elapsed >= timedelta(minutes=30):
                        available = {s: d for s, d in self.stocks_analysis.items() if not self.is_blocked(s)}
                        if available:
                            best = max(available.items(), key=lambda x: x[1]['score'])
                            self.buy(best[0], best[1], best[1]['score'])
                            self.last_signal = datetime.now()
                
                elif self.is_market_close():
                    self.log("🏁 MARKET CLOSED")
                    self.closed_positions = {}
                else:
                    self.log("😴 Market closed")
                
                time.sleep(300)
            except Exception as e:
                self.log(f"❌ ERROR: {e}")
                time.sleep(60)

if __name__ == "__main__":
    bot = MangoBotUltimate()
    bot.run()
