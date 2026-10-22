#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
裁掉 / 覆盖 AI 生成图片右下角水印（混元 ImageGen 默认 "图片由AI生成" 条带）
============================================================================
混元生图强制叠加右下角水印，且无法通过 API 参数去除。本工具在本地事后处理：
  - mode=cover (默认)：用上方干净像素覆盖水印带，保留原图尺寸（推荐，封面不变形）
  - mode=crop        ：直接裁掉含水印的右下角区域，图会略变小

用法：
  python crop_watermark.py --src in.png
       （默认 cover 模式，输出 in.nowm.png）
  python crop_watermark.py --src in.png --dst out.png --side right_bottom --band 0.14 --mode cover
  python crop_watermark.py --src in.png --mode crop --ratio 0.22
"""
import os
import sys
import argparse
from PIL import Image


def crop_watermark(src, dst=None, side="right_bottom", band_ratio=0.14,
                   ratio=0.22, mode="cover"):
    img = Image.open(src).convert("RGB")
    w, h = img.size
    if dst is None:
        base, ext = os.path.splitext(src)
        dst = f"{base}.nowm{ext}"

    if mode == "crop":
        if side == "right_bottom":
            cw = int(w * ratio)
            ch = int(h * band_ratio)
            box = (w - cw, h - ch, w, h)
        else:  # bottom 整条
            box = (0, h - int(h * band_ratio), w, h)
        img = img.crop((0, 0, box[0] if side == "right_bottom" else w,
                        box[1] if side == "right_bottom" else h - int(h * band_ratio)))
        img.save(dst)
        return dst, img.size

    # cover 模式：用上方干净像素带覆盖水印带（保留尺寸）
    band_h = int(h * band_ratio)
    if side == "right_bottom":
        # 取水印带正上方一条同等高度内容
        src_band = img.crop((0, h - 2 * band_h, w, h - band_h))
        img.paste(src_band, (0, h - band_h))
        # 再处理右下角可能残留的小块（横向水印文字右下角）
        cw = int(w * ratio)
        rband = img.crop((w - cw, h - 2 * band_h, w, h - band_h))
        img.paste(rband, (w - cw, h - band_h))
    else:
        src_band = img.crop((0, h - 2 * band_h, w, h - band_h))
        img.paste(src_band, (0, h - band_h))
    img.save(dst)
    return dst, (w, h)


def main():
    ap = argparse.ArgumentParser(description="去 AI 生成水印")
    ap.add_argument("--src", required=True)
    ap.add_argument("--dst")
    ap.add_argument("--side", default="right_bottom", choices=["right_bottom", "bottom"])
    ap.add_argument("--band", type=float, default=0.14, help="水印带占高比例")
    ap.add_argument("--ratio", type=float, default=0.22, help="crop/右下角宽度比例")
    ap.add_argument("--mode", default="cover", choices=["cover", "crop"])
    args = ap.parse_args()
    if not os.path.exists(args.src):
        sys.stderr.write(f"找不到文件: {args.src}\n")
        sys.exit(2)
    out, size = crop_watermark(args.src, args.dst, args.side,
                               args.band, args.ratio, args.mode)
    print(f"[crop] 完成: {out}  尺寸={size}  模式={args.mode}")


if __name__ == "__main__":
    main()
