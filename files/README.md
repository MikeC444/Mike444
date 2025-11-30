# GVI Stock Decile Movement Tracker v2.0

## What's New in v2.0

### 1. **Multi-Region Support**
You can now upload data for the same date from different regions:
- US
- Europe (excl UK)
- UK
- APAC (excl Japan)
- Japan
- Global
- Emerging Markets

### 2. **Upload History Page**
New page showing all file uploads with:
- Upload timestamp
- Filename
- Data date
- Region
- Number of stocks
- Success/failure status

### 3. **Fixed UNIQUE Constraint**
The database now uses `(date, ticker, region)` as the unique key instead of `(date, ticker)`, allowing same-date uploads for different regions.

---

## Installation

```bash
pip install -r requirements.txt
```

## Running the Dashboard

```bash
streamlit run gvi_dashboard.py
```

---

## Migrating Existing Database

If you have an existing `gvi_data.db` from the previous version, you have two options:

### Option 1: Migrate via Dashboard
1. Run the dashboard
2. Go to "⚙️ Data Management"
3. Click "Run Migration"

### Option 2: Migrate via Python
```python
from gvi_tracker import migrate_existing_database
migrate_existing_database('gvi_data.db')
```

### Option 3: Start Fresh
Simply delete your existing `gvi_data.db` file and the new schema will be created automatically on first run.

---

## Uploading Data

1. Go to "📤 Upload Data"
2. Select your Excel file
3. Choose the data date
4. **Select the region** (this is new!)
5. Click Upload

You can now upload multiple files for the same date as long as they're for different regions.

---

## Viewing Upload History

1. Go to "📁 Upload History"
2. See all uploads with timestamps
3. Filter by status (Success/Failed) or region
4. Download history as CSV

---

## File Structure

```
gvi_tracker.py      # Core tracking logic with database management
gvi_dashboard.py    # Streamlit dashboard
requirements.txt    # Python dependencies
gvi_data.db         # SQLite database (created on first run)
```

---

## Database Schema

### stock_scores table
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| date | TEXT | Data date (YYYY-MM-DD) |
| ticker | TEXT | Stock ticker |
| company_name | TEXT | Company name |
| sector | TEXT | FactSet sector |
| region | TEXT | Geographic region |
| score | REAL | GVI composite score |
| decile | INTEGER | Decile ranking (1-10, higher = better) |

**Unique constraint:** `(date, ticker, region)`

### upload_history table
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| upload_timestamp | TEXT | When file was uploaded |
| filename | TEXT | Original filename |
| date | TEXT | Data date |
| region | TEXT | Region |
| stocks_count | INTEGER | Number of stocks |
| status | TEXT | SUCCESS or FAILED with error |
