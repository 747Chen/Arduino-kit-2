import cv2
import numpy as np
from pathlib import Path


def remove_watermark_inpaint(
        image_path,
        output_path=None,
        region_width=450,
        region_height=120,
        inpaint_radius=3
):
    """
    去除右下角水印并保存。
    """
    image_path = Path(image_path)

    # 如果没有指定输出路径，默认在原文件名后加 _clean
    if output_path is None:
        output_path = image_path.with_name(image_path.stem + "_clean" + image_path.suffix)

    # 1. 读取原图
    img = cv2.imread(str(image_path), cv2.IMREAD_COLOR)
    if img is None:
        print(f"无法读取图片 (跳过): {image_path}")
        return

    h, w = img.shape[:2]

    # 2. 定义右下角水印区域
    x_start = max(0, w - region_width)
    y_start = max(0, h - region_height)

    # 3. 制作 Mask (掩膜)
    # 只在这个区域做 inpaint
    mask = np.zeros((h, w), dtype=np.uint8)
    mask[y_start:h, x_start:w] = 255

    # 4. 执行修复 (Inpaint)
    # cv2.INPAINT_TELEA 是常用的修复算法
    result = cv2.inpaint(img, mask, inpaint_radius, cv2.INPAINT_TELEA)

    # 5. 保存结果
    # 确保输出路径是字符串格式
    cv2.imwrite(str(output_path), result)
    print(f"已处理并保存: {output_path}")


# ==========================================
# 批量执行部分
# ==========================================

# 设定你的目标文件夹路径 (根据你的截图，文件夹叫 Slide)
target_folder = Path("Slide")

# 支持的图片格式
valid_extensions = {".jpg", ".jpeg", ".png", ".bmp"}

print(f"开始扫描文件夹: {target_folder.absolute()} ...")

# rglob("*") 会递归查找所有子文件夹里的文件
if not target_folder.exists():
    print("错误：找不到 'Slide' 文件夹，请确保脚本和 Slide 文件夹在同一个目录下。")
else:
    for file_path in target_folder.rglob("*"):
        # 检查是否是图片，且不是我们生成的 _clean 文件（防止重复处理）
        if file_path.suffix.lower() in valid_extensions and "_clean" not in file_path.stem:
            try:
                remove_watermark_inpaint(file_path)
            except Exception as e:
                print(f"处理出错 {file_path.name}: {e}")

    print("所有文件处理完成！")