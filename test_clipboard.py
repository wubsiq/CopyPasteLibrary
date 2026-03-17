import win32clipboard
from io import BytesIO
from PIL import Image
import time

print("请先复制一张图片，然后按Enter键继续...")
input()

print("正在检查剪贴板...")
try:
    win32clipboard.OpenClipboard()
    
    # 获取所有可用的剪贴板格式
    print("\n可用的剪贴板格式:")
    format_id = 0
    while True:
        format_name = win32clipboard.GetClipboardFormatName(format_id)
        if format_name:
            print(f"  {format_id}: {format_name}")
        format_id += 1
        try:
            # 尝试下一个格式
            win32clipboard.IsClipboardFormatAvailable(format_id)
        except:
            break
    
    # 检查标准格式
    print(f"\nCF_DIB 可用: {win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_DIB)}")
    print(f"CF_BITMAP 可用: {win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_BITMAP)}")
    
    # 尝试获取DIB格式
    if win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_DIB):
        print("\n尝试获取CF_DIB格式数据...")
        data = win32clipboard.GetClipboardData(win32clipboard.CF_DIB)
        print(f"获取到数据大小: {len(data)} 字节")
        
        # 尝试用PIL打开
        try:
            image = Image.open(BytesIO(data))
            print(f"成功打开图片! 尺寸: {image.size}, 模式: {image.mode}")
            
            # 保存测试
            test_file = "test_image.png"
            image.save(test_file)
            print(f"图片已保存为: {test_file}")
        except Exception as e:
            print(f"PIL打开失败: {e}")
            import traceback
            traceback.print_exc()
    
    # 尝试其他方法获取图片
    print("\n尝试其他方法...")
    try:
        from PIL import ImageGrab
        image = ImageGrab.grabclipboard()
        if image:
            print(f"ImageGrab成功! 尺寸: {image.size}, 模式: {image.mode}")
            image.save("test_image_grab.png")
            print(f"已保存为: test_image_grab.png")
        else:
            print("ImageGrab获取失败")
    except Exception as e:
        print(f"ImageGrab错误: {e}")
        import traceback
        traceback.print_exc()
    
    win32clipboard.CloseClipboard()
    
except Exception as e:
    print(f"\n错误: {e}")
    import traceback
    traceback.print_exc()

print("\n测试完成!")
