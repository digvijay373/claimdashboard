import pandas as pd
import streamlit as st
import plotly.express as px
from datetime import datetime
import plotly.graph_objects as go


st.set_page_config(
    page_title="Claim Leakage Dashboard Testing",
    page_icon="🏂",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
        /* General body background color */
        body {
            background-color: #f0f0f0;
        }
        /* Sidebar custom styling */
        .sidebar .sidebar-content {
            background-color: #ffffff;
        }
        /* Input fields in sidebar */
        .css-1to6prn input {
            border: 2px solid #5d3a9b;
            background-color: #f8f8f8;
            color: #333333;
            padding: 10px;
        }
        /* Sidebar header styling */
        .css-1to6prn label {
            color: #5d3a9b;
        }
        /* Title and Subheader text color */
        .css-ffhzg2 {
            color: #5d3a9b;
        }
        /* Button Styling */
        .css-1v3fvcr button {
            background-color: #5d3a9b;
            color: white;
            border-radius: 5px;
        }
        /* Styling for Metric Cards */
        .css-1v3fvcr {
            background-color: #5d3a9b;
            color: white;
            border-radius: 5px;
        }
        /* Change background of the filters */
        .stTextInput {
            background-color: #e0e0e0;
            border-radius: 8px;
            padding: 10px;
            border: 2px solid #5d3a9b;
        }
        /* Metric card styling */
        .stMetric {
            background-color: #ffffff;
            border: 2px solid #5d3a9b;
            padding: 15px;
            border-radius: 8px;
        }
        /* Styling for the multiselect input */
        .stMultiSelect {
            background-color: #e0e0e0;
            border-radius: 8px;
            padding: 10px;
            border: 2px solid #5d3a9b;
        }
        /* Change text color and border of selected items */
        .stMultiSelect input {
            color: #5d3a9b;
            background-color: #f8f8f8;
            padding: 8px;
        }
        /* Styling for the dropdown options */
        div[role="listbox"] {
            background-color: #f8f8f8; /* Background color of the dropdown */
            border: 2px solid #5d3a9b; /* Border color of the dropdown */
            border-radius: 8px;
            padding: 8px;
        }
        /* Change selected option in the dropdown */
        div[role="option"][aria-selected="true"] {
            background-color: #5d3a9b; /* Background color when an option is selected */
            color: white; /* Text color of the selected option */
        }
        /* Optional: Change unselected options background color */
        div[role="option"]:not([aria-selected="true"]) {
            background-color: #e0e0e0; /* Light gray for unselected options */
            color: #5d3a9b; /* Border color for unselected options */
        }
        /* Styling for the multiselect input */
        .stDateInput {
            background-color: #e0e0e0;
            border-radius: 8px;
            padding: 10px;
            border: 2px solid #5d3a9b;
        }
        /* Change text color, background color, and border of the selected item */
        .stDateInput input {
            color: #5d3a9b; /* Text color same as border color */
            background-color: #f8f8f8;
            padding: 8px;
        }
        .stDateInput input::placeholder {
            color: #5d3a9b; /* Match placeholder text color with the border */
        }
    </style>
""", unsafe_allow_html=True)

# Function to fetch data from the claims table in PostgreSQL
def fetch_claims_data():
    try:
        # # Database connection parameters
        # conn = psycopg2.connect(
        #     dbname="postgres",
        #     user="postgres",
        #     password="1234",
        #     host="localhost",
        #     port="5432"
        # )
        
        # # SQL query to fetch data
        # query = "SELECT * FROM claim_details limit 200000"
        
        # Fetch data and load it into a Pandas DataFrame
        df = pd.read_csv("Claims.csv")
        
        # Ensure date columns are in the correct format
        date_columns = [
            'claim_received_date', 'claim_loss_date', 'claim_finalised_date',
            'original_verified_date_of_loss_time', 'last_verified_date_of_loss_time',
            'catastrophe_valid_from_date_time', 'catastrophe_valid_to_date_time', 'update_date'
        ]
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce').dt.date
        
    except Exception as e:
        print(f"Error fetching data: {e}")
        df = pd.DataFrame()  # Return empty DataFrame on failure
    
    
    return df

# Streamlit app for the report with independent filters and charts
def main():
    # Initialize session state for date filters
    if "date_filters" not in st.session_state:
        data = fetch_claims_data()
        date_columns = [
            'claim_received_date', 'claim_loss_date', 'claim_finalised_date', 
            'original_verified_date_of_loss_time', 'last_verified_date_of_loss_time', 
            'catastrophe_valid_from_date_time', 'catastrophe_valid_to_date_time'
        ]
        st.session_state.date_filters = {
            col: (data[col].min(), data[col].max()) 
            for col in date_columns
        }

    # Display logo
    st.image("exl.png", width=150)
    st.title("Claim Report Dashboard Testing")

    # Fetch data from the database
    data = fetch_claims_data()

    if not data.empty:
        # Sidebar for filters
        st.sidebar.header("Filter Options")

        # Initialize session state for filters
        if 'claim_numbers' not in st.session_state:
            params = st.query_params
            st.session_state.claim_numbers = params.get('claim_numbers', '')

        # Apply claim number filter
        claim_numbers = st.sidebar.text_input(
            "Filter by Claim Number (comma-separated)", 
            value=st.session_state.claim_numbers
        )
        st.session_state.claim_numbers = claim_numbers

        if claim_numbers:
            claim_numbers = [num.strip() for num in claim_numbers.split(",") if num.strip()]
            filtered_data = data[data['claim_number'].astype(str).isin(claim_numbers)]
        else:
            filtered_data = data.copy()

        # Text-based filters with an "All" option for each relevant column
        text_columns = [
            'source_system', 'general_nature_of_loss', 'line_of_business', 'claim_status', 
            'fault_rating', 'fault_categorisation'
        ]

        # Initialize text filters in session state if not present
        if 'text_filters' not in st.session_state:
            params = st.query_params
            st.session_state.text_filters = {
                col: params.get(col, ['All']) 
                for col in text_columns
            }

        # Apply text-based filters
        for col in text_columns:
            unique_values = data[col].dropna().unique().tolist()
            unique_values.insert(0, "All")  # Add "All" option
            selected_values = st.sidebar.multiselect(
                f"Filter by {col}", 
                options=unique_values, 
                default=st.session_state.text_filters[col]
            )
            st.session_state.text_filters[col] = selected_values
            
            # Apply filter only if "All" is not selected
            if "All" not in selected_values:
                filtered_data = filtered_data[filtered_data[col].isin(selected_values)]

        # Independent Date range filters
        date_columns = [
            'claim_received_date', 'claim_loss_date', 'claim_finalised_date', 
            'original_verified_date_of_loss_time', 'last_verified_date_of_loss_time', 
            'catastrophe_valid_from_date_time', 'catastrophe_valid_to_date_time'
        ]
        for col in date_columns:
            min_date, max_date = st.session_state.date_filters[col]
            date_range = st.sidebar.date_input(f"{col} Range", value=(min_date, max_date))
            st.session_state.date_filters[col] = date_range
            if date_range:
                filtered_data = filtered_data[filtered_data[col].between(date_range[0], date_range[1])]

        # Display filtered statistics
        st.markdown("""
            <style>
                h3 {
                    color: #5d3a9b !important;
                }
            </style>
        """, unsafe_allow_html=True)
        st.subheader("Filtered Claims Statistics")
        st.write("Total Claims:", filtered_data["claim_number"].nunique())

        def display_custom_metric(title, value, background_color="#f0f0f0"):
            card_style = f"""
            <style>
            .metric-card {{
                border: 2px solid #5d3a9b;
                border-radius: 8px;
                background-color: {background_color};
                padding: 20px;
                margin: 10px;
                height: 200px;  
                width: 160px;
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
            }}
            .metric-card h3 {{
                color: #5d3a9b;
                font-size: 18px;
                margin-bottom: 10px;
            }}
            .metric-card .value {{
                font-size: 36px;
                font-weight: bold;
                color: #333;
                margin-bottom: 0px;
            }}
            </style>
            """

            # HTML for the metric card
            card_html = f"""
            <div class="metric-card">
                <h3>{title}</h3>
                <div class="value">{value}</div>
            </div>
            """

            # Render the card with custom styling
            st.markdown(card_style + card_html, unsafe_allow_html=True)
        
        st.subheader("Metrics Overview")
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        
        with col1:
            display_custom_metric("Claims Monitored", "3,071")
        with col2:
            display_custom_metric("Claims with Leakage Opportunity", "1,854")

        with col3:
            def display_gauge_in_metric_card(title, gauge_value, background_color="#f0f0f0"):
                if not isinstance(gauge_value, (int, float)):
                    raise ValueError("gauge_value must be a numeric type.")

                card_style = f"""
                <style>
                .gauge-card {{
                    border: 2px solid #5d3a9b;
                    border-radius: 8px;
                    background-color: {background_color};
                    padding: 20px;
                    margin: 10px;
                    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
                    height: 400px;  /* Fixed height for all cards */
                    width: 300px;   /* Fixed width for all cards */
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    text-align: center;
                    justify-content: space-between;
                }}
                .gauge-card h3 {{
                    color: #5d3a9b;
                    font-size: 18px;
                    margin-bottom: 10px;
                }}
                </style>
                """

                fig = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=gauge_value,
                    gauge={'axis': {'range': [0, 100]}, 'bar': {'color': "#5d3a9b"}},
                    title={'text': f"{title} (%)", 'font': {'size': 16, 'color': 'black'}},
                    domain={'x': [0, 1], 'y': [0, 1]}
                ))
                fig.update_layout(height=170, margin=dict(t=0, b=0, l=0, r=0))

                with st.container():
                    st.markdown(card_style, unsafe_allow_html=True)
                    st.markdown(f"<div class='gauge-card'><h3>{title}</h3></div>", unsafe_allow_html=True)
                    st.plotly_chart(fig, use_container_width=True)

            display_custom_metric("Leakage Opportunity %", 60)

        with col4:
            display_custom_metric("Potential Leakage $", "$51.2M")

        with col5:
            display_custom_metric("Leakage Rate %", 100)

        with col6:
            display_custom_metric("Opportunities Not Actioned", "3,063")
        
        st.markdown("<br><br>", unsafe_allow_html=True)
        col1, col2 = st.columns(2, gap="small")

        with col1:
            st.subheader("Claims by Status")
            status_counts = filtered_data['claim_status'].value_counts().reset_index()
            status_counts.columns = ['claim_status', 'count']
            fig_status = px.bar(
                status_counts, x='claim_status', y='count', title="Claims by Status", 
                color='claim_status', color_discrete_sequence=px.colors.sequential.Plasma
            )
            fig_status.update_layout(
                plot_bgcolor="#ffffff",
                paper_bgcolor="#f0f2f6",
            )
            st.plotly_chart(fig_status)

        with col2:
            st.subheader("Claims Over Time")
            claims_over_time = filtered_data.groupby('claim_received_date').size().reset_index(name='claim_count')
            fig_time = px.line(
                claims_over_time, x='claim_received_date', y='claim_count', 
                title="Claims Over Time", color_discrete_sequence=px.colors.sequential.Viridis
            )
            fig_time.update_layout(
                plot_bgcolor="#ffffff",
                paper_bgcolor="#f0f2f6",
            )
            st.plotly_chart(fig_time)

        col3, col4 = st.columns(2, gap="small")

        with col3:
            st.subheader("Claim Status Distribution")
            fig_pie = px.pie(filtered_data, names='claim_status', title="Claim Status Distribution", hole=0.3)
            fig_pie.update_layout(
                plot_bgcolor="#ffffff",
                paper_bgcolor="#f0f2f6",
            )
            st.plotly_chart(fig_pie)

        with col4:
            st.subheader("Claims by Line of Business")
            line_of_business_counts = filtered_data['line_of_business'].value_counts().reset_index()
            line_of_business_counts.columns = ['line_of_business', 'count']
            fig_line_of_business = px.bar(
                line_of_business_counts, 
                y='line_of_business', 
                x='count', 
                orientation='h', 
                title="Claims by Line of Business", 
                color='line_of_business'
            )
            fig_line_of_business.update_layout(
                plot_bgcolor="#ffffff",
                paper_bgcolor="#f0f2f6",
                showlegend=False,
            )
            fig_line_of_business.update_xaxes(title="Count")
            fig_line_of_business.update_yaxes(title="Line of Business")
            st.plotly_chart(fig_line_of_business)
            
        st.subheader("Claim Status Trend Over Months")
        filtered_data['claim_received_date'] = pd.to_datetime(filtered_data['claim_received_date'], errors='coerce')
        filtered_data['month_year'] = filtered_data['claim_received_date'].dt.to_period('M').astype(str)
        monthly_status_counts = (
            filtered_data.groupby(['month_year', 'claim_status'])
            .size()
            .reset_index(name='count')
        )

        fig_trend_monthly = px.bar(
            monthly_status_counts, 
            x='month_year', 
            y='count', 
            color='claim_status', 
            title="Monthly Claim Status Trend (Open vs Closed)",
            barmode='group'
        )

        monthly_totals = monthly_status_counts.groupby('month_year')['count'].sum().reset_index()
        fig_trend_monthly.add_scatter(
            x=monthly_totals['month_year'], 
            y=monthly_totals['count'], 
            mode='lines+markers', 
            name='Total Claims Trend',
            line=dict(color='blue', width=2)
        )

        fig_trend_monthly.update_layout(
            plot_bgcolor="#ffffff",
            paper_bgcolor="#f0f2f6",
            xaxis_title="Month-Year",
            yaxis_title="Number of Claims",
            xaxis_tickangle=-45
        )
        st.plotly_chart(fig_trend_monthly)
        
        st.subheader("Filtered Claims Data")
        filtered_data = filtered_data.head(20)

        def style_alternate_rows(x):
            style = pd.DataFrame('', index=x.index, columns=x.columns)
            style.iloc[::2] = 'background-color: #f9f9f9'  # Light gray for even rows
            style.iloc[1::2] = 'background-color: #e6e6e6'  # Slightly darker gray for odd rows
            return style

        styled_df = filtered_data.style.apply(style_alternate_rows, axis=None)
        st.dataframe(styled_df)

        csv = filtered_data.to_csv(index=False)
        st.download_button("Download as CSV", csv, "filtered_claims.csv", "text/csv")
        
    else:
        st.warning("No data available.")

if __name__ == "__main__":
    main()
