import cv2
import numpy as np
import imutils
import sys
import math
import urllib


class CustomUserAgentURLopener(urllib.FancyURLopener):
    version = 'Mozilla/5.0'


class cv2utils:
    # From https://stackoverflow.com/questions/19363293/whats-the-fastest-way-to-increase-color-image-contrast-with-opencv-in-python-c/44569460#44569460
    @staticmethod
    def increaseContrast(image):
        clahe = cv2.createCLAHE(clipLimit=3., tileGridSize=(8, 8))
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)  # convert from BGR to LAB color space
        l, a, b = cv2.split(lab)  # split on 3 different channels
        l2 = clahe.apply(l)  # apply CLAHE to the L-channel
        lab = cv2.merge((l2, a, b))  # merge channels
        return cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)  # convert from LAB to BGR

    # From https://www.pyimagesearch.com/2015/03/02/convert-url-to-image-with-pyth
    @staticmethod
    def urlToImage(url):
        uo = CustomUserAgentURLopener()
        resp = uo.open(url)
        image = np.asarray(bytearray(resp.read()), dtype="uint8")
        image = cv2.imdecode(image, cv2.IMREAD_COLOR)
        return image

    # From https://www.pyimagesearch.com/2015/01/26/multi-scale-template-matching-using-python-opencv/
    @staticmethod
    def scalingMatch(template, image, visualize=False):
        # convert the template to grayscale and detect edges
        template = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
        template = cv2.Canny(template, 50, 200)
        (tH, tW) = template.shape[:2]

        # convert the image to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        found = None
        # track the matched region
        # loop over the scales of the image
        for scale in np.linspace(0.2, 1.0, 20)[::-1]:
            # resize the image according to the scale, and keep track
            # of the ratio of the resizing
            resized = imutils.resize(gray, width=int(gray.shape[1] * scale))
            r = gray.shape[1] / float(resized.shape[1])

            # if the resized image is smaller than the template, then break
            if resized.shape[0] < tH or resized.shape[1] < tW:
                break

            # detect edges in the resized, grayscale image and apply template
            # matching to find the template in the image
            edged = cv2.Canny(resized, 50, 200)
            result = cv2.matchTemplate(edged, template, cv2.TM_CCOEFF)
            (_, maxVal, _, maxLoc) = cv2.minMaxLoc(result)

            # check to see if the iteration should be visualized
            if visualize:
                # draw a bounding box around the detected region
                clone = np.dstack([edged, edged, edged])
                cv2.rectangle(clone, (maxLoc[0], maxLoc[1]), (maxLoc[0] + tW, maxLoc[1] + tH), (0, 0, 255), 2)
                cv2.imshow("Visualize", clone)
                cv2.waitKey(0)

            # if we have found a new maximum correlation value, then update
            # the bookkeeping variable
            if found is None or maxVal > found[0]:
                found = (maxVal, maxLoc, r)

        (_, maxLoc, r) = found
        (startX, startY) = (int(maxLoc[0] * r), int(maxLoc[1] * r))
        (endX, endY) = (int((maxLoc[0] + tW) * r), int((maxLoc[1] + tH) * r))

        return ((startX, startY), (endX, endY))
