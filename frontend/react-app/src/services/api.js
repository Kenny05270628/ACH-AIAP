const API_BASE_URL = 'http://localhost:8080';

// 上传简历
export const uploadResume = async (file) => {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${API_BASE_URL}/api/v1/resume/upload`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || '上传简历失败');
  }

  return response.json();
};

// 分析简历
export const analyzeResume = async (resumeId) => {
  const response = await fetch(`${API_BASE_URL}/api/v1/resume/analyze?resume_id=${resumeId}`, {
    method: 'POST',
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || '分析简历失败');
  }

  return response.json();
};

// 生成面试问题
export const generateInterviewQuestions = async (
  jobTitle,
  resumeId
) => {
  const response = await fetch(`${API_BASE_URL}/api/v1/interview/start`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ job_title: jobTitle, resume_id: resumeId }),
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.message || '生成面试问题失败');
  }

  return response.json();
};

// 获取简历详情
export const getResumeDetails = async (resumeId) => {
  const response = await fetch(`${API_BASE_URL}/api/v1/resume/${resumeId}`, {
    method: 'GET',
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || '获取简历详情失败');
  }

  return response.json();
};