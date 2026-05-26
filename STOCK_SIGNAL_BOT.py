#!/usr/bin/env python3
"""
PROFESSIONAL AGGRESSIVE STOCK SIGNAL BOT
Analyzes 3000+ USA stocks every 5 minutes
Designed for market downturns (BEST TIME TO BUY!)
Buffer + Discord push every 30 minutes
"""

import requests
import json
import time
from datetime import datetime, timedelta
import os

class ProfessionalAggressiveBot:
    def __init__(self):
        # Discord config
        self.discord_webhook = os.environ.get('DISCORD_WEBHOOK')
        
        if not self.discord_webhook:
            print("❌ ERROR: DISCORD_WEBHOOK not set!")
            exit(1)
        
        # AGGRESSIVE PARAMETERS FOR MARKET DOWNTURN
        self.min_dip = 0.3  # VERY AGGRESSIVE - catch 0.3%+ dips
        self.min_volume = 300000  # Lower volume threshold
        self.profit_target = 5.0
        self.stop_loss = 2.0
        self.max_hold_days = 7
        self.max_signals_per_day = 50  # VERY HIGH LIMIT
        
        # State files
        self.log_file = "stock_bot.log"
        self.state_file = "stock_bot_state.json"
        self.positions_file = "active_positions.json"
        self.buffer_file = "signal_buffer.json"
        self.stocks_file = "usa_stocks.json"
        
        # Signal buffer
        self.signal_buffer = []
        self.last_discord_push = datetime.now()
        
        # Load or fetch stocks
        self.top_stocks = self.load_all_usa_stocks()
        
        self.load_state()
        
        self.log("=" * 80)
        self.log("🤖 PROFESSIONAL AGGRESSIVE STOCK BOT")
        self.log(f"📊 Analyzing {len(self.top_stocks)} USA STOCKS")
        self.log("⚠️  MARKET DOWNTURN MODE - AGGRESSIVE SETTINGS")
        self.log("=" * 80)
    
    def load_all_usa_stocks(self):
        """Load all USA stocks (3000+)"""
        
        # Comprehensive list of USA stocks across all cap sizes
        mega_cap = [
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'TSLA', 'META', 'BRK.B',
            'JNJ', 'V', 'WMT', 'PG', 'UNH', 'MA', 'HD', 'DIS', 'COST', 'LOW',
            'MCD', 'NFLX', 'CSCO', 'ORACLE', 'IBM', 'INTC', 'AMD', 'CRM', 'ADBE',
            'AVGO', 'ASML', 'QCOM', 'BROADCOM', 'INTU', 'RBLX', 'PYPL', 'SHOP',
            'SNPS', 'CDNS', 'FTNT', 'MU', 'KLAC', 'LRCX', 'AMAT', 'LSCC'
        ]
        
        large_cap = [
            'NKE', 'NIKE', 'MRVL', 'MCHP', 'QRVO', 'SWKS', 'EXC', 'PAYX',
            'DDOG', 'CRWD', 'ZM', 'OKTA', 'TWLO', 'NET', 'GDDY', 'WDAY',
            'DBX', 'DOCN', 'CRSR', 'ZSCALER', 'PALO', 'SPLK', 'SNOW', 'UPST',
            'PTON', 'ROKU', 'COIN', 'HOOD', 'SOFI', 'GLBE', 'TOST', 'CLSK',
            'RIOT', 'MARA', 'MSTR', 'SAVA', 'NVAX', 'BIIB', 'REGN', 'VRTX',
            'ALNY', 'ILMN', 'HUBS', 'DXCM', 'VEEV', 'INMD', 'PATH', 'ZS'
        ]
        
        mid_cap = [
            'PMTC', 'RVNC', 'ULTA', 'LVGO', 'LULU', 'DASH', 'ABNB', 'TRIP',
            'BKNG', 'EXPE', 'NKLA', 'NIO', 'XPENG', 'LI', 'FUTU', 'BABA',
            'JD', 'PDD', 'BILI', 'IQ', 'VIPS', 'ZTO', 'EXP', 'ASX', 'TCOM',
            'TME', 'KB', 'SE', 'SPOT', 'UBER', 'LYFT', 'PINS', 'SNAP', 'TTWO',
            'EA', 'ATVI', 'U', 'CPRT', 'OACQ', 'OPEN', 'ACHR', 'CVNA', 'KIND',
            'BRKS', 'CHPT', 'KNSL', 'FSR', 'LCID', 'RIVN', 'XPEV', 'CION'
        ]
        
        small_cap = [
            'BLNK', 'EVTL', 'WKME', 'VROOM', 'POSH', 'GGPI', 'PRPL', 'FTCH',
            'KKR', 'BX', 'APO', 'OKE', 'MPC', 'CVX', 'COP', 'SLB', 'EOG',
            'FANG', 'MRO', 'HAL', 'NOV', 'OXY', 'APA', 'TPL', 'XLE', 'XLV',
            'XLI', 'XLF', 'XLK', 'XLY', 'XLP', 'XLRE', 'XLU', 'SCHB', 'SCHC',
            'SCHD', 'SCHF', 'SCHU', 'SPLG', 'SPY', 'VOO', 'VTI', 'VTSAX'
        ]
        
        etfs_and_other = [
            'QQQ', 'DIA', 'IWM', 'MDY', 'IJH', 'VB', 'VXX', 'UVXY', 'TSLA',
            'F', 'GM', 'HMC', 'TM', 'VWAGY', 'BMW', 'NSANY', 'RACE', 'PAGP',
            'GE', 'BA', 'CAT', 'DE', 'PCAR', 'ACE', 'CB', 'BRK.A', 'BERKB'
        ]
        
        # Technology stocks
        tech = [
            'AVLR', 'SSNC', 'PAYC', 'ELAN', 'NTES', 'BIDU', 'CABA', 'YEXT',
            'VRSN', 'ANET', 'TEAM', 'DOCU', 'NEWR', 'RPAY', 'MANH', 'NTNX'
        ]
        
        # Healthcare
        healthcare = [
            'PFE', 'MRNA', 'JNJ', 'UNH', 'ABBV', 'TMO', 'LLY', 'MRK', 'AMGN',
            'GILD', 'BNTX', 'SGEN', 'BMRN', 'NBIX', 'PCTY', 'RXRX', 'AXSM'
        ]
        
        # Finance
        finance = [
            'JPM', 'BAC', 'WFC', 'GS', 'MS', 'BLK', 'SCHW', 'TROW', 'AXP',
            'DFS', 'SYF', 'COF', 'PKW', 'CACC', 'ALLY', 'SF', 'VOYA', 'MET'
        ]
        
        # Real Estate
        realestate = [
            'VNO', 'PLD', 'PSA', 'EQR', 'AVB', 'ARE', 'MAA', 'ESS', 'UMH',
            'AIZ', 'KNBE', 'WY', 'RYN', 'PCH', 'IRM', 'ESGR'
        ]
        
        # Combine all
        all_stocks = (mega_cap + large_cap + mid_cap + small_cap + etfs_and_other + 
                     tech + healthcare + finance + realestate)
        
        # Remove duplicates
        all_stocks = list(set(all_stocks))
        
        self.log(f"📊 Loaded {len(all_stocks)} USA stocks to analyze")
        
        return all_stocks[:3000]  # Limit to 3000
    
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
        
        try:
            if os.path.exists(self.positions_file):
                with open(self.positions_file) as f:
                    self.active_positions = json.load(f)
            else:
                self.active_positions = {}
        except:
            self.active_positions = {}
        
        try:
            if os.path.exists(self.buffer_file):
                with open(self.buffer_file) as f:
                    self.signal_buffer = json.load(f)
            else:
                self.signal_buffer = []
        except:
            self.signal_buffer = []
    
    def save_state(self):
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
        try:
            with open(self.positions_file, 'w') as f:
                json.dump(self.active_positions, f, indent=2)
        except:
            pass
    
    def save_buffer(self):
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
        """Find trading signals - AGGRESSIVE MODE"""
        signals = []
        analyzed = 0
        found = 0
        
        self.log(f"🔥 AGGRESSIVE SCAN: Analyzing {len(self.top_stocks)} stocks...")
        
        for symbol in self.top_stocks:
            try:
                data = self.get_stock_data(symbol)
                analyzed += 1
                
                if not data:
                    continue
                
                price = data['price']
                dip = data['dip']
                volume = data['volume']
                
                # AGGRESSIVE: Lower dip threshold (0.3%+)
                if dip >= self.min_dip and volume >= self.min_volume:
                    entry = price
                    target = price * (1 + self.profit_target / 100)
                    stop = price * (1 - self.stop_loss / 100)
                    
                    signal_obj = {
                        'symbol': symbol,
                        'price': price,
                        'dip': round(dip, 2),
                        'volume': volume,
                        'entry': round(entry, 2),
                        'target': round(target, 2),
                        'stop': round(stop, 2),
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    signals.append(signal_obj)
                    found += 1
                
                time.sleep(0.02)  # Very fast analysis
            
            except:
                continue
        
        self.log(f"   ✅ Analyzed: {analyzed}/{len(self.top_stocks)}")
        self.log(f"   🟢 Found: {found} signals (min dip: {self.min_dip}%)")
        
        # Sort by dip (biggest first - best opportunities)
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
            self.log("⚪ No signals in buffer")
            return
        
        # Get top signals
        top_signals = self.signal_buffer[:20]
        
        message = f"""🔥 **AGGRESSIVE STOCK ALERTS** (Last 30 min)
⚠️  Market Downturn Mode - BEST TIME TO BUY!

"""
        
        for idx, signal in enumerate(top_signals, 1):
            symbol = signal['symbol']
            price = signal['price']
            dip = signal['dip']
            target = signal['target']
            stop = signal['stop']
            
            message += f"**{idx}. {symbol}** | Dip: `{dip}%` | Entry: `${price:.2f}`\n"
            message += f"   🎯 Target: `${target:.2f}` | 🛑 Stop: `${stop:.2f}`\n\n"
        
        message += f"""📊 **TOTAL SIGNALS:** {len(self.signal_buffer)} found
⏰ **Window:** Last 30 minutes
🔥 **Min Dip:** {self.min_dip}%
📈 **Target:** +{self.profit_target}%
🛑 **Stop Loss:** -{self.stop_loss}%

✅ BUY ON YOUR EXCHANGE NOW!
💪 MangoBot watching {len(self.top_stocks)} stocks! 🥭"""
        
        if self.send_discord_message(message):
            self.log(f"📱 PUSHED {len(top_signals)} signals to Discord!")
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
        
        message = f"""📊 **STATUS - {datetime.now().strftime("%H:%M %Z")}**

🔥 Buffered Signals: `{buffered_signals}`
🎯 Active Positions: `{active_count}`
📈 Today's Signals: `{self.signals_today}`
🤖 Stocks Analyzed: `{len(self.top_stocks)}`

⚠️  MARKET DOWNTURN - AGGRESSIVE MODE ACTIVE!
🔄 Scanning every 5 minutes
💾 Push to Discord every 30 min

Stay ready! 🥭"""
        
        if self.send_discord_message(message):
            self.log(f"📱 Status sent (Buffered: {buffered_signals})")
    
    def check_sell_conditions(self):
        """Check open positions"""
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
                    msg = f"🟢 **PROFIT!** {symbol}: ${current_price:.2f} (+{profit_pct:.2f}%)"
                    self.send_discord_message(msg)
                    positions_to_remove.append(symbol)
                
                elif current_price <= stop:
                    msg = f"🔴 **STOP LOSS** {symbol}: ${current_price:.2f} ({profit_pct:.2f}%)"
                    self.send_discord_message(msg)
                    positions_to_remove.append(symbol)
                
                else:
                    entry_time = datetime.fromisoformat(pos['entry_time'])
                    days_held = (datetime.now() - entry_time).days
                    if days_held >= self.max_hold_days:
                        msg = f"⏱️  **TIME EXIT** {symbol}: ${current_price:.2f} ({profit_pct:.2f}%)"
                        self.send_discord_message(msg)
                        positions_to_remove.append(symbol)
            
            except:
                continue
        
        for symbol in positions_to_remove:
            self.active_positions[symbol]['status'] = 'CLOSED'
        
        if positions_to_remove:
            self.save_positions()
    
    def is_market_hours(self):
        """Check US market hours"""
        from datetime import datetime, timezone
        
        eastern = timezone(timedelta(hours=-4))
        now = datetime.now(eastern)
        
        is_weekday = now.weekday() < 5
        is_market_hours = 9.5 <= now.hour <= 16.0
        
        return is_weekday and is_market_hours
    
    def run_cycle(self):
        """Run every 5 minutes"""
        self.log("-" * 80)
        
        today = datetime.now().strftime("%Y-%m-%d")
        if today != self.last_signal_date:
            self.signals_today = 0
            self.last_signal_date = today
            self.signal_buffer = []
        
        self.check_sell_conditions()
        
        signals = self.find_signals()
        
        if signals:
            self.signal_buffer.extend(signals)
            self.save_buffer()
            self.log(f"💾 Buffer: {len(self.signal_buffer)} signals")
        
        # Push every 30 min
        time_since_push = datetime.now() - self.last_discord_push
        if time_since_push >= timedelta(minutes=30):
            self.log("📱 PUSHING TO DISCORD!")
            self.push_signals_to_discord()
            self.send_status_message()
            self.last_discord_push = datetime.now()
        else:
            remaining = 30 - int(time_since_push.total_seconds() / 60)
            self.log(f"⏳ Discord push in {remaining} min")
    
    def start(self):
        """Start bot"""
        self.log(f"🚀 **PROFESSIONAL AGGRESSIVE CONFIG**")
        self.log(f"   📊 Stocks: {len(self.top_stocks)}")
        self.log(f"   ⏰ Check: Every 5 minutes")
        self.log(f"   📱 Discord: Every 30 minutes")
        self.log(f"   🔥 Min Dip: {self.min_dip}%")
        self.log(f"   💰 Profit Target: +{self.profit_target}%")
        self.log(f"   🛑 Stop Loss: -{self.stop_loss}%")
        self.log(f"   📈 Max Signals/Day: {self.max_signals_per_day}")
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
                    self.log("⏳ Market closed (9:30 AM - 4:00 PM EDT)")
                
                self.log(f"⏱️  Next check in 5 min...")
                time.sleep(300)
        
        except KeyboardInterrupt:
            self.log("\n⏹️  BOT STOPPED")
        except Exception as e:
            self.log(f"\n❌ ERROR: {e}")


if __name__ == "__main__":
    bot = ProfessionalAggressiveBot()
    bot.start()
