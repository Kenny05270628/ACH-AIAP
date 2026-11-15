import requests
import json

# API基础URL
API_URL = "http://localhost:8080"

def test_root():
    """测试根路由"""
    print("测试根路由...")
    response = requests.get(f"{API_URL}/")
    if response.status_code == 200:
        print("✓ 根路由测试通过")
        print(f"  响应内容: {response.json()}")
        return True
    else:
        print(f"✗ 根路由测试失败，状态码: {response.status_code}")
        return False

def test_resume_upload():
    """测试简历上传功能"""
    print("\n测试简历上传功能...")
    
    # 创建一个简单的测试内容
    resume_content = """
    测试简历
    
    姓名：张三
    
    教育经历：
    - 2019-2023 清华大学 计算机科学与技术 学士
    
    技能：
    - Python, Java, C++
    - FastAPI, Django, Spring Boot
    - PostgreSQL, Redis, MongoDB
    """
    
    # 注意：API只接受PDF和DOCX格式，这里我们测试错误处理
    files = {"file": ("test_resume.txt", resume_content, "text/plain")}
    
    response = requests.post(f"{API_URL}/api/v1/resume/upload", files=files)
    
    if response.status_code == 400:
        print("✓ 简历上传格式验证测试通过")
        print(f"  响应内容: {response.json()}")
        return True
    else:
        print(f"✗ 简历上传测试失败，状态码: {response.status_code}")
        print(f"  响应内容: {response.json()}")
        return False

def test_resume_analyze():
    """测试简历分析功能"""
    print("\n测试简历分析功能...")
    
    # 由于API需要有效的简历ID，这里我们测试错误处理
    response = requests.get(f"{API_URL}/api/v1/resume/analyze", params={"resume_id": "invalid-id"})
    
    if response.status_code == 404:
        print("✓ 简历分析错误处理测试通过")
        print(f"  响应内容: {response.json()}")
        return True
    else:
        print(f"✗ 简历分析测试失败，状态码: {response.status_code}")
        print(f"  响应内容: {response.json()}")
        return False

def main():
    """运行所有测试"""
    print("=== 智能面试辅助平台 API 测试 ===")
    
    tests = [
        test_root,
        test_resume_upload,
        test_resume_analyze
    ]
    
    passed = 0
    for test in tests:
        if test():
            passed += 1
    
    print(f"\n=== 测试结果 ===")
    print(f"通过: {passed}/{len(tests)}")
    
    if passed == len(tests):
        print("✓ 所有测试通过！")
    else:
        print("✗ 部分测试失败，请检查代码")

if __name__ == "__main__":
    main()