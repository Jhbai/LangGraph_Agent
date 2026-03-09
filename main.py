# 一般套件
import os
import asyncio
import subprocess
from pydantic import BaseModel, Field
from typing_extensions import TypedDict
from typing import Annotated, Literal, List, Dict, Any

# LangChain + LangGraph 套件
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.types import Command, Send
from langgraph.prebuilt import create_react_agent
from langgraph_supervisor import create_supervisor
from langgraph.checkpoint.memory import MemorySaver
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, START, END, add_messages, MessagesState

# 定義輸出格式
class AgentPlan(BaseModel):
    agent_count: int = Field(..., description="Agent count")
    agent_roles: List[str] = Field(..., description="Roles of the agents")
    agent_prompts: List[str] = Field(..., description="Prompts for the agents")
    
class PlanningResult(BaseModel):
    plan: AgentPlan = Field(..., description="The plan for the agents")
    supervisor_prompt: str = Field(..., description="The prompt for the supervisor")

# 定義狀態格式
class DynamicState(TypedDict):
    messages: Annotated[list, add_messages]
    agent_plan: AgentPlan | None
    supervisor_prompt: str | None
    final_result: str | None

# 定義單一Agent的狀態格式
class AgentTaskState(TypedDict):
    role: str
    prompt: str
    task_description: str

# Tool定義
@tool
def execute_bash(command: str) -> str:
    """執行 Bash shell 指令並回傳標準輸出 (stdout) 或錯誤訊息 (stderr)。"""
    try:
        result = subprocess.run(
            command, shell=True, check=True, text=True, capture_output=True
        )
        return result.stdout if result.stdout else "指令執行成功，無輸出。"
    except subprocess.CalledProcessError as e:
        return f"指令執行失敗:\nError: {e.stderr}"

@tool
def read_file(file_path: str) -> str:
    """讀取指定檔案的內容。"""
    if not os.path.exists(file_path):
        return f"錯誤: 找不到檔案 {file_path}"
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"讀取檔案發生錯誤: {str(e)}"

@tool
def write_file(file_path: str, content: str) -> str:
    """新建或覆寫指定檔案的內容。"""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"成功將內容寫入檔案 {file_path}"
    except Exception as e:
        return f"寫入檔案發生錯誤: {str(e)}"

@tool
def append_file(file_path: str, content: str) -> str:
    """在指定檔案的末尾追加內容。"""
    try:
        with open(file_path, 'a', encoding='utf-8') as f:
            f.write(content)
        return f"成功將內容追加到檔案 {file_path}"
    except Exception as e:
        return f"追加檔案發生錯誤: {str(e)}"

agent_tools = [execute_bash, read_file, write_file, append_file]

# 定義 LLM 模型
NVIDIA_API_KEY = "XXXXXXX"
NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"
MODEL_NAME = "qwen/qwen3.5-122b-a10b"
model = ChatOpenAI(
    api_key=NVIDIA_API_KEY,
    base_url=NVIDIA_BASE_URL,
    model=MODEL_NAME,
    temperature=0.7
)

# Prompt 定義
planning_prompt = """你是一個專業的任務拆解與系統規劃專家。請分析以下任務描述，將其解構為多個可獨立執行的子任務，並為每個子任務指派一個專屬的 AI Agent。
請確保你的規劃具有高度的適用性，根據任務的專業領域自動決定最佳的分工架構。
任務描述：{task_description}
"""

def agent_planner(state: DynamicState) -> PlanningResult:
    task_description = state['messages'][-1].content
    prompt = planning_prompt.format(task_description=task_description)
    
    planning_model = model.with_structured_output(PlanningResult)
    response = planning_model.invoke([HumanMessage(content=prompt)])
    return {
        "agent_plan": response.plan,
        "supervisor_prompt": response.supervisor_prompt
    }

def dispatch_agents(state: DynamicState) -> List[Send]:
    plan = state["agent_plan"]
    task_description = state["messages"][-1].content
    
    sends = []
    for role, prompt in zip(plan.agent_roles, plan.agent_prompts):
        sends.append(Send("Executing", {
            "role": role, 
            "prompt": prompt, 
            "task_description": task_description
        }))
    return sends

def agent_executor(state: AgentTaskState) -> dict:
    agent = create_react_agent(
        model,
        tools=agent_tools,
        prompt=f"你扮演的角色是: {state['role']}\n你的職責: {state['prompt']}。當有與檔案操作相關的任務時，請務必使用工具實際產生程式碼檔案來完成任務。"
    )
    user_msg = HumanMessage(content=f"任務描述: {state['task_description']}")
    response = agent.invoke({"messages": [user_msg]})
    final_message = response["messages"][-1].content
    return {"messages": [f"【{state['role']}】的產出:\n{final_message}"]}

Graph = StateGraph(DynamicState)

Graph.add_node("Planning", agent_planner)
Graph.add_node("Executing", agent_executor)
Graph.add_edge(START, "Planning")
Graph.add_conditional_edges("Planning", dispatch_agents, ["Executing"])
Graph.add_edge("Executing", END)

app = Graph.compile()

inputs = {"messages": [HumanMessage(content="幫我在./code/這個路徑，用python的fastapi和html開發一個網頁，是可以讓使用者輸入文字，然後按下送出後，會把使用者輸入的文字顯示在網頁上。")]}
for chunk in app.stream(inputs):
    print(chunk)
