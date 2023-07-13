import tkinter as tk
from tkinter import messagebox

class LabelSelector:
    def __init__(self, master, labels, on_ok, on_cancel):
        self.master = master
        self.top = tk.Toplevel(self.master)
        self.top.title("选择标签")
        self.check_list = []
        for label in labels:
            var = tk.IntVar(0)
            cb = tk.Checkbutton(self.top, text=label, variable=var)
            cb.pack()
            self.check_list.append((label, var))
        ok_button = tk.Button(self.top, text="确定", command=self.on_ok_button)
        ok_button.pack(side="left", padx=30)
        cancel_button = tk.Button(self.top, text="取消", command=self.on_cancel_button)
        cancel_button.pack(side="right", padx=30)
        self.top.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.on_ok = on_ok
        self.on_cancel = on_cancel

        # 根据标签数量调整窗口高度
        num_labels = len(labels)
        window_height = num_labels * 30 + 100  # 调整高度的计算公式
        self.top.geometry(f"200x{window_height}")

        # 将窗口位置设置在主窗口中间
        self.center_window()

    def center_window(self):
        # 获取主窗口的位置和大小
        master_width = self.master.winfo_width()
        master_height = self.master.winfo_height()
        master_x = self.master.winfo_rootx()
        master_y = self.master.winfo_rooty()

        # 计算LabelSelector窗口的位置
        window_width = self.top.winfo_width()
        window_height = self.top.winfo_height()
        window_x = master_x + (master_width - window_width) // 4
        window_y = master_y + (master_height - window_height) // 4

        # 设置LabelSelector窗口的位置
        self.top.geometry(f"+{window_x}+{window_y}")

    def on_ok_button(self):
        tags = [label for label, var in self.check_list if var.get()]
        if not tags:
            messagebox.showerror("未选择标签！", "请至少勾选一个标签！")
            self.on_cancel_button()
            return
        self.top.destroy()
        if self.on_ok:
            self.on_ok(tags)

    def on_cancel_button(self):
        self.top.destroy()
        if self.on_cancel:
            self.on_cancel()
    
    def on_closing(self):
        self.on_cancel_button()

class RectSelector:
    def __init__(self, master):
        self.master = master
        self.canvas = tk.Canvas(master, width=700, height=500)
        self.canvas.pack()
        self.canvas.bind("<ButtonPress-1>", self.on_button_press)
        self.canvas.bind("<B1-Motion>", self.on_move_press)
        self.canvas.bind("<ButtonRelease-1>", self.on_button_release)
        self.rect = None
        self.start_x = None
        self.start_y = None
        self.end_x = None
        self.end_y = None
        self.rect_tags = []
        self.label_selector = None

    def on_button_press(self, event):
        self.start_x = self.canvas.canvasx(event.x)
        self.start_y = self.canvas.canvasy(event.y)
        self.rect = self.canvas.create_rectangle(self.start_x, self.start_y, self.start_x, self.start_y, outline="red")

    def on_move_press(self, event):
        self.end_x = self.canvas.canvasx(event.x)
        self.end_y = self.canvas.canvasy(event.y)
        self.canvas.coords(self.rect, self.start_x, self.start_y, self.end_x, self.end_y)
    
    def on_button_release(self, event):
        self.show_label_selector()

    def show_label_selector(self):
        labels = ["标签1", "标签2", "标签3", "标签4", "标签1", "标签2", "标签3", "标签4"]
        self.label_selector = LabelSelector(self.master, labels, self.on_label_ok, self.on_label_cancel)

    def on_label_ok(self, tags):
        self.canvas.itemconfig(self.rect, tags=tags)
        self.rect_tags = tags

        # 显示标签文本对象
        text_x = self.start_x
        text_y = self.start_y - 20
        text = ", ".join(tags)
        self.canvas.create_text(text_x, text_y, text=text, anchor="w")

    def on_label_cancel(self):
        self.canvas.delete(self.rect)
        self.rect = None
        self.start_x = None
        self.start_y = None
        self.end_x = None
        self.end_y = None
        self.rect_tags = []
        #self.label_selector = None

root = tk.Tk()
app = RectSelector(root)
root.mainloop()