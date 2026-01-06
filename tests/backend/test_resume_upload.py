import requests
import json
import os

# API基础URL
API_URL = "http://localhost:8080"

# 创建一个简单的测试PDF文件
# 注意：这里我们使用一个已经存在的PDF文件进行测试
# 如果没有测试文件，可以创建一个简单的文本文件并改名为test.pdf

def test_resume_upload_and_analyze():
    """测试简历上传和分析功能"""
    print("测试简历上传和分析功能...")
    
    # 确保有一个测试PDF文件
    test_file_path = "test_resume.pdf"
    
    # 如果测试文件不存在，创建一个简单的PDF文件（这里使用一个技巧，创建一个文本文件并改名为PDF）
    if not os.path.exists(test_file_path):
        with open(test_file_path, "w") as f:
            f.write("测试简历\n\n姓名：张三\n\n教育经历：\n- 2019-2023 清华大学 计算机科学与技术 学士\n\n技能：\n- Python, Java, C++\n- FastAPI, Django, Spring Boot\n- PostgreSQL, Redis, MongoDB")
    
    try:
        # 1. 上传简历
        print("\n1. 上传简历...")
        with open(test_file_path, "rb") as f:
            files = {"file": (test_file_path, f, "application/pdf")}
            response = requests.post(f"{API_URL}/api/v1/resume/upload", files=files)
        
        print(f"   上传状态码: {response.status_code}")
        print(f"   上传响应: {response.json()}")
        
        if response.status_code == 200:
            resume_id = response.json()["resume_id"]
            
            # 2. 分析简历
            print(f"\n2. 分析简历 (ID: {resume_id})...")
            response = requests.post(f"{API_URL}/api/v1/resume/analyze?resume_id={resume_id}")
            
            print(f"   分析状态码: {response.status_code}")
            print(f"   分析响应: {response.json()}")
            
            # 检查是否有AI分析内容
            if response.status_code == 200:
                result = response.json()
                if "analysis" in result and result["analysis"]:
                    print("\n3. AI分析内容:")
                    print(result["analysis"])
                    return True
                else:
                    print("\n3. 错误：AI分析内容为空！")
                    return False
            else:
                print("\n3. 错误：分析API调用失败！")
                return False
        else:
            print("\n3. 错误：上传API调用失败！")
            return False
    except Exception as e:
        print(f"\n3. 错误：测试过程中出现异常: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_resume_upload_and_analyze()
    if success:
        print("\n✅ 测试成功！")
    else:
        print("\n❌ 测试失败！")
