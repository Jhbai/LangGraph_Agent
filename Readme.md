# 套件安裝
pip install langchain langchain-core langchain-community langchain-experimental
pip install langgraph langgraph-checkpoint-sqlite
pip install langchain-openai langchain-anthropic tavily-python
pip install langsmith "langserve[all]"

# 啟動追蹤
- LANGCHAIN_TRACING_V2="true" (啟動遙測引擎)
- LANGCHAIN_API_KEY="你的密鑰" (授權寫入 LangSmith)
- LANGCHAIN_PROJECT="專案名稱" (將 Trace 記錄歸類至指定專案)
例如: 
  - export LANGCHAIN_TRACING_V2="true"
  - export LANGCHAIN_API_KEY="你的_LangSmith_API_Key"
  - export LANGCHAIN_PROJECT="FastAPI-Multi-Agent"
  - python your_script.py
