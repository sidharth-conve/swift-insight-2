from __future__ import annotations
from agents import Agent, HandoffInputData, Runner, function_tool, handoff, trace, ModelSettings
from agents.extensions import handoff_filters
from agents import Agent, Runner, gen_trace_id, trace
from agents.mcp import MCPServer, MCPServerStdio
import os
import json
import random
import asyncio
import time
from dataclasses import dataclass
from typing import Literal
import asyncio
import shutil
import asyncio
import os
import shutil
import re

from agents import Agent, Runner, gen_trace_id, trace
from agents.mcp import MCPServer, MCPServerStdio

# os.environ["OPENAI_API_KEY"] = "APIKEY"
user_question = "How many classrooms in shimla?"
output_format = r'''{table_name1: {column1: description of column1, column2: description of column2}, table_name2: and so on..]}'''
def create_system_prompt(user_question:str, tag):
    if tag == 1:
        output_format = r'''{table_name1: {column1: description of column1, column2: description of column2}, table_name2: and so on..]}'''
        intial_schema_prompt =f'''Your task is to find important tables and columns to frame sql for question: '{user_question}'
        Output format: {output_format}
        Do not return anything other than dict specified by me.
        Only return logical tables and columns required to form SQL. 
        No extra table or column should come in output
        Reason proper before selecting any table or column
        You should use only one file and do not return results that are from different files'''
        return intial_schema_prompt
    if tag == 2:
        output_format = r'''{table_name1: {column1: description of column1, column2: description of column2}, table_name2: and so on..]}'''
        clarification_schema_prompt =f'''Your task is to find important tables and columns for question: '{user_question}'
        Output format: {output_format}
        Do not return anything other than dict specified by me.
        Only return logical tables and columns required answer question
        Never return column alone, you should always return the table to which that column belongs.
        Reason proper before selecting any table or column
        You should use only one file and do not return results that are from different files'''
        return clarification_schema_prompt

system_prompt_1 = create_system_prompt(user_question, 1)
system_prompt_2 = create_system_prompt(user_question, 2)

async def mcp_file_server_run(mcp_server: MCPServer, user_question:str, system_prompt:str):
    agent = Agent(
        name="Assistant",
        instructions="Use the tools to read the filesystem and answer questions based on those files.",
        mcp_servers=[mcp_server],
    )

    # List the files it can read
    message = "Read the files and list them."
    print(f"Running: {message}")
    result = await Runner.run(starting_agent=agent, input=message)
    # output_format = r'''{table_name1: {list all the required columns in this table}, table_name2: and so on..]}'''
    # user_question = 'How many students have perfect attendance last month?'
    # user_question = input("Enter your question:  ")
    # print(output_format)

    message = system_prompt
    print(f"\n\nRunning: {message}")
    result = await Runner.run(starting_agent=agent, input=message)
    match = re.search(r"\{.*\}", str(result.final_output), re.DOTALL)

    if match:
        content_inside_braces = match.group(0)
        return content_inside_braces
    else:
        return None



async def intial_schema(user_question:str):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    samples_dir = os.path.join(current_dir, "sample_files")

    async with MCPServerStdio(
        name="Filesystem Server, via npx",
        params={
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-filesystem", samples_dir],
        },
    ) as server:
        return await mcp_file_server_run(server, user_question, system_prompt_1)


async def clarification_question_for_mcp_file_server(user_question:str):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    samples_dir = os.path.join(current_dir, "sample_files")
    print("clarification_question_for_mcp_file_server runing")

    async with MCPServerStdio(
        name="Filesystem Server, via npx",
        params={
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-filesystem", samples_dir],
        },
    ) as server:
        return await mcp_file_server_run(server, user_question, system_prompt_2)

# user_question = input("Ask your question: ")





@function_tool
def solve_doubt(doubt: str) -> str:
    """This returns tables and columns that contains information to answer your doubt"""
    print("solve doubt ->", doubt)
    result = asyncio.run(clarification_question_for_mcp_file_server(doubt))
    print("reuslt of doubt->", result)
    # pass new schema into eval func
    return result

@function_tool
def clarification_from_user_needed(doubt_to_user:str) -> str:
    """This returns clarification of your doubt from user. Use this when you have logical issue, and that did not answered using solve_doubt()"""
    # print("doubt to user->", doubt_to_user)
    # clarification = input("Give us clarification") 
    # print("clarification->", clarification)
    return doubt_to_user

eval_prompt = '''You are a SQL schema validator. Your task is to analyze if the provided schema contains all necessary tables and columns to construct a SQL query that answers the given question.
Process:
1. First, carefully analyze the question and identify what data elements would be needed to answer it.
2. Examine the provided schema to determine if it contains all required tables and columns.
3. If the schema is sufficient, respond with "PASS"
4. If the schema is insufficient, identify exactly what's missing by asking specific doubts via solve_doubt():
5. Wait for solve_doubt() to respond before asking additional doubts.
6. After each solve_doubt() response, reevaluate if you now have enough information.
7. If for a particular doubt, solve_doubt() didn't give required information, return ONLY a question to the user that asks them for the clarification on the specific topic.

Repeat this until schema is sufficient to form SQL. 
In the end return only either the SQL query, or doubts for clarification.
'''

def schema_question_answer_agent_handoff_message_filter(handoff_message_data: HandoffInputData) -> HandoffInputData:
    # First, we'll remove any tool-related messages from the message history
    handoff_message_data = handoff_filters.remove_all_tools(handoff_message_data)

    # Second, we'll also remove the first two items from the history, just for demonstration
    history = (
        tuple(handoff_message_data.input_history[2:])
        if isinstance(handoff_message_data.input_history, tuple)
        else handoff_message_data.input_history
    )

    return HandoffInputData(
        input_history=history,
        pre_handoff_items=tuple(handoff_message_data.pre_handoff_items),
        new_items=tuple(handoff_message_data.new_items),
    )

eval_agent = Agent(
    name="Schema Evaluation Agent",
    instructions=(
        eval_prompt
    ),
    tools=[solve_doubt],
    model_settings=ModelSettings(temperature=0.5),
)

async def evaluate_schema_question(user_question: str) -> str:
    """Evaluates if the schema can answer the given question and returns the result."""

    schema = await intial_schema(user_question)
    print("schema", schema)
    result = await Runner.run(
        eval_agent,
        input=f"Here is the conversation between user and agent {user_question}, and Schema: {schema}\nYou should think and check properly before saying 'pass'."
    )
    return result

# print(asyncio.run(evaluate_schema_question(user_question)).to_input_list())



# Previous reasoning steps and observations: {history}