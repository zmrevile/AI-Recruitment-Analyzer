#!/usr/bin/env python3
"""
服务集成测试 - 验证所有服务都使用优化后的embedding
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config.settings import get_spark_config
from app.services.resume_analyzer import ResumeAnalyzer
from app.services.job_analyzer import JobAnalyzer
from app.services.resume_job_matcher import ResumeJobMatcher
from app.core.spark_embedding import get_embedding_stats, clear_embedding_cache


def test_services_use_optimized_embedding():
    """测试所有服务是否使用优化后的embedding"""
    print("🧪 测试服务集成 - 验证优化后的embedding使用")
    print("=" * 50)
    
    # 获取配置
    spark_config = get_spark_config()
    
    # 清空缓存，开始新的测试
    clear_embedding_cache()
    
    # 初始化所有服务
    print("📦 初始化服务...")
    try:
        resume_analyzer = ResumeAnalyzer(spark_config)
        job_analyzer = JobAnalyzer(spark_config)
        resume_matcher = ResumeJobMatcher(spark_config)
        print("✅ 所有服务初始化成功")
    except Exception as e:
        print(f"❌ 服务初始化失败: {e}")
        return False
    
    # 验证单例模式 - 所有服务应该使用同一个embedding实例
    print("\n🔄 验证单例模式...")
    embedding1 = resume_analyzer.embeddings
    embedding2 = job_analyzer.embeddings
    embedding3 = resume_matcher.embeddings
    
    if embedding1 is embedding2 is embedding3:
        print("✅ 单例模式验证成功 - 所有服务使用同一个embedding实例")
    else:
        print("❌ 单例模式验证失败 - 服务使用了不同的embedding实例")
        return False
    
    # 测试基本功能
    print("\n🚀 测试基本embedding功能...")
    
    # 测试数据
    test_texts = [
        "Python开发工程师",
        "机器学习算法",
        "深度学习框架"
    ]
    
    try:
        # 通过resume_analyzer测试
        embeddings1 = [resume_analyzer.embeddings.embed_query(text) for text in test_texts]
        print(f"✅ ResumeAnalyzer embedding测试成功，处理了{len(embeddings1)}个文本")
        
        # 通过job_analyzer测试
        embeddings2 = [job_analyzer.embeddings.embed_query(text) for text in test_texts]
        print(f"✅ JobAnalyzer embedding测试成功，处理了{len(embeddings2)}个文本")
        
        # 通过resume_matcher测试
        embeddings3 = [resume_matcher.embeddings.embed_query(text) for text in test_texts]
        print(f"✅ ResumeJobMatcher embedding测试成功，处理了{len(embeddings3)}个文本")
        
        # 验证结果一致性（因为使用相同实例，结果应该一致）
        if embeddings1 == embeddings2 == embeddings3:
            print("✅ 结果一致性验证成功 - 所有服务返回相同结果")
        else:
            print("❌ 结果一致性验证失败")
            return False
            
    except Exception as e:
        print(f"❌ embedding功能测试失败: {e}")
        return False
    
    # 检查性能统计
    print("\n📊 检查性能统计...")
    stats = get_embedding_stats()
    
    print(f"实际请求数: {stats['total_requests']}")
    print(f"缓存命中数: {stats['cache_hits']}")
    print(f"缓存命中率: {stats['cache_hit_rate']}")
    
    print("\n📈 详细统计信息:")
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    return True


def main():
    """主测试函数"""
    print("🎯 开始服务集成测试")
    
    try:
        # 测试服务集成
        if test_services_use_optimized_embedding():
            print("\n🎉 服务集成测试通过！")
        else:
            print("\n❌ 服务集成测试失败！")
            return
        
        print("\n" + "=" * 50)
        print("🎉 所有测试完成！所有服务已成功使用优化后的embedding")
            
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 