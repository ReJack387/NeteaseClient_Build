# NeteaseClient_Build
网易MCBE客户端双端快速构建
# 如何使用

1.安装JAVA，python，以及一些依赖

2.脚本根目录下新建一个data文件夹

3.在data文件夹中新建一个文件夹，取你的客户端名称（如“Cyan Heart”）

4.将你的客户端中*behavior_packs*和*resource_packs*文件夹放入“Cyan Heart”文件夹中

5.将你的底包放入根目录，并在fastbuild.py的第11行配置你的底包名称（客户端icon与APKNAME自己用MT搞好）

6.运行fastbuild.py
# 温馨提示
1.此工具已提供签名文件，但其密钥为AOSP密钥，AOSP密钥人尽皆知，可能在未来被封禁

2.多端构建仅适配***Yant***底包
