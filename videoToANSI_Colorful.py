import cv2
import os
import sys
import json
import numpy as np
import base64

def create_color_ascii_html(video_path, fps, output_file="color_ascii_video.html", width=100, background_color="#000"):
    """将视频转换为彩色ASCII动画HTML（自动播放）"""
    
    if not os.path.isfile(video_path):
        print(f"错误: 视频文件不存在 '{video_path}'")
        sys.exit(1)
    
    # 优化的字符映射表
    ASCII_MAP =" .,-~:;=!*#$@"
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print("错误: 无法打开视频文件")
        sys.exit(1)
    
    # 获取视频详细信息
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    original_fps = cap.get(cv2.CAP_PROP_FPS)
    video_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    video_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    print(f"视频信息: {total_frames}帧 | {original_fps:.1f} FPS | {video_width}x{video_height}")
    
    # 处理所有帧
    frames = []  # 存储每帧的ASCII数据
    processed = 0
    
    # 获取第一帧分析亮度范围
    ret, first_frame = cap.read()
    if not ret:
        print("错误: 无法读取视频帧")
        sys.exit(1)
    
    # 转换为HSV色彩空间分析亮度
    hsv = cv2.cvtColor(first_frame, cv2.COLOR_BGR2HSV)
    v_channel = hsv[:, :, 2]
    global_min = np.min(v_channel)
    global_max = np.max(v_channel)
    
    print(f"亮度范围: {global_min}-{global_max}")
    
    # 重置视频读取器
    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # 保留原始彩色图像
            color_frame = frame.copy()
            
            # 转换为HSV色彩空间获取亮度通道
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            v_channel = hsv[:, :, 2]
            
            # 调整尺寸
            aspect_ratio = frame.shape[0] / frame.shape[1]
            height = int(width * aspect_ratio * 0.5)  # 字符高度补偿
            
            resized_color = cv2.resize(color_frame, (width, height))
            resized_v = cv2.resize(v_channel, (width, height))
            
            # 转换为彩色ASCII
            ascii_frame = ""
            for y in range(height):
                for x in range(width):
                    # 获取像素颜色
                    b, g, r = resized_color[y, x]
                    color_hex = f"#{r:02x}{g:02x}{b:02x}"
                    
                    # 获取亮度值用于选择字符
                    brightness = resized_v[y, x]
                    normalized = min(max((brightness - global_min) / (global_max - global_min + 1e-5), 0), 1)
                    index = int(normalized * (len(ASCII_MAP) - 1))
                    char = ASCII_MAP[index]
                    
                    # 创建带颜色的字符
                    ascii_frame += f'<span style="color:{color_hex}">{char}</span>'
                ascii_frame += "\n"
            
            frames.append(ascii_frame)
            processed += 1
            
            # 显示进度
            if processed % 10 == 0 or processed == total_frames:
                progress = processed / total_frames * 100
                print(f"\r处理进度: {processed}/{total_frames}帧 ({progress:.1f}%)", end="", flush=True)
    
    finally:
        cap.release()
    
    if not frames:
        print("\n错误: 没有生成任何帧数据!")
        print("可能原因:")
        print("1. 视频文件格式不受支持")
        print("2. 视频文件损坏")
        print("3. OpenCV无法解码视频")
        sys.exit(1)
    
    print(f"\n成功处理: {processed}帧")
    
    # 生成HTML内容
    frames_js = ",\n".join([json.dumps(frame) for frame in frames])
    
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>彩色ASCII视频播放器</title>
    <style>
        * {{ 
            margin: 0; 
            padding: 0; 
            box-sizing: border-box; 
        }}
        body {{ 
            background-color: {background_color} !important;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            overflow: hidden;
            font-family: 'Courier New', monospace;
        }}
        #ascii-container {{
            background-color: {background_color};
            padding: 10px;
            max-width: 100%;
            overflow: auto;
        }}
        #ascii-display {{
            white-space: pre;
            font-size: 12px;
            line-height: 1;
            letter-spacing: 0;
        }}
        .status {{
            color: #0f0;
            font-family: Arial;
            font-size: 12px;
            text-align: center;
            margin-top: 10px;
        }}
    </style>
</head>
<body>
    <div id="ascii-container">
        <div id="ascii-display">正在加载...</div>
        <div class="status" id="status">准备播放</div>
    </div>

    <script>
        // 帧数据数组
        const frames = [
            {frames_js}
        ];
        
        console.log("帧数据加载完成，数量:", frames.length);
        
        // 播放器参数
        let currentFrame = 0;
        const fps = {fps};
        const frameDelay = 1000 / fps;
        let lastTime = 0;
        let requestId;
        
        function renderFrame(timestamp) {{
            if (!lastTime) lastTime = timestamp;
            
            // 计算经过的时间
            const elapsed = timestamp - lastTime;
            
            // 确保精确播放
            if (elapsed >= frameDelay) {{
                try {{
                    // 更新显示
                    document.getElementById('ascii-display').innerHTML = frames[currentFrame];
                    // document.getElementById('status').textContent = `播放中: 帧 ${{currentFrame+1}}/${{frames.length}}`;
                    
                    // 前进帧计数
                    currentFrame = (currentFrame + 1) % frames.length;
                    
                    // 更新最后时间
                    lastTime = timestamp;
                }} catch (error) {{
                    console.error("渲染错误:", error);
                    document.getElementById('status').textContent = "渲染错误: " + error.message;
                }}
            }}
            
            // 继续请求下一帧
            requestId = requestAnimationFrame(renderFrame);
        }}
        
        // 开始播放
        window.addEventListener('DOMContentLoaded', () => {{
            console.log("DOM已加载，开始播放");
            if (frames.length > 0) {{
                try {{
                    document.getElementById('ascii-display').innerHTML = frames[0];
                    document.getElementById('status').textContent = "开始播放...";
                    renderFrame(performance.now());
                }} catch (error) {{
                    console.error("初始化错误:", error);
                    document.getElementById('status').textContent = "初始化错误: " + error.message;
                }}
            }} else {{
                console.error("错误: 没有可播放的帧数据");
                document.getElementById('status').textContent = "错误: 没有帧数据";
            }}
        }});
    </script>
</body>
</html>"""
    
    # 写入HTML文件
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"\n生成彩色ASCII播放器: {output_file}")
        print(f"文件大小: {os.path.getsize(output_file)//1024}KB")
    except Exception as e:
        print(f"\n❌ 写入文件失败: {e}")
        print(f"请检查输出路径: {output_file}")
        print("尝试使用绝对路径或不同文件名")
        sys.exit(1)
    
    return output_file

if __name__ == "__main__":
    # 配置参数
    VIDEO_PATH = "11.mp4"
    OUTPUT_FILE = "color_ascii_video.html"
    CHARACTER_WIDTH = 180  # 字符宽度
    FPS = 10
    BACKGROUND_COLOR = "#000"  # 背景颜色
    
    if not os.path.isfile(VIDEO_PATH):
        print(f"错误: 视频文件 '{VIDEO_PATH}' 不存在!")
        print("请确保:")
        print("1. 视频文件在相同目录下")
        print("2. 文件名是 'input.mp4'")
        print("3. 或修改代码中的 VIDEO_PATH 变量")
        sys.exit(1)
    
    create_color_ascii_html(VIDEO_PATH, FPS, OUTPUT_FILE, CHARACTER_WIDTH, BACKGROUND_COLOR)
    
    print("\n下一步:")
    print(f"1. 打开 {OUTPUT_FILE} 文件查看结果")
    print("2. 视频将自动播放")
    print("3. 如果遇到问题，按F12打开浏览器控制台查看错误信息")