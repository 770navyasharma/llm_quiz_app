from langgraph.graph import StateGraph, END, START
from langchain_core.rate_limiters import InMemoryRateLimiter
from langgraph.prebuilt import ToolNode
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from tools import get_rendered_html, download_file, post_request, run_code, add_dependencies, transcribe_audio
from typing import TypedDict, Annotated, List, Any
from langgraph.graph.message import add_messages
# 👇 Switch to Groq
from langchain_groq import ChatGroq
import os
from dotenv import load_dotenv

load_dotenv()

EMAIL = os.getenv("EMAIL")
SECRET = os.getenv("SECRET")
RECURSION_LIMIT = 5000

# -------------------------------------------------
# STATE
# -------------------------------------------------
class AgentState(TypedDict):
    messages: Annotated[List, add_messages]

# Define your tools list
TOOLS = [run_code, get_rendered_html, download_file, post_request, add_dependencies, transcribe_audio]

# -------------------------------------------------
# GROQ LLM SETUP
# -------------------------------------------------
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    print("❌ CRITICAL ERROR: GROQ_API_KEY not found in environment variables!")
else:
    print(f"✅ GROQ_API_KEY found")

# Groq Free Tier often allows ~30 requests per minute.
# We set a limiter to be safe (e.g., 1 request every 2 seconds).
rate_limiter = InMemoryRateLimiter(
    requests_per_second=30/60,  # 0.5 requests per second
    check_every_n_seconds=0.1,
    max_bucket_size=1
)

# 👇 Using Llama 3.3 70B (High intelligence, currently free on Groq)
# If you hit Token Limits (TPM), switch model to "llama-3.1-8b-instant"
llm = ChatGroq(
    model="llama-3.3-70b-versatile", 
    api_key=GROQ_API_KEY,
    rate_limiter=rate_limiter,
    temperature=0
).bind_tools(TOOLS)


# -------------------------------------------------
# SYSTEM PROMPT
# -------------------------------------------------
SYSTEM_PROMPT = f"""
You are an autonomous quiz-solving agent.

Your job is to:
1. Load the quiz page from the given URL.
2. Extract ALL instructions, required parameters, submission rules, and the submit endpoint.
3. Solve the task exactly as required.
4. Submit the answer ONLY to the endpoint specified on the current page (never make up URLs).
5. Read the server response and:
   - If it contains a new quiz URL → fetch it immediately and continue.
   - If no new URL is present → return "END".
   
AUDIO TASKS:
- If you encounter an audio file (mp3, wav), you MUST:
  1. Use 'download_file' to save it.
  2. Use 'transcribe_audio' on the saved filename to get the text.
  3. Use the transcribed text as the answer (or part of the answer).

STRICT RULES — FOLLOW EXACTLY:

GENERAL RULES:
- NEVER stop early. Continue solving tasks until no new URL is provided.
- NEVER hallucinate URLs, endpoints, fields, values, or JSON structure.
- NEVER shorten or modify URLs. Always submit the full URL.
- NEVER re-submit unless the server explicitly allows or it's within the 3-minute limit.
- ALWAYS inspect the server response before deciding what to do next.
- ALWAYS use the tools provided to fetch, scrape, download, render HTML, or send requests.
- **IMPORTANT**: If the HTML content is too large, focus only on the relevant forms and instructions.

TIME LIMIT RULES:
- Each task has a hard 3-minute limit.
- The server response includes a "delay" field indicating elapsed time.
- If your answer is wrong retry again.

STOPPING CONDITION:
- Only return "END" when a server response explicitly contains NO new URL.
- DO NOT return END under any other condition.

ADDITIONAL INFORMATION YOU MUST INCLUDE WHEN REQUIRED:
- Email: {EMAIL}
- Secret: {SECRET}

YOUR JOB:
- Follow pages exactly.
- Extract data reliably.
- Never guess.
- Submit correct answers.
- Continue until no new URL.
- Then respond with: END
"""

prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    MessagesPlaceholder(variable_name="messages")
])

llm_with_prompt = prompt | llm


# -------------------------------------------------
# AGENT NODE
# -------------------------------------------------
def agent_node(state: AgentState):
    # Invoke the LLM
    result = llm_with_prompt.invoke({"messages": state["messages"]})
    return {"messages": state["messages"] + [result]}


# -------------------------------------------------
# GRAPH
# -------------------------------------------------
def route(state):
    last = state["messages"][-1]
    
    # Robust tool call check
    tool_calls = None
    if hasattr(last, "tool_calls"):
        tool_calls = getattr(last, "tool_calls", None)
    elif isinstance(last, dict):
        tool_calls = last.get("tool_calls")

    if tool_calls:
        return "tools"
    
    # Robust content check
    content = None
    if hasattr(last, "content"):
        content = getattr(last, "content", None)
    elif isinstance(last, dict):
        content = last.get("content")

    # Check for END signal
    if isinstance(content, str) and content.strip() == "END":
        return END
    if isinstance(content, list) and len(content) > 0 and isinstance(content[0], dict):
         if content[0].get("text", "").strip() == "END":
             return END
             
    return "agent"

graph = StateGraph(AgentState)

graph.add_node("agent", agent_node)
graph.add_node("tools", ToolNode(TOOLS))

graph.add_edge(START, "agent")
graph.add_edge("tools", "agent")
graph.add_conditional_edges(
    "agent",    
    route       
)

app = graph.compile()


# -------------------------------------------------
# TEST FUNCTION
# -------------------------------------------------
def run_agent(url: str) -> str:
    print(f"🚀 Starting Groq Agent for URL: {url}")
    # Initialize with user message
    initial_message = {"role": "user", "content": url}
    
    app.invoke(
        {"messages": [initial_message]},
        config={"recursion_limit": RECURSION_LIMIT},
    )
    print("✅ Tasks completed successfully")
