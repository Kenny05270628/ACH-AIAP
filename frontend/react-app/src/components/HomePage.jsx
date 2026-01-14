import React, { useState } from 'react';
import { Button } from './Button';
import { uploadResume, analyzeResume, generateInterviewQuestions } from '../services/api';

const HomePage = () => {
  const [file, setFile] = useState(null);
  const [resumeId, setResumeId] = useState(null);
  const [jobTitle, setJobTitle] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isGeneratingQuestions, setIsGeneratingQuestions] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [interviewQuestions, setInterviewQuestions] = useState(null);
  const [error, setError] = useState(null);

  // 处理文件选择
  const handleFileChange = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      setFile(e.target.files[0]);
      setError(null);
    }
  };

  // 处理简历上传
  const handleUpload = async () => {
    if (!file) {
      setError('请选择一个简历文件');
      return;
    }

    setIsUploading(true);
    setError(null);

    try {
      const result = await uploadResume(file);
      setResumeId(result.resume_id);
      setAnalysisResult(null);
      setInterviewQuestions(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : '上传失败');
    } finally {
      setIsUploading(false);
    }
  };

  // 处理简历分析
  const handleAnalyze = async () => {
    if (!resumeId) {
      setError('请先上传简历');
      return;
    }

    setIsAnalyzing(true);
    setError(null);

    try {
      const result = await analyzeResume(resumeId);
      setAnalysisResult(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : '分析失败');
    } finally {
      setIsAnalyzing(false);
    }
  };

  // 处理面试问题生成
  const handleGenerateQuestions = async () => {
    if (!jobTitle.trim()) {
      setError('请输入岗位名称');
      return;
    }

    setIsGeneratingQuestions(true);
    setError(null);

    try {
      const result = await generateInterviewQuestions(jobTitle.trim(), resumeId || undefined);
      setInterviewQuestions(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : '生成面试问题失败');
    } finally {
      setIsGeneratingQuestions(false);
    }
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <header className="text-center mb-12">
        <h1 className="text-4xl font-bold text-gray-800 mb-4">智能面试辅助平台</h1>
        <p className="text-lg text-gray-600">
          上传简历，获得AI分析，生成针对性面试问题
        </p>
      </header>

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-6">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        {/* 简历上传和分析区域 */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold mb-4">简历分析</h2>
          
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              上传简历 (支持 PDF, DOCX)
            </label>
            <input
              type="file"
              accept=".pdf,.docx"
              onChange={handleFileChange}
              className="w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
            />
            {file && (
              <p className="mt-2 text-sm text-gray-500">
                已选择: {file.name}
              </p>
            )}
          </div>

          <div className="flex gap-4 mb-6">
            <Button
              onClick={handleUpload}
              disabled={isUploading || !file}
              className="flex-1"
            >
              {isUploading ? '上传中...' : '上传简历'}
            </Button>

            <Button
              variant="secondary"
              onClick={handleAnalyze}
              disabled={isAnalyzing || !resumeId}
              className="flex-1"
            >
              {isAnalyzing ? '分析中...' : '分析简历'}
            </Button>
          </div>

          {analysisResult && (
            <div className="mt-6">
              <h3 className="text-lg font-medium mb-2">分析结果</h3>
              <div className="bg-gray-50 p-4 rounded-md">
                <p className="text-sm mb-4">{analysisResult.analysis}</p>
                
                <h4 className="text-sm font-medium mb-2">评分</h4>
                <div className="space-y-2">
                  {Object.entries(analysisResult.scores).map(([key, value]) => (
                    <div key={key} className="flex justify-between items-center">
                      <span className="text-sm text-gray-600">{key}</span>
                      <span className="text-sm font-medium">{value}分</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* 面试问题生成区域 */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold mb-4">AI模拟面试</h2>
          
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              岗位名称
            </label>
            <input
              type="text"
              value={jobTitle}
              onChange={(e) => setJobTitle(e.target.value)}
              placeholder="例如：软件工程师"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          <Button
            onClick={handleGenerateQuestions}
            disabled={isGeneratingQuestions || !jobTitle.trim()}
            className="w-full"
          >
            {isGeneratingQuestions ? '生成中...' : '生成面试问题'}
          </Button>

          {interviewQuestions && interviewQuestions.questions && (
            <div className="mt-6">
              <h3 className="text-lg font-medium mb-4">面试问题</h3>
              <div className="space-y-3">
                {interviewQuestions.questions.map((q, index) => (
                  <div key={index} className="bg-gray-50 p-4 rounded-md">
                    <p className="text-sm font-medium mb-1">{q.question}</p>
                    <p className="text-xs text-gray-500">类型：{q.type}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default HomePage;