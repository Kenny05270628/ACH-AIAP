from fastapi import FastAPI, UploadFile, File, HTTPException, Body
from pydantic import BaseModel
from fastapi.responses import JSONResponse
import uvicorn
import uuid
import os
import sys
import json
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

# Pydantic模型定义
class InterviewRequest(BaseModel):
    job_title: str
    resume_id: str = None

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
            "scores": {},
            "message": "AI分析失败：请先在backend/config/config.py中配置有效的SILICONFLOW_API_KEY"
        }
    
    try:
        print(f"[DEBUG] 开始AI分析，使用模型: {MODEL_NAME}")
        # 构建分析prompt
        prompt = f"""请作为专业的简历分析师，分析以下简历内容，并提供详细的分析报告和多维度评分：

{resume_text}

请按照以下要求提供分析结果：
1. 分析报告应包括：
   - 简历的整体结构和组织情况
   - 优势和亮点
   - 需要改进的地方
   - 针对软件工程师岗位的匹配度评估
   - 具体的优化建议

2. 多维度评分应包括以下6个维度，每个维度评分范围为0-100分：
   - 专业技能
   - 项目经验
   - 教育背景
   - 工作经验
   - 沟通能力
   - 学习能力

请以JSON格式返回分析结果，JSON结构如下：
{{
  "analysis": "[详细分析报告内容]",
  "scores": {{
    "专业技能": 85,
    "项目经验": 78,
    "教育背景": 82,
    "工作经验": 88,
    "沟通能力": 75,
    "学习能力": 80
  }}
}}

请确保返回的内容是有效的JSON格式，不要包含任何额外的说明文字。"""
        
        # 调用硅基流动API
        print(f"[DEBUG] 调用硅基流动API，prompt长度: {len(prompt)}")
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "你是一位专业的简历分析师，能够提供结构化的简历分析和多维度评分。"},
                {"role": "user", "content": prompt}
            ],
            max_tokens=MAX_TOKENS,
            temperature=temperature
        )
        
        print(f"[DEBUG] API响应: {response}")
        if response.choices and response.choices[0].message.content:
            ai_content = response.choices[0].message.content
            try:
                # 解析JSON格式的响应
                result = json.loads(ai_content)
                return {
                    "success": True,
                    "analysis": result.get("analysis", ""),
                    "scores": result.get("scores", {}),
                    "message": "AI分析完成"
                }
            except json.JSONDecodeError as e:
                print(f"[ERROR] 解析AI分析结果JSON失败: {e}")
                return {
                    "success": False,
                    "analysis": "",
                    "scores": {},
                    "message": f"AI分析失败：返回内容解析错误，原始响应：{ai_content}"
                }
        else:
            return {
                "success": False,
                "analysis": "",
                "scores": {},
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
                "scores": {},
                "message": "AI分析失败：API密钥无效，请检查backend/config/config.py中的SILICONFLOW_API_KEY配置"
            }
        elif "403" in error_msg:
            return {
                "success": False,
                "analysis": "",
                "scores": {},
                "message": "AI分析失败：API访问被拒绝，请检查API密钥的权限设置"
            }
        elif "429" in error_msg:
            return {
                "success": False,
                "analysis": "",
                "scores": {},
                "message": "AI分析失败：API请求频率过高，请稍后再试"
            }
        else:
            return {
                "success": False,
                "analysis": "",
                "scores": {},
                "message": f"AI分析过程中出现错误：{error_msg}"
            }

def generate_interview_questions(job_title: str, resume_text: str = "") -> dict:
    """使用硅基流动API生成面试问题"""
    # 检查API密钥是否为默认值
    if SILICONFLOW_API_KEY == "your-api-key-here":
        return {
            "success": False,
            "questions": [],
            "message": "面试问题生成失败：请先在backend/config/config.py中配置有效的SILICONFLOW_API_KEY"
        }
    
    try:
        print(f"[DEBUG] 开始生成面试问题，岗位: {job_title}，使用模型: {MODEL_NAME}")
        
        # 构建生成面试问题的prompt
        if resume_text:
            prompt = f"""请作为专业的{job_title}面试官，基于以下简历内容，生成10个结构化的面试问题：

简历内容：
{resume_text}

请按照以下要求生成问题：
1. 问题应覆盖{job_title}岗位的核心技能、专业知识和相关经验
2. 问题类型应包括：技术问题、行为问题和项目经验问题
3. 问题难度应从基础到进阶递进
4. 每个问题应清晰明了，针对性强
5. 请以JSON数组格式返回问题，每个问题包含'question'和'type'（技术/行为/项目）字段
6. 问题语言为中文

示例输出格式：
[{{"question": "请简要介绍你在{job_title}领域的工作经验", "type": "行为"}},
 {{"question": "请解释{job_title}领域的某个核心概念", "type": "技术"}}]
"""
        else:
            prompt = f"""请作为专业的{job_title}面试官，生成10个结构化的面试问题：

请按照以下要求生成问题：
1. 问题应覆盖{job_title}岗位的核心技能、专业知识和相关经验
2. 问题类型应包括：技术问题、行为问题和项目经验问题
3. 问题难度应从基础到进阶递进
4. 每个问题应清晰明了，针对性强
5. 请以JSON数组格式返回问题，每个问题包含'question'和'type'（技术/行为/项目）字段
6. 问题语言为中文

示例输出格式：
[{{"question": "请简要介绍你在{job_title}领域的工作经验", "type": "行为"}},
 {{"question": "请解释{job_title}领域的某个核心概念", "type": "技术"}}]
"""
        
        # 调用硅基流动API
        print(f"[DEBUG] 调用硅基流动API生成面试问题，prompt长度: {len(prompt)}")
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": f"你是一位专业的{job_title}面试官，擅长生成结构化、针对性强的面试问题。"},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,  # 适当减少token数，因为只需要10个问题
            temperature=temperature
        )
        
        print(f"[DEBUG] API响应: {response}")
        if response.choices and response.choices[0].message.content:
            # 解析返回的JSON格式问题
            questions_content = response.choices[0].message.content
            try:
                questions = json.loads(questions_content)
                return {
                    "success": True,
                    "questions": questions,
                    "message": "面试问题生成完成"
                }
            except json.JSONDecodeError as e:
                print(f"[ERROR] 解析面试问题JSON失败: {e}")
                return {
                    "success": False,
                    "questions": [],
                    "message": f"面试问题生成失败：返回内容解析错误，原始响应：{questions_content}"
                }
        else:
            return {
                "success": False,
                "questions": [],
                "message": "面试问题生成失败：未获取到有效响应内容"
            }
    except Exception as e:
        error_msg = str(e)
        print(f"[ERROR] 生成面试问题出错: {error_msg}")
        
        # 提供更友好的错误信息
        if "401" in error_msg or "Invalid token" in error_msg:
            return {
                "success": False,
                "questions": [],
                "message": "面试问题生成失败：API密钥无效，请检查backend/config/config.py中的SILICONFLOW_API_KEY配置"
            }
        elif "403" in error_msg:
            return {
                "success": False,
                "questions": [],
                "message": "面试问题生成失败：API访问被拒绝，请检查API密钥的权限设置"
            }
        elif "429" in error_msg:
            return {
                "success": False,
                "questions": [],
                "message": "面试问题生成失败：API请求频率过高，请稍后再试"
            }
        else:
            return {
                "success": False,
                "questions": [],
                "message": f"面试问题生成过程中出现错误：{error_msg}"
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
        resume["scores"] = ai_result.get("scores", {})
        
        return JSONResponse({
            "resume_id": resume_id,
            "filename": resume["filename"],
            "text_preview": resume["text"][:500] + ("..." if len(resume["text"]) > 500 else ""),
            "content_length": len(resume["text"]),
            "analysis": ai_result["analysis"],
            "scores": ai_result.get("scores", {}),
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
            "scores": {},
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
async def start_interview(request: InterviewRequest):
    """开始AI模拟面试"""
    job_title = request.job_title
    resume_id = request.resume_id
    resume_text = ""
    
    # 如果提供了简历ID，获取简历内容
    if resume_id:
        if resume_id not in resumes:
            return JSONResponse(
                {
                    "success": False,
                    "job_title": job_title,
                    "message": "未找到指定的简历ID"
                },
                status_code=404
            )
        resume_text = resumes[resume_id].get("text", "")
    
    # 调用AI生成面试问题
    ai_result = generate_interview_questions(job_title, resume_text)
    
    if ai_result["success"]:
        # 生成面试ID
        interview_id = str(uuid.uuid4())
        
        # 返回成功响应，包含面试问题
        return JSONResponse({
            "success": True,
            "interview_id": interview_id,
            "job_title": job_title,
            "questions": ai_result["questions"],
            "message": "面试问题生成成功"
        })
    else:
        # 返回失败响应
        return JSONResponse(
            {
                "success": False,
                "job_title": job_title,
                "questions": [],
                "message": ai_result["message"]
            },
            status_code=500
        )

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
