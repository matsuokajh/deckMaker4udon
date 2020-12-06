import numpy as np
# import cv2
from PIL import Image, ImageTk
import math
import os
import pathlib 
import my_class_file as mcf
import shutil
from tkinter import messagebox
import time

class CutOutCards:
    def __init__(self, rownum, columnum, dir_out_path , ftype, mkblank = True, cut_offset_rate = 1):
        """
        dir_out_path：出力パス
        rownum：シート内のカードの行数
        columnum：シート内のカードの列数
        """
        self.rownum = rownum
        self.columnum =columnum
        self.dir_out_path = dir_out_path
        self.mkblank = mkblank
        self.ftype = ftype
        self.cut_offset_rate = cut_offset_rate

    
    def cut_out(self, img_list:list):
        """cut_out_cards
        説明：dir_in_path内のfile_type拡張子の  シートをカードサイズに切り取る
        引数：
            dir_in_path：入力するファイルのディレクトリパス
            file_type：入力するファイルの拡張子
        戻り値：なし
        """
        if self.rownum < 0 or self.columnum < 0:
            messagebox.showinfo("エラー","行数、列数は1以上を指定して下さい。")
            return

        if self.cut_offset_rate<0 or self.cut_offset_rate>99:
            messagebox.showinfo("エラー","カード幅は1.0-99.0の値を指定してください。")
            return
        k = 0

        f = self.dir_out_path.glob(f'**/*.{self.ftype}')
        for dir_blank in range(30):
            p = len(list(f))
            if  p== 0:
                break
            f = self.dir_out_path.glob(f'**/*.{self.ftype}')
            time.sleep(0.1)
        else:
            print(f"エラー：フォルダが空にならない")


        for in_file in img_list:
            in_file = str(in_file)
            input_im = my_imread(in_file)
            [all_h, all_w, all_d] = input_im.shape
            card_h = math.floor(all_h/self.rownum)
            card_w = math.floor(all_w/self.columnum)
            cut_offset = int(min([card_h, card_w])*self.cut_offset_rate*(0.01))
            # print(f"b={input_im.shape}")
            input_im = np.pad(input_im,((cut_offset//2,cut_offset//2),(cut_offset//2,cut_offset//2),(0,0)),"edge")
            [all_h, all_w, all_d] = input_im.shape
            # print(f"a={input_im.shape}")
            
            card_h = math.floor(all_h/self.rownum)
            card_w = math.floor(all_w/self.columnum)
            all_h = card_h*self.rownum
            all_w = card_w*self.columnum
            
            for i in range(0, all_h, card_h+1):
                for j in range(0, all_w, card_w+1):
                    i_end = i+card_h+1
                    j_end = j+card_w+1
                
                    card = input_im[i+cut_offset:i_end-cut_offset, j+cut_offset:j_end-cut_offset,:]
                    # cv2.imshow('sample', card)
                    # cv2.waitKey(0)
                    out_fname = self.dir_out_path / f"{k:0>3}.{self.ftype}"
                    my_imwrite(str(out_fname),card)
                    k = k+1
        if self.mkblank is True:
            self.make_blank_card(k, card)
        print("complete cut out.")

    def make_blank_card(self, k, card):
        bcard = 128*np.ones_like(card)
        out_fname = self.dir_out_path / f"blank.{self.ftype}"
        my_imwrite(str(out_fname),bcard)

# def my_imread(filename, flags=cv2.IMREAD_COLOR, dtype=np.uint8):
#     try:
#         n = np.fromfile(filename, dtype)
#         img = cv2.imdecode(n, flags)
#         return img
#     except Exception as e:
#         print(e)
#         return None

def my_imread(filename):
    try:
        img = Image.open(filename)
        input_im = np.asarray(img)
        return input_im
    except Exception as e:
        print(e)
        return None

# def my_imwrite(filename, img, params=None):
#     try:
#         ext = os.path.splitext(filename)[1]
#         result, n = cv2.imencode(ext, img, params)

#         if result:
#             with open(filename, mode='w+b') as f:
#                 n.tofile(f)
#             return True
#         else:
#             return False
#     except Exception as e:
#         print(e)
#         return False

def my_imwrite(filename, img, params=None):
    try:
        pil_img = Image.fromarray(img)
        pil_img.save(filename)
        return True
    except Exception as e:
        print(e)
        return False

class CreateZip:
    def __init__(self):
        self.s1 = '<?xml version="1.0" encoding="UTF-8"?><card-stack location.name="table" location.x="-25" location.y="-25" posZ="0" rotate="0" zindex="0" owner="" isShowTotal="true"><data name="card-stack"><data name="image"><data type="image" name="imageIdentifier"></data></data><data name="common"><data name="name">deck</data></data><data name="detail"></data></data><node name="cardRoot">'
        self.s2 = '<card location.name="table" location.x="0" location.y="0" posZ="0" state="0" rotate="0" owner="" zindex="0"><data name="card"><data name="image"><data type="image" name="imageIdentifier"></data><data type="image" name="front">'
        self.s3 = '</data>'
        self.s4 = '<data type="image" name="back">'
        self.s5 = '</data>'
        self.s6 = '</data><data name="common"><data name="name">card</data><data name="size">2</data></data><data name="detail"></data></data></card>'
        self.s7 = '</node></card-stack>'
        self.sn = '\n'
        self.fname = 'data.xml'

    def create_xml_str(self,card_list:list):
        xml_str = self.s1 + self.sn*2
        for card in card_list:
            xml_str = xml_str + self.s2 + card.face.f_hash + self.s3 +self.sn
            xml_str = xml_str + self.s4 + card.back.f_hash + self.s5 +self.sn
            xml_str = xml_str + self.s6 + self.sn
        xml_str = xml_str + self.sn + self.s7 + self.sn
        return xml_str
    
    def create_xml(self,card_list:list, path:pathlib.Path):
        sss = self.create_xml_str(card_list)
        fpath = path / self.fname
        with open(fpath, 'w', encoding="utf_8") as f:
            f.write(sss)

    def copy_output_cards(self, card_list:list, path:pathlib.Path):
        output_list = set()
        for card in card_list:
            output_list.add(card.face.path)
            output_list.add(card.back.path)
        
        for cimg in output_list:
            out_path = path / cimg.name
            shutil.copy(cimg, out_path)

    def create_zip(self, card_list:list, out_path:pathlib.Path, work_path:pathlib.Path):
        self.create_xml(card_list, work_path)
        self.copy_output_cards(card_list, work_path)
        shutil.make_archive(out_path, 'zip', root_dir=work_path)


