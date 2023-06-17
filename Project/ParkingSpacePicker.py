import cv2
import pickle
import numpy as np
  
POLYGONS = []
polygon_pos = []

# func to check if a point falls inside a polygon
def point_inside_polygon(x,y,poly):
    n = len(poly)
    inside =False
    p1x,p1y = poly[0]
    for i in range(n+1):
        p2x,p2y = poly[i % n]
        if y > min(p1y,p2y):
            if y <= max(p1y,p2y):
                if x <= max(p1x,p2x):
                    if p1y != p2y:
                        xinters = (y-p1y)*(p2x-p1x)/(p2y-p1y)+p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x,p1y = p2x,p2y
    return inside

def mouseClick(events, x, y, flags, params):
    global POLYGONS, polygon_pos
    if events == cv2.EVENT_LBUTTONDOWN:
        # posList.append((x, y))
        polygon_pos.append((x, y))
        print('polygon_pos: ', polygon_pos, 'updated')
    if len(polygon_pos) == 4:
        POLYGONS.append(polygon_pos)
        polygon_pos=[]
        print("Polygon: ", POLYGONS, 'updated')
    
    if events == cv2.EVENT_RBUTTONDOWN:
        if len(polygon_pos)>0:
            polygon_pos.clear()
        for polygon in POLYGONS:
            if point_inside_polygon(x,y,polygon):
                POLYGONS.remove(polygon)
                print('polygon removed')
                break

 
 

def open_parking_image_window(pngimage='carParkImg.png',params={'parking':'hazratganj_1'}):
    global POLYGONS, polygon_pos
    try:
        with open(params.get('parking'), 'rb') as f:
            POLYGONS = pickle.load(f)
    except:pass
    
    while True:
        img = cv2.imread(pngimage)
        overlay  = img.copy()
        for i,polygon in enumerate(POLYGONS):
            try:cv2.fillPoly(overlay, np.array([polygon]), (0, 255, 0))
            except:
                print('error in polygon: ',i, polygon)
        cv2.addWeighted(img, 0.5, overlay, 0.5, 0, img)
        for point in polygon_pos:
            cv2.circle(img, point, 2, (0, 0, 255), -1)
        

   
        cv2.imshow("Image", img)
        cv2.setMouseCallback("Image", mouseClick, params)
        # save all poslist
        if cv2.waitKey(1) == ord('s'):
            with open(params.get('parking'), 'wb') as f:
                pickle.dump(POLYGONS, f)
            print('saved')
        if cv2.waitKey(1) == 27:
            break
        
    cv2.destroyAllWindows()

if __name__ == "__main__":
    parking_img = r'static\uploads\WhatsApp_Image_2023-01-07_at_14.16.10.jpg'
    parking='parking_a'
    open_parking_image_window(parking_img, params=dict(parking=parking))