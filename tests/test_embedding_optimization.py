#!/usr/bin/env python3
"""
测试优化后的Embedding模型功能
展示缓存、批处理、性能监控等优化效果
"""

import time
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.spark_embedding import (
    get_embeddings, 
    embed_text, 
    embed_texts, 
    get_embedding_stats,
    clear_embedding_cache
)
from app.utils.logger import spark_embedding_logger


def test_basic_functionality():
    """测试基本功能"""
    print("🧪 测试基本功能...")
    
    # 单个文本嵌入
    text = "这是一个测试文本"
    embedding = embed_text(text)
    print(f"✅ 单文本嵌入完成，维度: {len(embedding)}")
    
    # 多个文本嵌入
    texts = [
        "人工智能工程师",
        "Python开发经验",
        "机器学习算法",
        "深度学习框架",
        "数据分析能力"
    ]
    embeddings = embed_texts(texts)
    print(f"✅ 多文本嵌入完成，数量: {len(embeddings)}")


def test_caching_performance():
    """测试缓存性能"""
    print("\n🚀 测试缓存性能...")
    
    # 清空缓存
    clear_embedding_cache()
    
    test_texts = [
        "Java开发工程师", 
        "前端开发经验", 
        "数据库设计", 
        "系统架构师",
        "产品经理"
    ] * 3  # 重复文本
    
    # 第一次嵌入（无缓存）
    start_time = time.time()
    embeddings1 = embed_texts(test_texts)
    first_time = time.time() - start_time
    
    # 第二次嵌入（有缓存）
    start_time = time.time()
    embeddings2 = embed_texts(test_texts)
    second_time = time.time() - start_time
    
    print(f"⏱️  第一次嵌入时间: {first_time:.3f}秒")
    print(f"⏱️  第二次嵌入时间: {second_time:.3f}秒")
    if second_time > 0:
        print(f"🎯 性能提升: {first_time/second_time:.1f}倍")
    else:
        print("🎯 性能提升: 极大（缓存命中，几乎瞬时完成）")
    
    # 验证结果一致性
    assert embeddings1 == embeddings2, "缓存结果不一致"
    print("✅ 缓存结果验证通过")


def test_batch_processing():
    """测试批处理功能"""
    print("\n📦 测试批处理功能...")
    
    # 生成大量测试文本
    large_texts = [f"测试文本_{i}" for i in range(100)]
    
    start_time = time.time()
    embeddings = embed_texts(large_texts)
    process_time = time.time() - start_time
    
    print(f"📊 处理{len(large_texts)}个文本")
    print(f"⏱️  总耗时: {process_time:.3f}秒")
    print(f"🚄 平均速度: {len(large_texts)/process_time:.1f}个/秒")
    print(f"✅ 结果数量: {len(embeddings)}")


def test_statistics_monitoring():
    """测试性能统计监控"""
    print("\n📊 测试性能统计...")
    
    # 执行一些嵌入操作
    test_texts = [
        "软件工程师", "测试工程师", "运维工程师",
        "算法工程师", "数据工程师", "安全工程师"
    ]
    
    # 多次嵌入相同文本（测试缓存命中率）
    for _ in range(3):
        embed_texts(test_texts)
    
    # 获取统计信息
    stats = get_embedding_stats()
    
    print("📈 性能统计信息:")
    for key, value in stats.items():
        print(f"   {key}: {value}")


def test_singleton_pattern():
    """测试单例模式"""
    print("\n🔄 测试单例模式...")
    
    # 获取多个实例
    embeddings1 = get_embeddings()
    embeddings2 = get_embeddings()
    
    # 验证是同一个实例
    assert embeddings1 is embeddings2, "单例模式失败"
    print("✅ 单例模式验证通过")


def test_error_handling():
    """测试错误处理"""
    print("\n🛡️  测试错误处理...")
    
    # 测试空文本
    empty_results = embed_texts(["", "   ", None])
    print(f"✅ 空文本处理: {len(empty_results)}个结果")
    
    # 测试特殊字符
    special_texts = [
        "🚀 特殊字符测试",
        "Multi-language: 中文 English 日本語",
        "Numbers: 123456789",
        "Symbols: @#$%^&*()"
    ]
    special_results = embed_texts(special_texts)
    print(f"✅ 特殊文本处理: {len(special_results)}个结果")


def benchmark_comparison():
    """性能基准测试"""
    print("\n⚡ 性能基准测试...")
    
    # 准备测试数据
    test_sizes = [10, 50, 100, 200]
    
    for size in test_sizes:
        texts = [f"测试文本编号_{i}_内容较长的文本用于测试批处理性能" for i in range(size)]
        
        # 清空缓存确保公平测试
        clear_embedding_cache()
        
        start_time = time.time()
        embeddings = embed_texts(texts)
        elapsed_time = time.time() - start_time
        
        print(f"📏 {size:3d}个文本: {elapsed_time:.3f}秒 ({size/elapsed_time:.1f}个/秒)")


def main():
    """主测试函数"""
    print("🎯 开始测试优化后的Embedding模型")
    print("=" * 50)
    
    try:
        # 基本功能测试
        test_basic_functionality()
        
        # 缓存性能测试
        test_caching_performance()
        
        # 批处理测试
        test_batch_processing()
        
        # 统计监控测试
        test_statistics_monitoring()
        
        # 单例模式测试
        test_singleton_pattern()
        
        # 错误处理测试
        test_error_handling()
        
        # 性能基准测试
        benchmark_comparison()
        
        print("\n" + "=" * 50)
        print("🎉 所有测试完成！")
        
        # 显示最终统计
        final_stats = get_embedding_stats()
        print("\n📊 最终统计信息:")
        for key, value in final_stats.items():
            print(f"   {key}: {value}")
            
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 