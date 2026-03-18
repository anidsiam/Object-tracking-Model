import cv2
import csv
import os
from datetime import datetime

print("="*60)
print("VIDEO OBJECT TRACKER")
print("="*60)

# Get video path from user
video_path = input("\nEnter the full path to your video file: ").strip('"').strip("'")

# Check if video exists
if not os.path.exists(video_path):
    print(f"\n ERROR: Video file not found at: {video_path}")
    print("Please check the path and try again.")
    input("Press Enter to exit...")
    exit()

# Open video
video = cv2.VideoCapture(video_path)
if not video.isOpened():
    print("\n ERROR: Cannot open video file.")
    print("Make sure the video format is supported (mp4, avi, mov, etc.)")
    input("Press Enter to exit...")
    exit()

# Get video properties
fps = video.get(cv2.CAP_PROP_FPS)
total_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
duration = total_frames / fps

print(f"\n Video loaded successfully!")
print(f"   Duration: {duration:.2f} seconds")
print(f"   FPS: {fps:.2f}")
print(f"   Total frames: {total_frames}")

# Read first frame
ret, frame = video.read()
if not ret:
    print("\n ERROR: Cannot read first frame.")
    input("Press Enter to exit...")
    exit()

# Instructions for user
print("\n" + "="*60)
print("INSTRUCTIONS:")
print("="*60)
print("1. A window will open showing the first frame")
print("2. Click and drag to draw a box around the object to track")
print("3. Press SPACE or ENTER when done")
print("4. Press C to cancel and try again")
print("\nMake sure to select the object tightly!")
print("="*60)
input("\nPress Enter to continue...")

# Let user select object
bbox = cv2.selectROI('SELECT OBJECT TO TRACK', frame, False, False)
cv2.destroyWindow('SELECT OBJECT TO TRACK')

if bbox[2] == 0 or bbox[3] == 0:
    print("\n No object selected. Exiting...")
    input("Press Enter to exit...")
    exit()

print(f"\n Object selected: x={bbox[0]}, y={bbox[1]}, width={bbox[2]}, height={bbox[3]}")

# Choose tracker
print("\n" + "="*60)
print("CHOOSE TRACKING ALGORITHM:")
print("="*60)
print("1. CSRT - Most accurate (RECOMMENDED for 46 seconds)")
print("2. KCF - Faster, good accuracy")
print("3. MOSSE - Fastest, lower accuracy")
print("="*60)

choice = input("\nEnter choice (1-3) or press Enter for default [1]: ").strip()
if choice == '2':
    tracker = cv2.TrackerKCF_create()
    tracker_name = "KCF"
elif choice == '3':
    tracker = cv2.TrackerMOSSE_create()
    tracker_name = "MOSSE"
else:
    tracker = cv2.TrackerCSRT_create()
    tracker_name = "CSRT"

print(f"\n Using {tracker_name} tracker")

# Initialize tracker
tracker.init(frame, bbox)

# Prepare output
video_name = os.path.splitext(os.path.basename(video_path))[0]
output_dir = os.path.dirname(video_path)
if not output_dir:
    output_dir = "."

output_video_path = os.path.join(output_dir, f"{video_name}_TRACKED.mp4")
output_csv_path = os.path.join(output_dir, f"{video_name}_TRACKING_DATA.csv")

# Get video properties for output
frame_width = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
frame_height = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out = cv2.VideoWriter(output_video_path, fourcc, fps, (frame_width, frame_height))

# Prepare CSV
csv_file = open(output_csv_path, 'w', newline='')
csv_writer = csv.writer(csv_file)
csv_writer.writerow(['Frame', 'Timestamp (seconds)', 'X', 'Y', 'Width', 'Height', 'Center_X', 'Center_Y', 'Tracking_Success'])

print("\n" + "="*60)
print("TRACKING IN PROGRESS...")
print("="*60)
print("Press 'Q' to stop early (video window)")

frame_number = 0
success_count = 0

# Reset video to beginning
video.set(cv2.CAP_PROP_POS_FRAMES, 0)

while True:
    ret, frame = video.read()
    if not ret:
        break
    
    frame_number += 1
    timestamp = frame_number / fps
    
    # Update tracker
    success, bbox = tracker.update(frame)
    
    if success:
        success_count += 1
        x, y, w, h = [int(v) for v in bbox]
        center_x = int(x + w/2)
        center_y = int(y + h/2)
        
        # Draw tracking box (green)
        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 3)
        
        # Draw center point
        cv2.circle(frame, (center_x, center_y), 5, (0, 0, 255), -1)
        
        # Add tracking info
        cv2.putText(frame, f"Frame: {frame_number}/{total_frames}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(frame, f"Time: {timestamp:.2f}s", (10, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(frame, "TRACKING", (10, 90),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        # Write to CSV
        csv_writer.writerow([frame_number, f"{timestamp:.3f}", x, y, w, h, center_x, center_y, 'Yes'])
        
    else:
        # Tracking failed
        cv2.putText(frame, f"Frame: {frame_number}/{total_frames}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(frame, f"Time: {timestamp:.2f}s", (10, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(frame, "TRACKING LOST", (10, 90),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        
        csv_writer.writerow([frame_number, f"{timestamp:.3f}", '', '', '', '', '', '', 'No'])
    
    # Write frame to output video
    out.write(frame)
    
    # Show frame
    cv2.imshow('Tracking - Press Q to Stop', frame)
    
    # Progress indicator
    if frame_number % 10 == 0:
        progress = (frame_number / total_frames) * 100
        print(f"Progress: {progress:.1f}% ({frame_number}/{total_frames} frames)")
    
    # Check for quit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        print("\n Tracking stopped by user")
        break

# Cleanup
video.release()
out.release()
cv2.destroyAllWindows()
csv_file.close()

# Final report
print("\n" + "="*60)
print("TRACKING COMPLETE!")
print("="*60)
print(f" Tracked {success_count}/{frame_number} frames successfully")
print(f"   Success rate: {(success_count/frame_number)*100:.1f}%")
print(f"\n Output files saved:")
print(f"   Video: {output_video_path}")
print(f"   Data:  {output_csv_path}")
print("="*60)
print("\nYour file is ready!")
input("\nPress Enter to exit...")
