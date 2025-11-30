"""
GVI Stock Decile Movement Tracker
==================================
Manages historical GVI data and tracks decile movements over time.
Supports multiple regions with same-date uploads.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sqlite3
import os
from pathlib import Path


class GVITracker:
    """Manages GVI stock score data and decile movement analysis"""
    
    def __init__(self, db_path='gvi_data.db'):
        """Initialize the tracker with a SQLite database"""
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Create the database tables if they don't exist"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Main table for stock scores
        # UNIQUE constraint now includes region to allow same-date uploads for different regions
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS stock_scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                ticker TEXT NOT NULL,
                company_name TEXT,
                sector TEXT,
                region TEXT DEFAULT 'US',
                score REAL,
                decile INTEGER,
                UNIQUE(date, ticker, region)
            )
        ''')
        
        # Upload history table to track all uploads
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS upload_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                upload_timestamp TEXT NOT NULL,
                filename TEXT NOT NULL,
                date TEXT NOT NULL,
                region TEXT NOT NULL,
                stocks_count INTEGER,
                status TEXT
            )
        ''')
        
        # Index for faster queries
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_ticker_date 
            ON stock_scores(ticker, date)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_region 
            ON stock_scores(region)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_date_region 
            ON stock_scores(date, region)
        ''')
        
        conn.commit()
        conn.close()
    
    def migrate_database(self):
        """
        Migrate existing database to new schema if needed.
        Call this if you have an existing database with the old UNIQUE constraint.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Check if region column exists
            cursor.execute("PRAGMA table_info(stock_scores)")
            columns = [col[1] for col in cursor.fetchall()]
            
            if 'region' not in columns:
                print("Adding region column to existing database...")
                cursor.execute("ALTER TABLE stock_scores ADD COLUMN region TEXT DEFAULT 'US'")
            
            # Check if upload_history table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='upload_history'")
            if not cursor.fetchone():
                print("Creating upload_history table...")
                cursor.execute('''
                    CREATE TABLE upload_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        upload_timestamp TEXT NOT NULL,
                        filename TEXT NOT NULL,
                        date TEXT NOT NULL,
                        region TEXT NOT NULL,
                        stocks_count INTEGER,
                        status TEXT
                    )
                ''')
            
            # Recreate the table with new unique constraint
            print("Updating unique constraint to include region...")
            
            # Create new table with correct constraint
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS stock_scores_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    ticker TEXT NOT NULL,
                    company_name TEXT,
                    sector TEXT,
                    region TEXT DEFAULT 'US',
                    score REAL,
                    decile INTEGER,
                    UNIQUE(date, ticker, region)
                )
            ''')
            
            # Copy data
            cursor.execute('''
                INSERT OR IGNORE INTO stock_scores_new 
                (date, ticker, company_name, sector, region, score, decile)
                SELECT date, ticker, company_name, sector, 
                       COALESCE(region, 'US'), score, decile 
                FROM stock_scores
            ''')
            
            # Drop old table and rename new one
            cursor.execute("DROP TABLE stock_scores")
            cursor.execute("ALTER TABLE stock_scores_new RENAME TO stock_scores")
            
            # Recreate indexes
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_ticker_date 
                ON stock_scores(ticker, date)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_region 
                ON stock_scores(region)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_date_region 
                ON stock_scores(date, region)
            ''')
            
            conn.commit()
            print("Migration complete!")
            return {'success': True, 'message': 'Database migrated successfully'}
            
        except Exception as e:
            conn.rollback()
            return {'success': False, 'error': str(e)}
        finally:
            conn.close()
    
    def load_gvi_file(self, filepath, date_str, region='US'):
        """
        Load a GVI Excel file and extract relevant data
        
        Parameters:
        -----------
        filepath : str
            Path to the Excel file
        date_str : str
            Date in YYYY-MM-DD format
        region : str
            Region identifier (US, Europe, UK, APAC, Japan, etc.)
        
        Returns:
        --------
        pd.DataFrame
            Cleaned dataframe with GVI scores
        """
        # Load Excel file
        df = pd.read_excel(filepath, skiprows=3)
        
        # Remove rows where Company Symbol is NaN
        df = df[df['Company Symbol'].notna()].copy()
        
        # Reverse decile ranking (1 = best becomes 10, 10 = worst becomes 1)
        # So higher decile = better quality
        df['Reversed_Decile'] = 11 - df['Score (Decile)']
        
        # Select and rename columns
        df_clean = pd.DataFrame({
            'date': date_str,
            'ticker': df['Company Symbol'],
            'company_name': df['Company Name'],
            'sector': df['FactSet Econ Sector'],
            'region': region,
            'score': df['Score'],
            'decile': df['Reversed_Decile']
        })
        
        return df_clean
    
    def add_data(self, df):
        """
        Add new GVI data to the database
        
        Parameters:
        -----------
        df : pd.DataFrame
            DataFrame with columns: date, ticker, company_name, sector, region, score, decile
        """
        conn = sqlite3.connect(self.db_path)
        
        # Use INSERT OR REPLACE to handle duplicates within same region
        for _, row in df.iterrows():
            conn.execute('''
                INSERT OR REPLACE INTO stock_scores 
                (date, ticker, company_name, sector, region, score, decile)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (row['date'], row['ticker'], row['company_name'], 
                  row['sector'], row['region'], row['score'], row['decile']))
        
        conn.commit()
        conn.close()
    
    def log_upload(self, filename, date_str, region, stocks_count, status):
        """Log an upload to the history table"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO upload_history (upload_timestamp, filename, date, region, stocks_count, status)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (datetime.now().isoformat(), filename, date_str, region, stocks_count, status))
        
        conn.commit()
        conn.close()
    
    def upload_file(self, filepath, date_str, region='US'):
        """
        Upload a GVI file to the database
        
        Parameters:
        -----------
        filepath : str
            Path to the Excel file
        date_str : str
            Date in YYYY-MM-DD format (e.g., '2024-07-10')
        region : str
            Region identifier (US, Europe, UK, APAC, Japan, etc.)
        
        Returns:
        --------
        dict
            Summary of the upload
        """
        filename = os.path.basename(filepath)
        
        try:
            # Load and clean the file
            df = self.load_gvi_file(filepath, date_str, region)
            
            # Add to database
            self.add_data(df)
            
            # Log the upload
            self.log_upload(filename, date_str, region, len(df), 'SUCCESS')
            
            return {
                'success': True,
                'date': date_str,
                'region': region,
                'stocks_added': len(df),
                'message': f'Successfully added {len(df)} stocks for {region} on {date_str}'
            }
        except Exception as e:
            # Log the failed upload
            self.log_upload(filename, date_str, region, 0, f'FAILED: {str(e)}')
            
            return {
                'success': False,
                'date': date_str,
                'region': region,
                'error': str(e),
                'message': f'Error uploading file: {str(e)}'
            }
    
    def get_upload_history(self):
        """Get the history of all file uploads"""
        conn = sqlite3.connect(self.db_path)
        query = """
            SELECT 
                id,
                upload_timestamp,
                filename,
                date,
                region,
                stocks_count,
                status
            FROM upload_history 
            ORDER BY upload_timestamp DESC
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    
    def get_all_dates(self):
        """Get list of all dates in the database"""
        conn = sqlite3.connect(self.db_path)
        query = "SELECT DISTINCT date FROM stock_scores ORDER BY date DESC"
        dates = pd.read_sql_query(query, conn)
        conn.close()
        return dates['date'].tolist()
    
    def get_all_regions(self):
        """Get list of all regions in the database"""
        conn = sqlite3.connect(self.db_path)
        query = "SELECT DISTINCT region FROM stock_scores ORDER BY region"
        regions = pd.read_sql_query(query, conn)
        conn.close()
        return regions['region'].tolist()
    
    def get_dates_by_region(self, region):
        """Get list of all dates for a specific region"""
        conn = sqlite3.connect(self.db_path)
        query = "SELECT DISTINCT date FROM stock_scores WHERE region = ? ORDER BY date DESC"
        dates = pd.read_sql_query(query, conn, params=(region,))
        conn.close()
        return dates['date'].tolist()
    
    def get_data_summary(self):
        """Get a summary of all data in the database"""
        conn = sqlite3.connect(self.db_path)
        query = """
            SELECT 
                region,
                date,
                COUNT(*) as stock_count
            FROM stock_scores 
            GROUP BY region, date
            ORDER BY region, date DESC
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    
    def get_data_for_date(self, date_str, region=None):
        """Get all stock data for a specific date, optionally filtered by region"""
        conn = sqlite3.connect(self.db_path)
        
        if region:
            query = "SELECT * FROM stock_scores WHERE date = ? AND region = ?"
            df = pd.read_sql_query(query, conn, params=(date_str, region))
        else:
            query = "SELECT * FROM stock_scores WHERE date = ?"
            df = pd.read_sql_query(query, conn, params=(date_str,))
        
        conn.close()
        return df
    
    def get_ticker_history(self, ticker, region=None):
        """Get historical data for a specific ticker"""
        conn = sqlite3.connect(self.db_path)
        
        if region:
            query = """
                SELECT * FROM stock_scores 
                WHERE ticker = ? AND region = ?
                ORDER BY date
            """
            df = pd.read_sql_query(query, conn, params=(ticker, region))
        else:
            query = """
                SELECT * FROM stock_scores 
                WHERE ticker = ?
                ORDER BY date
            """
            df = pd.read_sql_query(query, conn, params=(ticker,))
        
        conn.close()
        return df
    
    def find_significant_movers(self, start_date, end_date, region=None, 
                                 top_threshold=8, bottom_threshold=3):
        """
        Find stocks with significant decile movements between two dates.
        
        With reversed deciles (higher = better):
        - Top deciles (8-10) = Best quality stocks
        - Bottom deciles (1-3) = Worst quality stocks
        
        Parameters:
        -----------
        start_date : str
            Starting date (YYYY-MM-DD)
        end_date : str
            Ending date (YYYY-MM-DD)
        region : str, optional
            Filter by region
        top_threshold : int
            Decile threshold for "top" (default 8, meaning deciles 8-10)
        bottom_threshold : int
            Decile threshold for "bottom" (default 3, meaning deciles 1-3)
        
        Returns:
        --------
        dict
            Contains top_entrants, bottom_entrants, and all_movements
        """
        conn = sqlite3.connect(self.db_path)
        
        # Build query based on region filter
        if region:
            start_query = """
                SELECT ticker, company_name, sector, decile as start_decile, region
                FROM stock_scores 
                WHERE date = ? AND region = ?
            """
            end_query = """
                SELECT ticker, decile as end_decile
                FROM stock_scores 
                WHERE date = ? AND region = ?
            """
            start_df = pd.read_sql_query(start_query, conn, params=(start_date, region))
            end_df = pd.read_sql_query(end_query, conn, params=(end_date, region))
        else:
            start_query = """
                SELECT ticker, company_name, sector, decile as start_decile, region
                FROM stock_scores 
                WHERE date = ?
            """
            end_query = """
                SELECT ticker, decile as end_decile
                FROM stock_scores 
                WHERE date = ?
            """
            start_df = pd.read_sql_query(start_query, conn, params=(start_date,))
            end_df = pd.read_sql_query(end_query, conn, params=(end_date,))
        
        conn.close()
        
        # Merge to find stocks present in both periods
        merged = start_df.merge(end_df, on='ticker', how='inner')
        
        # Calculate movement (positive = improved, negative = declined)
        merged['decile_change'] = merged['end_decile'] - merged['start_decile']
        
        # Find significant movers
        # Top entrants: moved INTO top deciles (8-10) from below
        top_entrants = merged[
            (merged['start_decile'] < top_threshold) & 
            (merged['end_decile'] >= top_threshold)
        ].sort_values('decile_change', ascending=False)
        
        # Bottom entrants: moved INTO bottom deciles (1-3) from above
        bottom_entrants = merged[
            (merged['start_decile'] > bottom_threshold) & 
            (merged['end_decile'] <= bottom_threshold)
        ].sort_values('decile_change', ascending=True)
        
        # All movements sorted by magnitude
        all_movements = merged.sort_values('decile_change', key=abs, ascending=False)
        
        return {
            'top_entrants': top_entrants,
            'bottom_entrants': bottom_entrants,
            'all_movements': all_movements,
            'start_date': start_date,
            'end_date': end_date,
            'region': region,
            'total_stocks_analyzed': len(merged)
        }
    
    def delete_data(self, date_str=None, region=None):
        """
        Delete data from the database.
        
        Parameters:
        -----------
        date_str : str, optional
            Delete data for specific date
        region : str, optional
            Delete data for specific region
        
        If both provided, deletes data matching both criteria.
        If neither provided, does nothing (safety measure).
        """
        if not date_str and not region:
            return {'success': False, 'message': 'Must specify date, region, or both'}
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            if date_str and region:
                cursor.execute("DELETE FROM stock_scores WHERE date = ? AND region = ?", 
                             (date_str, region))
                message = f"Deleted data for {region} on {date_str}"
            elif date_str:
                cursor.execute("DELETE FROM stock_scores WHERE date = ?", (date_str,))
                message = f"Deleted all data for {date_str}"
            else:
                cursor.execute("DELETE FROM stock_scores WHERE region = ?", (region,))
                message = f"Deleted all data for region {region}"
            
            deleted_count = cursor.rowcount
            conn.commit()
            
            return {
                'success': True,
                'deleted_count': deleted_count,
                'message': f"{message} ({deleted_count} records)"
            }
        except Exception as e:
            conn.rollback()
            return {'success': False, 'error': str(e)}
        finally:
            conn.close()


# Convenience function for migration
def migrate_existing_database(db_path='gvi_data.db'):
    """Run migration on an existing database"""
    tracker = GVITracker(db_path)
    result = tracker.migrate_database()
    print(result['message'] if result['success'] else f"Error: {result['error']}")
    return result


if __name__ == "__main__":
    # Example usage
    tracker = GVITracker()
    
    # Show available regions
    print("Available regions:", tracker.get_all_regions())
    
    # Show data summary
    print("\nData Summary:")
    print(tracker.get_data_summary())
    
    # Show upload history
    print("\nUpload History:")
    print(tracker.get_upload_history())
