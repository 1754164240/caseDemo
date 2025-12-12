# LangChain & LangGraph 升级迁移指南

## 概述

本指南帮助您从 LangChain 0.1.x 和 LangGraph 0.1.x 迁移到最新的稳定版本。

**版本变更**:
- LangChain: `0.1.0` → `0.3.13`
- LangGraph: `0.1.0` → `0.2.62`
- OpenAI SDK: 新增 `1.59.5`

## 快速迁移（5 分钟）

### 步骤 1: 更新依赖包

```bash
cd backend
pip install -r requirements.txt --upgrade
```

### 步骤 2: 验证安装

```bash
python -c "import langchain; print(langchain.__version__)"
python -c "import langgraph; print(langgraph.__version__)"
```

预期输出:
```
0.3.13
0.2.62
```

### 步骤 3: 测试应用

```bash
python -m scripts.main
```

如果启动成功，迁移完成！✅

## 详细变更说明

### 1. ChatOpenAI 参数变更

#### 变更内容

| 旧参数名 | 新参数名 | 说明 |
|---------|---------|------|
| `openai_api_key` | `api_key` | API 密钥 |
| `openai_api_base` | `base_url` | API 基础 URL |

#### 代码对比

**❌ 旧代码**:
```python
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    model="gpt-4",
    openai_api_key="sk-xxx",
    openai_api_base="https://api.openai.com/v1",
    temperature=0.7
)
```

**✅ 新代码**:
```python
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    model="gpt-4",
    api_key="sk-xxx",
    base_url="https://api.openai.com/v1",
    temperature=0.7
)
```

#### 自动迁移脚本

如果您有多个文件需要更新，可以使用以下脚本：

```python
import re
import glob

def migrate_chatopanai(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 替换参数名
    content = re.sub(r'openai_api_key=', 'api_key=', content)
    content = re.sub(r'openai_api_base=', 'base_url=', content)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ Migrated: {file_path}")

# 迁移所有 Python 文件
for file in glob.glob("app/**/*.py", recursive=True):
    migrate_chatopanai(file)
```

### 2. OpenAIEmbeddings 参数变更

#### 代码对比

**❌ 旧代码**:
```python
from langchain_openai import OpenAIEmbeddings

embeddings = OpenAIEmbeddings(
    openai_api_key="sk-xxx",
    openai_api_base="https://api.openai.com/v1"
)
```

**✅ 新代码**:
```python
from langchain_openai import OpenAIEmbeddings

embeddings = OpenAIEmbeddings(
    api_key="sk-xxx",
    base_url="https://api.openai.com/v1"
)
```

### 3. Prompts 导入路径变更

#### 代码对比

**❌ 旧代码**:
```python
from langchain.prompts import ChatPromptTemplate
from langchain.prompts import PromptTemplate
```

**✅ 新代码**:
```python
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.prompts import PromptTemplate
```

### 4. LangGraph StateGraph 变更

#### 4.1 状态定义

**❌ 旧代码**:
```python
from typing import TypedDict, List, Dict, Any

class GraphState(TypedDict):
    requirement_text: str
    test_points: List[Dict[str, Any]]
    current_step: str
```

**✅ 新代码**:
```python
from typing import Annotated, List, Dict, Any
from typing_extensions import TypedDict
import operator

class GraphState(TypedDict):
    requirement_text: str
    test_points: Annotated[List[Dict[str, Any]], operator.add]
    current_step: str
```

**说明**:
- 使用 `Annotated` 类型支持状态字段的自动合并
- `operator.add` 表示列表字段会自动追加而非覆盖

#### 4.2 工作流入口

**❌ 旧代码**:
```python
from langgraph.graph import StateGraph, END

workflow = StateGraph(GraphState)
workflow.add_node("analyze", analyze_func)
workflow.set_entry_point("analyze")  # ❌ 已废弃
workflow.add_edge("analyze", END)
```

**✅ 新代码**:
```python
from langgraph.graph import StateGraph, END, START

workflow = StateGraph(GraphState)
workflow.add_node("analyze", analyze_func)
workflow.add_edge(START, "analyze")  # ✅ 使用 START
workflow.add_edge("analyze", END)
```

#### 4.3 节点函数返回值

**❌ 旧代码**:
```python
def analyze_requirement(state: GraphState) -> GraphState:
    """节点函数返回完整状态"""
    test_points = extract_test_points(state["requirement_text"])
    
    # 修改状态
    state["test_points"] = test_points
    state["current_step"] = "completed"
    
    # 返回完整状态
    return state
```

**✅ 新代码**:
```python
def analyze_requirement(state: GraphState) -> Dict[str, Any]:
    """节点函数只返回需要更新的字段"""
    test_points = extract_test_points(state["requirement_text"])
    
    # 只返回更新的字段
    return {
        "test_points": test_points,
        "current_step": "completed"
    }
```

**优势**:
- 更清晰的状态更新逻辑
- 避免意外修改其他状态字段
- 支持状态字段的自动合并

### 5. 完整示例对比

#### 旧版本完整代码

```python
from typing import TypedDict, List, Dict, Any
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END

class GraphState(TypedDict):
    text: str
    result: List[str]

class AIService:
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4",
            openai_api_key="sk-xxx",
            openai_api_base="https://api.openai.com/v1"
        )
    
    def create_workflow(self):
        workflow = StateGraph(GraphState)
        
        def process_node(state: GraphState) -> GraphState:
            result = ["processed"]
            state["result"] = result
            return state
        
        workflow.add_node("process", process_node)
        workflow.set_entry_point("process")
        workflow.add_edge("process", END)
        
        return workflow.compile()
```

#### 新版本完整代码

```python
from typing import Annotated, List, Dict, Any
from typing_extensions import TypedDict
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END, START
import operator

class GraphState(TypedDict):
    text: str
    result: Annotated[List[str], operator.add]

class AIService:
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4",
            api_key="sk-xxx",
            base_url="https://api.openai.com/v1"
        )
    
    def create_workflow(self):
        workflow = StateGraph(GraphState)
        
        def process_node(state: GraphState) -> Dict[str, Any]:
            result = ["processed"]
            return {"result": result}
        
        workflow.add_node("process", process_node)
        workflow.add_edge(START, "process")
        workflow.add_edge("process", END)
        
        return workflow.compile()
```

## 常见问题

### Q1: 升级后出现 `AttributeError: 'ChatOpenAI' object has no attribute 'openai_api_key'`

**原因**: 使用了旧的参数名

**解决**: 将 `openai_api_key` 改为 `api_key`，`openai_api_base` 改为 `base_url`

### Q2: 升级后出现 `TypeError: StateGraph.set_entry_point() is deprecated`

**原因**: `set_entry_point()` 方法已废弃

**解决**: 使用 `workflow.add_edge(START, "node_name")` 代替

### Q3: 状态更新不生效

**原因**: 节点函数返回了完整状态而非更新字典

**解决**: 节点函数只返回需要更新的字段字典

### Q4: 列表字段被覆盖而非追加

**原因**: 未使用 `Annotated` 类型

**解决**: 
```python
from typing import Annotated
import operator

class GraphState(TypedDict):
    items: Annotated[List[str], operator.add]  # 自动追加
```

### Q5: 导入错误 `ImportError: cannot import name 'ChatPromptTemplate' from 'langchain.prompts'`

**原因**: 导入路径已变更

**解决**: 使用 `from langchain_core.prompts import ChatPromptTemplate`

## 测试清单

升级后请测试以下功能：

- [ ] AI 服务初始化成功
- [ ] 测试点生成功能正常
- [ ] 测试用例生成功能正常
- [ ] 用户反馈重新生成功能正常
- [ ] WebSocket 通知正常
- [ ] 文档解析正常
- [ ] 向量数据库集成正常

## 回滚方案

如果升级后出现问题，可以回滚到旧版本：

```bash
cd backend
pip install langchain==0.1.0 langgraph==0.1.0 langchain-openai==0.0.2
```

然后恢复代码到升级前的版本。

## 获取帮助

- 📖 [LangChain 官方文档](https://python.langchain.com/docs/)
- 📖 [LangGraph 官方文档](https://langchain-ai.github.io/langgraph/)
- 📖 [更新日志](./CHANGELOG.md)
- 📖 [项目架构](./ARCHITECTURE.md)

## 总结

本次升级主要变更：

1. ✅ API 参数名称更新（更符合 OpenAI SDK 规范）
2. ✅ LangGraph 工作流 API 改进（更清晰的状态管理）
3. ✅ 导入路径优化（更好的模块组织）
4. ✅ 类型支持增强（更好的 IDE 提示）

升级后您将获得：
- 🚀 更好的性能
- 🛡️ 更强的类型安全
- 📚 更完善的文档
- 🐛 更少的 Bug

