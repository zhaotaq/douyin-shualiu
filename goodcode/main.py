#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
抖音刷量批量提交系统
简洁版主程序
"""

from douyin_batch_submitter_v2 import DouyinBatchSubmitterV2
import json
import time
from datetime import datetime

def load_urls_from_file(filename: str = "douyin_urls.txt") -> list:
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
            if key != 'response':
                print(f"   {key}: {value}")
        return True
    else:
        print(f"📋 提交结果: {message}")
        
        if "重复提交" in message or "已领取过" in message:
            print("ℹ️ 这说明API工作正常，只是有重复/限制")
            return True
        else:
            print("❌ 可能存在其他问题")
            return False

def batch_submit():
    """批量提交功能"""
    print("🚀 批量提交模式")
    print("=" * 40)
    
    # 选择输入方式
    print("请选择输入方式:")
    print("1. 从文件读取 (douyin_urls.txt)")
    print("2. 手动输入")
    
    choice = input("选择 (1-2): ").strip()
    
    urls = []
    if choice == '1':
        urls = load_urls_from_file()
        if not urls:
            print("❌ 文件为空或不存在")
            return
    elif choice == '2':
        print("请输入抖音视频链接（每行一个，输入空行结束）:")
        while True:
            url = input("链接: ").strip()
            if not url:
                break
            urls.append(url)
        
        if urls:
            save_choice = input("是否保存链接到文件？(y/n): ").lower()
            if save_choice == 'y':
                save_urls_to_file(urls)
    else:
        print("❌ 无效选择")
        return
    
    if not urls:
        print("❌ 没有可提交的链接")
        return
    
    print(f"📋 共有 {len(urls)} 个链接待提交")
    
    # 配置参数
    delay_min = float(input("最小延迟时间（秒，默认3）: ") or "3")
    delay_max = float(input("最大延迟时间（秒，默认8）: ") or "8")
    
    confirm = input(f"\n确认提交 {len(urls)} 个链接？(y/n): ").lower()
    if confirm != 'y':
        print("❌ 已取消")
        return
    
    print(f"\n🚀 开始批量提交...")
    
    submitter = DouyinBatchSubmitterV2()
    results = submitter.batch_submit(
        urls=urls,
        max_workers=1,
        delay_range=(delay_min, delay_max)
    )
    
    # 分析结果
    success_count = sum(1 for r in results if r['success'])
    total_count = len(results)
    
    print(f"\n📊 提交完成:")
    print(f"✅ 成功: {success_count}/{total_count}")
    print(f"📈 成功率: {(success_count/total_count*100):.1f}%")
    
    submitter.save_results(results)
    print(f"✅ 结果已保存到日志文件")

def main():
    """主菜单"""
    print("🎯 抖音刷量批量提交系统")
    print("=" * 40)
    
    while True:
        print("\n📋 请选择操作:")
        print("1. 快速测试")
        print("2. 批量提交")
        print("0. 退出")
        
        choice = input("\n请选择 (0-2): ").strip()
        
        if choice == '0':
            print("👋 感谢使用！")
            break
        elif choice == '1':
            quick_test()
        elif choice == '2':
            batch_submit()
        else:
            print("❌ 无效选择，请重新输入")
        
        input("\n按回车键继续...")

if __name__ == "__main__":
    main() 