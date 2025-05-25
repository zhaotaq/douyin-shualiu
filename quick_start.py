#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
抖音刷量批量提交系统 - 快速启动脚本
"""

from douyin_batch_submitter import DouyinBatchSubmitter

def quick_test():
    """快速测试功能"""
    print("🚀 快速测试模式")
    print("=" * 40)
    
    # 使用您实际测试过的链接
    test_url = "https://www.douyin.com/video/7502340698369212055"
    
    print(f"📤 测试链接: {test_url}")
    
    # 创建提交器
    submitter = DouyinBatchSubmitter()
    
    # 提交单个链接测试
    success, message, order_info = submitter.submit_single_url(test_url)
    
    if success:
        print("✅ 测试成功！")
        print(f"📋 订单信息:")
        print(f"   - 订单号: {order_info.get('order_id', 'N/A')}")
        print(f"   - 商品名称: {order_info.get('product_name', 'N/A')}")
        print(f"   - 金额: {order_info.get('amount', 'N/A')}元")
        print(f"   - 状态: {order_info.get('status', 'N/A')}")
        print(f"   - 提交时间: {order_info.get('submit_time', 'N/A')}")
    else:
        print(f"❌ 测试失败: {message}")
    
    return success

def quick_batch():
    """快速批量提交"""
    print("🚀 快速批量提交")
    print("=" * 40)
    
    # 获取用户输入的链接
    urls = []
    print("请输入抖音视频链接（每行一个，输入空行结束）:")
    
    while True:
        url = input().strip()
        if not url:
            break
        urls.append(url)
    
    if not urls:
        print("❌ 没有输入任何链接")
        return
    
    print(f"\n📋 共输入 {len(urls)} 个链接，开始批量提交...")
    
    # 创建提交器并执行
    submitter = DouyinBatchSubmitter()
    results = submitter.batch_submit(
        urls=urls,
        max_workers=1,      # 安全的单线程模式
        delay_range=(2, 4)  # 2-4秒延迟
    )
    
    # 保存结果
    submitter.save_results(results)
    
    print(f"\n✅ 批量提交完成！结果已保存到文件。")

def main():
    """主函数"""
    print("🎯 抖音刷量批量提交系统 - 快速启动")
    print("=" * 50)
    print("基于您的实际测试数据构建的自动化系统")
    print("=" * 50)
    
    while True:
        print("\n选择操作:")
        print("1. 快速测试（单个链接）")
        print("2. 批量提交")
        print("0. 退出")
        
        choice = input("\n请选择 (0-2): ").strip()
        
        if choice == '0':
            print("👋 感谢使用！")
            break
        elif choice == '1':
            quick_test()
        elif choice == '2':
            quick_batch()
        else:
            print("❌ 无效选择")
        
        input("\n按回车键继续...")

if __name__ == "__main__":
    main() 