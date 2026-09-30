#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""对抗 prompt 共享核心段一致性比对（sdlc-gate ↔ sdlc-doubt）。

两个 skill 的对抗 prompt 模板拆为「共享核心段」+「消费方输出段」两节：
- 共享核心段（英文 12 行）两侧逐字节同步——本脚本提取两侧
  <!-- adversarial-core-start/end --> 标记之间的 fenced 内容比对，漂移即 exit 1。
  这是把"同源声明"（有声明、无机制）升级为机检护栏：任何一侧单独改动会在这里红灯。
- 输出段按消费方有意分化（gate 需结构化字段 / doubt 行级证据），标记之外不比对。

用法：python3 scripts/check_adversarial_core.py   # exit 0 = 一致
"""
import sys
from pathlib import Path

START = '<!-- adversarial-core-start'
END = '<!-- adversarial-core-end'


def extract(path: Path) -> str:
    lines = path.read_text(encoding='utf-8').split('\n')
    try:
        a = next(i for i, l in enumerate(lines) if l.startswith(START))
        b = next(i for i, l in enumerate(lines) if l.startswith(END) and i > a)
    except StopIteration:
        sys.exit(f'FAIL: {path} 缺少 adversarial-core 标记（模板结构被破坏？）')
    seg = lines[a + 1:b]
    seg = [l for l in seg if l.strip() != '```']  # 只比内容，忽略围栏
    return '\n'.join(seg).strip('\n')


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    gate = extract(root / 'skills/sdlc-gate/SKILL.md')
    doubt = extract(root / 'skills/sdlc-doubt/SKILL.md')
    if gate != doubt:
        sys.exit(
            'FAIL: sdlc-gate 与 sdlc-doubt 的对抗 prompt 共享核心段不一致。\n'
            '两侧标记 <!-- adversarial-core-start/end --> 之间的内容必须逐字节同步\n'
            '（只有标记之外的输出段允许按消费方分化）。\n'
            f'gate 侧 {len(gate)} 字符 / doubt 侧 {len(doubt)} 字符'
        )
    print(f'OK: 对抗 prompt 共享核心段一致（{len(gate)} 字符）')


if __name__ == '__main__':
    main()
