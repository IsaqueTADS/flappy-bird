"""Flappy Bird: pixel art, procedural audio and a standalone Windows build."""
from __future__ import annotations

import argparse
import math
from pathlib import Path
import random
import sys
import tempfile
import time
import tkinter as tk

from audio import Audio
from storage import PlayerData

WIDTH, HEIGHT, GROUND = 288, 512, 400
GRAVITY, FLAP, SPEED = 850.0, -265.0, 105.0
PIPE_WIDTH, GAP, SPACING = 52, 112, 170
BIRD_X, BIRD_RADIUS = 78, 10
ROOT = Path(__file__).resolve().parent
VERSION = "0.2.0"


class World:
    """Time-based game simulation, independent from the window."""

    def __init__(self, rng=None):
        self.rng = rng or random.Random()
        self.reset()

    def reset(self):
        self.y, self.velocity = 190.0, 0.0
        self.score, self.dead = 0, False
        self.pipes = []
        self.distance = 0.0
        self.add_pipe(350)
        self.add_pipe(350 + SPACING)
        self.add_pipe(350 + SPACING * 2)

    def add_pipe(self, x):
        self.pipes.append({"x": float(x), "center": self.rng.randint(115, 285), "passed": False})

    def flap(self):
        if not self.dead:
            self.velocity = FLAP

    def step(self, dt):
        if self.dead:
            return
        self.velocity += GRAVITY * dt
        self.y += self.velocity * dt
        self.distance += SPEED * dt
        for pipe in self.pipes:
            pipe["x"] -= SPEED * dt
            left, center = pipe["x"], pipe["center"]
            # Circle versus the pipe rectangles, including their wider caps.
            nearest_x = max(left - 3, min(BIRD_X, left + PIPE_WIDTH + 3))
            for top, bottom in ((-100, center - GAP / 2), (center + GAP / 2, GROUND)):
                nearest_y = max(top, min(self.y, bottom))
                if (BIRD_X - nearest_x) ** 2 + (self.y - nearest_y) ** 2 < BIRD_RADIUS ** 2:
                    self.dead = True
            if not pipe["passed"] and left + PIPE_WIDTH < BIRD_X:
                pipe["passed"] = True
                self.score += 1
        if self.y - BIRD_RADIUS <= 0 or self.y + BIRD_RADIUS >= GROUND:
            self.dead = True
        if self.pipes[0]["x"] < -PIPE_WIDTH - 5:
            self.pipes.pop(0)
            self.add_pipe(self.pipes[-1]["x"] + SPACING)


# Each cell is two game pixels. Original sprite artwork, drawn for this project.
BIRD = [
    "......KKKKKK.....",
    "....KKYYYYWWK....",
    "...KYYYYYWWWWK...",
    "..KYYYYYYWWKWK...",
    ".KYYYYYYYWWKWK...",
    ".KYYKKKKYYWWWK...",
    "KYYKLLLLKYYYYKKK.",
    "KYYKLLLLKYKKKRRRK",
    "KYYYKLLKYYKRRRRRK",
    ".KOOOKKOOOOKKKKK.",
    "..KOOOOOOOOK.....",
    "...KKKKKKKK......",
]
PALETTE = {"K": "#42352c", "Y": "#f7df39", "W": "#fffbe8", "L": "#fff6b2", "R": "#f36b32", "O": "#eaa52e"}

GLYPHS = {
    "A": ["01110", "11011", "11011", "11111", "11011", "11011", "11011"],
    "B": ["11110", "11011", "11011", "11110", "11011", "11011", "11110"],
    "D": ["11110", "11011", "11011", "11011", "11011", "11011", "11110"],
    "E": ["11111", "11000", "11000", "11110", "11000", "11000", "11111"],
    "F": ["11111", "11000", "11000", "11110", "11000", "11000", "11000"],
    "G": ["01111", "11000", "11000", "11011", "11011", "11011", "01110"],
    "I": ["111", "010", "010", "010", "010", "010", "111"],
    "L": ["11000", "11000", "11000", "11000", "11000", "11000", "11111"],
    "M": ["11011", "11111", "11111", "11011", "11011", "11011", "11011"],
    "O": ["01110", "11011", "11011", "11011", "11011", "11011", "01110"],
    "P": ["11110", "11011", "11011", "11110", "11000", "11000", "11000"],
    "R": ["11110", "11011", "11011", "11110", "11100", "11010", "11011"],
    "T": ["11111", "00100", "00100", "00100", "00100", "00100", "00100"],
    "V": ["11011", "11011", "11011", "11011", "11011", "01110", "00100"],
    "Y": ["11011", "11011", "01110", "00100", "00100", "00100", "00100"],
    "0": ["01110", "11011", "11011", "11011", "11011", "11011", "01110"],
    "1": ["010", "110", "010", "010", "010", "010", "111"],
    "2": ["01110", "11011", "00011", "00110", "01100", "11000", "11111"],
    "3": ["11110", "00011", "00011", "01110", "00011", "00011", "11110"],
    "4": ["11011", "11011", "11011", "11111", "00011", "00011", "00011"],
    "5": ["11111", "11000", "11000", "11110", "00011", "00011", "11110"],
    "6": ["01110", "11000", "11000", "11110", "11011", "11011", "01110"],
    "7": ["11111", "00011", "00011", "00110", "00110", "01100", "01100"],
    "8": ["01110", "11011", "11011", "01110", "11011", "11011", "01110"],
    "9": ["01110", "11011", "11011", "01111", "00011", "00011", "01110"],
}


class Game:
    def __init__(self, window, data=None, audio_enabled=True):
        self.window = window
        self.scale = min(1.5, (window.winfo_screenheight() - 130) / HEIGHT)
        self.canvas = tk.Canvas(window, width=round(WIDTH * self.scale), height=round(HEIGHT * self.scale), bg="#70c5ce", highlightthickness=0)
        self.canvas.pack()
        window.title(f"Flappy Bird · {VERSION}")
        window.resizable(False, False)
        self.world = World()
        self.state, self.paused = "ready", False
        self.elapsed, self.ground_offset = 0.0, 0.0
        self.death_time, self.flash_until = 0.0, 0.0
        self.data = data if data is not None else PlayerData(legacy=ROOT / "data" / "record.json")
        self.best = self.data.best
        self.save_error = False
        self.sprites = {}
        self.button = None
        self.background()
        self.audio = Audio(self.data.music, self.data.effects, enabled=audio_enabled)
        self.icon = self.bird_image(1, 0)
        window.iconphoto(True, self.icon)
        window.protocol("WM_DELETE_WINDOW", self.close)
        window.bind("<space>", self.action)
        window.bind("<Up>", self.action)
        window.bind("<Button-1>", self.click)
        window.bind("<Key-r>", self.restart)
        window.bind("<Key-R>", self.restart)
        window.bind("<Key-p>", self.pause)
        window.bind("<Key-P>", self.pause)
        window.bind("<Escape>", self.pause)
        window.bind("<FocusOut>", self.focus_out)
        for key in ("m", "M"):
            window.bind(f"<Key-{key}>", self.toggle_music)
        for key in ("e", "E"):
            window.bind(f"<Key-{key}>", self.toggle_effects)
        self.last = time.perf_counter()
        self.render()
        window.after(16, self.tick)

    def save_best(self):
        self.save_error = not self.data.save_record(self.best)

    def toggle_music(self, event=None):
        self.audio.toggle_music()
        self.data.save_settings(self.audio.music_enabled, self.audio.effects_enabled)

    def toggle_effects(self, event=None):
        self.audio.toggle_effects()
        self.data.save_settings(self.audio.music_enabled, self.audio.effects_enabled)

    def close(self):
        self.audio.close()
        self.window.destroy()

    def rect(self, x1, y1, x2, y2, color, tag="dynamic", outline="", width=1):
        s = self.scale
        return self.canvas.create_rectangle(x1*s, y1*s, x2*s, y2*s, fill=color, outline=outline, width=width*s, tags=tag)

    def text(self, x, y, text, size=10, color="#fffbe8", **kwargs):
        return self.canvas.create_text(x*self.scale, y*self.scale, text=text, fill=color, font=("Segoe UI", round(size*self.scale), "bold"), tags="dynamic", **kwargs)

    def pixel_text(self, text, x, y, unit=3, color="#ffffff", border="#493b32"):
        glyphs = [GLYPHS.get(c, ["000"]*7) for c in text]
        total = sum(len(g[0])+1 for g in glyphs)*unit-unit
        start = x-total/2
        cells = []
        for glyph in glyphs:
            for row, line in enumerate(glyph):
                for col, cell in enumerate(line):
                    if cell == "1":
                        cells.append((start+col*unit, y+row*unit))
            start += (len(glyph[0])+1)*unit
        for px, py in cells:
            self.rect(px-1, py-1, px+unit+1, py+unit+2, border)
        for px, py in cells:
            self.rect(px, py, px+unit, py+unit, color)

    def background(self):
        self.rect(0, 0, WIDTH, GROUND, "#70c5ce", "background")
        # Distant clouds: stepped silhouettes, like a low-resolution tile set.
        for x, y in [(-18, 296), (31, 306), (86, 291), (151, 302), (218, 292), (268, 309)]:
            self.rect(x, y+8, x+54, 365, "#e4f6d5", "background")
            self.rect(x+8, y, x+42, 365, "#e4f6d5", "background")
            self.rect(x+16, y-5, x+33, 365, "#e4f6d5", "background")
        for i in range(14):
            x = i*23-7
            top = 333 + (i*17 % 26)
            self.rect(x, top, x+19, 390, "#b9dec5", "background")
            self.rect(x+2, top+3, x+17, 390, "#d4ead0", "background")
            for wy in range(top+7, 387, 9):
                for wx in (x+4, x+11):
                    self.rect(wx, wy, wx+3, wy+4, "#b0d8bd", "background")
        for i in range(19):
            x = i*17-7
            y = 374+(i*7 % 12)
            self.rect(x, y+5, x+20, 400, "#82c994", "background")
            self.rect(x+4, y, x+15, 400, "#82c994", "background")
            self.rect(x+5, y+3, x+13, y+6, "#b1dfa3", "background")

    def bird_image(self, phase, angle):
        key = phase, angle
        if key in self.sprites:
            return self.sprites[key]
        sprite = [list(row) for row in BIRD]
        # Three wing positions within the same silhouette.
        for row in range(5, 10):
            for col in range(3, 8):
                if sprite[row][col] in "KL":
                    sprite[row][col] = "Y" if row < 9 else "O"
        wing_y = (4, 6, 8)[phase]
        for row, line in enumerate(["KKKK", "KLLLK", "KLLLK", ".KKK"]):
            for col, value in enumerate(line):
                if value != ".":
                    sprite[min(11, wing_y+row)][3+col] = value
        size = round(48*self.scale)
        img = tk.PhotoImage(width=size, height=size)
        rad = math.radians(angle)
        ca, sa = math.cos(rad), math.sin(rad)
        for y in range(size):
            for x in range(size):
                dx, dy = (x-size/2)/self.scale, (y-size/2)/self.scale
                sx = int((ca*dx+sa*dy)/2+8.5)
                sy = int((-sa*dx+ca*dy)/2+6)
                if 0 <= sx < 17 and 0 <= sy < 12:
                    value = sprite[sy][sx]
                    if value != ".":
                        img.put(PALETTE[value], (x, y))
        self.sprites[key] = img
        return img

    def pipe(self, x, center):
        for top, bottom, upper in ((-5, center-GAP/2, True), (center+GAP/2, GROUND, False)):
            self.rect(x, top, x+52, bottom, "#543f33")
            self.rect(x+2, top, x+50, bottom, "#73bf2e")
            self.rect(x+4, top, x+9, bottom, "#d8ee77")
            self.rect(x+9, top, x+14, bottom, "#b3df51")
            self.rect(x+36, top, x+44, bottom, "#5b9f25")
            self.rect(x+44, top, x+49, bottom, "#458323")
            cap_top = bottom-24 if upper else top
            self.rect(x-3, cap_top, x+55, cap_top+24, "#543f33")
            self.rect(x-1, cap_top+2, x+53, cap_top+22, "#80c63b")
            self.rect(x+1, cap_top+3, x+7, cap_top+21, "#d8ee77")
            self.rect(x+7, cap_top+3, x+13, cap_top+21, "#b3df51")
            self.rect(x+39, cap_top+3, x+47, cap_top+21, "#5b9f25")
            self.rect(x+47, cap_top+3, x+52, cap_top+21, "#458323")

    def action(self, event=None):
        if self.paused:
            self.pause()
        elif self.state == "ready":
            self.state = "playing"
            self.world.flap()
            self.audio.effect("flap")
        elif self.state == "playing":
            self.world.flap()
            self.audio.effect("flap")
        elif time.perf_counter()-self.death_time > 0.65:
            self.restart()

    def click(self, event):
        x, y = event.x/self.scale, event.y/self.scale
        if 479 <= y <= 503:
            if 12 <= x <= 140:
                self.toggle_music()
                return
            if 148 <= x <= 276:
                self.toggle_effects()
                return
        if self.state == "over":
            if self.button:
                x1, y1, x2, y2 = self.button
                if x1 <= event.x/self.scale <= x2 and y1 <= event.y/self.scale <= y2:
                    self.action()
        else:
            self.action()

    def restart(self, event=None):
        if self.state == "over" and time.perf_counter()-self.death_time < 0.65:
            return
        self.world.reset()
        self.state, self.paused = "ready", False
        self.button = None
        self.audio.set_paused(False)
        self.audio.start_music()

    def pause(self, event=None):
        if self.state == "playing":
            self.paused = not self.paused
            self.audio.set_paused(self.paused)

    def focus_out(self, event):
        if self.state == "playing":
            self.paused = True
            self.audio.set_paused(True)

    def tick(self):
        now = time.perf_counter()
        dt = min(now-self.last, 0.05)
        self.last = now
        if not self.paused:
            self.elapsed += dt
            if self.state != "over":
                self.ground_offset = (self.ground_offset+SPEED*dt) % 24
            if self.state == "playing":
                previous_score = self.world.score
                # Small physics steps keep collision checks reliable after a slow frame.
                remaining = dt
                while remaining > 0 and not self.world.dead:
                    step = min(remaining, 1/120)
                    self.world.step(step)
                    remaining -= step
                if self.world.dead:
                    self.state = "over"
                    self.death_time = now
                    self.flash_until = now+0.09
                    self.audio.die()
                    self.new_best = self.world.score > self.best
                    if self.new_best:
                        self.best = self.world.score
                        self.save_best()
                elif self.world.score > previous_score:
                    self.audio.effect("point")
            elif self.state == "over" and self.world.y < GROUND-12:
                self.world.velocity += GRAVITY*dt
                self.world.y = min(GROUND-12, self.world.y+max(0, self.world.velocity)*dt)
        self.render()
        self.window.after(16, self.tick)

    def render(self):
        self.canvas.delete("dynamic")
        if self.state != "ready":
            for pipe in self.world.pipes:
                self.pipe(pipe["x"], pipe["center"])
        y = self.world.y if self.state != "ready" else 205+math.sin(self.elapsed*5)*5
        angle = 0 if self.state == "ready" else max(-25, min(85, (self.world.velocity+120)*0.20))
        angle = int(round(angle/10)*10)
        phase = int(self.elapsed*10) % 3 if self.state != "over" else 1
        self.canvas.create_image(BIRD_X*self.scale, y*self.scale, image=self.bird_image(phase, angle), tags="dynamic")
        self.rect(0, GROUND, WIDTH, HEIGHT, "#ded895")
        self.rect(0, GROUND, WIDTH, GROUND+2, "#553e32")
        self.rect(0, GROUND+2, WIDTH, GROUND+4, "#e9f4a4")
        self.rect(0, GROUND+4, WIDTH, GROUND+15, "#8ac641")
        for i in range(-1, 14):
            x = i*24-self.ground_offset
            s = self.scale
            self.canvas.create_polygon(x*s, (GROUND+4)*s, (x+12)*s, (GROUND+4)*s, (x+2)*s, (GROUND+15)*s, (x-10)*s, (GROUND+15)*s, fill="#c7e86b", outline="", tags="dynamic")
        self.rect(0, GROUND+15, WIDTH, GROUND+17, "#638b30")
        self.rect(0, GROUND+17, WIDTH, GROUND+20, "#f4e6a9")
        self.rect(0, GROUND+20, WIDTH, GROUND+23, "#d3ba7c")
        if self.state == "ready":
            self.pixel_text("FLAPPY", 144, 70, 5, "#f8e886")
            self.pixel_text("BIRD", 144, 115, 5, "#f8e886")
            self.pixel_text("GET READY", 144, 262, 3, "#8ee35f")
            self.text(144, 307, "ESPAÇO ou clique para voar", 10, "#38676b")
            self.text(144, 329, "Passe pelos canos!", 9, "#38676b")
            self.text(144, 459, f"RECORDE  {self.best}", 10, "#7b6541")
        elif self.state == "playing":
            self.pixel_text(str(self.world.score), 144, 35, 4)
            self.text(144, 464, "P · PAUSAR", 8, "#8b7950")
        elif time.perf_counter()-self.death_time > 0.45:
            self.pixel_text("GAME OVER", 144, 111, 3, "#f3a34b")
            self.rect(28, 171, 262, 299, "#543f33")
            self.rect(30, 173, 260, 297, "#f8edbc")
            self.rect(33, 176, 257, 294, "#ded895")
            self.rect(36, 179, 254, 181, "#ece6aa")
            self.text(76, 197, "MEDALHA", 8, "#a68752")
            score = self.world.score
            if score >= 10:
                medal_color = "#e6b650" if score >= 20 else "#c3c6bc"
                self.canvas.create_oval(51*self.scale, 216*self.scale, 101*self.scale, 266*self.scale, fill=medal_color, outline="#a08045", width=3*self.scale, tags="dynamic")
                self.text(76, 241, "★", 24, "#fff2b2")
            else:
                self.text(76, 240, "—", 25, "#c2b77c")
            self.text(229, 192, "PONTOS", 8, "#a68752", anchor="e")
            self.pixel_text(str(score), 218, 207, 3)
            self.text(229, 244, "RECORDE", 8, "#a68752", anchor="e")
            self.pixel_text(str(self.best), 218, 260, 3)
            if getattr(self, "new_best", False):
                self.rect(133, 242, 169, 254, "#ed6e43")
                self.text(151, 248, "NOVO", 6)
            self.button = (81, 320, 207, 356)
            self.rect(81, 323, 207, 360, "#543f33")
            self.rect(81, 320, 207, 356, "#543f33")
            self.rect(83, 322, 205, 354, "#fbf4ce")
            self.rect(86, 325, 202, 351, "#e78c3c")
            self.text(144, 338, "JOGAR DE NOVO", 10)
            self.text(144, 378, "ESPAÇO ou R para reiniciar", 9, "#38676b")
            self.text(144, 459, "Recorde indisponível para salvar" if self.save_error else "MAIS UM VOO?", 8, "#8b7950")
        if self.audio.available:
            self.rect(12, 479, 140, 503, "#d1ca88")
            self.rect(148, 479, 276, 503, "#d1ca88")
            self.text(76, 491, f"M · MÚSICA {'ON' if self.audio.music_enabled else 'OFF'}", 8, "#675635")
            self.text(212, 491, f"E · EFEITOS {'ON' if self.audio.effects_enabled else 'OFF'}", 8, "#675635")
        else:
            self.text(144, 491, "ÁUDIO INDISPONÍVEL", 8, "#8b7950")
        if self.paused:
            self.rect(38, 172, 250, 270, "#543f33")
            self.rect(41, 175, 247, 267, "#ded895")
            self.text(144, 202, "PAUSADO", 19, "#543f33")
            self.text(144, 239, "P ou espaço para continuar", 9, "#7b6541")
        if time.perf_counter() < self.flash_until:
            self.rect(0, 0, WIDTH, HEIGHT, "#fffbe8")


def main():
    parser = argparse.ArgumentParser(description="Flappy Bird em Python — espaço ou clique para voar.")
    parser.add_argument("--smoke-test", action="store_true", help="Abre a janela, verifica as telas e fecha automaticamente.")
    parser.add_argument("--no-audio", action="store_true", help="Executa sem inicializar o dispositivo de áudio.")
    parser.add_argument("--data-dir", type=Path, help="Diretório alternativo para recorde e preferências.")
    parser.add_argument("--smoke-report", type=Path, help="Salva o resultado do teste de interface em JSON.")
    args = parser.parse_args()
    test_directory = tempfile.TemporaryDirectory() if args.smoke_test and args.data_dir is None else None
    data_dir = args.data_dir or (Path(test_directory.name) if test_directory else None)
    legacy_root = Path(sys.executable).parent if getattr(sys, "frozen", False) else ROOT
    data = PlayerData(data_dir, legacy=None if args.smoke_test else legacy_root / "data" / "record.json")
    window = tk.Tk()
    game = Game(window, data, audio_enabled=not args.no_audio)
    failures = []
    if args.smoke_test:
        import json

        def check():
            report = {"version": VERSION, "frozen": bool(getattr(sys, "frozen", False)),
                      "audio": game.audio.available, "audio_backend": game.audio.backend, "audio_error": game.audio.error}
            try:
                game.action()
                game.world.step(1/60)
                game.render()
                assert game.state == "playing"
                game.pause()
                game.render()
                assert game.paused
                game.action()
                assert not game.paused
                game.audio.effect("point")
                game.toggle_music()
                game.toggle_music()
                game.toggle_effects()
                game.toggle_effects()
                game.audio.die()
                game.state = "over"
                game.death_time = time.perf_counter()-1
                game.world.score = 12
                game.render()
                window.update_idletasks()
                game.best = max(12, game.best)
                game.save_best()
                assert PlayerData(data.directory).best == game.best
                game.restart()
                game.render()
                assert game.state == "ready" and game.world.score == 0
                report["ok"] = True
            except Exception as error:
                failures.append(str(error))
                report.update(ok=False, error=repr(error))
            finally:
                if args.smoke_report:
                    args.smoke_report.parent.mkdir(parents=True, exist_ok=True)
                    args.smoke_report.write_text(json.dumps(report, indent=2), encoding="utf-8")
                if sys.stdout is not None:
                    print(json.dumps(report, indent=2))
                game.close()
        window.after(300, check)
    try:
        window.mainloop()
    finally:
        game.audio.close()
        if test_directory:
            test_directory.cleanup()
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
