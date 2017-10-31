import csv
import os
import json
from tkinter import *
# from sklearn.feature_extraction.text import CountVectorizer
# from sklearn.metrics.pairwise import cosine_similarity
import subprocess
import numpy as np
import cv2
from glob import *
import configparser

# file formats that can be 'read' by PIL
FILETYPES = ['.bmp', '.dib', '.dcx', '.gif', '.im', '.jpg',
             '.jpe', '.jpeg', '.pcd', '.pcx', '.png', '.pbm',
             '.pgm', '.ppm', '.psd', '.tif', '.tiff', '.xbm',
             '.xpm']

class Util:
    # @staticmethod
    # def measure_similarity(input, target):
    #     sentences = [input, target]
    #     cv = CountVectorizer()
    #     cv_fit = cv.fit_transform(sentences)
    #     w2v_arr = cv_fit.toarray()
    #     w1 = w2v_arr[0].reshape(1, -1)
    #     w2 = w2v_arr[1].reshape(1, -1)
    #     similarity = cosine_similarity(w1, w2)
    #     return similarity[0][0]
    #
    # @staticmethod
    # def getfield_from_db(filename, bookingnum, fieldname):
    #     data = {}
    #     try:
    #         with open(filename) as si_data:
    #             data = json.load(si_data)
    #             dic = json.loads(data[bookingnum])
    #             result=dic[fieldname]
    #     except IOError:
    #         print("Error: File does not appear to exist.")
    #         result=""
    #     except KeyError:
    #         print("Error: Key does not appear to exist.")
    #         result=""
    #     except Exception as e:
    #         print("Error: ", e)
    #         result = ""
    #     else:
    #         return result

    @staticmethod
    def filter_matix_by_index(mtx, lstIndx, noColum):
        finalCenterMtx = np.zeros((len(lstIndx), noColum))
        for idx, val in enumerate(lstIndx):
            finalCenterMtx[idx, :] = mtx[val, :]
        return finalCenterMtx

    @staticmethod
    def find(arg, func):
        return [i for (i, val) in enumerate(arg) if func(val)]

    @staticmethod
    def mode(arr):
        u, indices = np.unique(arr, return_inverse=True)
        return u[np.argmax(np.bincount(indices))]

    @staticmethod
    def levenshtein(s1, s2):
        if len(s1) > len(s2):
            s1, s2 = s2, s1
        distances = range(len(s1) + 1)
        for index2, char2 in enumerate(s2):
            newdistances = [index2 + 1]
            for index1, char1 in enumerate(s1):
                if char1 == char2:
                    newdistances.append(distances[index1])
                else:
                    newdistances.append(1 + min((distances[index1],
                                                 distances[index1 + 1],
                                                 newdistances[-1])))
            distances = newdistances
        return distances[-1]

    @staticmethod
    def getlcs(a, b):
        result = ""
        try:
            lengths = [[0 for j in range(len(b) + 1)] for i in range(len(a) + 1)]
            # row 0 and column 0 are initialized to 0 already
            for i, x in enumerate(a):
                for j, y in enumerate(b):
                    if x == y:
                        lengths[i + 1][j + 1] = lengths[i][j] + 1
                    else:
                        lengths[i + 1][j + 1] = max(lengths[i + 1][j], lengths[i][j + 1])
            # read the substring out from the matrix

            x, y = len(a), len(b)
            while x != 0 and y != 0:
                if lengths[x][y] == lengths[x - 1][y]:
                    x -= 1
                elif lengths[x][y] == lengths[x][y - 1]:
                    y -= 1
                else:
                    assert a[x - 1] == b[y - 1]
                    result = a[x - 1] + result
                    x -= 1
                    y -= 1
        except Exception as e:
            pass
        return result

    @staticmethod
    def findlocation_ofword_v1(word, strsource, continues=-1):
        result = (0, 0, 0, 0, -1)
        for i, item in enumerate(strsource):
            if (word in item['Text']) & (i > continues):
                result = (item['Left'], item['Top'], item['Right'], item['Bottom'], i)
                # print("Word: ",word)
                break
        return result

    @staticmethod
    def findlocation_ofword_v2(word, strSource, continues=-1):
        result = (0, 0, 0, 0, -1)
        for i, item in enumerate(strSource):
            try:
                measure = Util.measure_similarity(word,item['Text'])
            except:
                pass
            # print("Measure: ",measure)
            if (measure > 0.6) & (i > continues):
                result = (item['Left'], item['Top'], item['Right'], item['Bottom'], i)
                # print("Word: ", word)
                break
        return result

    @staticmethod
    def create_img(left, top, right, bottom, width, height, filename, outfilepath):
        imgdata = np.zeros((height, width), dtype=np.uint8)
        imgdata[top:bottom, left:right] = 1
        cv2.imwrite(outfilepath + filename, imgdata)

    @staticmethod
    def ocr(input_file,outputocrtextpath):
        try:
            from subprocess import DEVNULL  # py3k
        except ImportError:
            DEVNULL = open(os.devnull, 'wb')
        outputfilename = os.path.splitext(os.path.basename(input_file))[0]
        outputfile = os.path.join(outputocrtextpath,outputfilename)
        if not os.path.exists(outputocrtextpath):
            os.makedirs(outputocrtextpath)
        if not os.path.isfile(outputfile + ".tsv"):
            im = cv2.imread(input_file)
            subprocess.run(
                "convert -units PixelsPerInch " + input_file + " -density 300 " + input_file, shell=True,
                stdout=subprocess.PIPE,
                universal_newlines=True)

            subprocess.run(
                "tesseract --tessdata-dir /usr/local/share " + input_file + " " + outputfile + " -l eng -psm 7 tsv", shell=True,
                stdout=DEVNULL, universal_newlines=True)

        rslt = []
        with open(outputfile+".tsv") as fd:
            rd = csv.reader(fd, delimiter="\t", quotechar='"')
            for row in rd:
                rslt.append(row)
        if rslt:
            rslt.pop(0)

        words = []
        for item in rslt:
            arr = item
            arr[11] = arr[11].strip()
            E = {"left": int(arr[6]), "top": int(arr[7]), "right": int(arr[6]) + int(arr[8]),
                 "bottom": int(arr[7]) + int(arr[9]), "width": int(arr[8]), "height": int(arr[9]),
                 "conf": arr[10], "text": arr[11].upper(), "line": int(arr[4]), "block": int(arr[2])}
            if (arr[11] != ""):
                print("Text: {} - Left: {} - Top: {}".format(arr[11].upper(), arr[6], arr[7]))
                words.append(E)

        return words

    @staticmethod
    def getlist_shipper_fromdic():
        shipperdic = ["SHIPPER","SHIPPE","SHIP"]
        return shipperdic

    @staticmethod
    def getlist_notify_fromdic():
        notifydic = ["NOTIFY","NOTIFY","NOTIFY PARTY"]
        return notifydic

    @staticmethod
    def getlist_consignee_fromdic(inputfile):
        consigneeDic = []
        with open(inputfile, "r") as fd:
            for line in fd:
                words = line.split("\"")
                consigneeDic.append(words[1])
        # print("Consignee Dictionary: ", consigneeDic)
        return consigneeDic

    @staticmethod
    def getbookingnum(imgfilename):
        if(imgfilename!=""):
            imgfile=imgfilename.split("_")
        return imgfile[0]

    @staticmethod
    def isbookingnum(bookingnum):
        isMatch = re.match(r"[A-Z]{3}[\d]{9}\Z", bookingnum)
        if isMatch:
            return TRUE
        else:
            return FALSE

    @staticmethod
    def getimglist(dirname):
        dn = os.path.join(dirname, '*')
        imglist=[]
        for f in iglob(dn):
            if os.path.splitext(f)[1] in FILETYPES:
                imglist.append(f)
        return imglist

    @staticmethod
    def chunks(l, n):
        """Yield successive n-sized chunks from l."""
        for i in range(0, len(l), n):
            yield l[i:i + n]

    @staticmethod
    def readconfig(cfg_files):
        if (cfg_files != None):
            config = configparser.RawConfigParser()

            # merges all files into a single config
            for i, cfg_file in enumerate(cfg_files):
                if (os.path.exists(cfg_file)):
                    config.read(cfg_file)
            return config

    @staticmethod
    def isFileExist(file,dir):
        try:
            if any(x.startswith(file) for x in os.listdir(dir)):
                return True
        except Exception as e:
            print("error({0}): {1}".format(e.errno, e.strerror))
        return False

    # @staticmethod
    # def extract_text(image):
    #     with PyTessBaseAPI() as api:
    #         api.SetImage(image)
    #         boxes = api.GetComponentImages(RIL.TEXTLINE, True)
    #         print('Found {} textline image components.'.format(len(boxes)))
    #         for i, (im, box, _, _) in enumerate(boxes):
    #             api.SetRectangle(box['x'], box['y'], box['w'], box['h'])
    #             ocrResult = api.GetUTF8Text()
    #             conf = api.MeanTextConf()
    #             print("Box[{0}]: x={x}, y={y}, w={w}, h={h}, ""confidence: {1}, text: {2}".format(i, conf, ocrResult,
    #                                                                                               **box))

    # @staticmethod
    # def delete_all_file(dirPath):
    #     fileList = os.listdir(dirPath)
    #     print("File: ", fileList)
    #     for fileName in fileList:
    #         os.remove(dirPath + "/" + fileName)

# if __name__ == "__main__":
#     Util().ocr("/Users/phuonglv/Data/cnndata/images/SI/imgpdf/ALG500893300_SI0000076454.png")
