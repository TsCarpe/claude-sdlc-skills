"""任务清单模板。复制为 tasks_local.py 后填写真实 test 环境 URL 与预期断言；tasks_local.py 不进 git。

任务 = goal（操作段，自然语言）+ verify（断言段，独立校验终态，不信任 jev 的 DONE）。
阶段 B 正式判定需 ≥10 个任务，按 README 的控件/场景矩阵补齐（导航/文本/下拉/日期/列表/提交反馈）。
"""

TASKS = [
    {
        # 冒烟任务：公网零敏感页面，验证脚本链路本身（官方 Wikipedia 示例改编）
        "id": "smoke-wikipedia",
        "url": "https://en.wikipedia.org/wiki/Main_Page",
        "goals": "Find and open the Wikipedia article about Gödel's incompleteness theorems.",
        "tags": ["smoke", "navigation"],
        "verify": lambda page: {
            "passed": "Gödel" in page["url"] and "incompleteness" in page["url"].lower(),
            "checks": {"url": page["url"]},
        },
    },
    {
        # 模板：中性虚构业务（订单中后台）。复制后替换 URL 为真实 test 环境页面，
        # 并把 verify 改成对真实页面终态的断言（label→value / 文本 / 行数）。
        "id": "template-order-filter",
        "url": "https://order-admin.example.test/orders",
        "goals": (
            "打开订单列表，将状态筛选为「已发货」，"
            "确认列表中仅显示已发货订单后停止。"
        ),
        "tags": ["list", "select-component"],
        "verify": lambda page: {
            "passed": False,  # 占位：填写真实页面后改为具体断言
            "checks": {"placeholder": "TODO: 断言筛选值与列表行，参考 examples/flights.py 的 verify"},
        },
    },
]
