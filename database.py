import sqlite3
import os

DB_FILE = "interview.db"

def get_conn():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    conn = get_conn()
    c = conn.cursor()

    # ========== 原有所有表 100%保留 不做任何修改 ==========
    # 简历评估表（原有）
    c.execute('''CREATE TABLE IF NOT EXISTS resumes
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  filename TEXT, content TEXT, similarity REAL,
                  forbidden_words INTEGER, score REAL, report TEXT,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')

    # 面试录音分析表（原有）
    c.execute('''CREATE TABLE IF NOT EXISTS interviews
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  filename TEXT, transcript TEXT, score REAL, report TEXT,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')

    # 题库表（原有）
    c.execute('''CREATE TABLE IF NOT EXISTS questions
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  question TEXT, answer TEXT, source TEXT,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')

    # 个性化面试题生成历史表（原有）
    c.execute('''CREATE TABLE IF NOT EXISTS generated_questions
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  resume_filename TEXT,
                  questions TEXT,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')

    # 实时面试模拟历史表（原有）
    c.execute('''CREATE TABLE IF NOT EXISTS mock_interviews
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  resume_filename TEXT,
                  final_score REAL,
                  full_report TEXT,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')

    # 求职信生成历史表（原有）
    c.execute('''CREATE TABLE IF NOT EXISTS cover_letters
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  job TEXT,
                  company TEXT,
                  resume_filename TEXT,
                  content TEXT,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')

    # 薪资谈判历史表（原有）
    c.execute('''CREATE TABLE IF NOT EXISTS salary_advice
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  job TEXT,
                  city TEXT,
                  experience INTEGER,
                  content TEXT,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')

    # 职业规划历史表（原有）
    c.execute('''CREATE TABLE IF NOT EXISTS career_plans
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  interest TEXT,
                  resume_filename TEXT,
                  content TEXT,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')

    # ========== 新增3个扩展功能数据表 ==========
    # 1. 简历ATS优化记录表
    c.execute('''CREATE TABLE IF NOT EXISTS ats_optimizations
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  resume_filename TEXT,
                  target_jd TEXT,
                  ats_score REAL,
                  optimization_report TEXT,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')

    # 2. 多风格面试模拟记录表（包含复盘报告）
    c.execute('''CREATE TABLE IF NOT EXISTS multi_style_interviews
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  resume_filename TEXT,
                  interview_style TEXT,
                  conversation_history TEXT,
                  final_score REAL,
                  review_report TEXT,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')

    # 3. 统一智能助手对话历史表
    c.execute('''CREATE TABLE IF NOT EXISTS chat_history
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_message TEXT,
                  assistant_response TEXT,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')

    conn.commit()
    conn.close()

# 初始化数据库
init_database()