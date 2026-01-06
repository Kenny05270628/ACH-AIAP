import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.app.main import analyze_resume_with_ai

def test_ai_analysis():
    """测试AI分析函数"""
    # 简单的测试简历文本
    test_resume = """张三

个人信息：
- 电话：13800138000
- 邮箱：zhangsan@example.com
- 地址：北京市朝阳区

教育背景：
- 2018-2022 北京大学 计算机科学与技术 本科

工作经历：
- 2022-至今 腾讯科技有限公司 软件工程师
  负责微信支付后端系统开发，使用Java和Go语言
  参与了3个大型项目的开发，提升了系统性能30%

技能：
- 编程语言：Java, Go, Python
- 技术栈：Spring Boot, Docker, Kubernetes
- 数据库：MySQL, Redis, MongoDB
"""
    
    print("开始测试AI分析函数...")
    result = analyze_resume_with_ai(test_resume)
    print(f"\n测试结果：")
    print(f"成功状态：{result['success']}")
    print(f"消息：{result['message']}")
    print(f"分析内容：{result['analysis'][:500]}..." if result['analysis'] else "无分析内容")

if __name__ == "__main__":
    test_ai_analysis()
