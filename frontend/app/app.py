import streamlit as st
import requests
import json
from io import BytesIO

# 设置页面配置
st.set_page_config(
    page_title="ACH 智能面试辅助平台",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API基础URL
API_URL = "http://localhost:8080"

# 页面标题
st.title("🎯 ACH 智能面试辅助平台")

# 自定义CSS美化导航栏
st.markdown("""
<style>
/* 美化侧边栏 */
[data-testid="stSidebar"] {
    background-color: #f0f2f6;
}

/* 隐藏默认radio按钮 */
input[type="radio"] {
    display: none !important;
}

/* 功能导航标题居中显示 */
[data-testid="stSidebar"] h2 {
    text-align: center !important;
    font-size: 20px !important;
    font-weight: bold !important;
    margin: 20px 0 20px 0 !important;
    color: #333 !important;
}

/* 美化导航选项容器 */
.stRadio > div > div {
    margin-bottom: 8px;
    width: 100%;
}

/* 未选中的导航项样式 */
.stRadio label {
    display: flex;
    align-items: center;
    padding: 12px 16px;
    background-color: transparent !important;
    cursor: pointer;
    font-size: 16px;
    font-weight: 500;
    transition: all 0.2s ease;
    text-align: left !important;
    justify-content: flex-start !important;
    border: none !important;
    width: 100% !important;
}

/* 鼠标悬停效果 */
.stRadio label:hover {
    color: #1890ff !important;
    transform: translateX(4px);
}

/* 选中状态样式 - 圆角导航条 */
input[type="radio"]:checked + label {
    background-color: #1890ff !important;
    color: white !important;
    border-radius: 8px !important;
    padding: 12px 16px !important;
    box-shadow: 0 2px 8px rgba(24, 144, 255, 0.3) !important;
    display: flex !important;
    justify-content: space-between !important;
    align-items: center !important;
}

/* 为选中项添加">"符号 */
input[type="radio"]:checked + label::after {
    content: ">";
    font-size: 20px;
    font-weight: bold;
    margin-left: 8px;
}

/* 页脚样式 */
.footer {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    text-align: center;
    background-color: #f0f2f6;
    padding: 10px 0;
    margin: 0;
    font-size: 14px;
    z-index: 100;
    border-top: 1px solid #e0e0e0;
}

/* 确保内容不被页脚遮挡 */
.stApp {
    padding-bottom: 60px;
}
</style>
""", unsafe_allow_html=True)

# 导航菜单
nav = st.sidebar.radio(
    "功能导航",
    ["🏠 首页", "📄 简历上传与分析", "👨‍💻 AI模拟面试", "📊 历史记录"]
)

# 首页
if nav == "🏠 首页":
    # st.header("欢迎使用ACH智能面试辅助平台")
    st.markdown("""
    本平台提供以下核心功能：
    - 📄 **简历智能分析**：自动解析简历内容，评估质量，提出优化建议
    - 👨‍💻 **AI模拟面试**：基于岗位要求，生成结构化面试问题，进行交互式模拟面试
    - 📊 **个性化反馈**：提供详细的面试表现分析和改进建议
    
    开始使用，请先上传您的简历！
    """)

# 简历上传与分析
elif nav == "📄 简历上传与分析":
    st.header("📄 简历上传与分析")
    
    # 检查是否已有上传的简历
    if "resume_id" in st.session_state:
        st.success(f"已上传简历：{st.session_state['resume_filename']}")
        st.info(f"简历ID：{st.session_state['resume_id']}")
        
        # 显示重新上传选项
        if st.button("重新上传简历"):
            # 清除现有简历信息
            del st.session_state["resume_id"]
            del st.session_state["resume_filename"]
            if "resume_analysis" in st.session_state:
                del st.session_state["resume_analysis"]
            # 刷新页面以显示文件上传器
            st.rerun()
    else:
        # 文件上传
        uploaded_file = st.file_uploader(
            "选择您的简历文件",
            type=["pdf", "docx"],
            help="仅支持PDF和DOCX格式的简历文件"
        )
        
        if uploaded_file is not None:
            st.success(f"已选择文件：{uploaded_file.name}")
            
            # 上传按钮
            if st.button("上传并解析简历"):
                with st.spinner("正在上传和解析简历..."):
                    try:
                        # 发送文件到API
                        files = {"file": uploaded_file.getvalue()}
                        response = requests.post(
                            f"{API_URL}/api/v1/resume/upload",
                            files={"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                        )
                        
                        if response.status_code == 200:
                            result = response.json()
                            st.session_state["resume_id"] = result["resume_id"]
                            st.session_state["resume_filename"] = result["filename"]
                            st.success(f"简历上传成功！ID: {result['resume_id']}")
                            # 刷新页面以显示已上传信息
                            st.rerun()
                        else:
                            st.error(f"上传失败：{response.json().get('detail', '未知错误')}")
                    except Exception as e:
                        st.error(f"上传过程中出现错误：{str(e)}")
    
    # 分析简历
    if "resume_id" in st.session_state:
        st.markdown("---")
        st.subheader("简历分析")
        
        # 如果已有分析结果，直接显示
        if "resume_analysis" in st.session_state:
            st.success("简历分析已完成！")
            
            # 显示分析结果
            col1, col2 = st.columns(2)
            with col1:
                st.info(f"**文件名**：{st.session_state['resume_analysis']['filename']}")
                st.info(f"**内容长度**：{st.session_state['resume_analysis']['content_length']} 字符")
                st.info(f"**状态**：{st.session_state['resume_analysis']['status']}")
            
            with col2:
                st.markdown("### 简历内容预览")
                st.text_area("", st.session_state['resume_analysis']['text_preview'], height=300)
                
            # 显示AI分析结果
            st.markdown("---")
            st.markdown("### 📊 AI分析报告")
            st.markdown(st.session_state['resume_analysis']['analysis'])
        else:
            # 如果没有分析结果，显示分析按钮
            if st.button("开始分析简历"):
                with st.spinner("正在分析简历内容..."):
                    try:
                        response = requests.post(
                            f"{API_URL}/api/v1/resume/analyze?resume_id={st.session_state['resume_id']}"
                        )
                        
                        if response.status_code == 200:
                            result = response.json()
                            st.success("简历分析完成！")
                            
                            # 显示分析结果
                            col1, col2 = st.columns(2)
                            with col1:
                                st.info(f"**文件名**：{result['filename']}")
                                st.info(f"**内容长度**：{result['content_length']} 字符")
                                st.info(f"**状态**：{result['status']}")
                            
                            with col2:
                                st.markdown("### 简历内容预览")
                                st.text_area("", result['text_preview'], height=300)
                                
                            st.session_state["resume_analysis"] = result
                            
                            # 显示AI分析结果
                            st.markdown("---")
                            st.markdown("### 📊 AI分析报告")
                            st.markdown(result['analysis'])
                        else:
                            st.error(f"分析失败：{response.json().get('detail', '未知错误')}")
                    except Exception as e:
                        st.error(f"分析过程中出现错误：{str(e)}")

# AI模拟面试
elif nav == "👨‍💻 AI模拟面试":
    st.header("👨‍💻 AI模拟面试")
    
    # 检查是否已上传简历
    if "resume_id" not in st.session_state:
        st.warning("请先上传您的简历，然后再开始模拟面试")
        st.stop()
    
    # 岗位输入
    job_title = st.text_input(
        "请输入您想要模拟面试的岗位",
        placeholder="例如：软件工程师、数据分析师"
    )
    
    if st.button("开始模拟面试"):
        if not job_title:
            st.error("请输入岗位名称")
        else:
            with st.spinner("正在生成面试问题..."):
                try:
                    response = requests.post(
                        f"{API_URL}/api/v1/interview/start",
                        json={"job_title": job_title}
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        st.success(f"面试已开始！岗位：{result['job_title']}")
                        st.session_state["interview_id"] = "mock_interview_1"  # 临时ID
                        st.session_state["job_title"] = job_title
                        
                        # 显示模拟面试界面
                        st.markdown("---")
                        st.subheader(f"📋 {job_title} 模拟面试")
                        st.info("面试问题生成功能正在开发中...")
                    else:
                        st.error(f"面试开始失败：{response.json().get('detail', '未知错误')}")
                except Exception as e:
                    st.error(f"面试开始过程中出现错误：{str(e)}")

# 历史记录
elif nav == "📊 历史记录":
    st.header("📊 历史记录")
    
    if "resume_id" in st.session_state:
        st.markdown("### 最近上传的简历")
        st.info(f"文件名：{st.session_state['resume_filename']}")
        st.info(f"简历ID：{st.session_state['resume_id']}")
        
        if "resume_analysis" in st.session_state:
            st.markdown("### 简历内容预览")
            st.text_area("", st.session_state['resume_analysis']['text_preview'], height=200)
            
            st.markdown("---")
            st.markdown("### 📊 AI分析报告")
            st.markdown(st.session_state['resume_analysis']['analysis'])
    else:
        st.info("暂无历史记录，请先上传简历")

# 页脚
st.markdown("---")
st.markdown('<div class="footer">© 2026 ACH 智能面试辅助平台 </div>', unsafe_allow_html=True)
