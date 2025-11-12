from google import genai
from google.genai import types
import cv2
import time
import textwrap
import os
import json

# Initialize the GenAI client and specify the model
MODEL_ID = "gemini-robotics-er-1.5-preview"
client = genai.Client(api_key="AIzaSyCOJjSo9ZoWRy4haWRVBi0ghC2LSll8JcA")

def capture_video(duration=10, output_path="temp_video.mp4"):
    """
    Capture video from webcam for specified duration
    
    Args:
        duration: Recording duration in seconds
        output_path: Path to save the video file
    """
    print(f"Starting video capture for {duration} seconds...")
    print("Press 'q' to stop recording early")
    
    # Initialize webcam
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        raise Exception("Could not open webcam")
    
    # Get video properties
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    if fps == 0:
        fps = 30  # Default to 30 fps if not available
    
    # Define codec and create VideoWriter
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (frame_width, frame_height))
    
    start_time = time.time()
    
    while True:
        ret, frame = cap.read()
        
        if not ret:
            print("Failed to grab frame")
            break
        
        # Write frame to output
        out.write(frame)
        
        # Display the frame
        cv2.imshow('Recording... (Press q to stop)', frame)
        
        # Check if duration reached or 'q' pressed
        elapsed = time.time() - start_time
        if elapsed >= duration or cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    # Release everything
    cap.release()
    out.release()
    cv2.destroyAllWindows()
    
    actual_duration = time.time() - start_time
    print(f"Video captured: {actual_duration:.2f} seconds")
    return output_path

def upload_and_process_video(video_path, prompt):
    """
    Upload video to Gemini and process with given prompt
    
    Args:
        video_path: Path to video file
        prompt: User's prompt for analysis
    """
    print("\nUploading video to Gemini...")
    
    # Upload the video file
    myfile = client.files.upload(file=video_path)
    
    # Wait for processing
    print("Processing", end="")
    while myfile.state == "PROCESSING":
        print(".", end="", flush=True)
        time.sleep(1)
        myfile = client.files.get(name=myfile.name)
    
    if myfile.state.name == "FAILED":
        raise ValueError(f"File upload failed: {myfile.state.name}")
    
    print("\nUploaded successfully!")
    
    # Generate content with the video and prompt
    print("\nAnalyzing video with your prompt...")
    start_time = time.time()
    
    response = client.models.generate_content(
        model=MODEL_ID,
        contents=[myfile, prompt],
        config=types.GenerateContentConfig(
            temperature=0.5,
            thinking_config=types.ThinkingConfig(thinking_budget=-1),
        ),
    )
    
    end_time = time.time()
    elapsed_time = end_time - start_time
    
    print(f"\nTotal processing time: {elapsed_time:.4f} seconds")
    print("\n" + "="*50)
    print("RESPONSE:")
    print("="*50)
    print(response.text)
    
    return response.text

def main():
    """
    Main interactive loop for video capture and analysis
    """
    print("="*60)
    print("Live Video Analysis with Gemini Robotics")
    print("="*60)
    
    while True:
        print("\n" + "-"*60)
        print("Options:")
        print("1. Capture and analyze video")
        print("2. Analyze existing video file")
        print("3. Exit")
        print("-"*60)
        
        choice = input("\nSelect option (1/2/3): ").strip()
        
        if choice == '3':
            print("Goodbye!")
            break
        
        elif choice == '1':
            # Get recording duration
            duration_input = input("\nEnter recording duration in seconds (default: 10): ").strip()
            duration = int(duration_input) if duration_input else 10
            
            try:
                # Capture video
                video_path = capture_video(duration=duration)
                
                # Get user prompt
                print("\n" + "-"*60)
                print("Enter your prompt for analysis:")
                print("(Press Enter twice to finish)")
                print("-"*60)
                
                lines = []
                while True:
                    line = input()
                    if line == "" and lines and lines[-1] == "":
                        break
                    lines.append(line)
                
                prompt = "\n".join(lines).strip()
                
                if not prompt:
                    prompt = textwrap.dedent("""\
                        Describe in detail what happens in this video.
                        Breaking it down by timestamp, output in JSON format 
                        with keys "start_timestamp", "end_timestamp" and "description".""")
                    print(f"\nUsing default prompt:\n{prompt}")
                
                # Process the video
                response_text = upload_and_process_video(video_path, prompt)
                
                # Ask if user wants to save response
                save = input("\nSave response to file? (y/n): ").strip().lower()
                if save == 'y':
                    output_file = f"response_{int(time.time())}.txt"
                    with open(output_file, 'w') as f:
                        f.write(response_text)
                    print(f"Response saved to: {output_file}")
                
                # Ask if user wants to delete the video
                delete = input("Delete temporary video file? (y/n): ").strip().lower()
                if delete == 'y':
                    os.remove(video_path)
                    print("Video file deleted")
                    
            except Exception as e:
                print(f"Error: {e}")
        
        elif choice == '2':
            # Analyze existing video
            video_path = input("\nEnter path to video file: ").strip()
            
            if not os.path.exists(video_path):
                print(f"Error: File not found: {video_path}")
                continue
            
            # Get user prompt
            print("\n" + "-"*60)
            print("Enter your prompt for analysis:")
            print("(Press Enter twice to finish)")
            print("-"*60)
            
            lines = []
            while True:
                line = input()
                if line == "" and lines and lines[-1] == "":
                    break
                lines.append(line)
            
            prompt = "\n".join(lines).strip()
            
            if not prompt:
                prompt = textwrap.dedent("""\
                    Describe in detail what happens in this video.
                    Breaking it down by timestamp, output in JSON format 
                    with keys "start_timestamp", "end_timestamp" and "description".""")
                print(f"\nUsing default prompt:\n{prompt}")
            
            try:
                # Process the video
                response_text = upload_and_process_video(video_path, prompt)
                
                # Ask if user wants to save response
                save = input("\nSave response to file? (y/n): ").strip().lower()
                if save == 'y':
                    output_file = f"response_{int(time.time())}.txt"
                    with open(output_file, 'w') as f:
                        f.write(response_text)
                    print(f"Response saved to: {output_file}")
                    
            except Exception as e:
                print(f"Error: {e}")
        
        else:
            print("Invalid option. Please select 1, 2, or 3.")

if __name__ == "__main__":
    main()
