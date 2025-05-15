from langchain import hub
from langchain.agents import AgentExecutor, create_react_agent
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_openai import OpenAI
from mcp_file_server import clarification_question_for_mcp_file_server
user_question = "What is 2 *3?"
tools = [clarification_question_for_mcp_file_server(user_question)]
# Get the prompt to use - you can modify this!
prompt = hub.pull("hwchase17/react")

# Choose the LLM to use
llm = OpenAI()

# Construct the ReAct agent
agent = create_react_agent(llm, tools, prompt)
# Create an agent executor by passing in the agent and tools
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
agent_executor.invoke({"input": f"{user_question}"})