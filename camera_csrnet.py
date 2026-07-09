import cv2
      
                
import json

from commonsCRNet import get_model

# Custom Imports 
import numpy as np
import PIL.Image as Image

from torchvision import transforms
import matplotlib.pyplot as plt
import random



# Access commons
model = get_model()
# Standard RGB transform
transform=transforms.Compose([transforms.ToTensor(),transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),])





class VideoCamera(object):
    def __init__(self,fileName):
        # Using OpenCV to capture from device 0. If you have trouble capturing
        # from a webcam, comment the line below out and use a video file
        # instead.
        if (fileName ==''):
            self.video = cv2.VideoCapture(0)
        else:  
            self.video = cv2.VideoCapture(fileName)
            self.video.set(cv2.CAP_PROP_BUFFERSIZE, 1)
#        self.video = cv2.resize(self.video,(840,640))
        # If you decide to use video.mp4, you must have this file in the folder
        # as the main.py.
        # self.video = cv2.VideoCapture('video.mp4')
    
    def __del__(self):
        self.video.release()
    
    def get_frame(self):
        
        cap =self.video 
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        #fourcc = cv2.VideoWriter_fourcc('m', 'p', '4', 'v')


        ret, frame = self.video.read()
        print(frame.shape)

        '''out video'''
        width = frame.shape[1] #output size
        height = frame.shape[0] #output size
     

        while True:
     
            try:
                ret, frame = cap.read()

                scale_factor = 0.5
                frame = cv2.resize(frame, (0, 0), fx=scale_factor, fy=scale_factor)
                ori_img = frame.copy()
            except:
                cap.release()
                break
                
    
       
       
            frame = frame.copy()

            
            img = transform(frame)

            img = img.cpu()
            
            
            output = model(img.unsqueeze(0))
            prediction = int(output.detach().cpu().sum().numpy())
            
            try:
                from drishti.backend.count_ws import update_latest_count
                update_latest_count(int(prediction), "csrnet", None, "stream")
            except ImportError:
                pass
            except Exception as e:
                print("Failed to emit live count:", e)

            x = random.randint(1,100000) 
            density = 'static/density_map'+str(x)+'.jpg' 
            plt.imsave(density, output.detach().cpu().numpy()[0][0]) 
                
            cv2.putText(frame, "Count:" + str(prediction), (30, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

            ret, jpeg = cv2.imencode('.jpg', frame)
            return jpeg.tobytes()
