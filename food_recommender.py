import streamlit as st
from openai import OpenAI
import os
import sys

# --- Configuration ---
APP_TITLE = "D老师我今天吃什么"

# 从环境变量获取 API key 和 base URL
try:
    API_KEY = st.secrets["OPENAI_API_KEY"] if "OPENAI_API_KEY" in st.secrets else os.getenv("OPENAI_API_KEY")
    BASE_URL = st.secrets["OPENAI_BASE_URL"] if "OPENAI_BASE_URL" in st.secrets else os.getenv("OPENAI_BASE_URL", "https://api.deepseek.com/v1")
    
    # 打印调试信息（仅在本地运行时显示）
    if not st.secrets:
        st.write("Debug info (local only):")
        st.write(f"API_KEY exists: {bool(API_KEY)}")
        st.write(f"BASE_URL: {BASE_URL}")
except Exception as e:
    st.error(f"配置加载失败: {str(e)}")
    st.stop()

# --- Helper Functions ---
def get_food_recommendation(client, previous_recommendations=None, special_requirements=None):
    """
    Gets a food recommendation from the AI model.
    """
    try:
        system_prompt = """
        你是一个专业的美食推荐助手。请根据以下要求推荐一道菜：
        1. 推荐一道具体的中餐或西餐菜品
        2. 描述要简洁但具体，包含：
           - 菜品名称
           - 主要食材
           - 简单的烹饪方式
           - 为什么推荐这道菜（比如：适合当前季节/营养均衡/容易制作等）
        3. 回答要生动有趣，但不要过于冗长
        4. 如果之前已经推荐过，请确保推荐不同的菜品
        """
        
        messages = [{"role": "system", "content": system_prompt}]
        
        # 添加特殊要求到提示中
        if special_requirements:
            messages.append({
                "role": "user",
                "content": f"请注意以下特殊要求：{special_requirements}"
            })
            
        if previous_recommendations:
            messages.append({
                "role": "user", 
                "content": f"之前推荐过这些菜：{', '.join(previous_recommendations)}，请推荐一道不同的菜。"
            })

        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            temperature=0.8,
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"获取推荐时出错: {str(e)}")
        return None

# --- Main Application ---
def main():
    st.set_page_config(page_title=APP_TITLE, layout="centered")
    
    # 使用自定义CSS来美化界面
    st.markdown("""
        <style>
        .main {
            background-color: #ffffff;
        }
        .stButton>button {
            width: 100%;
            background-color: #1E90FF;
            color: white;
            padding: 10px 20px;
            border: none;
            border-radius: 5px;
            font-size: 16px;
            margin: 5px 0;
        }
        .stButton>button:hover {
            background-color: #187bcd;
        }
        h1 {
            text-align: center;
            color: #000000;
            padding: 20px;
        }
        .stMarkdown {
            color: #000000;
        }
        .stAlert {
            color: #000000;
        }
        /* 修改spinner文字颜色 */
        .stSpinner > div {
            color: #000000 !important;
        }
        /* 确保所有标题文字为黑色 */
        h3 {
            color: #000000 !important;
        }
        /* 确保所有提示文字为黑色 */
        .stSpinner > div > div {
            color: #000000 !important;
        }
        /* 隐藏侧边栏 */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        /* 文本框样式 */
        .stTextArea textarea {
            font-size: 16px;
            padding: 10px;
        }
        /* 确保所有文本输入框的标签为黑色 */
        .stTextArea label {
            color: #000000 !important;
        }
        /* 确保所有提示文本为黑色 */
        .stTextArea p {
            color: #000000 !important;
        }
        /* 确保所有警告文本为黑色 */
        .stWarning {
            color: #000000 !important;
        }
        </style>
    """, unsafe_allow_html=True)
    
    st.title(APP_TITLE)

    # 检查 API key 是否配置
    if not API_KEY:
        st.error("""
        API key 未配置。请在 Streamlit Cloud 的 Secrets 中配置 OPENAI_API_KEY。
        
        配置步骤：
        1. 在 Streamlit Cloud 中打开你的应用
        2. 点击右上角的 "Manage app"
        3. 在左侧菜单中找到 "Secrets"
        4. 添加以下配置：
        ```toml
        OPENAI_API_KEY = "你的API密钥"
        OPENAI_BASE_URL = "https://api.deepseek.com/v1"
        ```
        """)
        st.stop()

    # Initialize OpenAI client
    try:
        client = OpenAI(api_key=API_KEY, base_url=BASE_URL)
        # 测试连接
        client.models.list()
    except Exception as e:
        st.error(f"""
        初始化失败，错误信息：{str(e)}
        
        可能的原因：
        1. API key 不正确
        2. API base URL 不正确
        3. 网络连接问题
        
        请检查：
        1. API key 是否正确配置
        2. API base URL 是否正确
        3. 网络连接是否正常
        """)
        st.stop()

    # Initialize session state for storing recommendations
    if "recommendations" not in st.session_state:
        st.session_state.recommendations = []
    if "current_recommendation" not in st.session_state:
        st.session_state.current_recommendation = None
    if "special_requirements" not in st.session_state:
        st.session_state.special_requirements = None

    # 添加特殊要求输入框
    special_requirements = st.text_area(
        "有什么特殊要求需要注意的吗？（例如口味偏好：不吃香菜，或者感冒吃得清淡一点）",
        height=100,
        key="requirements_input"
    )

    # 创建三个按钮的布局
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("根据需求帮我推荐", key="recommend_button"):
            with st.spinner("正在思考今天吃什么..."):
                recommendation = get_food_recommendation(
                    client, 
                    st.session_state.recommendations,
                    special_requirements if special_requirements.strip() else None
                )
                if recommendation:
                    st.session_state.current_recommendation = recommendation
                    st.session_state.recommendations.append(recommendation)
                    st.session_state.special_requirements = special_requirements

    with col2:
        if st.button("没有要求直接推荐", key="no_requirements_button"):
            with st.spinner("正在思考今天吃什么..."):
                recommendation = get_food_recommendation(
                    client, 
                    st.session_state.recommendations
                )
                if recommendation:
                    st.session_state.current_recommendation = recommendation
                    st.session_state.recommendations.append(recommendation)
                    st.session_state.special_requirements = None

    with col3:
        if st.button("再来一次", key="again_button"):
            if st.session_state.recommendations:
                with st.spinner("换个口味..."):
                    recommendation = get_food_recommendation(
                        client, 
                        st.session_state.recommendations,
                        st.session_state.special_requirements
                    )
                    if recommendation:
                        st.session_state.current_recommendation = recommendation
                        st.session_state.recommendations.append(recommendation)
            else:
                st.warning('请先点击"根据需求帮我推荐"获取推荐！')

    # Display current recommendation
    if st.session_state.current_recommendation:
        st.markdown("### 今日推荐")
        st.markdown(st.session_state.current_recommendation)

if __name__ == "__main__":
    main() 