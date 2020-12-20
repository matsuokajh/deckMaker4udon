import numpy as np
import cv2
from matplotlib import pyplot as plt
import math

card_luminance_percentage = 0.2

def luminance_threshold(gray_img):
    """
    グレースケールでの値(輝度と呼ぶ)が `x` 以上のポイントの数が20%を超えるような最大のxを計算する
    ただし、 `100 <= x <= 200` とする
    """
    number_threshold = gray_img.size * card_luminance_percentage
    flat = gray_img.flatten()
    # 200 -> 100 
    for diff_luminance in range(100):
        if np.count_nonzero(flat > 200 - diff_luminance) >= number_threshold:
            return 200 - diff_luminance
    return 100

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
    rect0 = (rect[0], rect[1], 0.0)
    box = cv2.boxPoints(rect)
    pts = np.int0(cv2.transform(np.array([box]), M))[0]
    pts[pts < 0] = 0

    # crop
    img_crop = img_rot[pts[1][1]:pts[0][1],
    pts[1][0]:pts[2][0]]

    return img_crop


def myPad(img):
    h, w, d = img.shape
    lens = max([h,w])
    tmp = np.pad(img, [((lens-h)//2, (lens-h)//2),((lens-w)//2, (lens-w)//2),(0,0)], 'constant')
    
    return tmp


# def sortPoints(points,img):
#     xmax, ymax, d = img.shape
#     # xmax, ymax = np.max(points,axis=0)
    
#     nmax = np.max(points)**2
#     base = [np.array([0, 0]), np.array([0, ymax]), np.array([xmax, ymax]), np.array([xmax, 0])]
#     tar = points.copy()
#     res = points.copy()
#     min_e = [nmax, nmax, nmax, nmax]
#     for p in tar:
#         for i in range(len(base)):
#             tmp = np.linalg.norm(base[i]-p)
#             if min_e[i]>tmp:
#                 min_e[i] = tmp
#                 res[i] = p  
#     return res

def sortPoints(points,img):
    xmax, ymax, d = img.shape
    # xmax, ymax = np.max(points,axis=0)
    
    nmax = np.max(points)**2
    base = [np.array([0, 0]), np.array([0, ymax]), np.array([xmax, ymax]), np.array([xmax, 0])]
    tar = list(points)
    res = []
    for i, b in enumerate(base):
        min_num = nmax
        j_star = -1
        for j, p in enumerate(tar):
            tmp = np.linalg.norm(base[i]-p)
            if tmp < min_num:
                min_num = tmp
                j_star = j
        res.append(tar.pop(j_star))
    return np.array(res)

img = cv2.imread('rf.jpg')
img = myPad(img)
# Prepocess
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
flag, thresh = cv2.threshold(gray, luminance_threshold(gray), 255, cv2.THRESH_BINARY)
cv2.imwrite(f"bw.jpg", thresh)
# cv2.imshow("gray",thresh)
# cv2.waitKey(0)

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

num = 0
for i, ind in enumerate(listindex):
    cnt = contours[ind]
    rect = cv2.minAreaRect(cnt)



    #########################################
    # 輪郭を凸形で近似
    # 輪郭の全長に固定値で 0.1 の係数をかけるので十分
    # ある程度まともにカードを写す前提では係数のチューニングはほぼ不要と思われる(OCRの調整では必要かも)
    epsilon = 0.05 * cv2.arcLength(cnt, True)
    approx = cv2.approxPolyDP(cnt, epsilon, True)
    imghull = img.copy()
    cv2.drawContours(imghull, [approx], 0, (255,0,0), 10)
    plt.imshow(imghull)
    # plt.show()

    # カードの横幅
    card_img_height = 1600 # 適当な値
    card_img_width = 2400 # 適当な値

    src = np.float32(list(map(lambda x: x[0], approx[:4,...])))
    src = sortPoints(src,img)
    dst = np.float32([[0,0],[0,card_img_width],[card_img_height,card_img_width],[card_img_height,0]])

    projectMatrix = cv2.getPerspectiveTransform(src, dst)

    res = cv2.warpPerspective(img, projectMatrix, (card_img_height, card_img_width))
    #########################################

    if res.size != 0:
            cv2.imwrite(f"out/out{num}.jpg", res)
            # cv2.imwrite(f"out/out_d{i}.jpg", res)
            num = num + 1
    else:
        continue

    # canny = cv2.Canny(res, 100, 200)
    # cv2.imwrite(f"canny{i}.jpg", canny)

