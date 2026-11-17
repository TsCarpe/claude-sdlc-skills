#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""flow-viz 镜像段一致性比对（skills 仓协议文档 ↔ platform-server 速查卡）。

flow-viz 图协议的紧凑规范段同时存在于两处：
- claude-sdlc-skills/references/flow-viz-protocol.md 的 fv-mirror 标记段（单一权威来源）
- sdlc-platform-server/src/platform_sdlc/agent/prompts.py 速查卡内的镜像引用段

两处必须逐字节同步——速查卡是线上流水线 agent 的必读权威，只改协议文档不改速查卡
= 纪律到不了 agent。本脚本提取两侧 <!-- fv-mirror-start/end --> 标记段比对，
漂移即 exit 1（同 check_adversarial_core.py 的护栏模式）。

用法：python3 scripts/check_digest_mirror.py [server 仓根路径]   # 缺省 ../sdlc-platform-server
"""
import sys
from pathlib import Path

START = '<!-- fv-mirror-start'
END = '<!-- fv-mirror-end'


def extract_md(path: Path) -> str:
    lines = path.read_text(encoding='utf-8').split('\n')
    try:
        a = next(i for i, l in enumerate(lines) if l.startswith(START))
        b = next(i for i, l in enumerate(lines) if l.startswith(END) and i > a)
    except StopIteration:
        sys.exit(f'FAIL: {path} 缺少 fv-mirror 标记（模板结构被破坏？）')
    return '\n'.join(lines[a + 1:b]).strip('\n')


def extract_py(path: Path) -> str:
    """从 prompts.py 提取镜像段：字符串字面量里的标记行与正文行混排，还原为纯文本。

    速查卡是相邻字符串字面量拼接：按行扫描源码，取标记行之间的源码行，剥掉
    Python 字符串外壳（前导空白 + 引号 + 尾部 \n 拼接符），再反转义 \" ——
    与 extract_md 的产物在「渲染后的文本」层逐字节比对。
    """
    lines = path.read_text(encoding='utf-8').split('\n')
    try:
        a = next(i for i, l in enumerate(lines) if START in l)
        b = next(i for i, l in enumerate(lines) if END in l and i > a)
    except StopIteration:
        sys.exit(f'FAIL: {path} 缺少 fv-mirror 标记（速查卡结构被破坏？）')
    out = []
    for raw in lines[a + 1:b]:
        l = raw.strip()
        if not l.startswith('"'):
            sys.exit(f'FAIL: {path} 镜像段内存在非字符串字面量行：{raw[:60]}')
        # 剥 "..." 外壳与行尾 \n 转义，反转义内部双引号
        body = l[1:]
        q = body.rfind('"')
        body = body[:q]
        body = body.replace('\\n', '\n').replace('\\"', '"')
        out.append(body)
    return ''.join(out).strip('\n')


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    server = Path(sys.argv[1]) if len(sys.argv) > 1 else root.parent / 'sdlc-platform-server'
    md = extract_md(root / 'references/flow-viz-protocol.md')
    py = extract_py(server / 'src/platform_sdlc/agent/prompts.py')
    if md != py:
        import difflib
        diff = '\n'.join(difflib.unified_diff(md.split('\n'), py.split('\n'),
                                              fromfile='flow-viz-protocol.md', tofile='prompts.py', lineterm=''))
        sys.exit('FAIL: flow-viz 协议镜像段不一致（协议文档 ↔ server 速查卡）。\n'
                 '两侧 <!-- fv-mirror-start/end --> 标记段必须逐字节同步：\n'
                 '- 改协议：references/flow-viz-protocol.md 为权威来源，同步改 prompts.py 速查卡镜像段\n'
                 '- 改速查卡：反向同步回协议文档\n' + diff)
    print(f'MIRROR OK: flow-viz 镜像段一致（{len(md)} 字符）')


if __name__ == '__main__':
    main()
