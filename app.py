from fastapi import FastAPI, Query
from typing import Optional, Union, List
import asyncio
from pyzerox import zerox
import os
import json
from tempfile import NamedTemporaryFile
from dotenv import load_dotenv
### Model Setup (Use only Vision Models) Refer: https://docs.litellm.ai/docs/providers ###

## placeholder for additional model kwargs which might be required for some models
kwargs = {}
model = "gpt-4o" ## openai model

custom_system_prompt = """Convert the below PDF page into a JSON Object with the following properties :\n 
text : The text content of the page. Do not include the components present in tables, graphs or financial statements in this section. We only want the paragraph 
tables : This is a list of dictionaries. It should have all the tabular data present in the PDF in the following format: {Header: the header of the table, Body : The table's body}, 
graphs: This is a list of dictionaries. It should have a tabular representation of the graphs in the PDF page to the best of your availability in the following format: {Header: the header of the table, Body : The table's body},  
financial statements: This is a list of dictionaries. If any financial table or graph is present, they should be present in this property. It should have all the financial data present in the PDF in the following format: {Header: the header of the table, Body : The table's body}. In this content, financial data is anything sales, EBITDA,cost, debt. Anything that has to do with cash coming in or out.
FIBO entities : a list of dictionary in the following format {Entity: The entity present , Timestamp: The timestamp of the entity (if present) otherwise n.a., Value: The value of the entity } of FIBO Entites as per the ontology present in the page including a time stamp if present. The entities extracted should match the standard ontology terms 
Images: images must be replaced with [Description of image].\n
All information should be  comma separated in a markdown format. \n 

    RULES:\n
    - Return only the JSON with no explanation text. Do not include deliminators like ```markdown.\n
    - Don't forget to extract Graphs, Financials and FIBO Entities\n
    - If the page is a table of content or a glossary of terms or a disclaimer or confidentiality or contact information/Title page (or usual end of document or beginning of pages that contain no useful information), return "".
    - You must include all information on the page. Do not exclude headers, footers, or subtext.\n""".strip() ## example

app = FastAPI()
openai_api_key = os.getenv("OPENAI_API_KEY")
# Define the async processing function
async def process_file(file_path: str, model, output_dir, custom_system_prompt = None, select_pages = None, **kwargs):
    """
    Processes the given PDF file, converting it to markdown and saving the output.
    
    Args:
        file_path (str): Path to the PDF file.
        model: Model to use for processing.
        output_dir (str): Directory to save the consolidated markdown file.
        custom_system_prompt (str, optional): Custom prompt for zerox.
        select_pages (int or list of int, optional): Pages to process (1-indexed). None for all pages.
        **kwargs: Additional arguments for zerox function.
        
    Returns:
        result: The processed result from zerox.
    """
    # Call the zerox function with provided parameters
    result = await zerox(
        file_path=file_path,
        model=model,
        output_dir=output_dir,
        custom_system_prompt=custom_system_prompt,
        select_pages=select_pages,
        **kwargs
    )
    return result

# Create a FastAPI route for the process_file function
@app.get("/process-file")
async def process_file_endpoint(
    file_path: str = Query(..., description="Path to the PDF file"),
):
    """
    FastAPI endpoint to process a PDF file and return markdown content.
    """
    result = await process_file(
        file_path=file_path,
        model=model,
        output_dir="Dummy",
        custom_system_prompt=custom_system_prompt,
        select_pages=None,
    )
    return {"result": result}