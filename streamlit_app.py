import asyncio
import streamlit as st
from mcp_agent.agents.agent import Agent
from mcp_agent.app import MCPApp
from mcp_agent.workflows.llm.augmented_llm_openai import OpenAIAugmentedLLM
from mcp_agent.workflows.llm.augmented_llm import RequestParams
from dataclasses import dataclass
from typing import Optional, Type, TypeVar
import logging
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('mcp-agent.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('mcp-agent')

@dataclass
class AgentState:
    """代理状态容器"""
    agent: Agent
    llm: Optional[OpenAIAugmentedLLM] = None

async def get_agent_state(
    key: str,
    agent_class: Type[Agent],
    llm_class: Optional[Type[OpenAIAugmentedLLM]] = None,
    **agent_kwargs,
) -> AgentState:
    """
    获取或创建代理状态，如果从会话中检索则重新初始化连接
    """
    if key not in st.session_state:
        # 创建新代理
        agent = agent_class(
            connection_persistence=False,
            **agent_kwargs,
        )
        await agent.initialize()
        
        # 如果指定了则附加 LLM
        llm = None
        if llm_class:
            llm = await agent.attach_llm(llm_class)
        
        state: AgentState = AgentState(agent=agent, llm=llm)
        st.session_state[key] = state
    else:
        state = st.session_state[key]
    
    return state

async def process_message(state: AgentState, user_message: str, history: list) -> str:
    """处理用户消息并获取回复"""
    try:
        logger.info(f"Processing message: {user_message}")
        
        # 使用 LLM 生成回复
        response = await state.llm.generate_str(
            message=user_message,
            request_params=RequestParams(
                use_history=True,
                history=history,
            )
        )
        return response
        
    except Exception as e:
        error_msg = f"发生错误: {str(e)}"
        logger.error(error_msg)
        return f"抱歉，我遇到了一些问题。请稍后再试。错误信息：{str(e)}"

async def main():
    st.title("高德地图智能助手")
    
    # 初始化消息历史
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "你好！我是高德地图智能助手，我可以帮你：\n1. 查询地点信息\n2. 获取天气信息\n3. 规划出行路线\n4. 测量距离\n5. 搜索周边设施\n\n请问有什么可以帮你的吗？"}
        ]
    
    # 获取或初始化代理状态
    state = await get_agent_state(
        key="amap_agent",
        agent_class=Agent,
        llm_class=OpenAIAugmentedLLM,
        name="amap-agent",
        instruction="""你是一个智能助手，可以使用高德地图的各种服务。
        你可以帮助用户：
        1. 查询地点信息
        2. 获取天气信息
        3. 规划出行路线
        4. 测量距离
        5. 搜索周边设施
        请根据用户的需求，选择合适的工具来完成任务。""",
        server_names=["amap-maps"],
    )
    
    # 显示聊天历史
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # 用户输入
    if prompt := st.chat_input("你想了解什么？"):
        # 添加用户消息到历史
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # 显示助手回复
        with st.chat_message("assistant"):
            with st.spinner("思考中..."):
                # 获取对话历史（跳过初始问候语）
                conversation_history = st.session_state.messages[1:]
                
                # 处理消息并显示输出
                response = await process_message(state, prompt, conversation_history)
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
    
    # 添加清除聊天历史按钮
    if st.button("清除聊天历史"):
        st.session_state.messages = [
            {"role": "assistant", "content": "你好！我是高德地图智能助手，我可以帮你：\n1. 查询地点信息\n2. 获取天气信息\n3. 规划出行路线\n4. 测量距离\n5. 搜索周边设施\n\n请问有什么可以帮你的吗？"}
        ]
        st.rerun()

if __name__ == "__main__":
    app = MCPApp(name="amap-streamlit-app")
    asyncio.run(main()) 