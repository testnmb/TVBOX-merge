import os
import requests
import base64
from datetime import datetime

# ======================
# 1. 从 GitHub Secrets 读取配置
# ======================

GITHUB_TOKEN = os.getenv('GH_TOKEN')  # 用于读写你的目标仓库
GITHUB_USERNAME = os.getenv('GH_USERNAME', '你的用户名')  # 例如 'hxy97'
REPO_NAME = os.getenv('REPO_NAME', '你的仓库名')  # 例如 'tvbox-config-collector'
FILE_PATH = os.getenv('FILE_PATH', 'source.txt')  # 保存结果的文件，如 source.txt

# 🔍 搜索关键词（你可以自行增删，比如 tvbox、m3u、源、接口等）
KEYWORDS = ['荐片', '采集', '.spider']  # 你关注的 tvbox 配置相关关键词

# ======================
# 2. 搜索代码文件内容
# ======================

def search_github_code():
    headers = {
        'Authorization': f'token {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3+json'
    }

    all_contents = []

    for keyword in KEYWORDS:
        query = f'{keyword} in:file'
        url = f'https://api.github.com/search/code?q={query}&per_page=100'

        print(f"🔍 正在搜索关键词：'{keyword}' ...")
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            print(f"❌ 搜索 '{keyword}' 失败：{response.status_code}, {response.text}")
            continue

        data = response.json()
        items = data.get('items', [])

        print(f"✅ 找到 {len(items)} 个包含 '{keyword}' 的代码文件")

        for item in items:
            download_url = item.get('download_url')
            if not download_url:
                continue

            try:
                raw_resp = requests.get(download_url)
                if raw_resp.status_code == 200:
                    code = raw_resp.text
                    all_contents.append(f"=== 来源: {item['html_url']} ===\n{code}\n{'='*50}\n\n")
                else:
                    print(f"⚠️ 无法获取文件内容: {download_url}, 状态码: {raw_resp.status_code}")
            except Exception as e:
                print(f"⚠️ 获取文件出错 {download_url}: {e}")

    return all_contents

# ======================
# 3. 更新 source.txt 到你的 GitHub 仓库
# ======================

def update_source_txt(content_list):
    headers = {
        'Authorization': f'token {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3+json'
    }

    # 添加抓取时间
    current_time = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S (UTC)')
    header = f"🔍 自动抓取时间: {current_time}\n📌 以下为包含关键词的 tvbox 配置相关代码片段：\n\n"
    all_contents_with_header = [header] + content_list

    url = f'https://api.github.com/repos/{GITHUB_USERNAME}/{REPO_NAME}/contents/{FILE_PATH}'

    # 获取当前 SHA（如果文件已存在）
    response = requests.get(url, headers=headers)
    sha = None
    if response.status_code == 200:
        data = response.json()
        sha = data.get('sha')
        print(f"📄 {FILE_PATH} 已存在，将更新")
    elif response.status_code == 404:
        print(f"📄 {FILE_PATH} 不存在，将创建")
    else:
        print(f"❌ 获取文件信息失败：{response.status_code}, {response.text}")
        return

    # 编码为 base64
    encoded_content = base64.b64encode('\n'.join(all_contents_with_header).encode('utf-8')).decode('utf-8')

    data = {
        'message': '🤖 自动更新：抓取 tvbox 相关配置代码片段',
        'content': encoded_content,
        'branch': 'main'  # 或 master
    }
    if sha:
        data['sha'] = sha

    # 提交更新
    resp = requests.put(url, headers=headers, json=data)
    if resp.status_code in [200, 201]:
        print("✅ 成功更新/创建 source.txt")
    else:
        print(f"❌ 更新失败：{resp.status_code}, {resp.text}")

# ======================
# 4. 主函数
# ======================

def main():
    print("🚀 开始抓取 tvbox 相关配置代码...")
    contents = search_github_code()
    if not contents:
        print("⚠️ 未找到任何匹配的代码文件。")
    else:
        print(f"📦 共收集到 {len(contents)} 个代码片段，准备保存")
        update_source_txt(contents)

if __name__ == '__main__':
    main()
