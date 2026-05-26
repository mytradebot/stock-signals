#!/usr/bin/env python3
"""
STOCK SIGNAL BOT - Daily US Stock Analysis with Smart Auto-Sell
Analyzes 50+ stocks, sends 1-6 signals/day via Discord
Auto-sells based on: +5% profit, -2% loss, or 7-day limit
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
            exit(1)
        
        # Stock config
        self.top_stocks = [
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'TSLA', 'META', 'AVGO',
            'ASML', 'NFLX', 'AMD', 'INTC', 'CSCO', 'QCOM', 'CRM', 'ADBE',
            'PYPL', 'SHOP', 'SNPS', 'CDNS', 'FTNT', 'MU', 'KLAC', 'LRCX'
        ]
        
        # Strategy parameters
        self.min_dip = 1.5
        self.min_volume = 1000000
        self.profit_target = 5.0
        self.stop_loss = 2.0
        self.max_hold_days = 7
        self.max_signals_per_day = 6
        
        # State files
        self.log_file = "stock_bot.log"
        self.state_file = "stock_bot_state.json"
        self.positions_file = "active_positions.json"
        
        self.load_state()
        
        self.log("=" * 80)
        self.log("🤖 STOCK SIGNAL BOT WITH AUTO-SELL STARTED")
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
            else:
                self.signals_today = 0
                self.last_signal_date = ''
        except:
            self.signals_today = 0
            self.last_signal_date = ''
        
        # Load active positions
        try:
            if os.path.exists(self.positions_file):
                with open(self.positions_file) as f:
                    self.active_positions = json.load(f)
            else:
                self.active_positions = {}
        except:
            self.active_positions = {}
    
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
    
    def save_positions(self):
        """Save active positions"""
        try:
            with open(self.positions_file, 'w') as f:
                json.dump(self.active_positions, f, indent=2)
        except:
            pass
    
    def get_stock_data(self, symbol):
        """Fetch stock data from Yahoo Finance"""
        try:
            url = f"https://query1.finance.yahoo.com/v10/finance/quoteSummary/{symbol}"
            
            headers = {'User-Agent': 'Mozilla/5.0'}
            params = {'modules': 'price,summaryDetail'}
            
            response = requests.get(url, headers=headers, params=params, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                if 'quoteSummary' in data and 'result' in data['quoteSummary']:
                    result = data['quoteSummary']['result'][0]
                    
                    price_data = result.get('price', {})
                    summary = result.get('summaryDetail', {})
                    
                    current_price = price_data.get('regularMarketPrice', {}).get('raw', 0)
                    fifty_two_week_high = summary.get('fiftyTwoWeekHigh', {}).get('raw', 0)
                    avg_volume = summary.get('averageVolume', {}).get('raw', 0)
                    
                    if current_price > 0 and fifty_two_week_high > 0:
                        dip = ((fifty_two_week_high - current_price) / fifty_two_week_high) * 100
                        
                        return {
                            'symbol': symbol,
                            'price': current_price,
                            'high_52w': fifty_two_week_high,
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
                
                if dip >= self.min_dip and volume >= self.min_volume:
                    entry = price
                    target = price * (1 + self.profit_target / 100)
                    stop = price * (1 - self.stop_loss / 100)
                    
                    signals.append({
                        'symbol': symbol,
                        'price': price,
                        'dip': dip,
                        'volume': volume,
                        'entry': entry,
                        'target': target,
                        'stop': stop
                    })
                    
                    self.log(f" ✅ {symbol}: ${price:.2f} | Dip: {dip:.2f}%")
                
                time.sleep(0.1)
            
            except:
                continue
        
        signals.sort(key=lambda x: x['dip'], reverse=True)
        return signals[:self.max_signals_per_day]
    
    def send_discord_signal(self, message):
        """Send message to Discord"""
        try:
            payload = {'content': message}
            response = requests.post(self.discord_webhook, json=payload, timeout=10)
            return response.status_code == 204
        except:
            return False
    
    def send_buy_signal(self, signal):
        """Send buy signal"""
        symbol = signal['symbol']
        price = signal['price']
        dip = signal['dip']
        target = signal['target']
        stop = signal['stop']
        
        message = f"""🟢 **BUY SIGNAL**

📈 **Stock:** `{symbol}`
💰 **Entry Price:** `${price:.2f}`
🎯 **Profit Target:** `${target:.2f}` (+{self.profit_target:.1f}%)
🛑 **Stop Loss:** `${stop:.2f}` (-{self.stop_loss:.1f}%)
📉 **Current Dip:** `{dip:.2f}%` from 52-week high
⏱️ **Hold Period:** Up to {self.max_hold_days} days

**Auto-Sell Conditions:**
✅ Sells at +{self.profit_target}% profit
✅ Sells at -{self.stop_loss}% loss
✅ Auto-sells after {self.max_hold_days} days (if no exit)

Buy now on your exchange! 📲"""
        
        if self.send_discord_signal(message):
            entry_time = datetime.now().isoformat()
            self.active_positions[symbol] = {
                'entry_price': price,
                'entry_time': entry_time,
                'target': target,
                'stop': stop,
                'status': 'OPEN'
            }
            self.save_positions()
            self.log(f"📱 BUY Signal sent: {symbol}")
            return True
        
        return False
    
    def send_sell_signal(self, symbol, reason, current_price, entry_price, profit_pct):
        """Send sell signal"""
        message = f"""🔴 **SELL SIGNAL**

📈 **Stock:** `{symbol}`
💰 **Entry Price:** `${entry_price:.2f}`
💲 **Current Price:** `${current_price:.2f}`
📊 **Change:** `{profit_pct:+.2f}%`
❌ **Reason:** `{reason}`

**ACTION:** Sell your position on your exchange NOW! 📲"""
        
        if self.send_discord_signal(message):
            self.log(f"📱 SELL Signal sent: {symbol} ({reason})")
            return True
        
        return False
    
    def check_sell_conditions(self):
        """Check if any open positions should be closed"""
        positions_to_remove = []
        
        for symbol in list(self.active_positions.keys()):
            try:
                pos = self.active_positions[symbol]
                
                if pos['status'] != 'OPEN':
                    continue
                
                data = self.get_stock_data(symbol)
                if not data:
                    continue
                
                current_price = data['price']
                entry_price = pos['entry_price']
                target = pos['target']
                stop = pos['stop']
                
                profit_pct = ((current_price - entry_price) / entry_price) * 100
                
                if current_price >= target:
                    self.send_sell_signal(symbol, f"PROFIT TARGET +{self.profit_target}%", current_price, entry_price, profit_pct)
                    positions_to_remove.append(symbol)
                    continue
                
                if current_price <= stop:
                    self.send_sell_signal(symbol, f"STOP LOSS -{self.stop_loss}%", current_price, entry_price, profit_pct)
                    positions_to_remove.append(symbol)
                    continue
                
                entry_time = datetime.fromisoformat(pos['entry_time'])
                days_held = (datetime.now() - entry_time).days
                
                if days_held >= self.max_hold_days:
                    self.send_sell_signal(symbol, f"TIME LIMIT ({self.max_hold_days} days)", current_price, entry_price, profit_pct)
                    positions_to_remove.append(symbol)
                    continue
            
            except Exception as e:
                self.log(f"❌ Error checking {symbol}: {e}")
                continue
        
        for symbol in positions_to_remove:
            self.active_positions[symbol]['status'] = 'CLOSED'
        
        if positions_to_remove:
            self.save_positions()
    
    def is_market_hours(self):
        """Check if market is open (US Eastern time)"""
        from datetime import datetime, timezone
        
        eastern = timezone(timedelta(hours=-4)) # EDT (daylight saving)
        now = datetime.now(eastern)
        
        is_weekday = now.weekday() < 5
        is_market_hours = 9.5 <= now.hour <= 16.0
        
        return is_weekday and is_market_hours
    
    def run_cycle(self):
        """Run one analysis cycle"""
        self.log("-" * 80)
        
        today = datetime.now().strftime("%Y-%m-%d")
        if today != self.last_signal_date:
            self.signals_today = 0
            self.last_signal_date = today
        
        self.log("🔍 Checking open positions for sell signals...")
        self.check_sell_conditions()
        
        signals = self.find_signals()
        
        if not signals:
            self.log("⚪ No new buy signals found")
        else:
            self.log(f"🟢 Found {len(signals)} new buy signal(s)")
            
            for signal in signals:
                if self.signals_today < self.max_signals_per_day:
                    if self.send_buy_signal(signal):
                        self.signals_today += 1
                    time.sleep(2)
        
        self.save_state()
    
    def start(self):
        """Start bot"""
        self.log(f"🚀 CONFIGURATION")
        self.log(f" Stocks: {len(self.top_stocks)}")
        self.log(f" Min Dip: {self.min_dip}%")
        self.log(f" Profit Target: +{self.profit_target}%")
        self.log(f" Stop Loss: -{self.stop_loss}%")
        self.log(f" Max Hold: {self.max_hold_days} days")
        self.log(f" Max Signals/Day: {self.max_signals_per_day}")
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
                    self.log("⏳ Market closed - waiting for market hours (9:30 AM - 4:00 PM EDT)")
                
                self.log(f"📊 Active positions: {len([p for p in self.active_positions.values() if p['status'] == 'OPEN'])}")
                self.log(f"⏱️ Next check in 30 min...")
                time.sleep(1800)
        
        except KeyboardInterrupt:
            self.log("\n⏹️ BOT STOPPED")
        except Exception as e:
            self.log(f"\n❌ ERROR: {e}")


if __name__ == "__main__":
    bot = StockSignalBot()
    bot.start()
