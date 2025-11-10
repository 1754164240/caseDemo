"""
RAG (Retrieval-Augmented Generation) 服务
使用 LangChain 和 Milvus 实现知识库问答
支持 Short-term Memory (对话历史)
"""
from typing import List, Dict, Any, Optional, Tuple
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langchain_milvus import Milvus
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.core.config import settings
from sqlalchemy.orm import Session
import os


class RAGService:
    """RAG 知识库问答服务"""

    def __init__(self, db: Session = None):
        """初始化 RAG 服务"""
        self.db = db

        # 从数据库读取配置
        api_key = settings.OPENAI_API_KEY
        api_base = settings.OPENAI_API_BASE
        model_name = settings.MODEL_NAME
        embedding_model = settings.EMBEDDING_MODEL
        embedding_api_key = settings.EMBEDDING_API_KEY
        embedding_api_base = settings.EMBEDDING_API_BASE

        if db:
            from app.models.system_config import SystemConfig
            configs = db.query(SystemConfig).filter(
                SystemConfig.config_key.in_([
                    'OPENAI_API_KEY', 'OPENAI_API_BASE', 'MODEL_NAME',
                    'EMBEDDING_MODEL', 'EMBEDDING_API_KEY', 'EMBEDDING_API_BASE'
                ])
            ).all()

            config_dict = {c.config_key: c.config_value for c in configs}
            api_key = config_dict.get('OPENAI_API_KEY', api_key)
            api_base = config_dict.get('OPENAI_API_BASE', api_base)
            model_name = config_dict.get('MODEL_NAME', model_name)
            embedding_model = config_dict.get('EMBEDDING_MODEL', embedding_model)
            embedding_api_key = config_dict.get('EMBEDDING_API_KEY', embedding_api_key)
            embedding_api_base = config_dict.get('EMBEDDING_API_BASE', embedding_api_base)

        # 如果 Embedding 配置为空,使用 LLM 的配置
        if not embedding_api_key:
            embedding_api_key = api_key
        if not embedding_api_base:
            embedding_api_base = api_base

        print(f"[INFO] RAG 服务配置:")
        print(f"  LLM API Base: {api_base}")
        print(f"  LLM Model: {model_name}")
        print(f"  Embedding API Base: {embedding_api_base}")
        print(f"  Embedding Model: {embedding_model}")

        # 初始化 LLM
        self.llm = ChatOpenAI(
            model=model_name,
            api_key=api_key,
            base_url=api_base if api_base else None,
            temperature=0.3  # 降低温度以获得更准确的答案
        )

        # 初始化 Embeddings
        self.embeddings = OpenAIEmbeddings(
            model=embedding_model,
            api_key=embedding_api_key,
            base_url=embedding_api_base if embedding_api_base else None
        )

        # 初始化文本分割器
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,  # 每个文本块的大小
            chunk_overlap=200,  # 文本块之间的重叠
            length_function=len,
            separators=["\n\n", "\n", "。", "！", "？", ".", "!", "?", " ", ""]
        )

        self.vector_store = None
        
    def _get_vector_store(self, collection_name: str = "knowledge_base") -> Milvus:
        """获取或创建向量存储"""
        try:
            # 连接到 Milvus
            connection_args = {
                "uri": settings.MILVUS_URI,
            }
            
            # 如果有认证信息，添加到连接参数
            if settings.MILVUS_TOKEN:
                connection_args["token"] = settings.MILVUS_TOKEN
            elif settings.MILVUS_USER and settings.MILVUS_PASSWORD:
                connection_args["user"] = settings.MILVUS_USER
                connection_args["password"] = settings.MILVUS_PASSWORD
            
            # 创建或连接到向量存储
            vector_store = Milvus(
                embedding_function=self.embeddings,
                collection_name=collection_name,
                connection_args=connection_args,
                auto_id=True,
            )
            
            return vector_store
            
        except Exception as e:
            print(f"[ERROR] 连接 Milvus 失败: {str(e)}")
            raise
    
    def add_documents(
        self, 
        documents: List[str], 
        metadatas: Optional[List[Dict[str, Any]]] = None,
        collection_name: str = "knowledge_base"
    ) -> Dict[str, Any]:
        """
        添加文档到知识库
        
        Args:
            documents: 文档文本列表
            metadatas: 文档元数据列表
            collection_name: 集合名称
            
        Returns:
            添加结果
        """
        try:
            print(f"[INFO] 开始处理 {len(documents)} 个文档...")
            
            # 分割文档
            all_splits = []
            all_metadatas = []
            
            for i, doc_text in enumerate(documents):
                # 分割文本
                splits = self.text_splitter.split_text(doc_text)
                all_splits.extend(splits)
                
                # 为每个分块添加元数据
                metadata = metadatas[i] if metadatas and i < len(metadatas) else {}
                for j, split in enumerate(splits):
                    chunk_metadata = metadata.copy()
                    chunk_metadata["chunk_index"] = j
                    chunk_metadata["total_chunks"] = len(splits)
                    all_metadatas.append(chunk_metadata)
            
            print(f"[INFO] 文档分割完成，共 {len(all_splits)} 个文本块")
            
            # 获取向量存储
            vector_store = self._get_vector_store(collection_name)
            
            # 添加文档到向量存储
            vector_store.add_texts(
                texts=all_splits,
                metadatas=all_metadatas
            )
            
            print(f"[INFO] 成功添加 {len(all_splits)} 个文本块到知识库")
            
            return {
                "success": True,
                "total_documents": len(documents),
                "total_chunks": len(all_splits),
                "collection_name": collection_name
            }
            
        except Exception as e:
            print(f"[ERROR] 添加文档失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e)
            }
    
    def _parse_chat_history(self, chat_history: Optional[List[Dict[str, str]]]) -> List[BaseMessage]:
        """
        解析对话历史为 LangChain 消息格式

        Args:
            chat_history: 对话历史 [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]

        Returns:
            LangChain 消息列表
        """
        if not chat_history:
            return []

        messages = []
        for msg in chat_history:
            role = msg.get("role", "")
            content = msg.get("content", "")

            if role == "user":
                messages.append(HumanMessage(content=content))
            elif role == "assistant":
                messages.append(AIMessage(content=content))

        return messages

    def query(
        self,
        question: str,
        collection_name: str = "knowledge_base",
        top_k: int = 5,
        return_source: bool = True,
        stream: bool = False,
        chat_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        查询知识库 (支持对话历史)

        Args:
            question: 用户问题
            collection_name: 集合名称
            top_k: 返回最相关的文档数量
            return_source: 是否返回来源文档
            stream: 是否使用流式输出
            chat_history: 对话历史 [{"role": "user", "content": "..."}, ...]

        Returns:
            查询结果或生成器
        """
        try:
            print(f"[INFO] 查询问题: {question}")

            # 解析对话历史
            history_messages = self._parse_chat_history(chat_history)
            if history_messages:
                print(f"[INFO] 对话历史: {len(history_messages)} 条消息")

            # 获取向量存储
            vector_store = self._get_vector_store(collection_name)

            # 创建检索器
            retriever = vector_store.as_retriever(
                search_kwargs={"k": top_k}
            )

            # 创建 QA 链 (支持对话历史)
            if history_messages:
                # 有对话历史,使用包含历史的 prompt
                qa_prompt = ChatPromptTemplate.from_messages([
                    ("system", """你是一个专业的保险行业知识助手。请根据以下上下文信息和对话历史回答用户的问题。

上下文信息:
{context}

回答要求:
1. 基于上下文信息和对话历史提供准确、专业的回答
2. 如果用户的问题涉及之前的对话内容,请结合对话历史理解问题
3. 如果上下文中没有相关信息,请明确说明"根据现有知识库,我无法回答这个问题"
4. 回答要简洁明了,重点突出
5. 如果涉及专业术语,请适当解释
6. 可以引用上下文中的具体内容来支持你的回答"""),
                    MessagesPlaceholder(variable_name="chat_history"),
                    ("human", "{question}"),
                ])
            else:
                # 无对话历史,使用简单 prompt
                qa_prompt = ChatPromptTemplate.from_messages([
                    ("system", """你是一个专业的保险行业知识助手。请根据以下上下文信息回答用户的问题。

上下文信息:
{context}

回答要求:
1. 基于上下文信息提供准确、专业的回答
2. 如果上下文中没有相关信息,请明确说明"根据现有知识库,我无法回答这个问题"
3. 回答要简洁明了,重点突出
4. 如果涉及专业术语,请适当解释
5. 可以引用上下文中的具体内容来支持你的回答"""),
                    ("human", "{question}"),
                ])

            # 获取相关文档 (使用新的 invoke 方法)
            relevant_docs = retriever.invoke(question)

            print(f"[INFO] 找到 {len(relevant_docs)} 个相关文档")

            if not relevant_docs:
                # 如果是流式输出,返回流式生成器
                if stream:
                    return self._stream_no_docs_response(question, history_messages)
                # 非流式输出,直接调用 LLM 对话
                else:
                    print(f"[INFO] 没有找到相关文档,直接使用 LLM 对话(非流式)")

                    # 创建对话提示词 (支持对话历史)
                    if history_messages:
                        chat_prompt = ChatPromptTemplate.from_messages([
                            ("system", """你是一个专业的保险行业知识助手。

虽然当前知识库中没有找到与用户问题直接相关的文档,但你可以基于你的通用知识和对话历史来回答问题。

回答要求:
1. 提供准确、专业的回答
2. 如果用户的问题涉及之前的对话内容,请结合对话历史理解问题
3. 如果问题超出你的知识范围,请诚实说明
4. 回答要简洁明了,重点突出
5. 如果涉及专业术语,请适当解释
6. 可以建议用户上传相关文档以获得更准确的答案"""),
                            MessagesPlaceholder(variable_name="chat_history"),
                            ("human", "{question}"),
                        ])
                        messages = chat_prompt.format_messages(
                            chat_history=history_messages,
                            question=question
                        )
                    else:
                        chat_prompt = ChatPromptTemplate.from_messages([
                            ("system", """你是一个专业的保险行业知识助手。

虽然当前知识库中没有找到与用户问题直接相关的文档,但你可以基于你的通用知识来回答问题。

回答要求:
1. 提供准确、专业的回答
2. 如果问题超出你的知识范围,请诚实说明
3. 回答要简洁明了,重点突出
4. 如果涉及专业术语,请适当解释
5. 可以建议用户上传相关文档以获得更准确的答案"""),
                            ("human", "{question}"),
                        ])
                        messages = chat_prompt.format_messages(question=question)

                    # 调用 LLM
                    response = self.llm.invoke(messages)
                    answer = response.content

                    return {
                        "success": True,
                        "answer": answer,
                        "sources": [],
                        "question": question
                    }

            # 构建上下文
            context = "\n\n".join([
                f"文档片段 {i+1}:\n{doc.page_content}"
                for i, doc in enumerate(relevant_docs)
            ])

            # 生成回答 (支持对话历史)
            if history_messages:
                messages = qa_prompt.format_messages(
                    context=context,
                    chat_history=history_messages,
                    question=question
                )
            else:
                messages = qa_prompt.format_messages(
                    context=context,
                    question=question
                )

            # 如果使用流式输出
            if stream:
                return self._stream_response(messages, relevant_docs, question, return_source)

            # 非流式输出
            response = self.llm.invoke(messages)
            answer = response.content

            # 准备返回结果
            result = {
                "success": True,
                "answer": answer,
                "question": question
            }
            
            # 如果需要返回来源文档
            if return_source:
                sources = []
                for i, doc in enumerate(relevant_docs):
                    source = {
                        "index": i + 1,
                        "content": doc.page_content,
                        "metadata": doc.metadata
                    }
                    sources.append(source)
                result["sources"] = sources
            
            print(f"[INFO] 查询成功，返回答案长度: {len(answer)}")
            
            return result
            
        except Exception as e:
            print(f"[ERROR] 查询失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e),
                "question": question
            }

    def _stream_no_docs_response(self, question, history_messages: Optional[List[BaseMessage]] = None):
        """
        当没有找到相关文档时的流式响应
        直接调用 LLM 进行对话(不依赖知识库,支持对话历史)

        Args:
            question: 用户问题
            history_messages: 对话历史消息

        Yields:
            流式响应数据
        """
        import json

        print(f"[INFO] 没有找到相关文档,直接使用 LLM 对话")

        # 创建对话提示词 (支持对话历史)
        from langchain_core.prompts import ChatPromptTemplate

        if history_messages:
            chat_prompt = ChatPromptTemplate.from_messages([
                ("system", """你是一个专业的保险行业知识助手。

虽然当前知识库中没有找到与用户问题直接相关的文档,但你可以基于你的通用知识和对话历史来回答问题。

回答要求:
1. 提供准确、专业的回答
2. 如果用户的问题涉及之前的对话内容,请结合对话历史理解问题
3. 如果问题超出你的知识范围,请诚实说明
4. 回答要简洁明了,重点突出
5. 如果涉及专业术语,请适当解释
6. 可以建议用户上传相关文档以获得更准确的答案"""),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{question}"),
            ])
            messages = chat_prompt.format_messages(
                chat_history=history_messages,
                question=question
            )
        else:
            chat_prompt = ChatPromptTemplate.from_messages([
                ("system", """你是一个专业的保险行业知识助手。

虽然当前知识库中没有找到与用户问题直接相关的文档,但你可以基于你的通用知识来回答问题。

回答要求:
1. 提供准确、专业的回答
2. 如果问题超出你的知识范围,请诚实说明
3. 回答要简洁明了,重点突出
4. 如果涉及专业术语,请适当解释
5. 可以建议用户上传相关文档以获得更准确的答案"""),
                ("human", "{question}"),
            ])
            messages = chat_prompt.format_messages(question=question)

        # 流式生成回答
        full_answer = ""
        token_count = 0

        try:
            print(f"[DEBUG] 开始调用 LLM 流式生成(无知识库模式)")

            for chunk in self.llm.stream(messages):
                if chunk.content:
                    token_count += 1
                    full_answer += chunk.content
                    # 发送文本块
                    if token_count <= 5:  # 只打印前5个token
                        print(f"[DEBUG] Token {token_count}: {repr(chunk.content)}")
                    yield f"data: {json.dumps({'type': 'token', 'content': chunk.content}, ensure_ascii=False)}\n\n"

            print(f"[DEBUG] LLM 流式生成完成,总共 {token_count} 个 token")
            print(f"[DEBUG] 完整答案长度: {len(full_answer)} 字符")

        except Exception as e:
            print(f"[ERROR] LLM 流式生成失败: {str(e)}")
            import traceback
            traceback.print_exc()
            # 发送错误信息
            error_msg = "抱歉,生成回答时出现错误。请稍后重试。"
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)}, ensure_ascii=False)}\n\n"
            full_answer = error_msg

        # 发送完成信号
        print(f"[DEBUG] 发送完成信号")
        yield f"data: {json.dumps({'type': 'done', 'answer': full_answer}, ensure_ascii=False)}\n\n"

    def _stream_response(self, messages, relevant_docs, question, return_source):
        """
        流式响应生成器

        Args:
            messages: 格式化的消息
            relevant_docs: 相关文档
            question: 用户问题
            return_source: 是否返回来源

        Yields:
            流式响应数据
        """
        import json

        print(f"[DEBUG] 开始流式响应生成")
        print(f"[DEBUG] 相关文档数量: {len(relevant_docs)}")
        print(f"[DEBUG] 是否返回来源: {return_source}")

        # 首先发送来源信息
        if return_source and relevant_docs:
            sources = []
            for i, doc in enumerate(relevant_docs):
                source = {
                    "index": i + 1,
                    "content": doc.page_content,
                    "metadata": doc.metadata
                }
                sources.append(source)

            # 发送来源数据
            print(f"[DEBUG] 发送来源信息: {len(sources)} 个来源")
            yield f"data: {json.dumps({'type': 'sources', 'sources': sources}, ensure_ascii=False)}\n\n"

        # 流式生成回答
        print(f"[DEBUG] 开始调用 LLM 流式生成")
        full_answer = ""
        token_count = 0

        try:
            for chunk in self.llm.stream(messages):
                if chunk.content:
                    token_count += 1
                    full_answer += chunk.content
                    # 发送文本块
                    if token_count <= 5:  # 只打印前5个token
                        print(f"[DEBUG] Token {token_count}: {repr(chunk.content)}")
                    yield f"data: {json.dumps({'type': 'token', 'content': chunk.content}, ensure_ascii=False)}\n\n"

            print(f"[DEBUG] LLM 流式生成完成,总共 {token_count} 个 token")
            print(f"[DEBUG] 完整答案长度: {len(full_answer)} 字符")
        except Exception as e:
            print(f"[ERROR] LLM 流式生成失败: {str(e)}")
            import traceback
            traceback.print_exc()
            # 发送错误信息
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)}, ensure_ascii=False)}\n\n"
            return

        # 发送完成信号
        print(f"[DEBUG] 发送完成信号")
        yield f"data: {json.dumps({'type': 'done', 'answer': full_answer}, ensure_ascii=False)}\n\n"

    def search_similar(
        self, 
        query: str, 
        collection_name: str = "knowledge_base",
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        搜索相似文档
        
        Args:
            query: 查询文本
            collection_name: 集合名称
            top_k: 返回最相关的文档数量
            
        Returns:
            相似文档列表
        """
        try:
            print(f"[INFO] 搜索相似文档: {query}")
            
            # 获取向量存储
            vector_store = self._get_vector_store(collection_name)
            
            # 搜索相似文档
            results = vector_store.similarity_search_with_score(
                query=query,
                k=top_k
            )
            
            # 格式化结果
            similar_docs = []
            for doc, score in results:
                similar_docs.append({
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "score": float(score)
                })
            
            print(f"[INFO] 找到 {len(similar_docs)} 个相似文档")
            
            return similar_docs
            
        except Exception as e:
            print(f"[ERROR] 搜索失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return []
    
    def delete_collection(self, collection_name: str = "knowledge_base") -> bool:
        """
        删除知识库集合
        
        Args:
            collection_name: 集合名称
            
        Returns:
            是否成功
        """
        try:
            from pymilvus import connections, utility
            
            # 连接到 Milvus
            connections.connect(
                alias="default",
                uri=settings.MILVUS_URI,
                token=settings.MILVUS_TOKEN if settings.MILVUS_TOKEN else None
            )
            
            # 删除集合
            if utility.has_collection(collection_name):
                utility.drop_collection(collection_name)
                print(f"[INFO] 成功删除集合: {collection_name}")
                return True
            else:
                print(f"[WARNING] 集合不存在: {collection_name}")
                return False
                
        except Exception as e:
            print(f"[ERROR] 删除集合失败: {str(e)}")
            return False

