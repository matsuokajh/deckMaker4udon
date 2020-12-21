import numpy as np
import cv2
from matplotlib import pyplot as plt
# import math

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

def calc_outcard_size(contours):
    ''' 出力画像のサイズ計算'''
    cnt = contours[0]
    rect = cv2.minAreaRect(cnt)
    h, w = rect[1]
    return int(h), int(w)

def my_pad(img):
    size = img.shape
    if len(size) == 2:
        h, w = size
        lens = max([h,w])
        tmp = np.pad(img, [((lens-h)//2, (lens-h)//2),((lens-w)//2, (lens-w)//2)], 'edge')
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

    for y in range(h):
        for x in range(w):
            if thresh[x,y] != 0:
                thresh = cv2.floodFill(image=thresh, mask=None, seedPoint = (x,y), newVal=0,flags=4)[1]
                break
        else:
            continue
        break
    cv2.imwrite(f"bw.jpg", np.hstack([thresh_org,thresh]))
    return thresh

def main():
    # 画像読み込み
    # img = cv2.imread('image0.jpg')
    # img = cv2.imread('image0 (2).jpg')
    img = cv2.imread('rf.jpg')

    # 雑音除去
    # img = cv2.medianBlur(img,5)
    # img = cv2.GaussianBlur(img,(5,5),0)

    # Prepocess
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # gray = cv2.equalizeHist(gray) # ヒストグラム均等化：カードのエッジのコントラストが上がる。場合によっては必要かも

    # flag, thresh = cv2.threshold(gray, luminance_threshold(gray), 255, cv2.THRESH_BINARY)
    # thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY+cv2.THRESH_OTSU)[1]
    thresh = make_mask_at(gray) # 適応的しきい値処理による二値化、影の映り込みにロバストs
    # cv2.imwrite(f"bw.jpg", thresh)
    # cv2.imshow("bw",thresh)
    # cv2.waitKey(0)

    # 画像の射影変換（回転）時に端が途切れにくいように、画像を正方形にする
    img = my_pad(img)
    thresh = my_pad(thresh)

    # Find contours
    contours, hierarchy = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=cv2.contourArea, reverse=True) 
    # contours = sorted(contours, key=cv2.arcLength, reverse=True) 

    # Select long perimeters only
    perimeters = [cv2.contourArea(contours[i]) for i in range(len(contours))]
    # cv2.imshow("perim",perimeters[0])
    # cv2.waitKey(0)
    listindex=[i for i in range(len(perimeters)) if perimeters[i]>perimeters[0]/10]


    # Show image
    imgcont = img.copy()
    [cv2.drawContours(imgcont, [contours[i]], 0, (0,255,0), 5) for i in listindex]
    # plt.imshow(imgcont)
    # plt.show()
    cv2.imwrite(f"frame.jpg", imgcont)

    # 出力画像のサイズ計算
    card_img_height, card_img_width= calc_outcard_size(contours)

    num = 0
    for i, ind in enumerate(listindex):
        cnt = contours[ind]
        rect = cv2.minAreaRect(cnt)

        ###############矩形近似＆射影変換#################
        # 輪郭を凸形で近似
        epsilon = 0.05 * cv2.arcLength(cnt, True)
        approx = cv2.approxPolyDP(cnt, epsilon, True)
        imghull = img.copy()
        cv2.drawContours(imghull, [approx], 0, (255,0,0), 10)
        plt.imshow(imghull)
        # plt.show()

        # カードの横幅　# for分の外に移行
        # card_img_width = 1600 # 適当な値
        # card_img_height = 2400 # 適当な値

        src = np.float32(list(map(lambda x: x[0], approx[:4,...])))
        src = sort_points(src,img)
        dst = np.float32([[0,0],[0,card_img_height],[card_img_width,card_img_height],[card_img_width,0]])

        projectMatrix = cv2.getPerspectiveTransform(src, dst)

        res = cv2.warpPerspective(img, projectMatrix, (card_img_width, card_img_height),flags=cv2.INTER_CUBIC)
        #########################################

        if res.size != 0:
                cv2.imwrite(f"out/out{num}.jpg", res)
                # cv2.imwrite(f"out/out_d{i}.jpg", res)
                num = num + 1
        else:
            continue

        # canny = cv2.Canny(res, 100, 200)
        # cv2.imwrite(f"canny{i}.jpg", canny)

if __name__ == "__main__":
    main()