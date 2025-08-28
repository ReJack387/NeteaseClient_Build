import os
import shutil
import zipfile
import tempfile
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# 配置
APK_NAME = "Cyan Heart Recode.Apk"  # 底包文件名
APKSIGNER_PATH = "apksigner.jar"  # 需要提前下载 apksigner.jar
ZIPALIGN_PATH = "zipalign"  # 需要 Android SDK 中的 zipalign
KEY_DIR = "keys"  # 密钥文件目录
X509_CERT = os.path.join(KEY_DIR, "platform.x509.pem")  # x509证书
PK8_KEY = os.path.join(KEY_DIR, "platform.pk8")  # pk8私钥
BACKUP_DIR = "backups"  # 备份文件目录
DATA_DIR = "data"  # 资源目录
ICON_PATH = "icon.ico"  # 程序图标

def get_available_clients():
    """
    获取data文件夹中可用的客户端列表
    """
    clients = []
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), DATA_DIR)
    
    if not os.path.exists(data_dir):
        return clients
    
    for item in os.listdir(data_dir):
        item_path = os.path.join(data_dir, item)
        if os.path.isdir(item_path):
            # 检查是否包含resource_packs或behavior_packs文件夹
            has_resource = os.path.exists(os.path.join(item_path, "resource_packs"))
            has_behavior = os.path.exists(os.path.join(item_path, "behavior_packs"))
            if has_resource or has_behavior:
                clients.append(item)
    
    return sorted(clients)

def display_client_menu(clients):
    """
    显示客户端选择菜单
    """
    print("\n可用客户端列表:")
    print("0. 多客户端构建 (选择多个客户端)")
    for i, client in enumerate(clients, 1):
        print(f"{i}. {client}")
    
    while True:
        try:
            choice = input("\n请选择要构建的客户端 (输入序号，多选时用逗号分隔): ").strip()
            
            if choice == "0":
                # 多客户端构建
                multi_choice = input("请输入要构建的客户端序号 (用逗号分隔，如: 1,3,4): ").strip()
                selected_indices = [int(x.strip()) for x in multi_choice.split(",") if x.strip().isdigit()]
                
                selected_clients = []
                for idx in selected_indices:
                    if 1 <= idx <= len(clients):
                        selected_clients.append(clients[idx-1])
                    else:
                        print(f"警告: 序号 {idx} 无效，已跳过")
                
                if selected_clients:
                    return selected_clients
                else:
                    print("错误: 没有选择有效的客户端")
            else:
                # 单客户端构建
                if choice.isdigit():
                    idx = int(choice)
                    if 1 <= idx <= len(clients):
                        return [clients[idx-1]]
                    else:
                        print("错误: 选择的序号超出范围")
                else:
                    print("错误: 请输入有效的数字")
        except ValueError:
            print("错误: 请输入有效的数字")
        except Exception as e:
            print(f"选择过程中出现错误: {e}")

def clean_up():
    """清理构建和临时文件"""
    files_to_remove = [
        "build",
        "backups",
        "dist",
        f"{APK_NAME.replace('.Apk','')} PC Installer.spec",
        f"{os.path.splitext(APK_NAME)[0]}_aligned.apk.idsig",
        f"{os.path.splitext(APK_NAME)[0]}_unsigned.apk",
        f"{os.path.splitext(APK_NAME)[0]}_aligned.apk"
    ]
    
    print("\n正在清理临时文件...")
    for item in files_to_remove:
        try:
            if os.path.isfile(item):
                os.remove(item)
                print(f"已删除文件: {item}")
            elif os.path.isdir(item):
                shutil.rmtree(item)
                print(f"已删除目录: {item}")
        except Exception as e:
            print(f"删除 {item} 失败: {e}")

def create_backup(apk_path):
    """创建原始APK备份"""
    try:
        os.makedirs(BACKUP_DIR, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = os.path.splitext(os.path.basename(apk_path))[0]
        backup_name = f"{base_name}_backup_{timestamp}.apk"
        backup_path = os.path.join(BACKUP_DIR, backup_name)
        shutil.copy2(apk_path, backup_path)
        print(f"\n已创建备份文件: {backup_path}")
        return backup_path
    except Exception as e:
        print(f"\n创建备份失败: {e}")
        return None

def restore_backup(backup_path, original_path):
    """从备份还原APK"""
    try:
        if backup_path and os.path.exists(backup_path):
            shutil.copy2(backup_path, original_path)
            print(f"\n已从备份还原: {original_path}")
            return True
        return False
    except Exception as e:
        print(f"\n还原备份失败: {e}")
        return False

def extract_apk(apk_path, extract_dir):
    """解压 APK 文件"""
    try:
        with zipfile.ZipFile(apk_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
        return True
    except Exception as e:
        print(f"解压 APK 失败: {e}")
        return False

def repack_apk(extract_dir, output_apk):
    """重新打包 APK 文件（确保 resources.arsc 不压缩）"""
    try:
        with zipfile.ZipFile(output_apk, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(extract_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, extract_dir)
                    # 特别处理 resources.arsc
                    if arcname == 'resources.arsc':
                        zipf.write(file_path, arcname, compress_type=zipfile.ZIP_STORED)
                    else:
                        zipf.write(file_path, arcname)
        return True
    except Exception as e:
        print(f"打包 APK 失败: {e}")
        return False

def zipalign_apk(input_apk, output_apk):
    """对齐 APK 文件（针对 Android 11+ 的特别处理）"""
    try:
        # 先进行一次标准对齐
        subprocess.run([
            ZIPALIGN_PATH,
            "-v", "4",
            input_apk,
            output_apk
        ], check=True)
        
        # 对资源表进行特殊处理（关键修复）
        with zipfile.ZipFile(output_apk, 'a') as zf:
            # 确保不压缩 resources.arsc
            if 'resources.arsc' in zf.namelist():
                zf.getinfo('resources.arsc').compress_type = zipfile.ZIP_STORED
        
        # 再次对齐确保4字节边界
        temp_aligned = output_apk + "_temp"
        shutil.move(output_apk, temp_aligned)
        subprocess.run([
            ZIPALIGN_PATH,
            "-v", "4",
            temp_aligned,
            output_apk
        ], check=True)
        os.remove(temp_aligned)
        
        return True
    except Exception as e:
        print(f"zipalign 对齐失败: {e}")
        return False

def sign_apk_with_pem_pk8(apk_path):
    """使用 .x509.pem 和 .pk8 文件签名 APK（针对 Android 11+ 优化）"""
    try:
        # 先检查资源对齐
        with zipfile.ZipFile(apk_path, 'r') as zf:
            arsc_info = zf.getinfo('resources.arsc')
            if arsc_info.compress_type != zipfile.ZIP_STORED:
                print("错误: resources.arsc 必须使用存储模式(不压缩)")
                return False
        
        # 执行签名
        result = subprocess.run([
            "java", "-jar", APKSIGNER_PATH,
            "sign",
            "--key", PK8_KEY,
            "--cert", X509_CERT,
            "--v1-signer-name", "C=US, O=Android, CN=Android",
            "--v2-signing-enabled", "true",
            "--v3-signing-enabled", "false",
            "--min-sdk-version", "30",  # 明确指定最低SDK版本
            "--out", apk_path,
            apk_path
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"APK 签名失败: {result.stderr}")
            return False
        return True
    except Exception as e:
        print(f"APK 签名过程中出现错误: {e}")
        return False

def modify_packs_for_multiple_clients(extract_dir, selected_clients):
    """
    为多客户端构建修改资源包和行为包
    """
    try:
        yant_path = os.path.join(extract_dir, "assets", "Yant")
        os.makedirs(yant_path, exist_ok=True)
        
        data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), DATA_DIR)
        
        for client in selected_clients:
            client_dir = os.path.join(data_dir, client)
            vanilla_netease_src = os.path.join(client_dir, "resource_packs", "vanilla_netease")
            
            if os.path.exists(vanilla_netease_src):
                # 目标路径：assets\Yant\客户端名称
                client_dest = os.path.join(yant_path, client)
                
                # 复制vanilla_netease文件夹到目标路径
                if os.path.exists(client_dest):
                    shutil.rmtree(client_dest)
                shutil.copytree(vanilla_netease_src, client_dest)
                
                # 删除manifest.json文件
                manifest_path = os.path.join(client_dest, "manifest.json")
                if os.path.exists(manifest_path):
                    os.remove(manifest_path)
                    print(f"已删除 {client} 的 manifest.json")
                
                print(f"已为客户端 {client} 添加资源包到 assets\\Yant\\{client}")
            else:
                print(f"警告: 客户端 {client} 中没有找到 vanilla_netease 文件夹")
        
        return True
    except Exception as e:
        print(f"多客户端构建过程中出现错误: {e}")
        return False

def modify_packs(extract_dir, data_dir, selected_clients=None):
    """修改资源包和行为包"""
    try:
        # 如果是多客户端构建，使用特殊处理
        if isinstance(selected_clients, list) and len(selected_clients) > 1:
            return modify_packs_for_multiple_clients(extract_dir, selected_clients)
        
        # 单客户端构建的原有逻辑
        # 获取客户端目录路径
        if selected_clients and isinstance(selected_clients, list) and len(selected_clients) == 1:
            client_dir = os.path.join(data_dir, selected_clients[0])
        else:
            client_dir = data_dir
        
        possible_pack_paths = [
            os.path.join(extract_dir, "assets", "resource_packs"),
            os.path.join(extract_dir, "assets", "behavior_packs"),
            os.path.join(extract_dir, "assets", "assets", "resource_packs"),
            os.path.join(extract_dir, "assets", "assets", "behavior_packs"),
            os.path.join(extract_dir, "resource_packs"),
            os.path.join(extract_dir, "behavior_packs"),
        ]

        src_resource = os.path.join(client_dir, "resource_packs")
        if os.path.exists(src_resource):
            replaced = False
            for path in possible_pack_paths:
                if "resource" in path.lower() and os.path.exists(path):
                    shutil.rmtree(path)
                    shutil.copytree(src_resource, path)
                    print(f"已替换资源包: {path}")
                    replaced = True
                    break
            
            if not replaced:
                new_path = os.path.join(extract_dir, "assets", "assets", "resource_packs")
                os.makedirs(new_path, exist_ok=True)
                shutil.copytree(src_resource, new_path, dirs_exist_ok=True)
                print(f"已创建新资源包目录: {new_path}")

        src_behavior = os.path.join(client_dir, "behavior_packs")
        if os.path.exists(src_behavior):
            replaced = False
            for path in possible_pack_paths:
                if "behavior" in path.lower() and os.path.exists(path):
                    shutil.rmtree(path)
                    shutil.copytree(src_behavior, path)
                    print(f"已替换行为包: {path}")
                    replaced = True
                    break
            
            if not replaced:
                new_path = os.path.join(extract_dir, "assets", "assets", "behavior_packs")
                os.makedirs(new_path, exist_ok=True)
                shutil.copytree(src_behavior, new_path, dirs_exist_ok=True)
                print(f"已创建新行为包目录: {new_path}")

        return True
    except Exception as e:
        print(f"修改包内容失败: {e}")
        return False

def check_requirements():
    """检查必要的工具和文件是否存在"""
    missing = []
    
    if not os.path.exists(APKSIGNER_PATH):
        missing.append(f"apksigner.jar ({APKSIGNER_PATH})")
    
    if not os.path.exists(X509_CERT):
        missing.append(f"x509证书文件 ({X509_CERT})")
    
    if not os.path.exists(PK8_KEY):
        missing.append(f"pk8私钥文件 ({PK8_KEY})")
    
    try:
        subprocess.run(["java", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except:
        missing.append("Java运行时环境")
    
    try:
        subprocess.run([ZIPALIGN_PATH, "-h"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except:
        missing.append("zipalign工具")
    
    return missing

def build_pc_version():
    """构建PC平台可执行文件（优化版）"""
    try:
        if not os.path.exists(ICON_PATH):
            print(f"警告: 找不到图标文件 {ICON_PATH}，将不使用图标")
            icon_option = ""
        else:
            icon_option = f"--icon \"{ICON_PATH}\""
        
        script_name = os.path.basename(__file__)
        build_cmd = (
            f"pyinstaller --noconfirm --onefile --console "
            f"{icon_option} "
            f"--add-data \"./{DATA_DIR};{DATA_DIR}\" "
            "\"./install.py\" "
            f"--distpath ./ "
            f"--name \"./{APK_NAME.replace('.Apk','')} PC Installer\""
        )
        
        print("\n正在构建PC平台可执行文件...")
        print(f"执行命令: {build_cmd}")
        subprocess.run(build_cmd, shell=True, check=True)
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"构建失败: {e}")
        return False
    except Exception as e:
        print(f"构建过程中出现错误: {e}")
        return False


def verify_alignment(apk_path):
    """验证APK资源对齐"""
    try:
        # 使用zipalign验证
        result = subprocess.run([
            ZIPALIGN_PATH,
            "-c", "4",
            apk_path
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"对齐验证失败: {result.stderr}")
            return False
        
        # 验证resources.arsc压缩方式
        with zipfile.ZipFile(apk_path, 'r') as zf:
            arsc_info = zf.getinfo('resources.arsc')
            if arsc_info.compress_type != zipfile.ZIP_STORED:
                print("错误: resources.arsc 未设置为存储模式")
                return False
        
        return True
    except Exception as e:
        print(f"验证过程中出错: {e}")
        return False

def main():
    print("网易 MCBE 客户端快速构建")
    print("=" * 60)
    
    # 获取可用客户端列表
    clients = get_available_clients()
    if not clients:
        print(f"错误: 在 {DATA_DIR} 目录中没有找到任何客户端配置")
        input("按回车键退出...")
        return
    
    # 显示客户端选择菜单
    selected_clients = display_client_menu(clients)
    if not selected_clients:
        print("错误: 没有选择任何客户端")
        input("按回车键退出...")
        return
    
    print(f"\n已选择客户端: {', '.join(selected_clients)}")
    
    apk_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), APK_NAME)
    
    if not os.path.exists(apk_path):
        print(f"错误: 找不到底包文件 {APK_NAME}")
        print("请确保底包文件与脚本在同一目录下")
        input("按回车键退出...")
        return
    
    missing = check_requirements()
    if missing:
        print("错误: 缺少必要的工具或文件:")
        for item in missing:
            print(f" - {item}")
        input("按回车键退出...")
        return
    
    # 创建备份
    print("\n正在创建原始APK备份...")
    backup_path = create_backup(apk_path)
    if not backup_path:
        confirm = input("备份失败，是否继续? (y/n): ").lower()
        if confirm != 'y':
            return
    
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), DATA_DIR)
    if not os.path.exists(data_dir):
        print(f"错误: 找不到 {DATA_DIR} 目录")
        input("按回车键退出...")
        return
    
    with tempfile.TemporaryDirectory() as temp_dir:
        print("\n步骤 1/5: 解压 APK...")
        if not extract_apk(apk_path, temp_dir):
            input("按回车键退出...")
            return
        
        print("\n步骤 2/5: 修改资源包和行为包...")
        if not modify_packs(temp_dir, data_dir, selected_clients):
            input("按回车键退出...")
            return
        
        output_dir = os.path.dirname(apk_path)
        base_name = os.path.splitext(os.path.basename(apk_path))[0]
        unsigned_apk = os.path.join(output_dir, f"{base_name}_unsigned.apk")
        aligned_apk = os.path.join(output_dir, f"{base_name}_aligned.apk")
        final_apk = os.path.join(output_dir, f"{base_name}_signed.Apk")
        
        print("\n步骤 3/5: 重新打包 APK...")
        if not repack_apk(temp_dir, unsigned_apk):
            input("按回车键退出...")
            return

        print("\n步骤 4/5: 对齐 APK...")
        if not zipalign_apk(unsigned_apk, aligned_apk):
            input("按回车键退出...")
            return

        print("\n步骤 5/5: V1+V2签名 APK...")
        if not sign_apk_with_pem_pk8(aligned_apk):
            input("按回车键退出...")
            return
        
        os.rename(aligned_apk, final_apk)
        os.remove(unsigned_apk)
        
        print(f"\n处理完成! 已签名的 APK 保存在: {final_apk}")
        
        # 自动还原备份到当前目录
        print("\n正在还原原始APK备份...")
        restore_backup(backup_path, apk_path)
        
        # 构建PC版本
        build_pc_version()
        
        # 清理临时文件
        clean_up()
        input("按回车键退出...")

if __name__ == "__main__":
    main()