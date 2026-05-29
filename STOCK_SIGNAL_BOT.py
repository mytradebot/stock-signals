#!/usr/bin/env python3
"""
🥭 MANGO_BOT PRO - ULTIMATE VERSION
Pre-market analysis | Market sentiment | Daily recommendations | Compared with yesterday
"""
import os, time, json
from datetime import datetime, timedelta, timezone
import requests

class MangoBotPro:
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
        
        # Indices for market sentiment
        self.indices = ['SPY', 'QQQ', 'DIA', 'VIX']
        
        self.stocks_analysis = {}
        self.open_positions = {}
        self.closed_positions = {}
        self.yesterday_data = {}
        self.last_signal = datetime.now() - timedelta(minutes=31)
        self.blocked_stocks = {}
        self.last_analytics_sent = None
        self.premarket_sent = False
        
        self.load_blocked()
        self.load_yesterday()
        
        self.log("=" * 70)
        self.log("🥭 MANGO_BOT PRO - ULTIMATE VERSION")
        self.log("📊 Pre-market sentiment | Smart recommendations | Yesterday comparison")
        self.log("🚀 Auto buy/sell | 7-day block | Daily analytics | IST timezone")
        self.log("=" * 70)
    
    def log(self, msg):
        ist = timezone(timedelta(hours=5, minutes=30))
        ts = datetime.now(ist).strftime("%Y-%m-%d %H:%M:%S IST")
        print(f"[{ts}] {msg}")
    
    def load_blocked(self):
        """Load 7-day blocked stocks"""
        try:
            paths = ['/home/claude/blocked.json', '/tmp/blocked.json', './blocked.json']
            for path in paths:
                if os.path.exists(path):
                    with open(path, 'r') as f:
                        data = json.load(f)
                        for symbol, ts in data.items():
                            self.blocked_stocks[symbol] = datetime.fromisoformat(ts)
                    self.log(f"✅ Loaded blocked stocks")
                    return
        except:
            pass
    
    def save_blocked(self):
        """Save blocked stocks"""
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
    
    def load_yesterday(self):
        """Load yesterday's data for comparison"""
        try:
            if os.path.exists('./yesterday.json'):
                with open('./yesterday.json', 'r') as f:
                    self.yesterday_data = json.load(f)
                    self.log(f"✅ Loaded yesterday's data")
        except:
            pass
    
    def save_yesterday(self):
        """Save today's data as yesterday for tomorrow"""
        try:
            today_data = {
                'date': datetime.now(timezone(timedelta(hours=5, minutes=30))).strftime('%Y-%m-%d'),
                'closed_positions': self.closed_positions,
                'total_trades': len(self.closed_positions),
                'win_rate': self.get_win_rate(),
                'daily_pnl': sum(p.get('profit', 0) for p in self.closed_positions.values())
            }
            with open('./yesterday.json', 'w') as f:
                json.dump(today_data, f)
        except:
            pass
    
    def get_stock(self, symbol):
        """Get stock data from Finnhub"""
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
    
    def get_market_sentiment(self):
        """Analyze market sentiment using indices"""
        self.log("📈 Analyzing market sentiment...")
        spy = self.get_stock('SPY')
        qqq = self.get_stock('QQQ')
        vix = self.get_stock('VIX')
        
        if not spy or not qqq or not vix:
            return "UNKNOWN", 0
        
        # Calculate changes
        spy_change = ((spy['price'] - spy['prev']) / spy['prev']) * 100
        qqq_change = ((qqq['price'] - qqq['prev']) / qqq['prev']) * 100
        vix_change = ((vix['price'] - vix['prev']) / vix['prev']) * 100
        
        # Determine sentiment
        bullish_score = 0
        if spy_change > 0.5:
            bullish_score += 1
        if qqq_change > 0.5:
            bullish_score += 1
        if vix_change < 0:  # Lower VIX = less fear = bullish
            bullish_score += 1
        
        sentiment = "🟢 BULLISH" if bullish_score >= 2 else ("🔴 BEARISH" if bullish_score == 0 else "🟡 NEUTRAL")
        
        return sentiment, (spy_change + qqq_change) / 2
    
    def premarket_check(self):
        """Send pre-market sentiment analysis (1 hour before market opens)"""
        ist = timezone(timedelta(hours=5, minutes=30))
        now = datetime.now(ist)
        
        # Pre-market: 6 PM - 6:05 PM IST
        is_premarket = now.hour == 18 and now.minute < 5
        
        if not is_premarket or self.premarket_sent:
            return
        
        sentiment, momentum = self.get_market_sentiment()
        
        embed = {
            "title": "🌅 MANGO_BOT - PRE-MARKET ANALYSIS",
            "description": f"⏰ {now.strftime('%H:%M IST')} | Market opens in 1 hour!",
            "color": 16776960 if "BULLISH" in sentiment else (15158332 if "BEARISH" in sentiment else 16776960),
            "fields": [
                {"name": "📊 Market Sentiment", "value": sentiment, "inline": True},
                {"name": "📈 Momentum", "value": f"{momentum:+.2f}%", "inline": True},
                {"name": "💡 Strategy", "value": "Ready for trading! Watch for early signals.", "inline": False},
                {"name": "🎯 Expected", "value": "13 signals today" if "BULLISH" in sentiment else "Fewer signals, higher quality", "inline": True}
            ],
            "footer": {"text": "🥭 Mango_Bot - Get Ready!"}
        }
        
        try:
            requests.post(self.webhook, json={'embeds': [embed]}, timeout=10)
            self.log(f"🌅 PRE-MARKET: {sentiment} | Momentum: {momentum:+.2f}%")
            self.premarket_sent = True
        except:
            pass
    
    def score_stock(self, symbol, data):
        """Calculate stock quality score"""
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
        """Get stock logo"""
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
        """Generate buy reason"""
        reasons = []
        if data['prev'] > 0:
            change = ((data['price'] - data['prev']) / data['prev']) * 100
            if change > 0.5:
                reasons.append(f"Momentum +{change:.2f}%")
        if data['volume'] > 10000000:
            reasons.append("High liquidity")
        if score >= 85:
            reasons.append("Excellent signal")
        return reasons[0] if reasons else "Quality pick"
    
    def signals_left(self):
        """Calculate signals left"""
        ist = timezone(timedelta(hours=5, minutes=30))
        now = datetime.now(ist)
        if now.hour >= 19:
            mins = (24 - now.hour) * 60 - now.minute + 90
        elif now.hour < 1:
            mins = (1 - now.hour) * 60 - now.minute + 30
        else:
            return 0
        return max(1, (mins // 30) + 1)
    
    def is_blocked(self, symbol):
        """Check if blocked"""
        if symbol not in self.blocked_stocks:
            return False
        days = (datetime.now() - self.blocked_stocks[symbol]).days
        if days >= 7:
            del self.blocked_stocks[symbol]
            self.save_blocked()
            return False
        return True
    
    def block(self, symbol):
        """Block stock"""
        self.blocked_stocks[symbol] = datetime.now()
        self.save_blocked()
    
    def scan(self):
        """Scan all stocks"""
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
        """Monitor positions"""
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
        """Send sell signal"""
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
            self.closed_positions[symbol] = {
                'symbol': symbol, 'entry': entry, 'exit': exit_price, 'profit': profit
            }
            self.log(f"📤 SELL: {symbol} ({profit:+.2f}%)")
        except:
            pass
    
    def buy(self, symbol, data, score):
        """Send buy signal"""
        price = data['price']
        target = price * 1.035
        left = self.signals_left()
        logo = self.get_logo(symbol)
        reason = self.why_buy(symbol, data, score)
        
        self.open_positions[symbol] = {'entry': price, 'target': target, 'time': datetime.now()}
        self.block(symbol)
        
        embed = {
            "title": f"🟢 MANGO_BOT BUY: {symbol}",
            "description": f"⏰ {datetime.now(timezone(timedelta(hours=5, minutes=30))).strftime('%H:%M IST')}",
            "color": 3066993,
            "thumbnail": {"url": logo, "height": 100, "width": 100},
            "fields": [
                {"name": "📍 Entry", "value": f"${price:.2f}", "inline": True},
                {"name": "🎯 Target", "value": f"${target:.2f} (+3.5%)", "inline": True},
                {"name": "⭐ Score", "value": f"{score}/100", "inline": True},
                {"name": "💡 Why", "value": reason, "inline": False},
                {"name": "📢 Signals", "value": f"{left} left! ⏰", "inline": True},
                {"name": "🔒 Blocked", "value": "7 days", "inline": True}
            ],
            "footer": {"text": "🥭 Mango_Bot Pro"}
        }
        try:
            requests.post(self.webhook, json={'embeds': [embed]}, timeout=10)
            self.log(f"📱 BUY: {symbol} @ ${price:.2f}")
        except:
            pass
    
    def get_win_rate(self):
        """Calculate win rate"""
        if not self.closed_positions:
            return 0
        wins = sum(1 for p in self.closed_positions.values() if p.get('profit', 0) > 0)
        return (wins / len(self.closed_positions)) * 100
    
    def daily_analytics(self):
        """Send daily analytics with recommendations"""
        ist = timezone(timedelta(hours=5, minutes=30))
        now = datetime.now(ist)
        
        if not self.closed_positions:
            self.log("📊 No trades today")
            self.last_analytics_sent = datetime.now(ist)
            return
        
        total = len(self.closed_positions)
        wins = sum(1 for p in self.closed_positions.values() if p.get('profit', 0) > 0)
        losses = total - wins
        win_rate = (wins / total * 100) if total > 0 else 0
        total_pnl = sum(p.get('profit', 0) for p in self.closed_positions.values())
        avg_pnl = total_pnl / total if total > 0 else 0
        
        # Best and worst stocks
        best = max(self.closed_positions.values(), key=lambda x: x.get('profit', 0), default={})
        worst = min(self.closed_positions.values(), key=lambda x: x.get('profit', 0), default={})
        
        # Recommend best performing stocks
        top_stocks = sorted(self.closed_positions.values(), key=lambda x: x.get('profit', 0), reverse=True)[:3]
        recommendations = ", ".join([f"{s.get('symbol', 'N/A')}" for s in top_stocks])
        
        # Compare with yesterday
        yesterday_pnl = self.yesterday_data.get('daily_pnl', 0) if self.yesterday_data else 0
        pnl_change = total_pnl - yesterday_pnl
        comparison = f"+{pnl_change:.2f}%" if pnl_change >= 0 else f"{pnl_change:.2f}%"
        
        embed = {
            "title": "📊 MANGO_BOT PRO - DAILY ANALYTICS & RECOMMENDATIONS",
            "description": f"⏰ {now.strftime('%Y-%m-%d')} IST | Market Close Report",
            "color": 3066993,
            "fields": [
                {"name": "📈 Today's Performance", "value": f"Trades: {total} | Win Rate: {win_rate:.1f}%", "inline": True},
                {"name": "💰 P&L", "value": f"{total_pnl:+.2f}% | Avg: {avg_pnl:+.2f}%", "inline": True},
                {"name": "📊 vs Yesterday", "value": f"{comparison} ({yesterday_pnl:+.2f}% yesterday)", "inline": True},
                {"name": "🏆 Best Stock", "value": f"{best.get('symbol', 'N/A')}: +{best.get('profit', 0):.2f}%", "inline": True},
                {"name": "❌ Worst Stock", "value": f"{worst.get('symbol', 'N/A')}: {worst.get('profit', 0):.2f}%", "inline": True},
                {"name": "✅ Win/Loss", "value": f"{wins}W / {losses}L", "inline": True},
                {"name": "🎯 Tomorrow Recommendations", "value": f"Watch: {recommendations}", "inline": False},
                {"name": "💡 Strategy", "value": "Keep trading best performers! Follow the winners!", "inline": False}
            ],
            "footer": {"text": "🥭 Mango_Bot Pro - Smart Analysis & Recommendations"}
        }
        
        try:
            requests.post(self.webhook, json={'embeds': [embed]}, timeout=10)
            self.log(f"📊 ANALYTICS: {total} trades, {win_rate:.1f}% win, {total_pnl:+.2f}% P&L vs yesterday {comparison}")
            self.last_analytics_sent = datetime.now(ist)
            self.save_yesterday()
        except:
            self.log("❌ Failed to send analytics")
    
    def is_premarket_time(self):
        """Check pre-market (6 PM IST)"""
        ist = timezone(timedelta(hours=5, minutes=30))
        now = datetime.now(ist)
        return now.hour == 18 and now.minute < 5
    
    def is_open(self):
        """Check if market open"""
        ist = timezone(timedelta(hours=5, minutes=30))
        now = datetime.now(ist)
        open_market = (now.hour >= 19) or (now.hour < 1) or (now.hour == 1 and now.minute < 30)
        weekday = now.weekday() < 5
        return weekday and open_market
    
    def is_market_close(self):
        """Check market close"""
        ist = timezone(timedelta(hours=5, minutes=30))
        now = datetime.now(ist)
        is_close_time = now.hour == 1 and now.minute >= 30
        if self.last_analytics_sent:
            if self.last_analytics_sent.tzinfo is None:
                last_sent_ist = self.last_analytics_sent.replace(tzinfo=ist)
            else:
                last_sent_ist = self.last_analytics_sent.astimezone(ist)
            time_since = now - last_sent_ist
            if time_since.days == 0:
                return False
        return is_close_time
    
    def run(self):
        """Main loop"""
        cycle = 0
        while True:
            try:
                cycle += 1
                self.log(f"\n🔄 CYCLE #{cycle}")
                
                # Pre-market check
                if self.is_premarket_time():
                    self.premarket_check()
                
                # Market hours
                if self.is_open():
                    self.premarket_sent = False
                    self.scan()
                    self.monitor()
                    left = self.signals_left()
                    self.log(f"📊 Open: {len(self.open_positions)} | {left} signals left")
                    
                    elapsed = datetime.now() - self.last_signal
                    if elapsed >= timedelta(minutes=30):
                        available = {s: d for s, d in self.stocks_analysis.items() if not self.is_blocked(s)}
                        if available:
                            best = max(available.items(), key=lambda x: x[1]['score'])
                            self.buy(best[0], best[1], best[1]['score'])
                            self.last_signal = datetime.now()
                    else:
                        mins = 30 - int(elapsed.total_seconds() / 60)
                        self.log(f"⏳ Next signal in {mins} min")
                
                # Market close
                elif self.is_market_close():
                    self.log("🏁 MARKET CLOSED - SENDING ANALYTICS")
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
    bot = MangoBotPro()
    bot.run()
