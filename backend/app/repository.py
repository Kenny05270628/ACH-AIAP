"""数据访问层：简历、分析结果与面试会话。"""
from typing import Optional

from psycopg2.extras import Json

from backend.app.db import get_cursor


def create_user(user_id: str, email: str, username: str, password_hash: str) -> None:
    with get_cursor() as cur:
        cur.execute(
            """
            INSERT INTO users (id, email, username, password_hash)
            VALUES (%s, %s, %s, %s)
            """,
            (user_id, email, username, password_hash),
        )


def get_user(user_id: str) -> Optional[dict]:
    """按 ID 获取用户（不含密码哈希）"""
    with get_cursor(commit=False) as cur:
        cur.execute(
            "SELECT id, email, username, created_at FROM users WHERE id = %s",
            (user_id,),
        )
        row = cur.fetchone()
        return dict(row) if row else None


def get_user_by_email(email: str) -> Optional[dict]:
    """按邮箱获取用户（含密码哈希，仅用于登录校验）"""
    with get_cursor(commit=False) as cur:
        cur.execute(
            "SELECT id, email, username, password_hash, created_at FROM users WHERE email = %s",
            (email,),
        )
        row = cur.fetchone()
        return dict(row) if row else None


def create_resume(resume_id: str, filename: str, file_path: str, content_text: str,
                  user_id: Optional[str] = None) -> None:
    with get_cursor() as cur:
        cur.execute(
            """
            INSERT INTO resumes (id, user_id, filename, file_path, content_text, status)
            VALUES (%s, %s, %s, %s, %s, 'uploaded')
            """,
            (resume_id, user_id, filename, file_path, content_text),
        )


def get_resume(resume_id: str) -> Optional[dict]:
    with get_cursor(commit=False) as cur:
        cur.execute(
            """
            SELECT id, user_id, filename, file_path, content_text, status, created_at
            FROM resumes
            WHERE id = %s
            """,
            (resume_id,),
        )
        row = cur.fetchone()
        return dict(row) if row else None


def list_user_resumes(user_id: str, limit: int = 50) -> list:
    """当前用户的简历列表，附带最近一次分析总分"""
    with get_cursor(commit=False) as cur:
        cur.execute(
            """
            SELECT r.id, r.filename, r.status, r.created_at,
                   (SELECT ra.total_score
                      FROM resume_analyses ra
                     WHERE ra.resume_id = r.id
                     ORDER BY ra.created_at DESC
                     LIMIT 1) AS total_score
            FROM resumes r
            WHERE r.user_id = %s
            ORDER BY r.created_at DESC
            LIMIT %s
            """,
            (user_id, limit),
        )
        items = []
        for row in cur.fetchall():
            item = dict(row)
            item["id"] = str(item["id"])
            item["total_score"] = float(item["total_score"]) if item["total_score"] is not None else None
            item["created_at"] = item["created_at"].isoformat()
            items.append(item)
        return items


def update_resume_status(resume_id: str, status: str) -> None:
    with get_cursor() as cur:
        cur.execute(
            "UPDATE resumes SET status = %s, updated_at = now() WHERE id = %s",
            (status, resume_id),
        )


def save_analysis(resume_id: str, analysis_text: str, scores: dict, total_score: Optional[float]) -> None:
    with get_cursor() as cur:
        cur.execute(
            """
            INSERT INTO resume_analyses (resume_id, total_score, category_scores, analysis_text)
            VALUES (%s, %s, %s, %s)
            """,
            (resume_id, total_score, Json(scores), analysis_text),
        )
        cur.execute(
            "UPDATE resumes SET status = 'analyzed', updated_at = now() WHERE id = %s",
            (resume_id,),
        )


def create_interview(interview_id: str, resume_id: Optional[str], job_title: str, questions: list,
                     user_id: Optional[str] = None) -> None:
    with get_cursor() as cur:
        cur.execute(
            """
            INSERT INTO interviews (id, user_id, resume_id, job_title, questions)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (interview_id, user_id, resume_id, job_title, Json(questions)),
        )


def get_interview(interview_id: str) -> Optional[dict]:
    with get_cursor(commit=False) as cur:
        cur.execute(
            """
            SELECT id, user_id, resume_id, job_title, questions, created_at
            FROM interviews
            WHERE id = %s
            """,
            (interview_id,),
        )
        row = cur.fetchone()
        return dict(row) if row else None


def list_user_interviews(user_id: str, limit: int = 50) -> list:
    """当前用户的面试记录列表，附带已答数量与平均分"""
    with get_cursor(commit=False) as cur:
        cur.execute(
            """
            SELECT i.id, i.job_title, i.questions, i.created_at,
                   COUNT(a.id) AS answer_count,
                   AVG(a.score) AS avg_score
            FROM interviews i
            LEFT JOIN interview_answers a ON a.interview_id = i.id
            WHERE i.user_id = %s
            GROUP BY i.id
            ORDER BY i.created_at DESC
            LIMIT %s
            """,
            (user_id, limit),
        )
        items = []
        for row in cur.fetchall():
            item = dict(row)
            item["id"] = str(item["id"])
            item["question_count"] = len(item.pop("questions") or [])
            item["answer_count"] = int(item["answer_count"])
            item["avg_score"] = round(float(item["avg_score"]), 1) if item["avg_score"] is not None else None
            item["created_at"] = item["created_at"].isoformat()
            items.append(item)
        return items


def save_answer(interview_id: str, question_index: int, question: str, answer_text: str,
                score: float, feedback: str, suggestions: list) -> None:
    with get_cursor() as cur:
        cur.execute(
            """
            INSERT INTO interview_answers
                (interview_id, question_index, question, answer_text, score, feedback, suggestions)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (interview_id, question_index, question, answer_text, score, feedback, Json(suggestions)),
        )


def get_answers(interview_id: str) -> list:
    with get_cursor(commit=False) as cur:
        cur.execute(
            """
            SELECT question_index, question, answer_text, score, feedback, suggestions, created_at
            FROM interview_answers
            WHERE interview_id = %s
            ORDER BY question_index
            """,
            (interview_id,),
        )
        answers = []
        for row in cur.fetchall():
            item = dict(row)
            item["score"] = float(item["score"]) if item["score"] is not None else None
            item["created_at"] = item["created_at"].isoformat()
            answers.append(item)
        return answers
