import streamlit as st
import os
import sys
import utils
import agents
import database
from langchain_zhipu import ChatZhipuAI
import re
import csv
from datetime import datetime
import pandas as pd

# 页面配置（必须放在最前面）
st.set_page_config(page_title="智能面试助手", page_icon="🎓", layout="wide")

# 全局初始化 - 移除冗余的系统路径配置
# 统一创建上传文件夹（避免多处重复创建）
os.makedirs("uploads/resumes", exist_ok=True)
os.makedirs("uploads/audio", exist_ok=True)

# ========== 修复文字重叠+无重复的最终版CSS+JS ==========
st.html("""
<style>
/* 全局背景 */
html, body, [data-testid="stApp"], [data-testid="stAppViewContainer"] {
    background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 50%, #cbd5e1 100%) !important;
    background-attachment: fixed !important;
    min-height: 100vh !important;
}

/* 透明头部 */
[data-testid="stHeader"], [data-testid="stToolbar"] {
    background: transparent !important;
}

/* 侧边栏 */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #eff6ff 0%, #ffffff 100%) !important;
    border-right: 1px solid rgba(147,197,253,0.3) !important;
}

/* 主内容区 */
.main .block-container {
    padding-top: 1rem !important;
    padding-bottom: 3rem !important;
    min-height: 95vh !important;
    background-image: 
        radial-gradient(circle at 15% 20%, rgba(59,130,246,0.06) 0%, transparent 35%),
        radial-gradient(circle at 85% 75%, rgba(96,165,250,0.06) 0%, transparent 35%),
        radial-gradient(circle at 50% 50%, rgba(147,197,253,0.04) 0%, transparent 50%) !important;
    background-repeat: no-repeat !important;
    position: relative !important;
}

/* 聊天容器 */
.chat-container {
    background-color: rgba(255,255,255,0.92) !important;
    border-radius: 16px !important;
    padding: 1.2rem !important;
    overflow-y: auto !important;
    margin-bottom: 1rem !important;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06) !important;
    position: relative !important;
    z-index: 1 !important;
    min-height: 350px !important;
    max-height: 450px !important;
    border: 1px solid rgba(255,255,255,0.8) !important;
}

/* 卡片样式 */
.card {
    background-color: rgba(255,255,255,0.95) !important;
    border-radius: 16px !important;
    padding: 1.5rem !important;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06) !important;
    margin-bottom: 1.5rem !important;
    transition: all 0.3s ease !important;
    position: relative !important;
    z-index: 1 !important;
    border: 1px solid rgba(255,255,255,0.8) !important;
}
.card:hover {
    box-shadow: 0 8px 30px rgba(0, 0, 0, 0.1) !important;
    transform: translateY(-2px) !important;
}

/* 文字颜色 */
h1, h2, h3 {
    color: #1e40af !important;
    font-weight: 600 !important;
}
p, span, div {
    color: #334155 !important;
}

/* 通用按钮 */
.stButton > button {
    background-color: #3b82f6 !important;
    color: white !important;
    border-radius: 10px !important;
    padding: 0.5rem 1.2rem !important;
    border: none !important;
    font-weight: 500 !important;
    transition: all 0.2s ease !important;
}
.stButton > button:hover {
    background-color: #2563eb !important;
    box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3) !important;
    transform: translateY(-1px) !important;
}

/* 危险按钮 */
.danger-btn > button {
    background-color: #fff5f5 !important;
    color: #e53e3e !important;
    border: 1px solid #fed7d7 !important;
    border-radius: 10px !important;
    padding: 0.6rem 1rem !important;
    font-weight: 500 !important;
    width: 100% !important;
}
.danger-btn > button:hover {
    background-color: #fed7d7 !important;
    color: #c53030 !important;
}

/* 确认/取消按钮 */
.confirm-btn > button {
    background-color: #3b82f6 !important;
    color: white !important;
    border-radius: 10px !important;
    padding: 0.8rem 1rem !important;
    width: 100% !important;
}
.cancel-btn > button {
    background-color: #f8fafc !important;
    color: #4a5568 !important;
    border: 1px solid #e2e8f0 !important;
    border-radius: 10px !important;
    padding: 0.8rem 1rem !important;
    width: 100% !important;
}

/* 上传组件文字修复 */
div[data-testid="stFileUploaderDropzoneInstructions"] > span {
    display: none !important;
}
div[data-testid="stFileUploaderDropzone"] {
    border: 2px dashed #93c5fd !important;
    border-radius: 12px !important;
    background: rgba(239,246,255,0.5) !important;
    overflow: hidden !important;
}
div[data-testid="stFileUploader"] button {
    border: 1px solid #3b82f6 !important;
    border-radius: 10px !important;
    background: white !important;
}
div[data-testid="stFileUploaderFile"] button::after {
    content: none !important;
}

/* 其他组件样式 */
.stExpander, .stMetric, .stStatus {
    border-radius: 12px !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.05) !important;
    background: rgba(255,255,255,0.95) !important;
}

/* 模型徽章 */
.current-model-badge {
    display: inline-block !important;
    background: linear-gradient(135deg, #3b82f6 0%, #60a5fa 100%) !important;
    color: white !important;
    padding: 0.3rem 0.8rem !important;
    border-radius: 20px !important;
    font-size: 0.85rem !important;
}

/* 引导提示 */
.guide-tip {
    margin-top: 3rem !important;
    padding: 1.2rem !important;
    text-align: center !important;
    color: #64748b !important;
    background: rgba(255,255,255,0.7) !important;
    border-radius: 12px !important;
    border: 1px dashed #93c5fd !important;
}

/* 侧边栏菜单 */
.sidebar-group-title {
    font-size: 0.85rem !important;
    font-weight: 600 !important;
    color: #1e40af !important;
    margin: 1.5rem 0 0.5rem 0.5rem !important;
}
div[role="radiogroup"] label {
    padding: 0.6rem 0.8rem !important;
    border-radius:10px !important;
}
div[role="radiogroup"] label:hover {background:#dbeafe !important;}
div[role="radiogroup"] input:checked + div {
    background:#dbeafe !important;
    border-left:4px solid #3b82f6 !important;
    border-radius:0 10px 10px 0 !important;
}
div[role="radiogroup"] input {display:none !important;}

/* 表格样式 */
.styled-table {
    width: 100% !important;
    border-collapse: collapse !important;
}
.styled-table td {
    padding: 0.8rem 1rem !important;
    border-bottom: 1px solid #e2e8f0 !important;
    vertical-align: middle !important;
}
.styled-table tr:last-child td {border-bottom: none !important;}
.styled-table td:first-child {
    font-weight: 500 !important;
    color: #475569 !important;
    width: 40% !important;
}
.styled-table td:last-child {
    text-align: right !important;
    color: #1e40af !important;
    font-weight: 500 !important;
}

/* 聊天输入框 */
.custom-chat-form {margin-bottom: 1rem !important;}
.custom-chat-form > div {display: flex !important; gap: 0.5rem !important;}
.custom-chat-form > div > div:first-child {flex-grow: 1 !important;}
div[data-testid="stForm"] {border: none !important; padding: 0 !important;}

/* 输入框美化 */
.stTextInput input, .stTextArea textarea {
    border-radius: 10px !important;
    border: 1px solid #cbd5e1 !important;
    padding: 0.6rem 1rem !important;
}
.stTextInput input:focus, .stTextArea textarea:focus {
    border-color: #3b82f6 !important;
    box-shadow: 0 0 0 2px rgba(59,130,246,0.2) !important;
}

/* 暗黑模式适配 */
@media (prefers-color-scheme: dark), .dark-mode {
    html, body, [data-testid="stApp"], [data-testid="stAppViewContainer"] {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%) !important;
    }
    p, span, div, li, td {color: #e2e8f0 !important;}
    h1, h2, h3 {color: #60a5fa !important;}
    
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1e293b 0%, #334155 100%) !important;
        border-right: 1px solid #475569 !important;
    }
    
    .card, .chat-container, .stExpander {
        background: rgba(30,41,59,0.95) !important;
        border: 1px solid #475569 !important;
    }
}

/* 下载按钮样式 */
.download-btn > button {
    background-color: #10b981 !important;
    color: white !important;
    border-radius: 10px !important;
    padding: 0.6rem 1rem !important;
    width: 100% !important;
}
.download-btn > button:hover {
    background-color: #059669 !important;
    box-shadow: 0 4px 12px rgba(16,185,129,0.3) !important;
}
</style>
""")

# 工具函数：安全文件名处理
def safe_filename(filename):
    if not filename:
        return "unknown_file"
    safe_name = re.sub(r'[^\w\-.]', '_', filename)
    if len(safe_name) > 100:
        name, ext = os.path.splitext(safe_name)
        safe_name = name[:90] + ext
    return safe_name

# 下载历史报告函数
def download_history_report(table_name, display_name, columns_map, file_prefix):
    try:
        conn = database.get_conn()
        cursor = conn.execute(f"SELECT * FROM {table_name} ORDER BY id DESC")
        records = cursor.fetchall()
        conn.close()
        
        if not records:
            st.info(f"暂无{display_name}记录可下载")
            return
        
        df = pd.DataFrame(records)
        df = df.rename(columns=columns_map)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        st.markdown('<div class="download-btn">', unsafe_allow_html=True)
        st.download_button(
            label=f"📥 下载{display_name}历史报告",
            data=df.to_csv(index=False, encoding='utf-8-sig'),
            file_name=f"{file_prefix}_历史记录_{timestamp}.csv",
            mime="text/csv",
            key=f"download_{table_name}"
        )
        st.markdown('</div>', unsafe_allow_html=True)
    except Exception as e:
        st.error(f"生成{display_name}报告失败：{str(e)}")

# 页面跳转逻辑
def smart_jump(user_input):
    function_map = {
        "📄 简历评估": ["简历", "评估", "打分", "优化", "修改", "润色"],
        "🎙️ 面试录音分析": ["录音", "音频", "转写", "分析", "语音", "说话"],
        "❓ 个性化面试题": ["面试题", "题目", "出题", "练习题", "考题", "面试模板"],
        "🎯 实时面试模拟": ["面试", "模拟", "练习", "实战", "演练"],
        "✉️ 求职信生成": ["求职信", "自荐信", "cover letter", "申请信"],
        "💰 薪资谈判": ["薪资", "工资", "薪水", "谈判", "谈薪", "待遇"],
        "📈 职业规划": ["规划", "发展", "路线", "方向", "未来"],
        "🔍 简历ATS优化": ["ats", "筛选", "通过率", "系统", "关键词"],
        "🎭 多风格面试模拟": ["风格", "压力面", "hr面", "技术面", "面试官"],
        "📝 面试复盘": ["复盘", "总结", "回顾", "反思", "分析"]
    }
    user_input_lower = user_input.lower()
    for page_name, keywords in function_map.items():
        for keyword in keywords:
            if keyword in user_input_lower:
                return page_name
    return None

# 初始化会话状态
def init_session_states():
    default_states = {
        "pending_jump": None,
        "quick_question": "",
        "confirm_clear_resumes": False,
        "confirm_clear_interviews": False,
        "confirm_clear_generated_questions": False,
        "confirm_clear_cover_letters": False,
        "confirm_clear_salary_advice": False,
        "confirm_clear_ats_optimizations": False,
        "auto_resume_result": None,
        "auto_questions_result": None,
        "user_context": {},
        "interview_started": False,
        "current_question": "",
        "feedback": "",
        "finished": False,
        "final_report": "",
        "multi_interview_started": False,
        "multi_finished": False,
        "chat_messages": [],
    }
    for key, default_value in default_states.items():
        if key not in st.session_state:
            st.session_state[key] = default_value

init_session_states()

# 跳转处理
if st.session_state.pending_jump:
    st.session_state.single_menu = st.session_state.pending_jump
    st.session_state.pending_jump = None
    st.rerun()

if st.session_state.quick_question:
    user_in = st.session_state.quick_question
    st.session_state.quick_question = ""
    target_page = smart_jump(user_in)
    if target_page:
        st.session_state.single_menu = target_page
        st.rerun()

# 大模型初始化 - 移除明文API密钥，改为侧边栏输入（安全+不影响功能）
st.sidebar.subheader("🔑 API配置")
ZHIPU_API_KEY = st.sidebar.text_input("智谱API密钥", type="password", 
                                   value="",
                                   help="输入你的智谱AI API密钥")
# 保持模型参数不变
global_llm = None
if ZHIPU_API_KEY:
    global_llm = ChatZhipuAI(
        api_key=ZHIPU_API_KEY,
        model="glm-4-flash",
        temperature=0.6,
        streaming=True,
        max_tokens=2048
    )

# 顶部标题
st.markdown("""
<div style="text-align: center; margin-bottom: 1.5rem; padding: 1.2rem; background: linear-gradient(135deg, #3b82f6 0%, #60a5fa 100%); border-radius: 16px; box-shadow: 0 6px 20px rgba(59, 130, 246, 0.2);">
    <h1 style="color: white; margin-bottom: 0.3rem; font-size: 2.2rem;">🎓 第八届传智杯 · 智能面试助手</h1>
    <p style="color: rgba(255,255,255,0.9); font-size: 1rem; margin:0;">多Agent协同 | 多模型支持 | 参赛专用版</p>
</div>
""", unsafe_allow_html=True)

# 侧边栏
st.sidebar.title("🎓 智能面试助手")
st.sidebar.divider()

st.sidebar.subheader("🔧 系统设置")
selected_model = st.sidebar.selectbox(
    "选择大模型",
    options=list(agents.MODEL_CONFIGS.keys()),
    index=0,
    help="智谱清言4-Flash速度最快，响应最稳定"
)
agents.init_llm(selected_model)
st.sidebar.success(f"✅ 已切换到：{selected_model}")

# 修复：删除重复的暗黑模式CSS，仅保留开关逻辑（无样式冲突）
dark_mode = st.sidebar.checkbox("🌙 暗黑模式")
if dark_mode:
    st.html("""<script>document.documentElement.classList.add('dark-mode')</script>""")
else:
    st.html("""<script>document.documentElement.classList.remove('dark-mode')</script>""")

st.sidebar.divider()
st.sidebar.markdown('<div class="sidebar-group-title">🏠 基础功能</div>', unsafe_allow_html=True)
menu = st.sidebar.radio(
    "",
    [
        "🏠 首页",
        "🤖 智能面试助手",
        "📄 简历评估",
        "🎙️ 面试录音分析",
        "❓ 个性化面试题",
        "🎯 实时面试模拟",
        "---",
        "✉️ 求职信生成",
        "💰 薪资谈判",
        "📈 职业规划",
        "🔍 简历ATS优化",
        "🎭 多风格面试模拟",
        "📝 面试复盘"
    ],
    index=0,
    label_visibility="collapsed",
    key="single_menu"
)
if menu == "---":
    st.stop()

st.sidebar.markdown("""
<style>
div[role="radiogroup"] label:nth-child(7) { display:none !important; }
div[role="radiogroup"] label:nth-child(6)::after {
    content:"";display:block;height:1px;background:#93c5fd;margin:1rem 0.5rem;
}
div[role="radiogroup"] label:nth-child(7)::before {
    content:"✨ 扩展功能";display:block;font-size:0.85rem;color:#1e40af;margin:1rem 0 0.5rem 0.5rem;
}
</style>
""", unsafe_allow_html=True)

# 清除历史记录函数
def clear_history(table_name, display_name):
    confirm_key = f"confirm_clear_{table_name}"
    if confirm_key not in st.session_state:
        st.session_state[confirm_key] = False
    
    st.markdown('<div class="danger-btn">', unsafe_allow_html=True)
    if st.button(f"🗑️ 清除{display_name}历史", key=f"clear_{table_name}"):
        st.session_state[confirm_key] = True
    
    if st.session_state[confirm_key]:
        st.warning(f"⚠️ 确定清除全部{display_name}记录？操作不可恢复！")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown('<div class="confirm-btn">', unsafe_allow_html=True)
            if st.button("✅ 确认清除", type="primary", key=f"confirm_{table_name}"):
                try:
                    conn = database.get_conn()
                    conn.execute(f"DELETE FROM {table_name}")
                    conn.commit()
                    conn.close()
                    st.success(f"✅ {display_name}历史已清除")
                    st.session_state[confirm_key] = False
                    st.rerun()
                except Exception as e:
                    st.error(f"清除失败：{str(e)}")
            st.markdown('</div>', unsafe_allow_html=True)
        with c2:
            st.markdown('<div class="cancel-btn">', unsafe_allow_html=True)
            if st.button("❌ 取消", key=f"cancel_{table_name}"):
                st.session_state[confirm_key] = False
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ===================== 页面渲染区域（完全无修改） =====================
if menu == "🏠 首页":
    st.success("✅ 项目启动成功！所有功能正常运行")
    st.markdown("## 🎯 项目核心功能")
    c1,c2,c3=st.columns(3)
    with c1:
        st.markdown("""<div class="card"><h3 style="color:#1e40af;margin:0">📄 简历智能评估</h3><p>解析简历、违禁词检测、多维度评分+优化建议</p></div>""",unsafe_allow_html=True)
    with c2:
        st.markdown("""<div class="card"><h3 style="color:#1e40af;margin:0">🎙️ 面试录音分析</h3><p>语音转写、回答点评、逻辑梳理+改进方向</p></div>""",unsafe_allow_html=True)
    with c3:
        st.markdown("""<div class="card"><h3 style="color:#1e40af;margin:0">❓ 个性化面试题</h3><p>依托简历自动出题，配套答题参考要点</p></div>""",unsafe_allow_html=True)

    st.markdown("## 🛠️ 技术栈详情")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        <div class="card">
            <h3 style="color:#1e40af;margin:0 0 1rem 0;">前端与核心框架</h3>
            <table class="styled-table">
                <tr><td>前端框架</td><td>Streamlit 1.35.0</td></tr>
                <tr><td>大模型支持</td><td>智谱清言4-Flash</td></tr>
                <tr><td>文档解析</td><td>PyPDF2 / python-docx</td></tr>
            </table>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class="card">
            <h3 style="color:#1e40af;margin:0 0 1rem 0;">辅助与数据模块</h3>
            <table class="styled-table">
                <tr><td>语音转写</td><td>OpenAI Whisper</td></tr>
                <tr><td>数据存储</td><td>SQLite 数据库</td></tr>
                <tr><td>架构模式</td><td>多Agent协同架构</td></tr>
            </table>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("## 📊 个人数据可视化看板")
    def get_stats():
        try:
            conn = database.get_conn()
            resume_cnt = conn.execute("SELECT COUNT(*) FROM resumes").fetchone()
            interview_cnt = conn.execute("SELECT COUNT(*) FROM mock_interviews").fetchone()
            question_cnt = conn.execute("SELECT COUNT(*) FROM generated_questions").fetchone()
            ats_cnt = conn.execute("SELECT COUNT(*) FROM ats_optimizations").fetchone()
            conn.close()
            resume_cnt = resume_cnt[0] if resume_cnt else 0
            interview_cnt = interview_cnt[0] if interview_cnt else 0
            question_cnt = question_cnt[0] if question_cnt else 0
            ats_cnt = ats_cnt[0] if ats_cnt else 0
            return resume_cnt, interview_cnt, question_cnt, ats_cnt
        except Exception as e:
            st.warning(f"获取统计数据失败：{str(e)}")
            return 0,0,0,0
    resume_cnt, interview_cnt, question_cnt, ats_cnt = get_stats()
    c1,c2,c3,c4=st.columns(4)
    c1.metric("简历评估次数", resume_cnt)
    c2.metric("模拟面试次数", interview_cnt)
    c3.metric("生成面试题", question_cnt)
    c4.metric("ATS优化次数", ats_cnt)

    st.markdown("## 🚀 国赛核心：一键自动化面试全流程")
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.info("🤖 中央调度Agent：自动执行 简历评估 → 生成面试题 → 模拟面试 全流程")
    auto_file = st.file_uploader("上传简历启动自动化流程", type=["pdf", "docx"], key="auto_resume")
    if auto_file and st.button("▶️ 启动自动化全流程"):
        try:
            filename = safe_filename(auto_file.name)
            path = f"uploads/resumes/{filename}"
            with open(path, "wb") as f:
                f.write(auto_file.getbuffer())
            with st.status("🤖 中央调度Agent执行中...") as status:
                content = utils.parse_resume(path)
                st.session_state.user_context = {"resume_content": content, "resume_filename": filename}
                status.update(label="✅ 简历解析完成，执行评估...")
                utils.check_forbidden(content)
                resume_result = agents.resume_agent.run(path, filename)
                st.session_state.auto_resume_result = resume_result
                status.update(label="✅ 简历评估完成，生成面试题...")
                questions_result = agents.question_agent.run(content, filename)
                st.session_state.auto_questions_result = questions_result
                status.update(label="✅ 面试题生成完成，启动模拟面试...")
                st.session_state.interview_started = False
                st.session_state.current_question = agents.interview_agent.start(content, filename)
                st.session_state.interview_started = True
                st.session_state.finished = False
                st.session_state.feedback = ""
                status.update(label="✅ 自动化面试全流程执行完毕！", state="complete")
            st.success("✅ 自动化面试全流程执行完毕！可前往对应功能查看结果：")
            col1,col2,col3=st.columns(3)
            with col1:st.info("📄 简历评估报告已生成")
            with col2:st.info("❓ 面试题已生成完成")
            with col3:st.info("🎯 模拟面试已初始化")
            st.session_state.pending_jump = "📄 简历评估"
        except Exception as e:
            st.error(f"自动化流程执行失败：{str(e)}")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("## 📜 历史记录查询")
    with st.expander("📄 查看简历评估历史", expanded=True):
        try:
            conn = database.get_conn()
            history = conn.execute("SELECT id, filename, score, created_at FROM resumes ORDER BY id DESC LIMIT 10").fetchall()
            conn.close()
            if history:
                for record in history:
                    st.markdown(f"**{record[1]}** | 得分：{record[2]} | 时间：{record[3]}")
            else:
                st.info("暂无历史记录")
            download_history_report(
                table_name="resumes",display_name="简历评估",
                columns_map={"filename":"文件名","score":"评分","report":"评估报告","created_at":"创建时间"},
                file_prefix="简历评估"
            )
        except Exception as e:
            st.warning(f"获取历史记录失败：{str(e)}")
    st.markdown('<div class="guide-tip">💡 左侧菜单栏选择对应功能，即可开始面试辅助操作</div>',unsafe_allow_html=True)

elif menu == "📄 简历评估":
    st.subheader("📄 简历智能评估")
    with st.container():
        st.markdown('<div class="card">',unsafe_allow_html=True)
        if st.session_state.auto_resume_result:
            try:
                filename = st.session_state.user_context.get('resume_filename', '未知文件')
                st.success(f"📄 自动化流程生成的评估结果（来自：{filename}）")
                col1,col2=st.columns([1,2])
                with col1:
                    score = st.session_state.auto_resume_result.get('score', '0')
                    similarity = st.session_state.auto_resume_result.get('similarity', 0.0)
                    st.metric("简历评分",f"{score}分")
                    st.metric("模板相似度",f"{similarity:.2%}")
                with col2:
                    st.markdown("### 评估报告")
                    report = st.session_state.auto_resume_result.get("report", "暂无报告")
                    st.markdown(report)
                    st.download_button("下载报告", report, "简历评估报告.txt")
                st.markdown("---")
            except Exception as e:
                st.warning(f"显示自动化评估结果失败：{str(e)}")
        file=st.file_uploader("上传简历（PDF/DOCX）",type=["pdf","docx"], key="resume_upload")
        if file and st.button("🚀 开始评估"):
            try:
                filename = safe_filename(file.name)
                path=f"uploads/resumes/{filename}"
                with open(path,"wb") as f:f.write(file.getbuffer())
                with st.status("评估解析中...") as status:
                    content=utils.parse_resume(path)
                    utils.check_forbidden(content)
                    res=agents.resume_agent.run(path, filename)
                    status.update(label="✅ 评估完成",state="complete")
                col1,col2=st.columns([1,2])
                with col1:
                    st.metric("简历评分",f"{res.get('score', '0')}分")
                    st.metric("模板相似度",f"{res.get('similarity', 0.0):.2%}")
                with col2:
                    st.markdown("### 评估报告")
                    st.markdown(res.get("report", "暂无报告"))
                    st.download_button("下载报告", res.get("report", ""), "简历评估报告.txt")
            except Exception as e:
                st.error(f"评估失败：{str(e)}")
        st.markdown('</div>',unsafe_allow_html=True)
    st.markdown("---")
    h1,h2,h3=st.columns([6,2,2])
    with h1:st.subheader("📜 最近评估记录")
    with h2:clear_history("resumes","简历评估")
    with h3:
        download_history_report(
            table_name="resumes",display_name="简历评估",
            columns_map={"filename":"文件名","score":"评分","report":"评估报告","created_at":"创建时间"},
            file_prefix="简历评估"
        )
    try:
        conn=database.get_conn()
        rec=conn.execute("SELECT filename,score,report FROM resumes ORDER BY id DESC LIMIT 5").fetchall()
        conn.close()
        if rec:
            for r in rec:
                with st.expander(f"{r['filename']} - {r['score']}分"):
                    st.markdown(r["report"])
        else:
            st.info("暂无历史记录")
    except Exception as e:
        st.warning(f"获取评估记录失败：{str(e)}")
    st.markdown('<div class="guide-tip">📌 上传简历文件后点击评估，即可获取专业打分与优化意见</div>',unsafe_allow_html=True)

elif menu == "🎙️ 面试录音分析":
    st.subheader("🎙️ 面试录音分析")
    with st.container():
        st.markdown('<div class="card">',unsafe_allow_html=True)
        file=st.file_uploader("上传录音（MP3/WAV）",type=["mp3","wav"], key="audio_upload")
        if file and st.button("🎙️ 开始分析"):
            try:
                safe_name = safe_filename(file.name)
                path=os.path.join("uploads","audio",safe_name)
                with open(path,"wb") as f:f.write(file.getbuffer())
                with st.status("语音解析分析中...") as status:
                    utils.init_whisper()
                    text=utils.audio_to_text(path)
                    res=agents.audio_agent.run(path, safe_name)
                    status.update(label="✅ 分析完成",state="complete")
                c1,c2=st.columns([1,2])
                with c1:
                    st.metric("面试评分",f"{res.get('score', '0')}分")
                    st.download_button("下载转写文本", res.get("transcript", ""), f"{safe_name}_文本.txt")
                with c2:
                    st.markdown("录音转写内容")
                    st.text_area("", res.get("transcript", ""), height=120, key="audio_result_textarea")
                    st.markdown("分析报告")
                    st.markdown(res.get("report", "暂无报告"))
            except Exception as e:
                st.error(f"分析失败：{str(e)}")
        st.markdown('</div>',unsafe_allow_html=True)
    st.markdown("---")
    h1,h2,h3=st.columns([6,2,2])
    with h1:st.subheader("📜 最近分析记录")
    with h2:clear_history("interviews","录音分析")
    with h3:
        download_history_report(
            table_name="interviews",display_name="录音分析",
            columns_map={"filename":"文件名","score":"评分","transcript":"转写文本","report":"分析报告","created_at":"创建时间"},
            file_prefix="录音分析"
        )
    try:
        conn=database.get_conn()
        rec=conn.execute("SELECT id,filename,score,transcript,report FROM interviews ORDER BY id DESC LIMIT 5").fetchall()
        conn.close()
        if rec:
            for r in rec:
                with st.expander(f"{r['filename']} - {r['score']}分"):
                    st.text_area("转写", r["transcript"], height=80, key=f"history_audio_text_{r['id']}")
                    st.markdown(r["report"])
        else:
            st.info("暂无历史记录")
    except Exception as e:
        st.warning(f"获取录音分析记录失败：{str(e)}")
    st.markdown('<div class="guide-tip">🎧 上传面试录音，自动转写文字并点评答题表现</div>',unsafe_allow_html=True)

elif menu == "❓ 个性化面试题":
    st.subheader("❓ 个性化面试题生成")
    with st.container():
        st.markdown('<div class="card">',unsafe_allow_html=True)
        if st.session_state.auto_questions_result:
            try:
                filename = st.session_state.user_context.get('resume_filename', '未知文件')
                st.success(f"❓ 自动化流程生成的面试题（来自：{filename}）")
                st.markdown("### 面试练习题")
                st.markdown(st.session_state.auto_questions_result)
                st.download_button("下载题库", st.session_state.auto_questions_result, "面试题目.txt")
                st.markdown("---")
            except Exception as e:
                st.warning(f"显示自动化面试题失败：{str(e)}")
        file=st.file_uploader("上传简历生成题目",type=["pdf","docx"], key="question_resume_upload")
        if file and st.button("📝 生成面试题"):
            try:
                filename = safe_filename(file.name)
                path=f"uploads/resumes/{filename}"
                with open(path,"wb") as f:f.write(file.getbuffer())
                with st.status("题目生成中..."):
                    content=utils.parse_resume(path)
                    res=agents.question_agent.run(content, filename)
                st.markdown("### 面试练习题")
                st.markdown(res)
                st.download_button("下载题库", res, "面试题目.txt")
            except Exception as e:
                st.error(f"生成失败：{str(e)}")
        st.markdown('</div>',unsafe_allow_html=True)
    st.markdown("---")
    h1,h2,h3=st.columns([6,2,2])
    with h1:st.subheader("📜 最近生成记录")
    with h2:clear_history("generated_questions","面试题生成")
    with h3:
        download_history_report(
            table_name="generated_questions",display_name="面试题生成",
            columns_map={"resume_filename":"简历文件名","questions":"面试题目","created_at":"创建时间"},
            file_prefix="面试题生成"
        )
    try:
        conn=database.get_conn()
        rec=conn.execute("SELECT resume_filename,questions FROM generated_questions ORDER BY id DESC LIMIT 5").fetchall()
        conn.close()
        if rec:
            for r in rec:
                with st.expander(r["resume_filename"]):
                    st.markdown(r["questions"])
        else:
            st.info("暂无记录")
    except Exception as e:
        st.warning(f"获取面试题记录失败：{str(e)}")
    st.markdown('<div class="guide-tip">📖 依托个人简历，定制专属岗位面试考题辅助备考</div>',unsafe_allow_html=True)

elif menu == "🎯 实时面试模拟":
    st.subheader("🎯 实时交互式面试模拟")
    with st.container():
        st.markdown('<div class="card">',unsafe_allow_html=True)
        if st.session_state.interview_started:
            try:
                filename = st.session_state.user_context.get('resume_filename', '未知文件')
                st.info(f"🎯 自动化流程已为你初始化模拟面试（来自：{filename}）")
                st.markdown(f"### 面试官：{st.session_state.current_question}")
                ans=st.text_area("你的回答：",height=140, key="interview_answer_input")
                if st.button("✅ 提交回答") and ans:
                    try:
                        feed, next_q, fin = agents.interview_agent.answer(ans)
                        st.session_state.feedback = feed
                        st.session_state.finished = fin
                        if not fin:
                            st.session_state.current_question = next_q
                        else:
                            st.session_state.final_report = next_q
                        st.rerun()
                    except Exception as e:
                        st.error(f"提交回答失败：{str(e)}")
                if st.session_state.feedback:
                    st.info("AI点评："+st.session_state.feedback)
                if st.session_state.finished:
                    st.success("面试结束")
                    st.markdown(st.session_state.final_report)
                    st.download_button("下载面试报告", st.session_state.final_report, "模拟面试报告.txt")
                    if st.button("🔄 重新开始"):
                        st.session_state.interview_started = False
                        st.session_state.current_question = ""
                        st.session_state.feedback = ""
                        st.session_state.finished = False
                        st.session_state.final_report = ""
                        st.rerun()
                st.markdown("---")
            except Exception as e:
                st.warning(f"加载模拟面试失败：{str(e)}")
        file=st.file_uploader("上传简历开始面试",type=["pdf","docx"], key="interview_resume_upload")
        if file and not st.session_state.interview_started:
            if st.button("🚀 开始面试"):
                try:
                    filename = safe_filename(file.name)
                    path=f"uploads/resumes/{filename}"
                    with open(path,"wb") as f:f.write(file.getbuffer())
                    content=utils.parse_resume(path)
                    st.session_state.current_question=agents.interview_agent.start(content, filename)
                    st.session_state.interview_started=True
                    st.session_state.finished=False
                    st.session_state.feedback=""
                    st.rerun()
                except Exception as e:
                    st.error(f"启动面试失败：{str(e)}")
        st.markdown('</div>',unsafe_allow_html=True)
    st.markdown('<div class="guide-tip">🤝 沉浸式模拟面试流程，实时收获答题点评与改进建议</div>',unsafe_allow_html=True)

elif menu == "✉️ 求职信生成":
    st.subheader("✉️ 专业求职信生成")
    with st.container():
        st.markdown('<div class="card">',unsafe_allow_html=True)
        job=st.text_input("目标岗位",placeholder="例如：Python开发工程师", key="cover_job_input")
        company=st.text_input("目标公司",placeholder="例如：科技有限公司", key="cover_company_input")
        file=st.file_uploader("上传简历",type=["pdf","docx"], key="cover_resume_upload")
        if job and company and file and st.button("✉️ 生成求职信"):
            try:
                filename = safe_filename(file.name)
                path=f"uploads/resumes/{filename}"
                with open(path,"wb") as f:f.write(file.getbuffer())
                content=utils.parse_resume(path)
                res=agents.cover_agent.run(content, job, company, filename)
                st.markdown("### 求职信内容")
                st.markdown(res)
                st.download_button("下载文档", res, "求职信.txt")
            except Exception as e:
                st.error(f"生成求职信失败：{str(e)}")
        st.markdown('</div>',unsafe_allow_html=True)
    st.markdown("---")
    h1,h2,h3=st.columns([6,2,2])
    with h1:st.subheader("历史生成记录")
    with h2:clear_history("cover_letters","求职信")
    with h3:
        download_history_report(
            table_name="cover_letters",display_name="求职信",
            columns_map={"job":"目标岗位","company":"目标公司","content":"求职信内容","resume_filename":"简历文件名","created_at":"创建时间"},
            file_prefix="求职信"
        )
    key=st.text_input("搜索岗位/公司", key="cover_search_input")
    try:
        conn=database.get_conn()
        if key:
            rec=conn.execute("SELECT job,company,content FROM cover_letters WHERE job LIKE ? OR company LIKE ?",(f"%{key}%",f"%{key}%")).fetchall()
        else:
            rec=conn.execute("SELECT job,company,content FROM cover_letters ORDER BY id DESC LIMIT 10").fetchall()
        conn.close()
        for r in rec:
            with st.expander(f"{r['job']} | {r['company']}"):
                st.markdown(r["content"])
    except Exception as e:
        st.warning(f"获取求职信记录失败：{str(e)}")
    st.markdown('<div class="guide-tip">📩 填写岗位与企业信息，快速生成贴合个人经历的求职自荐信</div>',unsafe_allow_html=True)

elif menu == "💰 薪资谈判":
    st.subheader("💰 薪资谈判助手")
    with st.container():
        st.markdown('<div class="card">',unsafe_allow_html=True)
        job=st.text_input("应聘岗位",placeholder="例如：后端开发", key="salary_job_input")
        city=st.text_input("工作城市",placeholder="例如：广州", key="salary_city_input")
        exp=st.number_input("工作经验（年）",0,20, key="salary_exp_input")
        if st.button("💰 获取薪资建议"):
            try:
                res=agents.salary_agent.run(job, city, exp)
                st.markdown("### 薪资参考与谈判话术")
                st.markdown(res)
                st.download_button("保存建议", res, "薪资谈判建议.txt")
            except Exception as e:
                st.error(f"生成薪资建议失败：{str(e)}")
        st.markdown('</div>',unsafe_allow_html=True)
    st.markdown("---")
    h1,h2,h3=st.columns([6,2,2])
    with h1:st.subheader("查询记录")
    with h2:clear_history("salary_advice","薪资谈判")
    with h3:
        download_history_report(
            table_name="salary_advice",display_name="薪资谈判",
            columns_map={"job":"应聘岗位","city":"工作城市","experience":"工作经验(年)","content":"薪资建议","created_at":"创建时间"},
            file_prefix="薪资谈判"
        )
    key=st.text_input("搜索岗位/城市", key="salary_search_input")
    try:
        conn=database.get_conn()
        rec=conn.execute("SELECT job,city,experience,content FROM salary_advice ORDER BY id DESC LIMIT 10").fetchall()
        conn.close()
        for r in rec:
            with st.expander(f"{r['job']} {r['city']} {r['experience']}年"):
                st.markdown(r["content"])
    except Exception as e:
        st.warning(f"获取薪资建议记录失败：{str(e)}")
    st.markdown('<div class="guide-tip">💸 结合城市、岗位、工龄，给到合理薪资范围与谈判技巧</div>',unsafe_allow_html=True)

elif menu == "📈 职业规划":
    st.subheader("📈 个性化职业规划")
    with st.container():
        st.markdown('<div class="card">',unsafe_allow_html=True)
        interest=st.text_input("个人兴趣方向",placeholder="人工智能、前端、测试等", key="career_interest_input")
        file=st.file_uploader("上传简历",type=["pdf","docx"], key="career_resume_upload")
        if interest and file and st.button("📈 生成职业规划"):
            try:
                filename = safe_filename(file.name)
                path=f"uploads/resumes/{filename}"
                with open(path,"wb") as f:f.write(file.getbuffer())
                content=utils.parse_resume(path)
                res=agents.career_agent.run(content, interest, filename)
                st.markdown("### 职业规划方案")
                st.markdown(res)
                st.download_button("下载方案", res, "职业规划.txt")
            except Exception as e:
                st.error(f"生成职业规划失败：{str(e)}")
        st.markdown('</div>',unsafe_allow_html=True)
    st.markdown('<div class="guide-tip">🗺️ 结合自身履历与兴趣，制定短期中长期成长路线</div>',unsafe_allow_html=True)

elif menu == "🔍 简历ATS优化":
    st.subheader("🔍 简历ATS智能优化")
    st.markdown("自动检测ATS兼容问题，补齐岗位关键词优化简历通过率")
    with st.container():
        st.markdown('<div class="card">',unsafe_allow_html=True)
        c1,c2=st.columns(2)
        with c1:
            file=st.file_uploader("上传简历",type=["pdf","docx"], key="ats_resume_upload")
        with c2:
            jd=st.text_area("粘贴岗位JD描述",height=140, key="ats_jd_input")
        if file and jd and st.button("🚀 开始ATS优化"):
            try:
                filename = safe_filename(file.name)
                path=f"uploads/resumes/{filename}"
                with open(path,"wb") as f:f.write(file.getbuffer())
                content=utils.parse_resume(path)
                res=agents.ats_agent.run(content, filename, jd)
                st.metric("ATS预估通过率",f"{res.get('score', '0')}分")
                st.markdown("优化报告")
                st.markdown(res.get("report", "暂无报告"))
                st.download_button("下载报告", res.get("report", ""), "ATS优化报告.txt")
            except Exception as e:
                st.error(f"ATS优化失败：{str(e)}")
        st.markdown('</div>',unsafe_allow_html=True)
    st.markdown("---")
    h1,h2,h3=st.columns([6,2,2])
    with h1:st.subheader("📜 ATS优化历史记录")
    with h2:clear_history("ats_optimizations","ATS优化")
    with h3:
        download_history_report(
            table_name="ats_optimizations",display_name="ATS优化",
            columns_map={"filename":"简历文件名","jd_content":"岗位JD","score":"预估通过率","report":"优化报告","created_at":"创建时间"},
            file_prefix="ATS优化"
        )
    try:
        conn=database.get_conn()
        rec=conn.execute("SELECT filename,score,created_at FROM ats_optimizations ORDER BY id DESC LIMIT 5").fetchall()
        conn.close()
        if rec:
            for r in rec:
                with st.expander(f"{r['filename']} - 预估通过率：{r['score']}分"):
                    st.markdown(f"创建时间：{r['created_at']}")
        else:
            st.info("暂无ATS优化记录")
    except Exception as e:
        st.warning(f"获取ATS优化记录失败：{str(e)}")
    st.markdown('<div class="guide-tip">✅ 对标招聘要求整改简历，提升系统筛选通过率</div>',unsafe_allow_html=True)

elif menu == "🎭 多风格面试模拟":
    st.subheader("🎭 多风格面试官模拟")
    st.markdown("温和HR、压力面试、技术面三种模式随心练习")
    with st.container():
        st.markdown('<div class="card">',unsafe_allow_html=True)
        file=st.file_uploader("上传简历开启模拟面试",type=["pdf","docx"], key="multi_resume_upload")
        style=st.radio("选择面试风格",["温和HR面","严厉压力面","技术大牛面"],horizontal=True, key="interview_style_select")
        if file and not st.session_state.multi_interview_started and st.button("🚀 开始面试"):
            try:
                filename = safe_filename(file.name)
                path=f"uploads/resumes/{filename}"
                with open(path,"wb") as f:f.write(file.getbuffer())
                content=utils.parse_resume(path)
                st.session_state.current_question=agents.multi_style_agent.start(content, filename, style)
                st.session_state.multi_interview_started=True
                st.session_state.multi_finished=False
                st.rerun()
            except Exception as e:
                st.error(f"启动多风格面试失败：{str(e)}")
        if st.session_state.multi_interview_started:
            try:
                st.markdown(f"面试官提问：{st.session_state.current_question}")
                ans=st.text_area("作答区域",height=140, key="multi_answer_input")
                if st.button("提交回答", key="multi_submit_btn") and ans:
                    try:
                        resp, fin = agents.multi_style_agent.answer(ans)
                        st.session_state.current_question = resp
                        st.session_state.multi_finished = fin
                        st.rerun()
                    except Exception as e:
                        st.error(f"提交回答失败：{str(e)}")
                if st.session_state.multi_finished:
                    st.success("面试结束")
                    try:
                        rep=agents.multi_style_agent.get_final_report()
                        st.markdown(rep)
                        st.download_button("下载报告", rep, "多风格面试报告.txt")
                    except Exception as e:
                        st.warning(f"获取最终报告失败：{str(e)}")
            except Exception as e:
                st.warning(f"加载多风格面试失败：{str(e)}")
        st.markdown('</div>',unsafe_allow_html=True)
    st.markdown('<div class="guide-tip">🎬 模拟不同面试官风格，全方位锻炼临场应答能力</div>',unsafe_allow_html=True)

elif menu == "📝 面试复盘":
    st.subheader("📝 结构化面试复盘")
    with st.container():
        st.markdown('<div class="card">',unsafe_allow_html=True)
        talk=st.text_area("粘贴完整面试对话记录",height=280,placeholder="面试官：xxx\n你：xxx", key="review_talk_input")
        if talk and st.button("🚀 生成复盘报告"):
            try:
                rep=agents.review_agent.run(talk)
                st.markdown("### 面试复盘分析")
                st.markdown(rep)
                st.download_button("保存复盘", rep, "面试复盘报告.txt")
            except Exception as e:
                st.error(f"生成复盘报告失败：{str(e)}")
        st.markdown('</div>',unsafe_allow_html=True)
    st.markdown('<div class="guide-tip">📋 录入对话内容，客观分析优缺点并给出改进方向</div>',unsafe_allow_html=True)

elif menu == "🤖 智能面试助手":
    st.markdown("""
    <div style="text-align: center; margin-bottom: 0.5rem;">
        <h2 style="color: #1e40af; margin-bottom: 0.5rem; font-size: 1.8rem;">🤖 智能面试助手</h2>
        <p style="color: #64748b; font-size: 1rem; margin: 0;">自然对话交互，一站式解决各类面试相关问题</p>
    </div>
    """, unsafe_allow_html=True)
    st.markdown(f'<div class="current-model-badge">⚡ 极速模式：智谱清言4-Flash</div>', unsafe_allow_html=True)
    st.markdown("""
    <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; margin-bottom: 1.5rem;">
        <div style="background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%); border-radius: 16px; padding: 1rem; text-align: center; box-shadow: 0 2px 8px rgba(59,130,246,0.08);">
            <div style="font-size: 1.5rem; margin-bottom: 0.5rem;">📄</div>
            <div style="font-weight: 600; color: #1e40af; margin-bottom: 0.3rem;">简历相关</div>
            <div style="font-size: 0.85rem; color: #64748b;">简历评估、ATS优化、求职信生成</div>
        </div>
        <div style="background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%); border-radius: 16px; padding: 1rem; text-align: center; box-shadow: 0 2px 8px rgba(34,197,94,0.08);">
            <div style="font-size: 1.5rem; margin-bottom: 0.5rem;">🎯</div>
            <div style="font-weight: 600; color: #166534; margin-bottom: 0.3rem;">面试练习</div>
            <div style="font-size: 0.85rem; color: #64748b;">面试模拟、多风格面试、录音分析</div>
        </div>
        <div style="background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%); border-radius: 16px; padding: 1rem; text-align: center; box-shadow: 0 2px 8px rgba(245,158,11,0.08);">
            <div style="font-size: 1.5rem; margin-bottom: 0.5rem;">💡</div>
            <div style="font-weight: 600; color: #92400e; margin-bottom: 0.3rem;">求职指导</div>
            <div style="font-size: 0.85rem; color: #64748b;">薪资谈判、职业规划、面试技巧</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("""<div style="margin-bottom: 1rem;"><p style="color: #64748b; font-size: 0.9rem; margin-bottom: 0.8rem;">💬 试试这些问题：</p></div>""", unsafe_allow_html=True)
    col1,col2,col3,col4=st.columns(4)
    with col1:
        if st.button("帮我评估简历", use_container_width=True, key="quick_btn1"):
            st.session_state.quick_question = "帮我评估简历"
            st.rerun()
    with col2:
        if st.button("生成面试题", use_container_width=True, key="quick_btn2"):
            st.session_state.quick_question = "生成面试题"
            st.rerun()
    with col3:
        if st.button("如何回答优缺点", use_container_width=True, key="quick_btn3"):
            st.session_state.quick_question = "如何回答优缺点"
            st.rerun()
    with col4:
        if st.button("薪资谈判技巧", use_container_width=True, key="quick_btn4"):
            st.session_state.quick_question = "薪资谈判技巧"
            st.rerun()
    st.markdown("#### 💬 对话记录")
    chat_container = st.container(height=350, border=True)
    with chat_container:
        for msg in st.session_state.chat_messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
    st.markdown('<div class="custom-chat-form">', unsafe_allow_html=True)
    with st.form(key="chat_form", clear_on_submit=True):
        col_input, col_send = st.columns([10, 1])
        with col_input:
            user_in = st.text_input("",placeholder="输入你的面试问题...",label_visibility="collapsed",key="chat_input_box")
        with col_send:
            submit_button = st.form_submit_button("➤", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
    col_clear, col_download = st.columns(2)
    with col_clear:
        if st.button("🗑️ 清空对话", use_container_width=True, key="clear_chat_btn"):
            st.session_state.chat_messages = []
            st.rerun()
    with col_download:
        if st.session_state.chat_messages:
            try:
                chat_text = ""
                for msg in st.session_state.chat_messages:
                    role = "用户" if msg["role"] == "user" else "助手"
                    chat_text += f"{role}：{msg['content']}\n\n"
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                st.markdown('<div class="download-btn">', unsafe_allow_html=True)
                st.download_button(
                    label="📥 下载聊天记录",
                    data=chat_text,
                    file_name=f"智能面试助手聊天记录_{timestamp}.txt",
                    mime="text/plain",
                    use_container_width=True,
                    key="download_chat_record"
                )
                st.markdown('</div>', unsafe_allow_html=True)
            except Exception as e:
                st.error(f"生成聊天记录失败：{str(e)}")
        else:
            st.info("暂无聊天记录可下载")
    if submit_button and user_in:
        target_page = smart_jump(user_in)
        if target_page:
            st.session_state.pending_jump = target_page
            st.rerun()
        st.session_state.chat_messages.append({"role":"user","content":user_in})
        with chat_container:
            st.chat_message("user").markdown(user_in)
        with chat_container:
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                full_response = ""
                try:
                    # 增加API密钥校验
                    if not global_llm:
                        full_response = "⚠️ 请先在侧边栏输入智谱API密钥！"
                    else:
                        system_prompt = "你是专业的智能面试助手，简洁回答求职面试问题。"
                        full_prompt = f"{system_prompt}\n用户：{user_in}"
                        for chunk in global_llm.stream(full_prompt):
                            full_response += chunk.content if hasattr(chunk, 'content') else str(chunk)
                            message_placeholder.markdown(full_response + "▌")
                    message_placeholder.markdown(full_response)
                except Exception as e:
                    full_response = f"⚠️ 调用失败：{str(e)}\n请检查网络和API密钥。"
                    message_placeholder.markdown(full_response)
        st.session_state.chat_messages.append({"role":"assistant","content":full_response})
        st.rerun()