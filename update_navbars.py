"""
Quick script to update navbar in all HTML files
"""
import os
import re

# Unified navbar HTML
NEW_NAVBAR = """        <div class="nav-links">
            <a href="index.html" data-i18n="nav_analyzer">📊 Analyzer</a>
            <a href="screener.html" data-i18n="nav_screener">🔍 Screener</a>
            <a href="compare.html" data-i18n="nav_compare">⚖️ Compare</a>
            <a href="advanced.html" data-i18n="nav_advanced">🧠 Advanced</a>
            <a href="insider.html" data-i18n="nav_insider">👔 Insider</a>
            <a href="darkpool.html" data-i18n="nav_darkpool">🌊 Dark Pool</a>
            <a href="earnings.html" data-i18n="nav_earnings">📅 Earnings</a>
            <a href="calendar.html" data-i18n="nav_calendar">📆 Calendar</a>
            <a href="sectors.html" data-i18n="nav_sectors">🔄 Sectors</a>
            <a href="heatmap.html" data-i18n="nav_heatmap">🗺️ Heatmap</a>
            <a href="volatility.html" data-i18n="nav_volatility">⚡ Volatility</a>
            <a href="portfolio.html" data-i18n="nav_portfolio">💼 Portfolio</a>
        </div>"""

# Files to update
files = [
    'compare.html',
    'calendar.html',
    'advanced.html',
    'earnings.html',
    'insider.html',
    'darkpool.html',
    'sectors.html',
    'volatility.html',
    'portfolio.html',
    'heatmap.html',
    'trends.html'
]

def update_navbar(filename):
    """Update navbar in HTML file"""
    filepath = f'd:/stock/{filename}'
    
    if not os.path.exists(filepath):
        print(f"⚠️  {filename} not found")
        return
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find <nav class="navbar"> ... </nav>
    # Replace <div class="nav-links"> ... </div> inside it
    
    pattern = r'(<nav class="navbar">.*?<a href="index.html" class="logo">.*?</a>)(.*?)(</nav>)'
    
    def replacement(match):
        before = match.group(1)
        after = match.group(3)
        # Add active class to current page
        new_navbar_modified = NEW_NAVBAR.replace(f'href="{filename}"', f'href="{filename}" class="active"')
        return before + '\n' + new_navbar_modified + '\n    ' + after
    
    new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    
    if new_content != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"✅ Updated {filename}")
    else:
        print(f"⏭️  {filename} - no match found (may use different structure)")

print("🚀 Starting navbar update...\n")
for file in files:
    update_navbar(file)

print("\n✅ Done!")
