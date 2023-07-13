# -*- coding: utf-8 -*-

import tkinter
from tkinter import filedialog, IntVar, font
from tkinter import messagebox
from PIL import Image, ImageTk
import os
import json


class ImageLabelingTool:
    def __init__(self):
        self.image_root = ""
        self.image_list = []
        self.image_idx = -1
        self.label_list = []
        self.checkbutton_dict = {}
        self.rect_list = []
        self.json_dict = {}

        self.root = tkinter.Tk()
        self.root.title('图像多标签标注工具2')
        self.root.resizable(False, False)# 固定窗口大小

        self.windowWidth = 1280
        self.windowHeight = 680
        self.screenWidth, self.screenHeight = self.root.maxsize() # 获得屏幕宽和高
        geometryParam = '%dx%d+%d+%d' % (
            self.windowWidth, self.windowHeight, (self.screenWidth - self.windowWidth) / 2, 
            (self.screenHeight - self.windowHeight) / 2)  # 设置窗口大小及偏移坐标
        self.root.geometry(geometryParam)

        # 创建主菜单
        self.main_menu = tkinter.Menu(self.root)
        self.main_menu.add_command(label="打开文件夹", command=self.open_dir)
        self.main_menu.add_command(label="保存数据", command=self.write_json)
        self.main_menu.add_command(label="退出程序", command=self.close_window)
        self.root.config(menu=self.main_menu)

        # 创建组件
        self.main_window = tkinter.PanedWindow(self.root, orient='horizontal', sashwidth=10)

        self.canvas_width = 800
        self.canvas_height = 600
        self.canvas_frame = tkinter.LabelFrame(self.main_window, text='图片显示')
        self.canvas_frame.pack()

        self.img_canvas = tkinter.Canvas(self.canvas_frame, width=self.canvas_width, height=self.canvas_height)
        self.img_canvas.pack()

        self.label_frame = tkinter.LabelFrame(self.main_window, text='标签选择（支持多选）')
        self.label_frame.pack()

        self.rect_count = tkinter.Label(self.canvas_frame, text= '(' + str(len(self.rect_list)) + ' rectangles)', font=font.Font(size = 10))
        self.rect_count.place(relx=0.43, rely=0.93, anchor='w')

        self.label_index = tkinter.Label(self.canvas_frame, text='[{}/{}]'.format(self.image_idx+1, len(self.image_list)), font=font.Font(size = 12))
        self.label_index.place(relx=0.46, rely=0.96, anchor='w')

        self.btn_pre = tkinter.Button(self.canvas_frame, text='上一张', command=lambda: self.prev_image(), width=7, height=1)
        self.btn_next = tkinter.Button(self.canvas_frame, text='下一张', command=lambda: self.next_image(), width=7, height=1)


        self.btn_pre.place(relx=0.35, rely=0.96, anchor='w')
        self.btn_next.place(relx=0.55, rely=0.96, anchor='w')

        self.main_window.add(self.canvas_frame)
        self.main_window.add(self.label_frame)

        # 填满整个界面
        self.main_window.pack(padx=20, pady=5, fill='both', expand='yes')

        self.img_start_x = 0
        self.img_start_y = 0
        self.img_end_x = 0
        self.img_end_y = 0
        self.rect = None
        self.start_x = 0
        self.start_y = 0
        self.end_x = 0
        self.end_y = 0

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
            name for name in os.listdir(self.image_root)
            if name.split(".")[-1] in ["jpg", "png", "jpeg", "gif", "bmp", "JPG", "PNG", "JPEG", "GIF", "BMP"]
        ]

        if len(self.image_list) > 0:
            self.image_idx = 0
            self.load_label()
            self.load_json()
            self.init_checkbuttons()
            self.init_canvas()
            self.show_image(os.path.join(self.image_root, self.image_list[self.image_idx]))
            self.update_rect(self.image_idx)
            self.update_checkbuttons(self.image_idx)
            self.label_index.configure(text='{}/{}'.format(self.image_idx + 1, len(self.image_list)))
        else:
            messagebox.showinfo("Load Error", "当前目录下不包含图片！")


    def load_label(self):
        # 加载文件夹下的labels.ini，初始化labels_list
        try:
            with open(os.path.join(self.image_root, "labels.ini"), "r", encoding="utf-8") as label_file:
                label_lines = label_file.readlines()
        except (FileNotFoundError, IOError) as e:
            messagebox.showinfo("Load Error", "当前目录下不存在 <labels.ini> 文件!")
            label_lines = []
        self.label_list = [label_name.rstrip("\n") for label_name in label_lines]

    def load_json(self):
        # 加载目标路径下的json文件，填充到json_dict, 如果当前目录下没有result.json，则初始化json_dict并创建json文件
        json_name = os.path.join(self.image_root, "results.json")
        if os.path.exists(json_name):
            with open(json_name, "r", encoding="utf-8") as json_file:
                self.json_dict = json.load(json_file)
        else:
            for image_name in self.image_list:
                label_dict = {label_name: 0 for label_name in self.label_list}
                rect_list = []
                self.json_dict[image_name] = [label_dict, rect_list]

    def write_json(self):
        # 将当前的json_dict保存成json文件
        if len(self.json_dict) == 0:
            messagebox.showinfo("Save Error", "<json_dict> is empty, save failed!")
        else:
            with open(os.path.join(self.image_root, "results.json"), "w", encoding="utf-8") as json_file:
                json.dump(self.json_dict, json_file, ensure_ascii=False, indent=4)
            messagebox.showinfo("Save Success", "保存成功！")

    def init_checkbuttons(self):
        # 根据从文件中读取的label_list创建复选框并初始化到checkbuton_dict中
        for label_name in self.checkbutton_dict.keys():
            self.checkbutton_dict[label_name].destroy()

        for label_name in self.label_list:
            is_check = tkinter.IntVar(value=0)
            cb = tkinter.Checkbutton(
                self.label_frame,
                text=label_name,
                font=tkinter.font.Font(size=14),
                variable=is_check,
                onvalue=1,
                offvalue=0,
                command=lambda name=label_name, var=is_check: self.update_dict_cb(name, var.get())
            )
            cb.pack(anchor="w")
            self.checkbutton_dict[label_name] = cb

    def update_dict_cb(self, label_name, is_check):
        # 当复选框状态改变时，同步更新json_dict对应的label_dict
        image_name = self.image_list[self.image_idx]
        self.json_dict[image_name][0][label_name] = is_check

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

        self.img_start_x = self.canvas_width//2 - self.photo.width()//2
        self.img_start_y = self.canvas_height//2 - self.photo.height()//2
        self.img_end_x = self.img_start_x + self.photo.width()
        self.img_end_y = self.img_start_y + self.photo.height()

        self.img_canvas.delete("all")
        self.img_canvas.create_image(self.canvas_width//2, self.canvas_height//2, image=self.photo, anchor=tkinter.CENTER)

    def update_rect(self, image_idx):
        # 根据从文件中读取的json_dict[image_name]['rect_list']，在canvas中画出对应的rect
        image_name = self.image_list[image_idx]
        self.rect_list = []
        for rect_coords in self.json_dict[image_name][1]:
            (start_x, start_y), (end_x, end_y) = rect_coords
            rect = self.img_canvas.create_rectangle(
                start_x + self.img_start_x,
                start_y + self.img_start_y,
                end_x + self.img_start_x,
                end_y + self.img_start_y,
                outline='yellow', width=2
            )
            self.rect_list.append(rect)
        self.rect_count.configure(text='(' + str(len(self.rect_list)) + ' rectangles)')

    def on_left_press(self, event):
        self.start_x = self.img_canvas.canvasx(event.x)
        self.start_y = self.img_canvas.canvasy(event.y)
        if (self.start_x >= self.img_start_x and self.start_x <= self.img_end_x and
                  self.start_y >= self.img_start_y and self.start_y <= self.img_end_y):
            self.is_drawing_rect = True 
            self.rect = self.img_canvas.create_rectangle(self.start_x, self.start_y, self.start_x, self.start_y,
                                                         outline='yellow', width=2)

    def on_left_move(self, event):
        self.end_x = self.img_canvas.canvasx(event.x)
        self.end_y = self.img_canvas.canvasy(event.y)
        if self.is_drawing_rect and \
            (self.end_x >= self.img_start_x and self.end_x <= self.img_end_x and
                self.end_y >= self.img_start_y and self.end_y <= self.img_end_y):
            self.img_canvas.coords(self.rect, self.start_x, self.start_y, self.end_x, self.end_y)

    def on_left_release(self, event):
        self.end_x = self.img_canvas.canvasx(event.x)
        self.end_y = self.img_canvas.canvasy(event.y)
        if self.is_drawing_rect and \
            (self.end_x >= self.img_start_x and self.end_x <= self.img_end_x and
                self.end_y >= self.img_start_y and self.end_y <= self.img_end_y):
            self.is_drawing_rect = False
            # 打印左上顶点和右下顶点坐标
            # print(f"左上顶点坐标：({start_x - img_start_x}, {start_y - img_start_y})")
            # print(f"右下顶点坐标：({end_x - img_start_x}, {end_y - img_start_y})")
            self.rect_list.append(self.rect)
            image_name = self.image_list[self.image_idx]
            self.json_dict[image_name][1].append(((self.start_x - self.img_start_x, self.start_y - self.img_start_y), 
                                                (self.end_x - self.img_start_x, self.end_y - self.img_start_y)))
            self.rect_count.configure(text= '(' + str(len(self.rect_list)) + ' rectangles)')

    def on_right_press(self, event):
        image_name = self.image_list[self.image_idx]
        if len(self.rect_list) != 0:
            self.img_canvas.delete(self.rect_list.pop())
            self.json_dict[image_name][1].pop()
            self.rect_count.configure(text= '(' + str(len(self.rect_list)) + ' rectangles)')

    def update_checkbuttons(self, image_idx):
        # 根据json_dict更新当前页面中checkbutton的选中状态
        image_name = self.image_list[image_idx]
        for label_name in self.label_list:
            cb = self.checkbutton_dict[label_name]
            label_dict = self.json_dict[image_name][0]
            if label_name in label_dict and label_dict[label_name] == 1:
                cb.select()
            else:
                cb.deselect()


    def prev_image(self):
        self.image_idx = self.image_idx - 1
        self.image_idx = max(0, self.image_idx)
        if len(self.image_list) > 0 and 0 <= self.image_idx < len(self.image_list):
            self.show_image(os.path.join(self.image_root, self.image_list[self.image_idx]))
            self.update_rect(self.image_idx)
            self.update_checkbuttons(self.image_idx)
            self.label_index.configure(text='{}/{}'.format(self.image_idx + 1, len(self.image_list)))

    def next_image(self):
        self.image_idx = self.image_idx + 1
        self.image_idx = min(len(self.image_list) - 1, self.image_idx)
        if len(self.image_list) > 0 and 0 <= self.image_idx < len(self.image_list):
            self.show_image(os.path.join(self.image_root, self.image_list[self.image_idx]))
            self.update_rect(self.image_idx)
            self.update_checkbuttons(self.image_idx)
            self.label_index.configure(text='{}/{}'.format(self.image_idx + 1, len(self.image_list)))

    def close_window(self):
        self.root.destroy()
        self.root.quit()

    def run(self):
        self.root.mainloop()


if __name__ == '__main__':
    app = ImageLabelingTool()
    app.run()