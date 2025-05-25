import httpx
import time
import json

def test_proxies_api():
    time.sleep(2)  # 等待 mihomo 启动
    try:
        response = httpx.get('http://127.0.0.1:9900/proxies')
        data = response.json()
        print(json.dumps(data, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    test_proxies_api() 