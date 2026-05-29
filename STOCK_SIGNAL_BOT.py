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
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'TSLA', 'META',
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
        self.premarket_sent = False
        
        self.load_blocked()
        self.log("=" * 60)
        self.log("🥭 MANGO_BOT ULTIMATE - 4 INDICATORS")
        self.log("Finnhub API | Every 5 min scan | Every 30 min signal")
        self.log("=" * 60)
    
    def log(self, msg):
        ist = timezone(timedelta(hours=5, minutes=30))
        ts = datetime.now(ist).strftime("%Y-%m-%d %H:%M:%S IST")
        print(f"[{ts}] {msg}")
    
    def load_blocked(self):
        try:
            for path in ['/home/claude/blocked.json', '/tmp/blocked.json', './blocked.json']:
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
            data = {s: ts.isoformat() for s, ts in self.blocked_stocks.items()}
            for path in ['/home/claude/blocked.json', '/tmp/blocked.json', './blocked.json']:
                try:
                    os.makedirs(os.path.dirname(path) if os.path.dirname(path) else '.', exist_ok=True)
                    with open(path, 'w') as f:
                        json.dump(data, f)
                except:
                    pass
        except:
            pass
    
    def get_stock(self, symbol):
        """Get stock data from Finnhub"""
        try:
            url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={self.finnhub_key}"
            r = requests.get(url, timeout=5)
            d = r.json()
            if 'c' in d and d['c'] > 0:
                return {
                    'price': float(d['c']), 
                    'volume': int(d.get('v', 0)), 
                    'high': float(d.get('h', d['c'])), 
                    'low': float(d.get('l', d['c'])), 
                    'prev': float(d.get('pc', d['c']))
                }
        except:
            pass
        return None
    
    def score_stock(self, symbol, data):
        """Score stock based on current data"""
        if not data or data['price'] <= 0 or data['volume'] <= 0:
            return 0
        
        score = 0
        
        # Volume (0-30)
        if data['volume'] > 10000000:
            score += 30
        elif data['volume'] > 5000000:
            score += 25
        elif data['volume'] > 1000000:
            score += 20
        
        # Price range (0-30)
        if 50 < data['price'] < 300:
            score += 30
        elif 20 < data['price'] <= 50 or 300 <= data['price'] < 500:
            score += 20
        
        # Momentum (0-20)
        if data['prev'] > 0:
            change = ((data['price'] - data['prev']) / data['prev']) * 100
            if 0.5 <= change <= 3:
                score += 20
            elif 0 <= change < 0.5:
                score += 10
        
        # High/Low range (0-20)
        if data['high'] > data['low']:
            range_pct = ((data['high'] - data['low']) / data['low']) * 100
            if 0.5 <= range_pct <= 5:
                score += 20
            elif range_pct > 0:
                score += 10
        
        return min(max(score, 0), 100)
    
    def get_logo(self, symbol):
        try:
            url = f"https://finnhub.io/api/v1/stock/profile2?symbol={symbol}&token={self.finnhub_key}"
            r = requests.get(url, timeout=5)
            data = r.json()
            if 'logo' in data and data['logo']:
                return data['logo']
        except:
            pass
        return None
    
    def get_market_news(self):
        try:
            url = f"https://finnhub.io/api/v1/news?category=general&token={self.finnhub_key}"
            r = requests.get(url, timeout=5)
            data = r.json()
            if data and len(data) > 0:
                news = data[0]
                return {
                    'headline': news.get('headline', 'Market Update'),
                    'source': news.get('source', 'News')
                }
        except:
            pass
        return None
    
    def signals_left(self):
        ist = timezone(timedelta(hours=5, minutes=30))
        now = datetime.now(ist)
        if now.hour >= 19:
            mins = (24 - now.hour) * 60 - now.minute + 90
        elif now.hour < 1:
            mins = (1 - now.hour) * 60 - now.minute + 30
        else:
            return 0
        return max(1, (mins // 30) + 1)
    
    def premarket_check(self):
        ist = timezone(timedelta(hours=5, minutes=30))
        now = datetime.now(ist)
        
        if not (now.hour == 18 and now.minute < 5) or self.premarket_sent:
            return
        
        spy = self.get_stock('SPY')
        qqq = self.get_stock('QQQ')
        news = self.get_market_news()
        
        if spy and qqq:
            spy_change = ((spy['price'] - spy['prev']) / spy['prev']) * 100 if spy['prev'] > 0 else 0
            qqq_change = ((qqq['price'] - qqq['prev']) / qqq['prev']) * 100 if qqq['prev'] > 0 else 0
            sentiment = "🟢 BULLISH" if (spy_change + qqq_change) / 2 > 0.5 else "🟡 NEUTRAL"
            
            fields = [
                {"name": "📊 Sentiment", "value": sentiment, "inline": True},
                {"name": "SPY", "value": f"{spy_change:+.2f}%", "inline": True},
                {"name": "QQQ", "value": f"{qqq_change:+.2f}%", "inline": True},
            ]
            
            if news:
                fields.append({"name": "📰 News", "value": f"{news['headline'][:80]}...", "inline": False})
            
            embed = {
                "title": "🌅 PRE-MARKET ANALYSIS",
                "color": 16776960,
                "fields": fields,
                "footer": {"text": "🥭 Mango_Bot"}
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
                if data and data['price'] > 0 and data['volume'] > 0:
                    score = self.score_stock(symbol, data)
                    
                    if score > 20:
                        self.stocks_analysis[symbol] = {
                            'score': score, 
                            'price': data['price'], 
                            'volume': data['volume'], 
                            'prev': data['prev'],
                            'high': data['high'], 
                            'low': data['low']
                        }
                        found += 1
                time.sleep(0.25)
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
            if s in self.open_positions:
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
            "footer": {"text": "🥭 Mango_Bot"}
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
        logo = self.get_logo(symbol)
        left = self.signals_left()
        
        self.open_positions[symbol] = {'entry': price, 'target': target, 'time': datetime.now()}
        self.blocked_stocks[symbol] = datetime.now()
        self.save_blocked()
        
        # Why to buy
        change = ((price - data['prev']) / data['prev'] * 100) if data['prev'] > 0 else 0
        why_text = "Momentum bullish" if change > 0.5 else "Volume strong"
        
        fields = [
            {"name": "📍 Entry", "value": f"${price:.2f}", "inline": True},
            {"name": "🎯 Target", "value": f"${target:.2f} (+2.5%)", "inline": True},
            {"name": "⭐ Score", "value": f"{score}/100", "inline": True},
            {"name": "📢 Signals Left", "value": f"{left} today! ⏰", "inline": True},
            {"name": "📊 Why", "value": why_text, "inline": False},
        ]
        
        embed = {
            "title": f"🟢 BUY: {symbol}",
            "color": 3066993,
            "fields": fields,
            "footer": {"text": "🥭 Mango_Bot"}
        }
        
        if logo:
            embed["thumbnail"] = {"url": logo}
        
        try:
            requests.post(self.webhook, json={'embeds': [embed]}, timeout=10)
            self.log(f"📱 BUY: {symbol} @ ${price:.2f} | Score: {score}")
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
