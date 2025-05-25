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

def batch_submit(mihomo_path, config_path, proxy_port, api_port, group_name, all_nodes, urls, delay_min, delay_max):
    """批量提交功能"""
    print("🚀 批量提交模式")
    print("=" * 40)
    
    print(f"📋 共有 {len(urls)} 个链接待提交")
    
    print(f"\n🚀 开始批量提交...")
    
    # Estimate total time based on delay
    avg_delay = (delay_min + delay_max) / 2
    estimated_min_time = len(urls) * avg_delay
    print(f'⏳ 估算最小完成时间 (仅考虑延迟): 约 {estimated_min_time:.1f} 秒')

    results = []
    used_nodes_in_batch = set() # Set to keep track of nodes successfully used in this batch

    for i, url in enumerate(urls, 1):
        # Print progress
        print(f'\n--- 处理进度: {i}/{len(urls)} --- URL: {url} ---')

        tried_nodes = set()
        success = False
        message = ''
        order_info = {}
        node_used_for_success = None
        
        # Attempt to submit with different nodes, up to 10 times or until successful/other error
        max_attempts = 10
        attempt_count = 0
        
        # Filter out used nodes for this URL attempt block
        available_nodes_for_url = [node for node in all_nodes if node not in used_nodes_in_batch]
        random.shuffle(available_nodes_for_url)

        # Use a while loop to control attempts based on result
        while attempt_count < max_attempts and available_nodes_for_url:
            attempt_count += 1
            
            # Select a node from the filtered and shuffled list
            # We shuffle the list once before the loop, so just pick the next available one
            node = available_nodes_for_url.pop(0)
            tried_nodes.add(node) # Keep track of nodes tried in total for this URL
            
            print(f'🔄 尝试节点 ({attempt_count}/{max_attempts}) for {url}: {node}')

            mihomo_proc = None # Initialize mihomo_proc for this attempt
            
            try:
                # Start mihomo for this attempt
                print(f'🚀 启动mihomo代理内核 for {url} with {node}...')
                mihomo_proc = start_mihomo(mihomo_path, config_path)
                print(f'⏳ 等待代理API端口启动 for {url} with {node}...')
                if not wait_mihomo_api(api_port):
                    print(f'❌ mihomo启动失败 for {url} with {node}，尝试下一个节点')
                    # Ensure mihomo is terminated before continuing
                    if mihomo_proc:
                        mihomo_proc.terminate()
                        time.sleep(2)
                    continue # Continue to next node attempt
                print(f'✅ mihomo已启动，API可用 for {url} with {node}')
                
                try:
                    # Switch node - Use the selected node
                    print(f'🔄 切换节点 to {node} for {url}...')
                    switch_random_node_main_group(api_port, group_name, [node])
                    print(f'✅ 节点 {node} 切换成功 for {url}')
                except Exception as e:
                    print(f'❌ 节点切换失败 ({node}) for {url}: {e}，尝试下一个节点')
                    # Ensure mihomo is terminated before continuing
                    if mihomo_proc:
                        mihomo_proc.terminate()
                        time.sleep(2)
                    continue # Continue to next node attempt

                # 可用节点，提交刷流
                submitter = DouyinBatchSubmitterV2(base_url="https://longsiye.nyyo.cn")
                
                submit_success = False
                submit_message = ''
                submit_order_info = {}
                last_error_message = '' # Variable to store the last error message for the URL

                try:
                    print(f'📤 使用节点 {node} 提交链接: {url}')
                    submit_success, submit_message, submit_order_info = submitter.submit_single_url(url)
                    
                    # If submission was successful, set success and break the node loop
                    if submit_success:
                        success = True # Mark overall success for this URL
                        message = submit_message
                        order_info = submit_order_info
                        node_used_for_success = node
                        used_nodes_in_batch.add(node) # Add successfully used node to the set
                        print(f'✅ 提交成功 for {url}！使用节点: {node}')
                        # Terminate mihomo before breaking
                        if mihomo_proc:
                            mihomo_proc.terminate()
                            time.sleep(2)
                        break # Success, break the node attempt loop for this URL
                        
                    # If submission failed but is a known transient error, try next node
                    elif "您今天已领取过" in submit_message or "重复提交" in submit_message:
                        print(f'ℹ️ 节点 {node} 已领取过/重复提交 for {url}，尝试下一个节点...')
                        last_error_message = submit_message # Store this message
                        # Terminate mihomo before continuing
                        if mihomo_proc:
                            mihomo_proc.terminate()
                            time.sleep(2)
                        # continue # Continue the while loop to try the next node - continue is implied if no break/return
                        
                    else:
                        # Other API failure, record message and potentially break
                        # Modified log message to escape backslashes
                        print(f'❌ 提交失败 ({node}) for {url}: {submit_message}，尝试下一个节点...') 
                        last_error_message = submit_message # Store this message
                        # Terminate mihomo before potentially breaking
                        if mihomo_proc:
                            mihomo_proc.terminate()
                            time.sleep(2)
                        # continue # Continue is implied unless max attempts reached or no nodes left

                except requests.exceptions.SSLError as ssl_error:
                    # Modified log message to escape backslashes
                    print(f'❌ 提交时发生SSL连接错误 ({node}) for {url}: {ssl_error}，尝试下一个节点...') 
                    last_error_message = f'SSL连接错误 ({node}): {ssl_error}' # Store error message
                    # Ensure mihomo is terminated before continuing
                    if mihomo_proc:
                        mihomo_proc.terminate()
                        time.sleep(2) # Short delay after exception
                    continue # Continue the while loop to try the next node
                    
                except Exception as api_error:
                     # Catch other potential exceptions from submit_single_url
                     print(f'❌ 提交时发生其他异常 ({node}) for {url}: {api_error}，停止尝试该链接的其他节点') # Modified log
                     last_error_message = f'提交异常 ({node}): {api_error}' # Store error message
                     # Terminate mihomo
                     if mihomo_proc:
                        mihomo_proc.terminate()
                        time.sleep(2) # Short delay after exception
                     # This is a more critical error, break the node attempt loop for this URL
                     break # Break the node attempt loop for this URL

                # After a submission attempt (success, transient failure, or handled exception), mihomo should be terminated.
                # The terminate is now handled within the try/except blocks or before break/continue.

            except Exception as e:
                # Catch exceptions during mihomo start, switch, or before submission try block
                print(f'❌ 处理节点时异常 ({node}) for {url}: {e}，尝试下一个节点') # Modified log
                last_error_message = f'处理节点异常 ({node}): {e}' # Store error message
                # Ensure mihomo is terminated before continuing
                if mihomo_proc:
                    mihomo_proc.terminate()
                    time.sleep(2) # Short delay after exception
                continue # Continue the while loop to try the next node

        # End of node attempt loop for the current URL
        # Check if submission was successful with any node
        if success:
            print(f"✅ URL {url} 最终提交成功 (使用节点: {node_used_for_success})")
        else:
            # If loop finished and not success, report the last recorded error or a general failure
            # Modified log message to escape backslashes
            final_message = last_error_message if last_error_message else f'❌ URL {url} 在所有 {attempt_count} 次尝试后仍然失败。无具体错误信息。'
            print(f"❌ URL {url} 最终提交失败 (原因: {final_message})")
            message = final_message # Update the message for the result object

        # Record the result for this URL
        result = {
            'url': url,
            'success': success,
            'message': message, # Use the final message
            'order_info': order_info,
            'submit_time': datetime.now().isoformat(),
            'node_used': node_used_for_success # Record node only on final success
        }
        results.append(result)
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
    
    print('🛑 批量提交任务完成') # Update message

    # Save results to a JSON file
    try:
        existing_results = []
        if os.path.exists('submission_results.json'):
            with open('submission_results.json', 'r', encoding='utf-8') as f:
                try:
                    existing_results = json.load(f)
                except json.JSONDecodeError:
                    print("⚠️ 现有 submission_results.json 文件内容无效，将覆盖。")
                    existing_results = []

        existing_results.extend(results)

        with open('submission_results.json', 'w', encoding='utf-8') as f:
            json.dump(existing_results, f, indent=4, ensure_ascii=False)
        print("✅ 详细提交结果已保存到 submission_results.json")
    except Exception as e:
        print(f"❌ 保存结果到文件失败: {e}")

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
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
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

def is_node_available(proxy_port):
    proxies = {
        'http': f'http://127.0.0.1:{proxy_port}',
        'https': f'http://127.0.0.1:{proxy_port}',
    }
    try:
        resp = requests.get('https://longsiye.nyyo.cn', proxies=proxies, timeout=5, verify=False)
        return resp.status_code == 200
    except Exception:
        return False

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
    print('🚀 启动mihomo获取节点信息...')
    mihomo_proc_init = start_mihomo(mihomo_path, config_path)
    print('⏳ 等待代理API端口启动...')
    if not wait_mihomo_api(api_port):
        print('❌ mihomo启动失败，无法获取节点列表')
        mihomo_proc_init.terminate()
        time.sleep(2)
        return # Exit main function
    print('✅ mihomo已启动，API可用，正在获取节点列表...')

    try:
        group_name, all_nodes = get_main_group_and_all_nodes(api_port)
        print(f'检测到主分组: {group_name}，共{len(all_nodes)}个真实节点')
    except Exception as e:
        print(f'❌ 获取节点信息失败: {e}')
        mihomo_proc_init.terminate()
        time.sleep(2)
        return # Exit main function
    finally:
        # Terminate the initial mihomo process used only for getting the node list
        mihomo_proc_init.terminate()
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
    
    # 调用批量提交函数，传入参数
    batch_submit(mihomo_path, config_path, proxy_port, api_port, group_name, all_nodes, urls, delay_min, delay_max)

if __name__ == "__main__":
    main() 