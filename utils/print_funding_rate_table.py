import datetime as dt

def format_time_until_funding(next_funding_time: dt.datetime) -> str:
    """Formats time until next funding in human-readable format"""
    if not next_funding_time:
        return "N/A"
    
    now = dt.datetime.now()  # Use local time instead of UTC
    time_diff = next_funding_time - now
    
    if time_diff.total_seconds() < 0:
        # If time has already passed, show how many minutes ago
        abs_diff = abs(time_diff.total_seconds())
        minutes_ago = int(abs_diff // 60)
        if minutes_ago < 60:
            return f"in {minutes_ago}m"
        else:
            hours_ago = int(minutes_ago // 60)
            minutes_ago = minutes_ago % 60
            return f"in {hours_ago}h {minutes_ago}m"
    
    hours = int(time_diff.total_seconds() // 3600)
    minutes = int((time_diff.total_seconds() % 3600) // 60)
    
    if hours > 0:
        return f"in {hours}h {minutes}m"
    else:
        return f"in {minutes}m"

def format_volume(volume_usd: float) -> str:
    """Форматирует объем в человекочитаемом виде"""
    if volume_usd >= 1_000_000_000:  # >= 1B
        return f"${volume_usd/1_000_000_000:.1f}B"
    elif volume_usd >= 1_000_000:    # >= 1M
        return f"${volume_usd/1_000_000:.1f}M"
    elif volume_usd >= 1_000:        # >= 1K
        return f"${volume_usd/1_000:.1f}K"
    else:
        return f"${volume_usd:.0f}"

def format_price(price: float) -> str:
    """Форматирует цену в человекочитаемом виде"""
    if price >= 1000:
        return f"${price:,.0f}"
    elif price >= 1:
        return f"${price:.2f}"
    else:
        return f"${price:.4f}"

def print_hyperliquid_markets_table(markets):
    """Creates and displays a beautiful table with Hyperliquid data"""
    
    # Take top 10
    top_markets = markets[:10]
    
    print(f"\n📊 TOP-10 HYPERLIQUID MARKETS BY FUNDING RATE")
       # Statistics
    total_volume = sum(m['volume_24h_usd'] for m in top_markets)
    avg_funding = sum(m['funding_rate'] for m in top_markets) / len(top_markets) * 100
    
    print(f"   Total 24h Volume: {format_volume(total_volume)}")
    print(f"   Average Funding Rate: {avg_funding:.4f}%")
    print(f"   Highest Funding Rate: {top_markets[0]['funding_rate']*100:.4f}% ({top_markets[0]['coin']})")
    print("=" * 110)
    print(f"{'Market':<12} {'Price':<12} {'Funding/hr':<12} {'24h Volume':<12} {'Next Funding':<25}")
    print("-" * 110)
    
    for market in top_markets:
        coin = market['coin']
        price = format_price(market['mark_px'])
        funding_rate = market['funding_rate'] * 100  # convert to percentage
        volume = format_volume(market['volume_24h_usd'])
        
        # Format next funding time
        if market['next_funding_time']:
            funding_time_str = market['next_funding_time'].strftime("%H:%M %d.%m")
            time_until = format_time_until_funding(market['next_funding_time'])
            next_funding_display = f"{funding_time_str} ({time_until})"
        else:
            next_funding_display = "N/A"
        
        # Color indicator for funding rate and coin name
        if funding_rate > 0.01:  # > 1%
            coin_display = f"🟢 {coin}"
            funding_display = f"{funding_rate:>8.4f}%"
        elif funding_rate > 0.001:  # > 0.1%
            coin_display = f"🟡 {coin}"
            funding_display = f"{funding_rate:>8.4f}%"
        elif funding_rate < -0.01:  # < -1%
            coin_display = f"🔴 {coin}"
            funding_display = f"{funding_rate:>8.4f}%"
        elif funding_rate < -0.001:  # < -0.1%
            coin_display = f"🟠 {coin}"
            funding_display = f"{funding_rate:>8.4f}%"
        else:
            coin_display = f"⚪ {coin}"
            funding_display = f"{funding_rate:>8.4f}%"
        
        print(f"{coin_display:<12} {price:<12} {funding_display:<12} {volume:<12} {next_funding_display:<25}")
    
    print("-" * 110)
    
    print()