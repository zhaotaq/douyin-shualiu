#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
抖音刷量批量提交系统 - V2版本
基于真实API接口实现自动化批量提交
"""

import requests
import time
import json
import random
import re
import hashlib
from typing import List, Dict, Optional, Tuple
from urllib.parse import quote
import logging
from datetime import datetime
import ssl
import urllib3
import os
import httpx

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class DouyinBatchSubmitterV2:
    """抖音刷量批量提交器 - 只负责刷流，代理切换由外部(main.py)控制"""
    def __init__(self, base_url: str = "https://longsiye.nyyo.cn", proxy_port: int = 9950):
        self.base_url = base_url
        self.session = requests.Session()
        self.setup_session(proxy_port)
        self.setup_logging()
        
        # API端点
        self.endpoints = {
            'pay': f"{base_url}/ajax.php?act=pay",  # 真正的提交接口
            'query': f"{base_url}/ajax.php?act=query",
            'gettool': f"{base_url}/ajax.php?act=gettool",
            'getcount': f"{base_url}/ajax.php?act=getcount"
        }
        
        # 商品配置
        self.product_config = {
            'douyin_play': {
                'tid': '3210',
                'cid': '58',
                'name': '免费-DY作品播放1000个',
                'value': '1000',
                'num': '1'
            }
        }
        
        # 统计信息
        self.stats = {
            'total_submitted': 0,
            'success_count': 0,
            'failed_count': 0,
            'start_time': None
        }
    
    def setup_session(self, proxy_port):
        # 所有请求都走本地clash代理
        self.session.proxies = {
            'http': f'http://127.0.0.1:{proxy_port}',
            'https': f'http://127.0.0.1:{proxy_port}',
        }
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        })

    def setup_logging(self):
        """设置日志记录"""
        # 确保logs目录存在
        if not os.path.exists('logs'):
            os.makedirs('logs')
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
        )
        self.logger = logging.getLogger(__name__)
    
    def validate_douyin_url(self, url: str) -> bool:
        """验证抖音视频链接格式"""
        patterns = [
            r'https://www\.douyin\.com/video/\d+',
            r'https://v\.douyin\.com/\w+',
            r'https://www\.iesdouyin\.com/share/video/\d+'
        ]
        
        for pattern in patterns:
            if re.match(pattern, url):
                return True
        return False
    
    def generate_hashsalt(self, tid: str, inputvalue: str, num: str) -> str:
        """生成hashsalt参数"""
        # 基于观察到的模式生成哈希值
        # 这里需要根据实际的哈希算法来实现
        # 暂时使用随机生成的32位十六进制字符串
        import secrets
        return secrets.token_hex(16)
    
    def submit_single_url(self, douyin_url: str, max_retries: int = 3) -> Tuple[bool, str, Dict]:
        """提交单个抖音链接 - 增强版本，包含重试机制"""
        for attempt in range(max_retries):
            try:
                # 验证链接格式
                if not self.validate_douyin_url(douyin_url):
                    return False, "无效的抖音链接格式", {}
                
                # 准备提交参数
                tid = self.product_config['douyin_play']['tid']
                inputvalue = douyin_url
                num = self.product_config['douyin_play']['num']
                hashsalt = self.generate_hashsalt(tid, inputvalue, num)
                
                # 构造提交数据
                submit_data = {
                    'tid': tid,
                    'inputvalue': inputvalue,
                    'num': num,
                    'hashsalt': hashsalt
                }
                
                if attempt == 0:  # 只在第一次尝试时记录
                    self.logger.info(f"📤 提交链接: {douyin_url}")
                    self.logger.info(f"📋 参数: tid={tid}, num={num}, hashsalt={hashsalt}")
                else:
                    self.logger.info(f"🔄 重试第 {attempt} 次: {douyin_url}")
                
                # 提交订单 - 增加更多错误处理
                response = self.session.post(
                    self.endpoints['pay'], 
                    data=submit_data, 
                    timeout=15,
                    allow_redirects=True
                )
                response.raise_for_status()
                
                result = response.json()
                
                # 修复成功判断逻辑 - 检查消息内容而不只是code
                success_indicators = ["下单成功", "提交成功", "订单创建成功"]
                duplicate_indicators = ["请勿重复提交", "已添加过", "重复提交"]
                error_msg = result.get('msg', '提交失败')
                
                # 判断是否成功：code为0 或者 消息包含成功标识
                is_success = (result.get('code') == 0) or any(indicator in error_msg for indicator in success_indicators)
                # 判断是否为重复提交（也算验证成功）
                is_duplicate = any(indicator in error_msg for indicator in duplicate_indicators)
                
                if is_success:
                    order_info = {
                        'douyin_url': douyin_url,
                        'tid': tid,
                        'num': num,
                        'hashsalt': hashsalt,
                        'response': result,
                        'submit_time': datetime.now().isoformat(),
                        'attempts': attempt + 1,
                        'status': 'success'
                    }
                    
                    self.logger.info(f"✅ 提交成功: {douyin_url} -> {error_msg}")
                    return True, error_msg, order_info
                elif is_duplicate:
                    order_info = {
                        'douyin_url': douyin_url,
                        'tid': tid,
                        'num': num,
                        'hashsalt': hashsalt,
                        'response': result,
                        'submit_time': datetime.now().isoformat(),
                        'attempts': attempt + 1,
                        'status': 'duplicate_success'
                    }
                    
                    self.logger.info(f"✅ 验证成功（重复提交限制）: {douyin_url} -> {error_msg}")
                    return True, f"验证成功: {error_msg}", order_info
                else:
                    self.logger.error(f"❌ 提交失败: {douyin_url} -> {error_msg}")
                    return False, error_msg, {'error_type': 'api_error', 'response': result}
                    
            except (requests.exceptions.SSLError, ssl.SSLError) as e:
                error_msg = f"SSL连接错误 (尝试 {attempt + 1}/{max_retries}): {e}"
                self.logger.warning(error_msg)
                
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 2  # 递增等待时间
                    self.logger.info(f"⏳ 等待 {wait_time} 秒后重试...")
                    time.sleep(wait_time)
                    continue
                else:
                    self.logger.error(f"❌ SSL连接最终失败: {douyin_url}")
                    return False, f"SSL连接失败: {e}", {'error_type': 'ssl_error'}
                    
            except requests.exceptions.ConnectionError as e:
                error_msg = f"网络连接错误 (尝试 {attempt + 1}/{max_retries}): {e}"
                self.logger.warning(error_msg)
                
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 2
                    self.logger.info(f"⏳ 等待 {wait_time} 秒后重试...")
                    time.sleep(wait_time)
                    continue
                else:
                    self.logger.error(f"❌ 网络连接最终失败: {douyin_url}")
                    return False, f"网络连接失败: {e}", {'error_type': 'connection_error'}
                    
            except requests.exceptions.RequestException as e:
                error_msg = f"网络请求异常: {e}"
                self.logger.error(f"❌ 提交失败: {douyin_url} -> {error_msg}")
                return False, error_msg, {'error_type': 'network_error'}
            except Exception as e:
                error_msg = f"未知异常: {e}"
                self.logger.error(f"❌ 提交失败: {douyin_url} -> {error_msg}")
                return False, error_msg, {'error_type': 'unknown_error'}
        
        # 如果所有重试都失败了
        return False, "所有重试都失败了", {'error_type': 'max_retries_exceeded'}
    
    def batch_submit(self, urls: List[str], max_workers: int = 1, delay_range: Tuple[int, int] = (3, 8)) -> List[Dict]:
        """批量提交抖音链接"""
        self.stats['start_time'] = datetime.now()
        self.stats['total_submitted'] = len(urls)
        
        results = []
        
        self.logger.info(f"🚀 开始批量提交，共 {len(urls)} 个链接")
        self.logger.info(f"📋 使用真实API接口: {self.endpoints['pay']}")
        
        for i, url in enumerate(urls, 1):
            self.logger.info(f"📤 提交进度: {i}/{len(urls)} - {url}")
            
            success, message, order_info = self.submit_single_url(url)
            
            result = {
                'url': url,
                'success': success,
                'message': message,
                'order_info': order_info,
                'submit_time': datetime.now().isoformat()
            }
            results.append(result)
            
            if success:
                self.stats['success_count'] += 1
            else:
                self.stats['failed_count'] += 1
            
            # 随机延迟
            if i < len(urls):
                delay = random.uniform(delay_range[0], delay_range[1])
                self.logger.info(f"⏳ 等待 {delay:.1f} 秒...")
                time.sleep(delay)
        
        self.print_summary()
        return results
    
    def print_summary(self):
        """打印提交统计摘要"""
        end_time = datetime.now()
        duration = end_time - self.stats['start_time']
        
        self.logger.info("=" * 60)
        self.logger.info("📊 批量提交统计摘要")
        self.logger.info("=" * 60)
        self.logger.info(f"总提交数量: {self.stats['total_submitted']}")
        self.logger.info(f"成功数量: {self.stats['success_count']}")
        self.logger.info(f"失败数量: {self.stats['failed_count']}")
        if self.stats['total_submitted'] > 0:
            self.logger.info(f"成功率: {(self.stats['success_count']/self.stats['total_submitted']*100):.1f}%")
        else:
            self.logger.info("成功率: 0.0%（无有效提交）")
        self.logger.info(f"总耗时: {duration}")
        self.logger.info("=" * 60)
    
    def save_results(self, results: List[Dict], filename: str = None):
        """保存提交结果到文件"""
        if filename is None:
            filename = f"logs/douyin_submit_results_v2_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        try:
            # 处理datetime序列化问题
            stats_copy = self.stats.copy()
            if stats_copy.get('start_time'):
                stats_copy['start_time'] = stats_copy['start_time'].isoformat()
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump({
                    'summary': stats_copy,
                    'api_endpoint': self.endpoints['pay'],
                    'product_config': self.product_config,
                    'results': results
                }, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"📁 结果已保存到: {filename}")
        except Exception as e:
            self.logger.error(f"保存结果失败: {e}")
    
    def test_connection(self) -> bool:
        """测试连接"""
        self.logger.info("🔧 测试API连接...")
        
        try:
            resp = self.session.get(self.base_url, timeout=5)
            return resp.status_code == 200
        except Exception:
            return False


def main():
    """主函数 - 测试V2版本"""
    print("🎯 抖音刷量批量提交系统 - V2版本")
    print("=" * 50)
    print("基于真实API接口构建")
    print("=" * 50)
    
    # 创建V2版提交器
    submitter = DouyinBatchSubmitterV2()
    
    # 测试连接
    submitter.test_connection()
    
    # 测试单个链接
    test_url = "https://www.douyin.com/video/7502340698369212200"  # 使用新的测试链接
    print(f"\n📤 测试链接: {test_url}")
    
    success, message, order_info = submitter.submit_single_url(test_url)
    
    if success:
        print("✅ 测试成功！")
        print(f"📋 订单信息:")
        for key, value in order_info.items():
            print(f"   {key}: {value}")
    else:
        print(f"❌ 测试结果: {message}")
        if order_info.get('error_type') == 'duplicate':
            print("ℹ️ 这是正常的重复提交限制")
    
    print("\n" + "=" * 50)


if __name__ == "__main__":
    main() 