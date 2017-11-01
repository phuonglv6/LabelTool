#-------------------------------------------------------------------------------
# Name:        Object bounding box label tool
# Purpose:     Label object bboxes for ImageNet Detection data
# Author:      phuongle@dounet.com
# Created:     27/10/2017
#
#-------------------------------------------------------------------------------
from __future__ import division
from os.path import basename
from tkinter import *
from tkinter import filedialog
from PIL import Image, ImageTk
import random
from Utility.utilities import Util,FILETYPES
from glob import *
import os
import cv2

# colors for the bboxes
COLORS = ['red', 'blue', 'yellow', 'pink', 'cyan', 'green', 'black']

class LabelTool:
    # Input and output path images
    input_img_path          = ""
    output_tesseract_result = ""
    output_label_files      = ""

    def __init__(self, master):
        # set up the main frame
        self.parent = master
        self.parent.title("LabelTool")
        self.parent.resizable(width = FALSE, height = FALSE)

        # initialize global state
        self.category = 0
        self.imagename = ''
        self.labelfilename = ''
        self.imh = None
        self.imagePath=""

        # initialize mouse state
        self.STATE = {}
        self.STATE['click'] = 0
        self.STATE['x'], self.STATE['y'] = 0, 0

        # reference to bbox
        self.bboxIdList = []
        self.bboxId = None
        self.bboxList = []
        self.hl = None
        self.vl = None

        # ----------------- GUI stuff ---------------------

        header_frame = Frame(self.parent,width=1200)
        header_frame.pack(fill=None, expand=False)
        header_frame.grid(row=0,column=0,columnspan=2)

        left_frame = Frame(self.parent,padx=20,width=100)
        left_frame.pack(fill=None, expand=False)
        left_frame.grid(row=1,column=0,sticky=W)

        middle_frame = Frame(self.parent,width=1000)
        middle_frame.pack(fill=None, expand=False)
        middle_frame.grid(row=1, column=1)

        right_frame = Frame(self.parent,padx=20,width=100)
        right_frame.pack(fill=None, expand=False)
        right_frame.grid(row=1, column=2,sticky=E)

        footer_frame = Frame(self.parent,width=1200,padx=20)
        footer_frame.pack(fill=None, expand=False)
        footer_frame.grid(row=2, column=0,columnspan=3)

        # dir entry & load
        self._create_header_panel(header_frame)

        #List Images Panel
        self._create_left_panel(left_frame)

        # main panel for labeling
        self._create_middle_panel(middle_frame)

        # showing bbox info & delete bbox
        self._creat_right_panel(right_frame)

        # control panel for image navigation
        self._create_footer_panel(footer_frame)


    def _create_header_panel(self, parent):
        im = Image.open("./Images/dou_logo.gif")
        im = im.resize((250, 40), Image.ANTIALIAS)

        if im.mode == '1':
            self.imlogo = ImageTk.BitmapImage(im)
        else:
            self.imlogo = ImageTk.PhotoImage(im)
        self.logo = Label(parent, image=self.imlogo,anchor="w")
        self.logo.grid(row = 0, column = 0,padx=15)

        self.label = Label(parent, text = "Image Dir:")
        self.label.grid(row = 0, column = 1, sticky = W)

        self.curpath = LabelTool.input_img_path  # current path
        self.dirName = StringVar()  # entry control variable
        self.dirName.set(self.curpath)

        self.entry = Entry(parent,textvariable=self.dirName,width=70)
        self.entry.bind('<Return>', self._load_dir)
        self.entry.grid(row = 0, column = 2, sticky = W+E)
        self.ldBtn = Button(parent, text = "Load", command = self._select_dir)
        self.ldBtn.grid(row = 0, column = 3, sticky = W+E)

    def _create_left_panel(self,parent):
        self.tmpLabel2 = Label(parent, text = "List Images")
        self.tmpLabel2.pack(side = TOP, pady = 5)
        self.files = Listbox(parent, width=25, height=40)
        vbar = Scrollbar(parent, command=self.files.yview, orient=VERTICAL)
        # hbar = Scrollbar(parent, command=self.files.xview, orient=HORIZONTAL)

        self.files.configure(yscrollcommand=vbar.set)
        self._load_dir()
        self.files.pack(side=LEFT, fill=Y, expand=Y)
        vbar.pack(side=LEFT, fill=Y, expand=Y)
        # hbar.pack(side=BOTTOM, fill=X)

        self.files.bind('<<ListboxSelect>>', self._load_image)
    def _create_middle_panel(self,parent):
        self.mainPanel = Canvas(parent, cursor='tcross',scrollregion=(0, 0, 1200, 1400))

        hbar = Scrollbar(parent, orient=HORIZONTAL)
        hbar.pack(side=BOTTOM, fill=X)
        hbar.config(command=self.mainPanel.xview)
        vbar = Scrollbar(parent, orient=VERTICAL)
        vbar.pack(side=RIGHT, fill=Y)
        vbar.config(command=self.mainPanel.yview)
        self.mainPanel.config(width=800, height=750)
        self.mainPanel.config(xscrollcommand=hbar.set, yscrollcommand=vbar.set)

        self.mainPanel.bind("<Button-1>", self.mouseClick)
        self.mainPanel.bind("<Motion>", self.mouseMove)

        self.mainPanel.grid(row = 0, column = 0,  sticky = W+N)
        self.mainPanel.pack(side=RIGHT, expand=True, fill=BOTH)


        parent.update()

        # parent.update_idletasks()
        self.mainPanel.config(scrollregion=self.mainPanel.bbox("all"))

        self.parent.bind("<Escape>", self.cancelBBox)  # press <Espace> to cancel current bbox
        self.parent.bind("s", self.cancelBBox)


    def _creat_right_panel(self,parent):
        self.lblCategory = Label(parent, text='Select Category')
        self.lblCategory.grid(row=0, column=0,sticky=W)
        self.v = IntVar()

        self.rdheader=Radiobutton(parent , text='HEADER', variable=self.v,value=0,command=self.cat_selected)
        self.rdheader.grid(row=1, column=0,sticky=W,padx=15)

        self.rdshipper=Radiobutton(parent , text='SHIPPER', variable=self.v,value=1,command=self.cat_selected)
        self.rdshipper.grid(row=2, column=0,sticky=W,padx=15)

        self.rdconsignee=Radiobutton(parent , text='CONSIGNEE', variable=self.v,value=2,command=self.cat_selected)
        self.rdconsignee.grid(row=3, column=0,sticky=W,padx=15)

        self.rdnotify=Radiobutton(parent , text='NOTIFY', variable=self.v,value=3,command=self.cat_selected)
        self.rdnotify.grid(row=4, column=0,sticky=W,padx=15)

        self.rdothers = Radiobutton(parent, text='OTHERS', variable=self.v, value=4,command=self.cat_selected )
        self.rdothers.grid(row=5, column=0, sticky=W, padx=15)

        self.v.set(0)
        self.lb1 = Label(parent, text='Bounding boxes:')
        self.lb1.grid(row=6, column=0,sticky=W)
        self.listbox = Listbox(parent, width=22, height=12)
        self.listbox.grid(row=7, column=0)
        self.btnDel = Button(parent, text='Delete', command=self.delBBox,width=20)
        self.btnDel.grid(row=8, column=0, sticky=W + E + N)
        self.btnClear = Button(parent, text='ClearAll', command=self.clearBBox,width=20)
        self.btnClear.grid(row=9, column=0, sticky=W + E + N)
        self.btnClose = Button(parent,text='Close', command=self.parent.destroy)
        self.btnClose.grid(row=10, column=0, sticky=W + E + N)

    def cat_selected(self):
        self.category=self.v.get()



    def _create_footer_panel(self,parent):
        # display mouse position
        self.disp = Label(parent, text='')
        self.disp.pack(side = RIGHT)



    def _select_dir(self):
        dir = filedialog.askdirectory(initialdir=self.dirName.get(),
                                      parent=self.parent,
                                      title='Select a new files image directory',mustexist=True)  # only existing dirs
        if dir:
            self.dirName.set(dir)
            self._load_dir()

    def _load_dir(self, *args):
        dn = os.path.join(self.dirName.get(), '*')

        self.files.delete(0, END)

        # populate files list with filenames from
        # selected directory
        for f in iglob(dn):
            if os.path.splitext(f)[1] in FILETYPES:
                self.files.insert(END, basename(f))

        # prevent <Return> event from propagating to
        # windows higher up in the hierarchy
        return 'break'

    def _load_image(self, event):
        item = self.files.curselection()
        fn = self.files.get(item)

        self.imagePath = os.path.join(self.dirName.get(), fn)
        self.inputpath=self.imagePath

        try:
            im = Image.open(self.imagePath)
            im = im.resize((1200, 1400), Image.ANTIALIAS)

            if im.mode == '1':
                self.imh = ImageTk.BitmapImage(im)
            else:
                self.imh = ImageTk.PhotoImage(im)
            self.mainPanel.config(width=800, height=750)
            self.mainPanel.create_image(0, 0, image=self.imh, anchor=NW)

            # load labels
            self.clearBBox()
            self.imagename = os.path.split(self.imagePath)[-1].split('.')[0]
            labelname = self.imagename + '.txt'
            self.labelfilename = os.path.join(LabelTool.output_label_files, labelname)
            if not os.path.exists(LabelTool.output_label_files):
                os.mkdir(LabelTool.output_label_files)
            if not os.path.exists(LabelTool.output_tesseract_result):
                os.makedirs(LabelTool.output_tesseract_result)

            if not os.path.exists(self.labelfilename):
                with open(self.labelfilename, 'w') as f:
                    f.write(os.path.split(self.imagePath)[-1]+"\r\n")
                    f.write("{:^6} {:^6} {:^6}\r\n".format("OX", "OY", "Label"))

        except Exception as e:
            # mark non-image selections
            # print("I/O error({0}): {1}".format(e.errno, e.strerror))
            self.files.itemconfig(item, background='red',
                                  selectbackground='red')

    def mouseClick(self, event):
        if self.STATE['click'] == 0:
            self.STATE['x'], self.STATE['y'] = self.mainPanel.canvasx(event.x), self.mainPanel.canvasy(event.y)
        else:
            x1, x2 = min(self.STATE['x'], self.mainPanel.canvasx(event.x)), max(self.STATE['x'], self.mainPanel.canvasx(event.x))
            y1, y2 = min(self.STATE['y'], self.mainPanel.canvasy(event.y)), max(self.STATE['y'], self.mainPanel.canvasy(event.y))

            self.bboxList.append((x1, y1, x2, y2))
            self.bboxIdList.append(self.bboxId)
            self.bboxId = None
            self.listbox.insert(END, '(%d, %d) -> (%d, %d)' %(x1, y1, x2, y2))
            self.listbox.itemconfig(len(self.bboxIdList) - 1, fg = COLORS[(len(self.bboxIdList) - 1) % len(COLORS)])
            im=cv2.imread(self.imagePath)
            w=im.shape[1]
            h=im.shape[0]
            ratew=w/1200
            rateh=h/1400
            crop_img_temp=im[int(y1*rateh):int((y1+(y2-y1))*rateh),int(x1*ratew):int((x1+(x2-x1))*ratew)]
            imgtemp_path = os.path.join(LabelTool.output_tesseract_result,self.imagename+"_"+str(random.randint(1,1000))+".png")

            if not os.path.exists(LabelTool.output_label_files):
                os.mkdir(LabelTool.output_label_files)
            if not os.path.exists(LabelTool.output_tesseract_result):
                os.makedirs(LabelTool.output_tesseract_result)

            cv2.imwrite(imgtemp_path, crop_img_temp)
            ocr_result=Util.ocr(imgtemp_path,LabelTool.output_tesseract_result)
            print("ocr: ",ocr_result)
            if not ocr_result:
                print("The result of ocr is empty")
            else:
                self.create_label_file(ocr_result,self.category)

        self.STATE['click'] = 1 - self.STATE['click']

    def create_label_file(self,lstpos,category):
        if os.path.exists(self.labelfilename):
            with open(self.labelfilename, 'a') as f:
                for line in lstpos:
                    f.write("{:^6} {:^6} {:^6}\r\n".format(int(line['left']+line['width']/2), int(line['top']+line['height']/2), category))
        else:
            with open(self.labelfilename, 'w') as f:
                f.write(os.path.split(self.imagePath)[-1] + "\r\n")
                f.write("{:^6} {:^6} {:^6}\r\n".format("OX","OY","Label"))

    def mouseMove(self, event):
        self.disp.config(text='x: %d, y: %d' % (self.mainPanel.canvasx(event.x), self.mainPanel.canvasy(event.y)))
        if self.imh:
            if self.hl:
                self.mainPanel.delete(self.hl)
            self.hl = self.mainPanel.create_line(0, self.mainPanel.canvasy(event.y), self.imh.width(), self.mainPanel.canvasy(event.y), width=1)
            if self.vl:
                self.mainPanel.delete(self.vl)
            self.vl = self.mainPanel.create_line(self.mainPanel.canvasx(event.x), 0, self.mainPanel.canvasx(event.x), self.imh.height(), width=1)
        if 1 == self.STATE['click']:
            if self.bboxId:
                self.mainPanel.delete(self.bboxId)
            self.bboxId = self.mainPanel.create_rectangle(self.STATE['x'], self.STATE['y'], \
                                                          self.mainPanel.canvasx(event.x), self.mainPanel.canvasy(event.y), \
                                                          width=2, \
                                                          outline=COLORS[len(self.bboxList) % len(COLORS)])

    def cancelBBox(self, event):
        if 1 == self.STATE['click']:
            if self.bboxId:
                self.mainPanel.delete(self.bboxId)
                self.bboxId = None
                self.STATE['click'] = 0

    def delBBox(self):
        sel = self.listbox.curselection()
        if len(sel) != 1 :
            return
        idx = int(sel[0])
        self.mainPanel.delete(self.bboxIdList[idx])
        self.bboxIdList.pop(idx)
        self.bboxList.pop(idx)
        self.listbox.delete(idx)

    def clearBBox(self):
        for idx in range(len(self.bboxIdList)):
            self.mainPanel.delete(self.bboxIdList[idx])
        self.listbox.delete(0, len(self.bboxList))
        self.bboxIdList = []
        self.bboxList = []

    @staticmethod
    def getImgDemensionFiles(imgPathFiles):
        dn=os.path.join(imgPathFiles, '*')
        count=0
        for f in iglob(dn):
            count+=1
            im = cv2.imread(f)
            w = im.shape[1]
            h = im.shape[0]
            filename=os.path.split(f)[1]
            demensionfilename=os.path.join(imgPathFiles,"demension.txt")
            if os.path.exists(demensionfilename):
                with open(demensionfilename, 'a') as f:
                        f.write("{:^4} {:^30} {:^6} {:^6}\r\n".format(count,filename,w,h))
            else:
                with open(demensionfilename, 'w') as f:
                    f.write("{:^4} {:^30} {:^6} {:^6}\r\n".format("No", "FileName", "Width","Height"))
    @staticmethod
    def testLabelTool(imgPathFile,labelFile):
        img = cv2.imread(imgPathFile)
        with open(labelFile, 'r') as f:
            i=0
            for line in f.readlines():
                i+=1
                if(i>2):
                    results = line.split(" ")
                    results = list(filter(None, results))
                    x=int(results[0])
                    y=int(results[1])
                    cv2.circle(img, (x,y), 15, (0,0,255),-1)
        # cv2.imshow('image', img)
        cv2.imwrite("/Users/phuonglv/Desktop/AAR402402400_SI0000009835.png",img)
        # cv2.waitKey(0)

if __name__ == '__main__':
    # root = Tk()
    # tool = LabelTool(root)
    # root.resizable(width=True, height=True)

    cfg_local_path = os.path.join("Config", "config_local.properties")
    cfg_global_path = os.path.join("Config", "config_global.properties")
    config = Util.readconfig([cfg_local_path, cfg_global_path])
    if (config == None):
        print("Config files is require")
        sys.exit(1)
    else:
        # get the current branch (from local.properties)
        env = config.get('branch', 'env')

        # proceed to point everything at the 'branched' resources
        LabelTool.input_img_path = config.get(env + '.path', 'input_img_path')
        LabelTool.output_tesseract_result = config.get(env + '.path', 'output_tesseract_result')
        LabelTool.output_label_files = config.get(env + '.path', 'output_label_files')
        # LabelTool.getImgDemensionFiles(LabelTool.input_img_path)
        LabelTool.testLabelTool("/Users/phuonglv/Desktop/Input_Images/Group4/AAR501411400_SI0000271579.png",
                                "/Users/phuonglv/Desktop/Input_Images/output_label_files/AAR501411400_SI0000271579.txt")
    # root.mainloop()
