#!/usr/bin/env python3
"""
🥭 MANGO_BOT - FINAL COMPLETE VERSION
30-min signals | 7-day block | Auto-sell | Daily analytics | IST timezone
"""
import os, time, json
from datetime import datetime, timedelta, timezone
import requests

class MangoBot:
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
        self.last_analytics_sent = None  # Track when last analytics sent
        self.load_blocked()
        
        self.log("=" * 70)
        self.log("🥭 MANGO_BOT - FINAL COMPLETE VERSION")
        self.log("📊 1 signal every 30 MIN | Auto-sell at target | 7-day block")
        self.log("💰 Daily analytics | Stock logos | Why to buy | IST timezone")
        self.log("=" * 70)
    
    def log(self, msg):
        ist = timezone(timedelta(hours=5, minutes=30))
        ts = datetime.now(ist).strftime("%Y-%m-%d %H:%M:%S IST")
        print(f"[{ts}] {msg}")
    
    def load_blocked(self):
        """Load 7-day blocked stocks from file"""
        try:
            paths = ['/home/claude/blocked.json', '/tmp/blocked.json', './blocked.json']
            for path in paths:
                if os.path.exists(path):
                    with open(path, 'r') as f:
                        data = json.load(f)
                        for symbol, ts in data.items():
                            self.blocked_stocks[symbol] = datetime.fromisoformat(ts)
                    self.log(f"✅ Loaded blocked stocks from {path}")
                    return
        except Exception as e:
            self.log(f"⚠️ Could not load blocked stocks: {e}")
    
    def save_blocked(self):
        """Save 7-day blocked stocks to file"""
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
    
    def is_blocked(self, symbol):
        """Check if stock blocked (sent in last 7 days)"""
        if symbol not in self.blocked_stocks:
            return False
        
        blocked_time = self.blocked_stocks[symbol]
        days = (datetime.now() - blocked_time).days
        hours = ((datetime.now() - blocked_time).total_seconds() / 3600)
        
        if days >= 7:
            self.log(f"✅ {symbol} unblocked (7 days passed)")
            del self.blocked_stocks[symbol]
            self.save_blocked()
            return False
        
        self.log(f"🔒 {symbol} blocked for {7-days} more days ({hours:.1f}h passed)")
        return True
    
    def block(self, symbol):
        """Block stock for 7 days"""
        self.blocked_stocks[symbol] = datetime.now()
        self.save_blocked()
        self.log(f"🔒 {symbol} BLOCKED for 7 days")
    
    def get_stock(self, symbol):
        """Get stock data from Finnhub API"""
        try:
            url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={self.finnhub_key}"
            r = requests.get(url, timeout=5)
            d = r.json()
            if 'c' in d and d['c'] > 0:
                return {'price': float(d['c']), 'volume': int(d.get('v', 0)), 
                        'high': float(d.get('h', d['c'])), 'low': float(d.get('l', d['c'])), 
                        'prev': float(d.get('pc', d['c']))}
        except:
            pass
        return None
    
    def score_stock(self, symbol, data):
        """Calculate stock quality score (0-100)"""
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
        if data['high'] > 0 and data['low'] > 0:
            vol = ((data['high'] - data['low']) / data['price']) * 100
            if 0.5 <= vol <= 2:
                score += 25
        return min(score, 100)
    
    def get_logo(self, symbol):
        """Get stock logo URL"""
        try:
            url = f"https://finnhub.io/api/v1/stock/profile2?symbol={symbol}&token={self.finnhub_key}"
            r = requests.get(url, timeout=5)
            data = r.json()
            if 'logo' in data and data['logo']:
                return data['logo']
        except:
            pass
        return f"https://logo.clearbit.com/{symbol}.com"
    
    def why_buy(self, symbol, data, score):
        """Generate short reason why to buy"""
        reasons = []
        
        if data['prev'] > 0:
            change = ((data['price'] - data['prev']) / data['prev']) * 100
            if change > 0.5:
                reasons.append(f"Momentum +{change:.2f}%")
        
        if data['volume'] > 10000000:
            reasons.append("High liquidity")
        elif data['volume'] > 5000000:
            reasons.append("Strong volume")
        
        if 50 < data['price'] < 300:
            reasons.append("Optimal price")
        
        if score >= 85:
            reasons.append("Excellent signal")
        elif score >= 75:
            reasons.append("Strong setup")
        
        return reasons[0] if reasons else "Quality pick"
    
    def signals_left(self):
        """Calculate signals left today"""
        ist = timezone(timedelta(hours=5, minutes=30))
        now = datetime.now(ist)
        
        if now.hour >= 19:
            mins = (24 - now.hour) * 60 - now.minute + 90
        elif now.hour < 1:
            mins = (1 - now.hour) * 60 - now.minute + 30
        elif now.hour == 1 and now.minute < 30:
            mins = 30 - now.minute
        else:
            return 0
        
        return max(1, (mins // 30) + 1)
    
    def scan(self):
        """Scan all stocks from API"""
        self.log(f"🔍 Scanning {len(self.stocks)} stocks...")
        found = 0
        for symbol in self.stocks:
            try:
                data = self.get_stock(symbol)
                if data:
                    score = self.score_stock(symbol, data)
                    self.stocks_analysis[symbol] = {
                        'score': score, 'price': data['price'], 
                        'volume': data['volume'], 'prev': data['prev']
                    }
                    found += 1
                time.sleep(0.6)
            except:
                pass
        self.log(f"✅ Analyzed {found}/{len(self.stocks)} stocks")
    
    def monitor(self):
        """Monitor open positions for exits"""
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
                    self.sell(symbol, entry, price, profit, "🎉 TARGET HIT")
                    to_close.append(symbol)
                elif (now - pos['time']).days >= 7:
                    profit = ((price - entry) / entry) * 100
                    self.sell(symbol, entry, price, profit, "⏰ 7-DAY EXIT")
                    to_close.append(symbol)
            except:
                pass
        
        for s in to_close:
            del self.open_positions[s]
    
    def sell(self, symbol, entry, exit_price, profit, reason):
        """Send SELL signal to Discord"""
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
            self.log(f"📤 SELL: {symbol} | ${entry:.2f}→${exit_price:.2f} ({profit:+.2f}%)")
            self.closed_positions[symbol] = {
                'symbol': symbol, 'entry': entry, 'exit': exit_price, 'profit': profit
            }
        except:
            pass
    
    def buy(self, symbol, data, score):
        """Send BUY signal to Discord"""
        price = data['price']
        target = price * 1.035
        left = self.signals_left()
        logo = self.get_logo(symbol)
        reason = self.why_buy(symbol, data, score)
        
        self.open_positions[symbol] = {
            'entry': price, 'target': target, 'time': datetime.now()
        }
        self.block(symbol)
        
        embed = {
            "title": f"🟢 MANGO_BOT BUY: {symbol}",
            "description": f"⏰ {datetime.now(timezone(timedelta(hours=5, minutes=30))).strftime('%H:%M IST')}",
            "color": 3066993,
            "thumbnail": {
                "url": logo,
                "height": 100,
                "width": 100
            },
            "fields": [
                {"name": "📍 Entry", "value": f"${price:.2f}", "inline": True},
                {"name": "🎯 Target", "value": f"${target:.2f} (+3.5%)", "inline": True},
                {"name": "⭐ Score", "value": f"{score}/100", "inline": True},
                {"name": "💡 Why to Buy", "value": reason, "inline": False},
                {"name": "📢 Signals Left", "value": f"{left} more today! ⏰", "inline": True},
                {"name": "💰 Auto Sell", "value": "At target!", "inline": True},
                {"name": "🔒 Blocked", "value": "7 days (no repeat)", "inline": True}
            ],
            "footer": {"text": "🥭 Mango_Bot - Auto Signals & Auto Exits"}
        }
        
        try:
            requests.post(self.webhook, json={'embeds': [embed]}, timeout=10)
            self.log(f"📱 BUY: {symbol} @ ${price:.2f} | Score: {score} | {left} signals left!")
        except:
            self.log("❌ Discord error")
    
    def daily_analytics(self):
        """Send daily analytics at market close"""
        if not self.closed_positions:
            self.log("📊 No trades today")
            self.last_analytics_sent = datetime.now()
            return
        
        total = len(self.closed_positions)
        wins = sum(1 for p in self.closed_positions.values() if p.get('profit', 0) > 0)
        losses = total - wins
        win_rate = (wins / total * 100) if total > 0 else 0
        
        total_pnl = sum(p.get('profit', 0) for p in self.closed_positions.values())
        avg_pnl = total_pnl / total if total > 0 else 0
        
        best = max(self.closed_positions.values(), key=lambda x: x.get('profit', 0), default={})
        worst = min(self.closed_positions.values(), key=lambda x: x.get('profit', 0), default={})
        
        embed = {
            "title": "📊 MANGO_BOT - DAILY ANALYTICS",
            "description": f"⏰ {datetime.now(timezone(timedelta(hours=5, minutes=30))).strftime('%Y-%m-%d')} IST",
            "color": 3066993,
            "fields": [
                {"name": "📈 Total Trades", "value": f"{total}", "inline": True},
                {"name": "✅ Win Rate", "value": f"{win_rate:.1f}% ({wins}W/{losses}L)", "inline": True},
                {"name": "💰 Daily P&L", "value": f"{total_pnl:+.2f}%", "inline": True},
                {"name": "📊 Avg Per Trade", "value": f"{avg_pnl:+.2f}%", "inline": True},
                {"name": "🏆 Best Trade", "value": f"{best.get('symbol', 'N/A')}: +{best.get('profit', 0):.2f}%" if best else "N/A", "inline": True},
                {"name": "❌ Worst Trade", "value": f"{worst.get('symbol', 'N/A')}: {worst.get('profit', 0):.2f}%" if worst else "N/A", "inline": True}
            ],
            "footer": {"text": "🥭 Mango_Bot - Market Close Report"}
        }
        
        try:
            requests.post(self.webhook, json={'embeds': [embed]}, timeout=10)
            self.log(f"📊 DAILY ANALYTICS: {total} trades, {win_rate:.1f}% win rate, {total_pnl:+.2f}% P&L ✅")
            self.last_analytics_sent = datetime.now()
        except:
            self.log("❌ Failed to send analytics")
    
    def is_open(self):
        """Check if market is open (7 PM - 1:30 AM IST)"""
        ist = timezone(timedelta(hours=5, minutes=30))
        now = datetime.now(ist)
        open_market = (now.hour >= 19) or (now.hour < 1) or (now.hour == 1 and now.minute < 30)
        weekday = now.weekday() < 5
        return weekday and open_market
    
    def is_market_close(self):
        """Check if market closed (1:30 AM - 2:00 AM) and not sent yet today"""
        ist = timezone(timedelta(hours=5, minutes=30))
        now = datetime.now(ist)
        
        # Analytics window: 1:30 AM - 2:00 AM
        is_close_time = now.hour == 1 and now.minute >= 30
        
        # Check if already sent today
        if self.last_analytics_sent:
            time_since = now - self.last_analytics_sent
            if time_since.days == 0:  # Same day
                return False
        
        return is_close_time
    
    def run(self):
        """Main bot loop"""
        cycle = 0
        while True:
            try:
                cycle += 1
                self.log(f"\n🔄 CYCLE #{cycle}")
                
                if self.is_open():
                    self.scan()
                    self.monitor()
                    left = self.signals_left()
                    self.log(f"📊 Open: {len(self.open_positions)} | {left} signals left today")
                    
                    elapsed = datetime.now() - self.last_signal
                    if elapsed >= timedelta(minutes=30):
                        available = {s: d for s, d in self.stocks_analysis.items() if not self.is_blocked(s)}
                        if available:
                            best = max(available.items(), key=lambda x: x[1]['score'])
                            self.buy(best[0], best[1], best[1]['score'])
                            self.last_signal = datetime.now()
                        else:
                            self.log("⚠️ All stocks blocked")
                    else:
                        mins = 30 - int(elapsed.total_seconds() / 60)
                        self.log(f"⏳ Next signal in {mins} min | {left} signals left!")
                elif self.is_market_close():
                    self.log("🏁 MARKET CLOSED - SENDING DAILY ANALYTICS")
                    self.daily_analytics()
                    self.closed_positions = {}
                else:
                    self.log("😴 Market closed")
                
                self.log("⏱️ Next check in 5 min")
                time.sleep(300)
            except Exception as e:
                self.log(f"❌ ERROR: {e}")
                time.sleep(60)

if __name__ == "__main__":
    bot = MangoBot()
    bot.run()
