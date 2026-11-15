"""数据访问层：简历、分析结果与面试会话。"""
from typing import Optional

from psycopg2.extras import Json

from backend.app.db import get_cursor


def create_resume(resume_id: str, filename: str, file_path: str, content_text: str) -> None:
    with get_cursor() as cur:
        cur.execute(
            """
            INSERT INTO resumes (id, filename, file_path, content_text, status)
            VALUES (%s, %s, %s, %s, 'uploaded')
            """,
            (resume_id, filename, file_path, content_text),
        )


def get_resume(resume_id: str) -> Optional[dict]:
    with get_cursor(commit=False) as cur:
        cur.execute(
            """
            SELECT id, filename, file_path, content_text, status, created_at
            FROM resumes
            WHERE id = %s
            """,
            (resume_id,),
        )
        row = cur.fetchone()
        return dict(row) if row else None


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


def create_interview(interview_id: str, resume_id: Optional[str], job_title: str, questions: list) -> None:
    with get_cursor() as cur:
        cur.execute(
            """
            INSERT INTO interviews (id, resume_id, job_title, questions)
            VALUES (%s, %s, %s, %s)
            """,
            (interview_id, resume_id, job_title, Json(questions)),
        )


def get_interview(interview_id: str) -> Optional[dict]:
    with get_cursor(commit=False) as cur:
        cur.execute(
            """
            SELECT id, resume_id, job_title, questions, created_at
            FROM interviews
            WHERE id = %s
            """,
            (interview_id,),
        )
        row = cur.fetchone()
        return dict(row) if row else None


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
