#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
抖音刷量批量提交系统 - 最终完整版
基于真实API接口，完全可用的批量提交系统
"""

from douyin_batch_submitter_v2 import DouyinBatchSubmitterV2
import json
import time
from datetime import datetime

def load_urls_from_file(filename: str) -> list:
    """从文件加载URL列表"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            urls = [line.strip() for line in f if line.strip()]
        return urls
    except FileNotFoundError:
        print(f"❌ 文件 {filename} 不存在")
        return []

def save_urls_to_file(urls: list, filename: str = "douyin_urls.txt"):
    """保存URL列表到文件"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            for url in urls:
                f.write(url + '\n')
        print(f"📁 链接已保存到 {filename}")
    except Exception as e:
        print(f"❌ 保存失败: {e}")

def input_urls_manually() -> list:
    """手动输入URL列表"""
    urls = []
    print("请输入抖音视频链接（每行一个，输入空行结束）:")
    
    while True:
        url = input("链接: ").strip()
        if not url:
            break
        urls.append(url)
    
    return urls

def quick_test():
    """快速测试功能"""
    print("🚀 快速测试模式")
    print("=" * 40)
    
    submitter = DouyinBatchSubmitterV2()
    
    # 测试连接
    if submitter.test_connection():
        print("✅ API连接正常")
    else:
        print("❌ API连接异常")
        return False
    
    # 测试链接
    test_url = input("请输入测试链接（回车使用默认）: ").strip()
    if not test_url:
        test_url = f"https://www.douyin.com/video/75023406983692{datetime.now().strftime('%H%M%S')}"
    
    print(f"📤 测试链接: {test_url}")
    
    success, message, order_info = submitter.submit_single_url(test_url)
    
    if success:
        print("✅ 提交成功！")
        print("📋 订单信息:")
        for key, value in order_info.items():
            if key != 'response':  # 不显示完整响应
                print(f"   {key}: {value}")
        return True
    else:
        print(f"📋 提交结果: {message}")
        
        # 分析错误类型
        if "重复提交" in message:
            print("ℹ️ 这是重复提交限制，说明API工作正常")
            return True
        elif "已领取过" in message:
            print("ℹ️ 这是每日限制，说明API工作正常")
            print("💡 建议：明天再试或使用不同的链接")
            return True
        elif "SSL连接失败" in message:
            print("⚠️ 这是SSL连接问题，可能的解决方案：")
            print("   1. 检查网络连接是否稳定")
            print("   2. 尝试使用VPN或更换网络")
            print("   3. 稍后再试（服务器可能临时不稳定）")
            print("   4. 系统已自动重试3次")
            return False
        elif "网络连接失败" in message:
            print("⚠️ 这是网络连接问题，建议：")
            print("   1. 检查网络连接")
            print("   2. 确认防火墙设置")
            print("   3. 尝试更换DNS")
            print("   4. 稍后再试")
            return False
        else:
            print("❌ 可能存在其他问题")
            print(f"💡 详细错误信息: {message}")
            return False

def batch_submit_from_input():
    """从手动输入批量提交"""
    print("🚀 手动输入批量提交")
    print("=" * 40)
    
    urls = input_urls_manually()
    
    if not urls:
        print("❌ 没有输入任何链接")
        return
    
    print(f"📋 共输入 {len(urls)} 个链接")
    
    # 询问是否保存链接
    save_choice = input("是否保存链接到文件？(y/n): ").lower()
    if save_choice == 'y':
        save_urls_to_file(urls)
    
    # 配置参数
    delay_min = float(input("最小延迟时间（秒，默认3）: ") or "3")
    delay_max = float(input("最大延迟时间（秒，默认8）: ") or "8")
    
    print(f"\n🚀 开始批量提交...")
    print("⚠️ 注意：系统有每日提交限制，部分链接可能会失败")
    
    submitter = DouyinBatchSubmitterV2()
    results = submitter.batch_submit(
        urls=urls,
        max_workers=1,
        delay_range=(delay_min, delay_max)
    )
    
    # 分析结果
    analyze_results(results)
    
    submitter.save_results(results)
    print(f"\n✅ 批量提交完成！")

def batch_submit_from_file():
    """从文件批量提交"""
    print("🚀 从文件批量提交")
    print("=" * 40)
    
    filename = input("请输入文件名（默认: douyin_urls.txt）: ").strip()
    if not filename:
        filename = "douyin_urls.txt"
    
    urls = load_urls_from_file(filename)
    
    if not urls:
        print("❌ 文件为空或不存在")
        return
    
    print(f"📋 从文件加载了 {len(urls)} 个链接")
    print("前5个链接预览:")
    for i, url in enumerate(urls[:5], 1):
        print(f"   {i}. {url}")
    
    if len(urls) > 5:
        print(f"   ... 还有 {len(urls) - 5} 个链接")
    
    confirm = input("\n确认开始批量提交？(y/n): ").lower()
    if confirm != 'y':
        print("❌ 已取消")
        return
    
    # 配置参数
    delay_min = float(input("最小延迟时间（秒，默认3）: ") or "3")
    delay_max = float(input("最大延迟时间（秒，默认8）: ") or "8")
    
    print(f"\n🚀 开始批量提交...")
    print("⚠️ 注意：系统有每日提交限制，部分链接可能会失败")
    
    submitter = DouyinBatchSubmitterV2()
    results = submitter.batch_submit(
        urls=urls,
        max_workers=1,
        delay_range=(delay_min, delay_max)
    )
    
    # 分析结果
    analyze_results(results)
    
    submitter.save_results(results)
    print(f"\n✅ 批量提交完成！")

def analyze_results(results: list):
    """分析提交结果"""
    print("\n📊 结果分析:")
    
    success_count = sum(1 for r in results if r['success'])
    total_count = len(results)
    
    # 统计错误类型
    duplicate_count = 0
    daily_limit_count = 0
    other_error_count = 0
    
    for result in results:
        if not result['success']:
            message = result['message']
            if "重复提交" in message:
                duplicate_count += 1
            elif "已领取过" in message:
                daily_limit_count += 1
            else:
                other_error_count += 1
    
    print(f"✅ 成功提交: {success_count} 个")
    print(f"🔄 重复提交限制: {duplicate_count} 个")
    print(f"⏰ 每日限制: {daily_limit_count} 个")
    print(f"❌ 其他错误: {other_error_count} 个")
    print(f"📈 总成功率: {(success_count/total_count*100):.1f}%")
    
    if duplicate_count > 0:
        print("💡 重复提交说明这些链接今天已经提交过了")
    if daily_limit_count > 0:
        print("💡 每日限制说明今天的免费额度已用完，明天可以继续")

def show_system_info():
    """显示系统信息"""
    print("📊 系统信息")
    print("=" * 40)
    
    submitter = DouyinBatchSubmitterV2()
    
    print(f"🌐 API地址: {submitter.endpoints['pay']}")
    print(f"🎯 支持的商品: {submitter.product_config['douyin_play']['name']}")
    print(f"💰 商品价格: 免费")
    print(f"📋 每日限制: 是（防止滥用）")
    
    print("\n📋 API参数说明:")
    print("   - tid: 商品ID (3210)")
    print("   - inputvalue: 抖音视频链接")
    print("   - num: 数量 (1)")
    print("   - hashsalt: 安全哈希值")
    
    print("\n⚠️ 限制说明:")
    print("   - 每个链接每天只能提交一次")
    print("   - 每天有总提交次数限制")
    print("   - 系统会检测重复提交")

def show_usage_tips():
    """显示使用技巧"""
    print("💡 使用技巧")
    print("=" * 40)
    
    print("🎯 提高成功率的方法:")
    print("   1. 使用不同的抖音视频链接")
    print("   2. 避免重复提交相同链接")
    print("   3. 分时段提交（避开高峰期）")
    print("   4. 设置适当的延迟时间（3-8秒）")
    
    print("\n📅 最佳提交时间:")
    print("   - 每天早上重置限制")
    print("   - 避开网络高峰期")
    print("   - 分批次提交大量链接")
    
    print("\n🔧 故障排除:")
    print("   - 检查链接格式是否正确")
    print("   - 确认网络连接稳定")
    print("   - 查看日志文件获取详细信息")
    print("   - 如遇限制，明天再试")

def main():
    """主菜单"""
    print("🎯 抖音刷量批量提交系统 - 最终完整版")
    print("=" * 50)
    print("✅ 基于真实API接口构建")
    print("✅ 已验证可用的批量提交系统")
    print("✅ 支持每日免费提交限制检测")
    print("=" * 50)
    
    while True:
        print("\n📋 请选择操作:")
        print("1. 快速测试")
        print("2. 手动输入批量提交")
        print("3. 从文件批量提交")
        print("4. 显示系统信息")
        print("5. 使用技巧")
        print("0. 退出")
        
        choice = input("\n请选择 (0-5): ").strip()
        
        if choice == '0':
            print("👋 感谢使用！")
            break
        elif choice == '1':
            quick_test()
        elif choice == '2':
            batch_submit_from_input()
        elif choice == '3':
            batch_submit_from_file()
        elif choice == '4':
            show_system_info()
        elif choice == '5':
            show_usage_tips()
        else:
            print("❌ 无效选择，请重新输入")
        
        input("\n按回车键继续...")

if __name__ == "__main__":
    main() 