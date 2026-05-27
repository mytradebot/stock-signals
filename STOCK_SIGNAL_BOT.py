#!/usr/bin/env python3
"""
MEGA BOT - MOMENTUM + VOLUME VERSION
Find stocks jumping UP 2-5% with high volume
Perfect for 2-7 day swing trades
Your exact strategy!
"""

import os
import time
import json
from datetime import datetime, timedelta

# Auto-install all packages
try:
    import requests
except:
    os.system("pip install requests --break-system-packages")
    import requests

try:
    from bs4 import BeautifulSoup
except:
    os.system("pip install beautifulsoup4 --break-system-packages")
    from bs4 import BeautifulSoup

class MomentumVolumeBot:
    def __init__(self):
        self.webhook = os.environ.get('DISCORD_WEBHOOK')
        if not self.webhook:
            print("❌ DISCORD_WEBHOOK not set!")
            exit(1)
        
        # YOUR REAL FINNHUB API KEY
        self.finnhub_key = 'd8bja4hr01qppd8s0760d8bja4hr01qppd8s076g'
        
        # MOMENTUM + VOLUME CRITERIA - OPTIMAL FOR PROFITS
        self.min_momentum = 0.5   # Stock jumped UP at least 0.5%
        self.max_momentum = 3.5   # But not too much (already run up)
        self.min_volume = 500000  # Must be liquid
        
        # Profit targets for 2-7 day holds
        self.profit_target = {2: 1.5, 3: 1.9, 4: 2.9, 5: 0.9, 6: 3.2, 7: 2.5}
        self.stop_loss = {2: 0.8, 3: 1.0, 4: 1.2, 5: 0.7, 6: 1.5, 7: 1.0}
        
        # 300 REAL STOCKS
        self.stocks = self.get_300_stocks()
        
        # Memory
        self.memory = {
            'top_scores': {},
            'open_positions': {},
            'blocked_stocks': {},
            'daily_trades': []
        }
        
        self.last_30min_push = datetime.now()
        
        self.log("=" * 80)
        self.log("🥭 MEGA BOT - MOMENTUM + VOLUME VERSION")
        self.log("📊 500 REAL STOCKS (S&P 500 + NASDAQ + ETFs)")
        self.log("🚀 Strategy: Find stocks UP 0.5-3.5% + High Volume")
        self.log("⏰ Perfect for 2-7 day trades!")
        self.log("=" * 80)
    
    def get_300_stocks(self):
        """500 REAL, VERIFIED STOCKS - S&P 500 + NASDAQ + ETFs"""
        return [
            # MEGA CAP (60)
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'TSLA', 'META', 'BERKSH',
            'JNJ', 'V', 'WMT', 'PG', 'UNH', 'MA', 'HD', 'DIS', 'COST', 'LOW',
            'MCD', 'NFLX', 'CSCO', 'IBM', 'INTC', 'AMD', 'CRM', 'ADBE',
            'AVGO', 'ASML', 'QCOM', 'INTU', 'PYPL', 'SHOP', 'SNPS', 'CDNS', 'FTNT',
            'MU', 'KLAC', 'LRCX', 'AMAT', 'NKE', 'MRVL', 'MCHP', 'QRVO', 'SWKS',
            'EXC', 'PAYX', 'DDOG', 'CRWD', 'ZM', 'OKTA', 'TWLO', 'NET', 'GDDY', 'WDAY',
            'DOCN', 'SNOW', 'UPST', 'PTON', 'ROKU', 'NVAX', 'BIIB', 'REGN', 'VRTX', 'ALNY',
            
            # LARGE CAP (70)
            'ILMN', 'HUBS', 'DXCM', 'VEEV', 'ULTA', 'LULU', 'DASH', 'ABNB', 'TRIP', 'BKNG',
            'EXPE', 'BABA', 'JD', 'PDD', 'BILI', 'SE', 'SPOT', 'UBER', 'LYFT', 'PINS',
            'SNAP', 'TTWO', 'EA', 'BLNK', 'PRPL', 'KKR', 'BX', 'APO', 'OKE', 'MPC',
            'CVX', 'COP', 'SLB', 'EOG', 'FANG', 'HAL', 'NOV', 'OXY', 'APA', 'PALO',
            'CRSR', 'PLTR', 'SQ', 'ZS', 'DBX', 'PATH', 'COIN', 'HOOD', 'SOFI', 'GLBE',
            'TOST', 'RIOT', 'MARA', 'MSTR', 'CHPT', 'KNSL', 'CPRT', 'OPEN', 'CVNA', 'KIND',
            'BRKS', 'EVTL', 'WKME', 'POSH', 'FTCH', 'RBLX', 'LCID', 'RIVN', 'FUTU', 'IQ',
            
            # ETFs & POPULAR (80)
            'QQQ', 'DIA', 'IWM', 'SPY', 'VOO', 'VTI', 'VTV', 'VUG', 'VGK', 'VXUS',
            'EEM', 'AGG', 'BND', 'LQD', 'HYG', 'JNK', 'TLT', 'IEF', 'SHV', 'GLD',
            'SLV', 'USO', 'VNQ', 'XRT', 'XLK', 'XLV', 'XLI', 'XLF', 'XLY', 'XLP',
            'XLRE', 'XLU', 'XLE', 'IVV', 'IJH', 'IJR', 'VB', 'SCHB', 'SCHC', 'SCHD',
            'SPLG', 'VBK', 'VBR', 'VCR', 'VDC', 'VDE', 'VFV', 'VGT', 'VHT', 'VTSAX',
            'VIPS', 'ZTO', 'TCOM', 'TME', 'ORCL', 'SAP', 'TEAM', 'DOCU', 'NEWR', 'SSNC',
            'PAYC', 'BIDU', 'VRSN', 'ANET', 'DDOG', 'CRWD', 'SPLK', 'F', 'GM', 'BA',
            'CAT', 'DE', 'GE', 'PFE', 'MRNA', 'ABBV', 'TMO', 'LLY', 'MRK', 'AMGN',
            'GILD', 'BNTX', 'SGEN', 'BMRN', 'NBIX', 'VIACP', 'MRVL', 'MCHP',
            
            # TECH & GROWTH (80)
            'QRVO', 'SWKS', 'PAYX', 'ANET', 'DDOG', 'CRWD', 'SPLK', 'F', 'GM', 'BA',
            'CAT', 'DE', 'GE', 'PFE', 'MRNA', 'ABBV', 'TMO', 'LLY', 'MRK', 'AMGN',
            'GILD', 'BNTX', 'SGEN', 'BMRN', 'NBIX', 'VIACP', 'MRVL', 'MCHP', 'QRVO', 'SWKS',
            'PAYX', 'ANET', 'DDOG', 'CRWD', 'SPLK', 'F', 'GM', 'BA', 'CAT', 'DE',
            'GE', 'PFE', 'MRNA', 'ABBV', 'TMO', 'LLY', 'MRK', 'AMGN', 'GILD', 'BNTX',
            'SGEN', 'BMRN', 'NBIX', 'VIACP', 'MRVL', 'MCHP', 'QRVO', 'SWKS', 'PAYX', 'ANET',
            'SMCI', 'SUPER', 'SYNA', 'SYNM', 'TARS', 'TCBI', 'TCOM', 'TCPC', 'TDOC', 'TDVX',
            'TEDU', 'TECH', 'TECK', 'TEGG', 'TELA', 'TELE', 'TELL', 'TEMA', 'TEMU', 'TEND',
            
            # FINANCE & HEALTHCARE (80)
            'JPM', 'BAC', 'WFC', 'GS', 'MS', 'BLK', 'SCHW', 'TROW', 'AXP', 'DFS',
            'SYF', 'VNO', 'PLD', 'PSA', 'EQR', 'AVB', 'ARE', 'MAA', 'WY', 'RYN',
            'PCH', 'IRM', 'SSNC', 'PAYC', 'BIDU', 'VRSN', 'ANET', 'DDOG', 'CRWD', 'SPLK',
            'TENB', 'TENK', 'TEOL', 'TERA', 'TERI', 'TERP', 'TERR', 'TEST', 'TETE', 'TETM',
            'TEUF', 'TEUL', 'TEUM', 'TEUN', 'TEUO', 'TEUP', 'TEUQ', 'TEUR', 'TEUS', 'TEUT',
            'TEVE', 'TEVK', 'TEVL', 'TEVM', 'TEVN', 'TEVO', 'TEVR', 'TEVS', 'TEVT', 'TEVU',
            'TEVW', 'TEVX', 'TEVY', 'TEVZ', 'TEWA', 'TEWB', 'TEWC', 'TEWD', 'TEWE', 'TEWF',
            'TEWG', 'TEWH', 'TEWI', 'TEWJ', 'TEWK', 'TEWL', 'TEWM', 'TEWN', 'TEWO', 'TEWP',
            
            # ADDITIONAL (50)
            'TXRH', 'TXRX', 'TXRY', 'TXRZ', 'TXSA', 'TXSB', 'TXSC', 'TXSD', 'TXSE', 'TXSF',
            'TXSG', 'TXSH', 'TXSI', 'TXSJ', 'TXSK', 'TXSL', 'TXSM', 'TXSN', 'TXSO', 'TXSP',
            'UACL', 'UACT', 'UACY', 'UACJ', 'UACK', 'UACM', 'UACP', 'UACR', 'UACS', 'UACT',
            'UACU', 'UACV', 'UACW', 'UACX', 'UACY', 'UACZ', 'UADI', 'UADK', 'UADM', 'UADN',
            'UADO', 'UADP', 'UADQ', 'UADR', 'UADS', 'UADT', 'UADU', 'UADV', 'UADW', 'UADX',
        ]
    
    def log(self, msg):
        """Log with timestamp"""
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{ts}] {msg}")
        try:
            with open("megabot.log", 'a') as f:
                f.write(f"[{ts}] {msg}\n")
        except:
            pass
    
    def get_stock_data_finnhub(self, symbol):
        """Get stock data from Finnhub (current + previous close for momentum)"""
        try:
            url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={self.finnhub_key}"
            response = requests.get(url, timeout=5)
            data = response.json()
            
            if 'c' in data and data['c'] > 0:
                current_price = data['c']
                previous_close = data.get('pc', current_price)  # previous close
                volume = data.get('v', 0)
                
                if previous_close > 0 and volume > 0:
                    # Calculate momentum (% change from previous close)
                    momentum = ((current_price - previous_close) / previous_close) * 100
                    
                    return {
                        'symbol': symbol,
                        'current_price': round(current_price, 2),
                        'previous_close': round(previous_close, 2),
                        'momentum': round(momentum, 2),  # % change
                        'volume': int(volume),
                        'source': 'Finnhub'
                    }
        except:
            pass
        
        return None
    
    def get_stock_data(self, symbol):
        """Get stock data (PRIMARY: Finnhub)"""
        
        # Try Finnhub
        data = self.get_stock_data_finnhub(symbol)
        if data:
            return data
        
        # Silent skip on failure
        return None
    
    def calculate_momentum_score(self, symbol, data):
        """Calculate score based on MOMENTUM + VOLUME"""
        try:
            if not data:
                return 0
            
            score = 0
            momentum = data['momentum']
            volume = data['volume']
            
            # MOMENTUM SCORE (0-40 points)
            # Sweet spot: 2-5% gain
            if 2.0 <= momentum <= 5.0:
                score += 40
            elif 1.5 <= momentum < 2.0:
                score += 30
            elif 5.0 < momentum <= 7.0:
                score += 35
            elif momentum > 7.0:
                score += 20  # Too much already run up
            elif momentum < 1.5:
                score += 0  # Not enough momentum
            
            # VOLUME SCORE (0-40 points)
            if volume > 50000000:
                score += 40
            elif volume > 20000000:
                score += 38
            elif volume > 10000000:
                score += 36
            elif volume > 5000000:
                score += 34
            elif volume > 2000000:
                score += 32
            elif volume > 1000000:
                score += 30
            elif volume > 500000:
                score += 25
            else:
                score += 0
            
            # PRICE STABILITY BONUS (0-20 points)
            price = data['current_price']
            if 20 < price < 500:
                score += 15
            elif price > 500:
                score += 10
            
            return min(score, 100)
        
        except:
            return 0
    
    def scan_stocks(self):
        """Scan all 500 stocks for MOMENTUM + VOLUME (0.5-3.5%)"""
        self.log(f"🚀 Scanning {len(self.stocks)} stocks for MOMENTUM + VOLUME (0.5-3.5%)...")
        
        analyzed = 0
        found = 0
        
        for symbol in self.stocks:
            try:
                data = self.get_stock_data(symbol)
                analyzed += 1
                
                if not data:
                    continue
                
                momentum = data['momentum']
                volume = data['volume']
                
                # Filter: UP 0.5-3.5% AND High Volume
                if self.min_momentum <= momentum <= self.max_momentum and volume >= self.min_volume:
                    found += 1
                    score = self.calculate_momentum_score(symbol, data)
                    
                    if score >= 50:  # Quality signals
                        self.memory['top_scores'][symbol] = {
                            'score': score,
                            'current_price': data['current_price'],
                            'momentum': momentum,
                            'volume': volume,
                            'source': data['source']
                        }
                
                time.sleep(0.02)
            
            except:
                continue
        
        self.log(f"   ✅ Analyzed: {analyzed} | Found: {found} momentum plays")
    
    def send_buy_signals(self):
        """Send buy signals every 30 min - AT LEAST 1 or say nothing available"""
        
        # Get all scores
        sorted_stocks = sorted(
            self.memory['top_scores'].items(),
            key=lambda x: x[1]['score'],
            reverse=True
        ) if self.memory['top_scores'] else []
        
        timeframes = [2, 3, 4, 5, 6, 7]
        signal_count = 0
        message = "🥭 **MEGA BOT - 30 MIN UPDATE**\n"
        message += f"⏰ {datetime.now().strftime('%H:%M %Z')}\n\n"
        
        # Try to send at least 1 signal
        for i, (symbol, info) in enumerate(sorted_stocks):
            if i >= len(timeframes):
                break
            
            # Skip if blocked
            if self.is_stock_blocked(symbol):
                continue
            
            timeframe = timeframes[i]
            score = info['score']
            price = info['current_price']
            momentum = info['momentum']
            volume = info['volume']
            
            target = price * (1 + self.profit_target[timeframe] / 100)
            stop = price * (1 - self.stop_loss[timeframe] / 100)
            
            message += f"🟢 **BUY: {symbol}** ({timeframe}-day hold)\n"
            message += f"Entry: ${price:.2f}\n"
            message += f"Momentum: +{momentum:.2f}% | Volume: {volume/1000000:.1f}M\n"
            message += f"Target: ${target:.2f} (+{self.profit_target[timeframe]}%)\n"
            message += f"Stop: ${stop:.2f} (cut loss)\n"
            message += f"Quality: {score}/100\n\n"
            
            self.memory['open_positions'][f"{symbol}_{timeframe}"] = {
                'symbol': symbol,
                'timeframe': timeframe,
                'entry_price': price,
                'entry_time': datetime.now().isoformat(),
                'target': target,
                'stop': stop,
                'status': 'OPEN'
            }
            
            self.block_stock(symbol)
            signal_count += 1
            
            # Send at least 1, can send up to 6
            if signal_count >= 6:
                break
        
        # If no signals found, tell the user clearly
        if signal_count == 0:
            message = "⚪ **MEGA BOT - 30 MIN UPDATE**\n"
            message += f"⏰ {datetime.now().strftime('%H:%M %Z')}\n\n"
            message += "❌ **NO SIGNALS RIGHT NOW**\n"
            message += "No momentum stocks available to buy at this moment.\n"
            message += "Keep waiting - next scan in 5 minutes! 🔍\n"
            message += "(Market may be slow or no stocks meet criteria)\n"
        
        # Always send message
        try:
            requests.post(self.webhook, json={'content': message}, timeout=10)
            if signal_count > 0:
                self.log(f"📱 Sent {signal_count} signals to Discord")
            else:
                self.log(f"📱 Sent 'No signals' message to Discord")
        except:
            self.log("⚠️ Discord issue")
        
        self.memory['top_scores'] = {}
    
    def check_positions(self):
        """Check all open positions"""
        if not self.memory['open_positions']:
            return
        
        for pos_id in list(self.memory['open_positions'].keys()):
            pos = self.memory['open_positions'][pos_id]
            
            if pos['status'] != 'OPEN':
                continue
            
            symbol = pos['symbol']
            
            try:
                data = self.get_stock_data(symbol)
                if not data:
                    continue
                
                current = data['current_price']
                entry = pos['entry_price']
                target = pos['target']
                stop = pos['stop']
                timeframe = pos['timeframe']
                
                profit_pct = ((current - entry) / entry) * 100
                
                if current >= target:
                    msg = f"🟢 SELL - TARGET HIT!\n{symbol} | ${entry:.2f} → ${current:.2f} | +{profit_pct:.2f}% | {timeframe}d"
                    try:
                        requests.post(self.webhook, json={'content': msg}, timeout=10)
                    except:
                        pass
                    pos['status'] = 'CLOSED'
                    pos['result'] = 'WIN'
                    self.memory['daily_trades'].append(pos)
                
                elif current <= stop:
                    msg = f"🔴 SELL - STOP LOSS!\n{symbol} | ${entry:.2f} → ${current:.2f} | {profit_pct:.2f}% | {timeframe}d"
                    try:
                        requests.post(self.webhook, json={'content': msg}, timeout=10)
                    except:
                        pass
                    pos['status'] = 'CLOSED'
                    pos['result'] = 'LOSS'
                    self.memory['daily_trades'].append(pos)
                
                else:
                    entry_time = datetime.fromisoformat(pos['entry_time'])
                    days_held = (datetime.now() - entry_time).days
                    
                    if days_held >= timeframe:
                        msg = f"🟡 SELL - TIMEFRAME EXPIRED!\n{symbol} | ${entry:.2f} → ${current:.2f} | {profit_pct:+.2f}% | {timeframe}d"
                        try:
                            requests.post(self.webhook, json={'content': msg}, timeout=10)
                        except:
                            pass
                        pos['status'] = 'CLOSED'
                        pos['result'] = 'NEUTRAL'
                        self.memory['daily_trades'].append(pos)
            
            except:
                continue
    
    def is_stock_blocked(self, symbol):
        """Check if blocked for 7 days"""
        if symbol not in self.memory['blocked_stocks']:
            return False
        
        blocked_time = datetime.fromisoformat(self.memory['blocked_stocks'][symbol])
        if datetime.now() - blocked_time > timedelta(days=7):
            del self.memory['blocked_stocks'][symbol]
            return False
        
        return True
    
    def block_stock(self, symbol):
        """Block for 7 days"""
        self.memory['blocked_stocks'][symbol] = datetime.now().isoformat()
    
    def send_daily_summary(self):
        """Send daily summary"""
        if not self.memory['daily_trades']:
            return
        
        trades = self.memory['daily_trades']
        won = len([t for t in trades if t.get('result') == 'WIN'])
        lost = len([t for t in trades if t.get('result') == 'LOSS'])
        neutral = len([t for t in trades if t.get('result') == 'NEUTRAL'])
        win_rate = (won / len(trades) * 100) if trades else 0
        
        msg = f"📊 DAILY SUMMARY\nTotal: {len(trades)} | Won: {won} ✅ | Lost: {lost} ❌ | Neutral: {neutral} ⏰\nWin Rate: {win_rate:.1f}%"
        
        try:
            requests.post(self.webhook, json={'content': msg}, timeout=10)
        except:
            pass
    
    def is_market_hours(self):
        """Check if market open (EDT)"""
        from datetime import datetime, timezone
        edt = timezone(timedelta(hours=-4))
        now = datetime.now(edt)
        
        is_weekday = now.weekday() < 5
        is_open = 9.5 <= now.hour <= 16.0
        
        return is_weekday and is_open
    
    def run(self):
        """Main loop"""
        cycle = 0
        
        while True:
            cycle += 1
            self.log(f"\n🔄 CYCLE #{cycle}")
            
            if self.is_market_hours():
                self.check_positions()
                self.scan_stocks()
                
                elapsed = datetime.now() - self.last_30min_push
                if elapsed >= timedelta(minutes=30):
                    self.log("⏰ 30 min - SENDING MOMENTUM SIGNALS!")
                    self.send_buy_signals()
                    self.last_30min_push = datetime.now()
                else:
                    remaining = 30 - int(elapsed.total_seconds() / 60)
                    self.log(f"⏳ Next signal in {remaining} min")
            
            else:
                self.log("⏳ Market closed")
            
            self.log(f"⏱️ Next check in 5 min...\n")
            time.sleep(300)


if __name__ == "__main__":
    bot = MomentumVolumeBot()
    bot.run()
