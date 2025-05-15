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
import re

os.environ["OPENAI_API_KEY"] = "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"


user_question = 'How many teachers were on maternity leave last week?'
output_format = r'''{table_name1: [list all the required columns in this table], table_name2: and so on..]}'''
intial_schema_prompt =f'''Your task is to find important tables and columns to frame sql for question: '{user_question}'
Output format: {output_format}
Do not return anything other than dict specified by me.
Only return logical tables and columns required to form SQL. 
No extra table or column should come in output
Reason proper before selecting any table or column'''

@function_tool
def solve_doubt(doubt: str) -> str:
    """This returns tables and columns as per your doubt"""
    print("solve doubt ->", doubt)
    doubt_solve_prompt = f'''Your task is to find important tables and columns that contains information to answer question: '{doubt}'
    Output format: {output_format}
    Do not return anything other than dict specified by me.
    Only return logical tables and columns required to form SQL. 
    No extra table or column should come in output
    Reason proper before selecting any table or column
    '''
    result = asyncio.run(intial_schema(doubt, doubt_solve_prompt))
    print("reuslt of doubt->", result)
    result = asyncio.run(evaluate_schema_question(user_question, schema))
    list_str = str(result)
    if 'pass' not in list_str:

    # pass new schema into eval func
    return result

@function_tool
def clarification_from_user_needed(doubt_to_user:str) -> str:
    """This function asks doubt to user and then user gives clarification of that doubt"""
    print("doubt to user->", doubt_to_user)
    clarification = input("Give us clarification")
    print("clarification->", clarification)
    return clarification

async def run(mcp_server: MCPServer, user_question:str, intial_schema_prompt:str) -> str:
    agent = Agent(
        name="Assistant",
        instructions="Use the tools to read the filesystem and answer questions based on those files.",
        mcp_servers=[mcp_server],
    )

    # List the files it can read
    message = "Read the files and list them."
    print(f"Running: {message}")
    result = await Runner.run(starting_agent=agent, input=message)
    # user_question = 'How many students have perfect attendance last month?'
    # user_question = input("Enter your question:  ")
    # print(output_format)

    message = intial_schema_prompt
    print(f"\n\nRunning: {message}")
    result = await Runner.run(starting_agent=agent, input=message)
    match = re.search(r"\{.*\}", str(result.final_output), re.DOTALL)

    if match:
        content_inside_braces = match.group(0)  
        return content_inside_braces
    else:
        return None


async def intial_schema(user_question:str, prompt:str):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    samples_dir = os.path.join(current_dir, "sample_files")

    async with MCPServerStdio(
        name="Filesystem Server, via npx",
        params={
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-filesystem", samples_dir],
        },
    ) as server:
        return await run(server, user_question, prompt)

eval_prompt = '''You are a SQL schema validator. Your task is to analyze if the provided schema contains all necessary tables and columns to construct a SQL query that answers the given question.
Process:
1. First, carefully analyze the question and identify what data elements would be needed to answer it.
2. Examine the provided schema to determine if it contains all required tables and columns.
3. If the schema is sufficient, respond with "PASS"
4. If the schema is insufficient, identify exactly what's missing by asking specific doubts via solve_doubt():
5. Wait for solve_doubt() to respond before asking additional doubts.
6. After each solve_doubt() response, reevaluate if you now have enough information.
7. If for a particular doubt, solve_doubt() didn't give required information then only use clarification_from_user_needed() and this will return clarification of your doubt from user. 
8. After each clarification_from_user_needed() response, reevaluate if you now have enough information.
9. Only move to the next doubt when the current one is fully resolved.
Remember: Focus only on schema completeness, not on available data or related database. Your goal is to determine if constructing a syntactically correct and logically sound SQL query is possible with the given schema.
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
    tools=[solve_doubt, clarification_from_user_needed],
    model_settings=ModelSettings(temperature=0.5),
)

doubt_solver_agent = Agent(
    name="Doubt Solver Agent",
    instructions=(
        eval_prompt
    ),
    tools=[solve_doubt, clarification_from_user_needed],
    model_settings=ModelSettings(temperature=0.5),
)

async def evaluate_schema_question(user_question: str, schema: str) -> str:
    """Evaluates if the schema can answer the given question and returns the result."""
    result = await Runner.run(
        eval_agent,
        input=f"Question: {user_question} and Schema: {schema}\nYou should think and check properly before saying 'pass'."
    )
    return result

def func1(user_question):
    schema = asyncio.run(intial_schema(user_question, intial_schema_prompt))
    print("-"* 50)
    print("intial schema->", schema)
    result = asyncio.run(evaluate_schema_question(user_question, schema))
    print("-"* 50)
    print("result->", result)
    return result

print(func1(user_question).to_input_list())