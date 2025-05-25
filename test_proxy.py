import requests

proxy_port = 9950  # 和 main.py 里保持一致
proxies = {
    'http': f'http://127.0.0.1:{proxy_port}',
    'https': f'http://127.0.0.1:{proxy_port}',
}
try:
    resp = requests.get('https://www.youtube.com/', proxies=proxies, timeout=10, verify=False)
    print('代理访问YouTube成功，状态码:', resp.status_code)
    print('页面标题:', resp.text.split('<title>')[1].split('</title>')[0])
except Exception as e:
    print('代理访问YouTube失败:', e)