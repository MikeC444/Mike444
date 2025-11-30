# Galileo Decile Movement Dashboard - User Guide

## What This System Does

This system tracks stock movements across quality deciles from your Galileo data. It automatically identifies stocks making significant quality transitions - specifically those entering the **top 3 or bottom 3 deciles**.

**Important: Decile Scale**
- **Decile 10 = BEST quality** (top performers)
- **Decile 1 = WORST quality** (bottom performers)
- Movement UP in deciles = Quality improving
- Movement DOWN in deciles = Quality declining

## Your Analysis: July 2024 to March 2025

Based on your two uploaded files, here are the key findings:

### 📊 Summary Statistics
- **55 stocks** moved into **TOP 3 deciles (8, 9, 10)** (improving quality)
- **43 stocks** moved into **BOTTOM 3 deciles (1, 2, 3)** (declining quality)
- Analysis period: **8 months** (2024-07-10 to 2025-03-11)
- Region: **US**

### ⬆️ Top Performers (Moving Into Top Deciles 8-10)

**Biggest Improvers:**
1. **BEN** (Franklin Resources) - Decile 1 → 9 (+8 deciles)
2. **MOS** (Mosaic Company) - Decile 2 → 10 (+8 deciles)
3. **BA** (Boeing) - Decile 1 → 8 (+7 deciles)
4. **NEM** (Newmont Corporation) - Decile 2 → 9 (+7 deciles)
5. **AIG** (American International Group) - Decile 3 → 10 (+7 deciles)

**Notable Sectors:**
- Financials (BEN, AIG)
- Industrials (BA)
- Materials (MOS, NEM)

### ⬇️ Bottom Performers (Moving Into Bottom Deciles 1-3)

**Biggest Decliners:**
1. **MSI** (Motorola Solutions) - Decile 10 → 2 (-8 deciles)
2. **BKR** (Baker Hughes) - Decile 9 → 2 (-7 deciles)
3. **GRMN** (Garmin) - Decile 8 → 1 (-7 deciles)
4. **ADSK** (Autodesk) - Decile 9 → 3 (-6 deciles)
5. **PH** (Parker-Hannifin) - Decile 8 → 2 (-6 deciles)

**Notable Sectors:**
- Technology (MSI, GRMN, ADSK)
- Industrials (BKR, PH)

## How to Use the System

### Option 1: Interactive Dashboard (Recommended)

```bash
streamlit run gvi_dashboard.py
```

**Features:**
- 📁 **Upload new files** via drag-and-drop (with region selection)
- 🌍 **Filter by region** (US, Europe excl UK, UK, APAC excl Japan, Japan, China, Global)
- 📅 **Select time periods** (12 months, 6 months, 3 months, custom)
- 🎯 **View significant movers** automatically
- 🔍 **Search any ticker** to see its history
- 📊 **Sector analysis** to identify trends
- 📥 **Download results** as CSV

**Dashboard Tabs:**
1. **Significant Movers** - Your main view for stocks entering top/bottom 3
2. **All Movements** - Complete list with filtering options
3. **Stock Search** - Individual ticker history and charts
4. **Sector Analysis** - Compare sector-level trends

### Option 2: Command Line Interface

**Upload new data:**
```bash
python gvi_cli.py upload --file GVI_SP500_NewDate.xlsx --date 2025-04-01
```

**Quick analysis:**
```bash
python gvi_cli.py analyze --start 2024-07-10 --end 2025-03-11
```

**Check specific stock:**
```bash
python gvi_cli.py ticker --symbol AAPL
```

**Export to Excel:**
```bash
python gvi_cli.py export --output weekly_report.xlsx
```

## Weekly Workflow

1. **Monday Morning:** Export latest GVI data from FactSet
2. **Upload:** Drag file into dashboard sidebar or use CLI
3. **Review:** Check "Significant Movers" tab
4. **Investigate:** Search specific tickers of interest
5. **Export:** Download results for your records
6. **Repeat:** Next week, upload new file and compare

## Understanding the Metrics

### Decile Scale (REVERSED - Higher is Better!)
- **8-10:** High quality (best scores) - *Target zone*
- **4-7:** Middle quality
- **1-3:** Low quality (worst scores) - *Avoid zone*

### Decile Change
- **Positive change** = Quality improving (e.g., +5 means moved 5 deciles better)
- **Negative change** = Quality declining (e.g., -5 means moved 5 deciles worse)

### Regions Available
- **US** - United States stocks
- **Europe (excl UK)** - European markets excluding UK
- **UK** - United Kingdom only
- **APAC (excl. Japan)** - Asia-Pacific excluding Japan
- **Japan** - Japanese market
- **China** - Chinese market
- **Global** - Global/multi-regional stocks

### Thresholds
The system offers three threshold options:

1. **Top/Bottom 3 Deciles** (Default)
   - Stocks entering deciles 8-10 (from 1-7)
   - Stocks entering deciles 1-3 (from 4-10)
   - *Best for identifying quality transitions*

2. **Moving 3+ Deciles**
   - Any stock moving 3 or more deciles
   - *Captures medium-sized moves*

3. **Moving 5+ Deciles**
   - Any stock moving 5 or more deciles
   - *Only the most dramatic changes*

## Advanced Features

### Rolling Period Analysis
The system automatically calculates movements over your chosen period:
- **12 months:** Long-term quality trends
- **6 months:** Medium-term quality trends
- **3 months:** Recent short-term changes
- **Custom:** Any date range you specify

### Sector Comparison
Identify which sectors are collectively improving or declining:
- Average decile movement by sector
- Sector-level statistics
- Visual comparison charts

### Historical Tracking
For any ticker:
- Complete decile history
- Score evolution over time
- Current position and trend

## Data Storage

All your data is stored in `gvi_data.db` (SQLite database):
- ✅ Automatically manages duplicates
- ✅ Fast queries even with years of data
- ✅ No external dependencies
- ✅ Easy to backup (just copy the file)

## Example Use Cases

### 1. Weekly Portfolio Review
Upload weekly data and check which holdings are declining into bottom deciles (potential sells) or improving into top deciles (potential holds).

### 2. New Opportunity Identification
Look for stocks newly entering top 3 deciles - these represent improving quality that may warrant research.

### 3. Sector Rotation
Use sector analysis to identify which sectors are collectively improving, signaling potential rotation opportunities.

### 4. Quality Verification
Before buying a stock, check its decile history to see if it's consistently high quality or volatile.

## Tips for Best Results

1. **Upload Consistently:** Weekly uploads provide the best trend data
2. **Set Reminders:** Make Monday uploads part of your routine
3. **Review Extremes:** Pay special attention to stocks moving 5+ deciles
4. **Cross-Reference:** Use with your other research tools
5. **Track Holdings:** Add your portfolio tickers to a watchlist

## Customization Options

You can modify thresholds by editing `gvi_tracker.py`:

```python
# Change "top 3" to "top 2" deciles
top_entrants = movements[
    (movements['decile_end'] <= 2) &  # Changed from 3
    (movements['decile_start'] > 2)
]
```

## Troubleshooting

**Dashboard won't load?**
```bash
pip install streamlit --upgrade
streamlit run gvi_dashboard.py
```

**Upload error?**
- Verify your Excel file has the same format as the samples
- Check that headers start at row 4
- Ensure date is in YYYY-MM-DD format

**Database issues?**
- Delete `gvi_data.db` and re-upload files
- This will start fresh

## Getting Help

1. Check the README.md for detailed documentation
2. Review error messages - they usually indicate the problem
3. Test with the sample files first to verify setup

## Next Steps

1. ✅ System is loaded with your July 2024 and March 2025 data
2. 📊 Launch dashboard: `streamlit run gvi_dashboard.py`
3. 🔍 Explore the significant movers
4. 📁 Upload your next weekly file when ready
5. 📈 Build historical database over time

---

**Pro Tip:** The real value comes from building up 6-12 months of weekly data. The more historical data you have, the better you can identify meaningful quality transitions versus temporary noise.
