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

# def rotate_fit(image, angle):
#     h, w = image.shape[:2]
#     # 回転後のサイズ
#     radian = np.radians(angle)
#     sine = np.abs(np.sin(radian))
#     cosine = np.abs(np.cos(radian))
#     tri_mat = np.array([[cosine, sine],[sine, cosine]], np.float32)
#     old_size = np.array([w,h], np.float32)
#     new_size = np.ravel(np.dot(tri_mat, old_size.reshape(-1,1)))
#     # 回転アフィン
#     affine = cv2.getRotationMatrix2D((w/2.0, h/2.0), angle, 1.0)
#     # 平行移動
#     affine[:2,2] += (new_size-old_size)/2.0
#     # リサイズ
#     affine[:2,:] *= (old_size / new_size).reshape(-1,1)
#     return affine, h, w

def crop_minAreaRect(img, rect):

    # rotate img
    angle = rect[2]
    rows,cols = img.shape[0], img.shape[1]
    longs = max([rows,cols])
    M = cv2.getRotationMatrix2D((cols/2,rows/2),angle,1)
    # M, cols,rows = rotate_fit(img, angle)
    
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

img = cv2.imread('image0 (2).jpg')
img = myPad(img)
# Prepocess
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
flag, thresh = cv2.threshold(gray, luminance_threshold(gray), 255, cv2.THRESH_BINARY)
cv2.imwrite(f"deb.jpg", thresh)
# cv2.imshow("gray",thresh)
# cv2.waitKey(0)

# Find contours
contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
contours = sorted(contours, key=cv2.contourArea, reverse=True) 
# contours = sorted(contours, key=cv2.arcLength, reverse=True) 

# Select long perimeters only
# perimeters = [cv2.arcLength(contours[i],True) for i in range(len(contours))]
perimeters = [cv2.contourArea(contours[i]) for i in range(len(contours))]
# cv2.imshow("perim",perimeters[0])
# cv2.waitKey(0)
listindex=[i for i in range(len(perimeters)) if perimeters[i]>perimeters[0]/2]
numcards=len(listindex)

# Show image
imgcont = img.copy()
# [cv2.drawContours(imgcont, [contours[i]], 0, (0,255,0), 5) for i in listindex]
# plt.imshow(imgcont)
# plt.show()
# card_number = -1 #just so happened that this is the worst case

for i,ind in enumerate(listindex):
    # stencil = np.zeros(img.shape).astype(img.dtype)
    # cv2.drawContours(stencil, [contours[listindex[i]]], 0, (255, 255, 255), cv2.FILLED)
    # (y,x,z) = np.where(stencil == 255)
    # (topy, topx) = (np.min(y), np.min(x))
    # (bottomy, bottomx) = (np.max(y), np.max(x))
    # res = img[topy:bottomy+1, topx:bottomx+1]
    # cv2.imshow("test", res)
    # cv2.waitKey(0)
    # cv2.drawContours(imgcont, [contours[ind]], 0, (0,255,0), 5)
    # plt.imshow(imgcont)
    # plt.show()
    rect = cv2.minAreaRect(contours[ind])
    box = cv2.boxPoints(rect)
    box = np.int0(box)
    # img = cv2.drawContours(img,[box],0,(0,0,255),10)
    # plt.imshow(img)
    # plt.show()
    print(type(rect))
    res = crop_minAreaRect(img, rect)
    
    if res.size != 0:
        cv2.imwrite(f"out/out{i}.jpg", res)
    else:
        continue

    # break
    # canny = cv2.Canny(res, 100, 200)
    # cv2.imwrite(f"canny{i}.jpg", canny)