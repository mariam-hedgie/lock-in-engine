#!/usr/bin/env python3
"""
Lock-In Engine — corner overlay focus timer for macOS.
Double-click run.command  or  python3 lock_in.py
"""

from __future__ import annotations

import random
import sys
import tkinter as tk
from tkinter import messagebox
from typing import Optional

from config import (
    CORNER, CORNER_MARGIN,
    MINI_W, MINI_H, FULL_W, FULL_H,
    SESSION_PLAN, TOTAL_MINUTES,
    MESSAGES, THEMES,
)
from focus_watcher import FocusWatcher
from url_watcher import URLWatcher
from logger import SessionLogger

TOTAL_BLOCKS = len(SESSION_PLAN)

ANIM_STEP  = 18   # px per frame
ANIM_DELAY = 12   # ms between frames
NOTE_SECS  = 25   # seconds to wait before auto-advancing past note prompt


def fmt(secs: int) -> str:
    secs = max(0, secs)
    return f"{secs // 60:02d}:{secs % 60:02d}"


class LockInEngine:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Lock-In")
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.96)
        self.root.overrideredirect(True)
        self.root.resizable(True, True)
        self.root.protocol("WM_DELETE_WINDOW", self._handle_quit)

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
        self._anim_id: Optional[str] = None
        self.block_index    = 0
        self.secs_left      = 0
        self.block_mins     = 0
        self.total_done     = 0
        self.capture_count  = 0
        self.msg_index      = 0
        self.tick_id: Optional[str] = None
        self.panic_mode     = False
        self.run_title      = "Lock-In"
        self.allowed_tools  = ["Canvas", "PDFs", "Goodnotes", "ChatGPT"]
        self.session_log: Optional[SessionLogger] = None
        self.drift_secs     = 0
        self.intentions_logged = 0
        self.return_checks = 0
        self.break_glass_count = 0
        self.later_tasks: list[dict[str, str]] = []
        self._session_finalized = False
        self.is_drifting    = False
        self.theme          = THEMES[0]
        self.prev_theme: Optional[dict] = None
        self._moved         = False
        self._cur_w         = MINI_W
        self._cur_h         = MINI_H
        self._note_secs     = NOTE_SECS
        self._drag_ox       = 0
        self._drag_oy       = 0

        # ── StringVars ────────────────────────────────────────────────────────
        self.sv_timer  = tk.StringVar(value="00:00")
        self.sv_line   = tk.StringVar(value="Lock-In")
        self.sv_sub    = tk.StringVar(value="click ▸ to open")
        self.sv_charm  = tk.StringVar(value="tiny start → deep focus")
        self.sv_prog   = tk.StringVar(value="5 · 10 · 15 · 30 · 30 · 30 · 30 · 30")
        self.sv_title  = tk.StringVar()
        self.sv_tools  = tk.StringVar(value="Canvas, PDFs, Goodnotes, ChatGPT")
        self.sv_note   = tk.StringVar()
        self.sv_theme  = tk.StringVar(value="Matcha Night")
        self.sv_drift  = tk.StringVar(value="● focused")
        self.sv_toggle = tk.StringVar(value="▸")

        self._build_ui()
        self._place_window(MINI_W, MINI_H)
        self._apply_theme(self.theme)

        self.watcher = FocusWatcher(
            own_app_names=["python", "python3", "lock-in"],
            on_drift=self._on_drift,
            on_return=self._on_return,
        )
        self.watcher.start()

        # URL watcher — receives tab changes from the Chrome extension
        self.url_watcher = URLWatcher(
            on_drift=self._on_drift,
            on_return=self._on_return,
        )
        self.url_watcher.start()

        self.root.bind("<Return>",    self._handle_return)
        self.root.bind("<Escape>",    lambda e: self._animate_to(False))
        self.root.bind("<Control-p>", self._handle_panic)
        self.root.bind("<Control-q>", self._handle_quit)
        self.root.bind("<Control-Q>", self._handle_quit)

    # ── Window geometry ───────────────────────────────────────────────────────

    def _place_window(self, w: int, h: int) -> None:
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        m  = CORNER_MARGIN
        if CORNER == "bottom-right":
            x, y = sw - w - m, sh - h - m - 40
        elif CORNER == "bottom-left":
            x, y = m, sh - h - m - 40
        elif CORNER == "top-right":
            x, y = sw - w - m, m + 28
        else:
            x, y = m, m + 28
        self.root.geometry(f"{w}x{h}+{x}+{y}")
        self._cur_w, self._cur_h = w, h

    def _set_size(self, w: int, h: int) -> None:
        cx = self.root.winfo_x()
        cy = self.root.winfo_y()
        self.root.geometry(f"{w}x{h}+{cx}+{cy}")
        self._cur_w, self._cur_h = w, h
        self.mini_frame.place_configure(width=w, height=h)
        if self.expanded:
            self.full_frame.place_configure(width=w, height=h)

    # ── Drag ─────────────────────────────────────────────────────────────────

    def _drag_start(self, e: tk.Event) -> None:
        self._drag_ox = e.x_root - self.root.winfo_x()
        self._drag_oy = e.y_root - self.root.winfo_y()
        self._moved   = False

    def _drag_motion(self, e: tk.Event) -> None:
        self._moved = True
        self.root.geometry(f"+{e.x_root - self._drag_ox}+{e.y_root - self._drag_oy}")

    # ── Build UI ──────────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        self.root.configure(bg="#0f1410")

        # ─── Mini strip ───────────────────────────────────────────────────
        self.mini_frame = tk.Frame(self.root, bd=0, highlightthickness=0)
        self.mini_frame.place(x=0, y=0, width=MINI_W, height=MINI_H)
        self.mini_frame.bind("<Button-1>",       self._drag_start)
        self.mini_frame.bind("<B1-Motion>",       self._drag_motion)
        self.mini_frame.bind("<ButtonRelease-1>", self._mini_click)

        self.toggle_btn = tk.Button(
            self.mini_frame, textvariable=self.sv_toggle,
            font=("Menlo", 15, "bold"), relief="flat", bd=0, cursor="hand2",
            padx=8, pady=4,
            command=self._toggle,
        )
        self.toggle_btn.place(relx=1.0, y=6, anchor="ne", x=-6)

        self.drift_mini = tk.Label(
            self.mini_frame, textvariable=self.sv_drift,
            font=("Menlo", 10, "bold"), anchor="w",
        )
        self.drift_mini.place(x=8, y=6)

        self.mini_line = tk.Label(
            self.mini_frame, textvariable=self.sv_line,
            font=("Georgia", 11, "italic"),
            wraplength=MINI_W - 24, justify="center",
        )
        self.mini_line.place(relx=0.5, y=22, anchor="n")

        self.timer_mini = tk.Label(
            self.mini_frame, textvariable=self.sv_timer,
            font=("Menlo", 34, "bold"), anchor="center",
        )
        self.timer_mini.place(relx=0.5, rely=0.5, anchor="center", y=6)
        self.timer_mini.bind("<Button-1>",       self._drag_start)
        self.timer_mini.bind("<B1-Motion>",       self._drag_motion)
        self.timer_mini.bind("<ButtonRelease-1>", self._mini_click)

        self.charm_mini = tk.Label(
            self.mini_frame, textvariable=self.sv_charm,
            font=("Menlo", 10),
        )
        self.charm_mini.place(relx=0.5, rely=1.0, anchor="s", y=-5)

        # ─── Full panel ────────────────────────────────────────────────────
        self.full_frame = tk.Frame(self.root, bd=0, highlightthickness=0)

        # Header
        hdr = tk.Frame(self.full_frame, bd=0)
        hdr.pack(fill="x", padx=10, pady=(8, 0))
        self.theme_badge = tk.Label(
            hdr, textvariable=self.sv_theme,
            font=("Menlo", 10, "bold"), padx=10, pady=4,
        )
        self.theme_badge.pack(side="left")
        tk.Button(
            hdr, text="▴ collapse",
            font=("Menlo", 10, "bold"), relief="flat", bd=0, cursor="hand2",
            padx=8, pady=4,
            command=lambda: self._animate_to(False),
        ).pack(side="right")

        self.drift_full = tk.Label(
            self.full_frame, textvariable=self.sv_drift,
            font=("Menlo", 11, "bold"), anchor="center",
        )
        self.drift_full.pack(fill="x", padx=10)

        self.main_lbl = tk.Label(
            self.full_frame, textvariable=self.sv_line,
            font=("Georgia", 17, "italic"),
            wraplength=FULL_W - 30, justify="center",
        )
        self.main_lbl.pack(fill="x", padx=12, pady=(6, 0))

        self.sub_lbl = tk.Label(
            self.full_frame, textvariable=self.sv_sub,
            font=("Helvetica", 12),
            wraplength=FULL_W - 30, justify="center",
        )
        self.sub_lbl.pack(fill="x", padx=12)

        self.timer_big = tk.Label(
            self.full_frame, textvariable=self.sv_timer,
            font=("Menlo", 62, "bold"), anchor="center",
        )
        self.timer_big.pack(fill="x", pady=(2, 0))

        self.prog_lbl = tk.Label(
            self.full_frame, textvariable=self.sv_prog,
            font=("Menlo", 11, "bold"),
            wraplength=FULL_W - 20, justify="center",
        )
        self.prog_lbl.pack(fill="x", padx=10)

        self.tracker_row = tk.Frame(self.full_frame, bd=0)
        self.tracker_row.pack(fill="x", padx=12, pady=(6, 0))
        self.tracker_dots: list[tk.Label] = []
        self._build_tracker()

        self.charm_full = tk.Label(
            self.full_frame, textvariable=self.sv_charm,
            font=("Menlo", 11, "bold"),
        )
        self.charm_full.pack(pady=(4, 0))

        tk.Frame(self.full_frame, height=1).pack(fill="x", padx=12, pady=(8, 0))

        # Intro fields
        self.intro_frame = tk.Frame(self.full_frame, bd=0)
        tk.Label(
            self.intro_frame, text="Run title",
            font=("Helvetica", 12, "bold"), anchor="w",
        ).pack(fill="x", padx=14)
        self.title_entry = tk.Entry(
            self.intro_frame, textvariable=self.sv_title,
            font=("Helvetica", 14), relief="flat", justify="center",
        )
        self.title_entry.pack(fill="x", ipady=8, padx=14, pady=(2, 8))
        tk.Label(
            self.intro_frame, text="Allowed tools",
            font=("Helvetica", 12, "bold"), anchor="w",
        ).pack(fill="x", padx=14)
        self.tools_entry = tk.Entry(
            self.intro_frame, textvariable=self.sv_tools,
            font=("Helvetica", 13), relief="flat", justify="center",
        )
        self.tools_entry.pack(fill="x", ipady=8, padx=14, pady=(2, 0))

        # Note field
        self.note_frame = tk.Frame(self.full_frame, bd=0)
        tk.Label(
            self.note_frame, text="One line — what just happened?",
            font=("Helvetica", 12, "bold"), anchor="w",
        ).pack(fill="x", padx=14)
        self.note_entry = tk.Entry(
            self.note_frame, textvariable=self.sv_note,
            font=("Helvetica", 13), relief="flat", justify="center",
        )
        self.note_entry.pack(fill="x", ipady=8, padx=14, pady=(2, 0))

        # Primary button
        self.btn_primary = tk.Button(
            self.full_frame, text="Lock In →",
            font=("Helvetica", 14, "bold"),
            relief="flat", bd=0, padx=12, pady=12,
            command=self._start_run,
        )
        self.btn_primary.pack(fill="x", padx=14, pady=(10, 0))

        # Action buttons
        self.action_row = tk.Frame(self.full_frame, bd=0)
        self.action_row.pack(fill="x", padx=14, pady=(7, 0))
        self._action_btns: list[tk.Button] = []
        for idx, (label, cmd) in enumerate((
            ("Tools",     lambda: self._popup("allowed")),
            ("Intention", lambda: self._popup("intention")),
            ("Later",     lambda: self._popup("later")),
            ("Capture",   lambda: self._popup("capture")),
            ("Return",    lambda: self._popup("return")),
            ("🔴 Glass",  lambda: self._popup("break")),
            ("End Session", self._confirm_end_session),
        )):
            b = tk.Button(
                self.action_row, text=label,
                font=("Helvetica", 11, "bold"),
                relief="flat", bd=0, padx=8, pady=11,
                command=cmd,
            )
            row, col = divmod(idx, 3)
            b.grid(row=row, column=col, sticky="nsew", padx=4, pady=4)
            self._action_btns.append(b)
        for col in range(3):
            self.action_row.grid_columnconfigure(col, weight=1)

        tk.Label(
            self.full_frame,
            text="drag to move  ·  esc to collapse  ·  ctrl+q to quit",
            font=("Menlo", 9),
        ).pack(pady=(6, 6))

    # ── Tracker ───────────────────────────────────────────────────────────────

    def _build_tracker(self) -> None:
        for w in self.tracker_row.winfo_children():
            w.destroy()
        self.tracker_dots = []
        for m in SESSION_PLAN:
            lbl = tk.Label(
                self.tracker_row, text=str(m),
                font=("Menlo", 8, "bold"), width=3, pady=2,
            )
            lbl.pack(side="left", padx=1)
            self.tracker_dots.append(lbl)
        self._refresh_tracker()

    def _refresh_tracker(self) -> None:
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
        bg, surf, acc, muted, text, danger = (
            t["bg"], t["surface"], t["accent"],
            t["muted"], t["text"], t["danger"],
        )
        dc = danger if self.is_drifting else muted

        self.root.configure(bg=bg, highlightthickness=1, highlightbackground=surf)
        self.mini_frame.configure(bg=surf)
        self.full_frame.configure(bg=surf)

        for w in (self.mini_line, self.charm_mini):
            w.configure(bg=surf, fg=muted)
        self.timer_mini.configure(bg=surf, fg=acc)
        self.drift_mini.configure(bg=surf, fg=dc)
        self.toggle_btn.configure(
            bg=surf, fg=acc, activebackground=surf, activeforeground=acc
        )

        def _style(widget: tk.Widget) -> None:
            cls = widget.winfo_class()
            try:
                if cls == "Frame":
                    widget.configure(bg=surf)
                elif cls == "Label":
                    widget.configure(bg=surf, fg=text)
                elif cls == "Button":
                    widget.configure(
                        bg=bg, fg=text,
                        activebackground=acc, activeforeground=bg,
                        highlightthickness=0,
                    )
                elif cls == "Entry":
                    widget.configure(
                        bg=bg, fg=text,
                        insertbackground=text,
                        disabledbackground=bg,
                        disabledforeground=muted,
                    )
            except Exception:
                pass
            for child in widget.winfo_children():
                _style(child)

        _style(self.full_frame)

        self.theme_badge.configure(bg=acc, fg=bg)
        self.timer_big.configure(fg=acc)
        self.charm_full.configure(fg=acc)
        self.drift_full.configure(fg=dc)
        self.btn_primary.configure(
            bg=acc, fg=bg, activebackground=text, activeforeground=bg
        )
        for btn in self._action_btns:
            label = btn.cget("text")
            if label == "End Session":
                btn.configure(
                    bg=danger, fg=bg,
                    activebackground=text, activeforeground=bg,
                )
            elif label in {"Capture", "Later"}:
                btn.configure(
                    bg=acc, fg=bg,
                    activebackground=text, activeforeground=bg,
                )
            else:
                btn.configure(
                    bg=bg, fg=text,
                    activebackground=acc, activeforeground=bg,
                )
        self._refresh_tracker()

    def _pick_theme(self) -> None:
        opts = [t for t in THEMES if t is not self.prev_theme]
        t = random.choice(opts) if opts else self.theme
        self.prev_theme = t
        self._apply_theme(t)

    # ── Expand / collapse animation ───────────────────────────────────────────

    def _toggle(self) -> None:
        self._animate_to(not self.expanded)

    def _mini_click(self, e: tk.Event) -> None:
        if self._moved:
            self._moved = False
            return
        self._animate_to(not self.expanded)

    def _animate_to(self, expanding: bool) -> None:
        if self._anim_id:
            self.root.after_cancel(self._anim_id)
            self._anim_id = None

        target_w = FULL_W if expanding else MINI_W
        target_h = FULL_H if expanding else MINI_H

        if expanding and not self.expanded:
            self.full_frame.place(x=0, y=0, width=self._cur_w, height=self._cur_h)
            self._update_full_content()
            self.expanded = True
            self.sv_toggle.set("▾")

        def _step() -> None:
            cw, ch = self._cur_w, self._cur_h
            dw = target_w - cw
            dh = target_h - ch
            if abs(dw) <= ANIM_STEP and abs(dh) <= ANIM_STEP:
                self._set_size(target_w, target_h)
                if not expanding:
                    self.full_frame.place_forget()
                    self.expanded = False
                    self.sv_toggle.set("▸")
                self._anim_id = None
                return
            step_w = ANIM_STEP if dw > 0 else (-ANIM_STEP if dw < 0 else 0)
            step_h = ANIM_STEP if dh > 0 else (-ANIM_STEP if dh < 0 else 0)
            self._set_size(cw + step_w, ch + step_h)
            self._anim_id = self.root.after(ANIM_DELAY, _step)

        _step()

    def _update_full_content(self) -> None:
        self.intro_frame.pack_forget()
        self.note_frame.pack_forget()
        self.action_row.pack_forget()
        self.btn_primary.pack_forget()

        if self.state == "intro":
            self.intro_frame.pack(fill="x", pady=(4, 0))
            self.btn_primary.configure(text="Lock In →", command=self._start_run)
            self.btn_primary.pack(fill="x", padx=14, pady=(10, 0))
            self.root.after(50, lambda: self.title_entry.focus_set())

        elif self.state == "note":
            self.note_frame.pack(fill="x", pady=(4, 0))
            self.action_row.pack(fill="x", padx=14, pady=(7, 0))
            self.btn_primary.configure(text="Continue →", command=self._finish_note)
            self.btn_primary.pack(fill="x", padx=14, pady=(10, 0))
            self.root.after(50, lambda: self.note_entry.focus_set())

        elif self.state == "countdown":
            self.action_row.pack(fill="x", padx=14, pady=(7, 0))

        elif self.state == "finished":
            self.btn_primary.configure(text="Close", command=self._shutdown)
            self.btn_primary.pack(fill="x", padx=14, pady=(10, 0))

    # ── Keyboard ──────────────────────────────────────────────────────────────

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
        if self.state == "finished":
            if messagebox.askyesno("Quit", "Close Lock-In Engine?"):
                self._shutdown()
        elif self.state in {"countdown", "note"} and self.session_log:
            if messagebox.askyesno("Quit", "Exit and end this session?"):
                self._end_session("Quit app", close_after=True)
        else:
            if messagebox.askyesno("Quit", "Exit Lock-In Engine?"):
                self._shutdown()
        return "break"

    # ── Session flow ──────────────────────────────────────────────────────────

    def _start_run(self) -> None:
        title = self.sv_title.get().strip() or "Lock-In"
        self.run_title = title
        raw = [x.strip() for x in self.sv_tools.get().split(",") if x.strip()]
        self.allowed_tools = raw or ["Canvas", "PDFs", "Goodnotes", "ChatGPT"]
        self.session_log   = SessionLogger(title, self.allowed_tools)
        self.capture_count = 0
        self.drift_secs    = 0
        self.intentions_logged = 0
        self.return_checks = 0
        self.break_glass_count = 0
        self.later_tasks = []
        self._session_finalized = False
        self.block_index   = 0
        self.total_done    = 0

        self._animate_to(False)
        self.sv_line.set(title)
        self.sv_sub.set("starting…")

        if self.panic_mode:
            self.panic_mode = False
            self._start_countdown(3, "Survive 3 minutes.", panic=True)
        else:
            self._start_next_block()

    def _start_next_block(self) -> None:
        if self.block_index >= TOTAL_BLOCKS:
            self._finish_run()
            return
        self._pick_theme()
        self.block_mins = SESSION_PLAN[self.block_index]
        idx = self.block_index + 1
        if idx == 1:
            line, charm = "Only 5 minutes. That's it.", "tiny start"
        elif self.block_mins == 10:
            line, charm = "10 minutes. Settle in.", "getting warmer"
        elif self.block_mins == 15:
            line, charm = "15 minutes. Let it click.", "almost warm"
        elif idx == 4:
            line, charm = "Lock in. 30 minutes.", "deep focus starts here"
        else:
            line, charm = f"Block {idx}/{TOTAL_BLOCKS}. Hold the line.", "keep the streak"
        self.sv_charm.set(charm)
        self._start_countdown(self.block_mins, line, panic=False)

    def _start_countdown(self, mins: int, line: str, panic: bool) -> None:
        self.state      = "countdown"
        self.secs_left  = mins * 60
        self.block_mins = mins
        self.msg_index  = 0
        self.sv_line.set(line)
        self.sv_sub.set("eyes on the page")
        self.sv_timer.set(fmt(self.secs_left))
        self.sv_prog.set(
            f"{self.total_done}/{TOTAL_MINUTES} min · block {self.block_index+1}/{TOTAL_BLOCKS}"
            if not panic else "panic mode · breathe"
        )
        self.watcher.set_active(True)
        self.url_watcher.set_active(True)
        self._refresh_tracker()
        if self.tick_id:
            self.root.after_cancel(self.tick_id)
        self._tick(panic)

    def _tick(self, panic: bool) -> None:
        self.sv_timer.set(fmt(self.secs_left))
        if self.secs_left <= 0:
            self.watcher.set_active(False)
            self.url_watcher.set_active(False)
            self._chime(1)
            if panic:
                if self.session_log:
                    self.session_log.append("Panic block complete")
                self.sv_line.set("Back to the line.")
                self.sv_sub.set("real run starts now")
                self.tick_id = self.root.after(1200, self._start_next_block)
            else:
                self.total_done += self.block_mins
                self._begin_note_prompt()
            return

        if self.secs_left % 60 == 0 and self.secs_left != self.block_mins * 60:
            self.sv_sub.set(MESSAGES[self.msg_index % len(MESSAGES)])
            self.msg_index += 1
            if not panic and self.block_mins >= 30 and self.secs_left % (6 * 60) == 0:
                self.root.after(300, lambda: self._popup("return"))

        self.secs_left -= 1
        self.tick_id = self.root.after(1000, lambda: self._tick(panic))

    def _begin_note_prompt(self) -> None:
        """Show note prompt, auto-advance after NOTE_SECS if no input."""
        self.state = "note"
        idx = self.block_index + 1
        self.sv_line.set("Time.")
        self.sv_timer.set(fmt(self.block_mins * 60))
        self.sv_charm.set("little check-in")
        self.sv_prog.set(f"{self.total_done}/{TOTAL_MINUTES} min complete")
        self.sv_note.set("")
        self._refresh_tracker()
        self._animate_to(True)
        self._note_secs = NOTE_SECS
        self._note_countdown()

    def _note_countdown(self) -> None:
        if self.state != "note":
            return
        if self._note_secs <= 0:
            self._finish_note()
            return
        self.sv_sub.set(f"quick note · auto-advancing in {self._note_secs}s")
        self._note_secs -= 1
        self.tick_id = self.root.after(1000, self._note_countdown)

    def _finish_note(self) -> None:
        if self.tick_id:
            self.root.after_cancel(self.tick_id)
            self.tick_id = None
        note = self.sv_note.get().strip() or "—"
        if self.session_log:
            self.session_log.block_complete(
                self.block_index + 1, TOTAL_BLOCKS, self.block_mins, note
            )
        self.block_index += 1
        self._refresh_tracker()
        self._animate_to(False)
        self.root.after(320, self._start_next_block)

    def _finish_run(self) -> None:
        self.state = "finished"
        if self.tick_id:
            self.root.after_cancel(self.tick_id)
            self.tick_id = None
        self.watcher.set_active(False)
        self.url_watcher.set_active(False)
        self._pick_theme()
        self.sv_line.set("3 hours. Done.")
        self.sv_sub.set("session report ready")
        self.sv_timer.set("DONE")
        self.sv_charm.set("done is cute too")
        self.sv_prog.set(self._summary_line())
        self._finalize_session("Completed full plan")
        self._chime(3)
        self._refresh_tracker()
        self._animate_to(True)
        self._show_report("Completed full plan")

    def _summary_metrics(self) -> dict[str, int | str]:
        blocks_completed = 0
        running_total = 0
        for mins in SESSION_PLAN:
            running_total += mins
            if self.total_done >= running_total:
                blocks_completed += 1
        focus_score = max(
            0,
            min(
                100,
                int(round(((max(self.total_done * 60 - self.drift_secs, 0)) /
                           max(self.total_done * 60, 1)) * 100)),
            ),
        )
        return {
            "blocks_completed": blocks_completed,
            "intentions": self.intentions_logged,
            "return_checks": self.return_checks,
            "break_glass": self.break_glass_count,
            "later_tasks": len(self.later_tasks),
            "focus_score": focus_score,
        }

    def _summary_line(self) -> str:
        metrics = self._summary_metrics()
        return (
            f"{self.total_done}/{TOTAL_MINUTES} min · "
            f"{self.capture_count} captures · "
            f"{len(self.later_tasks)} later tasks · "
            f"~{self.drift_secs}s drift · "
            f"{metrics['focus_score']}% focus"
        )

    def _report_text(self, reason: str) -> str:
        metrics = self._summary_metrics()
        lines = [
            f"Reason: {reason}",
            f"Completed: {self.total_done}/{TOTAL_MINUTES} minutes",
            f"Blocks done: {metrics['blocks_completed']}/{TOTAL_BLOCKS}",
            f"Focus score: {metrics['focus_score']}%",
            f"Drift logged: ~{self.drift_secs} seconds",
            f"Intentions logged: {self.intentions_logged}",
            f"Distractions captured: {self.capture_count}",
            f"Return checks: {self.return_checks}",
            f"Break glass events: {self.break_glass_count}",
            f"Later tasks parked: {len(self.later_tasks)}",
        ]
        if self.later_tasks:
            lines.append("")
            lines.append("For later:")
            for idx, item in enumerate(self.later_tasks, start=1):
                task = item.get("task", "Untitled task")
                note = item.get("notes", "").strip()
                lines.append(f"{idx}. {task}" + (f" — {note}" if note else ""))
        return "\n".join(lines)

    def _finalize_session(self, reason: str) -> None:
        if self._session_finalized or not self.session_log:
            return
        metrics = self._summary_metrics()
        self.session_log.finish(
            self.total_done,
            self.drift_secs,
            self.capture_count,
            self.later_tasks,
            metrics,
            reason,
        )
        self._session_finalized = True

    def _show_report(self, reason: str) -> None:
        messagebox.showinfo("Session report", self._report_text(reason))

    def _shutdown(self) -> None:
        if self.tick_id:
            self.root.after_cancel(self.tick_id)
            self.tick_id = None
        self.watcher.stop()
        self.url_watcher.stop()
        self.root.destroy()

    def _end_session(self, reason: str, close_after: bool) -> None:
        self.state = "finished"
        if self.tick_id:
            self.root.after_cancel(self.tick_id)
            self.tick_id = None
        self.watcher.set_active(False)
        self.url_watcher.set_active(False)
        self.sv_line.set("Session ended.")
        self.sv_sub.set("report saved to logs")
        self.sv_timer.set("DONE")
        self.sv_charm.set("you can pick it back up later")
        self.sv_prog.set(self._summary_line())
        self._finalize_session(reason)
        self._show_report(reason)
        if close_after:
            self._shutdown()
        else:
            self._animate_to(True)

    def _confirm_end_session(self) -> None:
        if self.state not in {"countdown", "note"}:
            return
        if messagebox.askyesno("End Session", "End this session now and save a report?"):
            self._end_session("Ended early from app", close_after=False)

    # ── Focus watcher callbacks ───────────────────────────────────────────────

    def _on_drift(self, app: str, secs: int) -> None:
        self.is_drifting = True
        self.drift_secs += secs
        if self.session_log:
            self.session_log.drift(app, secs)
        danger = self.theme["danger"]
        self.drift_mini.configure(fg=danger)
        self.drift_full.configure(fg=danger)
        self.sv_drift.set(f"● {app}  {secs}s away")
        self.root.configure(highlightbackground=danger)
        self.root.after(4000, lambda: self.root.configure(
            highlightbackground=self.theme["surface"]
        ))

    def _on_return(self) -> None:
        self.is_drifting = False
        muted = self.theme["muted"]
        self.drift_mini.configure(fg=muted)
        self.drift_full.configure(fg=muted)
        self.sv_drift.set("● focused")

    # ── Popups ────────────────────────────────────────────────────────────────

    def _popup(self, kind: str) -> None:
        win = tk.Toplevel(self.root)
        win.title("")
        win.resizable(False, False)
        win.attributes("-topmost", True)
        win.overrideredirect(True)
        t  = self.theme
        pw = 340
        sx = self.root.winfo_x() + max(0, (self._cur_w - pw) // 2)
        sy = self.root.winfo_y() + 60
        win.geometry(f"{pw}x10+{sx}+{sy}")
        win.configure(bg=t["surface"])

        frame = tk.Frame(win, bg=t["surface"], padx=18, pady=14)
        frame.pack(fill="both", expand=True)

        def lbl(text: str, bold: bool = False, color: Optional[str] = None) -> None:
            tk.Label(
                frame, text=text,
                font=("Helvetica", 12, "bold" if bold else "normal"),
                bg=t["surface"], fg=color or t["text"],
                wraplength=pw - 44, justify="left", anchor="w",
            ).pack(fill="x", pady=(0, 3))

        def entry_field() -> tk.StringVar:
            sv = tk.StringVar()
            e = tk.Entry(
                frame, textvariable=sv,
                font=("Helvetica", 12), relief="flat",
                bg=t["bg"], fg=t["text"],
                insertbackground=t["text"], justify="center",
            )
            e.pack(fill="x", ipady=8, pady=(0, 8))
            e.focus_set()
            return sv

        def btn(text: str, cmd, primary: bool = True) -> None:
            tk.Button(
                frame, text=text,
                font=("Helvetica", 12, "bold"),
                bg=t["accent"] if primary else t["bg"],
                fg=t["bg"] if primary else t["text"],
                relief="flat", bd=0, padx=8, pady=7,
                activebackground=t["text"] if primary else t["accent"],
                activeforeground=t["bg"],
                command=cmd,
            ).pack(fill="x", pady=2)

        def close() -> None:
            win.destroy()

        if kind == "allowed":
            lbl("Allowed tools", bold=True)
            sv = entry_field()
            sv.set(", ".join(self.allowed_tools))
            def save():
                raw = [x.strip() for x in sv.get().split(",") if x.strip()]
                if raw:
                    self.allowed_tools = raw
                close()
            btn("Save", save)
            btn("Cancel", close, primary=False)

        elif kind == "intention":
            lbl("Open with intention", bold=True)
            lbl("Tool or app", color=t["muted"])
            sv_tool   = entry_field()
            lbl("Reason", color=t["muted"])
            sv_reason = entry_field()
            def save():
                tool   = sv_tool.get().strip() or "unspecified"
                reason = sv_reason.get().strip() or "no reason"
                if self.session_log:
                    self.session_log.capture("intent", "study_tool", tool, reason)
                self.intentions_logged += 1
                self.sv_sub.set(f"open {tool} for: {reason}")
                close()
            btn("Log intention →", save)
            btn("Cancel", close, primary=False)

        elif kind == "later":
            lbl("Park it for later", bold=True)
            lbl("What do you need to remember?", color=t["muted"])
            sv_task = entry_field()
            lbl("Context (optional)", color=t["muted"])
            sv_notes = entry_field()
            def save():
                task = sv_task.get().strip() or "Untitled follow-up"
                notes = sv_notes.get().strip()
                item = {"task": task, "notes": notes}
                self.later_tasks.append(item)
                if self.session_log:
                    self.session_log.capture("later_task", "backlog", task, notes)
                self.sv_charm.set(f"saved for later: {task[:24]}")
                close()
            btn("Save for later →", save)
            btn("Cancel", close, primary=False)

        elif kind == "capture":
            lbl("Capture distraction", bold=True)
            lbl("What is it?", color=t["muted"])
            sv_target = entry_field()
            lbl("Notes (optional)", color=t["muted"])
            sv_notes  = entry_field()
            def save():
                target = sv_target.get().strip() or "uncategorized"
                notes  = sv_notes.get().strip() or ""
                if self.session_log:
                    self.session_log.capture("capture", "distraction", target, notes)
                self.capture_count += 1
                self.sv_charm.set(f"captured: {target[:26]}")
                close()
            btn("Capture and return →", save)
            btn("Cancel", close, primary=False)

        elif kind == "return":
            lbl("Return mode", bold=True)
            lbl("Still on task?", color=t["muted"])
            def yes():
                if self.session_log:
                    self.session_log.capture("return_check", "yes", "on_task", "confirmed")
                self.return_checks += 1
                self.sv_sub.set("good. stay with it.")
                close()
            def reset():
                if self.session_log:
                    self.session_log.capture("return_check", "reset", "recenter", "needed reset")
                self.return_checks += 1
                self.sv_sub.set("back to the tab you meant to open.")
                close()
            btn("Yes, still there →", yes)
            btn("Reset me", reset, primary=False)
            btn("Break Glass", lambda: (close(), self._popup("break")), primary=False)

        elif kind == "break":
            lbl("Break Glass", bold=True)
            lbl("Name it before you do it.", color=t["muted"])
            lbl("Leaving for?", color=t["muted"])
            sv_target = entry_field()
            lbl("Why now?", color=t["muted"])
            sv_notes  = entry_field()
            def capture_it():
                t2 = sv_target.get().strip() or "unspecified"
                n  = sv_notes.get().strip() or ""
                if self.session_log:
                    self.session_log.capture("break_glass", "captured_instead", t2, n)
                self.break_glass_count += 1
                self.capture_count += 1
                close()
            def go_anyway():
                t2 = sv_target.get().strip() or "unspecified"
                n  = sv_notes.get().strip() or ""
                if self.session_log:
                    self.session_log.capture("break_glass", "override", t2, n)
                self.break_glass_count += 1
                self.sv_sub.set("fine. make it brief.")
                close()
            btn("Capture instead →", capture_it)
            btn("Continue anyway", go_anyway, primary=False)

        win.update_idletasks()
        win.geometry(f"{pw}x{win.winfo_reqheight()}+{sx}+{sy}")
        win.bind("<Escape>", lambda e: close())

    # ── Audio ─────────────────────────────────────────────────────────────────

    def _chime(self, n: int) -> None:
        def ring(count: int) -> None:
            if count <= 0:
                return
            self.root.bell()
            self.root.after(220, lambda: ring(count - 1))
        ring(n)


def main() -> int:
    root = tk.Tk()
    LockInEngine(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        sys.exit(130)
