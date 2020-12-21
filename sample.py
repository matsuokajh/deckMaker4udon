import numpy as np
import cv2
from matplotlib import pyplot as plt
# import math

DEB_DIR = "img_debug"
IN_DIR = "img_in"
OUT_DIR = "img_out"

IN_FIL = "01.jpg"
# IN_FIL = "image0 (1).jpg"
# IN_FIL = "image0 (2).jpg"
# IN_FIL = "image0.jpg"
# IN_FIL = "rf.jpg"
# IN_FIL = "rf_rot.jpg"
# IN_FIL = "yabaiare1.jpg"


# def histogram_equalization(img):
#     hist,bins = np.histogram(img.flatten(),256,[0,256])
#     cdf = hist.cumsum()
#     cdf_normalized = cdf * hist.max()/ cdf.max()
#     return cdf_normalized

# def luminance_threshold(gray_img, card_luminance_percentage = 0.2):
#     """
#     グレースケールでの値(輝度と呼ぶ)が `x` 以上のポイントの数が(100*card_luminance_percentage)%を超えるような最大のxを計算する
#     ただし、 `100 <= x <= 200` とする
#     """
    
#     number_threshold = gray_img.size * card_luminance_percentage
#     flat = gray_img.flatten()
#     # 200 -> 100 
#     for diff_luminance in range(100):
#         if np.count_nonzero(flat > 200 - diff_luminance) >= number_threshold:
#             return 200 - diff_luminance
#     return 100

# def within(point, cnts):
#     '''点 point が四角形 rect に含まれているかどうか
#     '''
#     for c in cnts:
#         count = 0
#         tar = 2
#         for p in point:
#             if cv2.pointPolygonTest(c, tuple(p), False) == 1:
#                 count = count+1
#             if count >= tar:    
#                 return True
#     return False

def crop_minAreaRect(img, rect):
    # rotate img
    angle = rect[2]
    rows,cols = img.shape[0], img.shape[1]
    M = cv2.getRotationMatrix2D((cols/2,rows/2),angle,1)
    img_rot = cv2.warpAffine(img,M,(rows,cols))

    plt.imshow(img_rot)
    # plt.show()

    # rotate bounding box
    box = cv2.boxPoints(rect)
    pts = np.int64(cv2.transform(np.array([box]), M))[0]
    pts[pts < 0] = 0

    # crop
    img_crop = img_rot[pts[1][1]:pts[0][1],
    pts[1][0]:pts[2][0]]

    return img_crop

# def calc_outcard_size(contours):
#     ''' 出力画像のサイズ計算'''
#     cnt = contours[0]
#     rect = cv2.minAreaRect(cnt)
#     h, w = rect[1]
#     return int(h), int(w)

def calc_outcard_size(contours):
    ''' 出力画像のサイズ計算'''
    min_l = cv2.arcLength(contours[0],True)
    rect = cv2.minAreaRect(contours[0])
    h_star, w_star = rect[1]
    for i, cnt in enumerate(contours):
        rect = cv2.minAreaRect(cnt)
        h, w = rect[1]
        length = cv2.arcLength(cnt, True)
        tmp = abs((h+w) - length/2)
        if tmp < min_l:
            min_l = tmp
            h_star = h
            w_star = w
        if i > 5:
            break
    return int(h_star), int(w_star)

def my_pad(img):
    size = img.shape
    if len(size) == 2:
        h, w = size
        lens = max([h,w])
        tmp = np.pad(img, [((lens-h)//2, (lens-h)//2), ((lens-w)//2, (lens-w)//2)], 'edge')
    else:
        h, w = size[:2]
        lens = max([h,w])
        tmp = np.pad(img, [((lens-h)//2, (lens-h)//2),((lens-w)//2, (lens-w)//2),(0,0)], 'edge')
    
    return tmp


def sort_points(points,img):
    xmax, ymax = img.shape[:2]
    # xmax, ymax = np.max(points,axis=0)
    
    nmax = np.max(points)**2
    base = [np.array([0, 0]), np.array([0, ymax]), np.array([xmax, ymax]), np.array([xmax, 0])]
    tar = list(points)
    res = []
    for i, b in enumerate(base):
        min_num = nmax
        j_star = -1
        for j, p in enumerate(tar):
            tmp = np.linalg.norm(b-p)
            if tmp < min_num:
                min_num = tmp
                j_star = j
        res.append(tar.pop(j_star))
    return np.array(res)

def make_mask_at(gray):
    h, w = gray.shape

    # グレー画像への雑音除去
    gray = cv2.medianBlur(gray,5)
    thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY,31, 5) # 適応的しきい値処理による二値化
    
    # モルフォロジーによる線調整
    # kernel = cv2.getStructuringElement(cv2.MORPH_CROSS,(3,3))
    # thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
    # thresh = cv2.erode(thresh,kernel,iterations = 1)

    thresh_org = thresh.copy() #デバッグ画像用

    for y in [0, h-1]:
        for x in range(w):

            if thresh[y, x] != 0:
                thresh = cv2.floodFill(image=thresh, mask=None, seedPoint = (y,x), newVal=0,flags=4)[1]
                break
        else:
            continue
        break

    cv2.imwrite(f"{DEB_DIR}/bw.jpg", np.hstack([thresh_org,thresh]))
    return thresh

def select_usable_contours(contours):
    """ 面積が一番大きい輪郭のn分の1以上で、四角に線形補間可能な輪郭とその近似線（aprrox）を返す
    """
    contours = sorted(contours, key=cv2.contourArea, reverse=True)
    res_cnt = []
    res_approx = []
    base_area = cv2.contourArea(contours[0])/10
    for i, cnt in enumerate(contours):
        a = cv2.contourArea(cnt)

        # 輪郭を凸形で近似
        epsilon = 0.05 * cv2.arcLength(cnt, True)
        approx = cv2.approxPolyDP(cnt, epsilon, True)

        if len(approx) == 4 and a>base_area:
            res_cnt.append(cnt)
            res_approx.append(approx)     
    return res_cnt, res_approx


def main():
    # 画像読み込み
    img = cv2.imread(f'{IN_DIR}/{IN_FIL}')

    # 雑音除去
    # img = cv2.medianBlur(img,5)
    # img = cv2.GaussianBlur(img,(5,5),0)

    # Prepocess
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # gray = cv2.equalizeHist(gray) # ヒストグラム均等化：カードのエッジのコントラストが上がる。場合によっては必要かも

    # flag, thresh = cv2.threshold(gray, luminance_threshold(gray), 255, cv2.THRESH_BINARY)
    # thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY+cv2.THRESH_OTSU)[1]
    thresh = make_mask_at(gray) # 適応的しきい値処理による二値化、影の映り込みにロバスト
    # cv2.imwrite(f"{DEB_DIR}/bw.jpg", thresh)
    # cv2.imshow("bw",thresh)
    # cv2.waitKey(0)

    # 画像の射影変換（回転）時に端が途切れにくいように、画像を正方形にする
    img = my_pad(img)
    thresh = my_pad(thresh)

    # Find contours
    contours, hierarchy = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    # Show image
    imgcont = img.copy()
    
    # deb: 抽出されたすべての輪郭を赤で表示
    [cv2.drawContours(imgcont, [cnt], 0, (0,0,255), 8) for cnt in contours]
    cv2.imwrite(f"{DEB_DIR}/frame.jpg", imgcont)
    
    # 条件を満たしたcontorsのindexのみを選出
    contours, approxes = select_usable_contours(contours)

    # deb: 条件を満たす輪郭とその近似線を、緑と青で表示
    [cv2.drawContours(imgcont, [cnt], 0, (0,255,0), 8) for cnt in contours]
    [cv2.drawContours(imgcont, [a], 0, (255, 0, 0), 8) for a in approxes]
    cv2.imwrite(f"{DEB_DIR}/frame.jpg", imgcont)

    # 条件を満たす輪郭がない場合は処理を終了する
    if len(contours) == 0:
        print("MyError:切り取れるカードがありません。debugフォルダを確認して下さい。")
        return -1

    # 出力画像のサイズ計算
    card_img_height, card_img_width= calc_outcard_size(contours)

    num = 0
    for approx in approxes:
        src = np.float32(list(map(lambda x: x[0], approx)))
        src = sort_points(src,img)
        dst = np.float32([[0,0],[0,card_img_height],[card_img_width,card_img_height],[card_img_width,0]])

        ###############射影変換#################
        project_matrix = cv2.getPerspectiveTransform(src, dst)
        res = cv2.warpPerspective(img, project_matrix, (card_img_width, card_img_height),flags=cv2.INTER_CUBIC)
        #########################################

        if res.size != 0:
                cv2.imwrite(f"{OUT_DIR}/out{num}.jpg", res)
                num = num + 1
        else:
            continue
if __name__ == "__main__":
    main()