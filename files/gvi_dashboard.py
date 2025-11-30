"""
GVI Stock Decile Movement Dashboard
====================================
Interactive dashboard for tracking GVI stock score movements.
Now supports multiple regions and shows upload history.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from gvi_tracker import GVITracker
import os

# Page configuration
st.set_page_config(
    page_title="Galalio Decile Tracker",
    page_icon="📊",
    layout="wide"
)

# Initialize tracker
@st.cache_resource
def get_tracker():
    return GVITracker()

tracker = get_tracker()

# Sidebar navigation
st.sidebar.title("📊 Galalio Tracker")
page = st.sidebar.radio(
    "Navigation",
    ["📈 Dashboard", "📤 Upload Data", "📁 Upload History", "🔍 Stock Lookup", "⚙️ Data Management"]
)

# Region options
REGIONS = [
    "US",
    "Europe (excl UK)",
    "UK",
    "APAC (excl Japan)",
    "Japan",
    "Global",
    "Emerging Markets"
]

# ============================================
# PAGE: Dashboard
# ============================================
if page == "📈 Dashboard":
    st.title("📈 GVI Decile Movement Dashboard")
    
    # Get available data
    regions = tracker.get_all_regions()
    
    if not regions:
        st.warning("No data uploaded yet. Go to 'Upload Data' to add your first file.")
    else:
        # Region selector
        col1, col2 = st.columns([1, 3])
        with col1:
            selected_region = st.selectbox("Select Region", ["All Regions"] + regions)
        
        region_filter = None if selected_region == "All Regions" else selected_region
        
        # Get dates for selected region
        if region_filter:
            dates = tracker.get_dates_by_region(region_filter)
        else:
            dates = tracker.get_all_dates()
        
        if len(dates) < 2:
            st.warning(f"Need at least 2 data points for {selected_region}. Currently have {len(dates)}.")
        else:
            # Date range selection
            st.subheader("📅 Select Analysis Period")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                period = st.selectbox(
                    "Quick Select",
                    ["Custom", "3 Months", "6 Months", "12 Months"]
                )
            
            with col2:
                end_date = st.selectbox("End Date", dates, index=0)
            
            with col3:
                if period == "Custom":
                    available_start_dates = [d for d in dates if d < end_date]
                    if available_start_dates:
                        start_date = st.selectbox("Start Date", available_start_dates)
                    else:
                        start_date = dates[-1]
                        st.info("Only one earlier date available")
                else:
                    # Calculate approximate start date based on period
                    months = {"3 Months": 3, "6 Months": 6, "12 Months": 12}[period]
                    target_date = datetime.strptime(end_date, "%Y-%m-%d") - timedelta(days=months*30)
                    
                    # Find closest available date
                    available_dates = [d for d in dates if d < end_date]
                    if available_dates:
                        closest = min(available_dates, 
                                     key=lambda x: abs(datetime.strptime(x, "%Y-%m-%d") - target_date))
                        start_date = closest
                        st.info(f"Using closest available date: {start_date}")
                    else:
                        start_date = dates[-1]
            
            # Run analysis
            if st.button("🔍 Analyze Movements", type="primary"):
                with st.spinner("Analyzing decile movements..."):
                    results = tracker.find_significant_movers(start_date, end_date, region_filter)
                
                # Summary metrics
                st.subheader("📊 Summary")
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total Stocks Analyzed", results['total_stocks_analyzed'])
                with col2:
                    st.metric("Top Decile Entrants", len(results['top_entrants']))
                with col3:
                    st.metric("Bottom Decile Entrants", len(results['bottom_entrants']))
                with col4:
                    avg_movement = results['all_movements']['decile_change'].mean()
                    st.metric("Avg Decile Change", f"{avg_movement:+.2f}")
                
                # Top Entrants
                st.subheader("🌟 Entered Top Deciles (8-10)")
                if len(results['top_entrants']) > 0:
                    top_df = results['top_entrants'][['ticker', 'company_name', 'sector', 
                                                       'start_decile', 'end_decile', 'decile_change']].copy()
                    top_df.columns = ['Ticker', 'Company', 'Sector', 'Start Decile', 'End Decile', 'Change']
                    st.dataframe(top_df, use_container_width=True, hide_index=True)
                    
                    # Download button
                    csv = top_df.to_csv(index=False)
                    st.download_button(
                        "📥 Download Top Entrants CSV",
                        csv,
                        f"top_entrants_{start_date}_to_{end_date}.csv",
                        "text/csv"
                    )
                else:
                    st.info("No stocks entered top deciles during this period")
                
                # Bottom Entrants
                st.subheader("⚠️ Entered Bottom Deciles (1-3)")
                if len(results['bottom_entrants']) > 0:
                    bottom_df = results['bottom_entrants'][['ticker', 'company_name', 'sector', 
                                                             'start_decile', 'end_decile', 'decile_change']].copy()
                    bottom_df.columns = ['Ticker', 'Company', 'Sector', 'Start Decile', 'End Decile', 'Change']
                    st.dataframe(bottom_df, use_container_width=True, hide_index=True)
                    
                    csv = bottom_df.to_csv(index=False)
                    st.download_button(
                        "📥 Download Bottom Entrants CSV",
                        csv,
                        f"bottom_entrants_{start_date}_to_{end_date}.csv",
                        "text/csv"
                    )
                else:
                    st.info("No stocks entered bottom deciles during this period")
                
                # Movement distribution chart
                st.subheader("📊 Decile Movement Distribution")
                fig = px.histogram(
                    results['all_movements'],
                    x='decile_change',
                    nbins=19,
                    title="Distribution of Decile Changes",
                    labels={'decile_change': 'Decile Change', 'count': 'Number of Stocks'}
                )
                fig.update_layout(bargap=0.1)
                st.plotly_chart(fig, use_container_width=True)

# ============================================
# PAGE: Upload Data
# ============================================
elif page == "📤 Upload Data":
    st.title("📤 Upload GVI Data")
    
    st.markdown("""
    Upload your GVI Excel files here. Each file should be for a specific date and region.
    You can upload multiple files for the same date as long as they are for different regions.
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        uploaded_file = st.file_uploader("Choose Excel file", type=['xlsx', 'xls'])
    
    with col2:
        date_str = st.date_input("Data Date").strftime("%Y-%m-%d")
        region = st.selectbox("Region", REGIONS)
    
    if uploaded_file and st.button("📤 Upload File", type="primary"):
        # Save temp file
        temp_path = f"/tmp/{uploaded_file.name}"
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        with st.spinner(f"Uploading {uploaded_file.name}..."):
            result = tracker.upload_file(temp_path, date_str, region)
        
        # Clean up
        os.remove(temp_path)
        
        if result['success']:
            st.success(result['message'])
            st.cache_resource.clear()
        else:
            st.error(result['message'])
    
    # Show current data summary
    st.subheader("📊 Current Data Summary")
    summary = tracker.get_data_summary()
    if not summary.empty:
        # Pivot for better display
        pivot = summary.pivot(index='date', columns='region', values='stock_count')
        st.dataframe(pivot.fillna(0).astype(int), use_container_width=True)
    else:
        st.info("No data uploaded yet")

# ============================================
# PAGE: Upload History
# ============================================
elif page == "📁 Upload History":
    st.title("📁 Upload History")
    
    st.markdown("""
    View all files that have been uploaded to the system, including successful and failed uploads.
    """)
    
    history = tracker.get_upload_history()
    
    if history.empty:
        st.info("No upload history available. Upload files from the 'Upload Data' page.")
    else:
        # Summary stats
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Uploads", len(history))
        with col2:
            successful = len(history[history['status'] == 'SUCCESS'])
            st.metric("Successful", successful)
        with col3:
            failed = len(history[history['status'].str.startswith('FAILED')])
            st.metric("Failed", failed)
        
        # Filter options
        st.subheader("🔍 Filter")
        col1, col2 = st.columns(2)
        with col1:
            status_filter = st.selectbox("Status", ["All", "SUCCESS", "FAILED"])
        with col2:
            region_filter = st.selectbox("Region", ["All"] + history['region'].unique().tolist())
        
        # Apply filters
        filtered = history.copy()
        if status_filter == "SUCCESS":
            filtered = filtered[filtered['status'] == 'SUCCESS']
        elif status_filter == "FAILED":
            filtered = filtered[filtered['status'].str.startswith('FAILED')]
        
        if region_filter != "All":
            filtered = filtered[filtered['region'] == region_filter]
        
        # Display table
        st.subheader("📋 Upload Records")
        
        # Format the dataframe for display
        display_df = filtered.copy()
        display_df['upload_timestamp'] = pd.to_datetime(display_df['upload_timestamp']).dt.strftime('%Y-%m-%d %H:%M:%S')
        display_df.columns = ['ID', 'Upload Time', 'Filename', 'Data Date', 'Region', 'Stocks', 'Status']
        
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        
        # Download history
        csv = display_df.to_csv(index=False)
        st.download_button(
            "📥 Download Upload History",
            csv,
            "upload_history.csv",
            "text/csv"
        )
    
    # Data summary by region and date
    st.subheader("📊 Data Summary by Region")
    summary = tracker.get_data_summary()
    if not summary.empty:
        # Group by region
        region_summary = summary.groupby('region').agg({
            'date': ['min', 'max', 'count'],
            'stock_count': 'sum'
        }).reset_index()
        region_summary.columns = ['Region', 'Earliest Date', 'Latest Date', 'Data Points', 'Total Records']
        st.dataframe(region_summary, use_container_width=True, hide_index=True)

# ============================================
# PAGE: Stock Lookup
# ============================================
elif page == "🔍 Stock Lookup":
    st.title("🔍 Stock Lookup")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        ticker = st.text_input("Enter Ticker Symbol").upper()
    with col2:
        regions = tracker.get_all_regions()
        region_filter = st.selectbox("Region", ["All"] + regions)
    
    if ticker:
        region = None if region_filter == "All" else region_filter
        history = tracker.get_ticker_history(ticker, region)
        
        if history.empty:
            st.warning(f"No data found for {ticker}")
        else:
            st.subheader(f"📈 {ticker} - {history.iloc[0]['company_name']}")
            
            # Current status
            latest = history.iloc[-1]
            earliest = history.iloc[0]
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Current Decile", int(latest['decile']))
            with col2:
                st.metric("Sector", latest['sector'])
            with col3:
                if len(history) > 1:
                    change = int(latest['decile'] - earliest['decile'])
                    st.metric("Overall Change", change, delta=change)
                else:
                    st.metric("Data Points", 1)
            with col4:
                st.metric("Region", latest['region'])
            
            # Chart
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=history['date'],
                y=history['decile'],
                mode='lines+markers',
                name='Decile',
                line=dict(color='blue', width=2),
                marker=dict(size=8)
            ))
            
            # Add reference lines for top/bottom thresholds
            fig.add_hline(y=8, line_dash="dash", line_color="green", 
                         annotation_text="Top Decile Threshold")
            fig.add_hline(y=3, line_dash="dash", line_color="red", 
                         annotation_text="Bottom Decile Threshold")
            
            fig.update_layout(
                title=f"{ticker} Decile History",
                xaxis_title="Date",
                yaxis_title="Decile (Higher = Better)",
                yaxis=dict(range=[0, 11])
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # History table
            st.subheader("📋 Historical Data")
            display_df = history[['date', 'decile', 'score', 'sector', 'region']].copy()
            display_df.columns = ['Date', 'Decile', 'Score', 'Sector', 'Region']
            st.dataframe(display_df, use_container_width=True, hide_index=True)

# ============================================
# PAGE: Data Management
# ============================================
elif page == "⚙️ Data Management":
    st.title("⚙️ Data Management")
    
    # Database migration
    st.subheader("🔄 Database Migration")
    st.markdown("""
    If you have an existing database from before the region support was added,
    run this migration to update the schema.
    """)
    
    if st.button("Run Migration"):
        with st.spinner("Migrating database..."):
            result = tracker.migrate_database()
        if result['success']:
            st.success(result['message'])
        else:
            st.error(f"Migration failed: {result.get('error', 'Unknown error')}")
    
    st.divider()
    
    # Delete data
    st.subheader("🗑️ Delete Data")
    st.warning("⚠️ This action cannot be undone!")
    
    col1, col2 = st.columns(2)
    with col1:
        dates = tracker.get_all_dates()
        delete_date = st.selectbox("Select Date to Delete", ["None"] + dates)
    with col2:
        regions = tracker.get_all_regions()
        delete_region = st.selectbox("Select Region to Delete", ["None"] + regions)
    
    if delete_date != "None" or delete_region != "None":
        date_val = delete_date if delete_date != "None" else None
        region_val = delete_region if delete_region != "None" else None
        
        confirm = st.checkbox("I understand this will permanently delete the selected data")
        
        if confirm and st.button("🗑️ Delete Selected Data", type="primary"):
            result = tracker.delete_data(date_val, region_val)
            if result['success']:
                st.success(result['message'])
                st.cache_resource.clear()
            else:
                st.error(result.get('error', 'Delete failed'))
    
    st.divider()
    
    # Database info
    st.subheader("📊 Database Statistics")
    summary = tracker.get_data_summary()
    if not summary.empty:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Records", summary['stock_count'].sum())
        with col2:
            st.metric("Unique Dates", len(summary['date'].unique()))
        with col3:
            st.metric("Regions", len(summary['region'].unique()))
        
        st.dataframe(summary, use_container_width=True, hide_index=True)
    else:
        st.info("No data in database")

# Footer
st.sidebar.divider()
st.sidebar.caption("GVI Decile Tracker v2.0")
st.sidebar.caption("With region support & upload history")
