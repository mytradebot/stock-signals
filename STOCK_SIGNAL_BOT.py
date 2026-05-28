#!/usr/bin/env python3
"""
MANGO_BOT - COMPLETE TRADING SYSTEM
✅ Market momentum at 8:30 AM (1 hour early)
✅ Buy signals every 3 min with logos
✅ Auto-sell signals (target/stop/time)
✅ Daily analytics at 4 PM
✅ Best stocks alert at 4 PM
✅ Bot sleeps after market close
"""

import os
import time
import json
from datetime import datetime, timedelta

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
        
        # 100 BEST STOCKS (Quality over quantity)
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
        self.blocked_stocks = {}  # Stocks blocked for 7 days
        
        # Load blocked stocks from file
        self.load_blocked_stocks()
        
        self.log("=" * 70)
        self.log("🥭 MANGO_BOT - COMPLETE TRADING SYSTEM")
        self.log("📊 100 BEST STOCKS → 1 BEST signal per 3 min")
        self.log("📈 Auto buy/sell + Daily analytics + Best stocks alert")
        self.log("⚡ Smart schedule: 8:30 AM - 4 PM, then sleep")
        self.log("=" * 70)
    
    def load_blocked_stocks(self):
        """Load blocked stocks from file"""
        try:
            if os.path.exists('/home/claude/blocked_stocks.txt'):
                with open('/home/claude/blocked_stocks.txt', 'r') as f:
                    for line in f:
                        symbol, timestamp_str = line.strip().split(',')
                        self.blocked_stocks[symbol] = datetime.fromisoformat(timestamp_str)
                self.log(f"   ✅ Loaded {len(self.blocked_stocks)} blocked stocks")
        except:
            pass
    
    def save_blocked_stocks(self):
        """Save blocked stocks to file"""
        try:
            with open('/home/claude/blocked_stocks.txt', 'w') as f:
                for symbol, timestamp in self.blocked_stocks.items():
                    f.write(f"{symbol},{timestamp.isoformat()}\n")
        except:
            pass
    
    def is_stock_blocked(self, symbol):
        """Check if stock is blocked (recommended in last 7 days)"""
        if symbol not in self.blocked_stocks:
            return False
        
        # Check if 7 days passed
        blocked_time = self.blocked_stocks[symbol]
        now = datetime.now()
        days_passed = (now - blocked_time).days
        
        if days_passed >= 7:
            # Unblock it
            del self.blocked_stocks[symbol]
            self.save_blocked_stocks()
            return False
        
        return True
    
    def block_stock(self, symbol):
        """Block stock for 7 days after sending signal"""
        self.blocked_stocks[symbol] = datetime.now()
        self.save_blocked_stocks()
        from datetime import timezone, timedelta
        ist = timezone(timedelta(hours=5, minutes=30))
        ts = datetime.now(ist).strftime("%Y-%m-%d %H:%M:%S IST")
        print(f"[{ts}] {msg}")
    
    def get_stock_data(self, symbol):
        """Get stock data from Finnhub"""
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
    
    def get_stock_logo(self, symbol):
        """Get stock logo URL from Finnhub"""
        try:
            url = f"https://finnhub.io/api/v1/stock/profile2?symbol={symbol}&token={self.finnhub_key}"
            response = requests.get(url, timeout=5)
            data = response.json()
            if 'logo' in data and data['logo']:
                return data['logo']
        except:
            pass
        
        return f"https://logo.clearbit.com/{symbol}.com"
    
    def analyze_stock(self, symbol, data):
        """Analyze stock and give score 0-100"""
        if not data:
            return 0
        
        score = 0
        
        # Volume score (0-25)
        volume = data['volume']
        if volume > 10000000:
            score += 25
        elif volume > 5000000:
            score += 20
        elif volume > 1000000:
            score += 15
        elif volume > 500000:
            score += 10
        
        # Price level score (0-25)
        price = data['price']
        if 50 < price < 300:
            score += 25
        elif 20 < price <= 50 or 300 <= price < 500:
            score += 20
        elif price > 500:
            score += 15
        
        # Momentum score (0-25)
        prev_close = data['prev_close']
        if prev_close > 0:
            change = ((price - prev_close) / prev_close) * 100
            if 0.5 <= change <= 3:
                score += 25
            elif 0 < change < 0.5:
                score += 15
            elif -1 < change < 0:
                score += 10
        
        # Volatility score (0-25)
        high = data['high']
        low = data['low']
        if high > 0 and low > 0:
            volatility = ((high - low) / price) * 100
            if 0.5 <= volatility <= 2:
                score += 25
            elif 0.2 <= volatility < 0.5:
                score += 15
            elif volatility > 2:
                score += 10
        
        return min(score, 100)
    
    def scan(self):
        """Scan 100 best stocks - with delay to respect Finnhub rate limit"""
        self.log(f"🔍 Analyzing {len(self.stocks)} best stocks...")
        
        found = 0
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
                
                time.sleep(0.6)  # 600ms delay between calls (respects 60/min limit)
            except:
                pass
        
        self.log(f"   ✅ Analyzed {found} stocks")
    
    def get_target_percentage(self, symbol):
        """Get profit target based on stock volatility and risk"""
        
        # High volatility tech - can move more
        high_volatility = ['NVDA', 'TSLA', 'AMD', 'ROKU', 'UPST', 'SNOW', 'CRWD', 'DDOG', 'PLTR', 'RIOT']
        
        # Regular growth stocks
        growth_stocks = ['MSFT', 'GOOGL', 'AMZN', 'META', 'ADBE', 'SHOP', 'ASML', 'QCOM', 'INTU', 'PYPL']
        
        # Stable blue chips - smaller moves
        stable_stocks = ['AAPL', 'JNJ', 'WMT', 'PG', 'HD', 'MCD', 'COST', 'V', 'MA', 'JPM']
        
        # High risk/reward stocks
        risky_stocks = ['BABA', 'JD', 'BILI', 'MARA', 'RIOT', 'BLNK', 'LCID']
        
        if symbol in high_volatility:
            return 3.5  # 3.5% target for volatile stocks
        elif symbol in growth_stocks:
            return 2.5  # 2.5% target for growth
        elif symbol in stable_stocks:
            return 1.8  # 1.8% target for stable
        elif symbol in risky_stocks:
            return 4.0  # 4% target for high risk/reward
        else:
            return 2.5  # Default 2.5%
    
    def get_stop_percentage(self, symbol):
        """Get stop loss based on stock risk"""
        
        high_volatility = ['NVDA', 'TSLA', 'AMD', 'ROKU', 'UPST', 'SNOW', 'CRWD', 'DDOG', 'PLTR', 'RIOT']
        stable_stocks = ['AAPL', 'JNJ', 'WMT', 'PG', 'HD', 'MCD', 'COST', 'V', 'MA', 'JPM']
        
        if symbol in high_volatility:
            return 2.0  # -2% stop for volatile
        elif symbol in stable_stocks:
            return 1.2  # -1.2% stop for stable
        else:
            return 1.5  # -1.5% default stop
        """Calculate how many signals left today"""
        from datetime import timezone
        edt = timezone(timedelta(hours=-4))
        now = datetime.now(edt)
        
        if now.hour >= 16:
            return 0
        
        minutes_until_close = (16 - now.hour) * 60 - now.minute
        signals_remaining = (minutes_until_close // 30)
        
        return max(0, signals_remaining)
    
    def get_why_to_buy(self, data, score):
        """Generate short reason why to buy this stock"""
        reasons = []
        
        price = data['price']
        volume = data['volume']
        prev_close = data['prev_close']
        
        if prev_close > 0:
            change = ((price - prev_close) / prev_close) * 100
            if change > 0.5:
                reasons.append(f"Building momentum (+{change:.2f}%)")
        
        if volume > 10000000:
            reasons.append("Very high liquidity")
        elif volume > 5000000:
            reasons.append("Strong volume")
        
        if 50 < price < 300:
            reasons.append("Optimal price range")
        
        if score >= 90:
            reasons.append("Excellent quality signal")
        elif score >= 80:
            reasons.append("High quality setup")
        
        return reasons[0] if reasons else "Quality signal identified"
    
    def send_buy_signal(self, symbol, data, score):
        """Send BUY signal to Discord with dynamic targets per stock"""
        price = data['price']
        
        # Get dynamic target based on stock
        target_pct = self.get_target_percentage(symbol) / 100
        stop_pct = self.get_stop_percentage(symbol) / 100
        
        target = price * (1 + target_pct)
        stop = price * (1 - stop_pct)
        target_pct_display = self.get_target_percentage(symbol)
        stop_pct_display = self.get_stop_percentage(symbol)
        
        logo_url = self.get_stock_logo(symbol)
        
        signals_left = self.get_remaining_signals()
        why_to_buy = self.get_why_to_buy(data, score)
        
        self.open_positions[symbol] = {
            'entry_price': price,
            'target': target,
            'stop': stop,
            'entry_time': datetime.now(),
            'timeframe': 7,
            'score': score
        }
        
        embed = {
            "title": f"🟢 MANGO_BOT BUY: {symbol}",
            "description": f"⏰ {datetime.now(timezone(timedelta(hours=5, minutes=30))).strftime('%H:%M IST')}",
            "color": 3066993,
            "thumbnail": {
                "url": logo_url,
                "height": 100,
                "width": 100
            },
            "fields": [
                {
                    "name": "📍 Entry Price",
                    "value": f"${price:.2f}",
                    "inline": True
                },
                {
                    "name": "🎯 Target Profit",
                    "value": f"${target:.2f} (+{target_pct_display:.1f}%)",
                    "inline": True
                },
                {
                    "name": "🛑 Stop Loss",
                    "value": f"${stop:.2f} (-{stop_pct_display:.1f}%)",
                    "inline": True
                },
                {
                    "name": "⭐ Quality Score",
                    "value": f"{score}/100 ⭐",
                    "inline": True
                },
                {
                    "name": "💡 Why to Buy",
                    "value": why_to_buy,
                    "inline": False
                },
                {
                    "name": "📊 Liquidity",
                    "value": f"{data['volume']/1000000:.1f}M shares",
                    "inline": True
                },
                {
                    "name": "⏳ Hold Duration",
                    "value": "2-7 days max",
                    "inline": True
                },
                {
                    "name": "📢 Signals Left Today",
                    "value": f"{signals_left} more signals! ⏰",
                    "inline": True
                },
                {
                    "name": "✅ Auto Management",
                    "value": "Auto-sell on target/stop/time",
                    "inline": True
                }
            ],
            "footer": {
                "text": "🥭 Mango_Bot - Auto Signals & Auto Exits | Sells within 5 min of target!"
            }
        }
        
        try:
            requests.post(self.webhook, json={'embeds': [embed]}, timeout=10)
            # Block this stock for 7 days
            self.block_stock(symbol)
            self.log(f"📱 BUY SIGNAL: {symbol} @ ${price:.2f} → Target: ${target:.2f} (+{target_pct_display:.1f}%) | {signals_left} signals left | BLOCKED for 7 days")
        except:
            self.log("❌ Discord error")
    
    def monitor_positions(self):
        """Monitor open positions and send SELL signals"""
        closed = []
        
        for symbol, pos in list(self.open_positions.items()):
            try:
                data = self.get_stock_data(symbol)
                if not data:
                    continue
                
                current_price = data['price']
                entry = pos['entry_price']
                target = pos['target']
                stop = pos['stop']
                entry_time = pos['entry_time']
                logo_url = self.get_stock_logo(symbol)
                
                embed = None
                
                if current_price >= target:
                    pnl = ((current_price - entry) / entry) * 100
                    embed = {
                        "title": f"🎉 SELL - TARGET HIT!",
                        "description": f"{symbol}",
                        "color": 3066993,
                        "thumbnail": {"url": logo_url, "height": 100, "width": 100},
                        "fields": [
                            {"name": "Entry → Exit", "value": f"${entry:.2f} → ${current_price:.2f}", "inline": False},
                            {"name": "Profit", "value": f"+{pnl:.2f}% ✅", "inline": True},
                            {"name": "Status", "value": "TAKE PROFIT!", "inline": True}
                        ]
                    }
                    
                    self.closed_positions[symbol] = {'entry': entry, 'exit': current_price, 'pnl': pnl, 'reason': 'TARGET_HIT'}
                    closed.append(symbol)
                
                elif current_price <= stop:
                    pnl = ((current_price - entry) / entry) * 100
                    embed = {
                        "title": f"⛔ SELL - STOP HIT",
                        "description": f"{symbol}",
                        "color": 15158332,
                        "thumbnail": {"url": logo_url, "height": 100, "width": 100},
                        "fields": [
                            {"name": "Entry → Exit", "value": f"${entry:.2f} → ${current_price:.2f}", "inline": False},
                            {"name": "Loss", "value": f"{pnl:.2f}% ❌", "inline": True},
                            {"name": "Status", "value": "CUT LOSS", "inline": True}
                        ]
                    }
                    
                    self.closed_positions[symbol] = {'entry': entry, 'exit': current_price, 'pnl': pnl, 'reason': 'STOP_HIT'}
                    closed.append(symbol)
                
                elif (datetime.now() - entry_time).days >= pos['timeframe']:
                    pnl = ((current_price - entry) / entry) * 100
                    embed = {
                        "title": f"⏰ SELL - TIME EXPIRED",
                        "description": f"{symbol}",
                        "color": 15844367,
                        "thumbnail": {"url": logo_url, "height": 100, "width": 100},
                        "fields": [
                            {"name": "Entry → Exit", "value": f"${entry:.2f} → ${current_price:.2f}", "inline": False},
                            {"name": "Return", "value": f"{pnl:+.2f}%", "inline": True},
                            {"name": "Status", "value": "7 DAY HOLD DONE", "inline": True}
                        ]
                    }
                    
                    self.closed_positions[symbol] = {'entry': entry, 'exit': current_price, 'pnl': pnl, 'reason': 'TIME_EXPIRED'}
                    closed.append(symbol)
                
                if embed:
                    try:
                        requests.post(self.webhook, json={'embeds': [embed]}, timeout=10)
                    except:
                        pass
            
            except:
                pass
        
        for symbol in closed:
            del self.open_positions[symbol]
    
    def check_market_momentum(self):
        """Check market momentum at 8:30 AM (1 hour before market opens)"""
        try:
            spy_data = self.get_stock_data('SPY')
            qqq_data = self.get_stock_data('QQQ')
            vix_data = self.get_stock_data('VIX')
            
            if not spy_data or not qqq_data:
                return None
            
            spy_change = ((spy_data['price'] - spy_data['prev_close']) / spy_data['prev_close']) * 100
            qqq_change = ((qqq_data['price'] - qqq_data['prev_close']) / qqq_data['prev_close']) * 100
            vix_price = vix_data['price'] if vix_data else 20
            
            avg_change = (spy_change + qqq_change) / 2
            
            if avg_change > 1:
                sentiment = "🚀 BULLISH"
                color = 3066993
                message = "Today is a GREAT day to invest! Market opening STRONG 📈"
                emoji = "🟢"
                strategy = "✅ Aggressive - Take signals with confidence!"
            elif avg_change > 0.3:
                sentiment = "📈 POSITIVE"
                color = 3066993
                message = "Good momentum today! Markets looking positive 📊"
                emoji = "🟢"
                strategy = "✅ Normal - Standard trading. Follow all signals."
            elif avg_change > -0.3:
                sentiment = "➡️ NEUTRAL"
                color = 16776960
                message = "Markets are neutral today. Be cautious with entries 🔍"
                emoji = "🟡"
                strategy = "⚠️ Cautious - Only take high-quality signals (90+)."
            elif avg_change > -1:
                sentiment = "📉 BEARISH"
                color = 15158332
                message = "Markets struggling today. Wait for better entries ⛔"
                emoji = "🔴"
                strategy = "❌ Selective - Only trade proven patterns."
            else:
                sentiment = "🔴 VERY BEARISH"
                color = 15158332
                message = "Strong selling pressure today. SKIP trading ⛔"
                emoji = "🔴"
                strategy = "❌ SKIP - Avoid trading today."
            
            embed = {
                "title": f"{emoji} MANGO_BOT - MARKET MOMENTUM",
                "description": f"📅 {datetime.now().strftime('%A, %B %d, %Y')} | 1 Hour Before Market",
                "color": color,
                "fields": [
                    {"name": "📊 Market Sentiment", "value": sentiment, "inline": True},
                    {"name": "📈 S&P 500 (SPY)", "value": f"{spy_change:+.2f}%", "inline": True},
                    {"name": "💻 Nasdaq (QQQ)", "value": f"{qqq_change:+.2f}%", "inline": True},
                    {"name": "😰 Market Fear (VIX)", "value": f"{vix_price:.1f}" + (" HIGH" if vix_price > 25 else ""), "inline": True},
                    {"name": "💡 Today's Action", "value": message, "inline": False},
                    {"name": "🎯 Strategy", "value": strategy, "inline": False}
                ],
                "footer": {"text": "🥭 Mango_Bot - Market Outlook | Happy Trading!"}
            }
            
            try:
                requests.post(self.webhook, json={'embeds': [embed]}, timeout=10)
                self.log(f"📈 Market momentum sent! Sentiment: {sentiment}")
            except:
                self.log("❌ Discord error")
        
        except Exception as e:
            self.log(f"❌ Error checking momentum: {e}")
    
    def calculate_stock_performance(self):
        """Calculate win rate per stock"""
        stock_stats = {}
        
        for symbol, trade in self.closed_positions.items():
            if symbol not in stock_stats:
                stock_stats[symbol] = {'total': 0, 'wins': 0, 'losses': 0, 'avg_pnl': 0, 'total_pnl': 0}
            
            stock_stats[symbol]['total'] += 1
            if trade['pnl'] > 0:
                stock_stats[symbol]['wins'] += 1
            else:
                stock_stats[symbol]['losses'] += 1
            stock_stats[symbol]['total_pnl'] += trade['pnl']
        
        for symbol in stock_stats:
            total = stock_stats[symbol]['total']
            if total > 0:
                stock_stats[symbol]['win_rate'] = (stock_stats[symbol]['wins'] / total) * 100
                stock_stats[symbol]['avg_pnl'] = stock_stats[symbol]['total_pnl'] / total
            else:
                stock_stats[symbol]['win_rate'] = 0
                stock_stats[symbol]['avg_pnl'] = 0
        
        return stock_stats
    
    def send_daily_analytics(self):
        """Send daily analytics at 4:00 PM"""
        if not self.closed_positions:
            embed = {
                "title": "📊 MANGO_BOT - DAILY ANALYTICS",
                "description": f"{datetime.now().strftime('%A, %B %d, %Y')}",
                "color": 15158332,
                "fields": [{"name": "Total Trades", "value": "0", "inline": True},
                           {"name": "Win Rate", "value": "N/A", "inline": True},
                           {"name": "Daily P&L", "value": "No trades today", "inline": True}],
                "footer": {"text": "🥭 Mango_Bot - Market Close Report"}
            }
        else:
            total_trades = len(self.closed_positions)
            winners = sum(1 for p in self.closed_positions.values() if p['pnl'] > 0)
            losers = sum(1 for p in self.closed_positions.values() if p['pnl'] < 0)
            win_rate = (winners / total_trades * 100) if total_trades > 0 else 0
            avg_pnl = sum(p['pnl'] for p in self.closed_positions.values()) / total_trades if total_trades > 0 else 0
            total_pnl = sum(p['pnl'] for p in self.closed_positions.values())
            
            best_trade = max(self.closed_positions.items(), key=lambda x: x[1]['pnl'])
            worst_trade = min(self.closed_positions.items(), key=lambda x: x[1]['pnl'])
            
            color = 3066993 if total_pnl > 0 else 15158332
            
            embed = {
                "title": "📊 MANGO_BOT - DAILY ANALYTICS",
                "description": f"{datetime.now().strftime('%A, %B %d, %Y')}",
                "color": color,
                "fields": [
                    {"name": "📈 Total Trades", "value": f"{total_trades}", "inline": True},
                    {"name": "✅ Win Rate", "value": f"{win_rate:.1f}% ({winners}W/{losers}L)", "inline": True},
                    {"name": "💰 Daily P&L", "value": f"{total_pnl:+.2f}%", "inline": True},
                    {"name": "📊 Average Per Trade", "value": f"{avg_pnl:+.2f}%", "inline": True},
                    {"name": "🏆 Best Trade", "value": f"{best_trade[0]} (+{best_trade[1]['pnl']:.2f}%)", "inline": True},
                    {"name": "📉 Worst Trade", "value": f"{worst_trade[0]} ({worst_trade[1]['pnl']:.2f}%)", "inline": True},
                    {"name": "🎯 Target Hit", "value": f"{sum(1 for p in self.closed_positions.values() if p['reason'] == 'TARGET_HIT')} ✅", "inline": True},
                    {"name": "🛑 Stop Hit", "value": f"{sum(1 for p in self.closed_positions.values() if p['reason'] == 'STOP_HIT')} ❌", "inline": True},
                    {"name": "⏰ Time Expired", "value": f"{sum(1 for p in self.closed_positions.values() if p['reason'] == 'TIME_EXPIRED')} ⏰", "inline": True}
                ],
                "footer": {"text": "🥭 Mango_Bot - Market Close Report | See you tomorrow!"}
            }
        
        try:
            requests.post(self.webhook, json={'embeds': [embed]}, timeout=10)
            self.log("📊 Daily analytics sent!")
        except:
            self.log("❌ Discord error")
    
    def send_best_stocks_alert(self):
        """Send best and worst stocks alert"""
        stock_stats = self.calculate_stock_performance()
        
        if not stock_stats:
            embed = {
                "title": "📊 BEST STOCKS ALERT",
                "description": f"{datetime.now().strftime('%A, %B %d, %Y')}",
                "color": 16776960,
                "fields": [{"name": "📈 Status", "value": "Not enough data yet. Keep trading! 📊", "inline": False}],
                "footer": {"text": "🥭 Mango_Bot - Coming soon!"}
            }
        else:
            sorted_stocks = sorted(stock_stats.items(), key=lambda x: x[1]['win_rate'], reverse=True)
            top_performers = sorted_stocks[:5]
            worst_performers = sorted_stocks[-5:]
            
            fields = [{"name": "🏆 TOP PERFORMERS (BUY THESE!)", "value": "High win rate stocks", "inline": False}]
            
            for symbol, stats in top_performers:
                if stats['total'] >= 2:
                    fields.append({"name": f"✅ {symbol}", "value": f"{stats['win_rate']:.0f}% win ({stats['wins']}W/{stats['losses']}L) | Avg: {stats['avg_pnl']:+.2f}%", "inline": False})
            
            fields.append({"name": "❌ AVOID THESE (SKIP!)", "value": "Low win rate stocks", "inline": False})
            
            for symbol, stats in worst_performers:
                if stats['total'] >= 2 and stats['win_rate'] < 60:
                    fields.append({"name": f"⛔ {symbol}", "value": f"{stats['win_rate']:.0f}% win ({stats['wins']}W/{stats['losses']}L) | Avg: {stats['avg_pnl']:+.2f}%", "inline": False})
            
            embed = {
                "title": "📊 BEST STOCKS ALERT",
                "description": f"{datetime.now().strftime('%A, %B %d, %Y')} | Smart Trading Filter",
                "color": 3066993,
                "fields": fields,
                "footer": {"text": "🥭 Mango_Bot - Trade smarter, follow the winners!"}
            }
        
        try:
            requests.post(self.webhook, json={'embeds': [embed]}, timeout=10)
            self.log("📊 Best stocks alert sent!")
        except:
            self.log("❌ Discord error")
    
    def is_market_hours(self):
        """Check if US market is open (IST time) - 7:00 PM to 1:30 AM next day"""
        from datetime import timezone, timedelta
        ist = timezone(timedelta(hours=5, minutes=30))
        now = datetime.now(ist)
        
        # Market hours in IST: 7:00 PM (19:00) to 1:30 AM (01:30)
        # Check if it's 7 PM or later, OR if it's before 1:30 AM
        is_market_open = (now.hour >= 19) or (now.hour < 1) or (now.hour == 1 and now.minute < 30)
        is_weekday = now.weekday() < 5
        
        return is_weekday and is_market_open
    
    def is_pre_market(self):
        """Check if it's 1 hour before market opens - 6:00 PM IST"""
        from datetime import timezone, timedelta
        ist = timezone(timedelta(hours=5, minutes=30))
        now = datetime.now(ist)
        
        # Pre-market: 6 PM to 7 PM IST
        is_pre = (now.hour == 18 and now.minute >= 0)
        is_weekday = now.weekday() < 5
        
        return is_weekday and is_pre
    
    def run(self):
        """Main loop - Smart schedule"""
        cycle = 0
        daily_analytics_sent = False
        market_momentum_sent = False
        
        while True:
            # PRE-MARKET: Check 1 hour before market opens (8:30 AM)
            if self.is_pre_market():
                if not market_momentum_sent:
                    cycle += 1
                    self.log(f"\n🔄 CYCLE #{cycle} - PRE-MARKET CHECK")
                    self.log("📈 1 HOUR BEFORE MARKET OPENS - CHECKING MOMENTUM!")
                    self.check_market_momentum()
                    market_momentum_sent = True
                    self.log("⏱️ Waiting for market open at 9:30 AM...\n")
                
                time.sleep(300)
            
            # MARKET HOURS: 9:30 AM - 4:00 PM EDT
            elif self.is_market_hours():
                cycle += 1
                self.log(f"\n🔄 CYCLE #{cycle}")
                
                self.scan()
                self.monitor_positions()
                self.log(f"   📊 Open positions: {len(self.open_positions)}")
                
                elapsed = datetime.now() - self.last_signal
                if elapsed >= timedelta(minutes=3):
                    self.log("⏰ 3 min - SENDING NEW SIGNAL!")
                    
                    if self.stocks_analysis:
                        best = max(self.stocks_analysis.items(), key=lambda x: x[1]['score'])
                        symbol = best[0]
                        data = best[1]
                        score = data['score']
                        
                        self.send_buy_signal(symbol, data, score)
                        self.last_signal = datetime.now()
                else:
                    remaining = 30 - int(elapsed.total_seconds() / 60)
                    self.log(f"   ⏳ Next signal in {remaining} min")
                
                if datetime.now().hour == 16 and datetime.now().minute < 5 and not daily_analytics_sent:
                    self.log("📊 MARKET CLOSE - SENDING DAILY ANALYTICS!")
                    self.send_daily_analytics()
                    time.sleep(2)
                    self.log("📊 SENDING BEST STOCKS ALERT!")
                    self.send_best_stocks_alert()
                    daily_analytics_sent = True
                
                self.log("⏱️ Next check in 5 min...\n")
                time.sleep(300)
            
            # AFTER MARKET CLOSE: Sleep
            else:
                self.log(f"\n😴 MARKET CLOSED - BOT SLEEPING")
                self.log("⏳ See you tomorrow at 8:30 AM!\n")
                
                daily_analytics_sent = False
                market_momentum_sent = False
                
                time.sleep(600)


if __name__ == "__main__":
    bot = CompleteBot()
    bot.run()
