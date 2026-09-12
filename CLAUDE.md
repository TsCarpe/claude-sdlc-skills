# claude-sdlc-skills 仓库导航（给在此仓库工作的 AI 与贡献者）

这是一个 Claude Code skill 集合仓库：5 个可安装 skill + 大需求三段式方法论文档。本文件是仓库结构约定与改动护栏。

## 仓库结构

```
skills/<name>/SKILL.md        # 5 个 skill（sdlc-intent/gate/test/doubt/config-review）
  references/                  # skill 的详细参考文档（模板/维度表/姿势手册），SKILL.md 只留精瘦主干+指针
  evals/                       # 评估场景（输入 + expected_behavior 勾选清单）
templates/                     # 大需求三段式产物模板（stage1/2/3），与 docs/large-req-playbook.md 配套
docs/                          # workflow（全流程叙述）/ large-req-playbook / example-walkthrough / faq / sdlc-test-design
.claude-plugin/marketplace.json  # 发布清单（plugin 渠道 + skills CLI 共用）
```

## 改动护栏（硬规则）

1. **新增/删除/改名 skill 必须同步 `.claude-plugin/marketplace.json` 的 `plugins[0].skills` 数组**——该数组是 plugin 渠道的完整集合（strict:false 下未列目录不加载）；漏登记 = 两渠道产物不一致
2. SKILL.md frontmatter：`name` 必须 kebab-case（marketplace 校验）；`description` 中英混合（英文语义句 + 中文触发词），这是触发与 /plugin 列表展示的唯一入口
3. **SKILL.md 保持精瘦**：细节放 references/，正文只留流程主干 + 指针；连续两层引用禁止（A 引 B、B 再引 C）
4. 跨 skill 引用用**同级相对路径**（`../sdlc-doubt/SKILL.md`）并声明「单独安装时仅作来源说明」——不同用户安装 scope（全局/项目）不同，禁止写死绝对路径
5. **脱敏红线**：不得出现真实项目名、公司名、内网地址、真实鉴权头字段、账号凭据；业务示例一律用中性虚构（商品/订单/评选活动类）。提交前跑：
   ```bash
   rg -i "edu-region|临平|linping|saasstaffid|saasregionid|saastenantid|skill_contest|工作室|hailiang|10\.30\." . --glob '!CHANGELOG.md'
   ```
   应零命中
6. 权限/配置示例只能新写条目，**禁止从任何本机 settings 文件复制**

## 本地验证（改完 skill 后）

```bash
npx skills@latest add ~/IdeaProjects/claude-sdlc-skills --list   # 应列出全部 skill（frontmatter 可解析）
python3 -m json.tool .claude-plugin/marketplace.json > /dev/null # JSON 合法
```

需要真实冒烟时：在 /tmp 建试验项目 `npx skills add <本仓库路径> -s <skill名> --copy -y` 安装后新开会话触发，验完删除。

## evals 约定

每个 skill 的 evals/README.md 是评估场景索引；场景文件 = 输入 + expected_behavior 勾选清单，手动回归用（无自动运行器），纪律红线（如「关卡未过就执行」）判负即整场景失败。
