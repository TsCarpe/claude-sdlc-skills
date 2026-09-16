# harness — 可移植红线检查引擎

> 对应心智模型 [docs/design/agent-stack-mental-model.md](../docs/design/agent-stack-mental-model.md) §4：时机定载体——
> 服从性规则（可机械校验的"写了就是错"）在**写文件瞬间**由 hook 拦截，
> 判断性规则留在 skill/spec（知识层本职）。

## 架构

- **引擎（机制）**：本目录 `engine/check.py`，全局一份，python3 + PyYAML
- **规则（内容）**：各项目 `.claude/guardrails.yaml`，从被检文件向上查找
- 引擎零项目知识；换项目 = 只写规则文件 + 挂载段

## 新项目接入（三步）

1. 复制挂载段到项目 `.claude/settings.json`（把引擎路径改为本机 checkout 位置）：

   见 [templates/settings-hook.json](templates/settings-hook.json)（harness 目录下，非仓库根 templates/）

2. 写项目 `.claude/guardrails.yaml`（从零，或参考 [docs/dev-standards-reference/guardrails.example.yaml](../docs/dev-standards-reference/guardrails.example.yaml)）：

   ```yaml
   version: 1
   rules:
     - id: no-printstacktrace        # 唯一标识
       glob: "**/*.java"             # ** 跨目录 / * 单段
       type: forbid                  # forbid | require | require_if | count_ge
       pattern: "printStackTrace\\s*\\("   # 正则（YAML 单引号防转义坑）
       message: "禁止 printStackTrace"
   ```

   - `forbid`：pattern 出现即违规
   - `require`：pattern 至少出现一次（文件级）
   - `require_if`：文件命中 `when` 模式时 `pattern` 必须出现（如"Req 含 page 字段则须有 @Min"）；`when` 为该类型必填
   - `count_ge`：`pattern` 出现次数 ≥ `anchor` 出现次数（如"每个 @PostMapping 都要有 @LogRecord"的文件级近似）

3. 写一个违规文件实测拦截（pipe-test）：

   ```bash
   echo '{"tool_input":{"file_path":"<绝对路径>"}}' \
     | python3 <引擎路径>/engine/check.py
   ```

## 语义要点

- **Write 新文件**：全文件全规则检查
- **Edit 存量文件**：只对本次新增文本（new_string）跑 forbid——存量旧账不阻塞编辑者，由基线扫描（`--check`）出报告
- **无规则文件 = no-op**：找不到 `.claude/guardrails.yaml` 直接退出，零开销
- **引擎永不打断 agent 循环**：内部异常静默 exit 0，拦截仅通过 JSON `decision: "block"` 表达，reason 会回给模型自我修正

## check 模式（pre-commit / 基线扫描）

```bash
python3 engine/check.py --check <file>...   # 违规 exit 1，人类可读输出
```

## 已知边界（v1）

- `count_ge` 是文件级计数近似，非逐方法解析（够用：缺注解必然计数不等）
- 规则纯 regex，不做 AST——需要类型/跨文件分析的规则（如 Service 出参 DTO）不在此层，走 CI/测试期（ArchUnit 等）
- 逃生通道：无（hook 层不放行豁免注释；确需例外改项目规则文件的 glob/删规则）
