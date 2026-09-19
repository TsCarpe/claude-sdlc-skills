# eval-5：v1.2 原文预处理与块级锚点管线

## 输入

- query：「梳理这个需求 <飞书链接>，完成后继续体检」（飞书 Docx，正文含表格详述与多级条款列表，内嵌图片/附件，段落带评论）
- 文档特征：详述表某行内嵌 ≥3 层列表条款；一处图片 token 已失效（下载必失败）；评论数 ≥12（产生 c10+ 引用键，考验自然序）

## expected_behavior

- [ ] 时机正确：正文 markdown 与评论 JSON 均读取完成后执行一次预处理（fetch XML → 提取 content/refmap → parse_doc.py），体检阶段不重复拉取 XML / 重跑解析器
- [ ] 落盘正确：doc-<YYYYMMDD>.json 与 media/ 均在 sdlc/<需求名>/intake/ 下；doc.json 含 source/generator/blocks/media，锚点用飞书原生块 ID（非 x- 合成 ID）
- [ ] 条款级出处：doc.json 存在时，梳理 §7 规则表与体检「原文定位」尽量写到条款级（「详述N·<小节名>」或「详述N·<序数>」，先用 list_clauses.py 查条款树）；定位不到条款级时回退章节名，不编造条款号
- [ ] 锚点附加：推送前用 resolve_anchors.py（--comments 优先传 list-comments JSON）生成 payload-anchored.json，fr_points/features/audit/items 的 anchor 均指向原文块 ID；「评论区#N」出处解析到第 N 条评论的 comment 块（N≥10 不错位）
- [ ] 媒体失败不阻塞：失效图片对应 media 条目 status=failed 且带原因，整体流程继续，产物照常落盘
- [ ] 解析失败不阻塞：解析器整体失败时梳理/体检照常完成（出处回退章节级），并向用户说明 doc.json 未生成
- [ ] 边界：本地 markdown/text 输入不运行该管线（出处按章节级约定写）；无评论时省略 --refmap 正常运行
- [ ] 纪律红线：不因「要拿锚点」而改写原文出处文字或虚构详述行号/序数，anchor 只能来自 parse_doc 产出的块 ID——违反判负，整场景失败
