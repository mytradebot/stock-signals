#!/usr/bin/env python3
"""MANGO_BOT - 30-MIN SIGNALS + 7-DAY BLOCK + AUTO-SELL"""
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
        self.last_signal = datetime.now() - timedelta(minutes=31)
        self.blocked_stocks = {}
        self.load_blocked_stocks()
        
        self.log("=" * 70)
        self.log("🥭 MANGO_BOT - FINAL VERSION")
        self.log("📊 100 BEST STOCKS → 1 signal every 30 MIN")
        self.log("🚀 Auto buy/sell + No repeats in 7 days + IST timezone")
        self.log("=" * 70)
    
    def log(self, msg):
        ist = timezone(timedelta(hours=5, minutes=30))
        ts = datetime.now(ist).strftime("%Y-%m-%d %H:%M:%S IST")
        print(f"[{ts}] {msg}")
    
    def load_blocked_stocks(self):
        """Load 7-day blocked stocks"""
        try:
            if os.path.exists('/home/claude/blocked_stocks.json'):
                with open('/home/claude/blocked_stocks.json', 'r') as f:
                    data = json.load(f)
                    for symbol, ts in data.items():
                        self.blocked_stocks[symbol] = datetime.fromisoformat(ts)
                self.log(f"✅ Loaded {len(self.blocked_stocks)} blocked stocks")
        except Exception as e:
            self.log(f"⚠️ Could not load blocked stocks: {e}")
    
    def save_blocked_stocks(self):
        """Save blocked stocks"""
        try:
            data = {symbol: ts.isoformat() for symbol, ts in self.blocked_stocks.items()}
            with open('/home/claude/blocked_stocks.json', 'w') as f:
                json.dump(data, f)
        except:
            pass
    
    def is_stock_blocked(self, symbol):
        """Check if stock blocked"""
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
                return {
                    'price': float(data['c']), 
                    'volume': int(data.get('v', 0)), 
                    'high': float(data.get('h', data['c'])), 
                    'low': float(data.get('l', data['c'])), 
                    'prev_close': float(data.get('pc', data['c']))
                }
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
        try:
            for symbol in self.stocks:
                try:
                    data = self.get_stock_data(symbol)
                    if data:
                        score = self.analyze_stock(symbol, data)
                        self.stocks_analysis[symbol] = {
                            'score': score, 
                            'price': data['price'], 
                            'volume': data['volume'], 
                            'prev_close': data['prev_close']
                        }
                        found += 1
                    time.sleep(0.6)
                except Exception as e:
                    pass
            self.log(f"✅ Analyzed {found}/{len(self.stocks)} stocks")
        except Exception as e:
            self.log(f"❌ Scan error: {e}")
    
    def monitor_positions(self):
        """Check for target hits, stops, time exits"""
        now = datetime.now()
        to_close = []
        
        for symbol, pos in list(self.open_positions.items()):
            try:
                data = self.get_stock_data(symbol)
                if not data:
                    continue
                
                price = data['price']
                entry = pos['entry_price']
                target = pos['target']
                entry_time = pos['entry_time']
                
                # Target hit
                if price >= target:
                    profit = ((price - entry) / entry) * 100
                    self.send_sell_signal(symbol, entry, price, profit, "🎉 TARGET HIT")
                    to_close.append(symbol)
                
                # 7 days passed
                elif (now - entry_time).days >= 7:
                    profit = ((price - entry) / entry) * 100
                    self.send_sell_signal(symbol, entry, price, profit, "⏰ 7-DAY EXIT")
                    to_close.append(symbol)
            except:
                pass
        
        for symbol in to_close:
            del self.open_positions[symbol]
    
    def send_sell_signal(self, symbol, entry, exit_price, profit, reason):
        """Send SELL signal"""
        color = 3066993 if profit > 0 else 15158332
        
        embed = {
            "title": f"{reason} {symbol}",
            "description": f"⏰ {datetime.now(timezone(timedelta(hours=5, minutes=30))).strftime('%H:%M IST')}",
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
            self.log(f"📤 SELL: {symbol} | ${entry:.2f} → ${exit_price:.2f} ({profit:+.2f}%)")
        except:
            pass
    
    def send_buy_signal(self, symbol, data, score):
        """Send BUY signal"""
        price = data['price']
        target = price * 1.035
        signals_left = self.get_remaining_signals()
        
        self.open_positions[symbol] = {
            'entry_price': price, 
            'target': target, 
            'entry_time': datetime.now()
        }
        self.block_stock(symbol)
        
        embed = {
            "title": f"🟢 MANGO_BOT BUY: {symbol}",
            "description": f"⏰ {datetime.now(timezone(timedelta(hours=5, minutes=30))).strftime('%H:%M IST')}",
            "color": 3066993,
            "fields": [
                {"name": "📍 Entry", "value": f"${price:.2f}", "inline": True},
                {"name": "🎯 Target", "value": f"${target:.2f} (+3.5%)", "inline": True},
                {"name": "⭐ Score", "value": f"{score}/100", "inline": True},
                {"name": "📢 Signals Left", "value": f"{signals_left} more today! ⏰", "inline": True},
                {"name": "💡 Auto Sell", "value": "At target!", "inline": True},
                {"name": "🔒 Blocked", "value": "7 days (no repeats)", "inline": True}
            ],
            "footer": {"text": "🥭 Mango_Bot - Auto Signals & Auto Exits"}
        }
        
        try:
            requests.post(self.webhook, json={'embeds': [embed]}, timeout=10)
            self.log(f"📱 BUY: {symbol} @ ${price:.2f} | Score: {score} | {signals_left} signals left!")
        except:
            self.log("❌ Discord error")
    
    def get_remaining_signals(self):
        """Calculate signals left today"""
        ist = timezone(timedelta(hours=5, minutes=30))
        now = datetime.now(ist)
        
        # Market: 7 PM (19:00) to 1:30 AM (01:30)
        if now.hour > 1 or (now.hour == 1 and now.minute >= 30):
            # After 1:30 AM
            if now.hour < 18:
                return 0
        
        if now.hour >= 19:
            # From 7 PM to midnight
            minutes_until_close = (24 - now.hour) * 60 - now.minute + 90  # 90 min = 1:30 AM
        elif now.hour < 1:
            # From midnight to 1:30 AM
            minutes_until_close = (1 - now.hour) * 60 - now.minute + 30
        else:
            return 0
        
        signals = (minutes_until_close // 30) + 1
        return max(0, signals)
    
    def is_market_open(self):
        ist = timezone(timedelta(hours=5, minutes=30))
        now = datetime.now(ist)
        is_open = (now.hour >= 19) or (now.hour < 1) or (now.hour == 1 and now.minute < 30)
        is_weekday = now.weekday() < 5
        return is_weekday and is_open
    
    def run(self):
        cycle = 0
        while True:
            try:
                cycle += 1
                self.log(f"\n🔄 CYCLE #{cycle}")
                
                if self.is_market_open():
                    self.scan()
                    self.monitor_positions()
                    self.log(f"📊 Open: {len(self.open_positions)} | Closed: {len(self.closed_positions)}")
                    
                    elapsed = datetime.now() - self.last_signal
                    signals_left = self.get_remaining_signals()
                    if elapsed >= timedelta(minutes=30):
                        available = {s: d for s, d in self.stocks_analysis.items() if not self.is_stock_blocked(s)}
                        if available:
                            best = max(available.items(), key=lambda x: x[1]['score'])
                            self.send_buy_signal(best[0], best[1], best[1]['score'])
                            self.last_signal = datetime.now()
                        else:
                            self.log("⚠️ All stocks blocked")
                    else:
                        remaining = 30 - int(elapsed.total_seconds() / 60)
                        self.log(f"⏳ Next signal in {remaining} min | {signals_left} signals left today!")
                else:
                    self.log("😴 Market closed")
                
                self.log("⏱️ Next check in 5 min\n")
                time.sleep(300)
            except Exception as e:
                self.log(f"❌ FATAL ERROR: {e}")
                time.sleep(60)

if __name__ == "__main__":
    bot = CompleteBot()
    bot.run()
