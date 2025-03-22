import pdfplumber
import pandas as pd
import base64
import re
from io import BytesIO

def extract_text_and_elements_from_pdf(pdf_path):
    """
    Extract text, tables, and images from a PDF file
    
    Args:
        pdf_path (str): Path to the PDF file
        
    Returns:
        tuple: (text, tables, charts)
    """
    text = ""
    tables = []
    charts = []
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            # Process each page
            for page_num, page in enumerate(pdf.pages):
                # Extract text
                page_text = page.extract_text() or ""
                text += f"\n--- Page {page_num + 1} ---\n{page_text}"
                
                # Extract tables
                page_tables = page.extract_tables()
                for i, table in enumerate(page_tables):
                    if table:
                        # Generate unique column names
                        num_columns = len(table[0]) if table and table[0] else len(table[1]) if table and len(table) > 1 else 0
                        
                        # Either use first row as headers or create default headers
                        if table[0]:
                            # Make sure column names are unique by adding a suffix if necessary
                            col_names = []
                            seen = {}
                            for j, col in enumerate(table[0]):
                                col_str = str(col).strip() if col else f"Col{j}"
                                if not col_str:  # Handle empty column names
                                    col_str = f"Col{j}"
                                
                                # If the column name already exists, add a suffix
                                if col_str in seen:
                                    seen[col_str] += 1
                                    col_str = f"{col_str}_{seen[col_str]}"
                                else:
                                    seen[col_str] = 0
                                
                                col_names.append(col_str)
                            
                            # Create DataFrame with clean headers and data
                            df = pd.DataFrame(table[1:], columns=col_names)
                        else:
                            # No headers, create default column names
                            df = pd.DataFrame(table, columns=[f"Col{j}" for j in range(num_columns)])
                            
                        tables.append({
                            "page": page_num + 1,
                            "table_id": f"page{page_num+1}_table{i+1}",
                            "data": df
                        })
                
                # Try to identify images/charts
                # This is a heuristic approach since pdfplumber doesn't directly extract images
                # We look for image-like content by checking for bounded areas
                rects = page.rects
                if len(rects) > 0:
                    # Filter out small rectangles that are likely not chart containers
                    potential_chart_rects = [rect for rect in rects if 
                                           (rect['height'] > 50 and rect['width'] > 50) or 
                                           (rect['height'] > 100 or rect['width'] > 100)]
                    
                    # Create placeholders for charts
                    for i, rect in enumerate(potential_chart_rects):
                        crop_area = (rect['x0'], rect['y0'], rect['x1'], rect['y1'])
                        
                        # Extract text within this area to check if it's a chart
                        area_text = page.within_bbox(crop_area).extract_text() or ""
                        
                        # Check if area contains words suggesting it's a chart
                        chart_keywords = ['chart', 'figure', 'graph', 'plot', 'histogram', 'bar', 'pie', 'line', 'scatter']
                        is_likely_chart = any(keyword in area_text.lower() for keyword in chart_keywords)
                        
                        if is_likely_chart or len(area_text) < 100:  # If very little text, might be a chart
                            charts.append({
                                "page": page_num + 1,
                                "chart_id": f"page{page_num+1}_chart{i+1}",
                                "area": crop_area,
                                "description": f"Chart found on page {page_num+1}"
                            })
    
    except Exception as e:
        print(f"Error processing PDF: {e}")
        return f"Error processing PDF: {e}", [], []
    
    return text, tables, charts

def extract_table_as_markdown(table_data):
    """
    Convert a pandas DataFrame to markdown format
    
    Args:
        table_data (dict): Table data with DataFrame
        
    Returns:
        str: Markdown representation of the table
    """
    df = table_data["data"]
    return df.to_markdown(index=False)

def extract_text_around_chart(text, chart_info, context_chars=200):
    """
    Extract text description around chart areas based on page number
    
    Args:
        text (str): Full document text
        chart_info (dict): Chart metadata
        context_chars (int): Number of characters to include before and after
        
    Returns:
        str: Text description around the chart
    """
    page_num = chart_info["page"]
    page_marker = f"--- Page {page_num} ---"
    
    # Find the page in the text
    page_start = text.find(page_marker)
    if page_start == -1:
        return "Could not find page reference in text"
    
    next_page_marker = f"--- Page {page_num + 1} ---"
    page_end = text.find(next_page_marker)
    if page_end == -1:
        page_end = len(text)
    
    page_text = text[page_start:page_end]
    
    # Look for figure/chart references in the text
    figure_pattern = re.compile(r'(Figure|Fig\.?|Chart|Graph|Plot)s?\s*\d+', re.IGNORECASE)
    matches = figure_pattern.finditer(page_text)
    
    for match in matches:
        start = max(0, match.start() - context_chars)
        end = min(len(page_text), match.end() + context_chars)
        return page_text[start:end]
    
    # If no specific figure reference found, return a portion of the page text
    chart_id = chart_info["chart_id"]
    middle = len(page_text) // 2
    start = max(0, middle - context_chars)
    end = min(len(page_text), middle + context_chars)
    
    return f"Context for {chart_id} on page {page_num}:\n{page_text[start:end]}"
