"""Constrained RGB detector: pixels + approved topology + camera calibration only."""
import cv2, numpy as np, math
from .topology import CONNECTIONS, BY_ID

VERSION='opencv-lines-1.0'
PARAMETERS=dict(canny_low=45,canny_high=125,hough_threshold=22,min_line_length_px=38,max_line_gap_px=10,approved_tolerance_px=7,anchor_tolerance_px=30,minimum_candidate_length_px=45)
LIMITS=['Controlled synthetic overhead views only; clutter, occlusion and thin wires can prevent detection.','Visible line geometry cannot establish ownership, authorization, current or energization.','No visible candidate does not clear an electrical imbalance.']

def project(points,pose):
    eye=np.array(pose['position'],float); target=np.array(pose['target'],float)
    forward=target-eye; forward/=np.linalg.norm(forward)
    right=np.cross(forward,[0,1,0]); right/=np.linalg.norm(right); up=np.cross(right,forward)
    focal=240/math.tan(math.radians(pose['fov'])/2)
    result=[]
    for point in points:
        d=np.array(point)-eye; depth=float(d@forward)
        result.append([320+float(d@right)*focal/max(depth,.001),240-float(d@up)*focal/max(depth,.001)])
    return result

def dist_segment(p,a,b):
    p,a,b=map(lambda v:np.array(v,float),(p,a,b)); ab=b-a
    return float(np.linalg.norm(p-(a+np.clip((p-a)@ab/max(ab@ab,1e-8),0,1)*ab)))

def detect(image,pose,target_id):
    gray=cv2.cvtColor(image,cv2.COLOR_BGR2GRAY); annotated=image.copy()
    target=BY_ID[target_id]['position_m']; anchor=project([target],pose)[0]
    approved=[]
    for c in CONNECTIONS:
        approved.append(project(c['geometry_points_m'],pose))
    local=[project(c['geometry_points_m'],pose) for c in CONNECTIONS if c['from_asset_id']==target_id]
    # Only the known overhead observation band; no event-dependent crop or mask.
    x0=max(0,int(min(p[0] for line in local for p in line))-55); x1=min(640,int(max(p[0] for line in local for p in line))+100)
    y0=max(0,int(min(p[1] for line in local for p in line))-45); y1=min(480,int(max(p[1] for line in local for p in line))+12)
    roi=np.zeros_like(gray); roi[y0:y1,x0:x1]=255
    edges=cv2.Canny(gray,PARAMETERS['canny_low'],PARAMETERS['canny_high']); edges=cv2.bitwise_and(edges,roi)
    lines=cv2.HoughLinesP(edges,1,np.pi/180,PARAMETERS['hough_threshold'],minLineLength=PARAMETERS['min_line_length_px'],maxLineGap=PARAMETERS['max_line_gap_px'])
    observed=[]; matched=0
    for raw in ([] if lines is None else lines[:,0]):
        a=raw[:2].astype(float); b=raw[2:].astype(float); length=float(np.linalg.norm(a-b))
        # A service line must originate near the approved pole and be oblique.
        if length<45 or min(np.linalg.norm(a-anchor),np.linalg.norm(b-anchor))>30: continue
        if abs(a[0]-b[0])<12: continue
        samples=[a*(1-t)+b*t for t in np.linspace(0,1,11)]
        # Hough may merge adjacent collinear approved spans. Compare to their
        # union, rather than incorrectly demanding one path cover the segment.
        distance=max(min(dist_segment(p,c[0],c[-1]) for c in approved) for p in samples)
        if distance<=7: matched+=1; continue
        def same_line(o):
            u=b-a;v=np.array(o['line_px'][2:])-np.array(o['line_px'][:2])
            return abs(u[0]*v[1]-u[1]*v[0])<100 and dist_segment(a,o['line_px'][:2],o['line_px'][2:])<10
        if any(same_line(o) for o in observed): continue
        box=[max(0,int(min(a[0],b[0]))-8),max(0,int(min(a[1],b[1]))-8),min(639,int(max(a[0],b[0]))+8),min(479,int(max(a[1],b[1]))+8)]
        observed.append(dict(label='candidate_extra_connection',bbox_px=box,line_px=[int(v) for v in raw],geometric_match_score=min(.99,distance/40)))
    usable=cv2.meanStdDev(gray[y0:y1,x0:x1])[1][0][0]>8 if y1>y0 and x1>x0 else False
    status='candidate_found' if observed else ('no_visible_candidate' if usable and matched else 'inconclusive')
    for o in observed:
        x,y,xx,yy=o['bbox_px']; cv2.rectangle(annotated,(x,y),(xx,yy),(30,187,255),2)
        cv2.putText(annotated,'Candidate line: verify in field',(max(5,x-20),max(18,y-10)),cv2.FONT_HERSHEY_SIMPLEX,.42,(30,187,255),1,cv2.LINE_AA)
    return dict(observation_status=status,observations=observed,parameters={**PARAMETERS,'roi_px':[x0,y0,x1,y1]},detector_version=VERSION,limitations=LIMITS,matched_approved_segments=matched),annotated
