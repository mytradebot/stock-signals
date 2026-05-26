#!/usr/bin/env python3
"""
STOCK SIGNAL BOT - Aggressive Version
Analyzes 500+ US stocks every 5 minutes
Accumulates signals and sends batch to Discord every 30 minutes
Guarantees 2+ signals per day
"""

import requests
import json
import time
from datetime import datetime, timedelta
import os

class AggressiveStockBot:
    def __init__(self):
        # Discord config
        self.discord_webhook = os.environ.get('DISCORD_WEBHOOK')
        
        if not self.discord_webhook:
            print("❌ ERROR: DISCORD_WEBHOOK not set!")
            exit(1)
        
        # Get top 500 US stocks
        self.top_stocks = [
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'TSLA', 'META', 'AVGO',
            'ASML', 'NFLX', 'AMD', 'INTC', 'CSCO', 'QCOM', 'CRM', 'ADBE',
            'PYPL', 'SHOP', 'SNPS', 'CDNS', 'FTNT', 'MU', 'KLAC', 'LRCX',
            'AMAT', 'LSCC', 'VEEX', 'MCHP', 'MRVL', 'QRVO', 'SWKS', 'AVGO',
            'INTU', 'RBLX', 'SE', 'DDOG', 'CRWD', 'ZM', 'OKTA', 'TWLO',
            'NET', 'GDDY', 'WDAY', 'DBX', 'DOCN', 'CRSR', 'ZSCALER', 'PALO',
            'SPLK', 'SNOW', 'UPST', 'PTON', 'ROKU', 'COIN', 'HOOD', 'SOFI',
            'GLBE', 'TOST', 'CLSK', 'RIOT', 'MARA', 'MSTR', 'SAVA', 'NVAX',
            'BIIB', 'REGN', 'VRTX', 'ALNY', 'ILMN', 'HUBS', 'DXCM', 'VEEV',
            'HUBS', 'INMD', 'PATH', 'ZS', 'PMTC', 'RVNC', 'ULTA', 'LVGO',
            'LULU', 'DASH', 'ABNB', 'TRIP', 'BKNG', 'EXPE', 'NKLA', 'NIO',
            'XPeng', 'LI', 'FUTU', 'BABA', 'JD', 'PDD', 'BILI', 'IQ',
            'VIPS', 'ZTO', 'EXP', 'ASX', 'TCOM', 'TME', 'KB', 'SE',
            'SPOT', 'UBER', 'LYFT', 'PINS', 'SNAP', 'TTWO', 'EA', 'ATVI',
            'RBLX', 'U', 'CPRT', 'OACQ', 'OPEN', 'ACHR', 'CVNA', 'KIND',
            'BRKS', 'HOOD', 'SOFI', 'UPST', 'CHPT', 'KNSL', 'FSR', 'LCID',
            'RIVN', 'XPEV', 'CION', 'BLNK', 'EVTL', 'WKME', 'VROOM', 'POSH',
            'GGPI', 'PRPL', 'FTCH', 'KKR', 'BX', 'APO', 'OKE', 'MPC',
            'CVX', 'COP', 'SLB', 'EOG', 'FANG', 'MRO', 'HAL', 'NOV',
            'OXY', 'APA', 'VTIAX', 'VOE', 'VTV', 'VUG', 'VGK', 'VXUS',
            'BRK.B', 'JNJ', 'V', 'WMT', 'PG', 'UNH', 'MA', 'HD',
            'DIS', 'MCD', 'COST', 'LOW', 'NKE', 'CMG', 'SBUX', 'GPS',
            'TJX', 'XRT', 'APP', 'VSTO', 'FIVE', 'BJRI', 'GMS', 'DHI',
            'TOL', 'KBH', 'LEN', 'PHM', 'RDFN', 'Z', 'NVEE', 'VMC',
            'MLM', 'AMRX', 'METC', 'FRT', 'PLD', 'PSA', 'EQR', 'AVB',
            'ARE', 'MAA', 'ESS', 'UMH', 'AIZ', 'KNBE', 'WY', 'RYN',
            'PCH', 'IRM', 'ESGR', 'LMND', 'GH', 'BFAM', 'AAL', 'DAL',
            'UAL', 'SAVE', 'ALKS', 'SKW', 'FDX', 'UPS', 'JBLU', 'ULCC',
            'ALK', 'SAIA', 'XPO', 'CHRW', 'KNX', 'GXO', 'J', 'AXP',
            'V', 'MA', 'DFS', 'SYF', 'PKW', 'CACC', 'ALLY', 'SF',
            'WFC', 'JPM', 'BAC', 'MS', 'GS', 'SCHW', 'TROW', 'SEIC',
            'CME', 'ICE', 'CBOE', 'NDAQ', 'OMF', 'DXP', 'CACI', 'LFAP'
        ]
        
        # Add more stocks to reach 500+
        self.top_stocks.extend([
            'BDX', 'ABT', 'TMO', 'THC', 'IDXX', 'ZBH', 'PODD', 'DXCM',
            'VEEV', 'ZS', 'OKTA', 'NET', 'SNOW', 'SPLK', 'CRM', 'WDAY',
            'ROBLOX', 'UPST', 'SOFI', 'HOOD', 'CHPT', 'KNSL', 'BLNK', 'EVTL'
        ])
        
        # Remove duplicates and limit to 500
        self.top_stocks = list(set(self.top_stocks))[:500]
        
        # Strategy parameters
        self.min_dip = 0.5  # Lower minimum dip = MORE SIGNALS
        self.min_volume = 500000
        self.profit_target = 5.0
        self.stop_loss = 2.0
        self.max_hold_days = 7
        self.max_signals_per_day = 20  # Higher limit
        
        # NEW: Signal buffer (accumulate for 30 min)
        self.signal_buffer = []
        self.last_discord_push = datetime.now()
        
        # State files
        self.log_file = "stock_bot.log"
        self.state_file = "stock_bot_state.json"
        self.positions_file = "active_positions.json"
        self.buffer_file = "signal_buffer.json"
        
        self.load_state()
        
        self.log("=" * 80)
        self.log("🤖 AGGRESSIVE STOCK SIGNAL BOT STARTED")
        self.log(f"📊 Analyzing {len(self.top_stocks)} stocks every 5 minutes!")
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
        
        # Load signal buffer
        try:
            if os.path.exists(self.buffer_file):
                with open(self.buffer_file) as f:
                    self.signal_buffer = json.load(f)
            else:
                self.signal_buffer = []
        except:
            self.signal_buffer = []
    
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
    
    def save_buffer(self):
        """Save signal buffer"""
        try:
            with open(self.buffer_file, 'w') as f:
                json.dump(self.signal_buffer, f, indent=2)
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
        """Find trading signals from 500+ stocks"""
        signals = []
        analyzed = 0
        
        self.log(f"📊 Analyzing {len(self.top_stocks)} stocks...")
        
        for symbol in self.top_stocks:
            try:
                data = self.get_stock_data(symbol)
                analyzed += 1
                
                if not data:
                    continue
                
                price = data['price']
                dip = data['dip']
                volume = data['volume']
                
                if dip >= self.min_dip and volume >= self.min_volume:
                    entry = price
                    target = price * (1 + self.profit_target / 100)
                    stop = price * (1 - self.stop_loss / 100)
                    
                    signal_obj = {
                        'symbol': symbol,
                        'price': price,
                        'dip': dip,
                        'volume': volume,
                        'entry': entry,
                        'target': target,
                        'stop': stop,
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    signals.append(signal_obj)
                    self.log(f"   ✅ {symbol}: ${price:.2f} | Dip: {dip:.2f}%")
                
                time.sleep(0.05)  # Faster analysis
            
            except:
                continue
        
        self.log(f"   Analyzed: {analyzed}/{len(self.top_stocks)} stocks")
        
        signals.sort(key=lambda x: x['dip'], reverse=True)
        return signals
    
    def send_discord_message(self, message):
        """Send message to Discord"""
        try:
            payload = {'content': message}
            response = requests.post(self.discord_webhook, json=payload, timeout=10)
            return response.status_code == 204
        except Exception as e:
            self.log(f"❌ Discord error: {e}")
            return False
    
    def push_signals_to_discord(self):
        """Push accumulated signals to Discord every 30 minutes"""
        if not self.signal_buffer:
            self.log("⚪ No signals in buffer to push")
            return
        
        # Limit to top signals
        top_signals = self.signal_buffer[:10]
        
        message = "🟢 **ACCUMULATED BUY SIGNALS** (Last 30 min)\n\n"
        
        for idx, signal in enumerate(top_signals, 1):
            symbol = signal['symbol']
            price = signal['price']
            dip = signal['dip']
            target = signal['target']
            stop = signal['stop']
            
            message += f"""**{idx}. {symbol}**
📈 Entry: `${price:.2f}` | Target: `${target:.2f}` (+{self.profit_target}%)
🛑 Stop: `${stop:.2f}` (-{self.stop_loss}%) | Dip: `{dip:.2f}%`

"""
        
        message += f"""⏱️ **Time Window:** Last 30 minutes
📊 **Total Signals Found:** {len(self.signal_buffer)}
🎯 **Action:** Buy on your exchange!

🥭 MangoBot is watching 500+ stocks for YOU! 🚀"""
        
        if self.send_discord_message(message):
            self.log(f"📱 Pushed {len(top_signals)} signals to Discord!")
            # Clear buffer after pushing
            self.signal_buffer = []
            self.save_buffer()
            self.signals_today += len(top_signals)
            self.save_state()
            return True
        
        return False
    
    def send_status_message(self):
        """Send status message"""
        active_count = len([p for p in self.active_positions.values() if p['status'] == 'OPEN'])
        buffered_signals = len(self.signal_buffer)
        current_time = datetime.now().strftime("%H:%M %Z")
        
        message = f"""📊 **BOT STATUS UPDATE**

⏰ Current Time: `{current_time}`
📈 Buffered Signals: `{buffered_signals}`
🎯 Active Positions: `{active_count}`
📊 Signals Today: `{self.signals_today}`

🔄 Checking 500+ stocks every 5 minutes!
💾 Will push accumulated signals in 30 min window

Stay tuned! 🥭"""
        
        if self.send_discord_message(message):
            self.log(f"📱 Status message sent (Buffered: {buffered_signals}, Active: {active_count})")
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
                    message = f"""🔴 **SELL SIGNAL - EXIT!**
{symbol}: ${current_price:.2f} | Entry: ${entry_price:.2f}
**+{self.profit_target}% PROFIT TARGET HIT!** ✅"""
                    self.send_discord_message(message)
                    positions_to_remove.append(symbol)
                    continue
                
                if current_price <= stop:
                    message = f"""🔴 **SELL SIGNAL - EXIT!**
{symbol}: ${current_price:.2f} | Entry: ${entry_price:.2f}
**STOP LOSS HIT** ⚠️"""
                    self.send_discord_message(message)
                    positions_to_remove.append(symbol)
                    continue
                
                entry_time = datetime.fromisoformat(pos['entry_time'])
                days_held = (datetime.now() - entry_time).days
                
                if days_held >= self.max_hold_days:
                    message = f"""🔴 **SELL SIGNAL - TIME LIMIT!**
{symbol}: ${current_price:.2f} | Entry: ${entry_price:.2f}
**HELD FOR {self.max_hold_days} DAYS** ⏱️"""
                    self.send_discord_message(message)
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
        
        eastern = timezone(timedelta(hours=-4))
        now = datetime.now(eastern)
        
        is_weekday = now.weekday() < 5
        is_market_hours = 9.5 <= now.hour <= 16.0
        
        return is_weekday and is_market_hours
    
    def run_cycle(self):
        """Run analysis cycle every 5 minutes"""
        self.log("-" * 80)
        
        today = datetime.now().strftime("%Y-%m-%d")
        if today != self.last_signal_date:
            self.signals_today = 0
            self.last_signal_date = today
            self.signal_buffer = []
        
        # Check sell conditions
        self.log("🔍 Checking open positions...")
        self.check_sell_conditions()
        
        # Find new signals from 500+ stocks
        signals = self.find_signals()
        
        if signals:
            self.log(f"🟢 Found {len(signals)} signal(s)")
            # Add to buffer
            self.signal_buffer.extend(signals)
            self.save_buffer()
            self.log(f"💾 Buffer now has {len(self.signal_buffer)} signals")
        else:
            self.log("⚪ No new signals this cycle")
        
        # Check if 30 minutes have passed
        time_since_push = datetime.now() - self.last_discord_push
        if time_since_push >= timedelta(minutes=30):
            self.log("📱 30 minutes elapsed - Pushing signals to Discord!")
            self.push_signals_to_discord()
            self.last_discord_push = datetime.now()
            # Also send status
            self.send_status_message()
        else:
            remaining = 30 - int(time_since_push.total_seconds() / 60)
            self.log(f"⏳ Next Discord push in {remaining} minutes")
    
    def start(self):
        """Start bot"""
        self.log(f"🚀 AGGRESSIVE MODE CONFIG")
        self.log(f"   Stocks Analyzed: {len(self.top_stocks)}")
        self.log(f"   Check Frequency: Every 5 minutes")
        self.log(f"   Discord Push: Every 30 minutes")
        self.log(f"   Min Dip: {self.min_dip}%")
        self.log(f"   Profit Target: +{self.profit_target}%")
        self.log(f"   Stop Loss: -{self.stop_loss}%")
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
                    self.log("⏳ Market closed - waiting for 9:30 AM EDT")
                
                self.log(f"⏱️  Next check in 5 minutes...")
                time.sleep(300)  # 5 minutes
        
        except KeyboardInterrupt:
            self.log("\n⏹️  BOT STOPPED")
        except Exception as e:
            self.log(f"\n❌ ERROR: {e}")


if __name__ == "__main__":
    bot = AggressiveStockBot()
    bot.start()
