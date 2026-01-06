from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import uvicorn
import uuid
import os
import sys
from pathlib import Path
import pdfplumber
from docx import Document
import shutil
from openai import OpenAI

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.config.config import SILICONFLOW_API_KEY, SILICONFLOW_BASE_URL, MODEL_NAME, MAX_TOKENS, temperature

# 配置硅基流动API
client = OpenAI(
    api_key=SILICONFLOW_API_KEY,
    base_url=SILICONFLOW_BASE_URL,
)

app = FastAPI(
    title="智能面试辅助平台 API",
    description="提供简历分析和AI模拟面试功能",
    version="0.1.0"
)

# 确保临时目录存在
TEMP_DIR = Path("./temp")
TEMP_DIR.mkdir(exist_ok=True)

# 简历数据存储（临时使用内存存储，后续将迁移到数据库）
resumes = {}

@app.get("/")
async def root():
    return {"message": "欢迎使用智能面试辅助平台 API！"}

@app.post("/api/v1/resume/upload")
async def upload_resume(file: UploadFile = File(...)):
    """上传简历文件"""
    allowed_extensions = {".pdf", ".docx"}
    file_extension = file.filename.split(".")[-1].lower()
    if f".{file_extension}" not in allowed_extensions:
        raise HTTPException(status_code=400, detail="仅支持 PDF 和 DOCX 格式的简历文件")
    
    # 生成唯一的简历ID
    resume_id = str(uuid.uuid4())
    
    # 保存文件到临时目录
    file_path = TEMP_DIR / f"{resume_id}.{file_extension}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # 解析简历内容
    resume_text = ""
    try:
        if file_extension == "pdf":
            resume_text = parse_pdf(str(file_path))
        elif file_extension == "docx":
            resume_text = parse_docx(str(file_path))
        
        if not resume_text:
            raise HTTPException(status_code=400, detail=f"无法解析{file_extension.upper()}文件内容，请确保文件有效且包含文本")
    except Exception as e:
        # 清理无效文件
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=400, detail=f"解析文件失败: {str(e)}")
    
    # 保存简历信息
    resumes[resume_id] = {
        "filename": file.filename,
        "file_path": str(file_path),
        "text": resume_text,
        "status": "uploaded"
    }
    
    return JSONResponse({
        "resume_id": resume_id,
        "filename": file.filename,
        "message": "简历上传并解析成功",
        "content_length": len(resume_text)
    })

def parse_pdf(file_path: str) -> str:
    """解析PDF格式的简历"""
    text = ""
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text

def parse_docx(file_path: str) -> str:
    """解析DOCX格式的简历"""
    text = ""
    doc = Document(file_path)
    for paragraph in doc.paragraphs:
        if paragraph.text:
            text += paragraph.text + "\n"
    return text

def analyze_resume_with_ai(resume_text: str) -> dict:
    """使用硅基流动API分析简历内容"""
    # 检查API密钥是否为默认值
    if SILICONFLOW_API_KEY == "your-api-key-here":
        return {
            "success": False,
            "analysis": "",
            "message": "AI分析失败：请先在backend/config/config.py中配置有效的SILICONFLOW_API_KEY"
        }
    
    try:
        print(f"[DEBUG] 开始AI分析，使用模型: {MODEL_NAME}")
        # 构建分析prompt
        prompt = f"""请作为专业的简历分析师，分析以下简历内容，并提供详细的分析报告：

{resume_text}

分析报告应包括：
1. 简历的整体结构和组织情况
2. 优势和亮点
3. 需要改进的地方
4. 针对软件工程师岗位的匹配度评估
5. 具体的优化建议

请用中文回复，语言简洁专业，重点突出。"""
        
        # 调用硅基流动API
        print(f"[DEBUG] 调用硅基流动API，prompt长度: {len(prompt)}")
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "你是一位专业的简历分析师。"},
                {"role": "user", "content": prompt}
            ],
            max_tokens=MAX_TOKENS,
            temperature=temperature
        )
        
        print(f"[DEBUG] API响应: {response}")
        if response.choices and response.choices[0].message.content:
            return {
                "success": True,
                "analysis": response.choices[0].message.content,
                "message": "AI分析完成"
            }
        else:
            return {
                "success": False,
                "analysis": "",
                "message": "AI分析失败：未获取到有效响应内容"
            }
    except Exception as e:
        error_msg = str(e)
        print(f"[ERROR] AI分析出错: {error_msg}")
        
        # 提供更友好的错误信息
        if "401" in error_msg or "Invalid token" in error_msg:
            return {
                "success": False,
                "analysis": "",
                "message": "AI分析失败：API密钥无效，请检查backend/config/config.py中的SILICONFLOW_API_KEY配置"
            }
        elif "403" in error_msg:
            return {
                "success": False,
                "analysis": "",
                "message": "AI分析失败：API访问被拒绝，请检查API密钥的权限设置"
            }
        elif "429" in error_msg:
            return {
                "success": False,
                "analysis": "",
                "message": "AI分析失败：API请求频率过高，请稍后再试"
            }
        else:
            return {
                "success": False,
                "analysis": "",
                "message": f"AI分析过程中出现错误：{error_msg}"
            }

@app.post("/api/v1/resume/analyze")
async def analyze_resume(resume_id: str):
    """分析简历内容"""
    if resume_id not in resumes:
        raise HTTPException(status_code=404, detail="未找到该简历ID")
    
    resume = resumes[resume_id]
    resume["status"] = "analyzing"
    
    # 调用AI分析简历
    ai_result = analyze_resume_with_ai(resume["text"])
    
    if ai_result["success"]:
        resume["status"] = "analyzed"
        resume["analysis"] = ai_result["analysis"]
        
        return JSONResponse({
            "resume_id": resume_id,
            "filename": resume["filename"],
            "text_preview": resume["text"][:500] + ("..." if len(resume["text"]) > 500 else ""),
            "content_length": len(resume["text"]),
            "analysis": ai_result["analysis"],
            "message": "简历分析完成",
            "status": "analyzed"
        })
    else:
        resume["status"] = "analysis_failed"
        
        # 返回分析失败的响应，包含原始简历文本供参考
        return JSONResponse({
            "resume_id": resume_id,
            "filename": resume["filename"],
            "text_preview": resume["text"][:500] + ("..." if len(resume["text"]) > 500 else ""),
            "content_length": len(resume["text"]),
            "analysis": "",
            "message": ai_result["message"],
            "status": "analysis_failed"
        })

@app.get("/api/v1/resume/{resume_id}")
async def get_resume(resume_id: str):
    """获取简历详情"""
    if resume_id not in resumes:
        raise HTTPException(status_code=404, detail="未找到该简历ID")
    
    resume = resumes[resume_id]
    return JSONResponse({
        "resume_id": resume_id,
        "filename": resume["filename"],
        "status": resume["status"]
    })

@app.post("/api/v1/interview/start")
async def start_interview(job_title: str):
    """开始AI模拟面试"""
    # 后续将添加面试生成逻辑
    return JSONResponse({
        "job_title": job_title,
        "message": "面试生成功能待实现"
    })

@app.post("/api/v1/interview/answer")
async def submit_answer(interview_id: str, answer: str):
    """提交面试答案"""
    # 后续将添加答案评估逻辑
    return JSONResponse({
        "interview_id": interview_id,
        "message": "答案评估功能待实现"
    })

import sys

if __name__ == "__main__":
    port = 8000
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            pass
    uvicorn.run(app, host="0.0.0.0", port=port)
