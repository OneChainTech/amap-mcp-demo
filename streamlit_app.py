import asyncio
import streamlit as st
from mcp_agent.agents.agent import Agent
from mcp_agent.app import MCPApp
from mcp_agent.workflows.llm.augmented_llm_openai import OpenAIAugmentedLLM
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

# 初始化 session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "agent" not in st.session_state:
    st.session_state.agent = None

if "app" not in st.session_state:
    st.session_state.app = None

async def initialize_agent():
    """初始化 MCP 应用和代理"""
    if st.session_state.app is None:
        st.session_state.app = MCPApp(name="amap-streamlit-app")
        await st.session_state.app.run().__aenter__()
        
        st.session_state.agent = Agent(
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
        await st.session_state.agent.__aenter__()
        st.session_state.llm = await st.session_state.agent.attach_llm(OpenAIAugmentedLLM)
        logger.info("Agent initialized successfully")

async def process_message(user_message):
    """处理用户消息并获取回复"""
    try:
        # 确保代理已初始化
        if st.session_state.agent is None:
            await initialize_agent()
        
        logger.info(f"Processing message: {user_message}")
        
        # 使用 LLM 生成回复
        responses = await st.session_state.llm.generate(message=user_message)
        
        # 处理每个响应
        for response in responses:
            if response.content:
                yield response.content
                
                # 记录工具调用
                if response.tool_calls:
                    for tool_call in response.tool_calls:
                        logger.info(f"Tool called: {tool_call.function.name}")
                        logger.info(f"Tool arguments: {tool_call.function.arguments}")
                        if hasattr(tool_call, 'output'):
                            logger.info(f"Tool output: {tool_call.output}")
        
    except Exception as e:
        error_msg = f"发生错误: {str(e)}"
        logger.error(error_msg)
        yield error_msg

# Streamlit 界面
st.title("高德地图智能助手")

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
        message_placeholder = st.empty()
        full_response = ""
        
        # 创建异步运行时
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # 处理消息并显示流式输出
            async def process_stream(current_response):
                async for text in process_message(prompt):
                    current_response += text
                    message_placeholder.markdown(current_response + "▌")
                return current_response
            
            full_response = loop.run_until_complete(process_stream(full_response))
        finally:
            loop.close()
        
        # 移除光标并保存消息
        message_placeholder.markdown(full_response)
        st.session_state.messages.append({"role": "assistant", "content": full_response})

# 添加清除聊天历史按钮
if st.button("清除聊天历史"):
    st.session_state.messages = []
    st.experimental_rerun() 