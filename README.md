# 高德地图 MCP 智能助手

这是一个基于 Streamlit 和 MCP Agent 的高德地图智能助手应用。

## 功能特点

- 地点信息查询
- 天气信息获取
- 出行路线规划
- 距离测量
- 周边设施搜索

## 快速开始

1. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```

2. 配置环境变量：
   ```bash
   cp .env.example .env
   ```
   编辑 `.env` 文件，填入高德地图 API 密钥 (`AMAP_API_KEY`)

3. 运行应用：
   ```bash
   streamlit run streamlit_app.py
   ```

## 系统要求

- Python 3.8 或更高版本 