import cv2
import os
import sys
import json
import numpy as np
from time import sleep
import matplotlib.pyplot as plt

def create_ascii_html(video_path, fps, output_file="ascii_video.html", width=100, background_color="#000", font_color="#fff"):
    """将视频转换为30fps纯字符ANSI动画HTML（带详细调试）"""
    
    if not os.path.isfile(video_path):
        print(f"错误: 视频文件不存在 '{video_path}'")
        sys.exit(1)
    
    # ASCII_MAP = " .,-~:;=!*#$@"
    ASCII_MAP = " .,-~:;=!*#$@"
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
    
    # 创建调试目录
    debug_dir = "video_debug"
    os.makedirs(debug_dir, exist_ok=True)
    
    # 分析前5帧的亮度统计
    brightness_stats = []
    frames = []
    
    try:
        frame_count = 0
        while frame_count < min(5, total_frames):
            ret, frame = cap.read()
            if not ret:
                break
                
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            min_val = gray.min()
            max_val = gray.max()
            mean_val = gray.mean()
            brightness_stats.append((min_val, max_val, mean_val))
            
            print(f"帧 {frame_count+1}: 亮度 min={min_val}, max={max_val}, mean={mean_val:.1f}")
            
            # 保存调试图像
            cv2.imwrite(f"{debug_dir}/frame_{frame_count}_original.jpg", frame)
            cv2.imwrite(f"{debug_dir}/frame_{frame_count}_gray.jpg", gray)
            
            # 直方图可视化
            plt.figure()
            plt.hist(gray.ravel(), 256, [0,256])
            plt.title(f"帧 {frame_count+1} 亮度直方图")
            plt.savefig(f"{debug_dir}/frame_{frame_count}_histogram.png")
            plt.close()
            
            frame_count += 1
        
        # 综合亮度分析
        min_vals, max_vals, mean_vals = zip(*brightness_stats)
        global_min = min(min_vals)
        global_max = max(max_vals)
        global_mean = sum(mean_vals) / len(mean_vals)
        
        print("\n亮度全局分析:")
        print(f"最小亮度: {global_min}")
        print(f"最大亮度: {global_max}")
        print(f"平均亮度: {global_mean:.1f}")
        print(f"亮度范围: {global_max - global_min}")
        
        # 确定亮度调整参数
        if global_max - global_min < 20:
            # print("警告: 视频对比度非常低，将应用自动增强")
            # alpha = 255.0 / (global_max - global_min + 1e-5)
            # beta = -global_min * alpha
            alpha = 1.0
            beta = 0
        else:
            alpha = 1.0
            beta = 0
        
        # 返回第一帧重新处理
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        
        # 处理所有帧
        processed = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # 转换为灰度图并进行亮度调整
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # 应用对比度增强
            adjusted = cv2.convertScaleAbs(gray, alpha=alpha, beta=beta)
            
            # 保存调整后的图像用于调试
            if processed < 3:
                cv2.imwrite(f"{debug_dir}/frame_{processed}_adjusted.jpg", adjusted)
                
                # 创建ASCII预览
                preview = create_ascii_preview(adjusted, ASCII_MAP, 60)
                cv2.imwrite(f"{debug_dir}/frame_{processed}_ascii_preview.jpg", preview)
            
            # 调整尺寸
            aspect_ratio = gray.shape[0] / gray.shape[1]
            height = int(width * aspect_ratio * 0.5)  # 字符高度补偿
            
            resized = cv2.resize(adjusted, (width, height))
            
            # 转换为ASCII
            ascii_frame = ""
            for row in resized:
                for pixel in row:
                    # 映射到字符
                    normalized = min(max((pixel - global_min) / (global_max - global_min + 1e-5), 0), 1)
                    index = int(normalized * (len(ASCII_MAP) - 1))
                    ascii_frame += ASCII_MAP[index]
                ascii_frame += "\n"
            
            frames.append(ascii_frame)
            processed += 1
            
            # 显示进度
            if processed % fps == 0 or processed == total_frames:
                progress = processed / total_frames * 100
                print(f"\r处理进度: {processed}/{total_frames}帧 ({progress:.1f}%)", end="", flush=True)
                sleep(0.01)  # 避免输出刷新过快
    
    finally:
        cap.release()
    
    print(f"\n成功处理: {processed}帧")
    
    # 生成HTML内容
    frames_js = ",\n".join([json.dumps(frame) for frame in frames])
    
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>ASCII Video Player</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            background-color: {background_color} !important;
            color: {font_color} !important;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            overflow: hidden;
        }}
        #ascii-container {{
            background-color: #000;
            padding: 10px;
        }}
        #ascii-display {{
            white-space: pre;
            font-family: monospace;
            font-size: 12px;
            line-height: 1;
            color: {font_color};
            letter-spacing: 0;
        }}
        .stats {{
            color: #0a0;
            font-family: Arial;
            font-size: 12px;
            text-align: center;
            margin-top: 10px;
        }}
    </style>
</head>
<body>
    <div id="ascii-container">
        <div id="ascii-display"></div>
        <div class="stats"><span id="status"></span></div>
    </div>

    <script>
        // 解决黑屏问题的关键设置
        document.body.style.backgroundColor = "#000";
        document.getElementById("ascii-container").style.backgroundColor = "#000";
        
        // 帧数据数组
        const frames = [
            {frames_js}
        ].map(frame => frame.replace(/\\\\n/g, '\\n'));
        
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
            
            // 确保30fps精确播放
            if (elapsed >= frameDelay) {{
                // 更新显示
                const display = document.getElementById('ascii-display');
                display.textContent = frames[currentFrame];
                
                // 更新状态
                
                // 前进帧计数
                currentFrame = (currentFrame + 1) % frames.length;
                
                // 更新最后时间
                lastTime = timestamp;
            }}
            
            // 继续请求下一帧
            requestId = requestAnimationFrame(renderFrame);
        }}
        
        // 开始播放
        window.addEventListener('DOMContentLoaded', () => {{
            console.log("DOM已加载，开始播放");
            if (frames.length > 0) {{
                renderFrame(performance.now());
            }} else {{
                console.error("错误: 没有可播放的帧数据");
            }}
        }});
    </script>
</body>
</html>"""
    
    # 写入HTML文件
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"\n生成HTML播放器: {output_file}")
    
    # 生成调试报告
    with open(f"{debug_dir}/debug_report.txt", "w") as report:
        report.write(f"视频分析报告\n")
        report.write(f"文件路径: {video_path}\n")
        report.write(f"总帧数: {total_frames}\n")
        report.write(f"原始分辨率: {video_width}x{video_height}\n")
        report.write(f"亮度范围: {global_min} - {global_max}\n")
        report.write(f"对比度增强: alpha={alpha:.2f}, beta={beta:.2f}\n")
        report.write(f"ASCII宽度: {width}\n")
        report.write(f"输出HTML尺寸: {os.path.getsize(output_file)//1024}KB\n")
        report.write("\n问题解决建议:\n")
        
        if global_mean < 50:
            report.write("- 视频太暗，请尝试提高源视频亮度\n")
        if global_max - global_min < 20:
            report.write("- 视频对比度太低，请使用视频编辑软件增强对比度\n")
        if video_width > 1920:
            report.write("- 视频分辨率过高，建议缩小到1080p\n")
    
    print("调试文件已保存到 'video_debug' 目录")
    print("如果输出仍然是黑色，请检查调试报告中的建议")
    
    return output_file

def create_ascii_preview(image, ascii_map, preview_width=80):
    """创建ASCII转换的预览图像"""
    # 计算预览高度
    aspect_ratio = image.shape[0] / image.shape[1]
    preview_height = int(preview_width * aspect_ratio * 0.5)
    
    # 调整大小
    resized = cv2.resize(image, (preview_width, preview_height))
    
    # 创建空白图像用于预览
    preview = np.zeros((preview_height * 15, preview_width * 8, 3), dtype=np.uint8)
    
    # 填充白色背景
    preview.fill(255)
    
    y_offset = 10
    for row in resized:
        x_offset = 10
        for pixel in row:
            # 映射到字符
            normalized = min(max(pixel / 255, 0), 1)
            index = int(normalized * (len(ascii_map) - 1))
            char = ascii_map[index]
            
            # 添加字符到图像
            cv2.putText(preview, char, (x_offset, y_offset), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.3, (0, 0, 0), 1)
            x_offset += 8
        y_offset += 15
    
    return preview

if __name__ == "__main__":
    # 配置参数
    VIDEO_PATH = "input.mp4"
    OUTPUT_FILE = "output.html"
    CHARACTER_WIDTH = 360  # 对于问题视频，减小宽度值
    FPS = 60 #这是每秒显示帧图片数(即源视频帧率*倍速的值)
    
    # 特殊处理：如果video_debug目录存在，先清空
    if os.path.exists("video_debug"):
        for file in os.listdir("video_debug"):
            os.remove(os.path.join("video_debug", file))
    
    if not os.path.isfile(VIDEO_PATH):
        print(f"错误: 视频文件 '{VIDEO_PATH}' 不存在!")
        print("请确保:")
        print("1. 视频文件在相同目录下")
        print("2. 文件名是 'input.mp4'")
        print("3. 或修改代码中的 VIDEO_PATH 变量")
        sys.exit(1)
    
    create_ascii_html(VIDEO_PATH, FPS, OUTPUT_FILE, CHARACTER_WIDTH)
    
    print("\n下一步:")
    print(f"1. 打开 {OUTPUT_FILE} 文件查看结果")
    print("2. 如果仍是黑屏，检查 video_debug 目录中的调试信息")
    print("3. 根据调试报告调整视频或参数")