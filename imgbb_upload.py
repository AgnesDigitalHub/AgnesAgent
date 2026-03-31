#!/usr/bin/env python3
"""
imgbb 图片上传工具
用法: python imgbb_upload.py <图片路径>
"""

import sys
import json
import base64
import urllib.request
import urllib.parse
import os

# 在这里填入你的 imgbb API Key
# 获取地址: https://api.imgbb.com/
API_KEY = "YOUR_API_KEY_HERE"


def upload_image(image_path):
    """上传图片到 imgbb"""
    
    if not os.path.exists(image_path):
        print(f"错误: 文件不存在 - {image_path}")
        return None
    
    # 读取图片并转为 base64
    with open(image_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode("utf-8")
    
    # 准备请求数据
    data = urllib.parse.urlencode({
        "key": API_KEY,
        "image": image_data,
    }).encode("utf-8")
    
    # 发送请求
    try:
        req = urllib.request.Request(
            "https://api.imgbb.com/1/upload",
            data=data,
            method="POST"
        )
        
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode("utf-8"))
            
        if result.get("success"):
            return result["data"]
        else:
            print(f"上传失败: {result}")
            return None
            
    except Exception as e:
        print(f"上传出错: {e}")
        return None


def copy_to_clipboard(text):
    """复制文本到剪贴板"""
    try:
        # Linux (xclip)
        import subprocess
        subprocess.run(["xclip", "-selection", "clipboard"], input=text.encode(), check=True)
        return True
    except:
        try:
            # macOS
            import subprocess
            subprocess.run(["pbcopy"], input=text.encode(), check=True)
            return True
        except:
            try:
                # Windows
                import subprocess
                subprocess.run(["clip"], input=text.encode(), check=True)
                return True
            except:
                return False


def main():
    if len(sys.argv) < 2:
        print("用法: python imgbb_upload.py <图片路径>")
        print("示例: python imgbb_upload.py screenshot.png")
        sys.exit(1)
    
    # 检查 API Key
    if API_KEY == "YOUR_API_KEY_HERE":
        print("错误: 请先在脚本中设置你的 imgbb API Key")
        print("获取地址: https://api.imgbb.com/")
        sys.exit(1)
    
    image_path = sys.argv[1]
    
    print(f"正在上传: {image_path}")
    result = upload_image(image_path)
    
    if result:
        print("\n" + "=" * 50)
        print("上传成功！")
        print("=" * 50)
        
        # 显示各种链接格式
        direct_link = result["url"]
        markdown = f"![image]({direct_link})"
        html = f'<img src="{direct_link}" alt="image">'
        
        print(f"\n直接链接:\n{direct_link}")
        print(f"\nMarkdown:\n{markdown}")
        print(f"\nHTML:\n{html}")
        
        # 尝试复制 Markdown 到剪贴板
        if copy_to_clipboard(markdown):
            print("\n✓ Markdown 格式已复制到剪贴板")
        else:
            print("\n⚠ 无法自动复制，请手动复制上方内容")
        
        print("\n" + "=" * 50)
    else:
        print("上传失败")
        sys.exit(1)


if __name__ == "__main__":
    main()