from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import uvicorn
import uuid
import os
from pathlib import Path
import pdfplumber
from docx import Document
import shutil
import dashscope
from dashscope import Generation
from config import DASHSCOPE_API_KEY, MODEL_NAME, MAX_TOKENS

# 配置通义千问API密钥
dashscope.api_key = DASHSCOPE_API_KEY

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
    if file_extension == "pdf":
        resume_text = parse_pdf(str(file_path))
    elif file_extension == "docx":
        resume_text = parse_docx(str(file_path))
    
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
    """使用通义千问API分析简历内容"""
    try:
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
        
        # 调用通义千问API
        response = Generation.call(
            model=MODEL_NAME,
            prompt=prompt,
            max_tokens=MAX_TOKENS,
            temperature=0.7
        )
        
        if response.status_code == 200 and response.output and response.output.text:
            return {
                "success": True,
                "analysis": response.output.text,
                "message": "AI分析完成"
            }
        else:
            return {
                "success": False,
                "analysis": "",
                "message": f"AI分析失败：{response.message}"
            }
    except Exception as e:
        return {
            "success": False,
            "analysis": "",
            "message": f"AI分析过程中出现错误：{str(e)}"
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
