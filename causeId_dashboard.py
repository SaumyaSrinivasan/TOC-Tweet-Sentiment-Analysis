# Import necessary libraries
import streamlit as st
import mysql.connector
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import os
import argparse


# Create a connection to the MySQL database
def create_db_connection():
    return mysql.connector.connect(
        host='localhost',
        user='root',
        password='',
        database='toc_db'
    )

# Get the 'toc_name' from the Flask session
toc_name = st.session_state.keys  
toc_name = os.environ.get('TOC_NAME')

# Read data from the MySQL database
def read_data(query, connection):
    with connection.cursor() as cursor:
        cursor.execute(query)
        data = cursor.fetchall()
    return data

# Streamlit App
def main():
    # Create a database connection
    connection = create_db_connection()

    # Title and header
    st.title("TOC key statistics Dashboard")
    st.sidebar.header("Select Options")

    # Sidebar - Year selection
    years_query = "SELECT DISTINCT Time_Period FROM toc_stats"
    years = [row[0] for row in read_data(years_query, connection)]
    selected_year = st.sidebar.selectbox("Select Year for finance information", years)


    if selected_tab == "General Statistics":
        st.header("General Statistics")

        # Query to fetch data for General Statistics
        general_stats_query = f"""
        SELECT Time_Period, 
               Number_of_Stations_Managed,
               Route_Kilometers_Operated,
               Number_of_FTE_Employees,
               Number_of_Passenger_Assists
        FROM toc_stats
        WHERE TOC_Name = '{toc_name}'
        """

        # Create a DataFrame from the query result
        general_stats_df = pd.DataFrame(read_data(general_stats_query, connection), columns=["Time_Period", "Stations", "Route_KM", "FTE_Employees", "Number_of_Passenger_Assists"])

        # Display the filtered data
        st.subheader("General Statistics for Selected Year and TOC")
        st.write(general_stats_df)

        # Bar chart for Number_of_Passenger_Assists
        st.subheader("Bar Chart for Number of Passenger Assists")
        bar_fig = px.bar(general_stats_df, x="Time_Period", y="Number_of_Passenger_Assists", title="Number of Passenger Assists Over Time")
        st.plotly_chart(bar_fig)

    elif selected_tab == "Usage Specific Information":
        st.header("Usage Specific Information")
        # First section - line chart for Passenger statistics
        st.subheader("Passenger Statistics")
        passenger_stats_query = f"""
        SELECT Time_Period,
              Passenger_Journeys_Millions,
              Passenger_Train_Kilometers_Millions
        FROM toc_stats
        WHERE TOC_Name = '{toc_name}'
        """

        # Create a DataFrame from the query result
        passenger_stats_df = DataFrame(read_data(passenger_stats_query, connection),
                                           columns=["Time_Period", "Journeys (Millions)", "Train Kilometers (Millions)"])

         # Convert columns to numeric
        passenger_stats_df["Journeys (Millions)"] = pd.to_numeric(passenger_stats_df["Journeys (Millions)"], errors='coerce')
        passenger_stats_df["Train Kilometers (Millions)"] = pd.to_numeric(passenger_stats_df["Train Kilometers (Millions)"], errors='coerce')

        # Line chart for Passenger statistics
        line_fig = px.line(passenger_stats_df, x="Time_Period", y=["Journeys (Millions)", "Train Kilometers (Millions)"],
                             title="Passenger Statistics Over Time")
        st.plotly_chart(line_fig)

        # Second section - bar charts for Delays, Complaints, and Compensations
        st.subheader("Delays, Complaints, and Compensations")
        delay_complaints_query = f"""
        SELECT Time_Period,
              Passenger_Kilometers_Millions,
              Complaints_Closed,
              Delay_Compensation_Claims_Closed,
              Delay_Minutes,
              Trains_On_Time_Percentage,
              Cancellation_Score_Percentage,
              Trains_Planned
        FROM toc_stats
        WHERE TOC_Name = '{toc_name}'
        """


        # Create separate charts
        st.subheader("Passenger Kilometers (Millions) Over Time")
        passenger_km_fig = px.bar(usage_stats_df, x="Time_Period", y="Passenger Kilometers (Millions)",
                              title="Passenger Kilometers (Millions) Over Time")
        st.plotly_chart(passenger_km_fig)

         # Line charts for Complaints and Delays
        line_fig1 = px.line(usage_stats_df, x="Time_Period", y="Complaints Closed", title="Complaints Closed Over Time")
        line_fig2 = px.line(usage_stats_df, x="Time_Period", y="Delay Compensation Claims Closed", title="Delay Compensation Claims Closed Over Time")
        line_fig3 = px.line(usage_stats_df, x="Time_Period", y="Delay Minutes", title="Delay Minutes Over Time")
        
        st.plotly_chart(line_fig1)
        st.plotly_chart(line_fig2)
        st.plotly_chart(line_fig3)
        
        # Second section - bar charts for 'Trains_On_Time_Percentage' and 'Cancellation_Score_Percentage'
        st.subheader("Trains On-Time Percentage and Cancellation Score Percentage")
        
        bar_fig1 = px.bar(usage_stats_df, x="Time_Period", y="Trains On-Time Percentage", title="Trains On-Time Percentage Over Time")
        bar_fig2 = px.bar(usage_stats_df, x="Time_Period", y="Cancellation Score Percentage", title="Cancellation Score Percentage Over Time")
        
        st.plotly_chart(bar_fig1)
        st.plotly_chart(bar_fig2)

        st.subheader("Trains Planned Over Time")
        trains_planned_fig = px.bar(usage_stats_df, x="Time_Period", y="Trains Planned", title="Trains Planned Over Time")
        st.plotly_chart(trains_planned_fig)

    elif selected_tab == "Finance Information":
        st.header("Finance Information")

        # Query to fetch finance data for the selected TOC and year
        finance_query = f"""
        SELECT Total_income, Fare_income, other_operator_income, Total_operating_expenditure, Staff_expense, Rolling_stock_expense
        FROM toc_stats
        WHERE TOC_Name = '{toc_name}' AND Time_Period = '{selected_year}'
        """

        # Create a DataFrame from the query result
        finance_df = pd.DataFrame(read_data(finance_query, connection), columns=["Total Income", "Fare Income", "Other Operator Income", "Total Operating Expenditure", "Staff Expense", "Rolling Stock Expense"])


        # Combine all the data into a single list
        combined_data = [finance_df[column].sum() for column in finance_df.columns]

        # Remove commas and convert columns to numeric
        columns_to_convert = ["Total Income", "Fare Income", "Other Operator Income", "Total Operating Expenditure", "Staff Expense", "Rolling Stock Expense"]
        finance_df[columns_to_convert] = finance_df[columns_to_convert].replace('[\$,]', '', regex=True).astype(float)

        # Calculate the sum of income and expenditure columns
        income_columns = ["Total Income", "Fare Income", "Other Operator Income"]
        expenditure_columns = ["Total Operating Expenditure", "Staff Expense", "Rolling Stock Expense"]

        total_income = finance_df[income_columns].sum().sum()
        total_expenditure = finance_df[expenditure_columns].sum().sum()

        # Create pie charts and display data
        st.subheader("Finance Data Pie Charts")
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(22, 12))

        # Pie chart for income and expenditure
        ax1.pie([total_income, total_expenditure], labels=["Income", "Expenditure"], autopct='%1.1f%%', shadow=True, startangle=90)
        ax1.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
        ax1.set_title("Income vs. Expenditure")

        # Display a pie chart with all the columns combined
        ax2.pie(combined_data, labels=finance_df.columns, autopct='%1.1f%%', shadow=True, startangle=90)
        ax2.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
        ax2.set_title("Combined Finance Data")

        st.pyplot(fig)

        # Display the values of each column as a table
        st.subheader("Finance Data Values")
        st.table(finance_df.sum().to_frame().reset_index().rename(columns={0: "Pence per passenger km"}))

    # Close the database connection
    connection.close()

if __name__ == "__main__":
    main()
