
#-------------------------------------------------------------------------------
# Name:        Object bounding box label tool
# Purpose:     Label object bboxes for ImageNet Detection data
# Author:      Qiushi
# Created:     06/06/2014

#
#-------------------------------------------------------------------------------
from __future__ import division
from tkinter import *
from tkinter import ttk
from os.path import basename
from tkinter import filedialog
from PIL import Image, ImageTk
import os
# import glob
from glob import *
import random

# colors for the bboxes
COLORS = ['red', 'blue', 'yellow', 'pink', 'cyan', 'green', 'black']
# image sizes for the examples
SIZE = 256, 256
# file formats that can be 'read' by PIL
FILETYPES = ['.bmp', '.dib', '.dcx', '.gif', '.im', '.jpg',
             '.jpe', '.jpeg', '.pcd', '.pcx', '.png', '.pbm',
             '.pgm', '.ppm', '.psd', '.tif', '.tiff', '.xbm',
             '.xpm']

class LabelTool():
    def __init__(self, master):
        # set up the main frame
        self.parent = master
        self.parent.title("LabelTool")
        # self.frame = Frame(self.parent)
        # self.frame.pack(fill=BOTH, expand=1)
        self.parent.resizable(width = FALSE, height = FALSE)

        # initialize global state
        self.imageDir = ''
        self.imageList= []
        self.egDir = ''
        self.egList = []
        self.outDir = ''
        self.cur = 0
        self.total = 0
        self.category = 0
        self.imagename = ''
        self.labelfilename = ''
        self.imh = None

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
        header_frame.grid(row=0,column=0,columnspan=3)

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



        # self.frame.columnconfigure(1, weight = 1)
        # self.frame.rowconfigure(4, weight = 1)
    def _create_header_panel(self, parent):
        self.label = Label(parent, text = "Image Dir:")
        self.label.grid(row = 0, column = 0, sticky = E)

        self.curpath = os.path.join(os.getcwd(), 'images')  # current path
        self.dirName = StringVar()  # entry control variable
        self.dirName.set(self.curpath)

        self.entry = Entry(parent,textvariable=self.dirName,width=70)
        self.entry.bind('<Return>', self._load_dir)
        self.entry.grid(row = 0, column = 1, sticky = W+E)
        self.ldBtn = Button(parent, text = "Load", command = self._select_dir)
        self.ldBtn.grid(row = 0, column = 2, sticky = W+E)

    def _create_left_panel(self,parent):
        self.tmpLabel2 = Label(parent, text = "List Images:")
        self.tmpLabel2.pack(side = TOP, pady = 5)

        self.files = Listbox(parent, width=25, height=40)
        vbar = Scrollbar(parent, command=self.files.yview, orient=VERTICAL)
        hbar = Scrollbar(parent, command=self.files.xview, orient=HORIZONTAL)

        self.files.configure(xscrollcommand=hbar.set,yscrollcommand=vbar.set)
        self._load_dir()
        self.files.pack(side=LEFT, fill=Y, expand=Y)
        vbar.pack(side=LEFT, fill=Y, expand=Y)
        hbar.pack(side=BOTTOM, fill=X)

        self.files.bind('<<ListboxSelect>>', self._load_image)
    def _create_middle_panel(self,parent):
        self.mainPanel = Canvas(parent, cursor='tcross',scrollregion=(0, 0, 3000, 2000))

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
        self.parent.bind("a", self.prevImage) # press 'a' to go backforward
        self.parent.bind("d", self.nextImage) # press 'd' to go forward


    def _creat_right_panel(self,parent):
        self.lblCategory = Label(parent, text='Select Category')
        self.lblCategory.grid(row=0, column=0,sticky=W)
        v = IntVar()
        self.rdshipper=Radiobutton(parent , text='SHIPPER', variable=v,value=3)
        self.rdshipper.grid(row=1, column=0,sticky=W,padx=15)

        self.rdconsignee=Radiobutton(parent , text='CONSIGNEE', variable=v,value=2)
        self.rdconsignee.grid(row=2, column=0,sticky=W,padx=15)

        self.rdnotify=Radiobutton(parent , text='NOTIFY', variable=v,value=1,)
        self.rdnotify.grid(row=3, column=0,sticky=W,padx=15)

        self.rdvesel = Radiobutton(parent, text='VESEL', variable=v, value=4, )
        self.rdvesel.grid(row=4, column=0, sticky=W, padx=15)

        self.lb1 = Label(parent, text='Bounding boxes:')
        self.lb1.grid(row=6, column=0,sticky=W)
        self.listbox = Listbox(parent, width=22, height=12)
        self.listbox.grid(row=7, column=0)
        self.btnDel = Button(parent, text='Delete', command=self.delBBox,width=20)
        self.btnDel.grid(row=8, column=0, sticky=W + E + N)
        self.btnClear = Button(parent, text='ClearAll', command=self.clearBBox,width=20)
        self.btnClear.grid(row=9, column=0, sticky=W + E + N)





    def _create_footer_panel(self,parent):
        self.prevBtn = Button(parent, text='<< Prev', width=10, command=self.prevImage)
        self.prevBtn.pack(side=LEFT, padx=5, pady=3)
        self.nextBtn = Button(parent, text='Next >>', width=10, command=self.nextImage)
        self.nextBtn.pack(side=LEFT, padx=5, pady=3)
        self.progLabel = Label(parent, text="Progress:     /    ")
        self.progLabel.pack(side=LEFT, padx=5)
        self.tmpLabel = Label(parent, text="Go to Image No.")
        self.tmpLabel.pack(side=LEFT, padx=5)
        self.idxEntry = Entry(parent, width=5)
        self.idxEntry.pack(side=LEFT)
        self.goBtn = Button(parent, text='Go', command=self.gotoImage)
        self.goBtn.pack(side=LEFT)

        # display mouse position
        self.disp = Label(parent, text='')
        self.disp.pack(side = RIGHT)



    def _select_dir(self):
        dir = filedialog.askdirectory(initialdir=self.dirName.get(),
                                      parent=self.parent,
                                      title='Select a new files image directory',mustexist=True)  # only existing dirs
        print("Dir: ",dir)
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

    def loadDir(self, dbg = False):
        if not dbg:
            s = self.entry.get()
            self.parent.focus()
            self.category = int(s)
        else:
            s = r'D:\workspace\python\labelGUI'
        self.imageDir = os.path.join(r'./Images', '%03d' %(self.category))
        self.imageList = glob(os.path.join(self.imageDir, '*.JPEG'))
        if len(self.imageList) == 0:
            print('No .JPEG images found in the specified dir!')
            return

        # default to the 1st image in the collection
        self.cur = 1
        self.total = len(self.imageList)

         # set up output dir
        self.outDir = os.path.join(r'./Labels', '%03d' %(self.category))
        if not os.path.exists(self.outDir):
            os.mkdir(self.outDir)

        # load example bboxes
        self.egDir = os.path.join(r'./Examples', '%03d' %(self.category))
        if not os.path.exists(self.egDir):
            return
        filelist = glob.glob(os.path.join(self.egDir, '*.JPEG'))
        self.tmp = []
        self.egList = []
        random.shuffle(filelist)
        for (i, f) in enumerate(filelist):
            if i == 3:
                break
            im = Image.open(f)
            r = min(SIZE[0] / im.size[0], SIZE[1] / im.size[1])
            new_size = int(r * im.size[0]), int(r * im.size[1])
            self.tmp.append(im.resize(new_size, Image.ANTIALIAS))
            self.egList.append(ImageTk.PhotoImage(self.tmp[-1]))
            self.egLabels[i].config(image = self.egList[-1], width = SIZE[0], height = SIZE[1])

        self.loadImage()
        print ('%d images loaded from %s' %(self.total, s))
    def _load_image(self, event):
        item = self.files.curselection()
        fn = self.files.get(item)

        imagePath = os.path.join(self.dirName.get(), fn)
        self.inputpath=imagePath
        try:
            im = Image.open(imagePath)
            im = im.resize((1200, 1400), Image.ANTIALIAS)

            if im.mode == '1':
                self.imh = ImageTk.BitmapImage(im)
            else:
                self.imh = ImageTk.PhotoImage(im)
            self.mainPanel.config(width=800, height=750)
            self.mainPanel.create_image(0, 0, image=self.imh, anchor=NW)
            self.progLabel.config(text="%04d/%04d" % (self.cur, self.total))

            # load labels
            self.clearBBox()
            self.imagename = os.path.split(imagePath)[-1].split('.')[0]
            labelname = self.imagename + '.txt'
            self.labelfilename = os.path.join(self.outDir, labelname)
            bbox_cnt = 0
            if os.path.exists(self.labelfilename):
                with open(self.labelfilename) as f:
                    for (i, line) in enumerate(f):
                        if i == 0:
                            bbox_cnt = int(line.strip())
                            continue
                        tmp = [int(t.strip()) for t in line.split()]
                        self.bboxList.append(tuple(tmp))
                        tmpId = self.mainPanel.create_rectangle(tmp[0], tmp[1], \
                                                                tmp[2], tmp[3], \
                                                                width = 2, \
                                                                outline = COLORS[(len(self.bboxList)-1) % len(COLORS)])
                        self.bboxIdList.append(tmpId)
                        self.listbox.insert(END, '(%d, %d) -> (%d, %d)' %(tmp[0], tmp[1], tmp[2], tmp[3]))
                        self.listbox.itemconfig(len(self.bboxIdList) - 1, fg = COLORS[(len(self.bboxIdList) - 1) % len(COLORS)])


        except Exception:
            # mark non-image selections
            self.files.itemconfig(item, background='red',
                                  selectbackground='red')

    def loadImage(self):
        # load image
        imagepath = self.imageList[self.cur - 1]
        self.img = Image.open(imagepath)
        self.tkimg = ImageTk.PhotoImage(self.img)
        self.mainPanel.config(width = max(self.tkimg.width(), 400), height = max(self.tkimg.height(), 400))
        self.mainPanel.create_image(0, 0, image = self.tkimg, anchor=NW)
        self.progLabel.config(text = "%04d/%04d" %(self.cur, self.total))

        # load labels
        self.clearBBox()
        self.imagename = os.path.split(imagepath)[-1].split('.')[0]
        labelname = self.imagename + '.txt'
        self.labelfilename = os.path.join(self.outDir, labelname)
        bbox_cnt = 0
        if os.path.exists(self.labelfilename):
            with open(self.labelfilename) as f:
                for (i, line) in enumerate(f):
                    if i == 0:
                        bbox_cnt = int(line.strip())
                        continue
                    tmp = [int(t.strip()) for t in line.split()]
                    self.bboxList.append(tuple(tmp))
                    tmpId = self.mainPanel.create_rectangle(tmp[0], tmp[1], \
                                                            tmp[2], tmp[3], \
                                                            width = 2, \
                                                            outline = COLORS[(len(self.bboxList)-1) % len(COLORS)])
                    self.bboxIdList.append(tmpId)
                    self.listbox.insert(END, '(%d, %d) -> (%d, %d)' %(tmp[0], tmp[1], tmp[2], tmp[3]))
                    self.listbox.itemconfig(len(self.bboxIdList) - 1, fg = COLORS[(len(self.bboxIdList) - 1) % len(COLORS)])

    def saveImage(self):
        with open(self.labelfilename, 'w') as f:
            f.write('%d\n' %len(self.bboxList))
            for bbox in self.bboxList:
                f.write(' '.join(map(str, bbox)) + '\n')
        print ('Image No. %d saved' %(self.cur))


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
        self.STATE['click'] = 1 - self.STATE['click']


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

    def prevImage(self, event = None):
        self.saveImage()
        if self.cur > 1:
            self.cur -= 1
            self.loadImage()

    def nextImage(self, event = None):
        self.saveImage()
        if self.cur < self.total:
            self.cur += 1
            self.loadImage()

    def gotoImage(self):
        idx = int(self.idxEntry.get())
        if 1 <= idx and idx <= self.total:
            self.saveImage()
            self.cur = idx
            self.loadImage()


if __name__ == '__main__':
    root = Tk()
    tool = LabelTool(root)
    root.resizable(width =  True, height = True)
    root.mainloop()


