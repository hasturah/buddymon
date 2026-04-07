"""
BuddyMon
========
A Gen V animated Pokémon desktop buddy for Windows.

Three Kanto starter lines with full evolutions, 1-in-100 shiny chance,
12 animated move effects, and a Professor Oak-inspired selection screen.

Usage
-----
    python buddymon.py

Right-click the sprite on your taskbar to access all controls.
"""

try:
    from PIL import Image, ImageTk
except ImportError:
    import subprocess, sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "Pillow"])
    from PIL import Image, ImageTk

import tkinter as tk
import urllib.request, os, sys, random, math

# ═══════════════════════════════════════════════════════════════════════════════
#  Config
# ═══════════════════════════════════════════════════════════════════════════════
DIR          = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sprites")
os.makedirs(DIR, exist_ok=True)

TRANSPARENT  = "#FF00FF"
TASKBAR_H    = 48
GRAVITY      = 0.8
WALK_SPEED   = 1.5
FRAME_MS     = 50            # 20 fps
SCALE        = 2
SHINY_CHANCE = 100           # 1-in-N

GEN5_URL  = ("https://raw.githubusercontent.com/PokeAPI/sprites/master"
             "/sprites/pokemon/versions/generation-v/black-white/animated/{}.gif")
SHINY_URL = ("https://raw.githubusercontent.com/PokeAPI/sprites/master"
             "/sprites/pokemon/versions/generation-v/black-white/animated/shiny/{}.gif")


# ═══════════════════════════════════════════════════════════════════════════════
#  Starter data
# ═══════════════════════════════════════════════════════════════════════════════
STARTER_LINES = [
    {
        "type": "Grass", "color": "#4CAF50",
        "evolutions": [
            {"id": 1, "name": "Bulbasaur"},
            {"id": 2, "name": "Ivysaur"},
            {"id": 3, "name": "Venusaur"},
        ],
        "moves": [
            {"name": "Vine Whip",    "fx": "vine_whip"},
            {"name": "Razor Leaf",   "fx": "razor_leaf"},
            {"name": "Solar Beam",   "fx": "solar_beam"},
            {"name": "Sleep Powder", "fx": "sleep_powder"},
        ],
    },
    {
        "type": "Fire", "color": "#FF5722",
        "evolutions": [
            {"id": 4, "name": "Charmander"},
            {"id": 5, "name": "Charmeleon"},
            {"id": 6, "name": "Charizard"},
        ],
        "moves": [
            {"name": "Ember",        "fx": "ember"},
            {"name": "Flamethrower", "fx": "flamethrower"},
            {"name": "Dragon Rage",  "fx": "dragon_rage"},
            {"name": "Scratch",      "fx": "scratch"},
        ],
    },
    {
        "type": "Water", "color": "#2196F3",
        "evolutions": [
            {"id": 7, "name": "Squirtle"},
            {"id": 8, "name": "Wartortle"},
            {"id": 9, "name": "Blastoise"},
        ],
        "moves": [
            {"name": "Water Gun",    "fx": "water_gun"},
            {"name": "Bubble",       "fx": "bubble"},
            {"name": "Bite",         "fx": "bite"},
            {"name": "Withdraw",     "fx": "withdraw"},
        ],
    },
]

ALL_IDS = [evo["id"] for line in STARTER_LINES for evo in line["evolutions"]]


# ═══════════════════════════════════════════════════════════════════════════════
#  Sprite helpers
# ═══════════════════════════════════════════════════════════════════════════════
def sprite_path(pid: int, shiny: bool) -> str:
    return os.path.join(DIR, f"{pid}{'_s' if shiny else ''}.gif")


def ensure_sprite(pid: int, shiny: bool = False) -> str:
    path = sprite_path(pid, shiny)
    if os.path.exists(path):
        return path
    url = (SHINY_URL if shiny else GEN5_URL).format(pid)
    tag = f"{'shiny ' if shiny else ''}#{pid}"
    print(f"  Downloading {tag}...", flush=True)
    req = urllib.request.Request(
        url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as r, open(path, "wb") as f:
            f.write(r.read())
    except Exception as exc:
        print(f"  Warning: could not download {tag}: {exc}", flush=True)
        if os.path.exists(path):
            os.remove(path)
    return path


def load_frames(path: str, scale: int = SCALE):
    """Load an animated GIF into mirrored left/right PhotoImage lists."""
    src = Image.open(path)
    rights, lefts = [], []

    def bake(frame: Image.Image) -> Image.Image:
        base = Image.new("RGBA", frame.size, (255, 0, 255, 255))
        fr   = frame.convert("RGBA")
        base.paste(fr, mask=fr.split()[3])
        img  = base.convert("RGB")
        if scale != 1:
            img = img.resize((img.width * scale, img.height * scale), Image.NEAREST)
        return img

    try:
        while True:
            img = bake(src.copy())
            rights.append(ImageTk.PhotoImage(img))
            lefts.append(ImageTk.PhotoImage(img.transpose(Image.FLIP_LEFT_RIGHT)))
            src.seek(src.tell() + 1)
    except EOFError:
        pass

    if not rights:
        img = bake(Image.open(path))
        rights = [ImageTk.PhotoImage(img)]
        lefts  = [ImageTk.PhotoImage(img.transpose(Image.FLIP_LEFT_RIGHT))]

    return rights, lefts, rights[0].width(), rights[0].height()


# ═══════════════════════════════════════════════════════════════════════════════
#  Particle
# ═══════════════════════════════════════════════════════════════════════════════
class Particle:
    __slots__ = ("x", "y", "vx", "vy", "life", "max_life", "color", "size", "grav")

    def __init__(self, x, y, vx, vy, life, color, size=4, grav=0.15):
        self.x = x;  self.y = y
        self.vx = vx; self.vy = vy
        self.life = life; self.max_life = life
        self.color = color; self.size = size; self.grav = grav

    def step(self):
        self.x += self.vx; self.y += self.vy
        self.vy += self.grav; self.life -= 1

    def draw(self, c):
        s = max(1, self.size * self.life / self.max_life)
        c.create_oval(self.x - s, self.y - s, self.x + s, self.y + s,
                      fill=self.color, outline="")


# ═══════════════════════════════════════════════════════════════════════════════
#  Move Effect Overlay
# ═══════════════════════════════════════════════════════════════════════════════
EFX_W, EFX_H = 540, 440


class MoveEffect:
    """Temporary transparent overlay window that animates a Pokémon move effect."""
    FRAMES = 44

    def __init__(self, root, sx: int, sy: int, sw: int, sh: int, fx: str, facing: int):
        self.root    = root
        self.fx      = fx
        self.facing  = facing
        self.frame   = 0
        self.parts   = []
        self.leaves  = []   # razor_leaf — drawn as leaf polygons
        self.bubbles = []   # (x, y, vy, r, life, max_life)

        wx = max(0, sx + sw // 2 - EFX_W // 2)
        wy = max(0, sy + sh // 2 - EFX_H // 2)

        self.win = tk.Toplevel(root)
        self.win.overrideredirect(True)
        self.win.attributes("-topmost", True)
        self.win.attributes("-transparentcolor", TRANSPARENT)
        self.win.configure(bg=TRANSPARENT)
        for attr in ("-toolwindow", "-disabled"):
            try: self.win.wm_attributes(attr, True)
            except tk.TclError: pass

        self.win.geometry(f"{EFX_W}x{EFX_H}+{wx}+{wy}")
        self.c = tk.Canvas(self.win, width=EFX_W, height=EFX_H,
                           bg=TRANSPARENT, highlightthickness=0)
        self.c.pack()

        # Sprite centre in canvas-local coordinates
        self.cx = sx + sw // 2 - wx
        self.cy = sy + sh // 2 - wy
        self._tick()

    # ── Helpers ───────────────────────────────────────────────────────────────
    def _burst(self, n, colors, spd=3, spread=math.pi, angle=None,
               life=20, size=4, grav=0.15):
        if angle is None:
            angle = 0 if self.facing == 1 else math.pi
        for _ in range(n):
            a = angle + random.uniform(-spread / 2, spread / 2)
            v = random.uniform(spd * 0.5, spd)
            self.parts.append(Particle(
                self.cx + random.randint(-4, 4),
                self.cy + random.randint(-4, 4),
                math.cos(a) * v, math.sin(a) * v,
                random.randint(life // 2, life),
                random.choice(colors),
                random.randint(2, size), grav,
            ))

    # ── Main tick ─────────────────────────────────────────────────────────────
    def _tick(self):
        try:
            if not self.win.winfo_exists():
                return
        except tk.TclError:
            return

        c, f = self.c, self.frame
        c.delete("all")
        cx, cy, facing = self.cx, self.cy, self.facing

        # ── Spawn logic ───────────────────────────────────────────────────────
        if self.fx == "razor_leaf" and f < 24 and f % 4 == 0:
            for _ in range(2):
                a = (0 if facing == 1 else math.pi) + random.uniform(-0.5, 0.5)
                s = random.uniform(5, 9)
                self.leaves.append(Particle(cx, cy, math.cos(a) * s, math.sin(a) * s,
                    30, random.choice(["#4CAF50","#66BB6A","#A5D6A7","#1B5E20"]),
                    8, grav=0.0))

        elif self.fx == "solar_beam" and f < 20:
            a    = random.uniform(0, 2 * math.pi)
            dist = random.uniform(55, 165)
            px, py = cx + math.cos(a) * dist, cy + math.sin(a) * dist
            self.parts.append(Particle(px, py, (cx - px) / 20, (cy - py) / 20,
                20, random.choice(["#FFD700","#FFF176","#FFEE58"]), 3, grav=0.0))

        elif self.fx == "sleep_powder" and f < 28 and f % 2 == 0:
            self._burst(2, ["#CE93D8","#BA68C8","#F48FB1","#80CBC4"],
                        spd=2.5, spread=math.pi * 1.6, angle=-math.pi / 2,
                        life=32, size=6, grav=0.02)

        elif self.fx == "ember" and f < 22:
            self._burst(3, ["#FF5722","#FF7043","#FFAB40","#FFD740"],
                        spd=4, spread=math.pi * 0.7, angle=-math.pi / 2,
                        life=18, size=5, grav=0.2)

        elif self.fx == "flamethrower" and f < 30:
            self._burst(5, ["#FF5722","#FF7043","#FF9800","#FFEB3B"],
                        spd=7, spread=0.35, life=15, size=7, grav=0.05)

        elif self.fx == "water_gun" and f < 26:
            self._burst(4, ["#1565C0","#1976D2","#42A5F5","#90CAF9"],
                        spd=7, spread=0.22, life=18, size=5, grav=0.3)

        elif self.fx == "bubble" and f % 6 == 0 and f < 32:
            for _ in range(2):
                self.bubbles.append([
                    float(cx + random.randint(-25, 25)), float(cy),
                    random.uniform(-1.6, -0.9),
                    random.randint(8, 15), 38, 38,
                ])

        elif self.fx == "bite" and f < 8:
            self._burst(6, ["#212121","#37474F","#78909C"],
                        spd=3, spread=math.pi * 2, life=12, size=4, grav=0.0)

        elif self.fx == "withdraw" and f % 5 == 0 and f < 22:
            for _ in range(3):
                a = random.uniform(0, 2 * math.pi)
                r = random.uniform(18, 40)
                self.parts.append(Particle(
                    cx + math.cos(a) * r, cy + math.sin(a) * r,
                    math.cos(a) * 0.4, math.sin(a) * 0.4,
                    22, random.choice(["#A5D6A7","#4CAF50","#1B5E20"]),
                    3, grav=0.0))

        # ── Update & draw circle particles ────────────────────────────────────
        alive = []
        for p in self.parts:
            p.step()
            if p.life > 0:
                p.draw(c); alive.append(p)
        self.parts = alive

        # ── Update & draw leaf particles ──────────────────────────────────────
        alive_l = []
        for p in self.leaves:
            p.step()
            if p.life > 0:
                a = math.atan2(p.vy, p.vx)
                pts = []
                for da, r in ((a, p.size * 2.8), (a + 2.4, p.size),
                              (a + math.pi, p.size * 2.8), (a - 2.4, p.size)):
                    pts += [p.x + math.cos(da) * r, p.y + math.sin(da) * r]
                c.create_polygon(pts, fill=p.color, outline="")
                alive_l.append(p)
        self.leaves = alive_l

        # ── Update & draw bubbles ─────────────────────────────────────────────
        alive_b = []
        for b in self.bubbles:
            bx, by, bvy, br, bl, bml = b
            by += bvy; bl -= 1
            if bl > 0:
                ar = max(2, int(br * bl / bml))
                c.create_oval(bx - ar, by - ar, bx + ar, by + ar,
                              outline="#42A5F5", width=2, fill="")
                alive_b.append([bx, by, bvy, br, bl, bml])
        self.bubbles = alive_b

        # ── Special vector drawings ───────────────────────────────────────────
        if self.fx == "vine_whip":
            ext = min(1.0, f / 12) * max(0.0, 1.0 - (f - 28) / 12)
            for sign in (1, -1):
                pts = [(cx, cy)]
                for seg in range(6):
                    prog = (seg + 1) / 6 * ext
                    x = cx + facing * prog * 200
                    y = (cy + sign * prog * 55
                         + math.sin(f * 0.4 + seg * 1.3) * 14 * prog)
                    pts.append((x, y))
                vcols = ["#1B5E20","#2E7D32","#388E3C","#43A047","#66BB6A","#A5D6A7"]
                for i in range(len(pts) - 1):
                    c.create_line(pts[i][0], pts[i][1], pts[i+1][0], pts[i+1][1],
                                  fill=vcols[i], width=max(1, 5 - i),
                                  capstyle=tk.ROUND)

        elif self.fx == "solar_beam":
            if f >= 20:
                bp   = (f - 20) / 24
                blen = bp * 340
                bw   = max(5, int(7 + bp * 18))
                x2   = cx + facing * blen
                c.create_line(cx, cy, x2, cy, fill="#FDD835",
                              width=bw, capstyle=tk.ROUND)
                c.create_line(cx, cy, x2, cy, fill="#FFFDE7",
                              width=max(2, bw - 5), capstyle=tk.ROUND)
            else:
                r = 10 + f * 1.9
                c.create_oval(cx - r, cy - r, cx + r, cy + r,
                              outline="#FDD835", width=2)

        elif self.fx == "dragon_rage":
            for ring in range(3):
                t = (f - ring * 7) * 2.2
                if 0 < t < 80:
                    r   = t * 2.2
                    col = ["#AB47BC", "#7E57C2", "#E040FB"][ring]
                    c.create_oval(cx - r, cy - r, cx + r, cy + r,
                                  outline=col, width=3)

        elif self.fx == "scratch" and f < 16:
            slashes = [
                (cx - 8,  cy - 28, cx + 26, cy + 9),
                (cx,      cy - 22, cx + 34, cy + 15),
                (cx + 8,  cy - 16, cx + 42, cy + 21),
            ]
            for x1, y1, x2, y2 in slashes:
                if facing == -1:
                    x1 = cx - (x1 - cx); x2 = cx - (x2 - cx)
                c.create_line(x1, y1, x2, y2, fill="#FFFFFF",
                              width=3, capstyle=tk.ROUND)
                c.create_line(x1, y1, x2, y2, fill="#FFEE58",
                              width=1, capstyle=tk.ROUND)

        elif self.fx == "bite" and f < 15:
            gap = max(0, (15 - f) * 3)
            c.create_arc(cx - 32, cy - 32 - gap, cx + 32, cy - gap,
                         start=0,   extent=180, outline="#EF5350",
                         width=3, style=tk.ARC)
            c.create_arc(cx - 32, cy + gap, cx + 32, cy + 32 + gap,
                         start=180, extent=180, outline="#EF5350",
                         width=3, style=tk.ARC)

        elif self.fx == "withdraw" and f < 28:
            r = 22 + f * 0.65
            c.create_oval(cx - r, cy - r, cx + r, cy + r,
                          outline="#A5D6A7", width=2)
            if f < 20:
                c.create_line(cx - r * 0.7, cy, cx + r * 0.7, cy,
                              fill="#81C784", width=1)
                c.create_line(cx, cy - r * 0.7, cx, cy + r * 0.7,
                              fill="#81C784", width=1)

        self.frame += 1
        if self.frame < self.FRAMES:
            self.win.after(FRAME_MS, self._tick)
        else:
            try: self.win.destroy()
            except tk.TclError: pass


# ═══════════════════════════════════════════════════════════════════════════════
#  Professor Oak's Lab — Starter selection
# ═══════════════════════════════════════════════════════════════════════════════
class StarterSelect:
    """
    Animated starter selection screen.
    Three cards on a wooden lab table; click one to begin.
    """
    W, H      = 700, 430
    CARD_TOP  = 82
    CARD_BOT  = 340
    SLOT_CX   = (140, 350, 560)

    def __init__(self, root, cache: dict, lines: list, callback):
        self.root     = root
        self.cache    = cache      # {(pid, shiny): (rights, lefts, w, h)}
        self.lines    = lines
        self.callback = callback   # callback(line_idx: int)
        self.hover    = -1
        self.frame    = 0
        self.done     = False

        # Static background stars / foliage dots
        self.stars = [
            (random.randint(0, self.W), random.randint(0, 270),
             random.choice(["#2D4E1F", "#3A6A2A", "#1E3A14", "#4A7A30"]))
            for _ in range(60)
        ]

        self.win = tk.Toplevel(root)
        self.win.title("BuddyMon — Choose your starter!")
        self.win.resizable(False, False)
        self.win.protocol("WM_DELETE_WINDOW", self._quit)

        sw = self.win.winfo_screenwidth()
        sh = self.win.winfo_screenheight()
        self.win.geometry(
            f"{self.W}x{self.H}"
            f"+{(sw - self.W) // 2}+{(sh - self.H) // 2}"
        )

        self.c = tk.Canvas(self.win, width=self.W, height=self.H,
                           bg="#0E1F09", highlightthickness=0)
        self.c.pack()
        self.c.bind("<Motion>",   self._on_motion)
        self.c.bind("<Button-1>", self._on_click)

        self._tick()

    # ── Events ────────────────────────────────────────────────────────────────
    @staticmethod
    def _quit():
        sys.exit(0)

    def _on_motion(self, e):
        new = -1
        for i, cx in enumerate(self.SLOT_CX):
            if abs(e.x - cx) < 82 and self.CARD_TOP < e.y < self.CARD_BOT:
                new = i; break
        self.hover = new

    def _on_click(self, e):
        if self.done:
            return
        for i, cx in enumerate(self.SLOT_CX):
            if abs(e.x - cx) < 82 and self.CARD_TOP < e.y < self.CARD_BOT:
                self.done = True
                self._flash(i)
                return

    def _flash(self, idx: int):
        self.c.create_rectangle(0, 0, self.W, self.H, fill="#FFFFFF", outline="")
        self.win.update()
        self.win.after(110, lambda: self._finish(idx))

    def _finish(self, idx: int):
        self.callback(idx)
        self.win.destroy()

    # ── Colour helper ─────────────────────────────────────────────────────────
    @staticmethod
    def _dim(hex_col: str, factor: float = 0.4) -> str:
        r = max(0, min(255, int(int(hex_col[1:3], 16) * factor)))
        g = max(0, min(255, int(int(hex_col[3:5], 16) * factor)))
        b = max(0, min(255, int(int(hex_col[5:7], 16) * factor)))
        return f"#{r:02x}{g:02x}{b:02x}"

    # ── Draw loop ─────────────────────────────────────────────────────────────
    def _tick(self):
        if self.done or not self.win.winfo_exists():
            return

        c, f = self.c, self.frame
        c.delete("all")

        # Background
        c.create_rectangle(0, 0, self.W, self.H, fill="#0E1F09", outline="")
        for sx, sy, sc in self.stars:
            c.create_oval(sx - 1, sy - 1, sx + 1, sy + 1, fill=sc, outline="")

        # Wooden table
        c.create_rectangle(0, 355, self.W, self.H,  fill="#2D1505", outline="")
        c.create_rectangle(0, 355, self.W, 369,      fill="#4A2008", outline="")
        c.create_rectangle(0, 369, self.W, 380,      fill="#6B3510", outline="")
        c.create_rectangle(0, 380, self.W, self.H,  fill="#3D2008", outline="")
        for gx in range(0, self.W, 58):
            c.create_line(gx, 369, gx + 38, self.H, fill="#321A06", width=1)

        # Title  (drop-shadow effect)
        for dx, dy, col in ((2, 2, "#7A5800"), (0, 0, "#FFD700")):
            c.create_text(self.W // 2 + dx, 27 + dy,
                          text="BuddyMon",
                          fill=col, font=("Consolas", 24, "bold"))
        c.create_text(self.W // 2, 55,
                      text="Choose your starter, trainer!",
                      fill="#A8C898", font=("Segoe UI", 12, "italic"))

        # ── Cards ─────────────────────────────────────────────────────────────
        ct, cb = self.CARD_TOP, self.CARD_BOT

        for i, (cx, line) in enumerate(zip(self.SLOT_CX, self.lines)):
            col = line["color"]
            hov = (i == self.hover)

            # Outer glow when hovered
            if hov:
                for expand, bg_col in (
                    (20, "#142010"), (14, "#1C3018"), (8, "#243820")
                ):
                    c.create_rectangle(
                        cx - 80 - expand, ct - expand,
                        cx + 80 + expand, cb + expand,
                        fill=bg_col, outline="",
                    )

            # Card body
            c.create_rectangle(cx - 80, ct, cx + 80, cb,
                               fill="#1A3015" if hov else "#131E0F",
                               outline="")

            # Card border (type colour)
            c.create_rectangle(cx - 80, ct, cx + 80, cb,
                               fill="", outline=col if hov else self._dim(col, 0.55),
                               width=3 if hov else 2)

            # Bottom type strip
            strip = col if hov else self._dim(col, 0.6)
            c.create_rectangle(cx - 80, cb - 46, cx + 80, cb,
                               fill=strip, outline="")

            # Pokémon name
            evo0 = line["evolutions"][0]
            c.create_text(cx, cb - 30,
                          text=evo0["name"],
                          fill="#FFFFFF" if hov else "#CCCCCC",
                          font=("Segoe UI", 10, "bold"))

            # Type label
            c.create_text(cx, cb - 13,
                          text=line["type"],
                          fill="#FFFFFF",
                          font=("Segoe UI", 8))

            # Animated sprite with bob
            pid = evo0["id"]
            if (pid, False) in self.cache:
                frames_r, _, sw_, sh_ = self.cache[(pid, False)]
                fidx = f % len(frames_r)
                bob  = int(math.sin(f * 0.12 + i * 2.1) * 6)
                # Centre sprite in the Pokemon area (above strip)
                sprite_cy = (ct + cb - 46) // 2
                c.create_image(
                    cx - sw_ // 2,
                    sprite_cy - sh_ // 2 + bob,
                    anchor="nw", image=frames_r[fidx],
                )

        # Footer hint
        c.create_text(self.W // 2, self.H - 10,
                      text="Click a Pokémon to begin",
                      fill="#4A6840", font=("Segoe UI", 9))

        self.frame += 1
        self.win.after(FRAME_MS, self._tick)


# ═══════════════════════════════════════════════════════════════════════════════
#  Buddy — the taskbar sprite
# ═══════════════════════════════════════════════════════════════════════════════
class Buddy:
    """Main desktop buddy: walks on the taskbar, responds to right-click."""

    def __init__(self):
        self.line_idx  = 0
        self.evo_stage = 0
        self.is_shiny  = False

        # Download sprites (skipped if already cached)
        print("BuddyMon — Checking sprites...", flush=True)
        for pid in ALL_IDS:
            ensure_sprite(pid, shiny=False)
            ensure_sprite(pid, shiny=True)
        print("All sprites ready.\n", flush=True)

        # Hidden root window (becomes the buddy after selection)
        self.root = tk.Tk()
        self.root.withdraw()

        self.scr_w = self.root.winfo_screenwidth()
        self.scr_h = self.root.winfo_screenheight()

        # Load all sprites (ImageTk requires root to exist)
        self._cache: dict = {}
        for pid in ALL_IDS:
            for shiny in (False, True):
                p = sprite_path(pid, shiny)
                if os.path.exists(p):
                    self._cache[(pid, shiny)] = load_frames(p)

        # Show starter selection
        select = StarterSelect(self.root, self._cache, STARTER_LINES, self._on_chosen)
        self.root.wait_window(select.win)

        if not getattr(self, "_started", False):
            return  # window closed without choosing

        # ── Configure root as the buddy window ────────────────────────────────
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.attributes("-transparentcolor", TRANSPARENT)
        self.root.configure(bg=TRANSPARENT)
        try: self.root.wm_attributes("-toolwindow", True)
        except tk.TclError: pass
        self.root.deiconify()

        self._apply()

        self.x         = float(random.randint(50, max(51, self.scr_w - self.sw - 50)))
        self.y         = float(-self.sh)
        self.root.geometry(f"{self.sw}x{self.sh}+{int(self.x)}+{int(self.y)}")

        self.vy        = 0.0
        self.state     = "falling"
        self.facing    = 1
        self.frame_i   = 0
        self.action_cd = 0

        self._drag_ox = self._drag_oy = 0
        self._dragging = False

        self.canvas.bind("<ButtonPress-1>",   self._press)
        self.canvas.bind("<B1-Motion>",       self._drag)
        self.canvas.bind("<ButtonRelease-1>", self._release)
        self.canvas.bind("<Button-3>",        self._show_menu)

        self._build_menu()
        self._tick()
        self.root.mainloop()

    # ── Starter selection callback ────────────────────────────────────────────
    def _on_chosen(self, line_idx: int):
        self.line_idx  = line_idx
        self.evo_stage = 0
        self.is_shiny  = random.random() < (1 / SHINY_CHANCE)
        self._started  = True

    # ── Sprite management ─────────────────────────────────────────────────────
    def _apply(self):
        """Apply current line/stage/shiny to the sprite."""
        evo = STARTER_LINES[self.line_idx]["evolutions"][self.evo_stage]
        pid = evo["id"]

        if (pid, self.is_shiny) not in self._cache:
            self.is_shiny = False   # fallback if shiny sprite missing

        r, l, w, h = self._cache[(pid, self.is_shiny)]
        self.frames_r, self.frames_l = r, l
        self.sw, self.sh = w, h
        self.ground_y = float(self.scr_h - TASKBAR_H - self.sh)
        self.n_frames  = len(r)

        if hasattr(self, "canvas"):
            self.canvas.config(width=self.sw, height=self.sh)
        else:
            self.canvas = tk.Canvas(
                self.root, width=self.sw, height=self.sh,
                bg=TRANSPARENT, highlightthickness=0,
            )
            self.canvas.pack()

        self.root.geometry(
            f"{self.sw}x{self.sh}"
            f"+{int(getattr(self,'x',0))}+{int(getattr(self,'y',0))}"
        )

    # ── Evolution ─────────────────────────────────────────────────────────────
    def _evolve(self):
        if self.evo_stage < 2:
            self.evo_stage += 1
            self.frame_i = 0
            self._apply()
            self._evo_flash()
            self._build_menu()

    def _devolve(self):
        if self.evo_stage > 0:
            self.evo_stage -= 1
            self.frame_i = 0
            self._apply()
            self._build_menu()

    def _evo_flash(self):
        """Pokemon-games-style white flash on evolution."""
        w = tk.Toplevel(self.root)
        w.overrideredirect(True)
        w.attributes("-topmost", True)
        try: w.wm_attributes("-toolwindow", True)
        except tk.TclError: pass
        w.geometry(f"{self.sw}x{self.sh}+{int(self.x)}+{int(self.y)}")
        w.configure(bg="#FFFFFF")
        w.after(120, w.destroy)

    # ── Starter line change ────────────────────────────────────────────────────
    def _change_line(self, idx: int):
        self.line_idx  = idx
        self.evo_stage = 0
        self.is_shiny  = random.random() < (1 / SHINY_CHANCE)
        self.frame_i   = 0
        self._apply()
        self._build_menu()

    def _reroll_shiny(self):
        self.is_shiny = random.random() < (1 / SHINY_CHANCE)
        self.frame_i  = 0
        self._apply()

    # ── Right-click menu ──────────────────────────────────────────────────────
    def _build_menu(self):
        line = STARTER_LINES[self.line_idx]
        evo  = line["evolutions"][self.evo_stage]
        name = evo["name"] + ("  [Shiny!]" if self.is_shiny else "")

        if hasattr(self, "_menu"):
            self._menu.destroy()

        m = tk.Menu(self.root, tearoff=0, font=("Segoe UI", 9))
        m.add_command(label=name, state="disabled",
                      font=("Segoe UI", 9, "bold"))
        m.add_separator()

        # Evolution
        m.add_command(
            label="Evolve",
            command=self._evolve,
            state="normal" if self.evo_stage < 2 else "disabled",
        )
        m.add_command(
            label="Devolve",
            command=self._devolve,
            state="normal" if self.evo_stage > 0 else "disabled",
        )
        m.add_separator()

        # Moves
        sub_m = tk.Menu(m, tearoff=0, font=("Segoe UI", 9))
        for mv in line["moves"]:
            sub_m.add_command(label=mv["name"],
                              command=lambda fx=mv["fx"]: self._use_move(fx))
        m.add_cascade(label="Use Move", menu=sub_m)

        # Change starter
        sub_s = tk.Menu(m, tearoff=0, font=("Segoe UI", 9))
        for i, ln in enumerate(STARTER_LINES):
            mark = "●  " if i == self.line_idx else "    "
            sub_s.add_command(
                label=f"{mark}{ln['evolutions'][0]['name']}",
                command=lambda idx=i: self._change_line(idx),
            )
        m.add_cascade(label="Change Starter", menu=sub_s)

        m.add_separator()
        m.add_command(label="Reroll Shiny", command=self._reroll_shiny)
        m.add_command(label="Throw Up",     command=self._throw)
        m.add_separator()
        m.add_command(label="Quit",         command=self.root.destroy)

        self._menu = m

    def _show_menu(self, e):
        try:    self._menu.tk_popup(e.x_root, e.y_root)
        finally: self._menu.grab_release()

    # ── Moves ─────────────────────────────────────────────────────────────────
    def _use_move(self, fx: str):
        MoveEffect(self.root, int(self.x), int(self.y),
                   self.sw, self.sh, fx, self.facing)

    # ── Drag ──────────────────────────────────────────────────────────────────
    def _press(self, e):
        self._drag_ox, self._drag_oy = e.x, e.y
        self._dragging = True
        self.vy = 0.0; self.state = "grounded"

    def _drag(self, e):
        if not self._dragging: return
        self.x += e.x - self._drag_ox
        self.y += e.y - self._drag_oy
        if self.y > self.ground_y: self.y = self.ground_y
        self.root.geometry(f"+{int(self.x)}+{int(self.y)}")

    def _release(self, _e):
        self._dragging = False

    # ── Actions ───────────────────────────────────────────────────────────────
    def _throw(self):
        self.vy = -16.0; self.state = "falling"

    def _start_walk(self):
        self.state     = "walk"
        self.facing    = random.choice([-1, 1])
        self.action_cd = random.randint(80, 200)

    def _start_idle(self):
        self.state     = "grounded"
        self.action_cd = random.randint(60, 160)

    # ── Main loop ─────────────────────────────────────────────────────────────
    def _tick(self):
        if not self._dragging:
            self._physics()
            self._behaviour()
        self._render()
        self.root.after(FRAME_MS, self._tick)

    def _physics(self):
        if self.state == "falling":
            self.vy += GRAVITY
            self.y  += self.vy
            if self.y >= self.ground_y:
                self.y = self.ground_y; self.vy = 0.0; self._start_idle()
            self.root.geometry(f"+{int(self.x)}+{int(self.y)}")
        elif self.state == "walk":
            self.x += self.facing * WALK_SPEED
            if self.x < 0:
                self.x = 0; self.facing = 1
            elif self.x > self.scr_w - self.sw:
                self.x = self.scr_w - self.sw; self.facing = -1
            self.root.geometry(f"+{int(self.x)}+{int(self.y)}")

    def _behaviour(self):
        if self.state == "falling": return
        self.action_cd -= 1
        if self.action_cd <= 0:
            if random.random() < 0.6: self._start_walk()
            else: self._start_idle()

    def _render(self):
        self.frame_i = (self.frame_i + 1) % self.n_frames
        frame = (self.frames_r if self.facing == 1 else self.frames_l)[self.frame_i]
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor="nw", image=frame)


# ═══════════════════════════════════════════════════════════════════════════════
#  Entry point
# ═══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    Buddy()
