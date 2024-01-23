# -*- coding: utf-8 -*-

import tkinter
from tkinter import filedialog, IntVar, font
from tkinter import messagebox
from PIL import Image, ImageTk
import os
import json


def resize_img(w_box, h_box, pil_image):  # 参数是：要适应的窗口宽、高、Image.open后的图片
    w, h = pil_image.size
    f1 = 1.0 * w_box / w
    f2 = 1.0 * h_box / h
    factor = min([f1, f2])
    width = int(w * factor)
    height = int(h * factor)
    return pil_image.resize((width, height), Image.ANTIALIAS)


def on_left_press(event):
    global rect, start_x, start_y, img_start_x, img_start_y, img_end_x, img_end_y
    # 保存起始点坐标
    start_x = img_canvas.canvasx(event.x)
    start_y = img_canvas.canvasy(event.y)
    # 创建矩形框
    if (start_x >= img_start_x and start_x <= img_end_x and
            start_y >= img_start_y and start_y <= img_end_y):
        rect = img_canvas.create_rectangle(start_x, start_y, start_x, start_y, outline='yellow', width=2)


def on_left_move(event):
    global rect, start_x, start_y, end_x, end_y
    # 更新矩形框坐标
    end_x = img_canvas.canvasx(event.x)
    end_y = img_canvas.canvasy(event.y)
    if (end_x >= img_start_x and end_x <= img_end_x and
            end_y >= img_start_y and end_y <= img_end_y):
        img_canvas.coords(rect, start_x, start_y, end_x, end_y)


def on_left_release(event):
    global rect, start_x, start_y, end_x, end_y, image_idx, image_list, rect_list, json_dict, img_start_x, img_start_y
    # 保存结束点坐标
    end_x = img_canvas.canvasx(event.x)
    end_y = img_canvas.canvasy(event.y)
    if (end_x >= img_start_x and end_x <= img_end_x and
            end_y >= img_start_y and end_y <= img_end_y):
        # 打印左上顶点和右下顶点坐标
        # print(f"左上顶点坐标：({start_x - img_start_x}, {start_y - img_start_y})")
        # print(f"右下顶点坐标：({end_x - img_start_x}, {end_y - img_start_y})")
        rect_list.append(rect)
        image_name = image_list[image_idx]
        json_dict[image_name][1].append(
            ((start_x - img_start_x, start_y - img_start_y),
             (end_x - img_start_x, end_y - img_start_y)))
        rect_count.configure(text='(' + str(len(rect_list)) + ' rectangles)')


def on_right_press(event):
    global rect_list
    global image_idx, image_list, json_dict
    # 右键撤回矩形框
    image_name = image_list[image_idx]
    if len(rect_list) != 0:
        img_canvas.delete(rect_list.pop())
        json_dict[image_name][1].pop()
        rect_count.configure(text='(' + str(len(rect_list)) + ' rectangles)')


def show_image(image_name):
    # 根据路径显示图片
    img_open = Image.open(image_name)
    global canvas_width, canvas_heigt, img_canvas, photo, img_start_x, img_start_y, img_end_x, img_end_y
    # img_open = resize_img(canvas_width, canvas_heigt, img_open)
    photo = ImageTk.PhotoImage(img_open)
    img_start_x = canvas_width // 2 - photo.width() // 2
    img_start_y = canvas_heigt // 2 - photo.height() // 2
    img_end_x = img_start_x + photo.width()
    img_end_y = img_start_y + photo.height()
    img_canvas.delete("all")
    img_canvas.create_image(canvas_width // 2, canvas_heigt // 2, image=photo, anchor=tkinter.CENTER)


def load_label():
    # 加载文件夹下的labels.ini，初始化labels_list
    global image_root, label_list
    try:
        with open(os.path.join(image_root, "labels.ini"), "r", encoding="utf-8") as label_file:
            label_lines = label_file.readlines()
    except (FileNotFoundError, IOError) as e:
        messagebox.showinfo("Load Error", "当前目录下不存在 <labels.ini> 文件!")
        label_lines = []
    label_list = [label_name.rstrip("\n") for label_name in label_lines]


def load_json():
    # 加载目标路径下的json文件，填充到json_dict, 如果当前目录下没有result.json，则初始化json_dict并创建json文件
    global image_root, label_list, json_dict
    json_name = os.path.join(image_root, "results.json")
    if os.path.exists(json_name):
        with open(json_name, "r", encoding="utf-8") as json_file:
            json_dict = json.load(json_file)
    else:
        for image_name in image_list:
            label_dict = {label_name: 0 for label_name in label_list}
            rect_list = []
            json_dict[image_name] = [label_dict, rect_list]


def write_json():
    # 将当前的json_dict保存成json文件
    global image_root, json_dict
    if (len(json_dict) == 0):
        messagebox.showinfo("Save Error", "<json_dict> is empty, save failed!")
    else:
        with open(os.path.join(image_root, "results.json"), "w", encoding="utf-8") as json_file:
            json.dump(json_dict, json_file, ensure_ascii=False, indent=4)
        messagebox.showinfo("Save Success", "保存成功！")


def update_dict_cb(label_name, is_check):
    # 当复选框状态改变时，同步更新json_dict对应的label_dict
    global image_idx, image_list, label_list, json_dict
    image_name = image_list[image_idx]
    json_dict[image_name][0][label_name] = is_check


def update_rect(image_idx):
    # 根据从文件中读取的json_dict[image_name]['rect_list']，在canvas中画出对应的rect
    global image_list, rect_list, json_dict, img_start_x, img_start_y
    image_name = image_list[image_idx]
    rect_list = []
    for rect_coords in json_dict[image_name][1]:
        (start_x, start_y), (end_x, end_y) = rect_coords
        rect = img_canvas.create_rectangle(
            start_x + img_start_x,
            start_y + img_start_y,
            end_x + img_start_x,
            end_y + img_start_y,
            outline='yellow',
            width=2)
        rect_list.append(rect)
    rect_count.configure(text='(' + str(len(rect_list)) + ' rectangles)')


def init_canvas():
    img_canvas.bind("<ButtonPress-1>", on_left_press)
    img_canvas.bind("<B1-Motion>", on_left_move)
    img_canvas.bind("<ButtonRelease-1>", on_left_release)
    img_canvas.bind("<ButtonPress-3>", on_right_press)


def init_checkbuttons():
    # 根据从文件中读取的label_list创建复选框并初始化到checkbuton_dict中
    global label_list, label_frame, checkbutton_dict
    for label_name in checkbutton_dict.keys():
        checkbutton_dict[label_name].destroy()

    for label_name in label_list:
        is_check = IntVar(value=0)
        cb = tkinter.Checkbutton(label_frame, text=label_name, font=font.Font(size=14),
                                 variable=is_check, onvalue=1, offvalue=0,
                                 command=lambda name=label_name, var=is_check: update_dict_cb(name, var.get()))
        cb.pack(anchor="w")
        checkbutton_dict[label_name] = cb


def update_checkbuttons(image_idx):
    # 根据json_dict更新当前页面中checkbutton的选中状态
    global image_list, label_list, json_dict, checkbutton_dict
    image_name = image_list[image_idx]
    for label_name in label_list:
        cb = checkbutton_dict[label_name]
        label_dict = json_dict[image_name][0]
        if label_name in label_dict and label_dict[label_name] == 1:
            cb.select()
        else:
            cb.deselect()


def open_dir():
    # 打开文件夹，加载label标签信息和json文件，并对页面进行初始化
    img_dir = filedialog.askdirectory()
    global image_root, image_list, image_idx
    image_root = img_dir
    image_list = [name for name in os.listdir(image_root) if name.split(
        ".")[-1] in ["jpg", "png", "jpeg", "gif", "bmp", "JPG", "PNG", "JPEG", "GIF", "BMP"]]

    # 加载标签和json等信息，显示图片并创建复选框
    if (len(image_list) > 0):
        image_idx = 0
        load_label()
        load_json()
        init_checkbuttons()
        init_canvas()
        show_image(os.path.join(image_root, image_list[image_idx]))
        update_rect(image_idx)
        update_checkbuttons(image_idx)
        label_index.configure(text='{}/{}'.format(image_idx + 1, len(image_list)))
    else:
        messagebox.showinfo("Load Error", "当前目录下不包含图片！")


def pre_image():
    # 显示上一张图片
    global image_idx, image_list, image_root
    image_idx = image_idx - 1
    image_idx = max(0, image_idx)
    if (len(image_list) > 0 and image_idx >= 0 and image_idx < len(image_list)):
        show_image(os.path.join(image_root, image_list[image_idx]))
        update_rect(image_idx)
        update_checkbuttons(image_idx)
        label_index.configure(text='{}/{}'.format(image_idx + 1, len(image_list)))


def next_image():
    # 显示下一张图片
    global image_idx, image_list, image_root
    image_idx = image_idx + 1
    image_idx = min(len(image_list) - 1, image_idx)
    if (len(image_list) > 0 and image_idx >= 0 and image_idx < len(image_list)):
        show_image(os.path.join(image_root, image_list[image_idx]))
        update_rect(image_idx)
        update_checkbuttons(image_idx)
        label_index.configure(text='{}/{}'.format(image_idx + 1, len(image_list)))


def close_window():
    global root
    root.destroy()
    root.quit()


def show_help():
    messagebox.showinfo("Help", "1. 请务必将所有待标注图片保存到同一个文件夹下\n\n\
2. 请务必在该文件夹下创建一个名为\"labels.ini\"的文件，用于保存分类信息，其中每个分类标签单独占一行\n\n\
3. 进入程序，点击“打开文件夹”，选择至少包含有1张图片和labels.ini文件的文件夹目录\n\n\
4. 成功加载后，程序会分为两个区域：左边为图片区，右边为标注区\n\n\
5. 用户可在图片区查看图片，并通过鼠标在图片区域内拉取矩形框，支持多矩形框拉取，单击右键可撤回矩形框\n\n\
6. 用户可在标注区为该图片进行标签勾选，支持多标签勾选\n\n\
7. 在图片区域下方，会显示当前图片矩形框的数量\n\n\
8. 对当前图片标注完成后，可点击“上一张”或“下一张”进行图片切换\n\n\
9. 当用户完成标注后，点击程序菜单栏中的“保存数据”即可将标注信息保存\n\n\
10. 直接关闭程序或点击菜单栏中的“退出程序”则不会保存任何标注数据\n\n\
11. 标注信息会被保存为该文件夹下名为\"result.json\"的文件中，包含每张图片的标签信息、以及矩形框角点坐标\n\n\
12. 程序支持数据加载，即当程序打开文件夹时，若当前目录下存在有\"result.json\"文件，则自动读取其中的信息并显示在程序中\n\n")


if __name__ == '__main__':
    image_root = ""
    image_list = []
    image_idx = -1
    label_list = []
    checkbutton_dict = {}
    rect_list = []
    json_dict = {}

    root = tkinter.Tk()
    root.title('图像多标签标注工具')  # 窗口标题
    root.resizable(False, False)  # 固定窗口大小

    windowWidth = 1280
    windowHeight = 680
    screenWidth, screenHeight = root.maxsize()  # 获得屏幕宽和高
    geometryParam = '%dx%d+%d+%d' % (
        windowWidth, windowHeight, (screenWidth - windowWidth) / 2, (screenHeight - windowHeight) / 2)
    root.geometry(geometryParam)  # 设置窗口大小及偏移坐标

    # 创建主菜单
    main_menu = tkinter.Menu(root)
    main_menu.add_command(label="打开文件夹", command=open_dir)
    main_menu.add_command(label="保存数据", command=write_json)
    main_menu.add_command(label="退出程序", command=close_window)
    main_menu.add_command(label="程序说明", command=show_help)
    root.config(menu=main_menu)

    # 创建组件
    main_window = tkinter.PanedWindow(root, orient='horizontal', sashwidth=10)

    canvas_width = 800
    canvas_heigt = 600
    canvas_frame = tkinter.LabelFrame(main_window, text='图片显示')
    canvas_frame.pack()

    img_canvas = tkinter.Canvas(canvas_frame, width=canvas_width, height=canvas_heigt)
    img_canvas.pack()

    label_frame = tkinter.LabelFrame(main_window, text='标签选择（支持多选）')
    label_frame.pack()

    rect_count = tkinter.Label(canvas_frame, text='(' + str(len(rect_list)) + ' rectangles)', font=font.Font(size=10))
    rect_count.place(relx=0.43, rely=0.93, anchor='w')

    label_index = tkinter.Label(
        canvas_frame, text='[{}/{}]'.format(image_idx + 1, len(image_list)),
        font=font.Font(size=12))
    label_index.place(relx=0.46, rely=0.96, anchor='w')

    btn_pre = tkinter.Button(canvas_frame, text='上一张', command=lambda: pre_image(), width=7, height=1)
    btn_next = tkinter.Button(canvas_frame, text='下一张', command=lambda: next_image(), width=7, height=1)

    btn_pre.place(relx=0.35, rely=0.96, anchor='w')
    btn_next.place(relx=0.55, rely=0.96, anchor='w')

    main_window.add(canvas_frame)
    main_window.add(label_frame)

    # 填满整个界面
    main_window.pack(padx=20, pady=5, fill='both', expand='yes')

    root.mainloop()
