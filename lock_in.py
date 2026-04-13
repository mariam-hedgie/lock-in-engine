#!/usr/bin/env python3
"""
Lock-In Engine — corner overlay focus timer for macOS.
Double-click run.command or run: python3 lock_in.py
"""

from __future__ import annotations

import random
import sys
import threading
import time
import tkinter as tk
from tkinter import font as tkfont
from typing import Optional

from config import (
    CORNER, CORNER_MARGIN,
    MINI_W, MINI_H, FULL_W, FULL_H, NOTE_H,
    SESSION_PLAN, TOTAL_MINUTES,
    MESSAGES, THEMES,
)

TOTAL_BLOCKS = len(SESSION_PLAN)
from focus_watcher import FocusWatcher
from logger import SessionLogger


# ── Helpers ───────────────────────────────────────────────────────────────────

def fmt(secs: int) -> str:
    secs = max(0, secs)
    return f"{secs // 60:02d}:{secs % 60:02d}"


def describe_plan() -> str:
    return "5 · 10 · 15 · 30 · 30 · 30 · 30 · 30"


# ── Main App ──────────────────────────────────────────────────────────────────

class LockInEngine:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Lock-In")
        self.root.resizable(False, False)
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.97)
        self.root.overrideredirect(True)   # no title bar

        # macOS: keep on top of full-screen spaces
        try:
            self.root.tk.call(
                "::tk::unsupported::MacWindowStyle",
                "style", self.root._w,
                "floating", "noTitleBar",
            )
        except Exception:
            pass

        # ── State ─────────────────────────────────────────────────────────────
        self.state          = "intro"
        self.expanded       = False
        self.block_index    = 0
        self.secs_left      = 0
        self.block_mins     = 0
        self.total_done     = 0
        self.capture_count  = 0
        self.msg_index      = 0
        self.after_id: Optional[str] = None
        self.panic_mode     = False
        self.run_title      = "Lock-In"
        self.allowed_tools  = ["Canvas", "PDFs", "Goodnotes", "ChatGPT"]
        self.session_log: Optional[SessionLogger] = None
        self.drift_secs     = 0
        self.is_drifting    = False
        self.theme          = THEMES[0]
        self.prev_theme     = None

        # StringVars
        self.sv_timer    = tk.StringVar(value="00:00")
        self.sv_line     = tk.StringVar(value="Lock-In Engine")
        self.sv_sub      = tk.StringVar(value="click to set up your session")
        self.sv_charm    = tk.StringVar(value="tiny start → deep focus")
        self.sv_prog     = tk.StringVar(value=describe_plan())
        self.sv_title    = tk.StringVar()
        self.sv_tools    = tk.StringVar(value="Canvas, PDFs, Goodnotes, ChatGPT")
        self.sv_note     = tk.StringVar()
        self.sv_theme    = tk.StringVar(value="Matcha Night")
        self.sv_drift    = tk.StringVar(value="● focused")

        # Build UI then position
        self._build_ui()
        self._position_window(MINI_W, MINI_H)
        self._apply_theme(self.theme)

        # Focus watcher
        self.watcher = FocusWatcher(
            own_app_names=["python", "python3", "lock-in"],
            on_drift=self._on_drift,
            on_return=self._on_return,
        )
        self.watcher.start()

        # Drag support (so user can reposition)
        self._drag_x = 0
        self._drag_y = 0
        self.mini_frame.bind("<Button-1>",   self._drag_start)
        self.mini_frame.bind("<B1-Motion>",  self._drag_motion)
        self.timer_lbl.bind("<Button-1>",    self._drag_start)
        self.timer_lbl.bind("<B1-Motion>",   self._drag_motion)

        # Click mini to toggle
        self.mini_frame.bind("<ButtonRelease-1>", self._on_mini_click)
        self.timer_lbl.bind("<ButtonRelease-1>",  self._on_mini_click)

        # Keyboard
        self.root.bind("<Return>",           self._handle_return)
        self.root.bind("<Escape>",           lambda e: self._collapse())
        self.root.bind("<Control-p>",        self._handle_panic)
        self.root.bind("<Control-q>",        self._handle_quit)
        self.root.bind("<Control-Q>",        self._handle_quit)

        self._show_mini()

    # ── Window positioning ────────────────────────────────────────────────────

    def _position_window(self, w: int, h: int) -> None:
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        m  = CORNER_MARGIN
        if CORNER == "bottom-right":
            x, y = sw - w - m, sh - h - m - 40   # -40 for macOS dock
        elif CORNER == "bottom-left":
            x, y = m, sh - h - m - 40
        elif CORNER == "top-right":
            x, y = sw - w - m, m + 28
        else:
            x, y = m, m + 28
        self.root.geometry(f"{w}x{h}+{x}+{y}")

    def _resize(self, w: int, h: int) -> None:
        # Keep same corner position when resizing
        geo   = self.root.geometry()
        parts = geo.split("+")
        old_w, old_h = map(int, parts[0].split("x"))
        cx    = int(parts[1])
        cy    = int(parts[2])
        sw    = self.root.winfo_screenwidth()
        m     = CORNER_MARGIN

        if CORNER in ("bottom-right", "top-right"):
            cx = cx + old_w - w          # keep right edge fixed
        # top: keep top edge; bottom: keep bottom edge (approximate)
        self.root.geometry(f"{w}x{h}+{cx}+{cy}")

    # ── Drag ─────────────────────────────────────────────────────────────────

    def _drag_start(self, e: tk.Event) -> None:
        self._drag_x = e.x_root - self.root.winfo_x()
        self._drag_y = e.y_root - self.root.winfo_y()

    def _drag_motion(self, e: tk.Event) -> None:
        self._moved = True
        x = e.x_root - self._drag_x
        y = e.y_root - self._drag_y
        w = self.root.winfo_width()
        h = self.root.winfo_height()
        self.root.geometry(f"{w}x{h}+{x}+{y}")

    # ── Build UI ──────────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        self.root.configure(bg="#0f1410")

        # ── Mini view (always visible in collapsed state) ──────────────────
        self.mini_frame = tk.Frame(self.root, bd=0, highlightthickness=0)
        self.mini_frame.place(x=0, y=0, width=MINI_W, height=MINI_H)

        self.drift_lbl = tk.Label(
            self.mini_frame, textvariable=self.sv_drift,
            font=("Menlo", 10), anchor="e",
        )
        self.drift_lbl.place(relx=1.0, y=8, anchor="ne", x=-10)

        self.mini_line = tk.Label(
            self.mini_frame, textvariable=self.sv_line,
            font=("Georgia", 12, "italic"),
            wraplength=MINI_W - 20, justify="center",
        )
        self.mini_line.place(relx=0.5, y=14, anchor="n")

        self.timer_lbl = tk.Label(
            self.mini_frame, textvariable=self.sv_timer,
            font=("Menlo", 32, "bold"),
            anchor="center",
        )
        self.timer_lbl.place(relx=0.5, rely=0.5, anchor="center", y=6)

        self.charm_lbl = tk.Label(
            self.mini_frame, textvariable=self.sv_charm,
            font=("Menlo", 9),
        )
        self.charm_lbl.place(relx=0.5, rely=1.0, anchor="s", y=-6)

        # ── Full / expanded view ───────────────────────────────────────────
        self.full_frame = tk.Frame(self.root, bd=0, highlightthickness=0)
        # placed dynamically when expanded

        # Theme badge
        self.theme_lbl = tk.Label(
            self.full_frame, textvariable=self.sv_theme,
            font=("Menlo", 10), padx=8, pady=3,
        )
        self.theme_lbl.pack(anchor="w", padx=10, pady=(10, 0))

        # Main line
        self.main_line_lbl = tk.Label(
            self.full_frame, textvariable=self.sv_line,
            font=("Georgia", 15, "italic"),
            wraplength=FULL_W - 40, justify="center",
        )
        self.main_line_lbl.pack(fill="x", padx=10, pady=(8, 0))

        # Sub line
        self.sub_lbl = tk.Label(
            self.full_frame, textvariable=self.sv_sub,
            font=("Helvetica", 11),
            wraplength=FULL_W - 40, justify="center",
        )
        self.sub_lbl.pack(fill="x", padx=10)

        # Timer (big)
        self.timer_big = tk.Label(
            self.full_frame, textvariable=self.sv_timer,
            font=("Menlo", 64, "bold"),
            anchor="center",
        )
        self.timer_big.pack(fill="x", pady=(4, 0))

        # Progress
        self.prog_lbl = tk.Label(
            self.full_frame, textvariable=self.sv_prog,
            font=("Menlo", 10),
            wraplength=FULL_W - 40, justify="center",
        )
        self.prog_lbl.pack(fill="x", padx=10)

        # Tracker
        self.tracker_frame = tk.Frame(self.full_frame)
        self.tracker_frame.pack(fill="x", padx=14, pady=(8, 0))
        self.tracker_dots: list[tk.Label] = []
        self._build_tracker_dots()

        # Charm
        self.charm_big = tk.Label(
            self.full_frame, textvariable=self.sv_charm,
            font=("Menlo", 10),
        )
        self.charm_big.pack(pady=(6, 0))

        # Intro inputs
        self.intro_frame = tk.Frame(self.full_frame)
        self.intro_frame.pack(fill="x", padx=14, pady=(10, 0))

        tk.Label(self.intro_frame, text="Run title",
                 font=("Helvetica", 11, "bold"), anchor="w").pack(fill="x")
        self.title_entry = tk.Entry(
            self.intro_frame, textvariable=self.sv_title,
            font=("Helvetica", 13), relief="flat", justify="center",
        )
        self.title_entry.pack(fill="x", ipady=6, pady=(2, 8))

        tk.Label(self.intro_frame, text="Allowed tools",
                 font=("Helvetica", 11, "bold"), anchor="w").pack(fill="x")
        self.tools_entry = tk.Entry(
            self.intro_frame, textvariable=self.sv_tools,
            font=("Helvetica", 12), relief="flat", justify="center",
        )
        self.tools_entry.pack(fill="x", ipady=6, pady=(2, 0))

        # Note frame
        self.note_frame = tk.Frame(self.full_frame)
        # packed dynamically

        tk.Label(self.note_frame, text="What did you just do?",
                 font=("Helvetica", 11, "bold"), anchor="w").pack(fill="x", padx=14)
        self.note_entry = tk.Entry(
            self.note_frame, textvariable=self.sv_note,
            font=("Helvetica", 12), relief="flat", justify="center",
        )
        self.note_entry.pack(fill="x", ipady=6, padx=14, pady=(4, 0))

        # Primary button
        self.btn_primary = tk.Button(
            self.full_frame, text="Lock In →",
            font=("Helvetica", 13, "bold"),
            relief="flat", bd=0, padx=10, pady=10,
            command=self._start_run,
        )
        self.btn_primary.pack(fill="x", padx=14, pady=(12, 0))

        # Action buttons
        self.action_frame = tk.Frame(self.full_frame)
        self.action_frame.pack(fill="x", padx=14, pady=(8, 0))
        self._action_buttons: list[tk.Button] = []
        for label, cmd in (
            ("Tools",     lambda: self._popup("allowed")),
            ("Intention", lambda: self._popup("intention")),
            ("Capture",   lambda: self._popup("capture")),
            ("Return",    lambda: self._popup("return")),
            ("Glass 🔴",  lambda: self._popup("break")),
        ):
            b = tk.Button(
                self.action_frame, text=label,
                font=("Helvetica", 10, "bold"),
                relief="flat", bd=0, padx=6, pady=7,
                command=cmd,
            )
            b.pack(side="left", expand=True, fill="x", padx=2)
            self._action_buttons.append(b)

        # Drift indicator (full)
        self.drift_full = tk.Label(
            self.full_frame, textvariable=self.sv_drift,
            font=("Menlo", 10),
        )
        self.drift_full.pack(pady=(6, 4))

        # Hint
        self.hint_lbl = tk.Label(
            self.full_frame,
            text="↓ collapse  ·  Ctrl+Q quit",
            font=("Menlo", 9),
        )
        self.hint_lbl.pack(pady=(0, 8))

    def _build_tracker_dots(self) -> None:
        for w in self.tracker_frame.winfo_children():
            w.destroy()
        self.tracker_dots = []
        for i, m in enumerate(SESSION_PLAN):
            lbl = tk.Label(
                self.tracker_frame, text=str(m),
                font=("Menlo", 9, "bold"),
                width=3, pady=3,
                relief="flat",
            )
            lbl.pack(side="left", padx=2)
            self.tracker_dots.append(lbl)
        self._update_tracker()

    def _update_tracker(self) -> None:
        t = self.theme
        for i, lbl in enumerate(self.tracker_dots):
            if i < self.block_index:
                lbl.configure(bg=t["accent"], fg=t["bg"])
            elif i == self.block_index and self.state == "countdown":
                lbl.configure(bg=t["surface"], fg=t["accent"])
            else:
                lbl.configure(bg=t["surface"], fg=t["muted"])

    # ── Theme ─────────────────────────────────────────────────────────────────

    def _apply_theme(self, t: dict) -> None:
        self.theme = t
        self.sv_theme.set(t["name"])
        bg, surf, acc, muted, text = (
            t["bg"], t["surface"], t["accent"], t["muted"], t["text"]
        )
        self.root.configure(bg=bg)

        # mini
        self.mini_frame.configure(bg=surf)
        self.mini_line.configure(bg=surf, fg=muted)
        self.timer_lbl.configure(bg=surf, fg=acc)
        self.charm_lbl.configure(bg=surf, fg=muted)
        self.drift_lbl.configure(bg=surf, fg=(self.theme["danger"] if self.is_drifting else muted))

        # full
        self.full_frame.configure(bg=surf)
        for w in self._all_full_widgets():
            try:
                w.configure(bg=surf)
            except Exception:
                pass
        self.theme_lbl.configure(bg=acc, fg=bg)
        self.main_line_lbl.configure(fg=text)
        self.sub_lbl.configure(fg=muted)
        self.timer_big.configure(fg=acc)
        self.prog_lbl.configure(fg=muted)
        self.charm_big.configure(fg=acc)
        self.drift_full.configure(fg=(self.theme["danger"] if self.is_drifting else muted))
        self.hint_lbl.configure(fg=muted)
        self.btn_primary.configure(bg=acc, fg=bg, activebackground=muted, activeforeground=bg)
        for b in self._action_buttons:
            b.configure(bg=bg, fg=muted, activebackground=surf, activeforeground=text)
        for e in (self.title_entry, self.tools_entry, self.note_entry):
            e.configure(bg=bg, fg=text, insertbackground=text,
                        disabledbackground=bg, disabledforeground=muted)
        self._update_tracker()

        # Outer border effect via highlight
        self.root.configure(highlightthickness=1,
                            highlightbackground=t["surface"],
                            highlightcolor=t["accent"])

    def _all_full_widgets(self):
        def children(w):
            yield w
            for c in w.winfo_children():
                yield from children(c)
        return list(children(self.full_frame))

    def _pick_theme(self) -> None:
        choices = [t for t in THEMES if t != self.prev_theme]
        t = random.choice(choices) if choices else self.theme
        self.prev_theme = t
        self._apply_theme(t)

    # ── Expand / collapse ─────────────────────────────────────────────────────

    def _on_mini_click(self, e: tk.Event) -> None:
        # Only toggle if not dragging
        if getattr(self, "_moved", False):
            self._moved = False
            return
        self._moved = False
        if self.state == "intro" and not self.expanded:
            self._expand()
        elif self.expanded:
            self._collapse()
        else:
            self._expand()

    def _expand(self, note: bool = False) -> None:
        self.expanded = True
        h = NOTE_H if note else FULL_H
        self._resize(FULL_W, h)
        self.full_frame.place(x=0, y=0, width=FULL_W, height=h)
        self.mini_frame.place_forget()
        # Show/hide intro vs action
        if self.state == "intro":
            self.intro_frame.pack(fill="x", padx=14, pady=(10, 0))
            self.action_frame.pack_forget()
            self.note_frame.pack_forget()
            self.btn_primary.configure(text="Lock In →", command=self._start_run)
            self.btn_primary.pack(fill="x", padx=14, pady=(12, 0))
            self.title_entry.focus_set()
        elif self.state == "note":
            self.intro_frame.pack_forget()
            self.action_frame.pack(fill="x", padx=14, pady=(8, 0))
            self.note_frame.pack(fill="x", pady=(8, 0))
            self.btn_primary.configure(text="Continue →", command=self._finish_note)
            self.btn_primary.pack(fill="x", padx=14, pady=(12, 0))
            self.note_entry.focus_set()
        elif self.state in ("countdown",):
            self.intro_frame.pack_forget()
            self.note_frame.pack_forget()
            self.action_frame.pack(fill="x", padx=14, pady=(8, 0))
            self.btn_primary.pack_forget()
        elif self.state == "finished":
            self.intro_frame.pack_forget()
            self.note_frame.pack_forget()
            self.action_frame.pack_forget()
            self.btn_primary.configure(text="Close", command=self.root.destroy)
            self.btn_primary.pack(fill="x", padx=14, pady=(12, 0))

    def _collapse(self) -> None:
        self.expanded = False
        self.full_frame.place_forget()
        self.mini_frame.place(x=0, y=0, width=MINI_W, height=MINI_H)
        self._resize(MINI_W, MINI_H)

    def _show_mini(self) -> None:
        if not self.expanded:
            self.mini_frame.place(x=0, y=0, width=MINI_W, height=MINI_H)

    # ── Session flow ──────────────────────────────────────────────────────────

    def _handle_return(self, _=None) -> str:
        if self.state == "intro":
            self._start_run()
        elif self.state == "note":
            self._finish_note()
        return "break"

    def _handle_panic(self, _=None) -> str:
        if self.state == "intro":
            self.panic_mode = True
            self._start_run()
        return "break"

    def _handle_quit(self, _=None) -> str:
        import tkinter.messagebox as mb
        if mb.askyesno("Quit", "Exit Lock-In Engine?"):
            if self.after_id:
                self.root.after_cancel(self.after_id)
            self.watcher.stop()
            self.root.destroy()
        return "break"

    def _start_run(self) -> None:
        title = self.sv_title.get().strip() or "Lock-In"
        self.run_title = title
        raw = [x.strip() for x in self.sv_tools.get().split(",") if x.strip()]
        self.allowed_tools = raw or ["Canvas", "PDFs", "Goodnotes", "ChatGPT"]
        self.session_log = SessionLogger(title, self.allowed_tools)
        self.capture_count = 0
        self.drift_secs    = 0
        self.block_index   = 0
        self.total_done    = 0
        self._collapse()
        self.sv_line.set(title)
        self.sv_sub.set("starting…")
        if self.panic_mode:
            self.panic_mode = False
            self._start_countdown(3, "Just survive 3 minutes.", panic=True)
        else:
            self._start_next_block()

    def _start_next_block(self) -> None:
        if self.block_index >= len(SESSION_PLAN):
            self._finish_run()
            return
        self._pick_theme()
        self.block_mins = SESSION_PLAN[self.block_index]
        idx = self.block_index + 1
        total = len(SESSION_PLAN)
        if idx == 1:
            line, charm = "Only 5 minutes. That's it.", "tiny start"
        elif self.block_mins == 10:
            line, charm = "10 minutes. Settle in.", "getting warmer"
        elif self.block_mins == 15:
            line, charm = "15 minutes. Let it click.", "warm-up almost done"
        elif idx == 4:
            line, charm = "Now lock in. 30 minutes.", "deep focus starts here"
        else:
            line, charm = f"Block {idx}/{total}. Hold the line.", "keep the streak"
        self.sv_charm.set(charm)
        self._start_countdown(self.block_mins, line, panic=False)

    def _start_countdown(self, mins: int, line: str, panic: bool) -> None:
        self.state    = "countdown"
        self.secs_left = mins * 60
        self.block_mins = mins
        self.msg_index  = 0
        self.sv_line.set(line)
        self.sv_sub.set("keep your eyes here")
        self.sv_timer.set(fmt(self.secs_left))
        self.sv_prog.set(
            f"{self.total_done}/{TOTAL_MINUTES} min done  ·  block {self.block_index+1}/{len(SESSION_PLAN)}"
            if not panic else "panic mode"
        )
        self.watcher.set_active(True)
        self._update_tracker()
        if self.after_id:
            self.root.after_cancel(self.after_id)
        self._tick(panic)

    def _tick(self, panic: bool) -> None:
        self.sv_timer.set(fmt(self.secs_left))
        if self.secs_left <= 0:
            self.watcher.set_active(False)
            if panic:
                if self.session_log:
                    self.session_log.append("Panic block complete")
                self.sv_line.set("Back to the line.")
                self.sv_sub.set("real run starts now")
                self._chime(2)
                self.after_id = self.root.after(1200, self._start_next_block)
            else:
                self.total_done += self.block_mins
                self._show_note_prompt()
            return

        # Periodic messages
        if self.secs_left % 60 == 0 and self.secs_left != self.block_mins * 60:
            self.sv_sub.set(MESSAGES[self.msg_index % len(MESSAGES)])
            self.msg_index += 1
            if not panic and self.block_mins >= 30 and self.secs_left % (6 * 60) == 0:
                self.root.after(200, lambda: self._popup("return"))

        self.secs_left -= 1
        self.after_id = self.root.after(1000, lambda: self._tick(panic))

    def _show_note_prompt(self) -> None:
        self.state = "note"
        idx = self.block_index + 1
        total = len(SESSION_PLAN)
        self.sv_line.set("Time.")
        self.sv_sub.set("One line. What just happened?" if idx < 3 else "Don't stop here.")
        self.sv_timer.set(fmt(self.block_mins * 60))
        self.sv_charm.set("little check-in")
        self.sv_prog.set(f"{self.total_done}/{TOTAL_MINUTES} min complete")
        self.sv_note.set("")
        self._chime(1)
        self._expand(note=True)
        self._update_tracker()

    def _finish_note(self) -> None:
        note = self.sv_note.get().strip() or "No note."
        if self.session_log:
            self.session_log.block_complete(
                self.block_index + 1, len(SESSION_PLAN), self.block_mins, note
            )
        self.block_index += 1
        self._update_tracker()
        self._collapse()
        self._start_next_block()

    def _finish_run(self) -> None:
        self.state = "finished"
        if self.after_id:
            self.root.after_cancel(self.after_id)
        self.watcher.set_active(False)
        self._pick_theme()
        self.sv_line.set("3 hours. Done.")
        self.sv_sub.set("you stayed in it")
        self.sv_timer.set("DONE")
        self.sv_charm.set("done is cute too")
        self.sv_prog.set(
            f"{self.total_done} min done  ·  {self.capture_count} distractions  ·  ~{self.drift_secs}s drift"
        )
        if self.session_log:
            self.session_log.finish(self.total_done, self.drift_secs, self.capture_count)
        self._chime(3)
        self._update_tracker()
        self._expand()

    # ── Focus watcher callbacks ───────────────────────────────────────────────

    def _on_drift(self, app: str, secs: int) -> None:
        self.is_drifting = True
        self.drift_secs += secs
        if self.session_log:
            self.session_log.drift(app, secs)
        t = self.theme
        self.drift_lbl.configure(fg=t["danger"])
        self.drift_full.configure(fg=t["danger"])
        self.sv_drift.set(f"● {app} ({secs}s)")
        # Subtle border flash
        self.root.configure(highlightbackground=t["danger"])
        self.root.after(3000, lambda: self.root.configure(highlightbackground=t["surface"]))

    def _on_return(self) -> None:
        self.is_drifting = False
        t = self.theme
        self.drift_lbl.configure(fg=t["muted"])
        self.drift_full.configure(fg=t["muted"])
        self.sv_drift.set("● focused")

    # ── Popups ────────────────────────────────────────────────────────────────

    def _popup(self, kind: str) -> None:
        win = tk.Toplevel(self.root)
        win.title("")
        win.resizable(False, False)
        win.attributes("-topmost", True)
        t = self.theme
        win.configure(bg=t["surface"])
        win.overrideredirect(True)

        # Center on screen
        win.update_idletasks()
        pw, ph = 360, 260
        sx = self.root.winfo_x() + (FULL_W - pw) // 2
        sy = self.root.winfo_y() + 80
        win.geometry(f"{pw}x{ph}+{sx}+{sy}")

        frame = tk.Frame(win, bg=t["surface"], padx=20, pady=16)
        frame.pack(fill="both", expand=True)

        def lbl(text, bold=False, color=None):
            tk.Label(frame, text=text,
                     font=("Helvetica", 12, "bold" if bold else "normal"),
                     bg=t["surface"], fg=color or t["text"],
                     wraplength=pw - 50, justify="left",
                     anchor="w").pack(fill="x", pady=(0, 4))

        def entry_var():
            sv = tk.StringVar()
            e = tk.Entry(frame, textvariable=sv,
                         font=("Helvetica", 12), relief="flat",
                         bg=t["bg"], fg=t["text"],
                         insertbackground=t["text"], justify="center")
            e.pack(fill="x", ipady=6, pady=(0, 8))
            e.focus_set()
            return sv

        def btn(text, cmd, primary=True):
            tk.Button(frame, text=text,
                      font=("Helvetica", 12, "bold"),
                      bg=t["accent"] if primary else t["bg"],
                      fg=t["bg"] if primary else t["muted"],
                      relief="flat", bd=0, padx=10, pady=8,
                      command=cmd).pack(fill="x", pady=2)

        def close_popup():
            win.destroy()

        if kind == "allowed":
            lbl("Allowed tools", bold=True)
            sv = entry_var()
            sv.set(", ".join(self.allowed_tools))
            def save():
                raw = [x.strip() for x in sv.get().split(",") if x.strip()]
                if raw: self.allowed_tools = raw
                close_popup()
            btn("Save", save)
            btn("Cancel", close_popup, primary=False)

        elif kind == "intention":
            lbl("Open with intention", bold=True)
            lbl("Tool or app", color=t["muted"])
            sv_tool = entry_var()
            lbl("Reason", color=t["muted"])
            sv_reason = entry_var()
            def save():
                tool   = sv_tool.get().strip() or "unspecified"
                reason = sv_reason.get().strip() or "no reason"
                if self.session_log:
                    self.session_log.capture("intent", "study_tool", tool, reason)
                self.sv_sub.set(f"open {tool} for: {reason}")
                close_popup()
            btn("Log intention →", save)
            btn("Cancel", close_popup, primary=False)

        elif kind == "capture":
            lbl("Capture distraction", bold=True)
            lbl("What is it?", color=t["muted"])
            sv_target = entry_var()
            lbl("Notes (optional)", color=t["muted"])
            sv_notes = entry_var()
            def save():
                target = sv_target.get().strip() or "uncategorized"
                notes  = sv_notes.get().strip() or ""
                if self.session_log:
                    self.session_log.capture("capture", "distraction", target, notes)
                self.capture_count += 1
                self.sv_charm.set(f"captured: {target[:28]}")
                close_popup()
            btn("Capture and return →", save)
            btn("Cancel", close_popup, primary=False)

        elif kind == "return":
            lbl("Return mode", bold=True)
            lbl("Are you still on the task you named?", color=t["muted"])
            def yes():
                if self.session_log:
                    self.session_log.capture("return_check", "yes", "on_task", "confirmed")
                self.sv_sub.set("good. stay with it.")
                close_popup()
            def reset():
                if self.session_log:
                    self.session_log.capture("return_check", "reset", "recenter", "needed reset")
                self.sv_sub.set("back to the tab you meant to open.")
                close_popup()
            btn("Yes, I'm still there →", yes)
            btn("Reset me — I drifted", reset, primary=False)
            btn("Break Glass", lambda: (close_popup(), self._popup("break")), primary=False)

        elif kind == "break":
            lbl("Break Glass", bold=True)
            lbl("Name it before you do it.", color=t["muted"])
            lbl("Leaving for?", color=t["muted"])
            sv_target = entry_var()
            lbl("Why now?", color=t["muted"])
            sv_notes = entry_var()
            def capture_instead():
                t2 = sv_target.get().strip() or "unspecified"
                n  = sv_notes.get().strip() or ""
                if self.session_log:
                    self.session_log.capture("break_glass", "captured_instead", t2, n)
                self.capture_count += 1
                close_popup()
            def continue_anyway():
                t2 = sv_target.get().strip() or "unspecified"
                n  = sv_notes.get().strip() or ""
                if self.session_log:
                    self.session_log.capture("break_glass", "override", t2, n)
                self.sv_sub.set("fine. make it brief.")
                close_popup()
            btn("Capture instead →", capture_instead)
            btn("Continue anyway", continue_anyway, primary=False)

        # Click outside to dismiss
        win.bind("<Escape>", lambda e: close_popup())
        win.bind("<FocusOut>", lambda e: win.after(100, lambda: win.destroy() if not win.focus_get() else None))

    # ── Audio ─────────────────────────────────────────────────────────────────

    def _chime(self, n: int) -> None:
        def ring(count):
            if count <= 0: return
            self.root.bell()
            self.root.after(220, lambda: ring(count - 1))
        ring(n)


# ── Entry ─────────────────────────────────────────────────────────────────────

def main() -> int:
    root = tk.Tk()
    app  = LockInEngine(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        sys.exit(130)
