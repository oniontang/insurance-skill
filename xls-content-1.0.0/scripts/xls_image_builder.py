# -*- coding: utf-8 -*-
"""
小绿书图片引擎 v1  ——  「情绪封面 × 手绘指引」双载体
================================================================
核心理念（对齐 xls-content skill 定位）：
  · 封面图 = 情绪价值感性图（特别吃图，决定 80% 点击）—— 6 大范式
  · 后端图 = 手绘风专业指引图（留住人+让人收藏）—— 4 大范式
引擎：HTML + CSS + Playwright(Chromium) 截图，device_scale_factor=2 高清
用法：
  python xls_image_builder.py            # 渲染全部内置样例
  （生产时：Stage4 按范式 import 对应函数，传入选题文案再 render）

范式函数命名：
  封面：cover_confession / cover_number / cover_question /
        cover_contrast / cover_checklist / cover_story
  手绘：hand_steps / hand_vs / hand_checklist / hand_map
每个函数都接收一个 data(dict)，返回 HTML 字符串，方便生产时喂真实文案。
"""
import sys, os, base64

BASE = r"D:\workbuddy\skills-data\wechat-publish"
if os.path.isdir(BASE):
    sys.path.insert(0, BASE)

ASSET = r"D:\workbuddy\skills-data\xls-content\assets\样例封面"
os.makedirs(ASSET, exist_ok=True)

# ---------- 配色主板（对齐 cover-design-system.md 第五节）----------
INK     = "#1f2a44"   # 墨蓝（主字/深底，专业信任）
GOLD    = "#c8a45c"   # 暖金（关键词/装饰线，高级感）
CREAM   = "#f7f3ec"   # 奶白（浅色封面底）
GREEN   = "#2f5d50"   # 墨绿（数字/理性/清单）
CORAL   = "#d8674f"   # 暖珊瑚（情绪强调/警示，克制用）
# ---------- 手绘配色（对齐 handdrawn-guide-style.md）----------
PAPER   = "#f6f0e2"   # 纸张底
MARK_Y  = "rgba(242,198,92,0.60)"   # 马克笔黄
MARK_G  = "rgba(90,138,111,0.45)"   # 马克笔绿
RED_PEN = "#d8674f"   # 红笔

FONT = '"Microsoft YaHei","PingFang SC","Hiragino Sans GB",sans-serif'
# 手写感：系统无手写体时用圆体+微旋转模拟
HAND_FONT = '"STKaiti","KaiTi","Kaiti SC","Microsoft YaHei",sans-serif'

COMMON = """
* { margin:0; padding:0; box-sizing:border-box; }
body { font-family:%s; -webkit-font-smoothing:antialiased; }
""" % FONT

# 尺寸常量
W_COVER, H_COVER = 1080, 1440      # 主封面 3:4
W_HAND,  H_HAND  = 1080, 1350      # 手绘正文图 4:5(近3:4)


def data_uri(path):
    """图片转 base64 data URI，避免 file:// 加载失败"""
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    ext = os.path.splitext(path)[1].lower().strip(".")
    mime = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg"}.get(ext, "image/png")
    return f"data:{mime};base64,{b64}"


def _bg(data):
    """封面背景：优先真实照片(photo=路径)；否则用情绪渐变兜底(sample)"""
    photo = data.get("photo")
    if photo and os.path.isfile(photo):
        return f"background:url('{data_uri(photo)}') center/cover no-repeat;"
    # 无照片时的高级情绪渐变（样例/兜底用）
    return data.get("grad", f"background:radial-gradient(120% 90% at 30% 20%, #33405f 0%, #171f33 62%, #0d1220 100%);")


# ================================================================
# 封面范式 1 · 戳心自白型（Confession）
#   情绪照片压暗 + 中下部大字白标题 + 底部小字副题 + 一抹金
# ================================================================
def cover_confession(d):
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{COMMON}
.page{{width:{W_COVER}px;height:{H_COVER}px;position:relative;overflow:hidden;{_bg(d)}}}
.scrim{{position:absolute;inset:0;background:linear-gradient(to top,
  rgba(8,11,22,0.94) 0%, rgba(8,11,22,0.72) 40%, rgba(8,11,22,0.22) 72%, rgba(8,11,22,0.35) 100%);}}
.tag{{position:absolute;top:70px;left:72px;border:1px solid rgba(200,164,92,0.85);
  color:#e9d6ad;font-size:26px;letter-spacing:6px;padding:9px 24px;border-radius:30px;}}
.wrap{{position:absolute;left:72px;right:72px;bottom:150px;color:#fff;}}
.title{{font-size:88px;font-weight:800;line-height:1.28;letter-spacing:2px;
  text-shadow:0 4px 24px rgba(0,0,0,0.55);}}
.title .hl{{color:{GOLD};}}
.rule{{width:80px;height:5px;background:{GOLD};margin:34px 0 26px;border-radius:3px;}}
.sub{{font-size:32px;color:#e4e8f2;line-height:1.7;font-weight:400;
  text-shadow:0 2px 10px rgba(0,0,0,0.5);}}
</style></head><body><div class="page"><div class="scrim"></div>
<div class="tag">{d.get('tag','真实故事')}</div>
<div class="wrap"><div class="title">{d['title']}</div>
<div class="rule"></div><div class="sub">{d.get('sub','')}</div></div>
</div></body></html>"""


# ================================================================
# 封面范式 2 · 数字冲击型（Number）
#   奶白底 + 超大数字(占1/2) + 短标题 + 墨绿/深蓝
# ================================================================
def cover_number(d):
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{COMMON}
.page{{width:{W_COVER}px;height:{H_COVER}px;position:relative;overflow:hidden;
  background:linear-gradient(160deg,{CREAM} 0%, #efe8da 100%);}}
.grid{{position:absolute;inset:0;opacity:0.5;
  background:repeating-linear-gradient(0deg,transparent 0 46px,rgba(31,42,68,0.03) 46px 47px);}}
.tag{{position:absolute;top:80px;left:80px;color:{GREEN};font-size:30px;
  font-weight:700;letter-spacing:4px;border-left:6px solid {GOLD};padding-left:20px;}}
.big{{position:absolute;top:300px;left:0;right:0;text-align:center;
  font-size:400px;font-weight:900;color:{GREEN};line-height:0.9;letter-spacing:-8px;}}
.big .unit{{font-size:150px;color:{GOLD};font-weight:800;}}
.title{{position:absolute;left:80px;right:80px;bottom:200px;
  font-size:66px;font-weight:800;color:{INK};line-height:1.35;text-align:center;}}
.title .hl{{color:{CORAL};}}
.sub{{position:absolute;left:80px;right:80px;bottom:130px;text-align:center;
  font-size:30px;color:#6a7290;letter-spacing:2px;}}
</style></head><body><div class="page"><div class="grid"></div>
<div class="tag">{d.get('tag','数据揭示')}</div>
<div class="big">{d['number']}<span class="unit">{d.get('unit','')}</span></div>
<div class="title">{d['title']}</div>
<div class="sub">{d.get('sub','')}</div>
</div></body></html>"""


# ================================================================
# 封面范式 3 · 灵魂拷问型（Question）
#   大留白 + 居中大字问句 + 角落手绘小元素
# ================================================================
def cover_question(d):
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{COMMON}
.page{{width:{W_COVER}px;height:{H_COVER}px;position:relative;overflow:hidden;
  background:linear-gradient(155deg,#eef2f4 0%, #dfe6ea 100%);
  display:flex;align-items:center;justify-content:center;padding:110px;}}
.qmark{{position:absolute;top:90px;right:100px;font-family:Georgia,serif;
  font-size:340px;color:rgba(31,42,68,0.07);line-height:1;}}
.deco{{position:absolute;left:90px;bottom:120px;}}
.q{{position:relative;font-size:78px;font-weight:800;color:{INK};
  text-align:center;line-height:1.5;letter-spacing:1px;max-width:900px;}}
.q .hl{{color:{CORAL};background:linear-gradient(transparent 62%, rgba(216,103,79,0.18) 62%);}}
.foot{{position:absolute;bottom:110px;left:0;right:0;text-align:center;
  font-size:28px;color:{GREEN};letter-spacing:6px;}}
</style></head><body><div class="page">
<div class="qmark">?</div>
<div class="q">{d['title']}</div>
<svg class="deco" width="150" height="90" viewBox="0 0 150 90">
  <path d="M8 70 Q60 10 130 40" fill="none" stroke="{GOLD}" stroke-width="5"
    stroke-linecap="round" stroke-dasharray="2 14"/>
  <path d="M118 26 L134 40 L116 52" fill="none" stroke="{GOLD}" stroke-width="5" stroke-linecap="round"/>
</svg>
<div class="foot">{d.get('foot','· 值得停下来想一想 ·')}</div>
</div></body></html>"""


# ================================================================
# 封面范式 4 · 反差对比型（Contrast）
#   左右分割(冷✗/暖✓) + 中间分割线 + 两组短标签
# ================================================================
def cover_contrast(d):
    L = d["left"]; R = d["right"]
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{COMMON}
.page{{width:{W_COVER}px;height:{H_COVER}px;position:relative;overflow:hidden;display:flex;}}
.side{{flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:70px 44px;}}
.left{{background:linear-gradient(160deg,#4a4f5c,#2c2f38);color:#c9ccd4;}}
.right{{background:linear-gradient(160deg,#2f5d50,#20463c);color:#fff;}}
.mark{{font-size:150px;font-weight:900;line-height:1;margin-bottom:30px;}}
.left .mark{{color:#8a8f9c;}} .right .mark{{color:{GOLD};}}
.lab{{font-size:56px;font-weight:800;line-height:1.35;text-align:center;}}
.desc{{margin-top:26px;font-size:30px;line-height:1.6;text-align:center;opacity:0.92;}}
.divider{{position:absolute;left:50%;top:0;bottom:0;width:0;transform:translateX(-50%);
  border-left:3px dashed rgba(255,255,255,0.55);}}
.vs{{position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);
  width:130px;height:130px;border-radius:50%;background:{INK};color:{GOLD};
  display:flex;align-items:center;justify-content:center;font-size:52px;font-weight:900;
  box-shadow:0 10px 40px rgba(0,0,0,0.4);border:4px solid #fff;}}
.top{{position:absolute;top:60px;left:0;right:0;text-align:center;z-index:5;color:#fff;
  font-size:34px;font-weight:800;letter-spacing:3px;text-shadow:0 2px 10px rgba(0,0,0,0.4);}}
</style></head><body><div class="page">
<div class="top">{d.get('top','')}</div>
<div class="side left"><div class="mark">✗</div><div class="lab">{L['label']}</div><div class="desc">{L.get('desc','')}</div></div>
<div class="side right"><div class="mark">✓</div><div class="lab">{R['label']}</div><div class="desc">{R.get('desc','')}</div></div>
<div class="divider"></div><div class="vs">VS</div>
</div></body></html>"""


# ================================================================
# 封面范式 5 · 清单预告型（Checklist）
#   顶部标题条 + 3要点缩影 + 底部"建议收藏"
# ================================================================
def cover_checklist(d):
    items = d["items"]
    rows = ""
    for i, it in enumerate(items, 1):
        rows += f"""<div class="row"><div class="n">{i:02d}</div>
          <div class="t">{it}</div></div>"""
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{COMMON}
.page{{width:{W_COVER}px;height:{H_COVER}px;position:relative;overflow:hidden;
  background:linear-gradient(165deg,{CREAM} 0%,#eae2d3 100%);padding:80px 72px;}}
.kicker{{font-size:30px;color:{GOLD};letter-spacing:5px;font-weight:700;}}
.head{{margin-top:18px;font-size:82px;font-weight:900;color:{INK};line-height:1.2;}}
.head .hl{{color:{GREEN};}}
.bar{{width:110px;height:8px;background:{GOLD};border-radius:4px;margin:34px 0 56px;}}
.row{{display:flex;align-items:center;gap:32px;background:#fff;border-radius:20px;
  padding:38px 40px;margin-bottom:28px;box-shadow:0 10px 30px rgba(31,42,68,0.08);
  border-left:8px solid {GREEN};}}
.n{{flex:0 0 88px;width:88px;height:88px;border-radius:20px;background:{INK};color:{GOLD};
  font-size:40px;font-weight:900;display:flex;align-items:center;justify-content:center;}}
.t{{font-size:42px;font-weight:700;color:{INK};line-height:1.3;}}
.foot{{position:absolute;left:0;right:0;bottom:70px;text-align:center;
  font-size:34px;color:{CORAL};font-weight:800;letter-spacing:2px;}}
.foot .ic{{margin-right:10px;}}
</style></head><body><div class="page">
<div class="kicker">{d.get('kicker','建议收藏 · 避坑指南')}</div>
<div class="head">{d['title']}</div><div class="bar"></div>
{rows}
<div class="foot"><span class="ic">★</span>{d.get('foot','先别下单，看完这 3 条再说')}</div>
</div></body></html>"""


# ================================================================
# 封面范式 6 · 温情故事型（Story）
#   暖光照片 + 故事感标题(引号) + 小字"真实故事"
# ================================================================
def cover_story(d):
    warm = d.get("grad", "background:radial-gradient(120% 90% at 70% 30%, #6b4e34 0%, #3c2b1c 60%, #241812 100%);")
    d2 = dict(d); 
    if not (d.get("photo") and os.path.isfile(d.get("photo",""))):
        d2["grad"] = warm
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{COMMON}
.page{{width:{W_COVER}px;height:{H_COVER}px;position:relative;overflow:hidden;{_bg(d2)}}}
.scrim{{position:absolute;inset:0;background:linear-gradient(to top,
  rgba(24,14,8,0.90) 0%, rgba(24,14,8,0.55) 42%, rgba(24,14,8,0.15) 75%);}}
.tag{{position:absolute;top:72px;left:72px;color:{GOLD};font-size:28px;
  letter-spacing:5px;font-weight:600;}}
.tag::before{{content:'';display:inline-block;width:40px;height:2px;background:{GOLD};
  vertical-align:middle;margin-right:16px;}}
.wrap{{position:absolute;left:72px;right:72px;bottom:170px;color:#fff;}}
.qm{{font-family:Georgia,serif;font-size:150px;color:rgba(200,164,92,0.55);line-height:0.4;}}
.title{{font-size:80px;font-weight:800;line-height:1.4;letter-spacing:1px;
  text-shadow:0 3px 18px rgba(0,0,0,0.5);}}
.title .hl{{color:{GOLD};}}
.sub{{margin-top:30px;font-size:30px;color:#ece3d6;line-height:1.7;
  text-shadow:0 2px 10px rgba(0,0,0,0.5);}}
</style></head><body><div class="page"><div class="scrim"></div>
<div class="tag">{d.get('tag','真实故事')}</div>
<div class="wrap"><div class="qm">"</div>
<div class="title">{d['title']}</div>
<div class="sub">{d.get('sub','')}</div></div>
</div></body></html>"""


# ================================================================
# 手绘范式 A · 步骤流程图（Steps）
# ================================================================
def _paper():
    return f"""background:{PAPER};
  background-image:repeating-linear-gradient(0deg,transparent 0 52px,rgba(31,42,68,0.035) 52px 53px);"""

def _hand_border():
    return "border:4px solid #2b2b2b;border-radius:225px 15px 225px 15px/15px 225px 15px 225px;"

def hand_steps(d):
    steps = d["steps"]
    body = ""
    for i, s in enumerate(steps, 1):
        arrow = "" if i == len(steps) else f"""<svg class="arr" width="60" height="70" viewBox="0 0 60 70">
          <path d="M30 6 Q40 35 30 56" fill="none" stroke="{GOLD}" stroke-width="6" stroke-linecap="round"/>
          <path d="M18 44 L30 60 L42 44" fill="none" stroke="{GOLD}" stroke-width="6" stroke-linecap="round"/></svg>"""
        body += f"""<div class="step"><div class="circle">{i}</div>
          <div class="stxt"><div class="stt">{s['t']}</div><div class="sdd">{s.get('d','')}</div></div></div>{arrow}"""
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{COMMON}
.page{{width:{W_HAND}px;height:{H_HAND}px;{_paper()}padding:80px 90px;font-family:{HAND_FONT};}}
.title{{font-size:72px;font-weight:900;color:{INK};transform:rotate(-1.2deg);}}
.uline{{width:420px;height:0;margin:14px 0 8px;
  border-bottom:8px solid {GOLD};border-radius:6px;transform:rotate(-0.8deg);}}
.hint{{font-size:30px;color:#7a7062;margin-bottom:46px;}}
.step{{display:flex;align-items:center;gap:36px;{_hand_border()}
  background:rgba(255,255,255,0.6);padding:34px 40px;transform:rotate(-0.5deg);}}
.step:nth-child(4n){{transform:rotate(0.6deg);}}
.circle{{flex:0 0 96px;width:96px;height:96px;border-radius:50%;border:5px solid {INK};
  color:{INK};font-size:50px;font-weight:900;display:flex;align-items:center;justify-content:center;
  background:{MARK_Y};}}
.stt{{font-size:46px;font-weight:800;color:{INK};line-height:1.25;}}
.sdd{{margin-top:8px;font-size:30px;color:#5a5348;line-height:1.55;font-family:{FONT};}}
.arr{{display:block;margin:2px auto;}}
</style></head><body><div class="page">
<div class="title">{d['title']}</div><div class="uline"></div>
<div class="hint">{d.get('hint','跟着 1-2-3 走，不踩坑')}</div>
{body}
</div></body></html>"""


# ================================================================
# 手绘范式 B · 对比图（VS）
# ================================================================
def hand_vs(d):
    L = d["left"]; R = d["right"]
    def li(items, ok):
        s = ""
        for x in items:
            ic = "✓" if ok else "✗"
            cls = "ok" if ok else "no"
            s += f'<div class="li {cls}"><span class="ic">{ic}</span>{x}</div>'
        return s
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{COMMON}
.page{{width:{W_HAND}px;height:{H_HAND}px;{_paper()}padding:76px 70px;font-family:{HAND_FONT};position:relative;}}
.title{{font-size:70px;font-weight:900;color:{INK};text-align:center;transform:rotate(-0.6deg);}}
.subt{{text-align:center;font-size:30px;color:#7a7062;margin:14px 0 50px;font-family:{FONT};}}
.cols{{display:flex;gap:40px;}}
.col{{flex:1;{_hand_border()}padding:40px 36px;background:rgba(255,255,255,0.6);}}
.col.bad{{border-color:#b98c86;transform:rotate(-0.8deg);}}
.col.good{{border-color:{GREEN};transform:rotate(0.7deg);}}
.ch{{font-size:52px;font-weight:900;text-align:center;margin-bottom:30px;}}
.bad .ch{{color:{RED_PEN};}} .good .ch{{color:{GREEN};}}
.li{{font-size:34px;line-height:1.5;margin-bottom:26px;color:{INK};display:flex;gap:16px;align-items:flex-start;font-family:{FONT};}}
.li .ic{{font-size:38px;font-weight:900;flex:0 0 auto;}}
.no .ic{{color:{RED_PEN};}} .ok .ic{{color:{GREEN};}}
.ok{{background:linear-gradient(transparent 60%, {MARK_G} 60%);border-radius:6px;padding:0 4px;}}
.vs{{position:absolute;left:50%;top:54%;transform:translate(-50%,-50%);
  width:120px;height:120px;border-radius:50%;background:{INK};color:{GOLD};
  display:flex;align-items:center;justify-content:center;font-size:46px;font-weight:900;
  border:5px solid {PAPER};box-shadow:0 8px 26px rgba(0,0,0,0.28);}}
</style></head><body><div class="page">
<div class="title">{d['title']}</div><div class="subt">{d.get('hint','一张图看清差别')}</div>
<div class="cols">
<div class="col bad"><div class="ch">{L.get('head','这样 ✗')}</div>{li(L['items'],False)}</div>
<div class="col good"><div class="ch">{R.get('head','这样 ✓')}</div>{li(R['items'],True)}</div>
</div><div class="vs">VS</div>
</div></body></html>"""


# ================================================================
# 手绘范式 C · 清单勾选图（Checklist）
# ================================================================
def hand_checklist(d):
    rows = ""
    for it in d["items"]:
        hl = it.get("hl", "")
        t = it["t"]
        if hl and hl in t:
            t = t.replace(hl, f'<span class="mk">{hl}</span>')
        rows += f"""<div class="row"><span class="box">✓</span><span class="tx">{t}</span></div>"""
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{COMMON}
.page{{width:{W_HAND}px;height:{H_HAND}px;{_paper()}padding:80px 84px;font-family:{HAND_FONT};}}
.title{{font-size:70px;font-weight:900;color:{INK};transform:rotate(-1deg);}}
.uline{{width:460px;height:0;border-bottom:10px solid {MARK_Y};margin:10px 0 12px;transform:rotate(-0.6deg);}}
.hint{{font-size:30px;color:#7a7062;margin-bottom:50px;font-family:{FONT};}}
.row{{display:flex;align-items:flex-start;gap:30px;margin-bottom:40px;transform:rotate(-0.3deg);}}
.box{{flex:0 0 62px;width:62px;height:62px;border:5px solid {INK};border-radius:14px;
  color:{GREEN};font-size:42px;font-weight:900;display:flex;align-items:center;justify-content:center;
  transform:rotate(-3deg);}}
.tx{{font-size:40px;line-height:1.5;color:{INK};font-family:{FONT};padding-top:4px;}}
.mk{{background:linear-gradient(transparent 55%, {MARK_Y} 55%);border-radius:4px;padding:0 6px;font-weight:800;}}
.star{{margin-top:20px;font-size:34px;color:{CORAL};font-family:{FONT};font-weight:800;}}
</style></head><body><div class="page">
<div class="title">{d['title']}</div><div class="uline"></div>
<div class="hint">{d.get('hint','对着勾一遍，缺哪补哪')}</div>
{rows}
<div class="star">★ {d.get('foot','全部打勾，才算真的配齐了')}</div>
</div></body></html>"""


# ================================================================
# 手绘范式 D · 关系/结构图（Map）—— 中心辐射
# ================================================================
def hand_map(d):
    nodes = d["nodes"]  # up to 4
    # 固定 4 个方位坐标
    pos = [("22%","16%"),("78%","16%"),("22%","78%"),("78%","78%")]
    ncards = ""
    lines = ""
    cx, cy = 540, 675
    coords = [(238,300),(842,300),(238,1050),(842,1050)]
    for i, n in enumerate(nodes[:4]):
        x, y = pos[i]
        ncards += f"""<div class="node" style="left:{x};top:{y};">
          <div class="nt">{n['t']}</div><div class="nd">{n.get('d','')}</div></div>"""
        ex, ey = coords[i]
        lines += f'<path d="M{cx} {cy} Q{(cx+ex)//2+ (30 if i%2 else -30)} {(cy+ey)//2} {ex} {ey}" fill="none" stroke="{GOLD}" stroke-width="5" stroke-linecap="round" stroke-dasharray="3 16"/>'
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{COMMON}
.page{{width:{W_HAND}px;height:{H_HAND}px;{_paper()}position:relative;font-family:{HAND_FONT};overflow:hidden;}}
.title{{position:absolute;top:56px;left:70px;font-size:60px;font-weight:900;color:{INK};transform:rotate(-1deg);z-index:5;}}
.lines{{position:absolute;inset:0;}}
.core{{position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);
  width:280px;height:280px;border-radius:50%;background:{INK};color:#fff;
  display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;
  box-shadow:0 12px 40px rgba(31,42,68,0.35);border:6px solid {GOLD};z-index:4;padding:20px;}}
.core .ct{{font-size:44px;font-weight:900;}}
.core .cd{{margin-top:10px;font-size:26px;color:{GOLD};font-family:{FONT};}}
.node{{position:absolute;transform:translate(-50%,-50%);width:300px;{_hand_border()}
  background:rgba(255,255,255,0.72);padding:30px 28px;text-align:center;z-index:3;}}
.nt{{font-size:40px;font-weight:800;color:{GREEN};}}
.nd{{margin-top:10px;font-size:27px;color:#5a5348;line-height:1.5;font-family:{FONT};}}
</style></head><body><div class="page">
<div class="title">{d['title']}</div>
<svg class="lines" viewBox="0 0 {W_HAND} {H_HAND}" preserveAspectRatio="none">{lines}</svg>
<div class="core"><div class="ct">{d['core']['t']}</div><div class="cd">{d['core'].get('d','')}</div></div>
{ncards}
</div></body></html>"""


# ================================================================
# 新增风格家族（归档库 S06/S10/S15/S16/S20/S26/S30/S31）
# 每个 = 一个视觉模板家族的封面实现，证明引擎可覆盖多风格
# ================================================================

# ---- S06 大字报：黑底白字 + 超大态度字 ----
def cover_dazibao(d):
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{COMMON}
.page{{width:{W_COVER}px;height:{H_COVER}px;position:relative;overflow:hidden;
  background:#111111;color:#fff;padding:90px 80px;display:flex;flex-direction:column;justify-content:center;}}
.strip{{position:absolute;top:0;left:0;right:0;height:18px;background:{CORAL};}}
.star{{position:absolute;top:60px;right:70px;color:{GOLD};font-size:60px;}}
.title{{font-size:150px;font-weight:900;line-height:1.02;letter-spacing:-2px;
  text-shadow:6px 6px 0 {CORAL};}}
.title .hl{{color:{GOLD};}}
.sub{{margin-top:46px;font-size:40px;font-weight:700;color:#e9e9e9;line-height:1.4;}}
.foot{{position:absolute;bottom:70px;left:80px;font-size:28px;color:{GOLD};letter-spacing:4px;}}
</style></head><body><div class="page"><div class="strip"></div><div class="star">★</div>
<div class="title">{d['title']}</div>
<div class="sub">{d.get('sub','')}</div>
<div class="foot">{d.get('foot','· 句句大实话 ·')}</div>
</div></body></html>"""


# ---- S10 霓虹灯字：近黑底 + 发光字 ----
def cover_neon(d):
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{COMMON}
.page{{width:{W_COVER}px;height:{H_COVER}px;position:relative;overflow:hidden;
  background:radial-gradient(circle at 50% 45%, #15151f 0%, #08080d 80%);
  display:flex;align-items:center;justify-content:center;padding:80px;}}
.noise{{position:absolute;inset:0;opacity:0.06;background:
  repeating-radial-gradient(circle at 20% 30%, #fff 0 1px, transparent 1px 3px);}}
.kicker{{position:absolute;top:90px;left:0;right:0;text-align:center;color:#7fe9e0;
  font-size:30px;letter-spacing:10px;}}
.title{{font-size:128px;font-weight:900;text-align:center;line-height:1.15;
  color:#fff;text-shadow:0 0 12px #2ee6d6,0 0 30px #2ee6d6,0 0 60px #1fb8ad;}}
.title .pink{{color:#ff7ec8;text-shadow:0 0 12px #ff3ea5,0 0 30px #ff3ea5,0 0 60px #d62e8c;}}
.sub{{position:absolute;bottom:120px;left:0;right:0;text-align:center;color:#9fb6c9;
  font-size:32px;letter-spacing:2px;}}
</style></head><body><div class="page"><div class="noise"></div>
<div class="kicker">{d.get('kicker','夜话 · 保险')}</div>
<div class="title">{d['title']}</div>
<div class="sub">{d.get('sub','')}</div>
</div></body></html>"""


# ---- S16 新中式极简：宣纸留白 + 黛青 + 朱红印 ----
def cover_guofeng(d):
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{COMMON}
.page{{width:{W_COVER}px;height:{H_COVER}px;position:relative;overflow:hidden;
  background:#f5f1e8;color:#2f4858;padding:100px 90px;
  display:flex;flex-direction:column;justify-content:center;}}
.seal{{position:absolute;top:90px;right:90px;width:96px;height:96px;background:{CORAL};
  color:#fff;font-size:30px;font-weight:800;display:flex;align-items:center;justify-content:center;
  border-radius:8px;letter-spacing:2px;line-height:1.1;text-align:center;transform:rotate(3deg);}}
.rule{{width:90px;height:6px;background:#2f4858;margin-bottom:34px;}}
.title{{font-size:96px;font-weight:800;line-height:1.3;letter-spacing:6px;}}
.title .hl{{color:{CORAL};}}
.sub{{margin-top:38px;font-size:34px;color:#5a6b78;line-height:1.7;}}
.foot{{position:absolute;bottom:80px;left:90px;font-size:26px;color:#9a8f7a;letter-spacing:3px;}}
</style></head><body><div class="page"><div class="seal">保障</div>
<div class="rule"></div>
<div class="title">{d['title']}</div>
<div class="sub">{d.get('sub','')}</div>
<div class="foot">{d.get('foot','· 东方家庭的安全感 ·')}</div>
</div></body></html>"""


# ---- S26 达芬奇手稿：羊皮纸 + 墨褐线条 + 红标注 ----
def cover_davinci(d):
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{COMMON}
.page{{width:{W_COVER}px;height:{H_COVER}px;position:relative;overflow:hidden;
  background:#efe6d0;color:#3a2e1f;padding:90px;font-family:Georgia,serif;}}
.sketch{{position:absolute;right:60px;top:120px;opacity:0.5;}}
.title{{font-size:84px;font-weight:800;line-height:1.3;margin-top:60px;max-width:760px;}}
.title .hl{{color:#9e3a2f;font-style:italic;}}
.sub{{margin-top:34px;font-size:30px;color:#5a4a36;line-height:1.7;max-width:760px;}}
.note{{position:absolute;left:90px;bottom:90px;font-size:24px;color:#9e3a2f;
  font-style:italic;transform:rotate(-2deg);}}
.scale{{position:absolute;right:90px;bottom:90px;font-size:22px;color:#7a6a50;}}
</style></head><body><div class="page">
<svg class="sketch" width="360" height="360" viewBox="0 0 360 360">
  <circle cx="180" cy="180" r="150" fill="none" stroke="#3a2e1f" stroke-width="2"/>
  <circle cx="180" cy="180" r="90" fill="none" stroke="#3a2e1f" stroke-width="1.5"/>
  <line x1="30" y1="180" x2="330" y2="180" stroke="#3a2e1f" stroke-width="1.5"/>
  <line x1="180" y1="30" x2="180" y2="330" stroke="#3a2e1f" stroke-width="1.5"/>
  <path d="M180 30 Q260 180 180 330" fill="none" stroke="#9e3a2f" stroke-width="2"/>
</svg>
<div class="title">{d['title']}</div>
<div class="sub">{d.get('sub','')}</div>
<div class="note">{d.get('note','fig. 保险之结构')}</div>
<div class="scale">比例尺 · 1 : 保障</div>
</div></body></html>"""


# ---- S11 时尚杂志：米白 + 衬线大标题 + 细线刊头 ----
def cover_magazine(d):
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{COMMON}
.page{{width:{W_COVER}px;height:{H_COVER}px;position:relative;overflow:hidden;
  background:#faf8f3;color:#1f2a44;padding:90px 84px;}}
.mast{{display:flex;justify-content:space-between;align-items:center;
  border-bottom:2px solid #1f2a44;padding-bottom:18px;font-size:26px;letter-spacing:4px;}}
.mast .iss{{color:{GOLD};font-weight:700;}}
.kicker{{margin-top:70px;font-size:30px;color:{GREEN};font-weight:700;letter-spacing:3px;}}
.title{{margin-top:20px;font-size:104px;font-weight:800;line-height:1.12;
  font-family:Georgia,'Times New Roman',serif;}}
.title .hl{{color:{CORAL};font-style:italic;}}
.rule{{width:120px;height:5px;background:{GOLD};margin:30px 0;}}
.sub{{font-size:32px;color:#5a6275;line-height:1.6;max-width:840px;}}
.foot{{position:absolute;bottom:80px;left:84px;right:84px;font-size:24px;color:#9a8f7a;
  border-top:1px solid #d8d2c4;padding-top:18px;letter-spacing:2px;}}
</style></head><body><div class="page">
<div class="mast"><span>保 障 志</span><span class="iss">ISSUE 01 · 家庭</span></div>
<div class="kicker">{d.get('kicker','封面故事')}</div>
<div class="title">{d['title']}</div><div class="rule"></div>
<div class="sub">{d.get('sub','')}</div>
<div class="foot">{d.get('foot','编辑部 · 用专业守护每一个家')}</div>
</div></body></html>"""


# ---- S31 孟菲斯：撞色几何 + 活泼圆体 ----
def cover_memphis(d):
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{COMMON}
.page{{width:{W_COVER}px;height:{H_COVER}px;position:relative;overflow:hidden;
  background:#fdf3e7;color:#1f2a44;}}
.shapes{{position:absolute;inset:0;}}
.t{{position:absolute;left:90px;bottom:200px;font-size:94px;font-weight:900;line-height:1.1;}}
.t .hl{{color:{CORAL};}} .t .bl{{color:#2f8fbf;}}
.sub{{position:absolute;left:90px;bottom:120px;font-size:32px;font-weight:700;color:#5a6275;}}
</style></head><body><div class="page"><div class="shapes">
<svg width="{W_COVER}" height="{H_COVER}">
  <circle cx="850" cy="320" r="150" fill="#ffd23f"/>
  <rect x="120" y="120" width="180" height="180" fill="#2f8fbf" transform="rotate(12 210 210)"/>
  <path d="M700 920 Q800 840 900 920" fill="none" stroke="#2f5d50" stroke-width="14" stroke-linecap="round"/>
  <circle cx="220" cy="1050" r="26" fill="#d8674f"/><circle cx="300" cy="1050" r="26" fill="#2f8fbf"/><circle cx="380" cy="1050" r="26" fill="#ffd23f"/>
  <path d="M120 600 L200 560 L280 600 L360 560" fill="none" stroke="#d8674f" stroke-width="10"/>
</svg></div>
<div class="t">{d['title']}</div>
<div class="sub">{d.get('sub','')}</div>
</div></body></html>"""


# ---- S20 知识卡：白卡 + 墨蓝标题 + 墨绿图标 + 金强调 ----
def cover_knowledge(d):
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{COMMON}
.page{{width:{W_COVER}px;height:{H_COVER}px;position:relative;overflow:hidden;
  background:linear-gradient(160deg,#eef1f5,#e2e8ef);padding:90px;display:flex;align-items:center;}}
.card{{width:100%;background:#fff;border-radius:28px;padding:64px 60px;
  box-shadow:0 24px 60px rgba(31,42,68,0.16);border-top:10px solid {GREEN};}}
.kicker{{display:inline-block;background:{GREEN};color:#fff;font-size:26px;font-weight:700;
  padding:8px 22px;border-radius:20px;letter-spacing:2px;}}
.icon{{font-size:78px;margin:24px 0 8px;}}
.title{{font-size:72px;font-weight:900;color:{INK};line-height:1.25;}}
.title .hl{{background:linear-gradient(transparent 60%, rgba(200,164,92,0.5) 60%);}}
.desc{{margin-top:24px;font-size:32px;color:#5a6275;line-height:1.7;}}
.tag{{margin-top:28px;font-size:26px;color:{GREEN};font-weight:700;letter-spacing:2px;}}
</style></head><body><div class="page"><div class="card">
<div class="kicker">{d.get('kicker','知识卡片')}</div>
<div class="icon">{d.get('icon','📌')}</div>
<div class="title">{d['title']}</div>
<div class="desc">{d.get('desc','')}</div>
<div class="tag">{d.get('tag','建议收藏 · 随时翻看')}</div>
</div></div></body></html>"""


# ---- S30 抽象几何（蒙德里安）：原色块 + 黑线 ----
def cover_mondrian(d):
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{COMMON}
.page{{width:{W_COVER}px;height:{H_COVER}px;position:relative;overflow:hidden;background:#fff;}}
.blk{{position:absolute;border:8px solid #111;}}
.b1{{left:0;top:0;width:46%;height:40%;background:#c0392b;}}
.b2{{right:0;top:0;width:54%;height:24%;background:#1f4e9b;}}
.b3{{right:0;top:24%;width:30%;height:36%;background:#f2c65c;}}
.txt{{position:absolute;left:60px;top:46%;width:42%;font-size:62px;font-weight:900;
  color:#111;line-height:1.15;}}
.txt .hl{{color:#c0392b;}}
.sub{{position:absolute;left:60px;bottom:60px;font-size:28px;color:#333;font-weight:700;}}
</style></head><body><div class="page">
<div class="blk b1"></div><div class="blk b2"></div><div class="blk b3"></div>
<div class="txt">{d['title']}</div>
<div class="sub">{d.get('sub','')}</div>
</div></body></html>"""


# ================================================================
# 其余风格家族（补齐至归档库全 40 式）
# ================================================================

# ---- S02 简笔插画：浅底 + 简笔图标 + 标题 ----
def cover_illustration(d):
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{COMMON}
.page{{width:{W_COVER}px;height:{H_COVER}px;position:relative;overflow:hidden;
  background:linear-gradient(160deg,#eaf3f1,#dcebe8);padding:90px;display:flex;flex-direction:column;justify-content:center;}}
.ill{{margin-bottom:30px;}}
.title{{font-size:84px;font-weight:900;color:{INK};line-height:1.25;}}
.title .hl{{color:{GREEN};}}
.sub{{margin-top:28px;font-size:32px;color:#5a6275;line-height:1.7;}}
</style></head><body><div class="page"><div class="ill">
<svg width="240" height="200" viewBox="0 0 240 200">
<path d="M40 170 L120 60 L200 170 Z" fill="none" stroke="{INK}" stroke-width="6" stroke-linejoin="round"/>
<path d="M120 60 L120 20" stroke="{CORAL}" stroke-width="6" stroke-linecap="round"/>
<circle cx="120" cy="14" r="14" fill="{GOLD}"/>
<rect x="80" y="120" width="80" height="50" fill="none" stroke="{GREEN}" stroke-width="5"/>
</svg></div>
<div class="title">{d['title']}</div>
<div class="sub">{d.get('sub','')}</div>
</div></body></html>"""


# ---- S03 涂鸦漫画：白底 + 对话气泡 + 手绘感 ----
def cover_doodle(d):
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{COMMON}
.page{{width:{W_COVER}px;height:{H_COVER}px;position:relative;overflow:hidden;background:#fffdf7;padding:90px;}}
.bubble{{border:5px solid {INK};border-radius:40px 40px 40px 6px;padding:50px 56px;max-width:820px;
  font-size:56px;font-weight:800;color:{INK};line-height:1.35;transform:rotate(-1.5deg);}}
.bubble .hl{{color:{CORAL};}}
.cap{{margin-top:50px;font-size:32px;color:#7a7062;font-family:{HAND_FONT};transform:rotate(-1deg);}}
</style></head><body><div class="page">
<div class="bubble">{d['title']}</div>
<div class="cap">{d.get('sub','—— 一个保险经纪人的大白话')}</div>
</div></body></html>"""


# ---- S04 儿童绘本：暖色厚涂 + 圆润 ----
def cover_storybook(d):
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{COMMON}
.page{{width:{W_COVER}px;height:{H_COVER}px;position:relative;overflow:hidden;
  background:radial-gradient(circle at 50% 30%, #fff3e0 0%, #ffe0c2 100%);padding:100px;display:flex;flex-direction:column;justify-content:center;}}
.star{{position:absolute;top:80px;right:90px;font-size:70px;color:{GOLD};}}
.title{{font-size:80px;font-weight:800;color:{INK};line-height:1.4;}}
.title .hl{{color:{CORAL};}}
.sub{{margin-top:30px;font-size:32px;color:#8a6f56;line-height:1.7;}}
</style></head><body><div class="page"><div class="star">★</div>
<div class="title">{d['title']}</div>
<div class="sub">{d.get('sub','')}</div>
</div></body></html>"""


# ---- S05 手绘信息长图：纸底竖向多段 ----
def hand_longinfo(d):
    blocks = ""
    for i, b in enumerate(d["blocks"], 1):
        blocks += f"""<div class="blk"><div class="bn">{i:02d}</div><div class="bt">{b['t']}</div><div class="bd">{b.get('d','')}</div></div>"""
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{COMMON}
.page{{width:{W_HAND}px;height:{H_HAND}px;{_paper()}padding:80px 90px;font-family:{HAND_FONT};}}
.title{{font-size:64px;font-weight:900;color:{INK};transform:rotate(-1deg);}}
.ul{{width:380px;height:0;border-bottom:8px solid {MARK_Y};margin:12px 0 40px;transform:rotate(-0.6deg);}}
.blk{{display:flex;gap:28px;margin-bottom:34px;{_hand_border()}background:rgba(255,255,255,0.55);padding:28px 32px;}}
.bn{{flex:0 0 64px;width:64px;height:64px;border-radius:14px;background:{INK};color:{GOLD};font-size:32px;font-weight:900;display:flex;align-items:center;justify-content:center;transform:rotate(-3deg);}}
.bt{{font-size:38px;font-weight:800;color:{INK};}} .bd{{font-size:26px;color:#5a5348;font-family:{FONT};margin-top:6px;}}
</style></head><body><div class="page">
<div class="title">{d['title']}</div><div class="ul"></div>{blocks}
</div></body></html>"""


# ---- S07 金句字卡：暗渐变 + 大字引言 ----
def cover_quote(d):
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{COMMON}
.page{{width:{W_COVER}px;height:{H_COVER}px;position:relative;overflow:hidden;
  background:radial-gradient(circle at 30% 20%, #2c3c60 0%, #161e33 70%);padding:110px;display:flex;flex-direction:column;justify-content:center;}}
.qm{{font-family:Georgia,serif;font-size:160px;color:rgba(200,164,92,0.5);line-height:0.4;}}
.quote{{font-size:64px;font-weight:800;color:#fff;line-height:1.5;letter-spacing:2px;margin-top:10px;}}
.quote .hl{{color:{GOLD};}}
.rule{{width:90px;height:5px;background:{GOLD};margin:40px 0 24px;}}
.attr{{font-size:28px;color:{GOLD};letter-spacing:4px;}}
</style></head><body><div class="page"><div class="qm">"</div>
<div class="quote">{d['title']}</div><div class="rule"></div>
<div class="attr">{d.get('sub','— 一位保险经纪人的手记')}</div>
</div></body></html>"""


# ---- S08 极简留白：大留白 + 一个关键词 ----
def cover_minimal(d):
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{COMMON}
.page{{width:{W_COVER}px;height:{H_COVER}px;position:relative;overflow:hidden;background:{CREAM};padding:90px;}}
.kw{{position:absolute;top:50%;left:90px;right:90px;transform:translateY(-50%);
  font-size:170px;font-weight:900;color:{INK};line-height:1.05;letter-spacing:4px;}}
.kw .hl{{color:{GOLD};}}
.sub{{position:absolute;bottom:90px;left:90px;font-size:30px;color:#9a8f7a;letter-spacing:3px;}}
</style></head><body><div class="page">
<div class="kw">{d['title']}</div>
<div class="sub">{d.get('sub','· 一句就够了 ·')}</div>
</div></body></html>"""


# ---- S09 报纸标题：新闻纸 + 刊头 + 红标题 ----
def cover_newspaper(d):
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{COMMON}
.page{{width:{W_COVER}px;height:{H_COVER}px;position:relative;overflow:hidden;
  background:#ece5d8;color:#1a1a1a;padding:80px;}}
.mast{{text-align:center;font-size:48px;font-weight:900;letter-spacing:8px;border-bottom:4px double #1a1a1a;padding-bottom:16px;}}
.date{{text-align:center;font-size:22px;color:#555;margin:10px 0 30px;letter-spacing:3px;}}
.head{{font-size:78px;font-weight:900;line-height:1.2;color:{CORAL};text-align:center;}}
.rule{{border-top:2px solid #1a1a1a;margin:30px 0;}}
.body{{font-size:28px;color:#333;line-height:1.8;column-count:2;column-gap:40px;text-align:justify;}}
</style></head><body><div class="page">
<div class="mast">家 庭 保 障 报</div><div class="date">每日洞察 · 泛保险观察</div>
<div class="head">{d['title']}</div><div class="rule"></div>
<div class="body">{d.get('sub','')}</div>
</div></body></html>"""


# ---- S12 杂志拼贴：撕边卡片 + 胶带 ----
def cover_collage(d):
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{COMMON}
.page{{width:{W_COVER}px;height:{H_COVER}px;position:relative;overflow:hidden;background:#dfe4e8;padding:80px;}}
.card{{position:absolute;background:#fff;box-shadow:0 14px 36px rgba(0,0,0,0.2);padding:46px;border-radius:4px;}}
.c1{{left:90px;top:120px;width:520px;transform:rotate(-4deg);}}
.c2{{right:90px;top:340px;width:480px;transform:rotate(3deg);background:{CREAM};}}
.tape{{position:absolute;width:140px;height:38px;background:rgba(200,164,92,0.55);top:-18px;left:50%;transform:translateX(-50%) rotate(-3deg);}}
.t{{font-size:64px;font-weight:900;color:{INK};line-height:1.2;}}
.t .hl{{color:{CORAL};}}
.s{{font-size:28px;color:#5a6275;margin-top:14px;line-height:1.6;}}
</style></head><body><div class="page">
<div class="card c1"><div class="tape"></div><div class="t">{d['title']}</div></div>
<div class="card c2"><div class="tape"></div><div class="s">{d.get('sub','')}</div></div>
</div></body></html>"""


# ---- S13 复古杂志：暖棕 + 颗粒 + 衬线 ----
def cover_retro(d):
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{COMMON}
.page{{width:{W_COVER}px;height:{H_COVER}px;position:relative;overflow:hidden;
  background:#c98a5a;color:#3a2418;padding:90px;}}
.grain{{position:absolute;inset:0;opacity:0.12;background:repeating-radial-gradient(circle,#000 0 1px,transparent 1px 4px);}}
.kick{{font-size:28px;letter-spacing:6px;font-weight:700;}}
.title{{margin-top:24px;font-size:96px;font-weight:800;line-height:1.15;font-family:Georgia,serif;}}
.title .hl{{color:#7a2e1c;}}
.sub{{margin-top:30px;font-size:30px;color:#4a3320;line-height:1.6;}}
</style></head><body><div class="page"><div class="grain"></div>
<div class="kick">{d.get('kicker','RETRO · 老故事')}</div>
<div class="title">{d['title']}</div>
<div class="sub">{d.get('sub','')}</div>
</div></body></html>"""


# ---- S14 瑞士网格：白底 + 严格对齐 + 原色块 ----
def cover_swiss(d):
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{COMMON}
.page{{width:{W_COVER}px;height:{H_COVER}px;position:relative;overflow:hidden;background:#fff;padding:90px;
  display:grid;grid-template-columns:1fr 1fr;grid-template-rows:auto 1fr auto;gap:30px;}}
.tag{{grid-column:1/3;font-size:26px;font-weight:700;letter-spacing:3px;color:{CORAL};}}
.block{{background:{INK};grid-column:1/3;height:120px;}}
.title{{grid-column:1/3;font-size:92px;font-weight:900;color:{INK};line-height:1.1;align-self:end;}}
.title .hl{{color:#1f4e9b;}}
.sub{{grid-column:1/3;font-size:30px;color:#5a6275;line-height:1.6;}}
</style></head><body><div class="page">
<div class="tag">{d.get('kicker','SWISS GRID')}</div>
<div class="block"></div>
<div class="title">{d['title']}</div>
<div class="sub">{d.get('sub','')}</div>
</div></body></html>"""


# ---- S15 国风水墨：宣纸 + 水墨晕染 + 竖排 ----
def cover_inkwash(d):
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{COMMON}
.page{{width:{W_COVER}px;height:{H_COVER}px;position:relative;overflow:hidden;background:#f5f1e8;padding:100px;}}
.ink{{position:absolute;right:80px;top:160px;width:420px;height:420px;border-radius:50%;
  background:radial-gradient(circle, rgba(43,43,43,0.85) 0%, rgba(43,43,43,0.25) 55%, transparent 72%);filter:blur(2px);}}
.title{{font-size:100px;font-weight:800;color:{INK};line-height:1.3;writing-mode:vertical-rl;position:absolute;left:110px;top:120px;letter-spacing:10px;}}
.seal{{position:absolute;left:120px;bottom:120px;width:84px;height:84px;background:{CORAL};color:#fff;font-size:28px;font-weight:800;display:flex;align-items:center;justify-content:center;border-radius:6px;}}
.sub{{position:absolute;right:110px;bottom:130px;font-size:28px;color:#5a6b78;writing-mode:vertical-rl;letter-spacing:4px;}}
</style></head><body><div class="page"><div class="ink"></div>
<div class="title">{d['title']}</div>
<div class="seal">保</div>
<div class="sub">{d.get('sub','')}</div>
</div></body></html>"""


# ---- S17 古籍活字：宣黄 + 竖排活字 + 朱批 ----
def cover_letterpress(d):
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{COMMON}
.page{{width:{W_COVER}px;height:{H_COVER}px;position:relative;overflow:hidden;background:#e8dcc0;padding:90px;}}
.col{{position:absolute;top:90px;bottom:90px;width:200px;display:flex;flex-wrap:wrap;align-content:flex-start;gap:6px;writing-mode:vertical-rl;}}
.col.l{{left:90px;}} .col.r{{right:90px;}}
.ch{{font-size:64px;font-weight:800;color:#2b2b2b;line-height:1;margin:0 4px;}}
.ch.red{{color:#9e3a2f;}}
.title{{position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);font-size:90px;font-weight:900;color:{INK};text-align:center;line-height:1.3;}}
</style></head><body><div class="page">
<div class="col l"><span class="ch">保</span><span class="ch red">障</span><span class="ch">之</span><span class="ch">道</span></div>
<div class="col r"><span class="ch">未</span><span class="ch">雨</span><span class="ch red">绸</span><span class="ch">缪</span></div>
<div class="title">{d['title']}</div>
</div></body></html>"""


# ---- S18 敦煌色彩：矿物色块 + 描金 ----
def cover_dunhuang(d):
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{COMMON}
.page{{width:{W_COVER}px;height:{H_COVER}px;position:relative;overflow:hidden;
  background:linear-gradient(135deg,#2a6b8a 0%,#b5482f 55%,#c8a45c 100%);padding:100px;}}
.frame{{position:absolute;inset:40px;border:4px solid rgba(200,164,92,0.8);}}
.title{{position:relative;font-size:96px;font-weight:900;color:#fff5e0;line-height:1.3;text-align:center;margin-top:200px;text-shadow:0 4px 16px rgba(0,0,0,0.4);}}
.sub{{position:relative;text-align:center;font-size:32px;color:#ffe9c8;margin-top:30px;letter-spacing:2px;}}
</style></head><body><div class="page"><div class="frame"></div>
<div class="title">{d['title']}</div>
<div class="sub">{d.get('sub','')}</div>
</div></body></html>"""


# ---- S19 节气民俗：当季色 + 红幅 + 民俗 ----
def cover_jieqi(d):
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{COMMON}
.page{{width:{W_COVER}px;height:{H_COVER}px;position:relative;overflow:hidden;background:#3a7d5d;padding:90px;}}
.banner{{background:{CORAL};color:#fff;font-size:44px;font-weight:800;text-align:center;padding:18px;letter-spacing:8px;border-radius:8px;}}
.knot{{position:absolute;top:60px;right:80px;font-size:64px;}}
.title{{font-size:84px;font-weight:900;color:#fff5e0;line-height:1.4;margin-top:60px;text-align:center;}}
.sub{{font-size:30px;color:#e8f3ea;margin-top:30px;text-align:center;line-height:1.6;}}
</style></head><body><div class="page"><div class="knot">🏮</div>
<div class="banner">{d.get('kicker','节 气 · 民 生')}</div>
<div class="title">{d['title']}</div>
<div class="sub">{d.get('sub','')}</div>
</div></body></html>"""


# ---- S27 工程蓝图：深蓝 + 白网格线 ----
def cover_blueprint(d):
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{COMMON}
.page{{width:{W_COVER}px;height:{H_COVER}px;position:relative;overflow:hidden;
  background:#0d2b4e;background-image:linear-gradient(rgba(255,255,255,0.12) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,0.12) 1px,transparent 1px);background-size:60px 60px;padding:100px;}}
.title{{font-size:80px;font-weight:900;color:#eaf3ff;line-height:1.3;}}
.title .hl{{color:#7fd0ff;}}
.note{{margin-top:30px;font-family:Georgia,serif;font-size:28px;color:#9fc4e8;letter-spacing:2px;}}
.dim{{position:absolute;bottom:90px;right:90px;font-size:26px;color:#7fd0ff;font-family:Georgia,serif;}}
</style></head><body><div class="page">
<div class="title">{d['title']}</div>
<div class="note">{d.get('sub','— 方案结构图 —')}</div>
<div class="dim">SCALE 1:保障</div>
</div></body></html>"""


# ---- S28 科学插画：白底 + 引线标注 ----
def cover_science(d):
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{COMMON}
.page{{width:{W_COVER}px;height:{H_COVER}px;position:relative;overflow:hidden;background:#fff;padding:100px;}}
.diag{{position:absolute;right:90px;top:200px;}}
.title{{font-size:80px;font-weight:900;color:{INK};line-height:1.3;max-width:640px;}}
.title .hl{{color:{GREEN};}}
.lab{{font-size:26px;color:#5a6275;margin-top:30px;font-family:Georgia,serif;}}
</style></head><body><div class="page">
<svg class="diag" width="320" height="320" viewBox="0 0 320 320">
<circle cx="160" cy="160" r="120" fill="none" stroke="{INK}" stroke-width="3"/>
<circle cx="160" cy="160" r="70" fill="rgba(47,93,80,0.15)" stroke="{GREEN}" stroke-width="2"/>
<line x1="160" y1="40" x2="160" y2="280" stroke="{CORAL}" stroke-width="2" stroke-dasharray="4 4"/>
<text x="170" y="50" font-size="22" fill="#5a6275" font-family="Georgia">A 区</text>
<text x="170" y="290" font-size="22" fill="#5a6275" font-family="Georgia">B 区</text>
</svg>
<div class="title">{d['title']}</div>
<div class="lab">{d.get('sub','图：保障结构示意')}</div>
</div></body></html>"""


# ---- S29 炭笔素描：灰纸 + 单色人物/场景 ----
def cover_charcoal(d):
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{COMMON}
.page{{width:{W_COVER}px;height:{H_COVER}px;position:relative;overflow:hidden;background:#e9e7e2;padding:100px;}}
.port{{position:absolute;right:90px;top:160px;width:360px;height:360px;border-radius:8px;
  background:linear-gradient(160deg,#bdbab4,#6f6c66);filter:grayscale(1) contrast(1.1);}}
.title{{font-size:78px;font-weight:900;color:#3a3a3a;line-height:1.35;max-width:620px;}}
.title .hl{{color:#1a1a1a;text-decoration:underline wavy {CORAL};}}
.sub{{margin-top:28px;font-size:30px;color:#5a5752;line-height:1.7;max-width:600px;}}
</style></head><body><div class="page"><div class="port"></div>
<div class="title">{d['title']}</div>
<div class="sub">{d.get('sub','')}</div>
</div></body></html>"""


# ---- S32 极简抽象：双色块 + 居中字 ----
def cover_abstract_min(d):
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{COMMON}
.page{{width:{W_COVER}px;height:{H_COVER}px;position:relative;overflow:hidden;background:#f2efe9;}}
.blk{{position:absolute;left:0;bottom:0;width:55%;height:42%;background:{INK};}}
.title{{position:absolute;left:90px;top:46%;font-size:96px;font-weight:900;color:#fff;line-height:1.1;}}
.title .hl{{color:{GOLD};}}
.sub{{position:absolute;right:90px;top:90px;font-size:30px;color:{INK};font-weight:700;letter-spacing:2px;}}
</style></head><body><div class="page">
<div class="blk"></div>
<div class="title">{d['title']}</div>
<div class="sub">{d.get('sub','')}</div>
</div></body></html>"""


# ---- S33 渐变流体：柔和渐变 + 细字 ----
def cover_fluid(d):
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{COMMON}
.page{{width:{W_COVER}px;height:{H_COVER}px;position:relative;overflow:hidden;
  background:linear-gradient(135deg,#a8e6cf 0%,#dcedc1 40%,#ffd3b6 100%);padding:100px;display:flex;flex-direction:column;justify-content:center;}}
.blob{{position:absolute;width:420px;height:420px;border-radius:50%;background:radial-gradient(circle,rgba(255,255,255,0.6),transparent 70%);top:120px;right:80px;}}
.title{{font-size:92px;font-weight:900;color:#3a4a42;line-height:1.25;}}
.title .hl{{color:#2f7d63;}}
.sub{{margin-top:30px;font-size:32px;color:#4a5a52;line-height:1.7;}}
</style></head><body><div class="page"><div class="blob"></div>
<div class="title">{d['title']}</div>
<div class="sub">{d.get('sub','')}</div>
</div></body></html>"""


# ---- S34 波普艺术：半调网点 + 粗框 ----
def cover_pop(d):
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{COMMON}
.page{{width:{W_COVER}px;height:{H_COVER}px;position:relative;overflow:hidden;background:{CORAL};padding:80px;}}
.halftone{{position:absolute;inset:0;opacity:0.18;background:radial-gradient(circle,#000 1px,transparent 2px);background-size:14px 14px;}}
.box{{position:relative;border:8px solid #111;background:#ffd23f;padding:50px;transform:rotate(-2deg);}}
.title{{font-size:84px;font-weight:900;color:#111;line-height:1.15;text-transform:uppercase;}}
.title .hl{{color:{CORAL};}}
.sub{{margin-top:30px;font-size:32px;font-weight:800;color:#111;}}
</style></head><body><div class="page"><div class="halftone"></div>
<div class="box"><div class="title">{d['title']}</div><div class="sub">{d.get('sub','')}</div></div>
</div></body></html>"""


# ---- S35 梦核蒸汽波：紫粉青渐变 + 故障 ----
def cover_dreamcore(d):
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{COMMON}
.page{{width:{W_COVER}px;height:{H_COVER}px;position:relative;overflow:hidden;
  background:linear-gradient(160deg,#7b5cff 0%,#ff7ec8 50%,#5ce0ff 100%);padding:100px;}}
.grid{{position:absolute;inset:0;opacity:0.25;background:linear-gradient(rgba(255,255,255,0.5) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,0.5) 1px,transparent 1px);background-size:50px 50px;}}
.title{{position:relative;font-size:90px;font-weight:900;color:#fff;line-height:1.2;text-shadow:4px 0 #ff3ea5,-4px 0 #2ee6d6;}}
.title .hl{{color:#fff;}}
.sub{{position:relative;margin-top:30px;font-size:30px;color:#fff;letter-spacing:3px;}}
</style></head><body><div class="page"><div class="grid"></div>
<div class="title">{d['title']}</div>
<div class="sub">{d.get('sub','')}</div>
</div></body></html>"""


# ---- S37 胶片质感：暗角 + 颗粒 + 时间戳 ----
def cover_film(d):
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{COMMON}
.page{{width:{W_COVER}px;height:{H_COVER}px;position:relative;overflow:hidden;
  background:linear-gradient(160deg,#5a5048,#2b2622);padding:80px;}}
.frame{{position:absolute;inset:36px;border:14px solid #1a1714;}}
.grain{{position:absolute;inset:0;opacity:0.15;background:repeating-radial-gradient(circle,#fff 0 1px,transparent 1px 3px);}}
.title{{position:relative;color:#f3ece0;font-size:76px;font-weight:900;line-height:1.3;margin-top:80px;text-align:center;}}
.time{{position:absolute;bottom:60px;left:0;right:0;text-align:center;color:#c8a45c;font-family:Georgia,serif;font-size:30px;letter-spacing:4px;}}
</style></head><body><div class="page"><div class="frame"></div><div class="grain"></div>
<div class="title">{d['title']}</div>
<div class="time">{d.get('sub','REC · 1998 · 家庭')}</div>
</div></body></html>"""


# ---- S38 产品平铺：干净底 + 物件占位 + 标签 ----
def cover_flatlay(d):
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{COMMON}
.page{{width:{W_COVER}px;height:{H_COVER}px;position:relative;overflow:hidden;background:#f4f1ea;padding:90px;}}
.tile{{position:absolute;width:200px;height:260px;background:#fff;border-radius:12px;box-shadow:0 10px 30px rgba(0,0,0,0.12);display:flex;align-items:center;justify-content:center;font-size:90px;}}
.t1{{left:120px;top:160px;transform:rotate(-6deg);}} .t2{{left:360px;top:300px;transform:rotate(4deg);background:{CREAM};}} .t3{{left:600px;top:180px;transform:rotate(-3deg);}}
.title{{position:absolute;left:90px;bottom:120px;font-size:72px;font-weight:900;color:{INK};line-height:1.2;}}
.title .hl{{color:{GREEN};}}
</style></head><body><div class="page">
<div class="tile t1">📄</div><div class="tile t2">🛡️</div><div class="tile t3">💡</div>
<div class="title">{d['title']}</div>
</div></body></html>"""


# ---- S39 场景代入：渐变场景 + 底部字幕（照片占位） ----
def cover_scene(d):
    bg = d.get("grad", "background:linear-gradient(160deg,#cdb89a 0%,#8a7458 100%);")
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{COMMON}
.page{{width:{W_COVER}px;height:{H_COVER}px;position:relative;overflow:hidden;{bg}}}
.scrim{{position:absolute;inset:0;background:linear-gradient(to top,rgba(12,16,30,0.75) 0%,transparent 55%);}}
.inner{{position:absolute;left:70px;right:70px;bottom:80px;color:#fff;}}
.tag{{display:inline-block;border:1px solid rgba(200,164,92,0.7);color:#e9d6ad;font-size:24px;padding:6px 18px;border-radius:18px;letter-spacing:3px;margin-bottom:18px;}}
.title{{font-size:64px;font-weight:800;line-height:1.35;text-shadow:0 2px 12px rgba(0,0,0,0.5);}}
.title .hl{{color:{GOLD};}}
.sub{{margin-top:14px;font-size:30px;color:#e2e6ee;line-height:1.6;}}
</style></head><body><div class="page"><div class="scrim"></div><div class="inner">
<div class="tag">{d.get('tag','真实场景')}</div>
<div class="title">{d['title']}</div>
<div class="sub">{d.get('sub','')}</div></div>
</div></body></html>"""


# ---- S40 信息图解摄影：模拟截图卡 + 红框强调 ----
def cover_datashot(d):
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{COMMON}
.page{{width:{W_COVER}px;height:{H_COVER}px;position:relative;overflow:hidden;background:#eef1f5;padding:90px;display:flex;align-items:center;}}
.shot{{width:100%;background:#fff;border-radius:18px;box-shadow:0 20px 50px rgba(31,42,68,0.18);overflow:hidden;border:3px solid {CORAL};}}
.bar{{background:{INK};color:#fff;font-size:26px;padding:18px 28px;letter-spacing:2px;}}
.row{{display:flex;justify-content:space-between;padding:30px 32px;border-bottom:1px solid #eee;font-size:34px;}}
.row .v{{font-weight:900;color:{GREEN};}} .row .v.red{{color:{CORAL};}}
.cap{{padding:26px 32px;font-size:28px;color:#5a6275;line-height:1.6;}}
</style></head><body><div class="page"><div class="shot">
<div class="bar">{d.get('kicker','理赔实录 · 脱敏')}</div>
<div class="row"><span>案件</span><span class="v">{d.get('a','重疾理赔')}</span></div>
<div class="row"><span>赔付</span><span class="v red">{d.get('b','88 万')}</span></div>
<div class="row"><span>时效</span><span class="v">{d.get('c','3 天到账')}</span></div>
<div class="cap">{d.get('sub','* 以保险公司核定为准')}</div>
</div></div></body></html>"""


# ================================================================
# S00 卡通知识卡固定式（Cartoon Knowledge Card · 核心风格）
# 来自公众号实战验证，三种子类型：对比双栏 / 误区纠错 / 分人群方案
# ================================================================

# S00 配色常量
CBLUE   = "#2B7DD8"   # 信息蓝（左侧/正确/标签）
CORANGE = "#FF8C42"   # 强调橙（金额/右侧/高亮）
CGREEN  = "#22C55E"   # 正确绿（CTA/对勾）
CRED    = "#EF4444"   # 错误红（X标记/警示）
CDARK   = "#1a1a2e"   # 超深黑（标题）
CGRAY   = "#666666"   # 灰色（副标题/次要文字）
CLIGHT  = "#F5FAFD"   # 浅蓝渐变底
CWARM   = "#FFF8F0"   # 奶暖底


def _svg_car(color, label="", w=180, h=100):
    """扁平卡通小车 SVG（简化版，用于对比卡和场景卡的插画元素）"""
    return f'''<svg viewBox="0 0 {w} {h}" width="{w}" height="{h}" xmlns="http://www.w3.org/2000/svg">
    <ellipse cx="{w//2}" cy="{h-12}" rx="{w//2-10}" ry="10" fill="rgba(0,0,0,0.08)"/>
    <rect x="20" y="25" width="{w-40}" height="50" rx="18" fill="{color}"/>
    <rect x="35" y="32" width="45" height="32" rx="8" fill="rgba(255,255,255,0.5)"/>
    <rect x="{w-80}" y="32" width="45" height="32" rx="8" fill="rgba(255,255,255,0.5)"/>
    <circle cx="50" cy="78" r="14" fill="#333"/>
    <circle cx="50" cy="78" r="7" fill="#aaa"/>
    <circle cx="{w-50}" cy="78" r="14" fill="#333"/>
    <circle cx="{w-50}" cy="78" r="7" fill="#aaa"/>
    <rect x="{w//2-15}" y="42" width="30" height="18" rx="4" fill="rgba(255,255,255,0.7)"/>
</svg>'''


def _svg_person_agent(w=120, h=160):
    """扁平卡通人物（代理人/专业人士站姿）——用于误区卡左侧插图"""
    return f'''<svg viewBox="0 0 {w} {h}" width="{w}" height={h}" xmlns="http://www.w3.org/2000/svg">
    <circle cx="{w//2}" cy="28" r="22" fill="#FFD8A8"/>
    <circle cx="{w//2-7}" cy="24" r="2.5" fill="#333"/>
    <circle cx="{w//2+9}" cy="24" r="2.5" fill="#333"/>
    <path d="M{w//2-10}38 Q{w//2}44 {w//2+10}38" stroke="#333" stroke-width="2" fill="none" stroke-linecap="round"/>
    <rect x="{w//2-26}" y="54" width="52" height="60" rx="10" fill="{CBLUE}"/>
    <rect x="{w//2-26}" y="54" width="20" height="60" rx="10" fill="rgba(255,255,255,0.15)"/>
    <line x1="{w//2}" y1="54" x2="{w//2}" y2="114" stroke="rgba(255,255,255,0.3)" stroke-width="1"/>
    <rect x="{w//2-22}" y="114" width="18" height="36" rx="8" fill="#333"/>
    <rect x="{w//2+4}" y="114" width="18" height="36" rx="8" fill="#333"/>
    <rect x="{w//2-30}" y="58" width="36" height="46" rx="4" fill="white" stroke="#ddd" stroke-width="1"/>
    <line x1="{w//2-26}" y1="68" x2="{w//2+2}" y2="68" stroke="{CBLUE}" stroke-width="2"/>
    <line x1="{w//2-26}" y1="76" x2="{w//2+2}" y2="76" stroke="{CBLUE}" stroke-width="2"/>
    <line x1="{w//2-26}" y1="84" x2="{w//2+2}" y2="84" stroke="{CBLUE}" stroke-width="2"/>
    <line x1="{w//2-26}" y1="92" x2="{w//2+0}" y2="92" stroke="{CBLUE}" stroke-width="2"/>
</svg>'''


def _svg_car_simple(color, w=140, h=85):
    """更小的卡通车——用于场景卡顶部横排"""
    return f'''<svg viewBox="0 0 {w} {h}" width="{w}" height="{h}" xmlns="http://www.w3.org/2000/svg">
    <rect x="12" y="18" width="{w-24}" height="40" rx="14" fill="{color}"/>
    <rect x="22" y="24" width="34" height="24" rx="6" fill="rgba(255,255,255,0.5)"/>
    <rect x="{w-56}" y="24" width="34" height="24" rx="6" fill="rgba(255,255,255,0.5)"/>
    <circle cx="38" cy="64" r="11" fill="#333"/><circle cx="38" cy="64" r="5" fill="#aaa"/>
    <circle cx="{w-38}" cy="64" r="11" fill="#333"/><circle cx="{w-38}" cy="64" r="5" fill="#aaa"/>
</svg>'''


def cartoon_comparison(data):
    """S00-A 对比双栏卡 —— 两栏对比（如 座位险 vs 驾乘险）
    data: title/subtitle/highlight/left_label/right_label/left_items(list)/right_items(list)/footer
    """
    d = data
    li = d.get("left_items", [])
    ri = d.get("right_items", [])
    left_bullets = "".join(f'<li><span class="dot" style="background:{CBLUE}"></span>{x}</li>' for x in li)
    right_bullets = "".join(f'<li><span class="dot" style="background:{CORANGE}"></span>{x}</li>' for x in ri)

    return f'''<!DOCTYPE html><html><head><meta charset="utf-8"><style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:{W_COVER}px;height:{H_COVER}px;background:linear-gradient(180deg,#E8F4FC 0%,#F5FAFD 40%,#FFFFFF 100%);
font-family:{FONT};display:flex;align-items:center;justify-content:center;overflow:hidden}}
.card{{width:calc(100% - 48px);background:#fff;border-radius:24px;
padding:32px 28px 24px;box-shadow:0 4px 24px rgba(0,0,0,0.07)}}
.tit{{font-size:42px;font-weight:900;color:{CDARK};text-align:center;line-height:1.25;letter-spacing:-0.5px}}
.sub{{font-size:19px;color:{CGRAY};text-align:center;margin-top:8px;line-height:1.4}}
.hl-bar{{display:inline-block;background:{CORANGE};color:#fff;font-size:17px;font-weight:700;
padding:10px 24px;border-radius:20px;margin:18px auto 16px;text-align:center;width:fit-content}}
.visual{{display:flex;justify-content:center;gap:20px;margin:16px 0 12px;align-items:flex-end}}
.v-item{{text-align:center}}
.badge{{display:inline-block;padding:5px 16px;border-radius:12px;font-size:15px;font-weight:700;color:#fff;margin-bottom:8px}}
.badge-l{{background:{CBLUE}}}.badge-r{{background:{CORANGE}}}
.cols{{display:flex;gap:16px;margin-top:8px}}
.col{{flex:1;border-radius:16px;border:2.5px solid;padding:16px 16px 14px}}
.col-l{{border-color:{CBLUE};background:#F0F7FF}}
.col-r{{border-color:{CORANGE};background:#FFF5EE}}
.col-head{{display:inline-block;padding:6px 18px;border-radius:10px;font-size:16px;font-weight:700;color:#fff;margin-bottom:12px}}
.ch-l{{background:{CBLUE}}}.ch-r{{background:{CORANGE}}}
.col ul{{list-style:none;padding:0}}
.col li{{font-size:15px;color:#333;line-height:1.75;display:flex;align-items:flex-start;gap:8px}}
.dot{{width:8px;height:8px;border-radius:50%;flex-shrink:0;margin-top:7px}}
.amt{{color:{CORANGE};font-weight:700}}
.ft{{text-align:center;font-size:15px;color:#777;margin-top:16px;line-height:1.4}}
</style></head><body>
<div class="card">
<div class="tit">{d.get("title","标题在这里")}</div>
<div class="sub">{d.get("subtitle","副标题说明文字")}</div>
<div class="hl-bar">{d.get("highlight","核心一句话：关键信息提炼")}</div>
<div class="visual">
<div class="v-item"><div class="badge badge-l">{d.get("left_label","选项 A")}</div>{_svg_car("#F5C842", "", 170, 95)}</div>
<div class="v-item"><div class="badge badge-r">{d.get("right_label","选项 B")}</div>{_svg_car("#7DBAE8", "", 170, 95)}</div>
</div>
<div class="cols">
<div class="col col-l">
<div class="col-head ch-l">{d.get("left_label","选项 A")}</div>
<ul>{left_bullets}</ul></div>
<div class="col col-r">
<div class="col-head ch-r">{d.get("right_label","选项 B")}</div>
<ul>{right_bullets}</ul></div>
</div>
<div class="ft">{d.get("footer","总结：不是二选一，是互补搭配")}</div>
</div>
</body></html>'''


def cartoon_mythbust(data):
    """S00-B 误区纠错卡 —— 常见误区/避坑（如 投保误区）
    data: title/subtitle/myths[{title,desc,correction}]/cta_text
    """
    d = data
    myths = d.get("myths", [])
    myth_cards = ""
    for i, m in enumerate(myths):
        cor = m.get("correction", "")
        cor_html = f'<div class="cor-badge">{cor}</div>' if cor else ""
        myth_cards += f'''
<div class="err-card">
<div class="x-icon">✗</div>
<div class="err-body">
<div class="err-tit">{m.get("title","误区标题")}</div>
<div class="err-desc">{m.get("desc","误区描述文字")}</div>
{cor_html}
</div></div>'''

    return f'''<!DOCTYPE html><html><head><meta charset="utf-8"><style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:{W_COVER}px;height:{H_COVER}px;background:linear-gradient(175deg,#E8F4FC 0%,#EEF5FB 40%,#FFFFFF 100%);
font-family:{FONT};display:flex;align-items:center;justify-content:center;overflow:hidden}}
.card{{width:calc(100% - 44px);background:#fff;border-radius:24px;
padding:28px 24px 20px;box-shadow:0 4px 20px rgba(0,0,0,0.06)}}
.tit{{font-size:40px;font-weight:900;color:{CDARK};text-align:center;line-height:1.2}}
.tit .num{{color:{CBLUE}}}
.sub{{font-size:17px;color:{CGRAY};text-align:center;margin-top:6px}}
.main{{display:flex;gap:20px;margin-top:18px;align-items:flex-start}}
.illu{{flex:0 0 32%;display:flex;flex-direction:column;align-items:center;gap:4px}}
.content{{flex:1;min-width:0}}
.err-card{{display:flex;gap:10px;margin-bottom:14px;align-items:flex-start}}
.x-icon{{flex-shrink:0;width:36px;height:36px;border-radius:50%;
background:{CRED};color:#fff;font-size:20px;font-weight:700;display:flex;
align-items:center;justify-content:center;margin-top:2px}}
.err-body{{flex:1;background:#FAFBFC;border-radius:14px;padding:14px 16px;border:1.5px solid #Eef2f7}}
.err-tit{{font-size:16px;font-weight:700;color:{CBLUE};margin-bottom:4px;line-height:1.3}}
.err-desc{{font-size:14px;color:#555;line-height:1.55}}
.cor-badge{{display:inline-block;background:{CGREEN};color:#fff;font-size:13px;
font-weight:600;padding:4px 14px;border-radius:10px;margin-top:8px}}
.cta{{display:flex;align-items:center;gap:8px;background:{CGREEN};color:#fff;
font-size:15px;font-weight:700;padding:12px 22px;border-radius:12px;
margin-top:8px;width:fit-content;cursor:pointer}}
.cta::after{{content:"›";font-size:20px;font-weight:900;margin-left:4px}}
</style></head><body>
<div class="card">
<div class="tit">{d.get("title","<span class='num'>3</span>个高频投保误区")}</div>
<div class="sub">{d.get("subtitle","别以为有保险就够了吗？")}</div>
<div class="main">
<div class="illu">{_svg_person_agent(115, 150)}
<span style="font-size:12px;color:#888;text-align:center">专业解读</span>
</div>
<div class="content">{myth_cards}
<div class="cta">{d.get("cta_text","正确思路：先看场景，再定方案 ›")}</div>
</div>
</div>
</div>
</body></html>'''


def cartoon_scenario(data):
    """S00-C 分人群方案卡 —— 按人群/场景给方案
    data: title/subtitle/scenarios[{name,desc,type:"2col"/"banner"}]/summary
    """
    d = data
    scenarios = d.get("scenarios", [])
    scen_html = ""
    for s in scenarios:
        t = s.get("type", "2col")
        if t == "2col":
            scen_html += f'<div class="sc-card sc-2col"><div class="sc-name">{s.get("name","分类名")}</div><div class="sc-desc">{s.get("desc","方案描述")}</div></div>'
        elif t == "banner":
            bg = "#fff" if scenarios.index(s) % 2 == 0 else "rgba(255,255,255,0.9)"
            scen_html += f'<div class="sc-card sc-banner" style="background:{bg}"><div class="sc-name">{s.get("name","分类名")}</div><div class="sc-desc">{s.get("desc","方案描述")}</div></div>'
        else:
            scen_html += f'<div class="sc-card sc-full"><div class="sc-name">{s.get("name","分类名")}</div><div class="sc-desc">{s.get("desc","方案描述")}</div></div>'

    return f'''<!DOCTYPE html><html><head><meta charset="utf-8"><style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:{W_COVER}px;height:{H_COVER}px;background:linear-gradient(180deg,{CWARM} 0%,#FFFDF8 60%,#FFFFFF 100%);
font-family:{FONT};display:flex;align-items:center;justify-content:center;overflow:hidden}}
.card{{width:calc(100% - 44px);border-radius:24px;padding:28px 24px 20px}}
.tit{{font-size:38px;font-weight:900;color:{CDARK};text-align:center;line-height:1.2}}
.sub{{font-size:17px;color:{CGRAY};text-align:center;margin-top:6px;line-height:1.4}}
.top-cars{{display:flex;justify-content:center;gap:14px;margin:16px 0 12px;align-items:flex-end}}
.car-wrap{{text-align:center}}
.car-label{{font-size:12px;color:{CBLUE};font-weight:700;background:#E8F0FE;
padding:3px 10px;border-radius:8px;display:inline-block;margin-bottom:5px}}
.box{{background:{CBLUE};border-radius:20px;padding:20px 18px 16px}}
.sc-grid{{display:grid;grid-template-columns:1fr 1fr;gap:12px}}
.sc-card{{border-radius:14px;padding:14px 16px}}
.sc-2col{{background:#fff}}
.sc-banner{{grid-column:1/-1;display:flex;align-items:center;gap:14px}}
.sc-banner .sc-name{{white-space:nowrap;min-width:fit-content}}
.sc-full{{grid-column:1/-1;background:#fff}}
.sc-name{{font-size:17px;font-weight:800;color:{CBLUE};margin-bottom:4px;line-height:1.2}}
.sc-banner .sc-name{{font-size:18px;color:{CBLUE};background:#E8F0FE;
padding:10px 18px;border-radius:10px}}
.sc-desc{{font-size:14px;color:#334;line-height:1.55}}
.sc-banner .sc-desc{{color:#4a5568}}
.ft{{text-align:center;font-size:14px;color:#777;margin-top:14px;line-height:1.4}}
</style></head><body>
<div class="card">
<div class="tit">{d.get("title","最新分人群选购方案")}</div>
<div class="sub">{d.get("subtitle","不同情况，保障重点不一样")}</div>
<div class="top-cars">
<div class="car-wrap"><div class="car-label">家用</div>{_svg_car_simple("#E8925C", 125, 75)}</div>
<div class="car-wrap"><div class="car-label">营运</div>{_svg_car_simple("#F5C842", 125, 75)}</div>
<div class="car-wrap"><div class="car-label">通勤</div>{_svg_car_simple("#7DBAE8", 125, 75)}</div>
</div>
<div class="box"><div class="sc-grid">{scen_html}</div></div>
<div class="ft">{d.get("summary","总结：根据实际场景搭配，才能买对不买贵")}</div>
</div>
</body></html>'''


# ================================================================
# S41 笔记本手账长图固定式（Notebook Planner Longform · 第二固定风格）
# 来自公众号大号实战验证：政策解读/分级对比/复杂攻略/多点科普
# 特征：螺旋装订 + 卡通mascot + 蓝幅金字 + 编号观点块 + 表格 + 侧边备注
# ================================================================

# S41 配色常量
NB_BG     = "#EEF5FB"   # 笔记本纸张底色
NB_BLUE   = "#4A90D9"   # 蓝色主色（横幅/pill/边框/渐变）
NB_GOLD   = "#F5C842"   # 金黄标题字（仅在蓝底上使用）
NB_INK    = "#2D3748"   # 正文墨色
NB_GRAY   = "#666666"   # 次要文字
NB_SPIRAL = "#D4A853"   # 金色装订线圈
NB_TABLE_H1 = "#FFE0E0" # 表头-粉
NB_TABLE_H2 = "#FFF3E0" # 表头-橙
NB_TABLE_H3 = "#E8F5E9" # 表头-绿
NB_NOTE_Y = "#FFFDE7"   # 备注框-淡黄
NB_NOTE_R = "#FFF0F0"   # 提示框-淡红
NB_ANN_BG = "rgba(74,144,217,0.08)"  # 公告框填充


def notebook_longform(data):
    """S41 笔记本手账长图 —— 政策解读/分级对比/复杂攻略/多点科普
    data: title/mascot_desc/announcement/
          sections[{num, color("star"/"green"/"red"), icon(emoji), title, body,
                    table({headers[], rows[]}), note}] /
          summary/qrcode(bool)
    """
    d = data
    sections = d.get("sections", [])

    # 构建编号观点块
    sec_html = ""
    for i, s in enumerate(sections):
        num = s.get("num", i + 1)
        color_tag = s.get("color", "star")
        icon = s.get("icon", "📋")
        title = s.get("title", f"观点{num}")
        body = s.get("body", "")
        table_data = s.get("table", None)
        note = s.get("note", "")

        # 编号徽章样式
        if color_tag == "star":
            badge_style = f"background:{NB_GOLD};color:#fff;"
            badge_shape = "★"
        elif color_tag == "green":
            badge_style = f"background:{CGREEN};color:#fff;"
            badge_shape = "●"
        else:
            badge_style = f"background:{CRED};color:#fff;"
            badge_shape = "●"

        # 表格HTML
        table_html = ""
        if table_data:
            headers = table_data.get("headers", [])
            rows = table_data.get("rows", [])
            th_color = [NB_TABLE_H1, NB_TABLE_H2, NB_TABLE_H3][i % 3]
            th_row = "".join(f"<th>{h}</th>" for h in headers)
            td_rows = ""
            for r in rows:
                td_rows += "<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>"
            table_html = f"""
<div class="sec-table-wrap">
<table class="sec-table">
<thead style="background:{th_color}"><tr>{th_row}</tr></thead>
<tbody>{td_rows}</tbody>
</table></div>"""

        # 侧边备注
        note_html = ""
        if note:
            note_bg = NB_NOTE_R if color_tag == "red" else NB_NOTE_Y
            note_html = f'<div class="side-note" style="background:{note_bg}">💡 {note}</div>'

        sec_html += f"""
<div class="section-block">
  <div class="sec-header">
    <div class="sec-badge" style="{badge_style}">{badge_shape}{num}</div>
    <div class="sec-pill">{title}</div>
  </div>
  <div class="sec-body">
    <div class="sec-icon">{icon}</div>
    <div class="sec-text">
      <div class="sec-content">{body}</div>
      {table_html}
    </div>
  </div>
        {note_html}
</div>"""

    # ── 预生成动态片段（避免 f-string 内嵌套拼接导致代码泄露）─
    spiral_html = "\n".join('<div class="spiral-ring"></div>' for _ in range(18))

    # 二维码区
    qrcode_html = ""
    if d.get("qrcode"):
        qrcode_html = """
<div class="qr-area">
  <div class="qr-placeholder"></div>
  <div class="qr-text">扫码关注<br>获取更多干货</div>
</div>"""

    return f'''<!DOCTYPE html><html><head><meta charset="utf-8"><style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:{W_HAND}px;min-height:{H_HAND}px;background:{NB_BG};
font-family:"Microsoft YaHei","PingFang SC","Hiragino Sans GB",sans-serif;
position:relative;overflow:hidden;padding:50px 56px 40px 72px;color:{NB_INK};
-webkit-font-smoothing:antialiased}}

/* ── 左侧螺旋装订线 ── */
.spiral{{position:absolute;left:16px;top:30px;bottom:30px;width:28px;display:flex;flex-direction:column;gap:22px;pointer-events:none;}}
.spiral-ring{{width:28px;height:28px;border-radius:50%;
  border:3.5px solid {NB_SPIRAL};
  box-shadow:inset 2px 2px 4px rgba(0,0,0,0.15), 1px 1px 3px rgba(0,0,0,0.1);
  background:radial-gradient(circle at 35% 35%, rgba(255,255,255,0.4), transparent 60%);}}

/* ── 头部：Mascot + 蓝幅金字标题 ── */
.header{{display:flex;align-items:flex-start;gap:24px;margin-bottom:20px;position:relative;}}
.mascot{{flex:0 0 120px;width:120px;height:140px;display:flex;align-items:center;justify-content:center;}}
.title-banner{{flex:1;background:{NB_BLUE};border-radius:12px 16px 16px 4px;
  padding:24px 28px 20px;position:relative;box-shadow:0 4px 16px rgba(74,144,217,0.25);
  transform:rotate(-0.8deg);}}
.title-banner::after{{content:"";position:absolute;right:-8px;top:18px;
  width:24px;height:36px;background:{NB_BLUE};border-radius:0 8px 8px 0;
  transform:skewY(-15deg);opacity:0.7;}}
.main-title{{font-size:48px;font-weight:900;color:{NB_GOLD};line-height:1.2;
  letter-spacing:2px;text-shadow:2px 2px 0 rgba(0,0,0,0.1);}}

/* ── 装饰元素 ── */
.deco-star{{position:absolute;font-size:32px;color:{NB_GOLD};top:10px;right:20px;}}
.deco-clip{{position:absolute;font-size:36px;right:60px;top:50px;transform:rotate(15deg);}}
.deco-tape{{position:absolute;width:80px;height:22px;background:rgba(74,144,217,0.25);
  border-radius:2px;top:-8px;right:40px;transform:rotate(-3deg);}}
.deco-dots{{position:absolute;right:20px;top:100px;display:flex;flex-direction:column;gap:8px;}}
.deco-dot{{width:14px;height:14px;border-radius:50%;}}
.dot-y{{background:{NB_GOLD}}}.dot-b{{background:{NB_BLUE}}}.dot-p{{background:#E890D4}}

/* ── 公告框 ── */
.announcement{{border:2.5px dashed {NB_BLUE};border-radius:14px;
  background:{NB_ANN_BG};padding:18px 22px;margin-bottom:26px;
  display:flex;align-items:flex-start;gap:14px;transform:rotate(0.3deg);}}
.anno-icon{{font-size:34px;flex-shrink:0;line-height:1;}}
.anno-text{{font-size:26px;color:{NB_BLUE};line-height:1.55;font-weight:600;}}

/* ── 观点块 ── */
.section-block{{margin-bottom:28px;border-radius:16px;
  background:rgba(255,255,255,0.7);padding:20px 22px 18px;
  border:1.5px solid rgba(74,144,217,0.15);
  box-shadow:0 2px 10px rgba(0,0,0,0.04);position:relative;}}
.section-block::before{{content:"";
  position:absolute;top:-4px;left:24px;width:20px;height:8px;
  background:rgba(200,168,83,0.4);border-radius:4px;}}
.sec-header{{display:flex;align-items:center;gap:12px;margin-bottom:14px;}}
.sec-badge{{width:44px;height:44px;border-radius:50%;font-size:22px;font-weight:900;
  display:flex;align-items:center;justify-content:center;flex-shrink:0;
  box-shadow:0 2px 6px rgba(0,0,0,0.12);}}
.sec-pill{{background:{NB_BLUE};color:#fff;font-size:26px;font-weight:800;
  padding:8px 22px;border-radius:22px;letter-spacing:1px;}}
.sec-body{{display:flex;gap:16px;align-items:flex-start;}}
.sec-icon{{font-size:42px;flex-shrink:0;line-height:1;}}
.sec-text{{flex:1;min-width:0;}}
.sec-content{{font-size:25px;line-height:1.65;color:{NB_INK};margin-bottom:10px;}}

/* ── 表格 ── */
.sec-table-wrap{{margin-top:12px;border-radius:10px;overflow:hidden;
  border:1.5px solid #E0E0E0;}}
.sec-table{{width:100%;border-collapse:collapse;font-size:23px;}}
.sec-table th{{padding:12px 14px;text-align:left;font-weight:700;color:{NB_INK};}}
.sec-table td{{padding:10px 14px;border-bottom:1px solid #EEEFEF;color:{NB_INK};}}
.sec-table tr:last-child td{{border-bottom:none;}}
.sec-table tr:nth-child(even){{background:rgba(0,0,0,0.02);}}

/* ── 侧边备注 ── */
.side-note{{margin-top:12px;padding:12px 16px;border-radius:10px;
  font-size:21px;font-style:italic;color:{NB_GRAY};line-height:1.5;
  border-left:4px solid {NB_BLUE};}}

/* ── 底部总结区 ── */
.footer-bar{{margin-top:30px;background:linear-gradient(135deg,{NB_BLUE},#357ABD);
  border-radius:14px;padding:24px 28px;color:#fff;display:flex;align-items:center;justify-content:space-between;}}
.footer-text{{font-size:25px;font-weight:600;line-height:1.5;max-width:70%;}}
.footer-text .hl{{color:{NB_GOLD};font-weight:800;}}
.qr-area{{display:flex;align-items:center;gap:12px;}}
.qr-placeholder{{width:86px;height:86px;border-radius:8px;background:#fff;flex-shrink:0;}}
.qr-text{{font-size:18px;text-align:right;line-height:1.4;opacity:0.9;}}
</style></head><body>

<!-- 螺旋装订线 -->
<div class="spiral">
{spiral_html}
</div>

<!-- 散布装饰圆点 -->
<div class="deco-dots">
  <div class="deco-dot dot-y"></div>
  <div class="deco-dot dot-b"></div>
  <div class="deco-dot dot-p"></div>
</div>

<!-- 头部 -->
<div class="header">
  <div class="mascot">
    <!-- Mascot SVG: 眼镜男孩 P1 -->
    <svg viewBox="0 0 120 140" width="120" height="140">
      <ellipse cx="60" cy="132" rx="34" ry="6" fill="rgba(0,0,0,0.06)"/>
      <!-- 头 -->
      <circle cx="60" cy="42" r="32" fill="#FFE0BD"/>
      <!-- 头发 -->
      <path d="M30 38 Q28 18 48 14 Q60 10 72 14 Q92 18 90 38 Q88 28 76 24 Q60 20 44 24 Q32 28 30 38Z" fill="#3D2914"/>
      <!-- 眼镜 -->
      <rect x="36" y="36" width="20" height="16" rx="4" fill="none" stroke="#333" stroke-width="2.5"/>
      <rect x="64" y="36" width="20" height="16" rx="4" fill="none" stroke="#333" stroke-width="2.5"/>
      <line x1="56" y1="44" x2="64" y2="44" stroke="#333" stroke-width="2.5"/>
      <!-- 眼睛 -->
      <circle cx="46" cy="45" r="3" fill="#333"/><circle cx="74" cy="45" r="3" fill="#333"/>
      <!-- 嘴 -->
      <path d="M52 58 Q60 64 68 58" stroke="#333" stroke-width="2" fill="none" stroke-linecap="round"/>
      <!-- 身体(P1白衬衫) -->
      <rect x="34" y="74" width="52" height="48" rx="8" fill="#FFF"/>
      <rect x="34" y="74" width="52" height="14" rx="8" fill="{NB_BLUE}"/>
      <text x="60" y="85" font-size="13" fill="#fff" text-anchor="middle" font-weight="bold">P1</text>
      <!-- 领带 -->
      <path d="M54 88 L60 102 L66 88 Z" fill="{NB_RED if 'CRED' in dir() else '#EF4444'}"/>
    </svg>
  </div>
  <div class="title-banner">
    <div class="main-title">{d.get("title","标题在这里")}</div>
  </div>
  <div class="deco-star">⭐</div>
  <div class="deco-clip">📎</div>
  <div class="deco-tape"></div>
</div>

<!-- 公告框 -->
<div class="announcement">
  <div class="anno-icon">📢</div>
  <div class="anno-text">{d.get("announcement","核心摘要信息放在这里，让读者一眼抓住重点")}</div>
</div>

<!-- 观点块列表 -->
{sec_html}

<!-- 底部总结 -->
<div class="footer-bar">
  <div class="footer-text">{d.get("summary","总结：了解规则，才能选对保障方案。<span class='hl'>收藏备用</span> ›")}</div>
  {qrcode_html}
</div>

</body></html>'''


# ================================================================
# 渲染器
# ================================================================
def render(html, out, width, height=10):
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch(args=["--no-sandbox", "--disable-dev-shm-usage"])
        pg = b.new_page(viewport={"width": width, "height": height}, device_scale_factor=2)
        pg.set_content(html, wait_until="networkidle")
        pg.wait_for_timeout(350)
        pg.screenshot(path=out, full_page=True)
        b.close()
    print("[img] built", out)


# ================================================================
# 内置样例（证明设计能力；生产时替换为真实选题文案）
# ================================================================
SAMPLES = {
    # ---- 封面 6 范式 ----
    "cover_confession": (cover_confession, {
        "tag": "真实故事 · 经纪人手记",
        "title": '我爸走后第7天，<br>才在抽屉里翻到<br>那张<span class="hl">保单</span>',
        "sub": "如果那天他没提前安排，<br>我们可能连它的存在都不知道。",
    }),
    "cover_number": (cover_number, {
        "tag": "90% 的家庭都做错了",
        "number": "90", "unit": "%",
        "title": '买保险，<span class="hl">买错了顺序</span>',
        "sub": "先保谁？答案可能和你想的相反",
    }),
    "cover_question": (cover_question, {
        "title": '如果明天你<span class="hl">不在了</span>，<br>家人找得到<br>那份保单吗？',
        "foot": "· 值得今晚就想一想 ·",
    }),
    "cover_contrast": (cover_contrast, {
        "top": "同样一场重疾，两个结局",
        "left": {"label": "没规划", "desc": "东拼西凑，<br>卖房凑药费"},
        "right": {"label": "有规划", "desc": "一通电话，<br>88万到账"},
    }),
    "cover_checklist": (cover_checklist, {
        "kicker": "建议收藏 · 投保避坑",
        "title": '买保险前<br><span class="hl">必看 3 件事</span>',
        "items": ["搞懂自己先该保什么", "看清条款里的免责", "留好家人的对接人"],
        "foot": "没搞懂这 3 条，先别急着下单",
    }),
    "cover_story": (cover_story, {
        "tag": "真实故事",
        "title": '她把最后一份礼物，<br>藏进了一张<span class="hl">保单</span>里',
        "sub": "妈妈没多说什么，<br>却把往后十年都替孩子安排好了。",
    }),
    # ---- 手绘 4 范式 ----
    "hand_steps": (hand_steps, {
        "title": "家庭保单配置顺序",
        "hint": "先大人后小孩，先保障后理财",
        "steps": [
            {"t": "先保家里的顶梁柱", "d": "谁赚钱最多，谁先配足——他倒下，全家才不倒。"},
            {"t": "再补孩子和老人", "d": "孩子重点是医疗+重疾，老人重点是意外+医疗。"},
            {"t": "先买保障型", "d": "重疾/医疗/意外/寿险配齐了，再谈存钱理财。"},
            {"t": "最后考虑理财型", "d": "有余力再配年金/增额，别本末倒置。"},
        ],
    }),
    "hand_vs": (hand_vs, {
        "title": "买对顺序 vs 买错顺序",
        "hint": "同样的预算，效果差一大截",
        "left": {"head": "买错 ✗", "items": ["先给孩子买一堆", "大人裸奔没保障", "预算全砸在理财险", "真出事赔不够"]},
        "right": {"head": "买对 ✓", "items": ["先保赚钱的大人", "保障型优先配齐", "余钱再谈理财", "出事有底气"]},
    }),
    "hand_checklist": (hand_checklist, {
        "title": "投保前自检 5 问",
        "hint": "对着勾一遍，缺哪补哪",
        "items": [
            {"t": "顶梁柱的寿险+重疾够不够？", "hl": "顶梁柱"},
            {"t": "医疗险能不能覆盖大病自费？", "hl": "大病自费"},
            {"t": "意外险给全家都配了吗？", "hl": "全家"},
            {"t": "受益人写的是具体人名吗？", "hl": "具体人名"},
            {"t": "家人知道去哪找保单吗？", "hl": "找保单"},
        ],
        "foot": "5 个都打勾，才算真配齐",
    }),
    "hand_map": (hand_map, {
        "title": "一个家庭的保障网",
        "core": {"t": "一个家", "d": "4 张保单各管一摊"},
        "nodes": [
            {"t": "重疾险", "d": "确诊即赔，补收入损失"},
            {"t": "医疗险", "d": "报销高额住院费"},
            {"t": "意外险", "d": "意外伤残身故兜底"},
            {"t": "寿险", "d": "顶梁柱倒下留爱不留债"},
        ],
    }),
    # ---- 新增风格家族（归档库） ----
    "cover_dazibao": (cover_dazibao, {
        "title": '别再乱买！<br>保险<span class="hl">顺序</span><br>搞反了',
        "sub": "先保赚钱的人，再保孩子",
        "foot": "· 句句大实话 ·",
    }),
    "cover_neon": (cover_neon, {
        "kicker": "夜话 · 保障",
        "title": '25岁<br>该不该<br>买<span class="pink">重疾</span>',
        "sub": "年轻人的第一份保单怎么选",
    }),
    "cover_guofeng": (cover_guofeng, {
        "title": '留爱<br>不<span class="hl">留债</span>',
        "sub": "东方家庭的安全感，<br>是一份提前的安排。",
        "foot": "· 东方家庭的安全感 ·",
    }),
    "cover_davinci": (cover_davinci, {
        "title": '一张保单，<br>如何<span class="hl">托住</span>一个家',
        "sub": "从结构看清保障的四根支柱。",
        "note": "fig. 保险之结构",
    }),
    "cover_magazine": (cover_magazine, {
        "kicker": "封面故事",
        "title": '她把礼物<br>藏进了<span class="hl">保单</span>',
        "sub": "一位母亲，替孩子安排好的十年。",
        "foot": "编辑部 · 用专业守护每一个家",
    }),
    "cover_memphis": (cover_memphis, {
        "title": '省钱<br>配齐<span class="hl">一家</span><span class="bl">三口</span>',
        "sub": "300块也能配出基础保障",
    }),
    "cover_knowledge": (cover_knowledge, {
        "kicker": "知识卡片",
        "icon": "📌",
        "title": '买保险前<br><span class="hl">必看 3 件事</span>',
        "desc": "搞懂先保谁 · 看清免责 · 留好对接人。",
        "tag": "建议收藏 · 随时翻看",
    }),
    "cover_mondrian": (cover_mondrian, {
        "title": '保障<br>四块<span class="hl">拼图</span>',
        "sub": "重疾·医疗·意外·寿险",
    }),
    # ---- 补齐至全 40 式 ----
    "cover_illustration": (cover_illustration, {
        "title": '买保险前<br>先搞懂<span class="hl">这件事</span>',
        "sub": "别让辛苦钱白交",
    }),
    "cover_doodle": (cover_doodle, {
        "title": '保险<span class="hl">不是</span>骗人的<br>但得买对',
        "sub": "—— 一个保险经纪人的大白话",
    }),
    "cover_storybook": (cover_storybook, {
        "title": '爸爸的<span class="hl">礼物</span>',
        "sub": "藏在保单里的爱",
    }),
    "hand_longinfo": (hand_longinfo, {
        "title": "家庭保障 这样做",
        "blocks": [
            {"t": "先保顶梁柱", "d": "谁赚钱最多，谁先配足。"},
            {"t": "再保孩子老人", "d": "医疗+重疾优先。"},
            {"t": "先保障后理财", "d": "配齐了再谈存钱。"},
            {"t": "留好对接人", "d": "出事有人办，不抓瞎。"},
        ],
    }),
    "cover_quote": (cover_quote, {
        "title": '保险留不住人，<br>但能<span class="hl">留爱</span>',
        "sub": "— 一位保险经纪人的手记",
    }),
    "cover_minimal": (cover_minimal, {
        "title": '<span class="hl">兜底</span>',
        "sub": "· 一句就够了 ·",
    }),
    "cover_newspaper": (cover_newspaper, {
        "title": '别让一场病<br>拖垮一个家',
        "sub": "近年来，因病致贫的案例屡见不鲜。家庭保障已成刚需：先保赚钱的人，再保孩子，先保障后理财。",
    }),
    "cover_collage": (cover_collage, {
        "title": '保障<br>怎么<span class="hl">配</span>',
        "sub": "一张图看懂家庭保单顺序",
    }),
    "cover_retro": (cover_retro, {
        "kicker": "RETRO · 老故事",
        "title": '当年那份<br><span class="hl">安排</span>',
        "sub": "如今看来，是最稳的托付",
    }),
    "cover_swiss": (cover_swiss, {
        "kicker": "SWISS GRID",
        "title": '保障<br><span class="hl">四支柱</span>',
        "sub": "重疾·医疗·意外·寿险",
    }),
    "cover_inkwash": (cover_inkwash, {
        "title": "留爱不留债",
        "sub": "未雨绸缪",
    }),
    "cover_letterpress": (cover_letterpress, {
        "title": "未雨绸缪",
    }),
    "cover_dunhuang": (cover_dunhuang, {
        "title": '守护<br>万家灯火',
        "sub": "一份保障，一份安心",
    }),
    "cover_jieqi": (cover_jieqi, {
        "kicker": "节 气 · 民 生",
        "title": '入秋了<br>给爸妈<span class="hl">加一道</span>',
        "sub": "秋冬季，别忘了这重保障",
    }),
    "cover_blueprint": (cover_blueprint, {
        "title": '家庭保障<br><span class="hl">结构图</span>',
        "sub": "— 方案结构图 —",
    }),
    "cover_science": (cover_science, {
        "title": '读懂<br><span class="hl">重疾</span>条款',
        "sub": "图：保障结构示意",
    }),
    "cover_charcoal": (cover_charcoal, {
        "title": '他不在的<br>那些年',
        "sub": "一份保单，替他守着家",
    }),
    "cover_abstract_min": (cover_abstract_min, {
        "title": '<span class="hl">安全</span>感',
        "sub": "SHIELD",
    }),
    "cover_fluid": (cover_fluid, {
        "title": '让保障<br><span class="hl">温柔</span>落地',
        "sub": "为每个家庭，定制安心",
    }),
    "cover_pop": (cover_pop, {
        "title": '买保险<br>别<span class="hl">踩坑</span>',
        "sub": "3步避开90%的坑",
    }),
    "cover_dreamcore": (cover_dreamcore, {
        "title": '未来<br><span class="hl">不设限</span>',
        "sub": "Z世代的第一次规划",
    }),
    "cover_film": (cover_film, {
        "title": '那年<br>他留下的<span class="hl">话</span>',
        "sub": "REC · 1998 · 家庭",
    }),
    "cover_flatlay": (cover_flatlay, {
        "title": '一家人的<br><span class="hl">保障包</span>',
    }),
    "cover_scene": (cover_scene, {
        "tag": "真实场景",
        "title": '深夜急诊<br>幸好<span class="hl">有它</span>',
        "sub": "那一刻，才懂保障的意义",
    }),
    "cover_datashot": (cover_datashot, {
        "kicker": "理赔实录 · 脱敏",
        "a": "重疾理赔", "b": "88 万", "c": "3 天到账",
        "sub": "* 以保险公司核定为准",
    }),

    # ── S00 卡通知识卡（固定式）─────────────────────────────
    "cartoon_comparison": (cartoon_comparison, {
        "title": "重疾险别只看保额",
        "subtitle": "保额保收入，保障保全责，二者要搭配",
        "highlight": "核心一句话：保额管赔多少，全责管能不能赔",
        "left_label": "只买消费型",
        "right_label": "含身故责任",
        "left_items": [
            "纯保疾病/轻症/中症",
            "保费低，杠杆高",
            "身故不赔（退现金价值）",
            "<span class='amt'>适合：预算有限</span>",
            "理财影响小",
        ],
        "right_items": [
            "疾病 + 身故都覆盖",
            "不挑责任归属",
            "身故直接赔保额",
            "<span class='amt'>百元可获50—100万</span>",
            "理赔不影响其他",
        ],
        "footer": "不是二选一，是按预算灵活搭配",
    }),
    "cartoon_mythbust": (cartoon_mythbust, {
        "title": "<span class='num'>3</span>个高频投保误区",
        "subtitle": "别以为买了保险就万事大吉",
        "myths": [
            {
                "title": "误区1：有社保就够了",
                "desc": "社保只报医保目录内，进口药/自费项目不报，大病自费部分可能高达数十万",
                "correction": "商保补充社保缺口",
            },
            {
                "title": "误区2：先给孩子买，大人再说",
                "desc": "大人才是家庭经济支柱，大人倒下全家断粮。孩子病了大人还能赚，大人病了谁来养？",
                "correction": "先大人后小孩",
            },
            {
                "title": "误区3：返还型更划算",
                "desc": "返还型的「返」其实是你自己多交的钱，几十年后的购买力已大幅缩水",
                "correction": "",
            },
        ],
        "cta_text": "正确思路：先保大人→再保小孩→先保定期→预算宽再考虑终身 ›",
    }),
    "cartoon_scenario": (cartoon_scenario, {
        "title": "不同收入怎么配保险",
        "subtitle": "收入不同，配置重点不一样",
        "scenarios": [
            {"name": "月入 5K 以下", "desc": "百万医疗+意外险+定期寿险\n先守住底线，年预算 1000 内", "type": "2col"},
            {"name": "月入 5K-1.5W", "desc": "医疗+重疾(30-50万)+定寿+意外\n核心保障配齐，年预算 3000-8000", "type": "2col"},
            {"name": "家庭经济支柱", "desc": "重疾50万起+定寿(年收入5-10倍)\n顶梁柱保障必须拉满", "type": "banner"},
            {"name": "预算充足", "desc": "重疾+终身寿险+教育金\n全方位覆盖无死角", "type": "banner"},
        ],
        "summary": "总结：量入为出、先急后缓，按收入阶梯逐步完善",
    }),

    # ── S41 笔记本手账长图（固定式）────────────────────────────
    "notebook_longform": (notebook_longform, {
        "title": "保险分级制度\n正式落地",
        "mascot_desc": "眼镜男孩 P1",
        "announcement": "从2026年7月1日起，《保险产品适当性管理自律规范》正式实施。其核心是「保险产品分级+销售人员分级+客户分级」的「三级匹配」。",
        "sections": [
            {
                "num": 1,
                "color": "star",
                "icon": "📋",
                "title": "产品分级更精细，风险描述更完整",
                "body": "根据产品的复杂程度和保单利益的确定性，将人身保险产品划分为五个等级，并对P4、P5类产品进一步划分风险等级R1-R5。",
                "table": {
                    "headers": ["产品等级(P类)", "特征说明"],
                    "rows": [
                        ["P1类", "低复杂程度、保单利益确定的产品（如一年期及以下短期健康险、意外险）"],
                        ["P2类", "中等复杂程度、保单利益确定的普通型期交产品（如重疾险、定期寿险）"],
                        ["P3类", "中等复杂程度、保单利益不动的年金保险产品（如分红险、万能险）"],
                        ["P4类", "中高复杂程度且利益浮动无保证的产品（如投连保险）"],
                        ["P5类", "高复杂程度且保单利益浮动无保证的产品（如未来更多复杂产品预留空间）"],
                    ],
                },
                "note": "特别提示：P4、P5类产品需进行一步划分风险等级，R1（低风险）至 R5（高风险）。",
            },
            {
                "num": 2,
                "color": "green",
                "icon": "🏃",
                "title": "销售人员分级管理，可售范围更清晰",
                "body": "销售人员能力等级从四级到一级，等级越高，可销售的产品范围越广。",
                "table": {
                    "headers": ["能力等级", "可销售的产品范围"],
                    "rows": [
                        ["四级", "可销售 P1、P2 类产品"],
                        ["三级", "可销售 P1、P2、P3 类产品"],
                        ["二级", "可销售 P1、P2、P3、P4 类产品"],
                        ["一级", "可销售 P1、P2、P3、P4、P5 类产品（全品类）"],
                    ],
                },
                "note": "注意：销售人员能力分制度目前仅发布征求意见稿，最终标准和培训、考试要求尚未正式实施。",
            },
            {
                "num": 3,
                "color": "red",
                "icon": "📊",
                "title": "客户评估更全面，匹配规则更科学",
                "body": "销售人员在销售前需对客户进行FNA评估，了解客户的投资需求与财务支付水平。\n\nP4、P5类产品还需评估客户的风险承受能力。",
                "table": {
                    "headers": ["FNA评估内容(包括但不限于)", ""],
                    "rows": [
                        ["保险保障需求", ""],
                        ["交费期限和期间", ""],
                        ["收入来源", ""],
                        ["财务实力等", ""],
                    ],
                },
                "note": "",
            },
        ],
        "summary": "《保险产品适当性管理自律规范》的发布，意味着中国保险业在销售流程方面的进一步完善。可以确保销售人员推荐给客户的产品金额与客户的实际需求与支付能力相匹配。并以此推动销售误导与投诉纠纷，推动行业从「以产品销售为中心」向「以客户需求为中心」转型，实现高质量发展。",
        "qrcode": True,
    }),
}


def build_all():
    for name, (fn, data) in SAMPLES.items():
        is_hand = name.startswith("hand_")
        w = W_HAND if is_hand else W_COVER
        out = os.path.join(ASSET, f"{name}.png")
        render(fn(data), out, w)
    print(f"ALL DONE — {len(SAMPLES)} images built into {ASSET}")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", help="只渲染指定范式（逗号分隔），如 cover_confession,hand_steps")
    args = ap.parse_args()
    if args.only:
        keys = [k.strip() for k in args.only.split(",")]
        for k in keys:
            if k in SAMPLES:
                fn, data = SAMPLES[k]
                w = W_HAND if k.startswith("hand_") else W_COVER
                render(fn(data), os.path.join(ASSET, f"{k}.png"), w)
            else:
                print("[skip] unknown:", k)
    else:
        build_all()
