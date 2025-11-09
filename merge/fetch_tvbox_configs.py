#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
脚本功能：从 GitHub 搜索包含关键词的代码片段，并更新到本仓库的 source.txt 文件中
配置说明：除了 GITHUB_TOKEN，其他所有配置（用户名、仓库名、文件路径、关键词）都已写死在代码里
适用环境：直接在 GitHub Actions 里运行
"""

import os
import requests
import base64
from datetime import datetime

# ======================
# 1. 配置区域（除 GITHUB_TOKEN 外，全部已写死）
# ======================

# 🔐 你的 GitHub Personal Access Token（必须要有 repo 权限！请替换为你自己的 Token）
GITHUB_TOKEN = os.getenv("GH_TOKEN")  
# 👤 你的 GitHub 用户名（已写死）
GITHUB_USERNAME = 'leexuben'
print(f"🔗 请求 URL: {url}")
print(f"🔐 请求头: {headers}")
print(f"⚠️ 响应状态码: {response.status_code}, 响应内容: {response.text}")

# 📦 你的目标仓库名（已写死，格式仅为仓库名）
REPO_NAME = 'TVBOX-merge'  # 注意：这里只是仓库名，不是 leexuben/TVBOX-merge

# 📂 你要保存/更新的文件路径（在仓库根目录下）
FILE_PATH = 'source.txt'  # 比如根目录下的 source.txt

# 🔍 搜索关键词（已写死）
KEYWORDS = ['荐片', '采集', '.spider']  # 你关注的关键词



# ======================
# 2. 搜索 GitHub 代码
# ======================

def search_github_code():
    headers = {
        'Authorization': f'token {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3+json'
    }

    all_contents = []

    for keyword in KEYWORDS:
        query = f'{keyword} in:file'
        url = f'https://api.github.com/search/code?q={query}&per_page=100'

        print(f"🔍 正在搜索关键词：'{keyword}' ...")
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            print(f"❌ 搜索 '{keyword}' 失败：状态码 {response.status_code}, 响应：{response.text}")
            continue

        data = response.json()
        items = data.get('items', [])

        print(f"✅ 找到 {len(items)} 个包含 '{keyword}' 的代码文件")

        for item in items:
            download_url = item.get('download_url')
            if not download_url:
                continue

            try:
                raw_resp = requests.get(download_url)
                if raw_resp.status_code == 200:
                    code = raw_resp.text
                    all_contents.append(f"=== 来源: {item['html_url']} ===\n{code}\n{'='*50}\n\n")
                else:
                    print(f"⚠️ 无法获取文件内容: {download_url}, 状态码: {raw_resp.status_code}")
            except Exception as e:
                print(f"⚠️ 获取文件出错 {download_url}: {e}")

    return all_contents



# ======================
# 3. 更新 source.txt 到 GitHub 仓库
# ======================

def update_source_txt(content_list):
    headers = {
        'Authorization': f'token {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3+json'
    }

    # 添加抓取时间
    current_time = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S (UTC)')
    header = f"🔍 自动抓取时间: {current_time}\n📌 以下为包含关键词的 tvbox 配置相关代码片段：\n\n"
    all_contents_with_header = [header] + content_list

    # 注意：REPO_NAME 已经是 'TVBOX-merge'，不是 'leexuben/TVBOX-merge'
    url = f'https://api.github.com/repos/{GITHUB_USERNAME}/{REPO_NAME}/contents/{FILE_PATH}'

    print(f"🔗 尝试更新/创建文件：{url}")  # 打印 URL，帮助调试

    # 获取当前 SHA（如果文件已存在）
    response = requests.get(url, headers=headers)
    sha = None
    if response.status_code == 200:
        data = response.json()
        sha = data.get('sha')
        print(f"📄 {FILE_PATH} 已存在，将更新")
    elif response.status_code == 404:
        print(f"📄 {FILE_PATH} 不存在，将创建")
    else:
        print(f"❌ 获取文件信息失败：状态码 {response.status_code}, 响应：{response.text}")
        return

    # 编码为 base64
    try:
        encoded_content = base64.b64encode('\n'.join(all_contents_with_header).encode('utf-8')).decode('utf-8')
    except Exception as e:
        print(f"❌ 编码内容失败：{e}")
        return

    data = {
        'message': '🤖 自动更新：抓取 tvbox 相关配置代码片段',
        'content': encoded_content,
        'branch': 'main'  # 如果你默认分支是 master，请改成 'master'
    }
    if sha:
        data['sha'] = sha

    # 提交更新
    resp = requests.put(url, headers=headers, json=data)
    if resp.status_code in [200, 201]:
        print("✅ 成功更新/创建 source.txt")
    else:
        print(f"❌ 更新失败：状态码 {resp.status_code}, 响应：{resp.text}")



# ======================
# 4. 主函数
# ======================

def main():
    print("🚀 开始抓取 tvbox 相关配置代码...")
    contents = search_github_code()
    if not contents:
        print("⚠️ 未找到任何匹配的代码文件。")
    else:
        print(f"📦 共收集到 {len(contents)} 个代码片段，准备保存")
        update_source_txt(contents)



if __name__ == '__main__':
    main()
