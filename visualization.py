import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import re
from secure_qa import answer_question

def extract_tables_and_visualize(table_data):
    """
    Provide insights about table data without displaying the full table
    
    Args:
        table_data (dict): Table data with DataFrame
    """
    try:
        # Extract the DataFrame but don't display it directly
        df = table_data["data"].copy()
        
        # Display only metadata about the table
        st.write(f"##### Table Analysis (Page {table_data['page']})")
        
        # Information about the table without showing content
        st.info(f"A table was detected on page {table_data['page']}. Below are insights about the table without displaying its full contents.")
        
        # Create a safe version of the table with fixed column names (for internal use only)
        df_safe = create_safe_dataframe(df)
        
        # Display table structure information
        st.write("**Table Structure:**")
        
        # Show column names and data types but not the actual data
        col_info = []
        for col in df_safe.columns:
            dtype = df_safe[col].dtype
            col_info.append(f"• {col} ({dtype})")
        
        st.write("\n".join(col_info))
        
        # Show summary stats of the table
        st.write("**Table Summary:**")
        st.write(f"• Rows: {len(df_safe)}")
        st.write(f"• Columns: {len(df_safe.columns)}")
        
        # Analyze the table using AI
        st.write("**Table Analysis:**")
        
        # Get insights about the table using the LLM
        with st.spinner("Analyzing table data..."):
            # Convert first few rows to string for analysis (limited data)
            table_sample = df_safe.head(3).to_string(index=False)
            
            # Create the prompt
            insights_prompt = (
                f"You're analyzing a table from page {table_data['page']}. "
                f"Provide 3-5 key insights about what this table represents based on its structure and a small sample. "
                f"DO NOT recreate the table or include large amounts of data in your response. "
                f"Format your response as bullet points and focus on the meaning/purpose of the table, not just describing it. "
                f"Do not include direct quotes from the table that could be used to reconstruct it.\n\n"
                f"Table columns: {', '.join(df_safe.columns.tolist())}"
            )
            
            # Use the secure_qa.answer_question function to generate insights
            insights = answer_question(insights_prompt, None)
            st.write(insights)
        
        # Add a section for evaluators to ask specific questions about the table using a form
        st.write("**Ask about this table:**")
        
        # Create a unique form key for this table
        form_key = f"table_form_{table_data['table_id']}"
        
        with st.form(key=form_key):
            table_question = st.text_input(
                "Ask a specific question about this table:", 
                key=f"table_question_{table_data['table_id']}"
            )
            submit_table_question = st.form_submit_button("Submit Question")
            
            if submit_table_question and table_question:
                with st.spinner("Analyzing..."):
                    # Create a prompt for the specific question that doesn't expose full data
                    question_prompt = (
                        f"Answer the following question about a table on page {table_data['page']} "
                        f"based on the table content. Do not include more than a few cells of data "
                        f"in your response and do not recreate the full table: {table_question}\n\n"
                        f"Table columns: {', '.join(df_safe.columns.tolist())}"
                    )
                    
                    answer = answer_question(question_prompt, None)
                    st.write("**Answer:**")
                    st.write(answer)
    
    except Exception as e:
        st.error(f"Error analyzing table: {e}")
        st.write("Could not analyze this table due to formatting issues.")

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
    Extract and display chart information securely without visualizing or revealing raw data
    
    Args:
        chart_info (dict): Chart information
    """
    st.write(f"##### Chart Analysis (Page {chart_info['page']})")
    
    # Only show that this is a chart detected on page X
    st.info(f"A chart or figure was detected on page {chart_info['page']}. Below are insights about what this chart likely represents, based on analysis of the surrounding content.")
    
    # Provide insights about the chart without showing raw context
    st.write("**Chart Insights:**")
    
    # Get chart insights using the LLM but don't visualize
    with st.spinner("Analyzing chart..."):
        # Create a prompt that doesn't expose the actual data
        insights_prompt = (
            f"Based on the surrounding text context of this chart on page {chart_info['page']}, "
            f"provide 3-5 key insights this chart likely conveys. DO NOT try to recreate or visualize the chart. "
            f"Just provide analytical insights based on the chart context. Format your response as bullet points. "
            f"Make sure your response does not include direct quotes that could be used to reconstruct the content."
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
        
    # Add a section for evaluators to ask specific questions about this chart using a form
    st.write("**Ask about this chart:**")
    
    # Create a unique form key for this chart
    form_key = f"chart_form_{chart_info['chart_id']}"
    
    with st.form(key=form_key):
        chart_question = st.text_input(
            "Ask a specific question about this chart:", 
            key=f"chart_question_{chart_info['chart_id']}"
        )
        submit_chart_question = st.form_submit_button("Submit Question")
        
        if submit_chart_question and chart_question:
            with st.spinner("Analyzing..."):
                # Create a prompt for the specific question
                question_prompt = (
                    f"Answer the following question about a chart on page {chart_info['page']} "
                    f"based on the surrounding context. Do not include direct quotes longer than a few words "
                    f"and do not try to recreate the chart: {chart_question}"
                )
                
                if "context" in chart_info:
                    question_prompt += f"\n\nChart context: {chart_info['context']}"
                
                if "area_text" in chart_info and chart_info["area_text"]:
                    question_prompt += f"\n\nText in chart area: {chart_info['area_text']}"
                
                answer = answer_question(question_prompt, None)
                st.write("**Answer:**")
                st.write(answer)

# The following placeholder visualization methods have been removed
# since we don't want to recreate any charts, even as placeholders.
# Instead, we only provide textual insights about the charts
# based on surrounding context.
