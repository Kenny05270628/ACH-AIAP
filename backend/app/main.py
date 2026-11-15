from fastapi import FastAPI, UploadFile, File, HTTPException, Body, Query
from pydantic import BaseModel
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
import uuid
import os
import sys
import json
import re
from pathlib import Path
import pdfplumber
from docx import Document
import shutil
from openai import OpenAI

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.config.config import SILICONFLOW_API_KEY, SILICONFLOW_BASE_URL, MODEL_NAME, MAX_TOKENS, temperature
from backend.app import repository
from backend.app.db import init_db, close_db

# 配置硅基流动API
client = OpenAI(
    api_key=SILICONFLOW_API_KEY,
    base_url=SILICONFLOW_BASE_URL,
)

# API 密钥是否已配置（来自 .env 或环境变量）
API_KEY_CONFIGURED = bool(SILICONFLOW_API_KEY) and SILICONFLOW_API_KEY != "your-api-key-here"

# Pydantic模型定义
class InterviewRequest(BaseModel):
    job_title: str
    resume_id: str = None


class AnswerRequest(BaseModel):
    interview_id: str
    question: str
    question_index: int = 0
    answer: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield
    close_db()


app = FastAPI(
    title="智能面试辅助平台 API",
    description="提供简历分析和AI模拟面试功能",
    version="0.1.0",
    lifespan=lifespan
)

# 配置CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 确保临时目录存在
TEMP_DIR = Path("./temp")
TEMP_DIR.mkdir(exist_ok=True)

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
    repository.create_resume(
        resume_id=resume_id,
        filename=file.filename,
        file_path=str(file_path),
        content_text=resume_text
    )
    
    return JSONResponse({
        "resume_id": resume_id,
        "filename": file.filename,
        "message": "简历上传并解析成功",
        "content_length": len(resume_text),
        "text_preview": resume_text[:500] + ("..." if len(resume_text) > 500 else "")
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

def _repair_json_text(text: str) -> str:
    """修复AI返回JSON中的常见问题：
    1. 字符串内部未转义的换行/制表符等控制字符
    2. 非法转义序列（如 \\d）
    """
    result = []
    in_string = False
    valid_escapes = set('"\\/bfnrtu')
    i = 0
    length = len(text)

    while i < length:
        ch = text[i]

        if not in_string:
            result.append(ch)
            if ch == '"':
                in_string = True
            i += 1
            continue

        if ch == '\\':
            nxt = text[i + 1] if i + 1 < length else ''
            if nxt in valid_escapes:
                result.append(ch)
                result.append(nxt)
                i += 2
                continue
            # 非法转义：补一个反斜杠，保留原字符
            result.append('\\\\')
            i += 1
            continue

        if ch == '"':
            in_string = False
            result.append(ch)
        elif ch == '\n':
            result.append('\\n')
        elif ch == '\r':
            result.append('\\r')
        elif ch == '\t':
            result.append('\\t')
        elif ord(ch) < 0x20:
            result.append(f'\\u{ord(ch):04x}')
        else:
            result.append(ch)
        i += 1

    return ''.join(result)


def analyze_resume_with_ai(resume_text: str) -> dict:
    """使用硅基流动API分析简历内容"""
    # 检查API密钥是否已配置
    if not API_KEY_CONFIGURED:
        return {
            "success": False,
            "analysis": "",
            "scores": {},
            "message": "AI分析失败：请先在项目根目录 .env 中配置有效的 SILICONFLOW_API_KEY"
        }
    
    try:
        print(f"[DEBUG] 开始AI分析，使用模型: {MODEL_NAME}")
        # 构建分析prompt
        prompt = f"""请作为专业的简历分析师，分析以下简历内容，并提供详细的分析报告和多维度评分：

{resume_text}

分析报告的 "analysis" 字段请使用 Markdown 分段输出，每部分单独成行，包含以下小节：
## 整体结构与组织
## 优势与亮点
## 需要改进的地方
## 岗位匹配度
## 优化建议
其中“优化建议”必须用 1. 2. 3. 分条列出，每部分之间使用换行分隔。

评分要求：每项为 0-100 的整数，必须依据简历中的实际证据计算，禁止套用固定模板分数，各维度之间应有区分度。
- 专业技能：技术栈的广度与深度、与软件工程师岗位的匹配度
- 项目经验：项目规模与复杂度、个人承担的角色和实际产出
- 教育背景：学历层次、院校与专业的相关性
- 工作经验：工作年限、职责范围与成长轨迹
- 沟通能力：简历中体现的协作、跨团队沟通、文档与表达能力；证据不足时给低分并在报告中说明
- 学习能力：新技术掌握情况、认证、持续学习与成长迹象

请只返回如下结构的 JSON，不要输出任何其他文字；其中 <整数> 为占位符，需替换为实际分数：
{{
  "analysis": "分析报告正文",
  "scores": {{
    "专业技能": <整数>,
    "项目经验": <整数>,
    "教育背景": <整数>,
    "工作经验": <整数>,
    "沟通能力": <整数>,
    "学习能力": <整数>
  }}
}}
"""
        
        # 调用硅基流动API
        print(f"[DEBUG] 调用硅基流动API，prompt长度: {len(prompt)}")
        
        # 构建API参数
        api_params = {
            "model": MODEL_NAME,
            "messages": [
                {"role": "system", "content": "你是一位专业的简历分析师，能够提供结构化的简历分析和多维度评分。"},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 2048,  # 减少token限制，加快响应速度
            "temperature": 0.3,   # 降低随机性，保证评分稳定
            "response_format": {"type": "json_object"}  # 强制JSON格式输出
        }
        
        # 如果是推理模型(Qwen3.5系列)，禁用思考模式以加快响应
        if "Qwen3.5" in MODEL_NAME:
            api_params["extra_body"] = {"thinking": {"type": "disabled"}}
        
        response = client.chat.completions.create(**api_params)
        
        print(f"[DEBUG] API响应: {response}")
        if response.choices and response.choices[0].message.content:
            ai_content = response.choices[0].message.content
            print(f"[DEBUG] AI返回的原始内容: '{ai_content}'")
            print(f"[DEBUG] 内容长度: {len(ai_content)}")
            print(f"[DEBUG] 内容类型: {type(ai_content)}")
            print(f"[DEBUG] 内容前100字符: '{ai_content[:100]}'")
            
            # 清除可能的BOM或不可见字符
            ai_content = ai_content.strip()
            if not ai_content:
                print("[ERROR] AI返回的内容为空")
                return {
                    "success": False,
                    "analysis": "",
                    "scores": {},
                    "message": "AI分析失败：返回内容为空"
                }
            
            # 移除markdown代码块标记
            ai_content = ai_content.replace('```json', '').replace('```', '').strip()
            
            # 检查内容是否以JSON开头
            if not (ai_content.startswith('{') or ai_content.startswith('[')):
                print(f"[ERROR] AI返回的内容不是有效的JSON开头: '{ai_content[:20]}...'")
                # 尝试提取JSON部分（可能AI返回了额外的文本）
                json_match = re.search(r'\{.*\}|\[.*\]', ai_content, re.DOTALL)
                if json_match:
                    ai_content = json_match.group(0)
                    print(f"[DEBUG] 提取到的JSON部分: '{ai_content}'")
                else:
                    return {
                        "success": False,
                        "analysis": "",
                        "scores": {},
                        "message": "AI分析失败：返回内容格式异常，请重试"
                    }
            
            try:
                # 修复字符串内部的原始换行、制表符等控制字符，避免 JSON 解析失败
                ai_content = _repair_json_text(ai_content)

                # 尝试解析JSON
                try:
                    result = json.loads(ai_content)
                except json.JSONDecodeError:
                    # 修复scores被包裹在字符串中的问题
                    scores_pattern = r'"scores"\s*:\s*"\s*\{([^}]+)\}\s*"'
                    scores_match = re.search(scores_pattern, ai_content, re.DOTALL)
                    if scores_match:
                        scores_str = scores_match.group(1)
                        scores_str = scores_str.replace('" "', '", "').replace(': "', '": ').replace('" }', '"}')
                        ai_content = re.sub(scores_pattern, f'"scores": {{{scores_str}}}', ai_content, flags=re.DOTALL)

                    ai_content = _repair_json_text(ai_content)
                    result = json.loads(ai_content)
                
                # 规范化评分：兼容 "85"、"85分" 等写法，并限制在 0-100
                raw_scores = result.get("scores", {})
                scores = {}
                if isinstance(raw_scores, dict):
                    for name, value in raw_scores.items():
                        try:
                            number = float(str(value).replace("分", "").strip())
                        except (TypeError, ValueError):
                            continue
                        scores[name] = max(0, min(100, int(round(number))))

                return {
                    "success": True,
                    "analysis": result.get("analysis", ""),
                    "scores": scores,
                    "message": "AI分析完成"
                }
            except json.JSONDecodeError as e:
                print(f"[ERROR] 解析AI分析结果JSON失败: {e}")
                print(f"[ERROR] 问题内容: '{ai_content[:200]}...'")
                return {
                    "success": False,
                    "analysis": "",
                    "scores": {},
                    "message": "AI分析失败：解析返回内容出错，请重试"
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
                "message": "AI分析失败：API密钥无效，请检查项目根目录 .env 中的 SILICONFLOW_API_KEY 配置"
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
    # 检查API密钥是否已配置
    if not API_KEY_CONFIGURED:
        return {
            "success": False,
            "questions": [],
            "message": "面试问题生成失败：请先在项目根目录 .env 中配置有效的 SILICONFLOW_API_KEY"
        }
    
    try:
        print(f"[DEBUG] 开始生成面试问题，岗位: {job_title}，使用模型: {MODEL_NAME}")
        
        # 构建生成面试问题的prompt
        if resume_text:
            prompt = f"""请作为专业的{job_title}面试官，基于以下简历内容生成面试问题：

简历内容：
{resume_text}

要求：
1. 覆盖{job_title}岗位的核心技能、专业知识和相关经验
2. 类型包括技术、行为、项目经验三类，难度由基础到进阶
3. 生成 6 到 10 个问题，每个问题清晰、有针对性
4. 使用中文

请只返回一个 JSON 对象，不要输出其他文字，结构如下：
{{"questions": [{{"question": "问题内容", "type": "技术"}}, {{"question": "问题内容", "type": "行为"}}]}}
"""
        else:
            prompt = f"""请作为专业的{job_title}面试官，生成面试问题：

要求：
1. 覆盖{job_title}岗位的核心技能、专业知识和相关经验
2. 类型包括技术、行为、项目经验三类，难度由基础到进阶
3. 生成 6 到 10 个问题，每个问题清晰、有针对性
4. 使用中文

请只返回一个 JSON 对象，不要输出其他文字，结构如下：
{{"questions": [{{"question": "问题内容", "type": "技术"}}, {{"question": "问题内容", "type": "行为"}}]}}
"""
        
        # 调用硅基流动API
        print(f"[DEBUG] 调用硅基流动API生成面试问题，prompt长度: {len(prompt)}")
        
        # 构建API参数
        api_params = {
            "model": MODEL_NAME,
            "messages": [
                {"role": "system", "content": f"你是一位专业的{job_title}面试官，擅长生成结构化、针对性强的面试问题。"},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 1500,
            "temperature": 0.5,
            "response_format": {"type": "json_object"}  # 强制JSON格式输出
        }
        
        # 如果是推理模型(Qwen3.5系列)，禁用思考模式以加快响应
        if "Qwen3.5" in MODEL_NAME:
            api_params["extra_body"] = {"thinking": {"type": "disabled"}}

        def extract_questions(content: str) -> list:
            """提取有效问题，兼容数组、{"questions": [...]} 与单个问题对象"""
            content = (content or "").strip()
            if not content:
                return []
            if not (content.startswith('{') or content.startswith('[')):
                match = re.search(r'\{.*\}|\[.*\]', content, re.DOTALL)
                if not match:
                    return []
                content = match.group(0)

            try:
                parsed = json.loads(_repair_json_text(content))
            except json.JSONDecodeError as exc:
                print(f"[ERROR] 解析面试问题JSON失败: {exc}")
                return []

            if isinstance(parsed, dict):
                if isinstance(parsed.get("questions"), list):
                    parsed = parsed["questions"]
                elif parsed.get("question"):
                    parsed = [parsed]
                else:
                    return []
            if not isinstance(parsed, list):
                return []

            return [
                item for item in parsed
                if isinstance(item, dict) and item.get("question")
            ]

        # 模型偶尔会返回错误对象或只返回单个问题，最多重试一次
        questions = []
        for attempt in range(2):
            api_params["temperature"] = 0.5 if attempt == 0 else 0.2
            response = client.chat.completions.create(**api_params)
            content = response.choices[0].message.content if response.choices else ""
            print(f"[DEBUG] 第{attempt + 1}次生成面试问题，返回前100字符: '{(content or '')[:100]}'")
            questions = extract_questions(content)
            if questions:
                break

        if not questions:
            return {
                "success": False,
                "questions": [],
                "message": "面试问题生成失败，请稍后重试"
            }

        return {
            "success": True,
            "questions": questions[:10],
            "message": "面试问题生成完成"
        }
    except Exception as e:
        error_msg = str(e)
        print(f"[ERROR] 生成面试问题出错: {error_msg}")
        
        # 提供更友好的错误信息
        if "401" in error_msg or "Invalid token" in error_msg:
            return {
                "success": False,
                "questions": [],
                "message": "面试问题生成失败：API密钥无效，请检查项目根目录 .env 中的 SILICONFLOW_API_KEY 配置"
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

@app.get("/api/v1/resume/analyze")
async def analyze_resume(resume_id: str = Query(..., description="简历ID")):
    """分析简历内容（流式响应，返回实际处理进度）"""
    resume = repository.get_resume(resume_id)
    if not resume:
        raise HTTPException(status_code=404, detail="未找到该简历ID")

    repository.update_resume_status(resume_id, "analyzing")
    resume_text = resume["content_text"]
    
    import asyncio
    
    def sse_msg(data):
        """格式化为SSE协议格式: data: {json}\n\n"""
        return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
    
    async def generate_progress():
        yield sse_msg({"progress": 1, "status": "connecting", "message": "正在连接AI服务..."})
        await asyncio.sleep(0)
        
        yield sse_msg({"progress": 2, "status": "analyzing", "message": "正在分析简历内容..."})
        await asyncio.sleep(0)
        
        yield sse_msg({"progress": 3, "status": "generating", "message": "正在生成分析报告..."})
        await asyncio.sleep(0)
        
        ai_result = analyze_resume_with_ai(resume_text)
        
        yield sse_msg({"progress": 4, "status": "processing", "message": "正在整理评分数据..."})
        await asyncio.sleep(0)
        
        if ai_result["success"]:
            scores = ai_result.get("scores", {})
            numeric_scores = [float(v) for v in scores.values() if isinstance(v, (int, float))]
            total_score = round(sum(numeric_scores) / len(numeric_scores), 2) if numeric_scores else None
            repository.save_analysis(resume_id, ai_result["analysis"], scores, total_score)

            yield sse_msg({
                "progress": 5, "status": "completed", "message": "分析完成",
                "data": {
                    "resume_id": resume_id,
                    "filename": resume["filename"],
                    "text_preview": resume_text[:500] + ("..." if len(resume_text) > 500 else ""),
                    "content_length": len(resume_text),
                    "analysis": ai_result["analysis"],
                    "scores": scores,
                    "message": "简历分析完成",
                    "status": "analyzed"
                }
            })
        else:
            repository.update_resume_status(resume_id, "analysis_failed")
            yield sse_msg({
                "progress": 5, "status": "failed", "message": "分析失败",
                "data": {
                    "resume_id": resume_id,
                    "filename": resume["filename"],
                    "text_preview": resume_text[:500] + ("..." if len(resume_text) > 500 else ""),
                    "content_length": len(resume_text),
                    "analysis": "",
                    "scores": {},
                    "message": ai_result["message"],
                    "status": "analysis_failed"
                }
            })
    
    return StreamingResponse(generate_progress(), media_type="text/event-stream")

@app.get("/api/v1/resume/{resume_id}")
async def get_resume(resume_id: str):
    """获取简历详情"""
    resume = repository.get_resume(resume_id)
    if not resume:
        raise HTTPException(status_code=404, detail="未找到该简历ID")

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
        resume = repository.get_resume(resume_id)
        if not resume:
            return JSONResponse(
                {
                    "success": False,
                    "job_title": job_title,
                    "message": "未找到指定的简历ID"
                },
                status_code=404
            )
        resume_text = resume["content_text"]
    
    # 调用AI生成面试问题
    ai_result = generate_interview_questions(job_title, resume_text)
    
    if ai_result["success"]:
        # 生成面试ID
        interview_id = str(uuid.uuid4())
        repository.create_interview(interview_id, resume_id, job_title, ai_result["questions"])
        
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

def evaluate_answer_with_ai(job_title: str, question: str, answer: str) -> dict:
    """调用AI评估面试回答，返回评分、评语与改进建议"""
    try:
        prompt = f"""你是资深{job_title}面试官，请评估候选人对以下问题的回答。

问题：{question}
候选人回答：{answer}

请从内容准确性、逻辑结构、专业深度、表达清晰度四个方面评估，并返回JSON对象：
- score: 0到100的整数
- feedback: 150字以内的总体评语
- suggestions: 2到3条具体可执行的改进建议（字符串数组）
"""

        api_params = {
            "model": MODEL_NAME,
            "messages": [
                {"role": "system", "content": f"你是一位专业的{job_title}面试官，评估客观、建议具体。"},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 800,
            "temperature": 0.3,
            "response_format": {"type": "json_object"}
        }

        # 推理模型（Qwen3.5 系列）关闭思考模式以加快响应
        if "Qwen3.5" in MODEL_NAME:
            api_params["extra_body"] = {"enable_thinking": False}

        response = client.chat.completions.create(**api_params)
        content = response.choices[0].message.content.strip()
        content = re.sub(r"^```(?:json)?\s*|\s*```$", "", content)
        result = json.loads(content)

        score = max(0, min(100, int(round(float(result.get("score", 0))))))
        suggestions = result.get("suggestions") or []
        if isinstance(suggestions, str):
            suggestions = [suggestions]
        suggestions = [str(item) for item in suggestions][:5]

        return {
            "success": True,
            "score": score,
            "feedback": str(result.get("feedback", "")),
            "suggestions": suggestions
        }
    except json.JSONDecodeError:
        return {"success": False, "message": "AI返回内容解析失败，请重试"}
    except Exception as e:
        return {"success": False, "message": f"评估失败: {str(e)}"}


@app.post("/api/v1/interview/answer")
async def submit_answer(request: AnswerRequest):
    """提交面试答案并由AI评分"""
    answer = request.answer.strip()
    if not answer:
        raise HTTPException(status_code=400, detail="回答内容不能为空")

    interview = repository.get_interview(request.interview_id)
    if not interview:
        raise HTTPException(status_code=404, detail="未找到该面试ID")

    ai_result = evaluate_answer_with_ai(interview["job_title"], request.question, answer)
    if not ai_result["success"]:
        return JSONResponse(
            {"success": False, "message": ai_result["message"]},
            status_code=500
        )

    repository.save_answer(
        request.interview_id,
        request.question_index,
        request.question,
        answer,
        ai_result["score"],
        ai_result["feedback"],
        ai_result["suggestions"]
    )

    return JSONResponse({
        "success": True,
        "interview_id": request.interview_id,
        "question_index": request.question_index,
        "score": ai_result["score"],
        "feedback": ai_result["feedback"],
        "suggestions": ai_result["suggestions"],
        "message": "评估完成"
    })


@app.get("/api/v1/interview/{interview_id}")
async def get_interview(interview_id: str):
    """获取面试详情与已提交答案的评估结果"""
    interview = repository.get_interview(interview_id)
    if not interview:
        raise HTTPException(status_code=404, detail="未找到该面试ID")

    return JSONResponse({
        "interview_id": interview_id,
        "job_title": interview["job_title"],
        "questions": interview["questions"],
        "answers": repository.get_answers(interview_id),
        "created_at": interview["created_at"].isoformat()
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
