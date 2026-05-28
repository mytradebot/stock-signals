#!/usr/bin/env python3
"""
MEGA BOT - COMPLETE TRADING SYSTEM
500 stocks → Analyze → Pick BEST 1 → Send BUY
Track positions → Monitor price → Send SELL when target/stop/time hit
Full P&L tracking + Daily summary
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
        
        # 500 BEST STOCKS
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
            'TOST', 'RIOT', 'MARA', 'MSTR', 'CHPT', 'KNSL', 'CPRT', 'OPEN', 'CVNA', 'KIND',
            'BRKS', 'EVTL', 'WKME', 'POSH', 'FTCH', 'RBLX', 'LCID', 'RIVN', 'FUTU', 'IQ',
            'VIPS', 'ZTO', 'TCOM', 'TME', 'ORCL', 'SAP', 'TEAM', 'DOCU', 'NEWR', 'SSNC',
            'PAYC', 'BIDU', 'VRSN', 'ANET', 'DDOG', 'CRWD', 'SPLK', 'F', 'GM', 'BA',
            'CAT', 'DE', 'GE', 'PFE', 'MRNA', 'ABBV', 'TMO', 'LLY', 'MRK', 'AMGN',
            'GILD', 'BNTX', 'SGEN', 'BMRN', 'NBIX', 'VIACP', 'MRVL', 'MCHP', 'QRVO', 'SWKS',
            'JPM', 'BAC', 'WFC', 'GS', 'MS', 'BLK', 'SCHW', 'TROW', 'AXP', 'DFS',
            'SYF', 'VNO', 'PLD', 'PSA', 'EQR', 'AVB', 'ARE', 'MAA', 'WY', 'RYN',
            'PCH', 'IRM', 'SSNC', 'PAYC', 'BIDU', 'VRSN', 'ANET', 'DDOG', 'CRWD', 'SPLK',
            'QQQ', 'DIA', 'IWM', 'SPY', 'VOO', 'VTI', 'VTV', 'VUG', 'VGK', 'VXUS',
            'EEM', 'AGG', 'BND', 'LQD', 'HYG', 'JNK', 'TLT', 'IEF', 'SHV', 'GLD',
            'SLV', 'USO', 'VNQ', 'XRT', 'XLK', 'XLV', 'XLI', 'XLF', 'XLY', 'XLP',
            'XLRE', 'XLU', 'XLE', 'IVV', 'IJH', 'IJR', 'VB', 'SCHB', 'SCHC', 'SCHD',
        ][:500]  # Limit to 500
        
        self.stocks_analysis = {}
        self.open_positions = {}  # Track open trades
        self.closed_positions = {}  # Track closed trades
        self.last_signal = datetime.now()
        self.daily_start = datetime.now().replace(hour=9, minute=30)
        
        self.log("=" * 70)
        self.log("🥭 MANGO_BOT - COMPLETE TRADING SYSTEM")
        self.log("📊 500 stocks → Analyze → BEST 1 BUY signal")
        self.log("📈 Auto-tracking → SELL when target/stop/time hit")
        self.log("💰 Full P&L tracking + Daily summary")
        self.log("=" * 70)
    
    def log(self, msg):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
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
        """Scan all 500 stocks"""
        self.log(f"🔍 Analyzing {len(self.stocks)} stocks...")
        
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
                
                time.sleep(0.03)
            except:
                pass
        
        self.log(f"   ✅ Analyzed {found} stocks")
    
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
        
        # Fallback logo
        return f"https://logo.clearbit.com/{symbol}.com"
    
    def send_buy_signal(self, symbol, data, score):
        """Send BUY signal to Discord with logo and track position"""
        price = data['price']
        target = price * 1.025  # +2.5% target
        stop = price * 0.98    # -2% stop
        logo_url = self.get_stock_logo(symbol)
        
        # Track position
        self.open_positions[symbol] = {
            'entry_price': price,
            'target': target,
            'stop': stop,
            'entry_time': datetime.now(),
            'timeframe': 7,  # 7 day hold max
            'score': score
        }
        
        # Discord Embed with logo - NO STOP LOSS (bot handles it)
        embed = {
            "title": f"🟢 MANGO_BOT BUY: {symbol}",
            "description": f"⏰ {datetime.now().strftime('%H:%M %Z')}",
            "color": 3066993,  # Green
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
                    "value": f"${target:.2f} (+2.5%)",
                    "inline": True
                },
                {
                    "name": "⭐ Quality Score",
                    "value": f"{score}/100 ⭐",
                    "inline": True
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
                    "name": "✅ Auto Management",
                    "value": "Bot exits automatically",
                    "inline": True
                }
            ],
            "footer": {
                "text": "🥭 Mango_Bot - Auto Signals & Auto Exits"
            }
        }
        
        try:
            requests.post(self.webhook, json={'embeds': [embed]}, timeout=10)
            self.log(f"📱 BUY SIGNAL: {symbol} @ ${price:.2f} (score: {score})")
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
                
                # Check if target hit
                if current_price >= target:
                    pnl = ((current_price - entry) / entry) * 100
                    
                    embed = {
                        "title": f"🎉 SELL - TARGET HIT!",
                        "description": f"{symbol}",
                        "color": 3066993,  # Green
                        "thumbnail": {
                            "url": logo_url,
                            "height": 100,
                            "width": 100
                        },
                        "fields": [
                            {
                                "name": "Entry → Exit",
                                "value": f"${entry:.2f} → ${current_price:.2f}",
                                "inline": False
                            },
                            {
                                "name": "Profit",
                                "value": f"+{pnl:.2f}% ✅",
                                "inline": True
                            },
                            {
                                "name": "Status",
                                "value": "TAKE PROFIT!",
                                "inline": True
                            }
                        ]
                    }
                    
                    self.closed_positions[symbol] = {
                        'entry': entry,
                        'exit': current_price,
                        'pnl': pnl,
                        'reason': 'TARGET_HIT'
                    }
                    closed.append(symbol)
                
                # Check if stop hit
                elif current_price <= stop:
                    pnl = ((current_price - entry) / entry) * 100
                    
                    embed = {
                        "title": f"⛔ SELL - STOP HIT",
                        "description": f"{symbol}",
                        "color": 15158332,  # Red
                        "thumbnail": {
                            "url": logo_url,
                            "height": 100,
                            "width": 100
                        },
                        "fields": [
                            {
                                "name": "Entry → Exit",
                                "value": f"${entry:.2f} → ${current_price:.2f}",
                                "inline": False
                            },
                            {
                                "name": "Loss",
                                "value": f"{pnl:.2f}% ❌",
                                "inline": True
                            },
                            {
                                "name": "Status",
                                "value": "CUT LOSS",
                                "inline": True
                            }
                        ]
                    }
                    
                    self.closed_positions[symbol] = {
                        'entry': entry,
                        'exit': current_price,
                        'pnl': pnl,
                        'reason': 'STOP_HIT'
                    }
                    closed.append(symbol)
                
                # Check if timeframe expired (7 days)
                elif (datetime.now() - entry_time).days >= pos['timeframe']:
                    pnl = ((current_price - entry) / entry) * 100
                    
                    embed = {
                        "title": f"⏰ SELL - TIME EXPIRED",
                        "description": f"{symbol}",
                        "color": 15844367,  # Orange
                        "thumbnail": {
                            "url": logo_url,
                            "height": 100,
                            "width": 100
                        },
                        "fields": [
                            {
                                "name": "Entry → Exit",
                                "value": f"${entry:.2f} → ${current_price:.2f}",
                                "inline": False
                            },
                            {
                                "name": "Return",
                                "value": f"{pnl:+.2f}%",
                                "inline": True
                            },
                            {
                                "name": "Status",
                                "value": "7 DAY HOLD DONE",
                                "inline": True
                            }
                        ]
                    }
                    
                    self.closed_positions[symbol] = {
                        'entry': entry,
                        'exit': current_price,
                        'pnl': pnl,
                        'reason': 'TIME_EXPIRED'
                    }
                    closed.append(symbol)
                
                else:
                    # Still open - show update
                    pnl = ((current_price - entry) / entry) * 100
                    continue
                
                # Send message
                try:
                    requests.post(self.webhook, json={'embeds': [embed]}, timeout=10)
                except:
                    pass
            
            except:
                pass
        
        # Remove closed positions
        for symbol in closed:
            del self.open_positions[symbol]
    
    def calculate_stock_performance(self):
        """Calculate win rate for each stock"""
        stock_stats = {}
        
        for symbol, trade in self.closed_positions.items():
            if symbol not in stock_stats:
                stock_stats[symbol] = {
                    'total': 0,
                    'wins': 0,
                    'losses': 0,
                    'avg_pnl': 0,
                    'total_pnl': 0
                }
            
            stock_stats[symbol]['total'] += 1
            if trade['pnl'] > 0:
                stock_stats[symbol]['wins'] += 1
            else:
                stock_stats[symbol]['losses'] += 1
            
            stock_stats[symbol]['total_pnl'] += trade['pnl']
        
        # Calculate averages and win rates
        for symbol in stock_stats:
            total = stock_stats[symbol]['total']
            if total > 0:
                stock_stats[symbol]['win_rate'] = (stock_stats[symbol]['wins'] / total) * 100
                stock_stats[symbol]['avg_pnl'] = stock_stats[symbol]['total_pnl'] / total
            else:
                stock_stats[symbol]['win_rate'] = 0
                stock_stats[symbol]['avg_pnl'] = 0
        
        return stock_stats
    
    def send_best_stocks_alert(self):
        """Send best and worst stocks alert"""
        stock_stats = self.calculate_stock_performance()
        
        if not stock_stats:
            embed = {
                "title": "📊 BEST STOCKS ALERT",
                "description": f"{datetime.now().strftime('%A, %B %d, %Y')}",
                "color": 16776960,  # Yellow
                "fields": [
                    {
                        "name": "📈 Status",
                        "value": "Not enough data yet. Keep trading! 📊",
                        "inline": False
                    }
                ],
                "footer": {
                    "text": "🥭 Mango_Bot - Coming soon!"
                }
            }
        else:
            # Find top 5 performers
            sorted_stocks = sorted(stock_stats.items(), key=lambda x: x[1]['win_rate'], reverse=True)
            top_performers = sorted_stocks[:5]
            worst_performers = sorted_stocks[-5:]
            
            # Build fields
            fields = []
            
            # Top performers
            fields.append({
                "name": "🏆 TOP PERFORMERS (BUY THESE!)",
                "value": "High win rate stocks",
                "inline": False
            })
            
            for symbol, stats in top_performers:
                if stats['total'] >= 2:  # Only show if at least 2 trades
                    fields.append({
                        "name": f"✅ {symbol}",
                        "value": f"{stats['win_rate']:.0f}% win rate ({stats['wins']}W/{stats['losses']}L) | Avg: {stats['avg_pnl']:+.2f}%",
                        "inline": False
                    })
            
            fields.append({
                "name": "❌ AVOID THESE (SKIP!)",
                "value": "Low win rate stocks",
                "inline": False
            })
            
            # Worst performers
            for symbol, stats in worst_performers:
                if stats['total'] >= 2:  # Only show if at least 2 trades
                    if stats['win_rate'] < 60:  # Only show if under 60% win rate
                        fields.append({
                            "name": f"⛔ {symbol}",
                            "value": f"{stats['win_rate']:.0f}% win rate ({stats['wins']}W/{stats['losses']}L) | Avg: {stats['avg_pnl']:+.2f}%",
                            "inline": False
                        })
            
            embed = {
                "title": "📊 BEST STOCKS ALERT",
                "description": f"{datetime.now().strftime('%A, %B %d, %Y')} | Smart Trading Filter",
                "color": 3066993,  # Green
                "fields": fields,
                "footer": {
                    "text": "🥭 Mango_Bot - Trade smarter, follow the winners!"
                }
            }
        
        try:
            requests.post(self.webhook, json={'embeds': [embed]}, timeout=10)
            self.log("📊 Best stocks alert sent to Discord!")
        except:
            self.log("❌ Discord error sending best stocks alert")
        """Check market momentum at market open"""
        try:
            # Get S&P 500 (SPY) data
            spy_data = self.get_stock_data('SPY')
            
            # Get Nasdaq (QQQ) data
            qqq_data = self.get_stock_data('QQQ')
            
            # Get VIX (volatility)
            vix_data = self.get_stock_data('VIX')
            
            if not spy_data or not qqq_data:
                return None
            
            spy_change = ((spy_data['price'] - spy_data['prev_close']) / spy_data['prev_close']) * 100
            qqq_change = ((qqq_data['price'] - qqq_data['prev_close']) / qqq_data['prev_close']) * 100
            vix_price = vix_data['price'] if vix_data else 20
            
            # Determine market sentiment
            avg_change = (spy_change + qqq_change) / 2
            
            if avg_change > 1:
                sentiment = "🚀 BULLISH"
                color = 3066993  # Green
                message = "Today is a GREAT day to invest! Market opening STRONG 📈"
                emoji = "🟢"
            elif avg_change > 0.3:
                sentiment = "📈 POSITIVE"
                color = 3066993  # Green
                message = "Good momentum today! Markets looking positive 📊"
                emoji = "🟢"
            elif avg_change > -0.3:
                sentiment = "➡️ NEUTRAL"
                color = 16776960  # Yellow
                message = "Markets are neutral today. Be cautious with entries 🔍"
                emoji = "🟡"
            elif avg_change > -1:
                sentiment = "📉 BEARISH"
                color = 15158332  # Red
                message = "Markets struggling today. Wait for better entries ⛔"
                emoji = "🔴"
            else:
                sentiment = "🔴 VERY BEARISH"
                color = 15158332  # Red
                message = "Strong selling pressure today. SKIP trading or be very selective ⛔"
                emoji = "🔴"
            
            # Create embed
            embed = {
                "title": f"{emoji} MANGO_BOT - MARKET MOMENTUM",
                "description": f"📅 {datetime.now().strftime('%A, %B %d, %Y')} | Market Open",
                "color": color,
                "fields": [
                    {
                        "name": "📊 Market Sentiment",
                        "value": sentiment,
                        "inline": True
                    },
                    {
                        "name": "📈 S&P 500 (SPY)",
                        "value": f"{spy_change:+.2f}%",
                        "inline": True
                    },
                    {
                        "name": "💻 Nasdaq (QQQ)",
                        "value": f"{qqq_change:+.2f}%",
                        "inline": True
                    },
                    {
                        "name": "😰 Market Fear (VIX)",
                        "value": f"{vix_price:.1f}" + (" 📈 HIGH" if vix_price > 25 else " NORMAL"),
                        "inline": True
                    },
                    {
                        "name": "💡 Today's Action",
                        "value": message,
                        "inline": False
                    },
                    {
                        "name": "🎯 Strategy",
                        "value": self.get_trading_strategy(sentiment),
                        "inline": False
                    }
                ],
                "footer": {
                    "text": "🥭 Mango_Bot - Market Outlook | Happy Trading!"
                }
            }
            
            try:
                requests.post(self.webhook, json={'embeds': [embed]}, timeout=10)
                self.log(f"📈 Market momentum analysis sent! Sentiment: {sentiment}")
            except:
                self.log("❌ Discord error sending momentum")
        
        except Exception as e:
            self.log(f"❌ Error checking market momentum: {e}")
    
    def get_trading_strategy(self, sentiment):
        """Get trading strategy based on sentiment"""
        strategies = {
            "🚀 BULLISH": "✅ Aggressive - Take signals with confidence! Volume will support moves.",
            "📈 POSITIVE": "✅ Normal - Standard trading. Follow all signals normally.",
            "➡️ NEUTRAL": "⚠️ Cautious - Only take high-quality signals (90+ score). Watch for reversals.",
            "📉 BEARISH": "❌ Selective - Only trade proven patterns. Skip weak setups.",
            "🔴 VERY BEARISH": "❌ SKIP - Avoid trading today. Wait for better conditions."
        }
        return strategies.get(sentiment, "Trade normally.")
        """Send daily analytics at market close (4:00 PM EDT)"""
        if not self.closed_positions:
            embed = {
                "title": "📊 MANGO_BOT - DAILY ANALYTICS",
                "description": f"{datetime.now().strftime('%A, %B %d, %Y')}",
                "color": 15158332,  # Red
                "fields": [
                    {
                        "name": "Total Trades",
                        "value": "0",
                        "inline": True
                    },
                    {
                        "name": "Win Rate",
                        "value": "N/A",
                        "inline": True
                    },
                    {
                        "name": "Daily P&L",
                        "value": "No trades today",
                        "inline": True
                    }
                ],
                "footer": {
                    "text": "🥭 Mango_Bot - Market Close Report"
                }
            }
        else:
            total_trades = len(self.closed_positions)
            winners = sum(1 for p in self.closed_positions.values() if p['pnl'] > 0)
            losers = sum(1 for p in self.closed_positions.values() if p['pnl'] < 0)
            win_rate = (winners / total_trades * 100) if total_trades > 0 else 0
            avg_pnl = sum(p['pnl'] for p in self.closed_positions.values()) / total_trades if total_trades > 0 else 0
            total_pnl = sum(p['pnl'] for p in self.closed_positions.values())
            
            # Find best and worst trades
            best_trade = max(self.closed_positions.items(), key=lambda x: x[1]['pnl'])
            worst_trade = min(self.closed_positions.items(), key=lambda x: x[1]['pnl'])
            
            # Color based on performance
            color = 3066993 if total_pnl > 0 else 15158332  # Green if profit, Red if loss
            
            embed = {
                "title": "📊 MANGO_BOT - DAILY ANALYTICS",
                "description": f"{datetime.now().strftime('%A, %B %d, %Y')}",
                "color": color,
                "fields": [
                    {
                        "name": "📈 Total Trades",
                        "value": f"{total_trades}",
                        "inline": True
                    },
                    {
                        "name": "✅ Win Rate",
                        "value": f"{win_rate:.1f}% ({winners}W/{losers}L)",
                        "inline": True
                    },
                    {
                        "name": "💰 Daily P&L",
                        "value": f"{total_pnl:+.2f}%",
                        "inline": True
                    },
                    {
                        "name": "📊 Average Per Trade",
                        "value": f"{avg_pnl:+.2f}%",
                        "inline": True
                    },
                    {
                        "name": "🏆 Best Trade",
                        "value": f"{best_trade[0]} (+{best_trade[1]['pnl']:.2f}%)",
                        "inline": True
                    },
                    {
                        "name": "📉 Worst Trade",
                        "value": f"{worst_trade[0]} ({worst_trade[1]['pnl']:.2f}%)",
                        "inline": True
                    },
                    {
                        "name": "🎯 Target Hit",
                        "value": f"{sum(1 for p in self.closed_positions.values() if p['reason'] == 'TARGET_HIT')} ✅",
                        "inline": True
                    },
                    {
                        "name": "🛑 Stop Hit",
                        "value": f"{sum(1 for p in self.closed_positions.values() if p['reason'] == 'STOP_HIT')} ❌",
                        "inline": True
                    },
                    {
                        "name": "⏰ Time Expired",
                        "value": f"{sum(1 for p in self.closed_positions.values() if p['reason'] == 'TIME_EXPIRED')} ⏰",
                        "inline": True
                    }
                ],
                "footer": {
                    "text": "🥭 Mango_Bot - Market Close Report | See you tomorrow!"
                }
            }
        
        try:
            requests.post(self.webhook, json={'embeds': [embed]}, timeout=10)
            self.log("📊 Daily analytics sent to Discord!")
        except:
            self.log("❌ Discord error sending analytics")
    
    def is_market_hours(self):
        """Check if market is open (EDT) - 9:30 AM to 4:00 PM"""
        from datetime import timezone
        edt = timezone(timedelta(hours=-4))
        now = datetime.now(edt)
        
        is_weekday = now.weekday() < 5
        is_open = 9.5 <= now.hour <= 16.0
        
        return is_weekday and is_open
    
    def is_pre_market(self):
        """Check if it's 1 hour before market opens - 8:30 AM"""
        from datetime import timezone
        edt = timezone(timedelta(hours=-4))
        now = datetime.now(edt)
        
        is_weekday = now.weekday() < 5
        is_pre = 8.5 <= now.hour < 9.5
        
        return is_weekday and is_pre
    
    def run(self):
        """Main loop - Smart schedule: check 1hr early, run during market, sleep after close"""
        cycle = 0
        daily_analytics_sent = False
        market_momentum_sent = False
        
        while True:
            cycle += 1
            
            # PRE-MARKET: Check 1 hour before market opens (8:30 AM)
            if self.is_pre_market():
                if not market_momentum_sent:
                    self.log(f"\n🔄 CYCLE #{cycle} - PRE-MARKET CHECK")
                    self.log("📈 1 HOUR BEFORE MARKET OPENS - CHECKING MOMENTUM!")
                    self.check_market_momentum()
                    market_momentum_sent = True
                    self.log("⏱️ Waiting for market open at 9:30 AM...\n")
                
                time.sleep(300)  # Check every 5 min during pre-market
            
            # MARKET HOURS: 9:30 AM - 4:00 PM EDT
            elif self.is_market_hours():
                cycle += 1
                self.log(f"\n🔄 CYCLE #{cycle}")
                
                # Scan for new signals
                self.scan()
                
                # Monitor existing positions (every cycle = every 5 min)
                self.monitor_positions()
                self.log(f"   📊 Open positions: {len(self.open_positions)}")
                
                # Send new signal every 30 min
                elapsed = datetime.now() - self.last_signal
                if elapsed >= timedelta(minutes=30):
                    self.log("⏰ 30 min - SENDING NEW SIGNAL!")
                    
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
                
                # Daily analytics + Best stocks alert at 4:00 PM (market close)
                if datetime.now().hour == 16 and datetime.now().minute < 5 and not daily_analytics_sent:
                    self.log("📊 MARKET CLOSE - SENDING DAILY ANALYTICS!")
                    self.send_daily_analytics()
                    time.sleep(2)
                    self.log("📊 SENDING BEST STOCKS ALERT!")
                    self.send_best_stocks_alert()
                    daily_analytics_sent = True
                
                self.log("⏱️ Next check in 5 min...\n")
                time.sleep(300)
            
            # AFTER MARKET CLOSE: Sleep until next day
            else:
                self.log(f"\n😴 MARKET CLOSED - BOT SLEEPING")
                self.log("⏳ See you tomorrow at 8:30 AM!\n")
                
                # Reset flags for next day
                daily_analytics_sent = False
                market_momentum_sent = False
                
                # Sleep for 10 minutes, then check again
                time.sleep(600)


if __name__ == "__main__":
    bot = CompleteBot()
    bot.run()
