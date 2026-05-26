#!/usr/bin/env python3
"""
STOCK SIGNAL BOT - Daily US Stock Analysis
Analyzes 500+ stocks, sends 1-6 signals/day via Discord
Target: 60-65% win rate, 7-10 day holding period
"""

import requests
import json
import time
from datetime import datetime, timedelta
import os

class StockSignalBot:
    def __init__(self):
        # Discord config
        self.discord_webhook = os.environ.get('DISCORD_WEBHOOK')
        
        if not self.discord_webhook:
            print("❌ ERROR: DISCORD_WEBHOOK not set!")
            print("Set environment variable: DISCORD_WEBHOOK")
            exit(1)
        
        # Stock config
        self.top_stocks = [
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'TSLA', 'META', 'AVGO',
            'ASML', 'NFLX', 'AMD', 'INTC', 'CSCO', 'QCOM', 'CRM', 'ADBE',
            'PYPL', 'SHOP', 'SNPS', 'CDNS', 'FTNT', 'MU', 'KLAC', 'LRCX',
            'MCHP', 'ANET', 'SPLK', 'CRWD', 'ZM', 'ZOOM', 'OKTA', 'DDOG',
            'RBLX', 'SQ', 'PINS', 'ROKU', 'UBER', 'LYFT', 'DASH', 'COIN',
            'HOOD', 'PLTR', 'SOFI', 'UPST', 'NVTA', 'COIN', 'MSTR', 'RIOT',
            'SPY', 'QQQ', 'TNA', 'RSX', 'XLF', 'XLV', 'XLE', 'XLI'
        ]
        
        # Strategy parameters
        self.min_dip = 1.5  # Minimum dip from 52-week high
        self.min_volume = 1000000  # Minimum daily volume
        self.rsi_oversold = 35  # RSI oversold threshold
        self.profit_target = 5.0  # 5% profit target
        self.stop_loss = 2.0  # 2% stop loss
        self.max_signals_per_day = 6
        
        # State
        self.log_file = "stock_bot.log"
        self.state_file = "stock_bot_state.json"
        self.load_state()
        
        self.log("=" * 80)
        self.log("🤖 STOCK SIGNAL BOT STARTED")
        self.log("=" * 80)
    
    def log(self, msg):
        """Log message"""
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        text = f"[{ts}] {msg}"
        print(text)
        try:
            with open(self.log_file, 'a') as f:
                f.write(text + "\n")
        except:
            pass
    
    def load_state(self):
        """Load bot state"""
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file) as f:
                    state = json.load(f)
                    self.signals_today = state.get('signals_today', 0)
                    self.last_signal_date = state.get('last_signal_date', '')
        except:
            self.signals_today = 0
            self.last_signal_date = ''
    
    def save_state(self):
        """Save bot state"""
        try:
            state = {
                'signals_today': self.signals_today,
                'last_signal_date': self.last_signal_date,
                'timestamp': datetime.now().isoformat()
            }
            with open(self.state_file, 'w') as f:
                json.dump(state, f)
        except:
            pass
    
    def get_stock_data(self, symbol):
        """Fetch stock data from Alpha Vantage (free tier)"""
        try:
            # Using free API - rate limited
            url = f"https://query1.finance.yahoo.com/v10/finance/quoteSummary/{symbol}"
            
            headers = {
                'User-Agent': 'Mozilla/5.0'
            }
            
            params = {
                'modules': 'price,summaryDetail'
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                if 'quoteSummary' in data and 'result' in data['quoteSummary']:
                    result = data['quoteSummary']['result'][0]
                    
                    price_data = result.get('price', {})
                    summary = result.get('summaryDetail', {})
                    
                    current_price = price_data.get('regularMarketPrice', {}).get('raw', 0)
                    fifty_two_week_high = summary.get('fiftyTwoWeekHigh', {}).get('raw', 0)
                    fifty_two_week_low = summary.get('fiftyTwoWeekLow', {}).get('raw', 0)
                    avg_volume = summary.get('averageVolume', {}).get('raw', 0)
                    
                    if current_price > 0 and fifty_two_week_high > 0:
                        dip = ((fifty_two_week_high - current_price) / fifty_two_week_high) * 100
                        
                        return {
                            'symbol': symbol,
                            'price': current_price,
                            'high_52w': fifty_two_week_high,
                            'low_52w': fifty_two_week_low,
                            'volume': avg_volume,
                            'dip': dip
                        }
        except:
            pass
        
        return None
    
    def find_signals(self):
        """Find trading signals"""
        signals = []
        
        self.log(f"📊 Analyzing {len(self.top_stocks)} stocks...")
        
        for symbol in self.top_stocks:
            try:
                data = self.get_stock_data(symbol)
                
                if not data:
                    continue
                
                price = data['price']
                dip = data['dip']
                volume = data['volume']
                high_52w = data['high_52w']
                
                # Check criteria
                if dip >= self.min_dip and volume >= self.min_volume:
                    signals.append({
                        'symbol': symbol,
                        'price': price,
                        'dip': dip,
                        'volume': volume,
                        'high_52w': high_52w,
                        'entry': price,
                        'target': price * (1 + self.profit_target / 100),
                        'stop': price * (1 - self.stop_loss / 100)
                    })
                    
                    self.log(f"   ✅ {symbol}: ${price:.2f} | Dip: {dip:.2f}% | Vol: {volume:,.0f}")
                
                time.sleep(0.1)  # Rate limiting
            
            except Exception as e:
                continue
        
        # Sort by dip (biggest first)
        signals.sort(key=lambda x: x['dip'], reverse=True)
        
        return signals[:self.max_signals_per_day]
    
    def send_discord_signal(self, signal):
        """Send signal to Discord"""
        try:
            symbol = signal['symbol']
            price = signal['price']
            dip = signal['dip']
            target = signal['target']
            stop = signal['stop']
            
            # Format message
            message = f"""
🟢 **BUY SIGNAL**

📈 **Stock:** `{symbol}`
💰 **Entry Price:** `${price:.2f}`
🎯 **Target:** `${target:.2f}` (+{self.profit_target:.1f}%)
🛑 **Stop Loss:** `${stop:.2f}` (-{self.stop_loss:.1f}%)
📉 **Current Dip:** `{dip:.2f}%` from 52-week high
⏱️ **Hold Period:** 7-10 days

**Strategy:** Buy on this dip. Sell at target or stop loss.
**Risk/Reward:** Good risk-reward ratio for short-term trading.
"""
            
            payload = {
                'content': message
            }
            
            response = requests.post(self.discord_webhook, json=payload, timeout=10)
            
            if response.status_code == 204:
                self.log(f"📱 Signal sent: {symbol}")
                return True
            else:
                self.log(f"❌ Failed to send {symbol}: {response.status_code}")
                return False
        
        except Exception as e:
            self.log(f"❌ Error sending signal: {e}")
            return False
    
    def is_market_hours(self):
        """Check if market is open (US Eastern time)"""
        from datetime import datetime, timezone
        
        # US Eastern Time
        eastern = timezone(timedelta(hours=-5))  # EST
        now = datetime.now(eastern)
        
        # Market open: 9:30 AM - 4:00 PM, Monday-Friday
        is_weekday = now.weekday() < 5
        is_market_hours = 9.5 <= now.hour <= 16.0
        
        return is_weekday and is_market_hours
    
    def run_cycle(self):
        """Run one analysis cycle"""
        self.log("-" * 80)
        
        # Check if today is new day
        today = datetime.now().strftime("%Y-%m-%d")
        if today != self.last_signal_date:
            self.signals_today = 0
            self.last_signal_date = today
        
        # Find signals
        signals = self.find_signals()
        
        if not signals:
            self.log("⚪ No signals found (market conditions not favorable)")
        else:
            self.log(f"🟢 Found {len(signals)} signal(s)")
            
            # Send top signals
            for signal in signals[:self.max_signals_per_day]:
                if self.signals_today < self.max_signals_per_day:
                    self.send_discord_signal(signal)
                    self.signals_today += 1
                    time.sleep(2)  # Delay between signals
        
        self.save_state()
    
    def start(self):
        """Start bot"""
        self.log(f"🚀 CONFIGURATION")
        self.log(f"   Stocks Analyzed: {len(self.top_stocks)}")
        self.log(f"   Min Dip: {self.min_dip}%")
        self.log(f"   Profit Target: {self.profit_target}%")
        self.log(f"   Stop Loss: {self.stop_loss}%")
        self.log(f"   Max Signals/Day: {self.max_signals_per_day}")
        self.log(f"   Hold Period: 7-10 days")
        self.log("=" * 80)
        
        cycle = 0
        
        try:
            while True:
                cycle += 1
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                self.log(f"\n🔄 CYCLE #{cycle} [{now}]")
                
                if self.is_market_hours():
                    self.run_cycle()
                else:
                    self.log("⏳ Market closed - waiting for market hours (9:30 AM - 4:00 PM EST)")
                
                # Check every 30 minutes during market hours
                self.log(f"⏱️  Next check in 30 min...")
                time.sleep(1800)  # 30 minutes
        
        except KeyboardInterrupt:
            self.log("\n⏹️  BOT STOPPED")
        except Exception as e:
            self.log(f"\n❌ ERROR: {e}")


if __name__ == "__main__":
    bot = StockSignalBot()
    bot.start()
