import os
import shutil
import zipfile
import tempfile
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# 配置
APK_NAME = ""  # 锁定的底包文件名
APKSIGNER_PATH = "apksigner.jar"  # 需要提前下载 apksigner.jar
ZIPALIGN_PATH = "zipalign"  # 需要 Android SDK 中的 zipalign
KEY_DIR = "keys"  # 密钥文件目录
X509_CERT = os.path.join(KEY_DIR, "platform.x509.pem")  # x509证书
PK8_KEY = os.path.join(KEY_DIR, "platform.pk8")  # pk8私钥
BACKUP_DIR = "backups"  # 备份文件目录
DATA_DIR = "data"  # 资源目录
ICON_PATH = "icon.ico"  # 程序图标

def clean_up():
    """清理构建和临时文件"""
    files_to_remove = [
        "build",
        "backups",
        "dist",
        "install.spec",
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
    """重新打包 APK 文件"""
    try:
        with zipfile.ZipFile(output_apk, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(extract_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, extract_dir)
                    zipf.write(file_path, arcname)
        return True
    except Exception as e:
        print(f"打包 APK 失败: {e}")
        return False

def zipalign_apk(input_apk, output_apk):
    """对齐 APK 文件"""
    try:
        subprocess.run([
            ZIPALIGN_PATH,
            "-v", "4",
            input_apk,
            output_apk
        ], check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"zipalign 对齐失败: {e}")
        return False
    except FileNotFoundError:
        print("错误: 找不到 zipalign 工具，请确保 Android SDK 已安装并配置")
        return False

def sign_apk_with_pem_pk8(apk_path):
    """使用 .x509.pem 和 .pk8 文件签名 APK"""
    try:
        subprocess.run([
            "java", "-jar", APKSIGNER_PATH,
            "sign",
            "--key", PK8_KEY,
            "--cert", X509_CERT,
            "--v1-signer-name", "C=US, O=Android, CN=Android",
            "--v2-signing-enabled", "true",
            "--out", apk_path,
            apk_path
        ], check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"APK 签名失败: {e}")
        return False
    except FileNotFoundError:
        print("错误: 找不到 apksigner.jar 或 java 命令")
        return False

def modify_packs(extract_dir, data_dir):
    """修改资源包和行为包"""
    try:
        possible_pack_paths = [
            os.path.join(extract_dir, "assets", "resource_packs"),
            os.path.join(extract_dir, "assets", "behavior_packs"),
            os.path.join(extract_dir, "assets", "assets", "resource_packs"),
            os.path.join(extract_dir, "assets", "assets", "behavior_packs"),
            os.path.join(extract_dir, "resource_packs"),
            os.path.join(extract_dir, "behavior_packs"),
        ]

        src_resource = os.path.join(data_dir, "resource_packs")
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

        src_behavior = os.path.join(data_dir, "behavior_packs")
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
            "--distpath \"./"
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

def main():
    print("网易 MCBE 客户端快速构建")
    print("=" * 60)
    
    # 检查是否要构建PC版本
    if len(sys.argv) > 1 and sys.argv[1].lower() == "build":
        build_pc_version()
        clean_up()
        input("按回车键退出...")
        return
    
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
        if not modify_packs(temp_dir, data_dir):
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
        
        print("\n步骤 5/5: 签名 APK...")
        if not sign_apk_with_pem_pk8(aligned_apk):
            input("按回车键退出...")
            return
        
        os.rename(aligned_apk, final_apk)
        os.remove(unsigned_apk)
        
        print(f"\n处理完成! 已签名的 APK 保存在: {final_apk}")
        
        # 自动还原备份到当前目录
        print("\n正在还原原始APK备份...")
        restore_backup(backup_path, apk_path)
        
        # 询问是否要构建PC版本
        build_confirm = input("\n是否要构建PC平台可执行文件? (y/n): ").lower()
        if build_confirm == 'y':
            build_pc_version()
        
        # 清理临时文件
        clean_up()
        input("按回车键退出...")

if __name__ == "__main__":
    APK_NAME = f"{input('底包名称:')}.apk"
    main()