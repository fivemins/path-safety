# folder-mapper

临时文件夹映射工具，为 AI Agent 提供安全访问外部目录的能力。

## 特性

- 🔗 将外部文件夹映射到工作空间（符号链接）
- 🔒 默认安全映射模式（附带风险提示）
- 🛡️ 系统目录保护（禁止映射危险目录）
- ⚙️ 用户可配置禁止/敏感目录
- ⚠️ 敏感操作二次确认

## 安装

```bash
npx skills add fivemins/folder-mapper
```

## 使用方法

### 映射文件夹

```bash
python3 scripts/map_folder.py mount "/path/to/folder"
```

### 查看当前映射

```bash
python3 scripts/map_folder.py list
```

### 取消映射

```bash
python3 scripts/map_folder.py unmount <文件夹名>
```

### 配置禁止目录（绝对不能映射）

```bash
python3 scripts/map_folder.py forbid "/path/to/secure"
```

### 配置敏感目录（需要二次确认）

```bash
python3 scripts/map_folder.py sensitive "/path/to/important"
```

### 查看配置

```bash
python3 scripts/map_folder.py config
```

### 清理所有映射

```bash
python3 scripts/map_folder.py clean
```

## 安全机制

| 机制 | 说明 |
|------|------|
| 默认禁止 | `/`, `/bin`, `/etc`, `/proc` 等系统目录 |
| 用户禁止 | 用户自定义的绝对不能映射的目录 |
| 敏感目录 | 用户自定义的需要二次确认的目录 |
| 安全映射 | 默认使用符号链接并附带风险提示 |
| 二次确认 | 删除/修改敏感目录时提示确认 |

## 工作流程

1. 用户配置禁止/敏感目录（可选）
2. 执行 `mount` 映射文件夹
3. 在 `mnt/<映射名>` 下访问
4. 任务完成后执行 `unmount` 解除映射

## 示例

```bash
# 映射一个文件夹
python3 scripts/map_folder.py mount "/home/user/Documents"

# 查看映射
python3 scripts/map_folder.py list

# 访问映射目录（在工作空间 mnt/Documents）

# 取消映射
python3 scripts/map_folder.py unmount Documents
```

## 许可证

MIT
