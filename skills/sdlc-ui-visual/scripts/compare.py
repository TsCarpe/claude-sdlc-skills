#!/usr/bin/env python3
"""sdlc-ui-visual 像素比对三件套（纯 PIL，无 numpy 依赖）。

输入实测截图与设计基准图，一次产出：
  overlay-50.png        50% 叠加图（基准贴到实测图锚点位置后混合）
  diff.png              差异图（×DIFF_GAIN 增强，便于人眼观察）
  crop-compare.png      --box 指定的元素区域：基准在上 / 实测在下，放大 --zoom 倍
  stats.txt / stdout    mean diff、>30 差异像素占比、热区网格（0-9 级，附格中心
                        实测图坐标，供 elementFromPoint 映射）、暗像素计数

坐标系约定：
  - 基准图先等比缩放（--design-scale，pngScale=2 下载的默认 0.5；或 --design-width 直达宽度）
  - 锚点模式（给 --ox --oy）：基准 (0,0) 对齐实测图 (ox, oy)，公共比对区 = 实测图上
    该偏移处、与基准等大的矩形。--box 的 x y w h 在【基准坐标系】（= 期望值清单坐标系）里取
  - 全图模式（不给锚点）：基准缩放后尺寸必须与实测图一致，否则 exit 2（提示先核对
    视口 / frame 尺寸 / 设备像素比，禁止拉伸对齐）

暗像素计数：--box 区域内亮度 < --dark-threshold 的像素数，基准与实测分别统计——
两数相对比例是「图标视觉等价性」证据（数值同 10×10 但墨迹 30% = 不等价）。
命中过少（两侧都 <10）视为不可判定，输出 WARNING，禁止据此下「一致」结论。

退出码：0 正常完成；2 参数 / 尺寸错误。比对存在差异不算错误（判定交给模型结合视觉做）。

用法示例：
  python3 compare.py --actual shot.png --design base.png --outdir r1/                  # 全图
  python3 compare.py --actual shot.png --design base.png --ox 220 --oy 188 --outdir r1/
  python3 compare.py --actual shot.png --design base.png --ox 220 --oy 188 \\
      --box 540 20 20 20 --zoom 4 --outdir r1/                                        # 小元素判读
  python3 compare.py --self-test
"""
import argparse
import os
import sys
import tempfile

try:
    from PIL import Image, ImageChops, ImageStat
except ImportError:
    sys.stderr.write("缺少 Pillow：pip3 install Pillow 后重试\n")
    sys.exit(2)

DIFF_GAIN = 6          # diff.png 增强倍数
LANCZOS = Image.LANCZOS if hasattr(Image, "LANCZOS") else Image.Resampling.LANCZOS


def to_rgb(img):
    """RGBA/P 统一转 RGB（alpha 贴白底，避免透明区变黑污染 diff）。"""
    if img.mode != "RGBA":
        return img.convert("RGB")
    bg = Image.new("RGB", img.size, (255, 255, 255))
    bg.paste(img, mask=img.split()[3])
    return bg


def load_scaled(path, scale, width):
    img = to_rgb(Image.open(path))
    if width:
        factor = width / img.width
    elif scale:
        factor = scale
    else:
        factor = 0.5  # pngScale=2 下载的惯例默认值
    if factor != 1:
        img = img.resize((round(img.width * factor), round(img.height * factor)), LANCZOS)
    return img


def heatmap(gray, cols, rows, offset_x, offset_y, out):
    """0-9 级热区矩阵；每格附中心点实测图坐标。返回矩阵文本。"""
    w, h = gray.size
    lines = []
    for r in range(rows):
        row = []
        for c in range(cols):
            box = (c * w // cols, r * h // rows, (c + 1) * w // cols, (r + 1) * h // rows)
            mean = ImageStat.Stat(gray.crop(box)).mean[0]
            row.append(min(9, int(mean // 12)))  # 12→1 级起报；108+ 封顶 9（案例校准值）
        lines.append(" ".join(str(v) for v in row))
    out.append("heatmap (0=一致 9=差异大; 格值为行×列):")
    for i, line in enumerate(lines):
        out.append("  " + line)
    # 中心坐标单独一行，便于 elementFromPoint 映射：格 (r,c) 中心 = 基准格中心 + 锚点偏移
    out.append("cell centers (actual coords): " + "; ".join(
        f"(r{r}c{c})@{offset_x + (c + 0.5) * w // cols:.0f},{offset_y + (r + 0.5) * h // rows:.0f}"
        for r in range(min(rows, 2)) for c in range(cols)))
    return lines


def dark_count(img, box, threshold):
    """亮度 < threshold 的像素数（histogram 实现，无弃用 API、比逐像素快）。"""
    return sum(img.crop(box).convert("L").histogram()[:threshold])


def run(args, out, outdir=None):
    actual = to_rgb(Image.open(args.actual))
    design = load_scaled(args.design, args.design_scale, args.design_width)
    dw, dh = design.size

    if args.ox is not None and args.oy is not None:
        ox, oy = args.ox, args.oy
        anchored = True
    else:
        ox = oy = 0
        anchored = False
        if design.size != actual.size:
            out.append(f"ERROR: 全图模式要求基准缩放后 {design.size} == 实测 {actual.size}；"
                       f"先核对视口/frame 尺寸/DPR 或用 --design-width/--ox --oy 锚定，禁止拉伸")
            return 2

    # 公共比对区（实测图坐标系）
    if ox + dw > actual.width or oy + dh > actual.height:
        out.append(f"WARNING: 比对区 ({ox},{oy})+{dw}x{dh} 超出实测图 {actual.size}，"
                   "超出部分按可用区域截断，结果偏乐观")
    cw = min(dw, actual.width - ox)
    ch = min(dh, actual.height - oy)
    a = actual.crop((ox, oy, ox + cw, oy + ch))
    d = design.crop((0, 0, cw, ch))

    # ① overlay：锚点模式在整张实测图上贴基准再混合（保留应用壳上下文）
    if anchored:
        layer = Image.new("RGBA", actual.size, (0, 0, 0, 0))
        layer.paste(d.convert("RGBA"), (ox, oy))
        overlay = Image.blend(actual.convert("RGBA"), layer, 0.5).convert("RGB")
    else:
        overlay = Image.blend(a.convert("RGBA"), d.convert("RGBA"), 0.5).convert("RGB")
    overlay.save(os.path.join(outdir, "overlay-50.png"))

    # ② diff（×DIFF_GAIN 增强）
    diff = ImageChops.difference(a, d)
    diff.point(lambda p: min(255, p * DIFF_GAIN)).save(os.path.join(outdir, "diff.png"))
    gray = diff.convert("L")
    mean = ImageStat.Stat(gray).mean[0]
    hist = gray.histogram()
    total = gray.width * gray.height
    gt30 = sum(hist[31:]) / total * 100

    out.append(f"mode: {'anchored' if anchored else 'full'} ({cw}x{ch} @ {ox},{oy})")
    out.append(f"mean_diff: {mean:.2f}")
    out.append(f"gt30_pct: {gt30:.2f}")
    out.append(f"design_scaled: {design.size} (from {Image.open(args.design).size})")

    # ③ 热区网格
    hm = heatmap(gray, args.grid_cols, args.grid_rows, ox, oy, out)

    # ④ --box：小元素裁剪拼图 + 暗像素计数
    if args.box:
        bx, by, bw, bh = args.box
        if bx + bw > cw or by + bh > ch:
            out.append(f"ERROR: --box ({bx},{by},{bw},{bh}) 超出比对区 {cw}x{ch}")
            return 2
        d_cut = d.crop((bx, by, bx + bw, by + bh))
        a_cut = a.crop((bx, by, bx + bw, by + bh))
        z = max(1, args.zoom)
        d_big = d_cut.resize((bw * z, bh * z), Image.NEAREST)
        a_big = a_cut.resize((bw * z, bh * z), Image.NEAREST)
        sep = Image.new("RGB", (bw * z, 4), (255, 0, 0))
        combo = Image.new("RGB", (bw * z, bh * z * 2 + 4))
        combo.paste(d_big, (0, 0))
        combo.paste(sep, (0, bh * z))
        combo.paste(a_big, (0, bh * z + 4))
        combo.save(os.path.join(outdir, "crop-compare.png"))

        dn = dark_count(d_cut, (0, 0, bw, bh), args.dark_threshold)
        an = dark_count(a_cut, (0, 0, bw, bh), args.dark_threshold)
        out.append(f"dark_pixels_design: {dn}")
        out.append(f"dark_pixels_actual: {an}")
        if dn:
            out.append(f"dark_ratio_actual_vs_design: {an / dn:.2f}")
        if dn < 10 and an < 10:
            out.append("WARNING: 两侧暗像素均 <10，元素过细/过浅，不可判定——"
                       "放大拼图视觉判读，禁止据此下『一致』结论")

    out.append(f"artifacts: {sorted(os.listdir(outdir))}")
    return 0


def self_test():
    """合成图自测：常量差异块 + 小元素暗块，断言 overlay/diff/热区/暗像素/尺寸守卫。"""
    with tempfile.TemporaryDirectory() as td:
        d = Image.new("RGB", (200, 100), (240, 240, 240))
        a = Image.new("RGB", (200, 100), (240, 240, 240))
        for x in range(100, 120):          # 差异竖条 → 热区右列应高、左列应低
            for y in range(100):
                a.putpixel((x, y), (180, 180, 180))
        for x in range(150, 156):          # 深色小方块：基准深墨迹 vs 实测浅墨迹
            for y in range(10, 16):
                d.putpixel((x, y), (60, 60, 60))
                a.putpixel((x, y), (200, 200, 200))
        dp, ap = os.path.join(td, "d.png"), os.path.join(td, "a.png")
        d.save(dp)
        a.save(ap)

        class Args:
            actual, design = ap, dp
            design_scale, design_width, ox, oy = 1, None, None, None
            box, zoom, dark_threshold = (150, 10, 6, 6), 4, 180
            grid_cols, grid_rows = 2, 2
        lines = []
        rc = run(Args(), lines, td)
        s = "\n".join(lines)
        assert rc == 0, s
        assert 0 < float(s.split("mean_diff: ")[1].split()[0]) < 60, s
        assert os.path.exists(os.path.join(td, "overlay-50.png"))
        assert os.path.exists(os.path.join(td, "diff.png"))
        assert os.path.exists(os.path.join(td, "crop-compare.png"))
        hm = [l.strip() for l in s.splitlines() if l.strip() and l.strip()[0].isdigit()]
        lv = [int(v) for line in hm for v in line.split()]  # 2×2 展平：下标 1/3 为右列
        assert lv[1] > lv[0] and lv[3] > lv[2], s
        dn = int(s.split("dark_pixels_design: ")[1].split()[0])
        an = int(s.split("dark_pixels_actual: ")[1].split()[0])
        assert dn == 36 and an == 0, f"暗像素计数错误: {dn}/{an}"  # 6×6 全深 vs 全浅

        # 尺寸守卫：全图模式尺寸不符必须 exit 2
        class Bad(Args):
            design_scale, design_width = None, 199
        assert run(Bad(), [], td) == 2
        print("self-test: OK")


def main():
    p = argparse.ArgumentParser(description=__doc__.split("\n")[1],
                                 formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog="详细坐标系约定见 docstring（--help 全文）")
    p.add_argument("--actual", help="实测截图（RGB/RGBA PNG）")
    p.add_argument("--design", help="设计基准图（建议 pngScale=2 下载）")
    p.add_argument("--design-scale", type=float, default=None,
                   help="基准等比缩放系数，默认 0.5（pngScale=2 惯例）")
    p.add_argument("--design-width", type=int, default=None,
                   help="基准缩放后目标宽度（px），优先生效；等比缩放")
    p.add_argument("--ox", type=int, default=None, help="锚点 x：基准(0,0)在实测图中的 x")
    p.add_argument("--oy", type=int, default=None, help="锚点 y：基准(0,0)在实测图中的 y")
    p.add_argument("--box", type=int, nargs=4, metavar=("X", "Y", "W", "H"),
                   help="小元素区域（基准坐标系），产出放大拼图 + 暗像素计数")
    p.add_argument("--zoom", type=int, default=3, help="--box 拼图放大倍数，默认 3（≥3 保小元素可判读）")
    p.add_argument("--dark-threshold", type=int, default=180,
                   help="暗像素亮度阈值（<此值计为墨迹），默认 180")
    p.add_argument("--grid-cols", type=int, default=5, help="热区网格列数，默认 5")
    p.add_argument("--grid-rows", type=int, default=4, help="热区网格行数，默认 4")
    p.add_argument("--outdir", default=".", help="产物输出目录（自动创建）")
    p.add_argument("--self-test", action="store_true", help="合成图自测后退出")
    args = p.parse_args()

    if args.self_test:
        self_test()
        return
    if not (args.actual and args.design):
        p.error("--actual 与 --design 必填（或用 --self-test）")
    if (args.ox is None) != (args.oy is None):
        p.error("--ox 与 --oy 必须成对出现")
    os.makedirs(args.outdir, exist_ok=True)

    out = []
    rc = run(args, out, args.outdir)
    text = "\n".join(out)
    print(text)
    with open(os.path.join(args.outdir, "stats.txt"), "w") as f:
        f.write(text + "\n")
    sys.exit(rc)


if __name__ == "__main__":
    main()
