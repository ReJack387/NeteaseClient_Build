import os
import shutil
import sys

def get_available_clients(data_folder):
    """
    获取data文件夹中可用的客户端列表
    """
    clients = []
    if not os.path.exists(data_folder):
        return clients
    
    for item in os.listdir(data_folder):
        item_path = os.path.join(data_folder, item)
        if os.path.isdir(item_path):
            # 检查是否包含resource_packs或behavior_packs文件夹
            has_resource = os.path.exists(os.path.join(item_path, "resource_packs"))
            has_behavior = os.path.exists(os.path.join(item_path, "behavior_packs"))
            if has_resource or has_behavior:
                clients.append(item)
    
    return sorted(clients)

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

def replace_packs_folders(resource_packs_path, behavior_packs_path, selected_client_folder):
    """
    替换资源包和行为包文件夹
    """
    try:
        # 替换 resource_packs
        if resource_packs_path:
            src_resource = os.path.join(selected_client_folder, "resource_packs")
            if os.path.exists(src_resource):
                print(f"找到 resource_packs 文件夹: {resource_packs_path}")
                shutil.rmtree(resource_packs_path)
                shutil.copytree(src_resource, resource_packs_path)
                print("resource_packs 文件夹已替换")
            else:
                print("警告: 选择的客户端中没有 resource_packs 文件夹，跳过替换")
        
        # 替换 behavior_packs
        if behavior_packs_path:
            src_behavior = os.path.join(selected_client_folder, "behavior_packs")
            if os.path.exists(src_behavior):
                print(f"找到 behavior_packs 文件夹: {behavior_packs_path}")
                shutil.rmtree(behavior_packs_path)
                shutil.copytree(src_behavior, behavior_packs_path)
                print("behavior_packs 文件夹已替换")
            else:
                print("警告: 选择的客户端中没有 behavior_packs 文件夹，跳过替换")
        
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
    
    # 获取可用的客户端列表
    available_clients = get_available_clients(data_folder)
    if not available_clients:
        print("错误: data 文件夹中没有找到任何客户端配置")
        print("请确保data文件夹中包含子文件夹，且子文件夹中包含resource_packs或behavior_packs文件夹")
        input("按回车键退出...")
        sys.exit(1)
    
    # 让用户选择客户端
    print("Minecraft 资源包和行为包替换工具")
    print("--------------------------------")
    print("可用的客户端配置:")
    for i, client in enumerate(available_clients, 1):
        print(f"{i}. {client}")
    
    while True:
        try:
            choice = input("\n请选择要使用的客户端配置 (输入数字): ").strip()
            choice_index = int(choice) - 1
            
            if 0 <= choice_index < len(available_clients):
                selected_client = available_clients[choice_index]
                selected_client_folder = os.path.join(data_folder, selected_client)
                break
            else:
                print("错误: 选择超出范围，请重新输入")
        except ValueError:
            print("错误: 请输入有效的数字")
    
    print(f"\n已选择客户端: {selected_client}")
    print(f"将从以下位置获取新的包文件: {selected_client_folder}")
    
    # 检查选择的客户端文件夹中是否有需要的子文件夹
    has_resource = os.path.exists(os.path.join(selected_client_folder, "resource_packs"))
    has_behavior = os.path.exists(os.path.join(selected_client_folder, "behavior_packs"))
    
    if not has_resource and not has_behavior:
        print("错误: 选择的客户端文件夹中没有找到 resource_packs 或 behavior_packs 文件夹")
        input("按回车键退出...")
        sys.exit(1)
    
    # 获取用户输入的 Minecraft 客户端路径
    print("\n")
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
    success = replace_packs_folders(resource_packs_path, behavior_packs_path, selected_client_folder)
    
    if success:
        print("\n替换完成！")
    else:
        print("\n替换过程中出现错误，请检查错误信息")
    
    input("按回车键退出...")

if __name__ == "__main__":
    print("""                                                                                 
               ░░░░           ░░                                                 
                ░░░░░░░░      ░░  ░░░░░░░░░░░░░░░░░                              
               ░░░░░░░░░░     ░░░░░░ ░░░░░░░░░░░░░░░░░░░                         
                ░░░░░░░░   ░░░░░░░░░░░░░░░░░░░░░░  ░░░░░░  ░  ░                  
                ░ ░░░░░  ░░░░░░░░░░ ░░░░░░░░░░░░░░░ ░░░░░░░ ░░                   
                ░▒ ░░░ ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  ░░░░░░░                    
                ░▒░░  ░░░░░░░░░░  ░░░░░░░░░░░░░░░░░░░ ░░░░░░░░                   
                 ░░  ░░░░░░░ ░░░ ░░░░░░░░░░░░░░░░░░░░░ ░░░░░░░░   ░░░░░░░░░░░░░░ 
                 ░░░░░░░░░░ ░░  ░░░░░░░░░░░░░░░░░░░░░░  ░░░░░░░░ ░░░░░░░░░░░░░░  
                  ░░░░░░░░ ░░░ ░░░░░░░░░░░░░░░░░ ░░░░░  ░░░░░░░░░ ░░░░░░░░░░▒░   
                  ░░░░░░░ ░░░  ░░░░░░░░░░░░░░░░░ ░░░░░  ░░░░░░░░░ ░░░░░░░▒▒▒░    
                 ░░░░░░░  ░░   ░░░░░░░░░░░░░░░░░ ░░░░░░ ░░░░░░░░░  ░ ░▒▒▒▒░░     
                ░░░░░░░░ ░░░  ░░░░░░░░░░░░░░░░░░ ░░░░░░ ░░░░░░░░░░░░▒▒▒▒▒░       
                ░░░░░░░ ░░░░ ▒░░░░░░░░░░░░░░░░░   ░ ░░░ ░░░░░░░░░░░▒▒▒▒░░        
                ░░░░░░░  ░░ ▒▒░░░░░░░░░░░░░░░░░ ░ ░ ░░░ ░░░░░░░░░░░▒▒░░          
                ░░░░░░ ░░░░▒▒▒ ░░░░░░░░░░░░░░░ ░░ ░░░░░ ░░░░░░░░░░░▒░            
                ░░░░░░ ▒░░░▒▓▒░░░░░░░░░░░░░░░░░▒▒░░░░░░ ░░░░░░░░░   ░░░░         
                ░░░░░░▒▒░░░▓▓▓▒░░░░░░░░░░░░░░░░▓▒░░░░░░ ░░░░░░░░░   ░░░          
                ░░░░░░▓▓░░▓▓▓▓▓░░░░░░░░░░░░░░▒▓▓▓▒░░░░░░░░░░░░░░░                
                ░░░░░░░░░▒▓▓▓▓▓▓░▒░░░░░░░░░░▒▓▓▓▓▒░░░░░░░░░░░░░░░   ░░░    ▒▒░▒░ 
               ░░▒░░░░▓▓▒   ▓▓▓▓▓▒▒░░░░░░▒░▒▓▓▓▓▓▓░▒░░░░░░░░░░░░    ░░░   ░▓▓▓▓▒░
                ▒▓░░░░▓▓▓▓▓▒ ▓▓▓▓▓▓▓▒░░▓▓▒▓▒░░░░       ░░░░░░░░░ ░ ░░░░   ░░▒▓▓░ 
                ▓▓░░▒▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▒░░░░░▒▓▒▒░░░░░░░░░ ░░ ░░░░       ░  
             ▒▓▓▓▓▒▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓░░░░░░░▒▓░░░░░░░░░  ░░ ░░░░          
          ░░░▒▓▓▓▓▒▓▒▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▒▒▒▒▓▓░░░░░░░░░  ░░░ ░░░░          
         ░░░░░░░░░▒  ░▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▒░░░░░░░░   ░░░  ░░░          
       ░░░░░░░░░░░░ ░░ ░▒▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▒░░░▓░░░    ░░░  ░░           
      ░░░░░░░░░░░░░░░░  ░░░▒▓▓▓▓▓▓▓▓▓▒▒▓▓▓▓▓▓▓▓▒▒▒▓▓░░▓▒░░     ░░░   ░░          
     ░░░░░░░░░░░░░░░ ░  ░░░░░░░▒▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▒░░▓▓▓▓▓░      ░░░   ░░          
     ░░░░░░░░░░░░░░░░░░ ░░░░░░░▒▒▒▒▒▒▒▓▒░░░░░░░░░░ ▒▓▓▓▓▓▒     ░░░    ░          
     ░░░░░░░░░░░░░░ ░░░  ░░░░░░▒▒▒▒▒▒▒░░░░░░░░░░░░ ░░░░░░░░░   ░░░░   ░░         
    ░░░░░░░░░░░░░░░░ ░░ ░░ ░░░░▒▒▒▒░░░░░░░░░░░░░░░░░░░░░░░░░    ░░░   ░░         
   ░░░░░░░░░░░░░░░░░ ░░ ░░░  ░░ ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░   ░░░             
   ░░░░░░░░░░░░░░ ░░  ░ ░░░░░░ ░░░░░░░░░░░░░░░░░  ░░░░░░░░░░░░░   ░░░            
   ░░░░░░░░░░░░░░░░░░  ░░░░░░░░░░░░░ ░░░░░ ░░░░░░ ░░░░░░░░░░░░░    ░░░           
   ░░░░░░░░░░░░░░░░░  ░░░░░░░░░░░░░░░░░░░░░░░ ░░░ ░░░░░░░░░░░░░     ░░           
     ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ ░░░░ ░░░░░░░░░░░░░      ░░          
       ░░░░░░░ ░░░░░░░░░ ░░░░░░░░░░░░░░░░░  ░░░░░░░░░░░░░░░░░░        ░          
               ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░                   
               ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░                   
""")
    main()