import os
import shutil
import sys

def find_minecraft_packs_folders(client_path):
    """
    在 Minecraft 客户端路径中查找 resource_packs 和 behavior_packs 文件夹
    """
    resource_packs_path = None
    behavior_packs_path = None
    
    # 检查常见的位置
    common_paths = [
        os.path.join(client_path, "resource_packs"),
        os.path.join(client_path, "behavior_packs"),
    ]
    
    # 遍历常见路径
    for path in common_paths:
        if os.path.exists(path):
            if "resource" in path.lower():
                resource_packs_path = path
            elif "behavior" in path.lower():
                behavior_packs_path = path
    
    # 如果没找到，尝试递归搜索
    if not resource_packs_path or not behavior_packs_path:
        for root, dirs, files in os.walk(client_path):
            if "resource_packs" in dirs and not resource_packs_path:
                resource_packs_path = os.path.join(root, "resource_packs")
            if "behavior_packs" in dirs and not behavior_packs_path:
                behavior_packs_path = os.path.join(root, "behavior_packs")
            if resource_packs_path and behavior_packs_path:
                break
    
    return resource_packs_path, behavior_packs_path

def replace_packs_folders(resource_packs_path, behavior_packs_path, data_folder):
    """
    替换资源包和行为包文件夹
    """
    try:
        # 替换 resource_packs
        if resource_packs_path:
            print(f"找到 resource_packs 文件夹: {resource_packs_path}")
            shutil.rmtree(resource_packs_path)
            src_resource = os.path.join(data_folder, "resource_packs")
            shutil.copytree(src_resource, resource_packs_path)
            print("resource_packs 文件夹已替换")
        
        # 替换 behavior_packs
        if behavior_packs_path:
            print(f"找到 behavior_packs 文件夹: {behavior_packs_path}")
            shutil.rmtree(behavior_packs_path)
            src_behavior = os.path.join(data_folder, "behavior_packs")
            shutil.copytree(src_behavior, behavior_packs_path)
            print("behavior_packs 文件夹已替换")
        
        return True
    except Exception as e:
        print(f"替换过程中出现错误: {e}")
        return False

def main():
    # 获取脚本所在目录的 data 文件夹路径
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_folder = os.path.join(script_dir, "data")
    
    # 检查 data 文件夹是否存在
    if not os.path.exists(data_folder):
        print("错误: 脚本所在目录下没有找到 data 文件夹")
        input("按回车键退出...")
        sys.exit(1)
    
    # 检查 data 文件夹中是否有需要的子文件夹
    has_resource = os.path.exists(os.path.join(data_folder, "resource_packs"))
    has_behavior = os.path.exists(os.path.join(data_folder, "behavior_packs"))
    
    if not has_resource and not has_behavior:
        print("错误: data 文件夹中没有找到 resource_packs 或 behavior_packs 文件夹")
        input("按回车键退出...")
        sys.exit(1)
    
    # 获取用户输入的 Minecraft 客户端路径
    print("Minecraft 资源包和行为包替换工具")
    print("--------------------------------")
    print(f"将从以下位置获取新的包文件: {data_folder}")
    print("")
    
    while True:
        client_path = input("请输入 Minecraft 客户端路径: ").strip()
        
        if not os.path.exists(client_path):
            print("错误: 指定的路径不存在，请重新输入")
            continue
        
        # 查找 packs 文件夹
        resource_packs_path, behavior_packs_path = find_minecraft_packs_folders(client_path)
        
        if not resource_packs_path and not behavior_packs_path:
            print("错误: 在指定路径中找不到 resource_packs 或 behavior_packs 文件夹")
            print("请确认您输入的是正确的 Minecraft 客户端路径")
            continue
        
        # 显示找到的文件夹
        if has_resource:
            if resource_packs_path:
                print(f"找到 resource_packs 文件夹: {resource_packs_path}")
            else:
                print("警告: 没有找到 resource_packs 文件夹，将跳过资源包替换")
        
        if has_behavior:
            if behavior_packs_path:
                print(f"找到 behavior_packs 文件夹: {behavior_packs_path}")
            else:
                print("警告: 没有找到 behavior_packs 文件夹，将跳过行为包替换")
        
        # 确认操作
        confirm = input("\n确认要替换上述文件夹吗？(y/n): ").lower()
        if confirm == 'y':
            break
        else:
            print("操作已取消，请重新输入路径")
    
    # 执行替换
    print("\n开始替换...")
    success = replace_packs_folders(resource_packs_path, behavior_packs_path, data_folder)
    
    if success:
        print("\n替换完成！")
    else:
        print("\n替换过程中出现错误，请检查错误信息")
    
    input("按回车键退出...")

if __name__ == "__main__":
    main()