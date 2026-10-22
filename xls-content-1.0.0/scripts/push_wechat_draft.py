#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微信公众号草稿 / 图片消息(小绿书) 推送工具
=========================================
本地读取 .env 凭证，调用微信官方接口：
  - 获取 / 缓存 access_token
  - 上传图文 / 图片消息所需图片（返回 media_id + 微信图床 url）
  - 建图文草稿 (draft/add)        → 公众号后台草稿箱
  - 建图片消息草稿 (news_image_message/add) → 小绿书(图文/图片消息)草稿箱，支持封面裁剪

用法：
  python push_wechat_draft.py --test
      最小验证：生成占位封面图 → 上传 → 建一条极简草稿（后台可见即成功）

  python push_wechat_draft.py --mode draft --title "标题" --digest "摘要" --content article.html --image cover.jpg
  python push_wechat_draft.py --mode image_message --title "..." --content imgmsg.html --image cover.jpg --crop '{"235_1":[0,0,1,0.5]}'

注意：
  - 微信正文 content 必须是 HTML，且图片必须用「微信图床 url」(上传后返回)，
    外链图会被过滤。本工具上传 --image 后会在 stdout 打印 media_id 与 url，供拼接。
  - 导出凭证请放 .env，切勿硬编码进脚本 / 提交到仓库。
"""
import os
import sys
import json
import time
import base64
import argparse
import mimetypes
import urllib.request
import urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(HERE, ".env")
TOKEN_CACHE = os.path.join(HERE, ".token_cache")
BASE = "https://api.weixin.qq.com/cgi-bin/"


def load_env():
    cfg = {}
    if os.path.exists(ENV_PATH):
        with open(ENV_PATH, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    k, v = line.split("=", 1)
                    cfg[k.strip()] = v.strip()
    return cfg


CFG = load_env()
APPID = CFG.get("WECHAT_APPID", "")
APPSECRET = CFG.get("WECHAT_APPSECRET", "")
AUTHOR = CFG.get("AUTHOR_NAME", "")
if not APPID or not APPSECRET:
    sys.stderr.write("[push] 错误：.env 缺少 WECHAT_APPID / WECHAT_APPSECRET\n")
    sys.exit(2)


def log(*a):
    print("[push]", *a, file=sys.stderr)


# ---------- token ----------
def get_token(force=False):
    if not force and os.path.exists(TOKEN_CACHE):
        try:
            data = json.load(open(TOKEN_CACHE, encoding="utf-8"))
            if time.time() < data.get("expire_at", 0) - 120:
                return data["access_token"]
        except Exception:
            pass
    url = f"{BASE}token?grant_type=client_credential&appid={APPID}&secret={APPSECRET}"
    try:
        resp = urllib.request.urlopen(urllib.request.Request(url), timeout=20).read()
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"获取token失败 HTTP {e.code}: {e.read().decode('utf-8','ignore')}")
    d = json.loads(resp)
    if "access_token" not in d:
        raise RuntimeError(f"获取token失败: {d}")
    json.dump({"access_token": d["access_token"],
               "expire_at": time.time() + d.get("expires_in", 7200)},
              open(TOKEN_CACHE, "w", encoding="utf-8"))
    return d["access_token"]


# ---------- 通用 POST(JSON) ----------
def api_post(path, obj, token=None, _retried=False):
    token = token or get_token()
    url = f"{BASE}{path}?access_token={token}"
    data = json.dumps(obj, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=data,
                                 headers={"Content-Type": "application/json"})
    try:
        resp = urllib.request.urlopen(req, timeout=30).read()
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"API {path} HTTP {e.code}: {e.read().decode('utf-8','ignore')}")
    d = json.loads(resp)
    err = d.get("errcode", 0)
    if err != 0:
        # token 失效类错误，强制刷新重试一次
        if not _retried and err in (40014, 42001, 41001):
            return api_post(path, obj, token=get_token(force=True), _retried=True)
        raise RuntimeError(f"API {path} errcode={err} errmsg={d.get('errmsg')}")
    return d


# ---------- 上传图片 ----------
def upload_image(path, token=None):
    token = token or get_token()
    url = f"{BASE}material/add_material?access_token={token}&type=image"
    boundary = "----wbpushboundary"
    fname = os.path.basename(path)
    ctype = mimetypes.guess_type(fname)[0] or "image/jpeg"
    with open(path, "rb") as f:
        raw = f.read()
    parts = [
        f"--{boundary}",
        f'Content-Disposition: form-data; name="media"; filename="{fname}"',
        f"Content-Type: {ctype}",
        "",
    ]
    body = ("\r\n".join(parts)).encode("utf-8") + b"\r\n" + raw + \
           f"\r\n--{boundary}--\r\n".encode("utf-8")
    req = urllib.request.Request(url, data=body,
                                 headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
    try:
        resp = urllib.request.urlopen(req, timeout=30).read()
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"上传图片失败 HTTP {e.code}: {e.read().decode('utf-8','ignore')}")
    d = json.loads(resp)
    if "media_id" not in d:
        raise RuntimeError(f"上传图片失败: {d}")
    return d["media_id"], d.get("url", "")


# ---------- 建图文草稿 ----------
def add_draft(title, content_html, thumb_media_id, digest="", author="", token=None):
    article = {
        "title": title,
        "author": author or AUTHOR,
        "digest": digest,
        "content": content_html,
        "thumb_media_id": thumb_media_id,
        "need_open_comment": 0,
        "only_fans_can_comment": 0,
        "show_cover_pic": 1,
    }
    return api_post("draft/add", {"articles": [article]}, token)


# ---------- 建图片消息草稿(小绿书 / 微信 newspic) ----------
# 注意：图片消息与图文消息同走 draft/add 端点，靠 article_type="newspic" 区分。
# 图片通过 image_info.image_list 传入（首张即封面），封面裁剪用 cover_info.crop_percent_list。
def add_image_message(title, content_html, image_media_ids, digest="", author="",
                      crop_ratio="2.35_1", token=None):
    if not isinstance(image_media_ids, (list, tuple)):
        image_media_ids = [image_media_ids]
    image_list = [{"image_media_id": m} for m in image_media_ids]
    cover_info = {}
    if crop_ratio:
        cover_info["crop_percent_list"] = [
            {"ratio": crop_ratio, "x1": "0", "y1": "0", "x2": "1", "y2": "1"}
        ]
    article = {
        "article_type": "newspic",
        "title": title,
        "content": content_html,
        "need_open_comment": 0,
        "only_fans_can_comment": 0,
        "image_info": {"image_list": image_list},
        "cover_info": cover_info,
    }
    if digest:
        article["digest"] = digest
    if author:
        article["author"] = author or AUTHOR
    return api_post("draft/add", {"articles": [article]}, token)


# ---------- 测试占位图 ----------
def gen_placeholder(path):
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        raise RuntimeError("test 模式需要 Pillow：pip install Pillow")
    img = Image.new("RGB", (900, 383), (26, 35, 126))
    d = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("msyh.ttc", 36)
    except Exception:
        font = ImageFont.load_default()
    d.text((40, 160), "草稿推送验证图 (可删除)", fill=(255, 255, 255), font=font)
    d.text((40, 220), time.strftime("%Y-%m-%d %H:%M"), fill=(200, 210, 255), font=font)
    img.save(path)


# ---------- CLI ----------
def main():
    ap = argparse.ArgumentParser(description="微信公众号草稿推送")
    ap.add_argument("--test", action="store_true", help="最小验证：占位图+建草稿")
    ap.add_argument("--mode", choices=["draft", "image_message"], default="draft")
    ap.add_argument("--title")
    ap.add_argument("--digest")
    ap.add_argument("--author")
    ap.add_argument("--content", help="HTML 内容(文件或字符串)")
    ap.add_argument("--image", help="封面/配图本地路径(会上传)")
    ap.add_argument("--crop", help='封面裁剪 JSON, e.g. {"235_1":[0,0,1,0.5]}')
    args = ap.parse_args()

    if args.test:
        ph = os.path.join(HERE, "_test_cover.png")
        gen_placeholder(ph)
        log("生成占位图:", ph)
        mid, url = upload_image(ph)
        log("上传成功 media_id=", mid)
        html = f'<p>这是一条草稿推送最小验证，生成于 {time.strftime("%Y-%m-%d %H:%M")}。</p>' \
               f'<p><img src="{url}"></p>'
        r = add_draft("【测试】草稿推送验证", html, mid,
                      digest="可删除的测试草稿", author=AUTHOR)
        log("建草稿成功 media_id(草稿)=", r.get("media_id"))
        print(json.dumps({"ok": True, "draft_media_id": r.get("media_id"),
                          "cover_media_id": mid, "cover_url": url}, ensure_ascii=False))
        return

    # 正式模式
    if not args.title or not args.content:
        sys.stderr.write("[push] 正式模式需要 --title 与 --content\n")
        sys.exit(2)
    if args.content and os.path.exists(args.content):
        content_html = open(args.content, encoding="utf-8").read()
    else:
        content_html = args.content
    thumb_mid = None
    cover_url = ""
    if args.image:
        thumb_mid, cover_url = upload_image(args.image)
        log("封面已上传 media_id=", thumb_mid)
    if not thumb_mid:
        sys.stderr.write("[push] 错误：缺少封面图(--image)，草稿必须带 thumb_media_id\n")
        sys.exit(2)
    crop = json.loads(args.crop) if args.crop else None
    if args.mode == "image_message":
        r = add_image_message(args.title, content_html, thumb_mid,
                              digest=args.digest or "", author=args.author or "",
                              crop=crop)
        log("图片消息草稿已建 media_id=", r.get("media_id"))
    else:
        r = add_draft(args.title, content_html, thumb_mid,
                      digest=args.digest or "", author=args.author or "")
        log("图文草稿已建 media_id=", r.get("media_id"))
    print(json.dumps({"ok": True, "mode": args.mode,
                      "draft_media_id": r.get("media_id"),
                      "cover_media_id": thumb_mid, "cover_url": cover_url},
                     ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as e:
        sys.stderr.write(f"[push] 失败：{e}\n")
        sys.exit(1)
