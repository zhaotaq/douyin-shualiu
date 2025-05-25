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
import subprocess
import requests
import os
import base64
import yaml
import random

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
    
    submitter = DouyinBatchSubmitterV2(group_name='刷流专用')
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
    if total_count > 0:
        print(f"📈 成功率: {(success_count/total_count*100):.1f}%")
    else:
        print("📈 成功率: 0.0%（无有效提交）")
    
    submitter.save_results(results)
    print(f"✅ 结果已保存到日志文件")

def download_and_generate_config(sub_url, config_path, proxy_port, api_port):
    resp = requests.get(sub_url)
    try:
        content = base64.b64decode(resp.text).decode()
    except Exception:
        content = resp.text  # 可能直接是yaml
    config = yaml.safe_load(content)
    config['port'] = proxy_port
    config['external-controller'] = f'127.0.0.1:{api_port}'
    # 保留所有分组，自动识别Selector分组
    with open(config_path, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, allow_unicode=True)

def start_mihomo(mihomo_path, config_path):
    proc = subprocess.Popen([
        mihomo_path,
        '-d', '.',
        '-f', config_path
    ])
    return proc

def wait_mihomo_api(api_port, timeout=30):
    for _ in range(timeout):
        try:
            r = requests.get(f'http://127.0.0.1:{api_port}/proxies', timeout=1)
            if r.status_code == 200:
                return True
        except Exception:
            time.sleep(1)
    return False

def get_main_group_and_all_nodes(api_port):
    r = requests.get(f'http://127.0.0.1:{api_port}/proxies')
    data = r.json()
    # 兼容顶层为{"proxies": {...}}的结构
    if 'proxies' in data:
        data = data['proxies']
    # 自动识别第一个有all字段且不是provider的分组为主分组
    group_names = [k for k, v in data.items() if v.get('all') and not v.get('type', '').lower().endswith('provider')]
    if not group_names:
        raise RuntimeError('未找到任何分组')
    main_group = group_names[0]
    # 递归展开所有真实节点
    def collect_nodes(group_name, visited=None):
        if visited is None:
            visited = set()
        if group_name in visited:
            return []
        visited.add(group_name)
        group = data.get(group_name, {})
        nodes = group.get('all') or []
        real_nodes = []
        for n in nodes:
            n_type = data.get(n, {}).get('type', '').lower()
            if n in data and n_type in ('selector', 'urltest', 'fallback'):
                real_nodes.extend(collect_nodes(n, visited))
            else:
                real_nodes.append(n)
        return real_nodes
    all_nodes = collect_nodes(main_group)
    if not all_nodes:
        raise RuntimeError('主分组下未找到任何真实节点')
    return main_group, all_nodes

def switch_random_node_main_group(api_port, group_name, all_nodes):
    node = random.choice(all_nodes)
    resp = requests.put(f'http://127.0.0.1:{api_port}/proxies/{group_name}', json={'name': node})
    resp.raise_for_status()
    now = requests.get(f'http://127.0.0.1:{api_port}/proxies/{group_name}').json().get('now')
    if now != node:
        raise RuntimeError(f'切换节点失败: 期望{node}, 实际{now}')
    return node

def main():
    print('🎯 抖音刷量批量提交系统（自动代理集成版）')
    print('=' * 40)
    config_path = './clash_config.yaml'
    mihomo_path = './mihomo-windows-amd64.exe'
    proxy_port = 9950
    api_port = 9900
    # 检查配置文件是否存在
    if not os.path.exists(config_path):
        sub_url = input('请输入代理订阅链接: ').strip()
        print('⏬ 正在下载订阅并生成配置...')
        download_and_generate_config(sub_url, config_path, proxy_port, api_port)
    else:
        # 检查并修正端口
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        changed = False
        if config.get('mixed-port') != proxy_port:
            config['mixed-port'] = proxy_port
            changed = True
        if config.get('external-controller') != f'127.0.0.1:{api_port}':
            config['external-controller'] = f'127.0.0.1:{api_port}'
            changed = True
        if changed:
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, allow_unicode=True)
            print(f'已自动修正配置文件端口为 {proxy_port}/{api_port}')
        else:
            print(f'检测到已存在配置文件 {config_path}，将直接复用。')
    # 获取所有节点信息（只需一次）
    print('🚀 启动mihomo代理内核...')
    mihomo_proc = start_mihomo(mihomo_path, config_path)
    print('⏳ 等待代理API端口启动...')
    if not wait_mihomo_api(api_port):
        print('❌ mihomo启动失败')
        mihomo_proc.terminate()
        return
    print('✅ mihomo已启动，API可用')
    group_name, all_nodes = get_main_group_and_all_nodes(api_port)
    print(f'检测到主分组: {group_name}，共{len(all_nodes)}个真实节点')
    mihomo_proc.terminate()
    time.sleep(2)
    # 选择刷流模式
    urls = []
    print('请输入抖音视频链接（每行一个，输入空行结束）:')
    while True:
        url = input('链接: ').strip()
        if not url:
            break
        urls.append(url)
    if not urls:
        print('❌ 没有可提交的链接')
        return
    print(f'📋 共有 {len(urls)} 个链接待提交')
    delay_min = float(input('最小延迟时间（秒，默认3）: ') or '3')
    delay_max = float(input('最大延迟时间（秒，默认8）: ') or '8')
    confirm = input(f'\n确认提交 {len(urls)} 个链接？(y/n): ').lower()
    if confirm != 'y':
        print('❌ 已取消')
        return
    print(f'\n🚀 开始批量提交...')
    results = []
    for i, url in enumerate(urls, 1):
        # 每次都重启mihomo
        mihomo_proc = start_mihomo(mihomo_path, config_path)
        if not wait_mihomo_api(api_port):
            print('❌ mihomo启动失败')
            mihomo_proc.terminate()
            continue
        try:
            node = switch_random_node_main_group(api_port, group_name, all_nodes)
            print(f'🔄 已切换到主分组: {group_name} 节点: {node}')
        except Exception as e:
            print(f'❌ 节点切换失败: {e}')
            mihomo_proc.terminate()
            continue
        submitter = DouyinBatchSubmitterV2(base_url="https://longsiye.nyyo.cn")
        success, message, order_info = submitter.submit_single_url(url)
        result = {
            'url': url,
            'success': success,
            'message': message,
            'order_info': order_info,
            'submit_time': datetime.now().isoformat()
        }
        results.append(result)
        mihomo_proc.terminate()
        time.sleep(2)  # 等待端口释放
        if i < len(urls):
            delay = random.uniform(delay_min, delay_max)
            print(f'⏳ 等待 {delay:.1f} 秒...')
            time.sleep(delay)
    # 统计
    success_count = sum(1 for r in results if r['success'])
    total_count = len(results)
    print(f"\n📊 提交完成:")
    print(f"✅ 成功: {success_count}/{total_count}")
    if total_count > 0:
        print(f"📈 成功率: {(success_count/total_count*100):.1f}%")
    else:
        print("📈 成功率: 0.0%（无有效提交）")
    print('🛑 mihomo已关闭')

if __name__ == "__main__":
    main() 