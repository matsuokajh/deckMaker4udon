import sys
import numpy as np
from PIL import Image, ImageTk
from natsort import natsorted
# from matplotlib import pyplot as plt
import math
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import filedialog
from tkinter import messagebox
from tkinter import scrolledtext
import os
import pathlib 
import time
import hashlib
import shutil

# 自作モジュール
import deck_modules as dmod
import my_class_file as mcf
GEO_MAIN_H = 700
GEO_MAIN_W = 1000
GEO_MAIN_X = 50
GEO_MAIN_Y = 50
THUMBNAIL_H = 115
THUMBNAIL_W = 100


INIT_SHEET_DIR = "sheet"
INIT_OUTPUT_NAME = "out"
TMP_WORK_DIR = "tmp_work"
INIT_FTYPE = "jpg"
DT_OMOTE = "表面"
DT_URA = "裏面"
DT_MAISUU = "枚数"

#カードリストの項目幅
C0WIDTH=3  #card ID
C1WIDTH=3 #チェックボックス
C2WIDTH=8  #face
C3WIDTH=8  #back
C4WIDTH=5  #num

########拾い物##################
GEO_SATE = '+50+50'
def get_size(tup, maxsize = 100):
    """ It returns the size of images on the summary"""
    x, y = tup
    if (x<=maxsize and y<=maxsize):
        return (x, y)
    elif x > y:
        r = float(maxsize) / float(x)
        return (maxsize, int(y*r))
    else:
        r = float(maxsize) / float(y)
        return (int(x*r), maxsize)

class ImageLabel:
    """ A Label class to show an image """

    id_original_size = None    # ID of the Label showing an original size image
    image_file_now = None
    
    def __init__(self, stxt, image_file, img):
        self.image= img
        self.image_file = image_file
        frame = tk.Frame(stxt, height=THUMBNAIL_H, width=THUMBNAIL_W)
        frame.pack_propagate(0)
        txt_label=tk.Label(frame, text=os.path.basename(self.image_file), font=('Helvetica', '8'))
        txt_label.pack(side=tk.BOTTOM)
        
        self.img_label=tk.Label(frame, image=self.image)
        self.img_label.pack(side=tk.BOTTOM)

        stxt.window_create(tk.END, align=tk.BASELINE, padx=5, pady=5, window=frame)
        self.img_label.bind('<Double-Button-1>', self.show)

    def show(self, event):
        label = ImageLabel.id_original_size
        if (label and label.winfo_exists()):
            top = label.winfo_toplevel()
            top.destroy()
        top = tk.Toplevel(self.img_label)
        top.title(os.path.basename(self.image_file))
        top.geometry(GEO_SATE)
        img = Image.open(self.image_file)
        self.timg = ImageTk.PhotoImage(img.resize(get_size(img.size,maxsize = 600), Image.NEAREST))
        label=tk.Label(top, image=self.timg)
        label.pack()
        ImageLabel.id_original_size = label
        ImageLabel.image_file_now = self.image_file
#######################

# アプリケーション（GUI）クラス
class Application(tk.Frame):
    DEBUG_LOG = True
    def __init__(self, master=None):
        super().__init__(master)
        self.master.geometry(f"{GEO_MAIN_W}x{GEO_MAIN_H}+{GEO_MAIN_X}+{GEO_MAIN_Y}") # ウィンドウの幅と高さピクセル単位で指定（width x height）
        # self.pack()
        # self.file = []
        self.disp_img_once = False
        self.list_once = False
        self.cardlist_once = False
        self.preview_once = False
        self.sheet_list = []    
        self.img_dict ={}       # CardImgオブジェクトのdict       
        self.card_list =[]      # Cardオブジェクトのlist
        self.dcard_list = []    # dCardオブジェクトのlist
        self.outcard_list =[]      # Cardオブジェクトのlist
        self.sheet_dir = pathlib.Path().resolve() / INIT_SHEET_DIR
        self.tmp_fils_path = pathlib.Path().resolve() / TMP_WORK_DIR
        self.output_dir =  pathlib.Path().resolve()
        self.ftype = INIT_FTYPE
        self.cut_out_cards = dmod.CutOutCards(rownum=1, columnum=1, dir_out_path = self.tmp_fils_path, ftype=INIT_FTYPE)
        self.copy_output = dmod.CreateZip()
        self.create_widgets()
        self.create_frame_select_dir()
        os.makedirs(self.tmp_fils_path, exist_ok=True)

    def create_widgets(self):
        # レイアウト
        self.frame_left = tk.Frame(self.master, width=GEO_MAIN_W//3, height=GEO_MAIN_H, bg="#f5f5dc")
        self.frame_center = tk.Frame(self.master, width=GEO_MAIN_W//3, height=GEO_MAIN_H, bg="#7fffd4")
        self.frame_right = tk.Frame(self.master, width=GEO_MAIN_W//3, height=GEO_MAIN_H, bg="#6495ed")
        self.frame_left.pack(side = tk.LEFT)
        self.frame_center.pack(side = tk.LEFT) 
        self.frame_right.pack(side = tk.LEFT) 

        self.frame_select_dir = tk.Frame(self.frame_left, width=GEO_MAIN_W//3, height=GEO_MAIN_H*(2/10),relief="sunken",borderwidth = 1, bg=self.frame_left.cget("bg"))
        self.frame_disp_img = tk.Frame(self.frame_left, width=GEO_MAIN_W//3, height=GEO_MAIN_H*(8/10), bg=self.frame_left.cget("bg"))
        self.frame_card_button = tk.Frame(self.frame_center, width=GEO_MAIN_W//3, height=GEO_MAIN_H*(2/10), bg=self.frame_center.cget("bg"))
        self.frame_card_list = tk.Frame(self.frame_center, width=GEO_MAIN_W//3, height=GEO_MAIN_H*(8/10), bg=self.frame_center.cget("bg"))
                
        self.frame_select_dir.pack(anchor=tk.W)      
        self.frame_select_dir.pack_propagate(False)    
        self.frame_select_dir.grid_propagate(False)
        self.frame_select_dir.update_idletasks()
        
        self.frame_disp_img.pack(anchor=tk.W)
        self.frame_disp_img.pack_propagate(False)
        self.frame_disp_img.grid_propagate(False)
        self.frame_disp_img.update_idletasks()

        self.frame_card_button.pack(anchor=tk.W)
        self.frame_card_button.pack_propagate(False)
        self.frame_card_button.grid_propagate(False)
        self.frame_card_button.update_idletasks() 

        self.frame_card_list.pack(anchor=tk.W)
        self.frame_card_list.pack_propagate(False)
        self.frame_card_list.grid_propagate(False)
        self.frame_card_list.update_idletasks() 

        self.frame_right.pack_propagate(False)
        self.frame_right.grid_propagate(False)
        self.frame_right.update_idletasks() 
      

    def create_frame_select_dir(self):
        # シートディレクトリ選択
        self.dir_tbox = tk.Entry(self.frame_select_dir, width = 50)
        self.dir_tbox.insert(tk.END,self.sheet_dir)   
        self.dir_tbox.grid(row=0, column=0, sticky=tk.W, pady=2)
    
        # 2行目表示
        row2 = tk.Frame(self.frame_select_dir, bg=self.frame_select_dir.cget("bg"))
        row2.grid(row=1,column = 0,sticky=tk.W,pady = 5)
        
        # 拡張子選択フォーム 
        self.ftype_list = ttk.Combobox(row2, state='readonly', width = 4)
        self.ftype_list["values"] = ("jpg", "png", "bmp")
        self.ftype_list.current(0)
        self.ftype_list.pack(side = tk.LEFT, anchor = tk.W)

        # シート選択ボタン
        self.select_dir_button = tk.Button(row2, text='シート選択', command=self.select_dir_button_func)
        self.select_dir_button.pack(side = tk.LEFT, padx=5) 

                
        # 3行目表示
        row3 = tk.Frame(self.frame_select_dir, bg=self.frame_select_dir.cget("bg"))
        row3.grid(row=2,column = 0,sticky=tk.W)
        # 行入力フォーム
        row_tex = tk.Label(row3,text = "行:", bg=self.frame_select_dir.cget("bg"))
        row_tex.pack(side = tk.LEFT) 
        self.row_tbox = tk.Entry(row3, width = 3)
        self.row_tbox.insert(tk.END, 3)   
        self.row_tbox.pack(side = tk.LEFT)
        # 列入力フォーム 
        colum_tex = tk.Label(row3,text = "列:", bg=self.frame_select_dir.cget("bg"))
        colum_tex.pack(side = tk.LEFT) 
        self.colum_tbox = tk.Entry(row3, width = 3)
        self.colum_tbox.insert(tk.END, 6)   
        self.colum_tbox.pack(side = tk.LEFT)
        # 削り幅割合フォーム
        colum_tex = tk.Label(row3,text = "削り幅(%):[短辺準拠]", bg=self.frame_select_dir.cget("bg"))
        colum_tex.pack(side = tk.LEFT) 
        self.rate_tbox = tk.Entry(row3, width = 3)
        self.rate_tbox.insert(tk.END, 3)   
        self.rate_tbox.pack(side = tk.LEFT)
        # 「シートをトリミング」ボタン
        self.run_trim_button = tk.Button(row3, text='シートをトリミング', command=self.run_trim_button_func)
        self.run_trim_button.pack(side = tk.LEFT, anchor=tk.E, padx = 12)

        row4 = tk.Frame(self.frame_select_dir, bg=self.frame_select_dir.cget("bg"))
        row4.grid(row=3,column = 0,sticky=tk.W)
        txt_label1 = tk.Label(row4, text = '【トリミング不要のカードを読み込む場合】', bg=row3.cget("bg"))
        txt_label1.pack(anchor = tk.W)
        txt_label2 = tk.Label(row4, font=("", 8, ""), text = ' 1)「シート選択」でカードのあるフォルダを選択。\n 2) 行1、列 1、削り幅を任意にしてトリミング。', bg=row3.cget("bg"),justify="left")
        txt_label2.pack(side = tk.LEFT, anchor = tk.W)
        # 「カード一覧表示」ボタン
        self.run_cardlist_button = tk.Button(row4, text='カード一覧表示', command=self.disp_card_list_button_func)
        self.run_cardlist_button.pack(side = tk.LEFT, anchor=tk.E, padx = 5)
        self.run_cardlist_button.config(state = tk.DISABLED)

        self.make_sheet_list()
        self.disp_img(self.sheet_list)

    def create_frame_card_operation(self):
        frow1 = tk.Frame(self.frame_card_button, bg = self.frame_card_button.cget("bg"))
        frow1.pack(anchor=tk.W)
        # #リストの選択解除ボタン
        all_select_button = tk.Button(frow1,text='全て選択',command=self.all_select_button_func)
        all_select_button.grid(row=0,column=0)
        all_clear_button = tk.Button(frow1, text='選択解除',command=self.all_clear_button_func)
        all_clear_button.grid(row=0, column=1)
 
        add_card_button = tk.Button(frow1, text='カード追加',command=self.add_card_buttom_func)
        add_card_button.grid(row=0, column=2)

        frow2 = tk.Frame(self.frame_card_button, bg = self.frame_card_button.cget("bg"))
        frow2.pack(anchor=tk.E)
        label1 = tk.Label(frow2, text="選択したカードの", bg = frow2.cget("bg"))
        label1.pack(side = tk.LEFT)
        self.card_cbox = tk.ttk.Combobox(frow2,width = 6, state = "readonly")
        self.card_cbox["values"] = (DT_OMOTE,DT_URA,DT_MAISUU)
        self.card_cbox.current(1)
        self.card_cbox.pack(side = tk.LEFT)
        label2 = tk.Label(frow2, text="を", bg = frow2.cget("bg"))
        label2.pack(side = tk.LEFT)
        self.card_entry = tk.Entry(frow2,width=8)
        self.card_entry.insert(tk.END, f'000.{INIT_FTYPE}') 
        self.card_entry.pack(side = tk.LEFT)
        label3 = tk.Label(frow2, text="に", bg = frow2.cget("bg"))
        label3.pack(side = tk.LEFT)
        run_card_change_button = tk.Button(frow2, text='変更する',command=self.run_card_change_button_func)
        run_card_change_button.pack(side = tk.LEFT)
        frow3 = tk.Frame(self.frame_card_button, bg = self.frame_card_button.cget("bg"))
        frow3.pack(anchor=tk.E)
        preview_button = tk.Button(frow3, text='選択したカードのプレビュー',command=self.preview_button_func)
        preview_button.pack()

    def create_frame_output_buttoms(self):
        frow1 = tk.Frame(self.frame_right, width = self.frame_right.cget("width"), height=GEO_MAIN_H*(1/10), bg = self.frame_right.cget("bg"))

        # 出力先ディレクトリ選択
        self.outdir_tbox = tk.Entry(frow1, width = 50)
        self.outdir_tbox.insert(tk.END, self.output_dir)   
        self.outdir_tbox.pack(side = tk.LEFT)

        frow2 = tk.Frame(self.frame_right, width = self.frame_right.cget("width"), height=GEO_MAIN_H*(1/10),bg = self.frame_right.cget("bg"))

        # シート選択ボタン
        select_dir_button = tk.Button(frow2, text='出力先フォルダの選択', command=self.select_outdir_button_func)
        select_dir_button.pack(side = tk.LEFT) 

        frow3 = tk.Frame(self.frame_right, width = self.frame_right.cget("width"), height=GEO_MAIN_H*(1/10),bg = self.frame_right.cget("bg"))
        # 出力ボタン
        l1 = tk.Label(frow3, text=" 出力ファイル名:", bg = frow3.cget("bg"))
        l1.pack(side = tk.LEFT)
        self.output_name_entry = tk.Entry(frow3, width = 8)
        self.output_name_entry.insert(tk.END, INIT_OUTPUT_NAME)
        self.output_name_entry.pack(side = tk.LEFT)
        l2 = tk.Label(frow3, text=".zip", bg = frow3.cget("bg"))
        l2.pack(side = tk.LEFT)
        deck_output_buttom = tk.Button(frow3, text='デッキを出力', command = self.deck_output_buttom_fnc)
        deck_output_buttom.pack(padx = 6, side = tk.LEFT)

        frow3.pack(fill=tk.BOTH, side = tk.BOTTOM,anchor=tk.N)
        frow2.pack(fill=tk.BOTH, side = tk.BOTTOM,anchor=tk.N)        
        frow1.pack(fill=tk.BOTH, side = tk.BOTTOM,anchor=tk.N)

    # def create_frame_disp_card(self):
    #     frame = tk.Frame(self.frame_right, width = self.frame_right.cget("width"), height=GEO_MAIN_H*(9/10), bg = self.frame_right.cget("bg"))

    def all_select_button_func(self):
        for dcard in self.dcard_list:
            dcard.cb.set(True)

    def all_clear_button_func(self):
        for dcard in self.dcard_list:
            dcard.cb.set(False)

    def disp_unimplemented(self):
        messagebox.showinfo("未実装", "この機能はまだないよ")

    def run_card_change_button_func(self):
        tar = self.card_cbox.get()
        txt = self.card_entry.get()
        if tar == DT_MAISUU and (txt.isdecimal() is False):
            messagebox.showinfo("エラー", "数字を入れて")
            return
        
        if tar != DT_MAISUU and not(INIT_FTYPE in txt):
            messagebox.showinfo("エラー", "拡張子不明")
            return
        
        for dcard in self.dcard_list:
            c = dcard.cb.get()
            if c is True:
                if tar == DT_OMOTE:
                    dcard.face.delete(0, tk.END)
                    dcard.face.insert(tk.END, txt)
                elif tar == DT_URA:
                    dcard.back.delete(0, tk.END)
                    dcard.back.insert(tk.END, txt)
                elif tar == DT_MAISUU:
                    dcard.num.delete(0, tk.END)
                    dcard.num.insert(tk.END, txt)
                else:
                    messagebox.showinfo("エラー", "予期せぬエラー")


    def select_dir_button_func(self):
        # フォルダ選択ダイアログ
        tmp_dir = filedialog.askdirectory(initialdir = os.path.dirname(__file__), title ="シートがあるフォルダを選択")
        if len(tmp_dir)!=0:
            self.sheet_dir = pathlib.Path(tmp_dir)
            self.dir_tbox.delete(0, tk.END) 
            self.dir_tbox.insert(tk.END, str(self.sheet_dir))
            self.make_sheet_list()
            self.disp_img(self.sheet_list)
    
    
    def select_outdir_button_func(self):
        # フォルダ選択ダイアログ
        tmp_dir = filedialog.askdirectory(initialdir = os.path.dirname(__file__), title ="出力フォルダを選択")
        if len(tmp_dir)!=0:
            self.output_dir = pathlib.Path(tmp_dir)
            self.outdir_tbox.delete(0, tk.END) 
            self.outdir_tbox.insert(tk.END, str(self.output_dir))
                
    def run_trim_button_func(self):
        self.remove_cards()
        self.ftype = self.ftype_list.get()
        self.cut_out_cards.rownum = int(self.row_tbox.get())
        self.cut_out_cards.columnum = int(self.colum_tbox.get())
        self.cut_out_cards.cut_offset_rate = float(self.rate_tbox.get())
        self.cut_out_cards.cut_out(self.sheet_list)
        time.sleep(0.1)
        self.make_cardimg_dict()
        self.disp_img(self.img_dict)
        # messagebox.showinfo("メッセージ", "トリミング完了")
        self.run_cardlist_button.config(state = tk.ACTIVE)     

    def disp_card_list_button_func(self):
        self.make_card_list()
        self.disp_card_list()
        if self.cardlist_once is False:
            self.create_frame_card_operation()
            self.cardlist_once = True
    
    def deck_output_buttom_fnc(self):
        oname = self.output_name_entry.get()
        if len(str(self.output_dir)) == 0:
            messagebox.showinfo("エラー", "フォルダが指定されていません。")
            return
        if len(str(oname)) == 0:
            messagebox.showinfo("エラー", "ファイル拡張子が指定されていません。")
            return 
        opath = self.output_dir / oname
        wpath = self.tmp_fils_path / oname

        os.makedirs(wpath, exist_ok=True)
        self.copy_output.create_zip(card_list = self.outcard_list, out_path=opath, work_path = wpath)
        messagebox.showinfo("メッセージ", "デッキ作成完了")
        
    def add_card_buttom_func(self):
        self.add_new_card_dcard()

    def preview_button_func(self):
        self.make_outcard_list()
        if self.preview_once is False:
            self.create_frame_output_buttoms()
        self.disp_outcard_preview()
        self.preview_once = True
        

    def make_cardimg_dict(self):
        self.img_dict = {}
        if len(str(self.tmp_fils_path)) == 0:
            messagebox.showinfo("エラー", "フォルダが指定されていません。")
            return
        if len(str(self.ftype)) == 0:
            messagebox.showinfo("エラー", "ファイル拡張子が指定されていません。")
            return         
        files = self.tmp_fils_path.glob(f'**/*.{INIT_FTYPE}')
        files = natsorted(files)

        for file in files:
            with open(file, 'rb') as image:
                target = image.read()
                target_sha256 = hashlib.sha256(target).hexdigest() 
                card = mcf.CardImg(path = file, f_hash= target_sha256)
                self.img_dict.update({file.name: card})

    def make_card_list(self):
        self.card_list = []
        for id,cimg in enumerate(self.img_dict.values()):
            self.card_list.append(mcf.Card(id=id, face = cimg, back = self.img_dict[f"blank.{INIT_FTYPE}"]))

    def make_outcard_list(self):
        self.outcard_list = []
        for dc in self.dcard_list:
            if dc.cb.get() is True:
                id = dc.id
                face_img_name = dc.face.get()
                back_img_name = dc.back.get()
                tnum = dc.num.get()
                if not(tnum.isdecimal()):
                    messagebox.showinfo("エラー", f"ID{id}の枚数が正しくありません。")
                    return                   
                if not(face_img_name in self.img_dict.keys()):
                    messagebox.showinfo("エラー", f"ID{id}の表面{face_img_name}は存在しません。")
                    return
                if not(back_img_name in self.img_dict.keys()):
                    messagebox.showinfo("エラー", f"ID{id}の裏面{back_img_name}のカードは存在しません。")
                    return
                face = self.img_dict[face_img_name]
                back = self.img_dict[back_img_name]
                for i in range(int(tnum)):
                    self.outcard_list.append(mcf.Card(id = id, face = face, back = back))

    def add_new_card_dcard(self):
        id = len(self.dcard_list)
        self.card_list.append(mcf.Card(id = id,face =  self.img_dict[f"blank.{INIT_FTYPE}"], back = self.img_dict[f"blank.{INIT_FTYPE}"]))
        self.add_dcard_list(id, self.card_list[-1])

    def remove_cards(self):
        files = self.tmp_fils_path.glob(f'**/*')
        for f in files:
            if os.path.isfile(f):
                os.remove(f)    
    
    def remove_dir(self):
        for i in range(20):
            if os.path.isdir(self.tmp_fils_path):
                try:
                    shutil.rmtree(self.tmp_fils_path)
                except Exception:
                    print(f"{i}回目:e　",end="")
                    time.sleep(0.5)
            else:
                print()
                break
        else:
            messagebox.showinfo("エラー", "作業フォルダを削除できませんでした。")
        

    def make_sheet_list(self):
        self.ftype = self.ftype_list.get()
        if len(str(self.sheet_dir)) == 0:
            messagebox.showinfo("エラー", "フォルダが指定されていません。")
            return
        if len(str(self.ftype)) == 0:
            messagebox.showinfo("エラー", "ファイル拡張子が指定されていません。")
            return
        files = self.sheet_dir.glob(f'**/*.{self.ftype}')
        self.sheet_list = natsorted(files)

    def disp_img(self, tarflist):
        """
        カードシートとカードシートで共有で使う画像表示領域作成＆更新用
        """
        if self.disp_img_once is False:
            self.disp_img_once = True
            self.disp_img_stxt = scrolledtext.ScrolledText(self.frame_disp_img, bg = self.frame_disp_img.cget("bg"))
            self.disp_img_stxt.pack(fill=tk.BOTH, expand=1)
        else:
            self.disp_img_stxt.configure(state=tk.NORMAL)
            self.disp_img_stxt.delete('1.0', tk.END)
        self.disp_img_stxt.configure(state=tk.DISABLED)

        if type(tarflist) is dict:
            tarflist = list(tarflist.values())

        for in_file in tarflist:
            s = str(in_file)
            img = Image.open(open(s, 'rb'))
            ImageLabel(self.disp_img_stxt, s, ImageTk.PhotoImage(img.resize(get_size(img.size), Image.NEAREST)))

    def disp_outcard_preview(self):
        """
        出力画像プレビューで使う画像表示領域作成＆更新用。
        frameを引数にしてdisp_imgと共有にしてもいいかと思ったが、場合分け面倒なので別作成。
        """
        if self.preview_once is False:
            frame = tk.Frame(self.frame_right, width = self.frame_right.cget("width"), height=GEO_MAIN_H*(9/10), bg = self.frame_right.cget("bg"))
            frame.pack(fill=tk.BOTH, side = tk.BOTTOM,anchor=tk.N)
            frame.pack_propagate(False)    
            frame.grid_propagate(False)
            frame.update_idletasks()
            self.disp_card_stxt = scrolledtext.ScrolledText(frame, bg = self.frame_right.cget("bg"))
            self.disp_card_stxt.pack(fill=tk.BOTH, expand=1)
        else:
            self.disp_card_stxt.configure(state=tk.NORMAL)
            self.disp_card_stxt.delete('1.0', tk.END)
        self.disp_card_stxt.configure(state=tk.DISABLED)
        
        #subframeをdisp_card_stxtに配置
        subframe = tk.Frame(self.disp_card_stxt, bg = self.disp_card_stxt.cget("bg")) #背景を白に
        # frame.pack(fill=tk.BOTH, side = tk.BOTTOM,anchor=tk.N)
        self.disp_card_stxt.window_create(tk.END, align=tk.BASELINE, padx=5, pady=5, window=subframe)

        for card in self.outcard_list:
            fp = str(card.face.path)
            bp = str(card.back.path)
            fimg = Image.open(open(fp, 'rb'))
            bimg = Image.open(open(bp, 'rb'))
            width = 2.3*THUMBNAIL_W
            height =1.3* THUMBNAIL_H
            label_frame = tk.LabelFrame(subframe,bd=2, width = width, height=height, relief="ridge",text=f"ID{card.id}", bg = self.disp_card_stxt.cget("bg"))
            label_frame.pack(pady=5)
            label_frame.pack_propagate(False)
            txtw = tk.Text(label_frame, bg = self.disp_card_stxt.cget("bg"))
            txtw.pack()
            txtw.configure(state=tk.DISABLED)
            ImageLabel(txtw, fp, ImageTk.PhotoImage(fimg.resize(get_size(fimg.size), Image.NEAREST)))
            ImageLabel(txtw, bp, ImageTk.PhotoImage(bimg.resize(get_size(bimg.size), Image.NEAREST)))
           

    #表を作成
    def disp_card_list(self):       
        num_list = len(self.card_list) #リストの数
        
        cv_width = GEO_MAIN_W//4
        cv_height = GEO_MAIN_H*(8/10)

        #スクロールバー
        # self.disp_cardlist_stxt=tk.ttk.Scrollbar(self.frame_card_list,orient=tk.VERTICAL) #縦方向
        if self.list_once is False:
            self.list_once = True
            self.disp_cardlist_stxt = scrolledtext.ScrolledText(self.frame_card_list, bg = self.frame_card_list.cget("bg"))
            # self.disp_cardlist_stxt.grid(row=1,column=0,sticky='ns') 
            self.disp_cardlist_stxt.pack(fill=tk.BOTH, expand=1)
        else:
            self.disp_cardlist_stxt.configure(state=tk.NORMAL)
            self.disp_cardlist_stxt.delete('1.0', tk.END)
        self.disp_cardlist_stxt.configure(state=tk.DISABLED)

        #Frameを作成
        self.subframe_card_list = tk.Frame(self.disp_cardlist_stxt, bg ='white') #背景を白に

        #frameをvbarに配置
        self.disp_cardlist_stxt.window_create(tk.END, align=tk.BASELINE, padx=5, pady=5, window=self.subframe_card_list)


    
        #header row=1に設定する文字列 余白は0に
        e0=tk.Label(self.subframe_card_list,width=C0WIDTH,text='ID',background='white')
        e0.grid(row=1,column=0,padx=0,pady=0,ipadx=0,ipady=0) #0列目
    
        e1=tk.Label(self.subframe_card_list,width=C1WIDTH,text='選択',background='white',anchor='w')
        e1.grid(row=1,column=1,padx=0,pady=0,ipadx=0,ipady=0) #1列目
    
        e2=tk.Label(self.subframe_card_list,width=C2WIDTH,text=DT_OMOTE,background='white',anchor='w')
        e2.grid(row=1,column=2,padx=0,pady=0,ipadx=0,ipady=0) #2列目
        
        e3=tk.Label(self.subframe_card_list,width=C3WIDTH,text=DT_URA,background='white',anchor='w')
        e3.grid(row=1,column=3,padx=0,pady=0,ipadx=0,ipady=0) #3列目

        e4=tk.Label(self.subframe_card_list,width=C4WIDTH,text=DT_MAISUU,background='white',anchor='w')
        e4.grid(row=1,column=4,padx=0,pady=0,ipadx=0,ipady=0) #4列目

        irow = 2
        irow0=2
        erow=num_list+irow0
            
        self.dcard_list = []
        # while irow < erow:   #リストの数分ループしてLabelとチェックボックスを設置
        for i, card in enumerate(self.card_list):            
            self.add_dcard_list(id=i, card=card)

    def add_dcard_list(self, id, card):
        irow = id+2
        #色の設定
        if irow%2==0:
            color='#cdfff7'  #薄い青
        else:
            color='white'
        #カードID
        a0 = id
        b0=tk.Label(self.subframe_card_list,width=C0WIDTH,text=a0,background=color,anchor='w')
        b0.grid(row=irow,column=0,padx=0,pady=0,ipadx=0,ipady=0) #0列目

        #チェックボックスの設置
        bln=tk.BooleanVar()        
        bln.set(False) 
        c = tk.Checkbutton(self.subframe_card_list,variable = bln,width=C0WIDTH,text='',background=color)
        # list_chk.append(bln) #チェックボックスの初期値
        c.grid(row=irow,column=1,padx=0,pady=0,ipadx=0,ipady=0)  #1列目
        
        #カード表面
        # a2 = self.card_list[irow-irow0].face.path.name
        a2 = card.face.path.name
        b2 = tk.Entry(self.subframe_card_list,width=C2WIDTH, background=color)
        b2.insert(tk.END, a2) 
        b2.grid(row=irow,column=2,padx=0,pady=0,ipadx=0,ipady=0) #2列目
        
        #カード裏面
        # a3 = self.card_list[irow-irow0].face.path.name
        a3 = card.back.path.name
        b3 = tk.Entry(self.subframe_card_list,width=C3WIDTH, background=color)
        b3.insert(tk.END, a3) 
        b3.grid(row=irow,column=3,padx=0,pady=0,ipadx=0,ipady=0) #3列目
        
        #カード枚数
        a4 = 1 #デフォルトは1枚
        b4 = tk.Entry(self.subframe_card_list,width=C4WIDTH, background=color)
        b4.insert(tk.END, a4) 
        b4.grid(row=irow,column=4,padx=0,pady=0,ipadx=0,ipady=0) #4列目
        
        # チェックボックス、テキストボックスの情報を外部参照できるように保存
        self.dcard_list.append(mcf.dCard(a0, bln, b2, b3, b4))

# 実行
root = tk.Tk()        
root.resizable(1,1)
myapp = Application(master=root)
myapp.master.title("デッキメーカー") # タイトル

myapp.mainloop()
myapp.remove_dir()
