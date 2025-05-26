# 抖音刷量批量提交系统

基于真实API接口的抖音视频刷量批量提交工具。

## 快速开始

1.  **克隆仓库:**
    ```bash
    git clone https://github.com/zhaotaq/douyin-shualiu.git
    cd douyin-shualiu
    ```

2.  **安装依赖:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **配置:**
    *   编辑 `config.json` 文件，根据需要修改 API 设置、提交设置和产品信息。
    *   确保 `clash_config.yaml` 是有效的 Clash/Mihomo 配置文件，并根据需要调整。
    *   将要刷量的抖音视频链接添加到 `douyin_urls.txt` 文件中，每行一个。

4.  **运行程序:**
    ```bash
    python main.py
    ```

## 功能说明

- **快速测试** - 测试单个链接，验证API连接
- **批量提交** - 批量提交多个视频链接
- **自动代理切换** - 每刷一个链接自动切换clash verge节点

## 文件说明

- `main.py` - 主程序（推荐使用）
- `douyin_batch_submitter_v2.py` - 核心提交逻辑
- `final_douyin_submitter.py` - 完整版程序
- `quick_start.py` - 快速启动脚本
- `logs/` - 日志文件目录
- `config.json` - 项目主要配置文件，包含 API、提交和产品信息。
- `clash_config.yaml` - Clash/Mihomo 代理配置文件。

## 使用方式

### 批量提交
1. 将链接保存到 `douyin_urls.txt` 文件，每行一个
2. 或在程序中手动输入链接

### 链接格式
```
https://www.douyin.com/video/7502340698369234567
https://v.douyin.com/iFhMj2R/
```

## Clash Verge 集成说明

- 程序会自动通过 Clash Verge API 切换节点，每刷一个链接自动切换一个节点。
- 代理端口：`7897`
- Clash Verge API 地址：`http://127.0.0.1:9097`
- 节点切换后会自动检测是否切换成功。
- 请确保 Clash Verge 已开启 RESTful API 并允许本地访问。
- 支持节点分组自动轮换。

## 注意事项

- 每个链接每天只能提交一次
- 系统有每日总提交限制
- 遇到限制属于正常现象
- 所有日志文件自动保存到 `logs/` 目录 