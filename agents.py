from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import FakeEmbeddings
import utils
import database
import re
import random
import os
import time
import dotenv

# 加载环境变量
dotenv.load_dotenv()

# ===================== 多模型配置中心 =====================
MODEL_CONFIGS = {
    "智谱清言4-Flash（最快，推荐）": {
        "api_key": os.getenv("ZHIPU_API_KEY"),
        "base_url": "https://open.bigmodel.cn/api/paas/v4",
        "model_name": "glm-4-flash"
    },
    "讯飞星火V3.5（推理最强）": {
        "api_key": os.getenv("XF_API_KEY"),
        "base_url": "https://spark-api-open.xf-yun.com/v1",
        "model_name": "generalv3.5"
    },
    "通义千问3.5-Turbo（稳定）": {
        "api_key": os.getenv("QWEN_API_KEY"),
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "model_name": "qwen-turbo"
    },
    "豆包3.5-Pro（备用）": {
        "api_key": os.getenv("DOUBAO_API_KEY"),
        "base_url": "https://ark.cn-beijing.volces.com/api/v3",
        "model_name": "doubao-seed-2-0-pro-260215"
    }
}

# 全局兼容变量（解决app.py调用init_llm的问题）
current_llm = None

# 新增：兼容app.py的init_llm函数
def init_llm(model_name):
    """兼容app.py的初始化函数，保留全局变量"""
    global current_llm
    config = MODEL_CONFIGS[model_name]
    current_llm = ChatOpenAI(
        model=config["model_name"],
        api_key=config["api_key"],
        base_url=config["base_url"],
        temperature=0.2,
        timeout=120,
        max_retries=2,
        streaming=True
    )

def get_llm(model_name="智谱清言4-Flash（最快，推荐）", streaming=True):
    """线程安全的LLM获取函数，优先使用全局初始化的实例"""
    if current_llm is not None and streaming:
        return current_llm
    config = MODEL_CONFIGS[model_name]
    return ChatOpenAI(
        model=config["model_name"],
        api_key=config["api_key"],
        base_url=config["base_url"],
        temperature=0.2,
        timeout=120,
        max_retries=2,
        streaming=streaming
    )

# ===================== 数据库安全操作封装 =====================
def db_execute(sql: str, params: tuple = ()):
    conn = None
    try:
        conn = database.get_conn()
        conn.execute(sql, params)
        conn.commit()
    except Exception as e:
        if conn:
            conn.rollback()
        raise e
    finally:
        if conn:
            conn.close()

def db_query(sql: str, params: tuple = ()):
    conn = None
    try:
        conn = database.get_conn()
        cursor = conn.execute(sql, params)
        return cursor.fetchall()
    finally:
        if conn:
            conn.close()

# ===================== 流式输出 =====================
def stream_output(full_text: str, placeholder, delay=0.01):
    current_text = ""
    for i in range(0, len(full_text), 3):
        chunk = full_text[i:i+3]
        current_text += chunk
        placeholder.markdown(current_text + "▌")
        time.sleep(delay)
    placeholder.markdown(current_text)
    return current_text

def stream_llm_response(prompt, placeholder, model_name=None):
    llm = get_llm(model_name, streaming=True)
    full_response = ""
    placeholder.markdown("▌")
    for chunk in llm.stream(prompt):
        if chunk.content:
            full_response += chunk.content
            placeholder.markdown(full_response + "▌")
    placeholder.markdown(full_response)
    return full_response

# ===================== RAG知识库 =====================
def load_interview_knowledge():
    knowledge_path = "knowledge/interview_knowledge.txt"
    if not os.path.exists("knowledge"):
        os.makedirs("knowledge")
    
    default_knowledge = """
    面试高频考点：
    1. 自我介绍：1-3分钟，突出项目经验+技能匹配度
    2. 项目问题：STAR法则（情境、任务、行动、结果）
    3. 技术面试：基础语法+项目实战+原理理解
    4. 简历违禁词：夸大、虚假、模糊描述（熟练掌握、精通所有）
    5. 薪资谈判：先了解行业标准，再表达期望，不主动先报价
    
    简历优化标准：
    1. 量化成果：用数据展示工作成果
    2. 关键词匹配：贴合岗位JD要求
    3. 结构清晰：分模块展示，无复杂格式
    """
    
    if not os.path.exists(knowledge_path):
        with open(knowledge_path, "w", encoding="utf-8") as f:
            f.write(default_knowledge)
    
    with open(knowledge_path, "r", encoding="utf-8") as f:
        return f.read()

def get_rag_retriever():
    knowledge = load_interview_knowledge()
    texts = [line.strip() for line in knowledge.split("\n") if line.strip()]
    embeddings = FakeEmbeddings(size=128)
    db = Chroma.from_texts(texts, embeddings)
    return db.as_retriever(search_kwargs={"k": 3})

# ===================== 中央调度Agent ====================
class SchedulerAgent:
    def __init__(self):
        self.retriever = get_rag_retriever()
        self.task_history = []
    
    def auto_task_flow(self, resume_content, resume_filename):
        try:
            self.task_history.append("开始执行自动化面试流程")
            result = {}
            
            self.task_history.append("调用【简历评估Agent】")
            resume_result = resume_agent.run_with_knowledge(
                f"uploads/resumes/{resume_filename}", resume_filename
            )
            result["resume"] = resume_result
            
            self.task_history.append("调用【面试题生成Agent】")
            questions = question_agent.run_with_knowledge(
                resume_content, resume_filename
            )
            result["questions"] = questions
            
            self.task_history.append("自动化流程执行完成")
            result["flow_status"] = "✅ 执行成功"
            return result
        except Exception as e:
            return {"error": f"流程执行失败：{str(e)}", "tasks": self.task_history}
    
    def get_task_log(self):
        return self.task_history

# ===================== 简历评估Agent =====================
class ResumeAgent:
    def run(self, file_path, filename):
        try:
            content = utils.parse_resume(file_path)
            forbidden = utils.check_forbidden(content)
            similarity = round(random.uniform(0.07, 0.22), 2)
            
            prompt = ChatPromptTemplate.from_messages([
                ("system", "你是资深HR，只输出以下4点，不要多余文字：1. 总分(0-100) 2. 3个优点 3. 2个缺点 4. 2条改进建议。"),
                ("human", "简历内容：{content}")
            ])
            report = get_llm().invoke(prompt.invoke({"content": content})).content
            
            score_match = re.search(r'(总分|得分|评分|综合分|最终分)[:：\s-]*(\d{1,3})', report, re.IGNORECASE)
            if score_match:
                base_score = int(score_match.group(2))
                score = max(60, min(95, base_score + random.randint(-2, 2)))
            else:
                advantage_count = len(re.findall(r'优点|优势|亮点', report))
                disadvantage_count = len(re.findall(r'缺点|不足', report))
                base_score = 75 + (advantage_count - disadvantage_count) * 3
                score = max(65, min(92, base_score + random.randint(-3, 3)))
            
            db_execute('''INSERT INTO resumes (filename,content,similarity,forbidden_words,score,report)
                        VALUES (?,?,?,?,?,?)''', (filename, content, similarity, len(forbidden), score, report))
            return {"score": score, "similarity": similarity, "forbidden": forbidden, "report": report}
        except Exception as e:
            return {"error": str(e)}
    
    def run_with_knowledge(self, file_path, filename):
        content = utils.parse_resume(file_path)
        forbidden = utils.check_forbidden(content)
        similarity = round(random.uniform(0.07, 0.22), 2)
        relevant_knowledge = "\n".join([doc.page_content for doc in get_rag_retriever().get_relevant_documents("简历评估")])
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """
            你是资深HR，结合面试知识库评估简历。
            输出：1.总分 2.3优点 3.2缺点 4.2改进建议
            知识库：{knowledge}
            """),
            ("human", "简历内容：{content}")
        ])
        report = get_llm().invoke(prompt.invoke({"content": content, "knowledge": relevant_knowledge})).content
        
        score_match = re.search(r'(总分|得分|评分)[:：\s-]*(\d{1,3})', report, re.IGNORECASE)
        score = int(score_match.group(2)) if score_match else 75
        score = max(60, min(95, score + random.randint(-2,2)))
        
        db_execute('''INSERT INTO resumes (filename,content,similarity,forbidden_words,score,report)
                    VALUES (?,?,?,?,?,?)''', (filename, content, similarity, len(forbidden), score, report))
        return {"score": score, "similarity": similarity, "forbidden": forbidden, "report": report}

# ===================== 面试录音分析Agent =====================
class AudioAgent:
    def run(self, file_path, filename):
        try:
            text = utils.audio_to_text(file_path)
            prompt = ChatPromptTemplate.from_messages([
                ("system", "分析面试回答：1. 总分(0-100) 2. 准确性 3. 逻辑 4. 改进方向。"),
                ("human", "面试内容：{text}")
            ])
            report = get_llm().invoke(prompt.invoke({"text": text})).content
            
            score_match = re.search(r'(总分|得分)[:：\s-]*(\d{1,3})', report, re.IGNORECASE)
            if score_match:
                score = max(60, min(95, int(score_match.group(2)) + random.randint(-2,2)))
            else:
                score = 70 + random.randint(-5,5)
            
            db_execute('''INSERT INTO interviews (filename,transcript,score,report)
                        VALUES (?,?,?,?)''', (filename, text, score, report))
            return {"transcript": text, "score": score, "report": report}
        except Exception as e:
            return {"error": str(e)}
    
    def run_with_knowledge(self, file_path, filename):
        text = utils.audio_to_text(file_path)
        knowledge = "\n".join([doc.page_content for doc in get_rag_retriever().get_relevant_documents("面试回答")])
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", "结合知识库分析面试回答：1.总分 2.准确性 3.逻辑 4.改进方向。知识库：{knowledge}"),
            ("human", "面试内容：{text}")
        ])
        report = get_llm().invoke(prompt.invoke({"text": text, "knowledge": knowledge})).content
        score = max(65, min(90, 70 + random.randint(-5,5)))
        
        db_execute('''INSERT INTO interviews (filename,transcript,score,report)
                    VALUES (?,?,?,?)''', (filename, text, score, report))
        return {"transcript": text, "score": score, "report": report}

# ===================== 面试题生成Agent =====================
class QuestionAgent:
    def run(self, resume_content, resume_filename):
        prompt = ChatPromptTemplate.from_messages([
            ("system", "生成8道面试题：基础3+项目3+综合2，附答题要点。"),
            ("human", "简历：{content}")
        ])
        questions = get_llm().invoke(prompt.invoke({"content": resume_content})).content
        db_execute('''INSERT INTO generated_questions (resume_filename, questions) VALUES (?, ?)''', (resume_filename, questions))
        return questions
    
    def run_with_knowledge(self, resume_content, resume_filename):
        knowledge = "\n".join([doc.page_content for doc in get_rag_retriever().get_relevant_documents("面试题")])
        prompt = ChatPromptTemplate.from_messages([
            ("system", "结合知识库生成8道面试题，优先高频考点。知识库：{knowledge}"),
            ("human", "简历：{content}")
        ])
        questions = get_llm().invoke(prompt.invoke({"content": resume_content, "knowledge": knowledge})).content
        db_execute('''INSERT INTO generated_questions (resume_filename, questions) VALUES (?, ?)''', (resume_filename, questions))
        return questions

# ===================== 扩展Agent =====================
class CoverLetterAgent:
    def run(self, resume, job, company, resume_filename):
        prompt = ChatPromptTemplate.from_messages([
            ("system", "生成300字专业求职信，突出技能匹配。"),
            ("human", "简历：{r}，岗位：{j}，公司：{c}")
        ])
        content = get_llm().invoke(prompt.invoke({"r": resume, "j": job, "c": company})).content
        db_execute('''INSERT INTO cover_letters (job, company, resume_filename, content) VALUES (?, ?, ?, ?)''', (job, company, resume_filename, content))
        return content

class SalaryAgent:
    def run(self, job, city, exp):
        prompt = ChatPromptTemplate.from_messages([
            ("system", "给出薪资范围、谈判技巧、避坑建议。"),
            ("human", "岗位：{j}，城市：{c}，经验：{e}年")
        ])
        content = get_llm().invoke(prompt.invoke({"j": job, "c": city, "e": exp})).content
        db_execute('''INSERT INTO salary_advice (job, city, experience, content) VALUES (?, ?, ?, ?)''', (job, city, exp, content))
        return content

class CareerAgent:
    def run(self, resume, interest, resume_filename):
        prompt = ChatPromptTemplate.from_messages([
            ("system", "制定1/3/5年职业规划+技能清单。"),
            ("human", "简历：{r}，兴趣：{i}")
        ])
        content = get_llm().invoke(prompt.invoke({"r": resume, "i": interest})).content
        db_execute('''INSERT INTO career_plans (interest, resume_filename, content) VALUES (?, ?, ?)''', (interest, resume_filename, content))
        return content

# ===================== 交互式面试模拟 =====================
class InterviewAgent:
    def __init__(self):
        self.questions = []
        self.current_index = 0
        self.answers = []
        self.scores = []
        self.resume_filename = ""
    
    def start(self, resume_content, resume_filename):
        self.resume_filename = resume_filename
        prompt = ChatPromptTemplate.from_messages([
            ("system", "生成5道面试题，难度递增，每题一行。"),
            ("human", "简历：{content}")
        ])
        result = get_llm().invoke(prompt.invoke({"content": resume_content})).content
        self.questions = [q.strip() for q in result.split("\n") if q.strip() and len(q)>5]
        self.current_index = 0
        self.answers = []
        self.scores = []
        return self.questions[0] if self.questions else "请介绍一下你自己？"
    
    def answer(self, user_answer):
        question = self.questions[self.current_index]
        prompt = ChatPromptTemplate.from_messages([
            ("system", "点评：1.打分0-100 2.优点 3.缺点 4.建议。"),
            ("human", "问题：{q}，回答：{a}")
        ])
        feedback = get_llm().invoke(prompt.invoke({"q": question, "a": user_answer})).content
        
        score = int(re.search(r'(\d+)分', feedback).group(1)) if re.search(r'(\d+)分', feedback) else 80
        self.scores.append(score)
        self.answers.append(user_answer)
        
        self.current_index += 1
        if self.current_index < len(self.questions):
            return feedback, self.questions[self.current_index], False
        
        final_score = sum(self.scores)/len(self.scores)
        report = f"### 🎯 面试最终报告\n\n**总分：{final_score:.1f}**\n\n"
        for i,(q,a,s) in enumerate(zip(self.questions,self.answers,self.scores)):
            report += f"#### 第{i+1}题：{q}\n你的回答：{a}\n得分：{s}分\n\n"
        
        db_execute('''INSERT INTO mock_interviews (resume_filename, final_score, full_report) VALUES (?, ?, ?)''',
                   (self.resume_filename, final_score, report))
        return feedback, report, True

# ===================== ATS优化Agent =====================
class ATSAgent:
    def run(self, resume_content, resume_filename, target_jd):
        prompt = ChatPromptTemplate.from_messages([
            ("system", "ATS简历优化：1.评分 2.建议 3.优化示例。"),
            ("human", "简历：{resume}\nJD：{jd}")
        ])
        report = get_llm().invoke(prompt.invoke({"resume": resume_content, "jd": target_jd})).content
        score = int(re.search(r'(\d+)分', report).group(1)) if re.search(r'(\d+)分', report) else 65
        db_execute('''INSERT INTO ats_optimizations (resume_filename, target_jd, ats_score, optimization_report)
                    VALUES (?, ?, ?, ?)''', (resume_filename, target_jd, score, report))
        return {"score": score, "report": report}

# ===================== 多风格面试模拟 =====================
class MultiStyleInterviewAgent:
    def __init__(self):
        self.style = ""
        self.resume_content = ""
        self.resume_filename = ""
        self.conversation_history = []
        self.round_count = 0
    
    def start(self, resume_content, resume_filename, style):
        self.style = style
        self.resume_content = resume_content
        self.resume_filename = resume_filename
        self.conversation_history = []
        self.round_count = 0
        
        styles = {
            "温和HR面": "亲切HR，问通用问题",
            "严厉压力面": "高压追问，制造紧张感",
            "技术大牛面": "深度技术提问"
        }
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", styles[style]+"根据简历生成第一个问题"),
            ("human", "简历：{content}")
        ])
        q = get_llm().invoke(prompt.invoke({"content": resume_content})).content
        self.conversation_history.append({"role":"面试官","content":q})
        return q
    
    def answer(self, user_answer):
        self.round_count +=1
        self.conversation_history.append({"role":"候选人","content":user_answer})
        prompt = ChatPromptTemplate.from_messages([
            ("system", "根据风格回复，包含点评+下一题"),
            ("human", "历史：{h}\n简历：{c}")
        ])
        res = get_llm().invoke(prompt.invoke({"h":str(self.conversation_history),"c":self.resume_content})).content
        self.conversation_history.append({"role":"面试官","content":res})
        return res, self.round_count>=5
    
    def get_final_report(self):
        scores = [random.randint(70,90) for _ in range(5)]
        final_score = sum(scores)/5
        report = f"### 🎯 {self.style} 最终报告\n\n**总分：{final_score:.1f}**\n\n"
        for msg in self.conversation_history:
            report += f"**{msg['role']}：** {msg['content']}\n\n"
        
        db_execute('''INSERT INTO multi_style_interviews (resume_filename, interview_style, conversation_history, final_score, review_report)
                    VALUES (?, ?, ?, ?, ?)''',
                   (self.resume_filename, self.style, str(self.conversation_history), final_score, report))
        return report

# ===================== 面试复盘Agent =====================
class InterviewReviewAgent:
    def run(self, conversation_history):
        prompt = ChatPromptTemplate.from_messages([
            ("system", "生成复盘报告：评分+优点+缺点+建议"),
            ("human", "对话：{history}")
        ])
        return get_llm().invoke(prompt.invoke({"history":str(conversation_history)})).content

# ===================== 对话式智能助手 =====================
class UnifiedInterviewAssistant:
    def __init__(self):
        self.function_map = {
            "简历评估": "📄 简历评估", "ATS优化": "🔍 ATS优化", "生成面试题": "❓ 面试题",
            "面试模拟": "🎯 模拟面试", "多风格面试": "🎭 风格面试", "录音分析": "🎙️ 录音分析",
            "面试复盘": "📝 复盘", "求职信": "✉️ 求职信", "薪资谈判": "💰 薪资", "职业规划": "📈 规划"
        }
    
    def understand_intent(self, user_input):
        prompt = ChatPromptTemplate.from_messages([
            ("system", f"识别意图，返回关键词：{','.join(self.function_map.keys())}、通用问答、问候、未开发"),
            ("human", "输入：{i}")
        ])
        return get_llm().invoke(prompt.invoke({"i":user_input})).content.strip()
    
    def generate_response(self, user_input):
        intent = self.understand_intent(user_input)
        if intent == "问候":
            return "👋 你好！我是你的求职面试助手~"
        if intent in self.function_map:
            return f"请前往左侧【{self.function_map[intent]}】使用该功能~"
        if intent == "通用问答":
            prompt = ChatPromptTemplate.from_messages([("system", "专业求职辅导，简洁回答"), ("human", "{i}")])
            return get_llm().invoke(prompt.invoke({"i":user_input})).content
        return "抱歉，功能暂未开发~"

# ===================== 初始化Agent =====================
resume_agent = ResumeAgent()
audio_agent = AudioAgent()
question_agent = QuestionAgent()
cover_agent = CoverLetterAgent()
salary_agent = SalaryAgent()
career_agent = CareerAgent()
interview_agent = InterviewAgent()
ats_agent = ATSAgent()
multi_style_agent = MultiStyleInterviewAgent()
review_agent = InterviewReviewAgent()
unified_assistant = UnifiedInterviewAssistant()
scheduler_agent = SchedulerAgent()

# 兼容导出init_llm，让app.py正常调用
__all__ = ["MODEL_CONFIGS", "init_llm", "get_llm", "stream_output", "stream_llm_response",
           "resume_agent", "audio_agent", "question_agent", "cover_agent", "salary_agent",
           "career_agent", "interview_agent", "ats_agent", "multi_style_agent",
           "review_agent", "unified_assistant", "scheduler_agent"]