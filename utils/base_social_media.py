from pathlib import Path
from typing import List
import json
from datetime import datetime, timedelta
import csv

from conf import BASE_DIR

SOCIAL_MEDIA_DOUYIN = "douyin"
SOCIAL_MEDIA_TENCENT = "tencent"
SOCIAL_MEDIA_TIKTOK = "tiktok"
SOCIAL_MEDIA_BILIBILI = "bilibili"
SOCIAL_MEDIA_KUAISHOU = "kuaishou"

from utils.files_times import get_title_and_hashtags, generate_schedule_time_next_day
from utils.constant import TencentZoneTypes
from utils.log import tencent_logger


def get_supported_social_media() -> List[str]:
    return [SOCIAL_MEDIA_DOUYIN, SOCIAL_MEDIA_TENCENT, SOCIAL_MEDIA_TIKTOK, SOCIAL_MEDIA_KUAISHOU]


def get_cli_action() -> List[str]:
    return ["upload", "login", "watch"]


async def set_init_script(context):
    stealth_js_path = Path(BASE_DIR / "utils/stealth.min.js")
    await context.add_init_script(path=stealth_js_path)
    return context


def load_workflow_config(config_path: str):
    """Loads the workflow configuration from a JSON file."""
    config_file = Path(config_path)
    if not config_file.exists():
        raise FileNotFoundError(f"Workflow config file not found at {config_path}")
    with open(config_file, 'r', encoding='utf-8') as f:
        config = json.load(f)
    return config


async def run_workflow(config: dict | str):
    """Runs the multi-account and multi-video-type workflow."""
    
    generated_schedule_times = None
    
    workflow_config = None

    if isinstance(config, str):
        print(f"Loading workflow config from {config}")
        workflow_config = load_workflow_config(config)
        if 'generated_schedule' in workflow_config:
            generated_schedule_times = workflow_config.pop('generated_schedule')
            print(f"Found generated schedule with {len(generated_schedule_times)} entries from file.")
    else:
        print("Using provided workflow config dictionary.")
        workflow_config = config
        if 'generated_schedule' in workflow_config:
            generated_schedule_times = workflow_config.pop('generated_schedule')
            print(f"Found generated schedule with {len(generated_schedule_times)} entries from dictionary.")

    print("Workflow config loaded successfully." if isinstance(config, str) else "Using provided workflow config.")
    print("Starting workflow execution...")

    base_videos_path = Path(BASE_DIR) / "videos"
    base_cookies_path = Path(BASE_DIR) / "cookies"

    # Import uploader modules here to avoid circular dependency
    import os
    import asyncio
    import time
    from uploader.douyin_uploader.main import douyin_setup, DouYinVideo
    from uploader.ks_uploader.main import ks_setup, KSVideo
    from uploader.tencent_uploader.main import weixin_setup, TencentVideo
    from uploader.bilibili_uploader.main import BilibiliUploader, read_cookie_json_file, extract_keys_from_json

    from utils.files_times import get_title_and_hashtags, generate_schedule_time_next_day
    from utils.constant import TencentZoneTypes

    video_index_counter = 0

    for account in workflow_config.get('accounts', []):
        account_name = account.get('name')
        video_types = account.get('video_types', [])
        platforms = account.get('platforms', [])
        
        if not account_name:
            print("Warning: Skipping account with no name defined in config.")
            continue

        print(f"\nProcessing account: {account_name}")
        print(f"Video types: {video_types}")
        print(f"Platforms: {platforms}")

        for video_type in video_types:
            video_type_path = base_videos_path / account_name / video_type
            if not video_type_path.exists() or not video_type_path.is_dir():
                print(f"Warning: Video type directory not found: {video_type_path}. Skipping.")
                continue
            
            video_files = sorted(list(video_type_path.glob("**/*.mp4")))
            
            if not video_files:
                print(f"No MP4 videos found for video type '{video_type}' in {video_type_path}. Skipping.")
                continue

            print(f"Found {len(video_files)} videos for type '{video_type}': {[f.name for f in video_files]}")
            
            for index, video_file in enumerate(video_files):
                video_path_str = str(video_file)
                title, tags = get_title_and_hashtags(video_path_str)
                
                publish_date = 0

                if generated_schedule_times and video_index_counter < len(generated_schedule_times):
                    try:
                        publish_date_str = generated_schedule_times[video_index_counter]
                        publish_date = datetime.strptime(publish_date_str, '%Y-%m-%d %H:%M')
                        print(f"Using generated schedule time for video {video_file.name}: {publish_date}")
                    except Exception as e:
                        print(f"Warning: Failed to parse generated schedule time '{publish_date_str}' for video {video_file.name}: {e}. Using default immediate publish.")
                        publish_date = 0
                else:
                    print(f"Warning: No generated schedule time available for video {video_file.name}. Using default immediate publish.")
                    publish_date = 0

                video_index_counter += 1

                if not title:
                    print(f"Warning: Skipping video {video_file.name} due to missing title (.txt file).")
                    continue
                
                print(f"\n  Processing video: {video_file.name}")
                print(f"    Title: {title}")
                print(f"    Tags: {tags}")
                print(f"    Scheduled for: {publish_date if publish_date != 0 else 'Immediate'}")
                
                upload_tasks = []
                
                for platform in platforms:
                    print(f"    Attempting to upload to platform: {platform}")
                    
                    cookie_file = base_cookies_path / f"{platform}_uploader" / f"{account_name}.json"
                    
                    if not cookie_file.exists():
                        print(f"      Error: Cookie file not found for account '{account_name}' on platform '{platform}' at {cookie_file}. Skipping upload to this platform for this video.")
                        continue
                        
                    try:
                        if platform == SOCIAL_MEDIA_DOUYIN:
                            await douyin_setup(cookie_file, handle=False)
                            app = DouYinVideo(title, video_path_str, tags, publish_date, cookie_file)
                            task = asyncio.create_task(app.main(), name=f"{platform}_{account_name}_{video_file.name}")
                            upload_tasks.append(task)
                            
                        elif platform == SOCIAL_MEDIA_KUAISHOU:
                            await ks_setup(cookie_file, handle=False)
                            app = KSVideo(title, video_path_str, tags, publish_date, cookie_file)
                            task = asyncio.create_task(app.main(), name=f"{platform}_{account_name}_{video_file.name}")
                            upload_tasks.append(task)
                            
                        elif platform == SOCIAL_MEDIA_TENCENT:
                            await weixin_setup(cookie_file, handle=False)
                            category = TencentZoneTypes.LIFESTYLE.value
                            app = TencentVideo(title, video_path_str, tags, publish_date, cookie_file, category)
                            task = asyncio.create_task(app.main(), name=f"{platform}_{account_name}_{video_file.name}")
                            upload_tasks.append(task)
                            
                        elif platform == SOCIAL_MEDIA_BILIBILI:
                            bili_cookie_data = read_cookie_json_file(cookie_file)
                            bili_cookie_data = extract_keys_from_json(bili_cookie_data)
                            tid = 255
                            print(f"      Creating BilibiliUploader for {video_file.name}")
                            app = BilibiliUploader(bili_cookie_data, video_file, title, title, tid, tags, publish_date)
                            task = asyncio.create_task(app.upload(), name=f"{platform}_{account_name}_{video_file.name}")
                            upload_tasks.append(task)
                            
                        else:
                            print(f"      Warning: Unsupported platform '{platform}'. Skipping.")
                            
                    except FileNotFoundError as e:
                        print(f"      Error processing {video_file.name} for {platform} (Account: {account_name}): {e}")
                    except Exception as e:
                         print(f"      An unexpected error occurred during task creation for {video_file.name} to {platform} (Account: {account_name}): {e}")

                if upload_tasks:
                    print(f"\n    Waiting for uploads to {len(upload_tasks)} platforms to complete for {video_file.name}...")
                    results = await asyncio.gather(*upload_tasks, return_exceptions=True)
                    
                    # Process results/exceptions
                    for i, result in enumerate(results):
                        task = upload_tasks[i]
                        task_name = task.get_name()
                        platform_name = task_name.split('_')[0]
                        video_name = '_'.join(task_name.split('_')[2:])
                        
                        if isinstance(result, Exception):
                            try:
                                from playwright.async_api import TargetClosedError
                            except ImportError:
                                TargetClosedError = None

                            if TargetClosedError is not None and isinstance(result, TargetClosedError):
                                tencent_logger.warning(f"      Upload task for {platform_name} for {video_name} encountered TargetClosedError: {result}")
                            else:
                                import traceback
                                tencent_logger.error(f"      Upload to {platform_name} for {video_name} failed with unexpected error: {result}\n{traceback.format_exc()}")
                        else:
                            tencent_logger.success(f"      Upload to {platform_name} for {video_name} completed successfully.")
                        
                        # Add delay after Bilibili upload regardless of success or failure
                        if platform_name == SOCIAL_MEDIA_BILIBILI:
                            tencent_logger.info(f"      Waiting 30 seconds after Bilibili upload for {video_name}...")
                            await asyncio.sleep(30)

            await asyncio.sleep(10)

        await asyncio.sleep(30)

    print("Workflow execution finished.") 