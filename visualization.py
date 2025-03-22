import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import re
from secure_qa import answer_question

def extract_tables_and_visualize(table_data):
    """
    Visualize table data securely
    
    Args:
        table_data (dict): Table data with DataFrame
    """
    try:
        # Extract the DataFrame and make a copy to avoid modifying the original
        df = table_data["data"].copy()
        
        # Display basic information
        st.write(f"Table from page {table_data['page']}")
        
        # Create a safe version of the table with fixed column names
        df_safe = create_safe_dataframe(df)
        
        # Display the table in a secure way
        st.dataframe(df_safe)
        
        # Try to intelligently create a visualization if possible
        try:
            # Check if there are numeric columns that could be visualized
            numeric_cols = df_safe.select_dtypes(include=['int64', 'float64']).columns.tolist()
            text_cols = df_safe.select_dtypes(include=['object']).columns.tolist()
            
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
                    fig = px.bar(df_safe, x=category_col, y=value_col, title=f"{value_col} by {category_col}")
                    st.plotly_chart(fig, use_container_width=True)
                elif chart_type == "Line Chart":
                    fig = px.line(df_safe, x=category_col, y=value_col, title=f"{value_col} by {category_col}")
                    st.plotly_chart(fig, use_container_width=True)
                else:  # Scatter Plot
                    fig = px.scatter(df_safe, x=category_col, y=value_col, title=f"{value_col} vs {category_col}")
                    st.plotly_chart(fig, use_container_width=True)
            
            elif len(numeric_cols) >= 2:
                # We have multiple numeric columns, so we can create a scatter plot
                st.write("### Visualization")
                
                x_col = st.selectbox("Select X-axis:", numeric_cols, key=f"x_{table_data['table_id']}")
                y_col = st.selectbox("Select Y-axis:", numeric_cols, key=f"y_{table_data['table_id']}", index=min(1, len(numeric_cols)-1))
                
                fig = px.scatter(df_safe, x=x_col, y=y_col, title=f"{y_col} vs {x_col}")
                st.plotly_chart(fig, use_container_width=True)
        
        except Exception as e:
            st.write(f"Could not create visualization: {e}")
            
        # Offer table analysis option
        if st.button("Analyze Table", key=f"analyze_{table_data['table_id']}"):
            with st.spinner("Analyzing table..."):
                # Perform basic table analysis
                st.write("### Table Analysis")
                
                # Display basic statistics for numeric columns
                numeric_cols = df_safe.select_dtypes(include=['int64', 'float64']).columns.tolist()
                if numeric_cols:
                    st.write("#### Numeric Column Statistics")
                    st.dataframe(df_safe[numeric_cols].describe())
                
                # Count unique values for categorical columns
                categorical_cols = df_safe.select_dtypes(include=['object']).columns.tolist()
                if categorical_cols:
                    st.write("#### Categorical Column Distributions")
                    for col in categorical_cols[:3]:  # Limit to first 3 columns to avoid overload
                        st.write(f"**{col}** distribution:")
                        value_counts = df_safe[col].value_counts().reset_index()
                        value_counts.columns = [col, 'Count']
                        st.dataframe(value_counts)
                        
                        # Simple bar chart of distribution
                        fig = px.bar(value_counts, x=col, y='Count', title=f"{col} Distribution")
                        st.plotly_chart(fig, use_container_width=True)
            
    except Exception as e:
        st.error(f"Error displaying table: {e}")
        st.write("Could not display this table due to formatting issues. Displaying text version instead.")
        try:
            # Try to show a text representation
            st.text(str(table_data["data"]))
        except:
            st.write("Unable to display table contents in any format.")

def create_safe_dataframe(df):
    """
    Create a safe version of a DataFrame with unique, clean column names
    
    Args:
        df (pandas.DataFrame): The original DataFrame
        
    Returns:
        pandas.DataFrame: A DataFrame with safe column names
    """
    try:
        # Make a copy of the DataFrame
        safe_df = df.copy()
        
        # Generate unique column names
        cols = df.columns.tolist()
        clean_cols = []
        seen = {}
        
        for i, col in enumerate(cols):
            # Convert to string and clean
            col_str = str(col).strip() if col else f"Col{i}"
            
            # If empty or None, use default name
            if not col_str:
                col_str = f"Col{i}"
            
            # Handle duplicates
            if col_str in seen:
                seen[col_str] += 1
                col_str = f"{col_str}_{seen[col_str]}"
            else:
                seen[col_str] = 0
                
            clean_cols.append(col_str)
        
        # Set the cleaned column names
        safe_df.columns = clean_cols
        return safe_df
    
    except Exception as e:
        # If we can't fix the DataFrame, create a new one with the data
        st.warning(f"Had to reconstruct table due to: {e}")
        
        # Try to create a completely new DataFrame
        try:
            if hasattr(df, 'values') and hasattr(df, 'shape'):
                # Get the data values
                data = df.values
                
                # Create new column names
                cols = [f"Column_{i}" for i in range(df.shape[1])]
                
                # Create a new DataFrame
                import pandas as pd
                return pd.DataFrame(data, columns=cols)
            else:
                # Fallback if we can't get values
                return pd.DataFrame({"Data": ["Unable to display table"]})
        except:
            # Last resort fallback
            return pd.DataFrame({"Error": ["Could not reconstruct table"]})

def extract_charts_and_visualize(chart_info):
    """
    Extract and display chart information securely without visualizing
    
    Args:
        chart_info (dict): Chart information
    """
    st.write(f"##### Chart/Figure from page {chart_info['page']}")
    
    # Display chart context
    if "context" in chart_info:
        st.write("**Chart Context:**")
        st.markdown(f"```{chart_info['context']}```")
    
    # Display any text found in the chart area
    if "area_text" in chart_info and chart_info["area_text"]:
        st.write("**Text in chart area:**")
        st.markdown(f"```{chart_info['area_text']}```")
    
    # Provide insights about the chart
    st.write("**Chart Insights:**")
    
    # Get chart insights using the LLM but don't visualize
    with st.spinner("Analyzing chart context..."):
        insights_prompt = (
            f"Based on the surrounding text context of this chart on page {chart_info['page']}, "
            f"provide 3-5 key insights this chart likely conveys. DO NOT try to recreate or visualize the chart. "
            f"Just provide analytical insights based on the chart context. Format your response as bullet points."
        )
        
        if "context" in chart_info:
            insights_prompt += f"\n\nChart context: {chart_info['context']}"
        
        if "area_text" in chart_info and chart_info["area_text"]:
            insights_prompt += f"\n\nText in chart area: {chart_info['area_text']}"
            
        # Use the secure_qa.answer_question function to generate insights
        # We pass chunks=None because this is a special case not using document chunks
        insights = answer_question(insights_prompt, None)
        
        # Display the insights
        st.write(insights)

# The following placeholder visualization methods have been removed
# since we don't want to recreate any charts, even as placeholders.
# Instead, we only provide textual insights about the charts
# based on surrounding context.
