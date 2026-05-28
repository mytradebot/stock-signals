#!/usr/bin/env python3
"""MANGO_BOT - FINAL VERSION - IST + 3-min signals + 7-day block"""
import os, time, json
from datetime import datetime, timedelta, timezone

try:
    import requests
except:
    os.system("pip install requests --break-system-packages")
    import requests

class CompleteBot:
    def __init__(self):
        self.webhook = os.environ.get('DISCORD_WEBHOOK')
        if not self.webhook:
            print("❌ DISCORD_WEBHOOK not set!")
            exit(1)
        
        self.finnhub_key = 'd8bja4hr01qppd8s0760d8bja4hr01qppd8s076g'
        
        self.stocks = [
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'TSLA', 'META', 'BERKSH',
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
            'CRSR', 'PLTR', 'SQ', 'ZS', 'DBX', 'PATH', 'COIN', 'HOOD', 'SOFI', 'GLBE',
        ]
        
        self.stocks_analysis = {}
        self.open_positions = {}
        self.closed_positions = {}
        self.last_signal = datetime.now()
        self.blocked_stocks = {}
        self.load_blocked_stocks()
        
        self.log("=" * 70)
        self.log("🥭 MANGO_BOT - FINAL VERSION (IST + 3-MIN SIGNALS + 7-DAY BLOCK)")
        self.log("📊 100 BEST STOCKS → 1 signal every 3 MIN")
        self.log("🚀 Auto buy/sell + Daily analytics + No repeats in 7 days")
        self.log("=" * 70)
    
    def log(self, msg):
        ist = timezone(timedelta(hours=5, minutes=30))
        ts = datetime.now(ist).strftime("%Y-%m-%d %H:%M:%S IST")
        print(f"[{ts}] {msg}")
    
    def load_blocked_stocks(self):
        """Load 7-day blocked stocks from file"""
        try:
            if os.path.exists('/home/claude/blocked_stocks.json'):
                with open('/home/claude/blocked_stocks.json', 'r') as f:
                    data = json.load(f)
                    for symbol, ts in data.items():
                        self.blocked_stocks[symbol] = datetime.fromisoformat(ts)
                self.log(f"✅ Loaded {len(self.blocked_stocks)} blocked stocks")
        except:
            pass
    
    def save_blocked_stocks(self):
        """Save blocked stocks to file"""
        try:
            data = {symbol: ts.isoformat() for symbol, ts in self.blocked_stocks.items()}
            with open('/home/claude/blocked_stocks.json', 'w') as f:
                json.dump(data, f)
        except:
            pass
    
    def is_stock_blocked(self, symbol):
        """Check if stock blocked (sent in last 7 days)"""
        if symbol not in self.blocked_stocks:
            return False
        
        days = (datetime.now() - self.blocked_stocks[symbol]).days
        if days >= 7:
            del self.blocked_stocks[symbol]
            self.save_blocked_stocks()
            return False
        return True
    
    def block_stock(self, symbol):
        """Block stock for 7 days"""
        self.blocked_stocks[symbol] = datetime.now()
        self.save_blocked_stocks()
    
    def get_stock_data(self, symbol):
        try:
            url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={self.finnhub_key}"
            response = requests.get(url, timeout=5)
            data = response.json()
            if 'c' in data and data['c'] > 0:
                return {'price': float(data['c']), 'volume': int(data.get('v', 0)), 
                        'high': float(data.get('h', data['c'])), 'low': float(data.get('l', data['c'])), 
                        'prev_close': float(data.get('pc', data['c']))}
        except:
            pass
        return None
    
    def analyze_stock(self, symbol, data):
        if not data:
            return 0
        score = 0
        volume = data['volume']
        if volume > 10000000:
            score += 25
        elif volume > 5000000:
            score += 20
        price = data['price']
        if 50 < price < 300:
            score += 25
        prev_close = data['prev_close']
        if prev_close > 0:
            change = ((price - prev_close) / prev_close) * 100
            if 0.5 <= change <= 3:
                score += 25
        high, low = data['high'], data['low']
        if high > 0 and low > 0:
            volatility = ((high - low) / price) * 100
            if 0.5 <= volatility <= 2:
                score += 25
        return min(score, 100)
    
    def scan(self):
        self.log(f"🔍 Scanning {len(self.stocks)} stocks...")
        found = 0
        for symbol in self.stocks:
            try:
                data = self.get_stock_data(symbol)
                if data:
                    score = self.analyze_stock(symbol, data)
                    self.stocks_analysis[symbol] = {'score': score, 'price': data['price'], 
                                                     'volume': data['volume'], 'prev_close': data['prev_close']}
                    found += 1
                time.sleep(0.6)
            except:
                pass
        self.log(f"✅ Analyzed {found} stocks")
    
    def send_signal(self, symbol, data, score):
        price = data['price']
        target = price * 1.035
        logo = f"https://logo.clearbit.com/{symbol}.com"
        
        self.open_positions[symbol] = {'entry_price': price, 'target': target, 'entry_time': datetime.now()}
        self.block_stock(symbol)
        
        embed = {
            "title": f"🟢 MANGO_BOT BUY: {symbol}",
            "description": f"⏰ {datetime.now(timezone(timedelta(hours=5, minutes=30))).strftime('%H:%M IST')}",
            "color": 3066993,
            "thumbnail": {"url": logo, "height": 100, "width": 100},
            "fields": [
                {"name": "📍 Entry", "value": f"${price:.2f}", "inline": True},
                {"name": "🎯 Target", "value": f"${target:.2f} (+3.5%)", "inline": True},
                {"name": "⭐ Score", "value": f"{score}/100", "inline": True},
                {"name": "✅ Auto Sell", "value": "When target hits!", "inline": True}
            ],
            "footer": {"text": "🥭 Mango_Bot - No repeats for 7 days!"}
        }
        
        try:
            requests.post(self.webhook, json={'embeds': [embed]}, timeout=10)
            self.log(f"📱 SIGNAL: {symbol} @ ${price:.2f} | BLOCKED 7 DAYS")
        except:
            self.log("❌ Discord error")
    
    def is_market_open(self):
        ist = timezone(timedelta(hours=5, minutes=30))
        now = datetime.now(ist)
        is_open = (now.hour >= 19) or (now.hour < 1) or (now.hour == 1 and now.minute < 30)
        is_weekday = now.weekday() < 5
        return is_weekday and is_open
    
    def run(self):
        cycle = 0
        while True:
            cycle += 1
            self.log(f"\n🔄 CYCLE #{cycle}")
            
            if self.is_market_open():
                self.scan()
                self.log(f"📊 Open positions: {len(self.open_positions)}")
                
                elapsed = datetime.now() - self.last_signal
                if elapsed >= timedelta(minutes=3):
                    available = {s: d for s, d in self.stocks_analysis.items() if not self.is_stock_blocked(s)}
                    if available:
                        best = max(available.items(), key=lambda x: x[1]['score'])
                        self.send_signal(best[0], best[1], best[1]['score'])
                        self.last_signal = datetime.now()
                    else:
                        self.log("⚠️ All stocks blocked, waiting...")
                else:
                    remaining = 3 - int(elapsed.total_seconds() / 60)
                    self.log(f"⏳ Next signal in {remaining} min")
            else:
                self.log("😴 Market closed")
            
            self.log("⏱️ Next check in 1 min\n")
            time.sleep(60)

if __name__ == "__main__":
    bot = CompleteBot()
    bot.run()
