#!/usr/bin/env python3
"""
GVI Tracker Command Line Interface
===================================
Simple CLI for managing GVI stock data
"""

import sys
import argparse
from datetime import datetime
from gvi_tracker import GVITracker


def main():
    parser = argparse.ArgumentParser(
        description='GVI Stock Decile Movement Tracker',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Upload a new file
  python gvi_cli.py upload --file data.xlsx --date 2025-03-11
  
  # Show all available dates
  python gvi_cli.py dates
  
  # Analyze movements between two dates
  python gvi_cli.py analyze --start 2024-07-10 --end 2025-03-11
  
  # Export summary
  python gvi_cli.py export --output summary.xlsx
  
  # Get history for a specific ticker
  python gvi_cli.py ticker --symbol AAPL
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Upload command
    upload_parser = subparsers.add_parser('upload', help='Upload a new Galileo file')
    upload_parser.add_argument('--file', required=True, help='Path to Excel file')
    upload_parser.add_argument('--date', required=True, help='Date in YYYY-MM-DD format')
    upload_parser.add_argument('--region', default='US', 
                              choices=['US', 'Europe (excl UK)', 'UK', 'APAC (excl. Japan)', 
                                      'Japan', 'China', 'Global'],
                              help='Region for the data (default: US)')
    
    # Dates command
    dates_parser = subparsers.add_parser('dates', help='List all available dates')
    
    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Analyze movements between dates')
    analyze_parser.add_argument('--start', required=True, help='Start date (YYYY-MM-DD)')
    analyze_parser.add_argument('--end', required=True, help='End date (YYYY-MM-DD)')
    analyze_parser.add_argument(
        '--threshold', 
        choices=['top_bottom_3', 'magnitude_3', 'magnitude_5'],
        default='top_bottom_3',
        help='Movement threshold type'
    )
    analyze_parser.add_argument('--region', default=None,
                               choices=['US', 'Europe (excl UK)', 'UK', 'APAC (excl. Japan)', 
                                       'Japan', 'China', 'Global'],
                               help='Filter by region (default: all regions)')
    
    # Export command
    export_parser = subparsers.add_parser('export', help='Export summary to Excel')
    export_parser.add_argument('--output', default='gvi_summary.xlsx', help='Output file path')
    
    # Ticker command
    ticker_parser = subparsers.add_parser('ticker', help='Get history for a ticker')
    ticker_parser.add_argument('--symbol', required=True, help='Ticker symbol')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Initialize tracker
    tracker = GVITracker()
    
    # Execute command
    if args.command == 'upload':
        print(f"Uploading {args.file} for {args.region} on {args.date}...")
        result = tracker.upload_file(args.file, args.date, args.region)
        print(result['message'])
        
        if not result['success']:
            sys.exit(1)
    
    elif args.command == 'dates':
        dates = tracker.get_all_dates()
        print(f"\nAvailable dates ({len(dates)} total):")
        for date in dates:
            print(f"  {date}")
    
    elif args.command == 'analyze':
        region_str = f" ({args.region})" if args.region else ""
        print(f"\nAnalyzing movements from {args.start} to {args.end}{region_str}")
        print("=" * 70)
        print("Note: Decile 10 = Best Quality | Decile 1 = Worst Quality")
        print("=" * 70)
        
        analysis = tracker.find_significant_movers(
            args.start, 
            args.end,
            args.threshold,
            args.region
        )
        
        top = analysis['top_entrants']
        bottom = analysis['bottom_entrants']
        
        print(f"\nStocks Moving Up (Entering Top Deciles 8-10): {len(top)}")
        if len(top) > 0:
            print("\nTop 10:")
            display = top[['ticker', 'company_name', 'decile_start', 'decile_end', 'decile_change']].head(10)
            print(display.to_string(index=False))
        
        print(f"\n\nStocks Moving Down (Entering Bottom Deciles 1-3): {len(bottom)}")
        if len(bottom) > 0:
            print("\nTop 10:")
            display = bottom[['ticker', 'company_name', 'decile_start', 'decile_end', 'decile_change']].head(10)
            print(display.to_string(index=False))
    
    elif args.command == 'export':
        print(f"Exporting summary to {args.output}...")
        tracker.export_summary(args.output)
    
    elif args.command == 'ticker':
        symbol = args.symbol.upper()
        print(f"\nGetting history for {symbol}...")
        
        history = tracker.get_ticker_history(symbol)
        
        if len(history) == 0:
            print(f"No data found for {symbol}")
            sys.exit(1)
        
        print(f"\n{symbol} - {history.iloc[0]['company_name']}")
        print("=" * 70)
        
        display = history[['date', 'decile', 'score', 'sector']]
        print(display.to_string(index=False))


if __name__ == '__main__':
    main()
