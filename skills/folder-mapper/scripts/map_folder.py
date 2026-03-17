#!/usr/bin/env python3
"""
文件夹映射工具 - 安全增强版（用户可配置）
"""
import os
import sys
import json
import re
import fcntl
import tempfile
from contextlib import contextmanager
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
SAFE_LINK_NAME_RE = re.compile(r'^[A-Za-z0-9_.-]+$')


def format_error_response(message: str, exc: Exception | None = None) -> dict:
    """统一错误返回结构，保留简洁提示并附带可诊断字段。"""
    response = {"success": False, "error": message}
    if exc is not None:
        response["error_type"] = type(exc).__name__
        response["error_detail"] = str(exc)
    return response


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


def _print_json_warning(file_path: Path, exc: Exception):
    print(f"⚠️ JSON 解析失败: {file_path} ({type(exc).__name__}: {exc})", file=sys.stderr)


def _read_json(path: Path, default):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        if not content.strip():
            return default
        data = json.loads(content)
        if isinstance(default, dict) and isinstance(data, dict):
            return data
        return default
    except FileNotFoundError:
        return default
    except json.JSONDecodeError as e:
        _print_json_warning(path, e)
    except OSError as e:
        print(f"⚠️ 读取失败: {path} ({type(e).__name__}: {e})", file=sys.stderr)
    return default


def _lock_file_path(path: Path) -> Path:
    return path.parent / f".{path.name}.lock"


@contextmanager
def _locked_file(path: Path, lock_type: int):
    ensure_workspace_files()
    path.parent.mkdir(parents=True, exist_ok=True)
    lock_path = _lock_file_path(path)
    with open(lock_path, 'a+', encoding='utf-8') as lock_handle:
        fcntl.flock(lock_handle.fileno(), lock_type)
        try:
            yield
        finally:
            fcntl.flock(lock_handle.fileno(), fcntl.LOCK_UN)


def _atomic_write_json(path: Path, payload: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as tmp_file:
            json.dump(payload, tmp_file, indent=2)
            tmp_file.flush()
            os.fsync(tmp_file.fileno())
        os.replace(tmp_name, path)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)


def _read_json_locked(path: Path, default):
    with _locked_file(path, fcntl.LOCK_SH):
        return _read_json(path, default)


def _write_json_locked(path: Path, payload: dict):
    with _locked_file(path, fcntl.LOCK_EX):
        _atomic_write_json(path, payload)


def _update_json_locked(path: Path, default, updater):
    with _locked_file(path, fcntl.LOCK_EX):
        data = _read_json(path, default)
        updated = updater(data)
        _atomic_write_json(path, updated)
        return updated


def load_config() -> dict:
    """加载用户配置"""
    return _read_json_locked(CONFIG_FILE, {"forbidden_paths": [], "sensitive_paths": []})


def save_config(config: dict):
    """保存用户配置"""
    _write_json_locked(CONFIG_FILE, config)


def add_forbidden(path: str) -> dict:
    """添加禁止访问的目录"""
    path = str(Path(path).expanduser().resolve())

    changed = {"value": False}

    def _updater(config: dict):
        forbidden_paths = config.setdefault("forbidden_paths", [])
        if path not in forbidden_paths:
            forbidden_paths.append(path)
            changed["value"] = True
        return config

    _update_json_locked(CONFIG_FILE, {"forbidden_paths": [], "sensitive_paths": []}, _updater)
    if changed["value"]:
        return {"success": True, "message": f"已添加禁止目录: {path}"}
    return {"success": False, "message": "目录已在黑名单中"}


def remove_forbidden(path: str) -> dict:
    """移除禁止访问的目录"""
    path = str(Path(path).expanduser().resolve())

    changed = {"value": False}

    def _updater(config: dict):
        forbidden_paths = config.setdefault("forbidden_paths", [])
        if path in forbidden_paths:
            forbidden_paths.remove(path)
            changed["value"] = True
        return config

    _update_json_locked(CONFIG_FILE, {"forbidden_paths": [], "sensitive_paths": []}, _updater)
    if changed["value"]:
        return {"success": True, "message": f"已移除禁止目录: {path}"}
    return {"success": False, "message": "目录不在黑名单中"}


def add_sensitive(path: str) -> dict:
    """添加敏感目录（需要二次确认）"""
    path = str(Path(path).expanduser().resolve())

    changed = {"value": False}

    def _updater(config: dict):
        sensitive_paths = config.setdefault("sensitive_paths", [])
        if path not in sensitive_paths:
            sensitive_paths.append(path)
            changed["value"] = True
        return config

    _update_json_locked(CONFIG_FILE, {"forbidden_paths": [], "sensitive_paths": []}, _updater)
    if changed["value"]:
        return {"success": True, "message": f"已添加敏感目录: {path}"}
    return {"success": False, "message": "目录已在敏感列表中"}


def remove_sensitive(path: str) -> dict:
    """移除敏感目录"""
    path = str(Path(path).expanduser().resolve())

    changed = {"value": False}

    def _updater(config: dict):
        sensitive_paths = config.setdefault("sensitive_paths", [])
        if path in sensitive_paths:
            sensitive_paths.remove(path)
            changed["value"] = True
        return config

    _update_json_locked(CONFIG_FILE, {"forbidden_paths": [], "sensitive_paths": []}, _updater)
    if changed["value"]:
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
    return _read_json_locked(META_FILE, {})


def save_mappings(mappings: dict):
    _write_json_locked(META_FILE, mappings)


def is_same_or_subpath(path: str, base: str) -> bool:
    """检查 path 是否等于或位于 base 下方"""
    path_obj = Path(path)
    base_obj = Path(base)
    try:
        path_obj.relative_to(base_obj)
        return True
    except ValueError:
        return False


def normalize_path(raw_path: str) -> tuple[Path | None, str | None]:
    """路径规范化策略：输入必须是原始字符串；返回 (绝对 Path, 错误信息)。"""
    if WINDOWS_DRIVE_ROOT_RE.match(raw_path):
        return None, f"禁止映射盘符根目录: {raw_path}"
    return Path(raw_path).expanduser().resolve(), None


def is_forbidden_path(path_str: str, config: dict) -> tuple[bool, str]:
    """禁止判定策略：输入必须是规范化后的绝对路径字符串。"""
    for forbidden in DEFAULT_FORBIDDEN:
        # "/" 仅阻止根目录本身；其余目录阻止自身及其子目录
        if forbidden == "/":
            if path_str == "/":
                return True, "禁止映射系统目录: /"
            continue
        if is_same_or_subpath(path_str, forbidden):
            return True, f"禁止映射系统目录: {forbidden}"

    for forbidden in config.get("forbidden_paths", []):
        if is_same_or_subpath(path_str, forbidden):
            return True, f"用户禁止映射: {forbidden}"

    return False, ""


def is_sensitive_path(path_str: str, config: dict) -> bool:
    """敏感判定策略：输入必须是规范化后的绝对路径字符串。"""
    return any(
        is_same_or_subpath(path_str, sensitive_path)
        for sensitive_path in config.get("sensitive_paths", [])
    )


def classify_path(raw_input: str, config: dict | None = None) -> dict:
    """统一路径分类策略：输入必须是原始字符串，返回规范化结果与风险标签。"""
    if config is None:
        config = load_config()

    path_obj, normalize_error = normalize_path(raw_input)
    if path_obj is None:
        return {
            "allowed": False,
            "reason": normalize_error,
            "path": None,
            "path_str": None,
            "is_sensitive": False,
        }

    path_str = str(path_obj)
    sensitive = is_sensitive_path(path_str, config)
    forbidden, forbidden_reason = is_forbidden_path(path_str, config)
    if forbidden:
        return {
            "allowed": False,
            "reason": forbidden_reason,
            "path": path_obj,
            "path_str": path_str,
            "is_sensitive": sensitive,
        }

    return {
        "allowed": True,
        "reason": "sensitive" if sensitive else "ok",
        "path": path_obj,
        "path_str": path_str,
        "is_sensitive": sensitive,
    }


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
    result = classify_path(folder_path)
    if not result["allowed"]:
        return {"success": False, "error": result["reason"]}

    path = result["path"]
    assert path is not None

    if not path.exists():
        return {"success": False, "error": f"文件夹不存在: {path}"}
    
    if not path.is_dir():
        return {"success": False, "error": f"不是有效文件夹: {path}"}
    
    sensitive_warning = ""
    if result["is_sensitive"]:
        sensitive_warning = f"\n⚠️ 警告: 该目录需要二次确认！"
    
    link_name = get_unique_name(path)
    link_path = MOUNT_DIR / link_name
    
    try:
        os.symlink(path, link_path)
        
        def _updater(mappings: dict):
            mappings[link_name] = {
                "source": str(path),
                "link": str(link_path),
                "sensitive": result["is_sensitive"],
            }
            return mappings

        _update_json_locked(META_FILE, {}, _updater)
        
        return {
            "success": True,
            "link_name": link_name,
            "link_path": str(link_path),
            "access_path": f"mnt/{link_name}",
            "source": str(path),
            "warning": sensitive_warning,
            "message": f"✅ 已映射到 mnt/{link_name} (安全映射（非强制只读）){sensitive_warning}\n⚠️ 警告：此为符号链接，删除/修改会直接影响原文件！"
        }
        
    except FileNotFoundError as e:
        return format_error_response("映射失败：路径不存在", e)
    except PermissionError as e:
        return format_error_response("映射失败：权限不足", e)
    except OSError as e:
        return format_error_response("映射失败：系统错误", e)


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
        
        def _updater(mappings: dict):
            if link_name in mappings:
                del mappings[link_name]
            return mappings

        _update_json_locked(META_FILE, {}, _updater)
        
        return {"success": True, "message": f"✅ 已解除映射: {link_name}"}
    except FileNotFoundError as e:
        return format_error_response("解除映射失败：映射路径不存在", e)
    except PermissionError as e:
        return format_error_response("解除映射失败：权限不足", e)
    except OSError as e:
        return format_error_response("解除映射失败：系统错误", e)


def list_mappings() -> dict:
    ensure_mount_dir()
    mappings = load_mappings()
    config = load_config()
    has_anomaly = False
    anomaly_items: list[str] = []
    
    # 如果映射文件为空/损坏，尝试从实际符号链接恢复
    if not mappings and MOUNT_DIR.exists():
        for item in MOUNT_DIR.iterdir():
            if item.is_symlink():
                try:
                    target = item.resolve()
                    if target.exists() and target.is_dir():
                        # 从实际符号链接恢复映射记录
                        mappings[item.name] = {
                            "source": str(target),
                            "link": str(item),
                            "sensitive": classify_path(str(target), config)["is_sensitive"],
                        }
                except (OSError, RuntimeError):
                    has_anomaly = True
                    anomaly_items.append(item.name)
                    continue
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
    warning = ""
    if has_anomaly:
        warning = "发现异常挂载条目，请人工确认"
        if anomaly_items:
            warning = f"{warning}: {', '.join(sorted(set(anomaly_items)))}"

    return {
        "active": active,
        "count": len(active),
        "has_anomaly": has_anomaly,
        "warning": warning,
    }


def check_dangerous_operation(path: str, operation: str) -> tuple:
    mappings = load_mappings()
    path_info = classify_path(path)
    normalized_path = path_info["path_str"]
    normalized_operation = operation.strip().lower()

    if not normalized_path:
        return True, f"⚠️ 路径判定异常: {path_info['reason']}"

    current_sensitive = path_info["is_sensitive"]
    
    for name, info in mappings.items():
        source = info.get("source", "")
        source_info = classify_path(source)
        sensitive = source_info["is_sensitive"] or current_sensitive
        
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
    
    _update_json_locked(META_FILE, {}, lambda _: {})
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
