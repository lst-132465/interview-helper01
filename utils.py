import os
import sys
import tempfile
import shutil
from PyPDF2 import PdfReader
from docx import Document
import whisper
import jieba
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# 全局Whisper模型，懒加载
whisper_model = None

def init_whisper():
    """初始化Whisper模型，自动配置ffmpeg路径"""
    global whisper_model
    if whisper_model is None:
        # 将项目根目录加入系统路径，让Whisper自动找到ffmpeg.exe
        sys.path.append(os.getcwd())
        os.environ["PATH"] += os.pathsep + os.getcwd()
        
        print("正在加载Whisper语音模型（small版，约2GB，技术术语识别更准确）...")
        whisper_model = whisper.load_model("small")
        print("✅ Whisper模型加载完成！")

def parse_resume(file_path):
    """解析PDF和DOCX格式简历"""
    ext = os.path.splitext(file_path)[-1].lower()
    text = ""
    try:
        if ext == ".pdf":
            reader = PdfReader(file_path)
            text = "\n".join([page.extract_text() for page in reader.pages])
        elif ext == ".docx":
            doc = Document(file_path)
            text = "\n".join([p.text for p in doc.paragraphs])
        return text.strip()
    except Exception as e:
        raise Exception(f"简历解析失败：{str(e)}")

def audio_to_text(file_path):
    """语音转文字（简体中文强制输出版，彻底解决繁体问题）"""
    init_whisper()
    
    # 创建临时目录，使用纯英文文件名，解决中文文件名问题
    temp_dir = tempfile.mkdtemp()
    temp_file = os.path.join(temp_dir, "temp_audio.mp3")
    
    try:
        shutil.copy2(file_path, temp_file)
        
        # 转写音频，关闭半精度计算，解决Windows兼容性问题
        result = whisper_model.transcribe(
            temp_file,
            language="zh",  # 修正：使用Whisper官方支持的中文代码
            fp16=False,
            verbose=False,
            beam_size=5,       # 增加搜索宽度，提高识别准确率
            best_of=5,         # 生成多个候选结果，选择最优解
            temperature=0.0,   # 关闭随机性，输出最确定的结果
            initial_prompt="以下是一段简体中文的技术面试录音，内容涉及前端开发、后端开发、数据库等技术话题。"
        )
        
        # 强制转换为简体中文（双重保险）
        from opencc import OpenCC
        cc = OpenCC('t2s')
        simplified_text = cc.convert(result["text"].strip())
        
        return simplified_text
    
    except Exception as e:
        raise Exception(f"语音转写失败：{str(e)}\n💡 请确认ffmpeg.exe已放在项目根目录")
    
    finally:
        # 清理临时文件
        try:
            shutil.rmtree(temp_dir)
        except:
            pass

def check_forbidden(text):
    """检测简历中的违禁词"""
    forbidden_words = ["造假", "伪造", "虚假", "冒充", "谎报", "虚构", "作弊", "抄袭"]
    return [word for word in forbidden_words if word in text]

def calc_similarity(text1, text2):
    """计算两段文本的余弦相似度"""
    try:
        vectorizer = TfidfVectorizer(tokenizer=jieba.lcut, stop_words=["的", "了", "是", "在", "我"])
        tfidf_matrix = vectorizer.fit_transform([text1, text2])
        return cosine_similarity(tfidf_matrix[0], tfidf_matrix[1])[0][0]
    except Exception as e:
        print(f"相似度计算失败：{str(e)}")
        return 0.0