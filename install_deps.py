import importlib.util
import subprocess
import sys

# 模块名 → pip 包名映射表
packages = {
    "requests": "requests",
    "execjs": "PyExecJS",
    "Crypto": "pycryptodome",
    "bs4": "beautifulsoup4",
    "requests_toolbelt": "requests-toolbelt",
    # 其他标准库模块（如 sys, os, time, json, base64, random, datetime, traceback, binascii, urllib）
    # 都是 Python 自带的，不需要安装
}

def check_and_install(module_name, package_name):
    spec = importlib.util.find_spec(module_name)
    if spec is not None:
        print(f"✅ 模块 {module_name} 已安装")
    else:
        print(f"⚠️ 模块 {module_name} 未安装，尝试安装 {package_name}...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
            print(f"🎉 成功安装 {package_name}")
        except Exception as e:
            print(f"❌ 安装 {package_name} 失败: {e}")

if __name__ == "__main__":
    for module, package in packages.items():
        check_and_install(module, package)

    print("\n所有依赖检查完成，现在你可以运行原始脚本了！")