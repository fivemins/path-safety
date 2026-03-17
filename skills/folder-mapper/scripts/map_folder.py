#!/usr/bin/env python3
"""
文件夹映射工具 - 安全增强版（用户可配置）
"""
import os
import sys
import json
import re
from pathlib import Path

WORKSPACE = Path.home() / ".openclaw" / "workspace"
MOUNT_DIR = WORKSPACE / "mnt"
META_FILE = WORKSPACE / "folder_mapping.json"
CONFIG_FILE = WORKSPACE / "folder_mapper_config.json"

# 默认禁止的系统目录（不可修改）
# Linux 系统目录
DEFAULT_FORBIDDEN = [
    "/",
    "/bin",
    "/boot",
    "/dev",
    "/etc",
    "/lib",
    "/lib64",
    "/proc",
    "/root",
    "/sbin",
    "/sys",
    "/usr",
    "/var",
]

# 添加所有可能的盘符挂载点（/mnt/a 到 /mnt/z）
for letter in 'abcdefghijklmnopqrstuvwxyz':
    DEFAULT_FORBIDDEN.append(f"/mnt/{letter}")

WINDOWS_DRIVE_ROOT_RE = re.compile(r'^[A-Za-z]:\\?$')
WINDOWS_DRIVE_PATH_RE = re.compile(r'^[A-Za-z]:\\')
SAFE_LINK_NAME_RE = re.compile(r'^[A-Za-z0-9_.-]+$')


def validate_link_name(link_name: str) -> tuple[bool, str]:
    """统一校验映射名，避免路径穿越和非法字符。"""
    if not link_name:
        return False, "映射名不能为空"

    if not SAFE_LINK_NAME_RE.match(link_name):
        return False, "映射名仅允许字母、数字、下划线(_)、连字符(-)、点(.)"

    if link_name in {'.', '..'} or '..' in link_name:
        return False, "映射名不能包含 '..'"

    if '/' in link_name or '\\' in link_name:
        return False, "映射名不能包含路径分隔符"

    return True, "ok"


def is_within_mount_dir(path: Path) -> bool:
    """检查路径是否位于 MOUNT_DIR 目录下（按条目自身路径，不跟随最终符号链接目标）。"""
    mount_root = MOUNT_DIR.resolve()
    candidate = path.parent.resolve() / path.name
    try:
        candidate.relative_to(mount_root)
        return True
    except ValueError:
        return False


def ensure_workspace_files():
    """确保工作目录存在"""
    WORKSPACE.mkdir(parents=True, exist_ok=True)
    MOUNT_DIR.mkdir(parents=True, exist_ok=True)


def load_config() -> dict:
    """加载用户配置"""
    ensure_workspace_files()
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r') as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data
        except (json.JSONDecodeError, OSError):
            pass
    return {"forbidden_paths": [], "sensitive_paths": []}


def save_config(config: dict):
    """保存用户配置"""
    ensure_workspace_files()
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)


def add_forbidden(path: str) -> dict:
    """添加禁止访问的目录"""
    config = load_config()
    path = str(Path(path).expanduser().resolve())
    
    if path not in config.get("forbidden_paths", []):
        config.setdefault("forbidden_paths", []).append(path)
        save_config(config)
        return {"success": True, "message": f"已添加禁止目录: {path}"}
    return {"success": False, "message": "目录已在黑名单中"}


def remove_forbidden(path: str) -> dict:
    """移除禁止访问的目录"""
    config = load_config()
    path = str(Path(path).expanduser().resolve())
    
    if path in config.get("forbidden_paths", []):
        config["forbidden_paths"].remove(path)
        save_config(config)
        return {"success": True, "message": f"已移除禁止目录: {path}"}
    return {"success": False, "message": "目录不在黑名单中"}


def add_sensitive(path: str) -> dict:
    """添加敏感目录（需要二次确认）"""
    config = load_config()
    path = str(Path(path).expanduser().resolve())
    
    if path not in config.get("sensitive_paths", []):
        config.setdefault("sensitive_paths", []).append(path)
        save_config(config)
        return {"success": True, "message": f"已添加敏感目录: {path}"}
    return {"success": False, "message": "目录已在敏感列表中"}


def remove_sensitive(path: str) -> dict:
    """移除敏感目录"""
    config = load_config()
    path = str(Path(path).expanduser().resolve())
    
    if path in config.get("sensitive_paths", []):
        config["sensitive_paths"].remove(path)
        save_config(config)
        return {"success": True, "message": f"已移除敏感目录: {path}"}
    return {"success": False, "message": "目录不在敏感列表中"}


def show_config():
    """显示当前配置"""
    config = load_config()
    print("\n📋 当前配置:")
    print("-" * 50)
    print(f"系统默认禁止目录 ({len(DEFAULT_FORBIDDEN)}): {', '.join(DEFAULT_FORBIDDEN[:5])}...")
    forbidden_paths = config.get("forbidden_paths", [])
    sensitive_paths = config.get("sensitive_paths", [])

    print(f"\n用户禁止目录 ({len(forbidden_paths)}):")
    for p in forbidden_paths:
        print(f"  🚫 {p}")
    if not forbidden_paths:
        print("  (无)")

    print(f"\n敏感目录 ({len(sensitive_paths)}):")
    for p in sensitive_paths:
        print(f"  ⚠️  {p}")
    if not sensitive_paths:
        print("  (无)")
    print("-" * 50)


def ensure_mount_dir():
    ensure_workspace_files()


def load_mappings() -> dict:
    ensure_workspace_files()
    if META_FILE.exists():
        try:
            with open(META_FILE, 'r') as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def save_mappings(mappings: dict):
    ensure_workspace_files()
    with open(META_FILE, 'w') as f:
        json.dump(mappings, f, indent=2)


def is_same_or_subpath(path: str, base: str) -> bool:
    """检查 path 是否等于或位于 base 下方"""
    path_obj = Path(path)
    base_obj = Path(base)
    try:
        path_obj.relative_to(base_obj)
        return True
    except ValueError:
        return False


def is_path_allowed(path: str) -> tuple:
    """
    检查路径是否允许映射
    返回: (允许, 原因)
    """
    # 先检查用户输入的原始字符串，而不是 resolve() 后的规范化路径。
    # 原因：在 Linux 上 resolve() 会把 "C:\\" 等字符串当作普通文件名处理，
    # 变成 "<cwd>/C:\\"，从而丢失“它原本是 Windows 盘符路径”的语义。
    # 因此要先基于原始输入拦截 Windows 盘符根目录，再对普通路径做规范化与黑名单检查。
    if WINDOWS_DRIVE_ROOT_RE.match(path):
        return False, f"禁止映射盘符根目录: {path}"

    p = Path(path).expanduser().resolve()
    config = load_config()
    path_str = str(p)
    
    # 检查默认黑名单
    for forbidden in DEFAULT_FORBIDDEN:
        # "/" 仅阻止根目录本身；其余目录阻止自身及其子目录
        if forbidden == "/":
            if path_str == "/":
                return False, "禁止映射系统目录: /"
            continue
        if is_same_or_subpath(path_str, forbidden):
            return False, f"禁止映射系统目录: {forbidden}"
    
    # 检查用户黑名单
    for forbidden in config.get("forbidden_paths", []):
        if is_same_or_subpath(path_str, forbidden):
            return False, f"用户禁止映射: {forbidden}"
    
    # 检查是否敏感
    is_sensitive = any(is_same_or_subpath(path_str, s) for s in config.get("sensitive_paths", []))
    
    return True, "sensitive" if is_sensitive else "ok"


def get_unique_name(folder_path: Path) -> str:
    ensure_mount_dir()
    base_name = folder_path.name
    name = base_name
    counter = 1
    while (MOUNT_DIR / name).exists():
        name = f"{base_name}_{counter}"
        counter += 1
    return name


def mount_folder(folder_path: str) -> dict:
    path = Path(folder_path).expanduser().resolve()
    
    if not path.exists():
        return {"success": False, "error": f"文件夹不存在: {path}"}
    
    if not path.is_dir():
        return {"success": False, "error": f"不是有效文件夹: {path}"}
    
    allowed, reason = is_path_allowed(str(path))
    if not allowed:
        return {"success": False, "error": reason}
    
    sensitive_warning = ""
    if reason == "sensitive":
        sensitive_warning = f"\n⚠️ 警告: 该目录需要二次确认！"
    
    link_name = get_unique_name(path)
    link_path = MOUNT_DIR / link_name
    
    try:
        os.symlink(path, link_path)
        
        mappings = load_mappings()
        mappings[link_name] = {
            "source": str(path),
            "link": str(link_path),
            "sensitive": reason == "sensitive",
        }
        save_mappings(mappings)
        
        return {
            "success": True,
            "link_name": link_name,
            "link_path": str(link_path),
            "access_path": f"mnt/{link_name}",
            "source": str(path),
            "warning": sensitive_warning,
            "message": f"✅ 已映射到 mnt/{link_name} (安全映射（非强制只读）){sensitive_warning}\n⚠️ 警告：此为符号链接，删除/修改会直接影响原文件！"
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}


def unmount_folder(link_name: str) -> dict:
    ensure_mount_dir()
    valid, reason = validate_link_name(link_name)
    if not valid:
        return {"success": False, "error": f"非法映射名: {reason}"}

    link_path = MOUNT_DIR / link_name
    if not is_within_mount_dir(link_path):
        return {"success": False, "error": "非法映射路径: 仅允许操作 mnt 目录内的直接子项"}
    
    if not link_path.exists():
        return {"success": False, "error": f"映射不存在: {link_name}"}
    
    try:
        if link_path.is_symlink():
            link_path.unlink()
        else:
            return {"success": False, "error": f"映射损坏，请手动检查: {link_name}"}
        
        mappings = load_mappings()
        if link_name in mappings:
            del mappings[link_name]
            save_mappings(mappings)
        
        return {"success": True, "message": f"✅ 已解除映射: {link_name}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def list_mappings() -> dict:
    ensure_mount_dir()
    mappings = load_mappings()
    has_anomaly = False
    
    # 如果映射文件为空/损坏，尝试从实际符号链接恢复
    if not mappings and MOUNT_DIR.exists():
        for item in MOUNT_DIR.iterdir():
            if item.is_symlink():
                target = item.resolve()
                if target.exists() and target.is_dir():
                    # 从实际符号链接恢复映射记录
                    mappings[item.name] = {
                        "source": str(target),
                        "link": str(item),
                        "sensitive": False,
                    }
        if mappings:
            save_mappings(mappings)
    
    active = []
    stale = []
    for name, info in mappings.items():
        link_path = Path(info["link"])
        if not link_path.exists():
            stale.append(name)
            continue

        if not link_path.is_symlink():
            stale.append(name)
            has_anomaly = True
            continue

        if link_path.exists():
            active.append({**info, "name": name})

    for name in stale:
        del mappings[name]

    if MOUNT_DIR.exists():
        for item in MOUNT_DIR.iterdir():
            if item.is_symlink():
                continue
            has_anomaly = True
    
    save_mappings(mappings)
    return {
        "active": active,
        "count": len(active),
        "has_anomaly": has_anomaly,
        "warning": "发现异常挂载条目，请人工确认" if has_anomaly else "",
    }


def check_dangerous_operation(path: str, operation: str) -> tuple:
    mappings = load_mappings()
    normalized_path = str(Path(path).expanduser().resolve())
    normalized_operation = operation.strip().lower()
    
    for name, info in mappings.items():
        source = info.get("source", "")
        sensitive = info.get("sensitive", False)
        
        if is_same_or_subpath(normalized_path, source):
            if sensitive:
                return True, f"⚠️ 敏感目录操作: {normalized_operation} {normalized_path}\n需要二次确认！"
            if normalized_operation in ["delete", "rm", "rm -r"]:
                return True, f"⚠️ 删除操作: {normalized_path}\n这是映射目录，删除将直接影响原文件！请确认。"
    
    return False, ""


def clean_all() -> dict:
    ensure_mount_dir()
    mappings = load_mappings()
    
    warnings = []

    safe_entries = []
    for name in list(mappings.keys()):
        valid, reason = validate_link_name(name)
        if not valid:
            return {"success": False, "error": f"发现非法映射名 '{name}': {reason}"}

        link_path = MOUNT_DIR / name
        if not is_within_mount_dir(link_path):
            return {"success": False, "error": f"发现越界映射路径，已停止清理: {name}"}
        safe_entries.append((name, link_path))
    
    for name, link_path in safe_entries:
        try:
            if link_path.exists():
                if link_path.is_symlink():
                    link_path.unlink()
                else:
                    warnings.append(f"跳过异常条目(非符号链接): {link_path}")
        except OSError:
            continue
    
    save_mappings({})
    message = "已清理所有映射"
    if warnings:
        message += "\n发现异常挂载条目，请人工确认"
    return {"success": True, "message": message, "warnings": warnings}


def show_usage():
    print("""
📁 文件夹映射工具 (用户可配置版)

用法:
  python3 map_folder.py mount <路径>      映射文件夹（安全映射，非强制只读）
  python3 map_folder.py unmount <名称>    取消映射
  python3 map_folder.py list             查看当前映射
  python3 map_folder.py clean            清理所有映射
  python3 map_folder.py config           显示配置
  python3 map_folder.py forbid <路径>    添加禁止目录
  python3 map_folder.py allow <路径>     移除禁止目录
  python3 map_folder.py sensitive <路径> 添加敏感目录
  python3 map_folder.py desensitive <路径> 移除敏感目录
  python3 map_folder.py guard <操作> <路径> 风险检测并执行确认

配置说明:
  - 禁止目录: 绝对不能映射（系统目录自动包含）
  - 敏感目录: 可通过 guard 命令触发风险检测与确认
""")


def main():
    if len(sys.argv) < 2:
        show_usage()
        return
    
    command = sys.argv[1].lower()
    
    if command == "mount":
        if len(sys.argv) < 3:
            print("用法: python3 map_folder.py mount <文件夹路径>")
            sys.exit(1)
        result = mount_folder(sys.argv[2])
        print(result.get("message", result.get("error", "")))
        if not result.get("success", False):
            sys.exit(1)
        
    elif command == "unmount":
        if len(sys.argv) < 3:
            print("用法: python3 map_folder.py unmount <映射名>")
            sys.exit(1)
        valid, reason = validate_link_name(sys.argv[2])
        if not valid:
            print(f"非法映射名: {reason}")
            sys.exit(1)
        result = unmount_folder(sys.argv[2])
        print(result.get("message", result.get("error", "")))
        if not result.get("success", False):
            sys.exit(1)
        
    elif command == "list":
        result = list_mappings()
        print(f"\n📁 当前映射 ({result['count']} 个):")
        for m in result['active']:
            print(f"  {m['name']} -> {m['source']}")
        if result.get("has_anomaly"):
            print(f"\n⚠️ {result['warning']}")
        
    elif command == "config":
        show_config()
        
    elif command == "forbid":
        if len(sys.argv) < 3:
            print("用法: python3 map_folder.py forbid <路径>")
            sys.exit(1)
        result = add_forbidden(sys.argv[2])
        print(result["message"])
        
    elif command == "allow":
        if len(sys.argv) < 3:
            print("用法: python3 map_folder.py allow <路径>")
            sys.exit(1)
        result = remove_forbidden(sys.argv[2])
        print(result["message"])
        
    elif command == "sensitive":
        if len(sys.argv) < 3:
            print("用法: python3 map_folder.py sensitive <路径>")
            sys.exit(1)
        result = add_sensitive(sys.argv[2])
        print(result["message"])
        
    elif command == "desensitive":
        if len(sys.argv) < 3:
            print("用法: python3 map_folder.py desensitive <路径>")
            sys.exit(1)
        result = remove_sensitive(sys.argv[2])
        print(result["message"])

    elif command == "guard":
        if len(sys.argv) < 4:
            print("用法: python3 map_folder.py guard <操作> <路径>")
            sys.exit(1)

        operation = sys.argv[2]
        target_path = sys.argv[3]
        needs_confirm, warning = check_dangerous_operation(target_path, operation)

        if not needs_confirm:
            print("✅ 风险检测通过：当前操作无需额外确认")
            return

        print(warning)
        user_input = input("请输入 YES 确认继续执行：").strip()
        if user_input == "YES":
            print("✅ 已确认，可继续执行")
            return

        print("❌ 未确认，已取消操作")
        sys.exit(1)
        
    elif command == "clean":
        result = clean_all()
        print(result.get("message", result.get("error", "")))
        for warning in result.get("warnings", []):
            print(f"⚠️ {warning}")
        if not result.get("success", False):
            sys.exit(1)
        
    else:
        show_usage()


if __name__ == "__main__":
    main()
