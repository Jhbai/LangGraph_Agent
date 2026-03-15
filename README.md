# AI Agent 系統

## 簡介
本系統是一個基於 LangChain 和 LangGraph 的 AI Agent 架構，能夠將複雜任務自動分解給多個 AI Agent 並行執行。系統包含任務規劃、執行、檢查和修正的完整流程，確保任務能夠正確完成。


## 功能特色
- 自動將任務分解為多個子任務
- 多個 AI Agent 平行協作執行
- 具備訊息通訊機制解決任務依賴
- Supervisor 檢查機制確保任務品質
- 自動修正錯誤並重新執行

## 使用套件
- langchain
- langgraph
- langchain-openai
- langchain-mcp-adapters
- langchain-core
- pydantic
- asyncio
- subprocess

## 安裝方式
1. 確保已安裝 Python 3.8+
2. 安裝所需套件：
```bash
pip install langchain langchain-core langchain-community langchain-experimental
pip install langgraph langgraph-checkpoint-sqlite
pip install langchain-openai langchain-anthropic tavily-python
pip install langsmith "langserve[all]"
pip install langchain-mcp-adapters pydantic
```

## 使用方法
執行系統時需提供初始任務描述：

```bash
python dev.py -p "你的任務描述"
```

執行流程：
1. 系統會先要求你確認任務規格
2. 確認後系統會自動規劃 Agent 並分配任務
3. 多個 Agent 會平行執行各自任務
4. Supervisor 會檢查執行結果
5. 如有問題會自動進入修正迴圈

## 程式架構

### 主要元件
- `agent_planner`: 負責將任務分解為多個子任務並指派給不同 Agent
- `agent_executor`: 執行指派給各 Agent 的任務
- `checker_node`: 檢查任務執行結果
- `route_after_check`: 根據檢查結果決定是否需要修正

### 通訊機制
- `send_message`: 發送訊息給其他 Agent
- `check_messages`: 讀取發給自己的訊息
- `wait_for_reply`: 等待其他 Agent 回覆

### 檔案操作工具
- `execute_bash`: 執行 Bash 指令
- `read_file`: 讀取檔案
- `write_file`: 寫入檔案
- `append_file`: 追加內容到檔案

## 注意事項
1. 系統預設使用 NVIDIA 的 GLM-5 模型，請確保網路連線正常
2. 執行過程中可能需要手動確認任務規格
3. 系統會自動處理 Agent 間的協作與依賴關係
4. 任務執行結果會顯示在終端機上
