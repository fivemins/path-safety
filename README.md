# folder-mapper

[English](#english) | [中文](#中文)

---

## 中文

**folder-mapper** 是一个面向 AI Agent 的受控目录接入工具。  
它不是为了替代 WSL 自带的 `/mnt/c`、`/mnt/d` 盘符访问，而是为了在 Agent 工作流中提供：

- **统一的外部目录入口**
- **危险路径拦截**
- **敏感目录标记与风险检测**
- **映射关系的可管理性与可追踪性**

换句话说，`folder-mapper` 的核心价值不在“让目录变得可访问”，而在“让 AI 以更可控的方式访问目录”。

### 它适合解决什么问题？

当 AI Agent 需要访问外部目录时，直接使用原始绝对路径通常会带来一些问题：

- 路径分散，不利于统一管理
- 容易误操作系统目录或高风险目录
- 调用方很难在执行前做风险判断
- 不清楚当前到底映射了哪些目录

`folder-mapper` 提供了一层轻量治理机制：

- 将外部目录映射到工作区统一入口
- 禁止系统目录、盘符根目录等危险路径
- 支持自定义 forbidden / sensitive 路径
- 为删除等高风险操作提供 `guard` 风险检测接口
- 维护映射元数据，避免“映射过什么已经不清楚”

### 适用场景

1. **AI Agent 的受控文件访问**  
   让 Agent 只通过映射后的工作区目录访问外部数据，而不是直接操作分散的绝对路径。
2. **非 WSL 自动挂载路径**  
   例如：网络共享目录、NAS 挂载目录、SSHFS 挂载目录、容器卷、其他外部挂载点。
3. **团队协作中的统一路径规范**  
   团队可约定统一通过映射目录访问外部资源，减少脚本、技能、工具之间的路径分歧。
4. **高风险操作前的安全检查**  
   对删除、覆盖、批量处理等操作，可先调用 `guard` 做风险判定，再决定是否继续。

### 不适合的场景

如果你只是想在 WSL 中访问 Windows 盘符，例如：

- `/mnt/c/...`
- `/mnt/d/...`

那么通常 **无需** 使用本工具。  
这些路径本身已经可直接访问，`folder-mapper` 不会提升底层访问能力。

因此，本工具更适合“**需要治理、约束、统一入口和风险控制**”的场景，而不是单纯的目录访问。

### 特性

- 将外部文件夹映射到工作空间（符号链接）
- 提供统一目录入口，便于 Agent / Skill 使用
- 系统目录保护（禁止映射危险目录）
- 盘符根目录保护（禁止映射 `/mnt/c`、`/mnt/d` 等所有盘符挂载点）
- 用户可配置 forbidden / sensitive 目录
- 提供风险检测接口，调用方可接入二次确认流程
- 维护映射元数据，便于审计与管理
- 安全映射（**非强制只读**）

### 安装

```bash
npx skills add fivemins/folder-mapper
```

### 使用方法

以下示例默认在仓库根目录执行：

```bash
# 最小自检：验证脚本路径
python3 skills/folder-mapper/scripts/map_folder.py list

# 映射文件夹
python3 skills/folder-mapper/scripts/map_folder.py mount "/path/to/folder"

# 查看当前映射
python3 skills/folder-mapper/scripts/map_folder.py list

# 取消映射
python3 skills/folder-mapper/scripts/map_folder.py unmount <folder_name>

# 清理所有映射
python3 skills/folder-mapper/scripts/map_folder.py clean

# 添加禁止目录
python3 skills/folder-mapper/scripts/map_folder.py forbid "/path/to/secure"

# 添加敏感目录
python3 skills/folder-mapper/scripts/map_folder.py sensitive "/path/to/important"

# 移除禁止目录
python3 skills/folder-mapper/scripts/map_folder.py allow "/path/to/secure"

# 移除敏感目录
python3 skills/folder-mapper/scripts/map_folder.py desensitive "/path/to/important"

# 风险检测（按需触发确认）
python3 skills/folder-mapper/scripts/map_folder.py guard delete "/path/to/important/file"

# 查看配置
python3 skills/folder-mapper/scripts/map_folder.py config
```

或者进入脚本目录运行：

```bash
cd skills/folder-mapper/scripts
python3 map_folder.py list
```

### 工作方式说明

`folder-mapper` 当前采用符号链接（symlink）实现目录映射。

这意味着：

- 它不是内核级挂载工具
- 它不是强制只读沙箱
- 通过映射路径进行写入、删除、重命名，会直接作用于源目录

因此，更准确地说，它是一个**面向 AI Agent 的目录接入与风险治理工具**，而不是一个强隔离的文件系统安全容器。

### 注意事项

- 当前映射基于符号链接，不是内核级强制只读挂载
- 通过映射路径进行写入、删除、重命名会直接作用于源目录
- 建议在高风险操作前先使用 `guard` 做风险检测
- 自动化调用建议检查进程退出码：`mount` / `unmount` / `clean` 失败返回非 0（成功为 0）
- 当映射元数据丢失并由实际符号链接自动恢复时，工具会按当前 `sensitive_paths` 配置重新计算并保留敏感标记

### 兼容性

- 当前脚本依赖 `fcntl` 文件锁，仅支持类 Unix 环境（Linux/macOS/WSL）
- 在原生 Windows（非 WSL）上无法直接运行，因为标准库缺少 `fcntl`
- 建议在 WSL 中运行；若需原生 Windows 支持，可后续引入跨平台锁实现替代 `fcntl`

### 常见错误

| 场景 | 典型提示 | 说明 |
|---|---|---|
| 权限不足 | 映射失败：权限不足 / 解除映射失败：权限不足 | 当前用户无权创建/删除符号链接或访问目标目录 |
| 路径不存在 | 文件夹不存在: ... / 映射失败：路径不存在 | 目标目录已删除、路径输入错误，或并发操作导致路径失效 |
| 映射名非法 | 非法映射名: ... | `unmount` 入参包含非法字符、路径分隔符，或包含 `..` |

### 安全机制

| 机制 | 说明 |
|---|---|
| 默认禁止 | `/`、`/bin`、`/etc`、`/proc` 等系统目录 |
| 盘符保护 | `/mnt/a` 到 `/mnt/z` 全部禁止 |
| 用户禁止 | 自定义绝对不能映射的目录 |
| 敏感目录 | 标记高风险目录，供 `guard` 检测 |
| 策略复用 | 风险判定与映射判定共用同一策略实现 |
| 安全映射（非强制只读） | 使用符号链接映射，避免复制；不提供内核级只读保证 |
| 跨平台路径规范化差异 | 原始输入会先执行 Windows 盘符根目录判定，再进行 `Path(...).expanduser().resolve()` 与黑名单/敏感判断，避免语义丢失 |

### 一句话总结

`folder-mapper` 不是为了替代系统挂载，而是为了给 AI Agent 提供一个更可控、更可治理、更适合自动化工作流的外部目录接入层。

---

## English

**folder-mapper** is a controlled directory access tool for AI agents.  
It is not meant to replace WSL’s built-in access to paths like `/mnt/c` or `/mnt/d`. Instead, it provides:

- a unified entry point for external directories,
- dangerous path blocking,
- sensitive path marking and risk checks,
- and manageable mapping metadata.

In short, the core value of `folder-mapper` is not “making folders accessible,” but making folder access more controllable for AI workflows.

### What problem does it solve?

When an AI agent works with external directories through raw absolute paths, several problems usually appear:

- scattered paths with no unified convention,
- accidental access to system or high-risk directories,
- no pre-check before destructive operations,
- unclear visibility into what has already been mapped.

`folder-mapper` adds a lightweight governance layer:

- maps external folders into a unified workspace entry,
- blocks system directories and drive-root mount points,
- supports user-defined forbidden and sensitive paths,
- provides a `guard` interface for risky operations,
- maintains mapping metadata for visibility and recovery.

### Good fit for

1. **Controlled file access for AI agents**  
   Allow agents to operate through mapped workspace directories instead of arbitrary absolute paths.
2. **Non-default mounted locations**  
   Examples include network shares, NAS mounts, SSHFS mounts, container volumes, and other external mounted locations.
3. **Team-wide path conventions**  
   Different skills, scripts, and tools can access external resources through a consistent mapping pattern.
4. **Pre-checks for destructive operations**  
   Before delete / overwrite / batch actions, callers can use `guard` as a safety gate.

### Not the best fit for

If you only want to access standard Windows drives from WSL, such as:

- `/mnt/c/...`
- `/mnt/d/...`

then you usually do not need this tool.  
Those paths are already directly accessible, and `folder-mapper` does not add new low-level access capability.

So this tool is better understood as a governance and control layer, not as a generic folder access utility.

### Features

- Map external folders into workspace via symlinks
- Provide a unified directory entry for agents / skills
- System directory protection
- Drive-root protection (`/mnt/c`, `/mnt/d`, etc.)
- User-configurable forbidden and sensitive paths
- Risk-detection interface for caller-controlled confirmation flow
- Mapping metadata management
- Safe mapping (not enforced read-only)

### Installation

```bash
npx skills add fivemins/folder-mapper
```

### Usage

Examples assume you run commands from the repository root:

```bash
# Minimal self-check: verify script path
python3 skills/folder-mapper/scripts/map_folder.py list

# Map a folder
python3 skills/folder-mapper/scripts/map_folder.py mount "/path/to/folder"

# List current mappings
python3 skills/folder-mapper/scripts/map_folder.py list

# Unmount
python3 skills/folder-mapper/scripts/map_folder.py unmount <folder_name>

# Clean all mappings
python3 skills/folder-mapper/scripts/map_folder.py clean

# Add forbidden directory
python3 skills/folder-mapper/scripts/map_folder.py forbid "/path/to/secure"

# Add sensitive directory
python3 skills/folder-mapper/scripts/map_folder.py sensitive "/path/to/important"

# Remove forbidden directory
python3 skills/folder-mapper/scripts/map_folder.py allow "/path/to/secure"

# Remove sensitive directory
python3 skills/folder-mapper/scripts/map_folder.py desensitive "/path/to/important"

# Risk check (optional confirmation gate)
python3 skills/folder-mapper/scripts/map_folder.py guard delete "/path/to/important/file"

# View configuration
python3 skills/folder-mapper/scripts/map_folder.py config
```

Or run from the script directory:

```bash
cd skills/folder-mapper/scripts
python3 map_folder.py list
```

### How it works

`folder-mapper` currently uses symlinks for mapping.

That means:

- it is not a kernel-level mount tool,
- it is not an enforced read-only sandbox,
- writes, deletes, and renames through mapped paths affect the source directory directly.

So the project should be understood as a **directory access and risk-governance layer for AI agents**, not a strong filesystem isolation boundary.

### Notes

- Mapping is implemented via symlinks, not a kernel-enforced read-only mount
- Writes, deletes, and renames through mapped paths apply directly to the source directory
- Use `guard` before destructive operations when safety matters
- For automation, check exit codes: `mount` / `unmount` / `clean` return non-zero on failure
- If metadata is lost and restored from actual symlinks, sensitive flags are recalculated using current `sensitive_paths`

### Compatibility

- Depends on `fcntl` file locking, so it currently supports Unix-like environments only (Linux/macOS/WSL)
- Does not run directly on native Windows because Python stdlib there does not provide `fcntl`
- WSL is recommended; native Windows support could be added later via a cross-platform lock implementation

### Common errors

| Scenario | Typical message | Explanation |
|---|---|---|
| Permission denied | 映射失败：权限不足 / 解除映射失败：权限不足 | The current user cannot create/remove symlinks or access the target directory |
| Path does not exist | 文件夹不存在: ... / 映射失败：路径不存在 | Target folder was removed, the path is wrong, or concurrent operations invalidated it |
| Invalid mapping name | 非法映射名: ... | The `unmount` argument contains illegal characters, path separators, or `..` |

### Security model

| Mechanism | Description |
|---|---|
| Default blocked paths | Blocks `/`, `/bin`, `/etc`, `/proc`, etc. |
| Drive-root protection | Blocks `/mnt/a` to `/mnt/z` |
| User forbidden paths | User-defined paths that must never be mapped |
| Sensitive paths | Marks high-risk paths for `guard` checks |
| Shared policy logic | Risk checks and mapping checks reuse the same policy layer |
| Safe mapping (not enforced read-only) | Uses symlinks for low-overhead mapping without kernel-level read-only guarantees |
| Cross-platform path normalization nuance | Windows drive-root checks happen before `Path(...).expanduser().resolve()` so path meaning is not lost |

### One-line summary

`folder-mapper` is not a replacement for system mounts.  
It is a controlled external-directory access layer for AI agents, designed for safer automation, better path governance, and more manageable workflows.
