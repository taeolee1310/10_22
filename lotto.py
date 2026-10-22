import random
import tkinter as tk
from datetime import datetime

SET_COUNT = 5
NUMBERS_PER_SET = 6
MAX_NUMBER = 45
WEEKDAYS = ["월", "화", "수", "목", "금", "토", "일"]


def ball_color(n):
    """번호 구간별 색상 (동행복권 공 색상 기준) -> (배경색, 글자색)"""
    if n <= 10:
        return "#FBC400", "black"
    if n <= 20:
        return "#69C8F2", "black"
    if n <= 30:
        return "#FF7272", "black"
    if n <= 40:
        return "#AAAAAA", "black"
    return "#B0D840", "black"


def draw_ball(canvas, x, y, number):
    bg, fg = ball_color(number)
    r = 22
    canvas.create_oval(x - r, y - r, x + r, y + r, fill=bg, outline="")
    canvas.create_text(x, y, text=str(number), fill=fg, font=("맑은 고딕", 13, "bold"))


def generate():
    now = datetime.now()
    date_label.config(
        text=now.strftime(f"%Y년 %m월 %d일 ({WEEKDAYS[now.weekday()]}) %H:%M:%S")
    )

    canvas.delete("all")
    for i in range(SET_COUNT):
        numbers = sorted(random.sample(range(1, MAX_NUMBER + 1), NUMBERS_PER_SET))
        y = 35 + i * 55
        canvas.create_text(30, y, text=chr(ord("A") + i), font=("맑은 고딕", 14, "bold"))
        for j, n in enumerate(numbers):
            draw_ball(canvas, 90 + j * 55, y, n)


root = tk.Tk()
root.title("로또 번호 생성기")
root.resizable(False, False)

tk.Label(root, text="로또 번호 생성기", font=("맑은 고딕", 18, "bold")).pack(pady=(15, 5))
date_label = tk.Label(root, text="버튼을 눌러 번호를 뽑아보세요", font=("맑은 고딕", 11))
date_label.pack()

canvas = tk.Canvas(root, width=440, height=SET_COUNT * 55 + 10, highlightthickness=0)
canvas.pack(padx=20, pady=10)

tk.Button(
    root, text="번호 생성", font=("맑은 고딕", 13, "bold"), width=14, command=generate
).pack(pady=(0, 15))

legend = tk.Frame(root)
legend.pack(pady=(0, 15))
for text, color in [("1~10", "#FBC400"), ("11~20", "#69C8F2"), ("21~30", "#FF7272"),
                    ("31~40", "#AAAAAA"), ("41~45", "#B0D840")]:
    tk.Label(legend, text=text, bg=color, width=7, font=("맑은 고딕", 9)).pack(side="left", padx=2)

root.mainloop()
