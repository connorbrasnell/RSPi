# import the necessary packages
from __future__ import print_function
from PIL import Image
from PIL import ImageTk
from PIL import ImageDraw
from PIL import ImageFont
import tkinter as tki
from tkinter import StringVar
import threading
import datetime
import imutils
import cv2
import os
import pytesseract
import re
from imutils.video import VideoStream
import time
import requests
import json

class StockScanner:
	def __init__(self, vs):
		# store the video stream object and output path, then initialize
		# the most recently read frame, thread for reading frames, and
		# the thread stop event
		self.vs = vs
		self.frame = None
		self.thread = None
		self.stopEvent = None
		
		self.menuScreen = True
		self.captureScreen = False
		self.infoScreen = False
		
		self.initialSet = True
		
		self.pressTime = datetime.datetime.now()
		
		self.drawTryAgain = False

		# initialize the root window and image panel
		self.root = tki.Tk()
		self.root.geometry('{}x{}'.format(800,410))
		self.root.configure(background="white")
		self.root.resizable(width=False, height=False)
		self.panel = None
		
		self.tryAgainFont = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',18)
		
		self.nameText = tki.StringVar()
		self.nameText.set("Raspberry Pi 3 Model B SBC")
		
		self.codeText = tki.StringVar()
		self.codeText.set("896-8660")
		
		self.priceText = tki.StringVar()
		self.priceText.set("\n£29.99")
		
		self.availabilityText = StringVar()
		self.availabilityText.set("\nAvailability: 17721 FREE next working day delivery")
		
		self.startLbl = tki.Label(self.root,text = 'Stock \nScanner',bg="white",fg='#482D60',font='"DejaVu Sans" 64 bold')
		self.startLbl.pack(padx=10,pady=10)
		
		self.startBtn = tki.Button(self.root, text="START", width = 15, height= 5, bg="red", fg="white", font='"DejaVu Sans" 16 bold', command=self.startScanner)
		self.startBtn.pack(padx=10,pady=10)
		
		#self.nameLbl = tki.Label(self.root,textvariable=self.nameText,bg="white",fg='#482D60',font='"DejaVu Sans" 20 bold')
		self.nameLbl = tki.Text(self.root,wrap='word',height='3',bd="0",selectborderwidth="0",borderwidth="0",highlightthickness="0",bg="white",fg='#482D60',font='"DejaVu Sans" 20 bold')
		self.nameLbl.pack(padx=10,pady=10)
		self.nameLbl.tag_configure("center", justify='center')
		
		self.codeLbl = tki.Label(self.root,textvariable=self.codeText,bg="white",fg='#482D60',font='"DejaVu Sans" 12')
		self.codeLbl.pack(padx=10,pady=10)
		
		self.priceLbl = tki.Label(self.root,textvariable=self.priceText,bg="white",fg='#482D60',font='"DejaVu Sans" 14')
		self.priceLbl.pack(padx=10,pady=10)
		
		self.availabilityLbl = tki.Label(self.root,textvariable=self.availabilityText,bg="white",fg='#482D60',font='"DejaVu Sans" 14')
		self.availabilityLbl.pack(padx=10,pady=10)
		
		self.backBtn = tki.Button(self.root, text="Scan Again", width = 15, height = 2, bg="red", fg="white", font='"DejaVu Sans" 20 bold', command=self.scanMode)
		self.backBtn.pack(padx=10,pady=10)
		
		self.backBtn.pack_forget()
		self.availabilityLbl.pack_forget()
		self.nameLbl.pack_forget()
		self.codeLbl.pack_forget()
		self.priceLbl.pack_forget()
		
		self.original = Image.open("images/camera.png")
		#photo = ImageTk.PhotoImage(original)
		self.resized = self.original.resize((100,100),Image.ANTIALIAS)
		self.photo = ImageTk.PhotoImage(self.resized)

		# create a button, that when pressed, will take the current
		# frame and save it to file
		self.btn = tki.Button(self.root, text="Capture!", width = 10,
			command=self.takeSnapshot)
		self.btn.config(image=self.photo,width=120)
		self.btn.pack(side="right", fill="both", expand="yes", padx=10,pady=10)
		
		self.btn.pack_forget()

		# start a thread that constantly pools the video sensor for
		# the most recently read frame
		self.stopEvent = threading.Event()

		# set a callback to handle when the window is closed
		self.root.wm_title("Stock Scanner")
		self.root.wm_protocol("WM_DELETE_WINDOW", self.onClose)
		
		self.cameraTimeout()
		
		self.startScanner()

	def videoLoop(self):
		# DISCLAIMER:
		# I'm not a GUI developer, nor do I even pretend to be. This
		# try/except statement is a pretty ugly hack to get around
		# a RunTime error that Tkinter throws due to threading
		try:
			# keep looping over frames until we are instructed to stop
			if not self.stopEvent.is_set():
				# grab the frame from the video stream and resize it to
				# have a maximum width of 300 pixels
				self.frame = self.vs.read()
				self.frame = imutils.resize(self.frame, width=650)
		
				# OpenCV represents images in BGR order; however PIL
				# represents images in RGB order, so we need to swap
				# the channels, then convert to PIL and ImageTk format
				image = cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGB)
				image = Image.fromarray(image)
				
				draw = ImageDraw.Draw(image)
				draw.line([221,142,244,142],fill="black", width=5)
				draw.line([221,142,221,165],fill="black", width=5)
				
				draw.line([221,142,244,142],fill="white", width=1)
				draw.line([221,142,221,165],fill="white", width=1)
				
				draw.line([221,235,221,212],fill="black", width=5)
				draw.line([221,235,244,235],fill="black", width=5)
				
				draw.line([221,235,221,212],fill="white", width=1)
				draw.line([221,235,244,235],fill="white", width=1)
				
				draw.line([429,142,406,142],fill="black", width=5)
				draw.line([429,142,429,165],fill="black", width=5)
				
				draw.line([429,142,406,142],fill="white", width=1)
				draw.line([429,142,429,165],fill="white", width=1)
				
				draw.line([429,235,429,212],fill="black", width=5)
				draw.line([429,235,406,235],fill="black", width=5)
				
				draw.line([429,235,429,212],fill="white", width=1)
				draw.line([429,235,406,235],fill="white", width=1)
				
				if self.drawTryAgain == True:
					draw.text([231,245],"PLEASE TRY AGAIN",fill="red",font=self.tryAgainFont)
								
				#draw.line([0,390,650,390],fill="red") # Shows buttom of camera
				del draw
				
				image = ImageTk.PhotoImage(image)
		
				# if the panel is not None, we need to initialize it
				if self.panel is None:
					self.panel = tki.Label(image=image)
					self.panel.image = image
					self.panel.pack(side="left", padx=10, pady=10)
		
				# otherwise, simply update the panel
				else:
					self.panel.configure(image=image)
					self.panel.image = image

		except RuntimeError as e:
			print("[INFO] caught a RuntimeError")
			
		if self.captureScreen == True:
                    self.panel.after(10,self.videoLoop)

	def getApi(self, product_id):
		
		print("Testing: " + product_id)
		
		urlTitle = "https://st1-services-json.electrocomponents.com/service/ProductService/v01_01/JSON/Location/STORE_ID/GB_1/Product/" + str(product_id)
		urlPrice = "https://st1-services-json.electrocomponents.com/service/ProductPriceService/v01_00/JSON/Location/COUNTRY_CODE/GB/Timezone/UTC/ProductPrices?ProductNumber=" + str(product_id)
		urlStock = "https://st1-services-json.electrocomponents.com/service/ProductStockService/v01_00/JSON/Location/COUNTRY_CODE/GB/ProductStocks?ProductNumber=" + str(product_id)

		headers={'Authorization':'Basic c3lzdGVtdGVzdGluZ2FwcGxpY2F0aW9uX3YxXzAtdXNlcjpwYXNzd29yZA==','Accept':'application/json','Cache-Control':'no-cache'}
		
		reqTitle = requests.get(urlTitle,headers=headers)
		
		try:
			parsedTitle = json.loads(reqTitle.content.decode('utf-8'))
		except:
			return 0
		
		reqPrice = requests.get(urlPrice,headers=headers)
		parsedPrice = json.loads(reqPrice.content.decode('utf-8'))
		reqStock = requests.get(urlStock,headers=headers)
		parsedStock = json.loads(reqStock.content.decode('utf-8'))
		
		productTitle = parsedTitle['GetProductResp']['Product']['ProductSummary']['LongDescription']
		productPrice = parsedPrice['GetProductPricesResp']['ProductPriceCollection']['ProductPrice'][0]['CatalogueBreakPriceCollection']['BreakPrice'][0]['PriceNoTax']
		productStock = parsedStock['GetProductStocksResp']['ProductStockCollection']['ProductStock'][0]['Quantity']
		
		return [productTitle, productPrice, productStock]

	def takeSnapshot(self):

                # load the example image and convert it to grayscale
                image = self.frame.copy()[142:235, 221:429]
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

                #cv2.imshow("Image", gray)

                #gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]

                #gray = cv2.medianBlur(gray, 3)

                # write the grayscale image to disk as a temporary file so we can
                # apply OCR to it
                filename = "{}.png".format(os.getpid())
                cv2.imwrite(filename, gray)

                # load the image as a PIL/Pillow image, apply OCR, and then delete
                # the temporary file
                text = pytesseract.image_to_string(Image.open(filename))
                os.remove(filename)
                print("Found:")
                print(text)
                
                matches = []
                checkOrder = []
                
                matches.append(re.findall(r"\d{3}\-\d{4}",text))
                matches.append(re.findall(r"\d{3}\-\d{3}",text))
                
                matches.append(re.findall(r"\d{7}",text))
                matches.append(re.findall(r"\d{6}",text))
                
                matches.append(re.findall(r"\d{3}\s\d{4}",text))
                matches.append(re.findall(r"\d{3}\s\d{3}",text))
                
                print("Matched (XXX-XXXX): " + str(matches[0]))
                print("Matched (XXX-XXX): " + str(matches[1]))
                print("Matched (XXXXXXX): " + str(matches[2]))
                print("Matched (XXXXXX): " + str(matches[3]))
                print("Matched (XXX XXXX): " + str(matches[4]))
                print("Matched (XXX XXX): " + str(matches[5]))
                
                print("Matches: " + str(len(matches)))
                
                listEmpty = True
                
                for i in range(len(matches)):
                    if len(matches[i]) > 0:
                        listEmpty = False
                        break
                
                if listEmpty == True:
					
                    print("Found nothing, filtering text")
					
                    text = text.replace(' ','')
                    text = text.replace('-','')
                    text = text.replace('—','')
                    
                    print(text)
					
                    matches.append(re.findall(r"\d{7}",text))
                    matches.append(re.findall(r"\d{6}",text))
                
                for i in range(len(matches)):
                    for j in range(len(matches[i])):
                        matches[i][j] = matches[i][j].replace(' ','')
                        matches[i][j] = matches[i][j].replace('-','')
                        checkOrder.append(matches[i][j])
                
                #print ("\nMatches: " + str(matches) + "\n")
                print ("\nCheck Order: " + str(checkOrder) + "\n")
                
                apiResultFail = False
                apiResult = 0
                self.successfulID = ""
                
                for i in range(len(checkOrder)):
                    apiResult = self.getApi(checkOrder[i])
                    if apiResult != 0:
                        successfulID = checkOrder[i]
                        break
                    
                if apiResult == 0:
                    apiResultFail = True
                
                #cv2.imshow("Output", gray)
                
                if apiResultFail == False and len(checkOrder) > 0:
                    
                    #print(apiResult[0])
                    #print(str(successfulID))
                    #print("£" + str(apiResult[1]))
                    #print(str(apiResult[2]) + " available for NEXT DAY delivery!")
                    
                    #self.nameText.set(apiResult[0])
                    
                    self.nameLbl.delete(1.0, tki.END)
                    self.nameLbl.insert(tki.END,apiResult[0])
                    
                    self.nameLbl.tag_add("center", "1.0", "end")
                    
                    self.codeText.set(str(successfulID))
                    self.priceText.set("£" + str(apiResult[1]))
                    self.availabilityText.set(str(apiResult[2]) + " available for NEXT DAY delivery!")
                    
                    self.btn.pack_forget()
                    self.panel.pack_forget()
                    self.nameLbl.pack(padx=10,pady=10)
                    self.codeLbl.pack(padx=10,pady=10)
                    self.priceLbl.pack(padx=10,pady=10)
                    self.availabilityLbl.pack(padx=10,pady=10)
                    self.backBtn.pack(padx=10,pady=10)
                    self.captureScreen = False
                    self.infoScreen = True
                else:
                    apiResultFail = False
                    self.cannotIdentify()

	def scanMode(self):
		self.pressTime = datetime.datetime.now()
		
		self.backBtn.pack_forget()
		self.nameLbl.pack_forget()
		self.codeLbl.pack_forget()
		self.priceLbl.pack_forget()
		self.availabilityLbl.pack_forget()
		self.panel.pack(side="left", padx=10, pady=10)
		self.infoScreen = False
		self.captureScreen = True
		self.videoLoop()
		self.btn.pack(side="right", expand="yes", padx=10,pady=10)
		
	def startScanner(self):
		self.pressTime = datetime.datetime.now()
		
		self.startBtn.pack_forget()
		self.startLbl.pack_forget()
		
		if self.initialSet == False:
			self.panel.pack(side="left", padx=10, pady=10)
		else:
			self.initialSet = False
		
		self.menuScreen = False
		self.captureScreen = True
		
		self.videoLoop()
		
		self.btn.pack(side="right", padx=10,pady=10)
		
		self.panel.after(300000,self.cameraTimeout)
		
	def cameraTimeout(self):
		
		currentTime = datetime.datetime.now()

		difference = ((currentTime - self.pressTime).total_seconds()) / 60
		
		if difference > 5:
			self.backBtn.pack_forget()
			self.nameLbl.pack_forget()
			self.codeLbl.pack_forget()
			self.priceLbl.pack_forget()
			self.availabilityLbl.pack_forget()
			self.btn.pack_forget()
			self.panel.pack_forget()
		
			self.captureScreen = False
			self.infoScreen = False
			self.menuScreen = True
		
			self.startLbl.pack(padx=10,pady=10)
			self.startBtn.pack(padx=10,pady=10)
			
		self.root.after(180000,self.cameraTimeout)
		
	def cannotIdentify(self):
		
		if self.drawTryAgain == True:
			self.drawTryAgain = False
		else:
			self.drawTryAgain = True
			self.root.after(1000,self.cannotIdentify)

	def onClose(self):
		# set the stop event, cleanup the camera, and allow the rest of
		# the quit process to continue
		print("[INFO] closing...")
		self.stopEvent.set()
		self.vs.stop()
		self.root.quit()


# initialize the video stream and allow the camera sensor to warmup
print("[INFO] warming up camera...")
vs = VideoStream(usePiCamera=1 > 0).start()
time.sleep(2.0)

# start the app
sc = StockScanner(vs)
sc.root.mainloop()
