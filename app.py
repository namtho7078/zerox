from fastapi import FastAPI, Query
from fastapi import HTTPException

from typing import Optional, Union, List, Dict, Any
import asyncio
from pyzerox import zerox
import os
import json
from tempfile import NamedTemporaryFile
from dotenv import load_dotenv
from pydantic import BaseModel
from py_zerox.pyzerox.models import litellmmodel, types
import litellm
import json
### Model Setup (Use only Vision Models) Refer: https://docs.litellm.ai/docs/providers ###

## placeholder for additional model kwargs which might be required for some models
kwargs = {}
model = "gpt-4o" ## openai model

custom_system_prompt = """Convert the below PDF page into a JSON Object with the following properties :\n 
text : a list of dictionary of all content of all the paragraphs in the page. Do not include the components present in tables, graphs or financial statements in this section. We only want the paragraphs. Do not include superscripts or footnotes / headers. results should be in the following format : {section : The title of the section where the paragraph is present (if any otherwise "") , paragraph: The text content of each paragraph }
tables : This is a list of dictionaries. It should have all the tabular data present in the PDF in the following format: {Header: the header of the table, Body : The table's body}, 
graphs: This is a list of dictionaries. It should have a tabular representation of the graphs in the PDF page to the best of your availability in the following format: {Header: the header of the table, Body : The table's body},  
financial statements: This is a list of dictionaries. If any financial table or graph is present, they should be present in this property. It should have all the financial data present in the PDF in the following format: {Header: the header of the table, Body : The table's body}. In this content, financial data is anything sales, EBITDA,cost, debt. Anything that has to do with cash coming in or out.
FIBO entities : a list of dictionary in the following format {Entity: The entity present , Timestamp: The timestamp of the entity (if present) otherwise n.a., Value: The value of the entity } of FIBO Entites as per the ontology present in the page including a time stamp if present. The entities extracted should match the standard ontology terms 
Images: images must be replaced with [Description of image].\n
Summary: A detailed text summary of what is covered in the tables and the financial statements if any. We care mostly about the words here no need to mention any value apart from rate, dates and movements. If this is a continuation of another table, graph or statement provided in the context, mention briefly what were the previous ones about \n
All information should be  comma separated in a markdown format. \n 

    RULES:\n
    - If a table, graph or financial statements have no spefic headers, assume the header from the context provided carries over\n
    - Return only the JSON with no explanation text. Do not include deliminators like ```markdown.\n
    - Don't forget to extract Graphs, Financials and FIBO Entities. Don't forget to include a summary.\n
    - If the page is a table of content or a glossary of terms or a disclaimer or confidentiality or contact information/Title page (or usual end of document or beginning of pages that contain no useful information), return "".
    - You must include all information on the page. Do not exclude headers, footers, or subtext.\n""".strip() ## example

app = FastAPI()
openai_api_key = os.getenv("OPENAI_API_KEY")


# Define the async processing function
class QueryRequest(BaseModel):
    prompt: str
@app.post("/analyze_query/")
async def analyze_query(request: QueryRequest):
    messages: List[Dict[str, Any]] = [
        {
            "role": "system",
            "content": request.prompt,
        },
    ]

    # Call the LLM asynchronously
    llm = litellmmodel(model=model)
    try:
        response = await litellm.acompletion(model=llm.model, messages=messages)
        
        # Extract content from the response
        print(response)
        comp_response = types.CompletionResponse(
            content=response["choices"][0]["message"]["content"],
            input_tokens=response["usage"]["prompt_tokens"],
            output_tokens=response["usage"]["completion_tokens"],
        )
        print(comp_response)

        # Directly create the response dictionary
        response_data = json.loads(comp_response.content)
        print(response_data)
        return response_data

    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Failed to parse JSON response from LLM")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")


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
    if select_pages:
        maintain = False
    else:
        maintain = True
    print(select_pages)
    result = await zerox(
        file_path=file_path,
        model=model,
        output_dir=output_dir,
         maintain_format= maintain, 
        custom_system_prompt=custom_system_prompt,
        select_pages=select_pages,
        **kwargs
    )
    return result

# Create a FastAPI route for the process_file function
@app.get("/process-file")
async def process_file_endpoint(
    file_path: str = Query(..., description="Path to the PDF file"),
    select_pages : Optional[List[int]] = Query(None, description="List of page numbers to process")
):
    """
    FastAPI endpoint to process a PDF file and return markdown content.
    """
    result = await process_file(
        file_path=file_path,
        model=model,
        output_dir="Dummy",
        custom_system_prompt=custom_system_prompt,
        select_pages=select_pages,
    )
    print(result)
    return {"result": result}