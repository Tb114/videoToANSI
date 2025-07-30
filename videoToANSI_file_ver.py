import cv2
import os
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

def save_color_ascii_frames(video_path, output_dir="ascii_frames", width=100, background_color="#000"):
    """将视频每一帧转换为彩色ASCII图片并保存到指定文件夹"""
    
    if not os.path.isfile(video_path):
        print(f"错误: 视频文件不存在 '{video_path}'")
        sys.exit(1)
    
    # 创建输出目录
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # 优化的字符映射表
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
    
    # 处理所有帧
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
    
    # 字体设置
    try:
        font = ImageFont.truetype("Courier New.ttf", 12)
    except:
        try:
            font = ImageFont.truetype("arial.ttf", 12)
        except:
            font = ImageFont.load_default()
            print("警告: 使用默认字体，显示效果可能不理想")
    
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
            
            # 创建PIL图像用于保存帧图片
            char_width = 8  # 估计字符宽度
            char_height = 16  # 估计字符高度
            img_width = width * char_width
            img_height = height * char_height
            frame_img = Image.new("RGB", (img_width, img_height), background_color)
            draw = ImageDraw.Draw(frame_img)
            
            for y in range(height):
                for x in range(width):
                    # 获取像素颜色
                    b, g, r = resized_color[y, x]
                    color_rgb = (r, g, b)
                    
                    # 获取亮度值用于选择字符
                    brightness = resized_v[y, x]
                    normalized = min(max((brightness - global_min) / (global_max - global_min + 1e-5), 0), 1)
                    index = int(normalized * (len(ASCII_MAP) - 1))
                    char = ASCII_MAP[index]
                    
                    # 在图像上绘制字符
                    draw.text((x * char_width, y * char_height), char, fill=color_rgb, font=font)
            
            # 保存当前帧为图片
            frame_img_path = os.path.join(output_dir, f"frame_{processed:05d}.png")
            frame_img.save(frame_img_path)
            
            processed += 1
            
            # 显示进度
            if processed % 10 == 0 or processed == total_frames:
                progress = processed / total_frames * 100
                print(f"\r处理进度: {processed}/{total_frames}帧 ({progress:.1f}%)", end="", flush=True)
    
    finally:
        cap.release()
    
    if processed == 0:
        print("\n错误: 没有生成任何帧数据!")
        print("可能原因:")
        print("1. 视频文件格式不受支持")
        print("2. 视频文件损坏")
        print("3. OpenCV无法解码视频")
        sys.exit(1)
    
    print(f"\n成功处理: {processed}帧")
    print(f"帧图片已保存到: {output_dir}")
    
    return output_dir

if __name__ == "__main__":
    # 配置参数
    VIDEO_PATH = "bing.mp4"
    OUTPUT_DIR = "ascii_frames"  # 帧图片输出目录
    CHARACTER_WIDTH = 240  # 字符宽度
    BACKGROUND_COLOR = "#000000"  # 背景颜色(黑色)
    
    if not os.path.isfile(VIDEO_PATH):
        print(f"错误: 视频文件 '{VIDEO_PATH}' 不存在!")
        print("请确保:")
        print("1. 视频文件在相同目录下")
        print("2. 文件名正确")
        print("3. 或修改代码中的 VIDEO_PATH 变量")
        sys.exit(1)
    
    save_color_ascii_frames(
        video_path=VIDEO_PATH,
        output_dir=OUTPUT_DIR,
        width=CHARACTER_WIDTH,
        background_color=BACKGROUND_COLOR
    )
    
    print("\n处理完成!")
    print(f"所有帧图片已保存到: {OUTPUT_DIR}")