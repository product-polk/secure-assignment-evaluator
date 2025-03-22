import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import re

def extract_tables_and_visualize(table_data):
    """
    Visualize table data securely
    
    Args:
        table_data (dict): Table data with DataFrame
    """
    # Extract the DataFrame
    df = table_data["data"]
    
    # Display basic information
    st.write(f"Table from page {table_data['page']}")
    
    # Clean column names (remove whitespace)
    df.columns = [str(col).strip() for col in df.columns]
    
    # Display the table in a secure way
    st.dataframe(df)
    
    # Try to intelligently create a visualization if possible
    try:
        # Check if there are numeric columns that could be visualized
        numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns.tolist()
        text_cols = df.select_dtypes(include=['object']).columns.tolist()
        
        if len(numeric_cols) > 0 and len(text_cols) > 0:
            # We have both text and numeric columns, so we can create a bar or line chart
            st.write("### Visualization")
            
            # Select columns for visualization
            category_col = st.selectbox("Select category column:", text_cols, key=f"cat_{table_data['table_id']}")
            value_col = st.selectbox("Select value column:", numeric_cols, key=f"val_{table_data['table_id']}")
            
            # Determine chart type
            chart_types = ["Bar Chart", "Line Chart", "Scatter Plot"]
            chart_type = st.selectbox("Select chart type:", chart_types, key=f"chart_type_{table_data['table_id']}")
            
            # Create the chart
            if chart_type == "Bar Chart":
                fig = px.bar(df, x=category_col, y=value_col, title=f"{value_col} by {category_col}")
                st.plotly_chart(fig, use_container_width=True)
            elif chart_type == "Line Chart":
                fig = px.line(df, x=category_col, y=value_col, title=f"{value_col} by {category_col}")
                st.plotly_chart(fig, use_container_width=True)
            else:  # Scatter Plot
                fig = px.scatter(df, x=category_col, y=value_col, title=f"{value_col} vs {category_col}")
                st.plotly_chart(fig, use_container_width=True)
        
        elif len(numeric_cols) >= 2:
            # We have multiple numeric columns, so we can create a scatter plot
            st.write("### Visualization")
            
            x_col = st.selectbox("Select X-axis:", numeric_cols, key=f"x_{table_data['table_id']}")
            y_col = st.selectbox("Select Y-axis:", numeric_cols, key=f"y_{table_data['table_id']}", index=min(1, len(numeric_cols)-1))
            
            fig = px.scatter(df, x=x_col, y=y_col, title=f"{y_col} vs {x_col}")
            st.plotly_chart(fig, use_container_width=True)
    
    except Exception as e:
        st.write(f"Could not create visualization: {e}")
        
    # Offer table analysis option
    if st.button("Analyze Table", key=f"analyze_{table_data['table_id']}"):
        with st.spinner("Analyzing table..."):
            # Perform basic table analysis
            st.write("### Table Analysis")
            
            # Display basic statistics for numeric columns
            numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns.tolist()
            if numeric_cols:
                st.write("#### Numeric Column Statistics")
                st.dataframe(df[numeric_cols].describe())
            
            # Count unique values for categorical columns
            categorical_cols = df.select_dtypes(include=['object']).columns.tolist()
            if categorical_cols:
                st.write("#### Categorical Column Distributions")
                for col in categorical_cols[:3]:  # Limit to first 3 columns to avoid overload
                    st.write(f"**{col}** distribution:")
                    value_counts = df[col].value_counts().reset_index()
                    value_counts.columns = [col, 'Count']
                    st.dataframe(value_counts)
                    
                    # Simple bar chart of distribution
                    fig = px.bar(value_counts, x=col, y='Count', title=f"{col} Distribution")
                    st.plotly_chart(fig, use_container_width=True)

def extract_charts_and_visualize(chart_info):
    """
    Visualize chart information securely
    
    Args:
        chart_info (dict): Chart information
    """
    st.write(f"Chart/Figure from page {chart_info['page']}")
    st.write(chart_info["description"])
    
    # Since we can't access the actual chart image, we'll create a placeholder
    # and provide a description of what would be visible
    st.info(f"This is a protected chart area. The chart appears on page {chart_info['page']}.")
    
    # Offer to generate a recreation based on description
    if st.button("Generate Visual Interpretation", key=f"recreate_{chart_info['chart_id']}"):
        with st.spinner("Interpreting chart..."):
            # Create a placeholder chart based on the chart area text
            st.write("### Visual Interpretation")
            
            # Create a placeholder visualization
            create_placeholder_visualization(chart_info)

def create_placeholder_visualization(chart_info):
    """
    Create a placeholder visualization based on chart description
    
    Args:
        chart_info (dict): Chart information
    """
    # Create a placeholder figure with a note
    fig = go.Figure()
    
    fig.add_annotation(
        text="Chart Visual Interpretation<br>(Based on surrounding text context)",
        xref="paper", yref="paper",
        x=0.5, y=0.5,
        showarrow=False,
        font=dict(size=16)
    )
    
    # Check if the chart description contains keywords to guess chart type
    description = chart_info["description"].lower()
    
    # Detect chart type from the description
    chart_type = "unknown"
    if "bar" in description:
        chart_type = "bar"
        fig = example_bar_chart()
    elif "pie" in description:
        chart_type = "pie"
        fig = example_pie_chart()
    elif "line" in description:
        chart_type = "line"
        fig = example_line_chart()
    elif "scatter" in description:
        chart_type = "scatter"
        fig = example_scatter_chart()
    elif "histogram" in description:
        chart_type = "histogram"
        fig = example_histogram()
    
    # Set figure layout
    fig.update_layout(
        title=f"Interpreted {chart_type.title()} Chart",
        title_x=0.5,
        xaxis_title="X Axis (Categories/Values)",
        yaxis_title="Y Axis (Values)",
        plot_bgcolor='rgba(240, 240, 240, 0.5)',
        height=400,
    )
    
    # Display with a disclaimer
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Note: This is a visual interpretation based on context clues, not the actual chart from the document.")

# Example chart generators for placeholder visualizations
def example_bar_chart():
    categories = ["Category A", "Category B", "Category C", "Category D"]
    values = [15, 30, 25, 20]
    return px.bar(x=categories, y=values)

def example_pie_chart():
    categories = ["Segment 1", "Segment 2", "Segment 3", "Segment 4"]
    values = [35, 25, 20, 20]
    return px.pie(values=values, names=categories)

def example_line_chart():
    x = list(range(10))
    y = [i**2 for i in range(10)]
    return px.line(x=x, y=y)

def example_scatter_chart():
    import numpy as np
    x = np.random.rand(20)
    y = x + np.random.normal(0, 0.2, 20)
    return px.scatter(x=x, y=y)

def example_histogram():
    import numpy as np
    data = np.random.normal(0, 1, 100)
    return px.histogram(data)
