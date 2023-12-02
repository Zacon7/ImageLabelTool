# -*- coding: utf-8 -*-

import json
import os
import tkinter
from tkinter import filedialog, font
from tkinter import messagebox

from PIL import Image, ImageTk


class LabelSelector:
    def __init__(self, master, label_list, on_ok, on_cancel):
        self.master = master
        self.top = tkinter.Toplevel(self.master)
        self.top.title("选择标签")
        self.top.resizable(False, False)
        self.check_list = []
        for label in label_list:
            var = tkinter.IntVar()
            cb = tkinter.Checkbutton(
                self.top, text=label, variable=var, font=font.Font(size=12)
            )
            cb.pack(anchor="w", padx=50, pady=2)
            self.check_list.append((label, var))
        ok_button = tkinter.Button(self.top, text="确定", command=self.on_ok_button)
        ok_button.pack(side="left", padx=30)
        cancel_button = tkinter.Button(
            self.top, text="取消", command=self.on_cancel_button
        )
        cancel_button.pack(side="right", padx=30)
        self.top.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.on_ok = on_ok
        self.on_cancel = on_cancel

        # 根据标签数量调整窗口高度
        num_labels = len(label_list)
        window_height = num_labels * 30 + 100  # 调整高度的计算公式
        self.top.geometry(f"250x{window_height}")

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
        window_x = master_width - 30
        window_y = master_y - 30

        # 设置LabelSelector窗口的位置
        self.top.geometry(f"+{window_x}+{window_y}")

    def on_ok_button(self):
        tags = [label for label, var in self.check_list if var.get()]
        if not tags:
            messagebox.showerror("未选择标签！", "请至少选择一个标签！")
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


class ImageLabelingTool:
    def __init__(self):
        self.image_root = ""
        self.image_list = []
        self.image_idx = -1
        self.label_list = []
        self.checkbutton_dict = {}
        self.rect_stack = []
        self.tags_stack = []
        self.json_dict = {}
        self.is_drawing_rect = False

        self.root = tkinter.Tk()
        self.root.title("图像多标签标注工具")
        self.root.resizable(False, False)  # 固定窗口大小

        self.windowWidth = 1024
        self.windowHeight = 720
        self.screenWidth, self.screenHeight = self.root.maxsize()  # 获得屏幕宽和高
        geometry_param = "%dx%d+%d+%d" % (
            self.windowWidth,
            self.windowHeight,
            (self.screenWidth - self.windowWidth) / 2,
            (self.screenHeight - self.windowHeight) / 2,
        )  # 设置窗口大小及偏移坐标
        self.root.geometry(geometry_param)

        # 创建主菜单
        self.main_menu = tkinter.Menu(self.root)
        self.main_menu.add_command(label="打开文件夹", command=self.open_dir)
        self.main_menu.add_command(label="保存数据", command=self.write_json_dict)
        self.main_menu.add_command(label="退出程序", command=self.close_window)
        self.root.config(menu=self.main_menu)

        # 创建组件
        self.main_window = tkinter.PanedWindow(
            self.root, orient="horizontal", sashwidth=10
        )

        self.canvas_width = self.windowWidth
        self.canvas_height = self.windowHeight
        self.canvas_frame = tkinter.LabelFrame(self.main_window, text="图片显示")
        self.canvas_frame.pack()

        self.img_canvas = tkinter.Canvas(
            self.canvas_frame, width=self.canvas_width, height=self.canvas_height
        )
        self.img_canvas.pack()

        self.rect_count = tkinter.Label(
            self.canvas_frame,
            text="(" + str(len(self.rect_stack)) + " rectangles)",
            font=font.Font(size=10),
        )
        self.rect_count.place(relx=0.43, rely=0.93, anchor="w")

        self.label_index = tkinter.Label(
            self.canvas_frame,
            text="[{}/{}]".format(self.image_idx + 1, len(self.image_list)),
            font=font.Font(size=12),
        )
        self.label_index.place(relx=0.46, rely=0.96, anchor="w")

        self.btn_pre = tkinter.Button(
            self.canvas_frame,
            text="上一张",
            command=lambda: self.prev_image(),
            width=7,
            height=1,
        )
        self.btn_next = tkinter.Button(
            self.canvas_frame,
            text="下一张",
            command=lambda: self.next_image(),
            width=7,
            height=1,
        )

        self.btn_pre.place(relx=0.35, rely=0.96, anchor="w")
        self.btn_next.place(relx=0.55, rely=0.96, anchor="w")

        self.main_window.add(self.canvas_frame)

        # 填满整个界面
        self.main_window.pack(padx=20, pady=5, fill="both", expand=1)

        self.img_start_x = 0
        self.img_start_y = 0
        self.img_end_x = 0
        self.img_end_y = 0
        self.rect = None
        self.tag_text = None
        self.rect_start_x = 0
        self.rect_start_y = 0
        self.rect_end_x = 0
        self.rect_end_y = 0

        self.img_canvas.bind("<ButtonPress-1>", self.on_left_press)
        self.img_canvas.bind("<B1-Motion>", self.on_left_move)
        self.img_canvas.bind("<ButtonRelease-1>", self.on_left_release)
        self.img_canvas.bind("<ButtonPress-3>", self.on_right_press)

    def resize_img(self, w_box, h_box, pil_image):
        # 参数是：要适应的窗口宽、高、Image.open后的图片
        w, h = pil_image.size
        f1 = 1.0 * w_box / w
        f2 = 1.0 * h_box / h
        factor = min([f1, f2])
        width = int(w * factor)
        height = int(h * factor)
        return pil_image.resize((width, height), Image.ANTIALIAS)

    def open_dir(self):
        # 打开文件夹，加载label标签信息和json文件，并对页面进行初始化
        self.image_root = filedialog.askdirectory()
        self.image_list = [
            name
            for name in os.listdir(self.image_root)
            if name.split(".")[-1]
            in ["jpg", "png", "jpeg", "gif", "bmp", "JPG", "PNG", "JPEG", "GIF", "BMP"]
        ]

        if len(self.image_list) > 0:
            self.image_idx = 0
            self.init_label_list()
            self.init_json_dict()
            self.init_canvas()
            self.show_image(
                os.path.join(self.image_root, self.image_list[self.image_idx])
            )
            self.restore_rect(self.image_idx)
            # self.update_checkbuttons(self.image_idx)
            self.label_index.configure(
                text="{}/{}".format(self.image_idx + 1, len(self.image_list))
            )
        else:
            messagebox.showinfo("Load Error", "当前目录下不包含图片！")

    def init_label_list(self):
        # 加载文件夹下的labels.ini，初始化labels_list
        try:
            with open(
                os.path.join(self.image_root, "labels.ini"), "r", encoding="utf-8"
            ) as label_file:
                label_lines = label_file.readlines()
        except (FileNotFoundError, IOError) as e:
            messagebox.showinfo("Load Error", "当前目录下不存在 <labels.ini> 文件!")
            label_lines = []
        self.label_list = [label_name.rstrip("\n") for label_name in label_lines]

    def init_json_dict(self):
        # 加载目标路径下的json文件，填充到json_dict, 如果当前目录下没有result.json，则初始化json_dict并创建json文件
        json_name = os.path.join(self.image_root, "results.json")
        if os.path.exists(json_name):
            with open(json_name, "r", encoding="utf-8") as json_file:
                self.json_dict = json.load(json_file)
        else:
            for image_name in self.image_list:
                rect_list = []
                self.json_dict[image_name] = rect_list

    def write_json_dict(self):
        # 将当前的json_dict保存成json文件
        if len(self.json_dict) == 0:
            messagebox.showinfo("Save Error", "<json_dict> is empty, save failed!")
        else:
            with open(
                os.path.join(self.image_root, "results.json"), "w", encoding="utf-8"
            ) as json_file:
                json.dump(self.json_dict, json_file, ensure_ascii=False, indent=4)
            messagebox.showinfo("Save Success", "保存成功！")

    def init_canvas(self):
        self.img_canvas.bind("<ButtonPress-1>", self.on_left_press)
        self.img_canvas.bind("<B1-Motion>", self.on_left_move)
        self.img_canvas.bind("<ButtonRelease-1>", self.on_left_release)
        self.img_canvas.bind("<ButtonPress-3>", self.on_right_press)
        self.is_drawing_rect = False

    def show_image(self, image_name):
        # 根据路径显示图片
        img_open = Image.open(image_name)
        self.photo = ImageTk.PhotoImage(img_open)
        self.img_start_x = self.canvas_width // 2 - self.photo.width() // 2
        self.img_start_y = self.canvas_height // 2 - self.photo.height() // 2
        self.img_end_x = self.img_start_x + self.photo.width()
        self.img_end_y = self.img_start_y + self.photo.height()
        self.img_canvas.delete("all")
        self.img_canvas.create_image(
            self.canvas_width // 2, self.canvas_height // 2, image=self.photo
        )

    def restore_rect(self, image_idx):
        # 将json_dict中的rect_dict读取出来，在canvas中恢复出对应的rect
        image_name = self.image_list[image_idx]
        self.rect_stack = []
        self.tags_stack = []
        for rect_dict in self.json_dict[image_name]:  # 有多少个矩形框就有多少个rect_dict
            labels = rect_dict["labels"]  # string list: ['xxx', 'yyy', 'zzz']
            rect_coords = rect_dict[
                "points"
            ]  # tuple: ((start_x, start_y), (end_x, end_y)
            (start_x, start_y), (end_x, end_y) = rect_coords
            self.rect_start_x, self.rect_start_y = (
                start_x + self.img_start_x,
                start_y + self.img_start_y,
            )
            self.rect_end_x, self.rect_end_y = (
                end_x + self.img_start_x,
                end_y + self.img_start_y,
            )

            self.rect = self.img_canvas.create_rectangle(
                start_x + self.img_start_x,
                start_y + self.img_start_y,
                end_x + self.img_start_x,
                end_y + self.img_start_y,
                outline="yellow",
                width=2,
            )
            self.tag_text = self.img_canvas.create_text(
                self.rect_start_x,
                self.rect_start_y - 20,
                text=labels,
                anchor="w",
                font=font.Font(size=11),
                fill="yellow",
            )
            self.rect_stack.append(self.rect)
            self.tags_stack.append(self.tag_text)
        self.rect_count.configure(text="(" + str(len(self.rect_stack)) + " rectangles)")
        self.canvas_frame.configure(text="图片显示" + " [ " + image_name + " ]")

    def on_left_press(self, event):
        self.rect_start_x = self.img_canvas.canvasx(event.x)
        self.rect_start_y = self.img_canvas.canvasy(event.y)
        if (
            self.img_start_x <= self.rect_start_x <= self.img_end_x
            and self.img_start_y <= self.rect_start_y <= self.img_end_y
        ):
            self.is_drawing_rect = True
            self.rect = self.img_canvas.create_rectangle(
                self.rect_start_x,
                self.rect_start_y,
                self.rect_start_x,
                self.rect_start_y,
                outline="yellow",
                width=2,
            )

    def on_left_move(self, event):
        self.rect_end_x = self.img_canvas.canvasx(event.x)
        self.rect_end_y = self.img_canvas.canvasy(event.y)
        if self.is_drawing_rect and (
            self.img_start_x <= self.rect_end_x <= self.img_end_x
            and self.img_start_y <= self.rect_end_y <= self.img_end_y
        ):
            self.img_canvas.coords(
                self.rect,
                self.rect_start_x,
                self.rect_start_y,
                self.rect_end_x,
                self.rect_end_y,
            )

    def on_left_release(self, event):
        self.rect_end_x = self.img_canvas.canvasx(event.x)
        self.rect_end_y = self.img_canvas.canvasy(event.y)
        if self.is_drawing_rect and (
            self.img_start_x <= self.rect_end_x <= self.img_end_x
            and self.img_start_y <= self.rect_end_y <= self.img_end_y
        ):
            self.is_drawing_rect = False
            self.show_label_selector()
            # 打印左上顶点和右下顶点坐标
            # print(f"左上顶点坐标：({self.rect_start_x - self.img_start_x}, {self.rect_start_y - self.img_start_y})")
            # print(f"右下顶点坐标：({self.rect_end_x - self.img_start_x}, {self.rect_end_y - self.img_start_y})")

    def on_right_press(self, event):
        image_name = self.image_list[self.image_idx]
        if len(self.rect_stack) != 0:
            self.img_canvas.delete(self.rect_stack.pop())
            self.img_canvas.delete(self.tags_stack.pop())
            self.json_dict[image_name].pop()
            self.rect_count.configure(
                text="(" + str(len(self.rect_stack)) + " rectangles)"
            )

    def show_label_selector(self):
        self.label_selector = LabelSelector(
            self.root, self.label_list, self.on_button_ok, self.on_button_cancel
        )

    def on_button_ok(self, tags):
        # 标注完成，将矩形框和标签存储到json_dict中
        image_name = self.image_list[self.image_idx]
        labels = ", ".join(tags)
        # 显示标签文本对象
        self.tag_text = self.img_canvas.create_text(
            self.rect_start_x,
            self.rect_start_y - 20,
            text=labels,
            anchor="w",
            font=font.Font(size=11),
            fill="yellow",
        )
        self.json_dict[image_name].append(
            {
                "labels": labels,
                "points": (
                    (
                        self.rect_start_x - self.img_start_x,
                        self.rect_start_y - self.img_start_y,
                    ),
                    (
                        self.rect_end_x - self.img_start_x,
                        self.rect_end_y - self.img_start_y,
                    ),
                ),
            }
        )
        self.rect_stack.append(self.rect)
        self.tags_stack.append(self.tag_text)
        self.rect_count.configure(text="(" + str(len(self.rect_stack)) + " rectangles)")

    def on_button_cancel(self):
        self.img_canvas.delete(self.rect)
        self.rect = None
        self.tag_text = None
        self.rect_start_x = 0
        self.rect_start_y = 0
        self.rect_end_x = 0
        self.rect_end_y = 0

    def prev_image(self):
        self.image_idx = self.image_idx - 1
        self.image_idx = max(0, self.image_idx)
        if len(self.image_list) > 0 and 0 <= self.image_idx < len(self.image_list):
            self.show_image(
                os.path.join(self.image_root, self.image_list[self.image_idx])
            )
            self.restore_rect(self.image_idx)
            self.label_index.configure(
                text="{}/{}".format(self.image_idx + 1, len(self.image_list))
            )

    def next_image(self):
        self.image_idx = self.image_idx + 1
        self.image_idx = min(len(self.image_list) - 1, self.image_idx)
        if len(self.image_list) > 0 and 0 <= self.image_idx < len(self.image_list):
            self.show_image(
                os.path.join(self.image_root, self.image_list[self.image_idx])
            )
            self.restore_rect(self.image_idx)
            self.label_index.configure(
                text="{}/{}".format(self.image_idx + 1, len(self.image_list))
            )

    def close_window(self):
        self.root.destroy()
        self.root.quit()

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = ImageLabelingTool()
    app.run()
