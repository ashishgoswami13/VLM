from google import genai
from google.genai import types
import json
from PIL import Image, ImageDraw, ImageFont

# Initialize the GenAI client and specify the model
MODEL_ID = "gemini-robotics-er-1.5-preview"
client = genai.Client(api_key="AIzaSyCOJjSo9ZoWRy4haWRVBi0ghC2LSll8JcA")
# Load your image and set up your prompt
with open('/home/dev/VLM/Screenshot from 2025-11-12 18-10-24.png', 'rb') as f:
    image_bytes = f.read()

points_data = []
prompt = """
 i want to keep both the blue and the red box on the paoer.The points should be labeled by order of the trajectory, from '0'
        (start point at left hand) to <n> (final point)
        The answer should follow the json format:
        [{"point": <point>, "label": <label1>}, ...].
        The points are in [y, x] format normalized to 0-1000.

        """

image_response = client.models.generate_content(
  model=MODEL_ID,
  contents=[
    types.Part.from_bytes(
      data=image_bytes,
      mime_type='image/png',
    ),
    prompt
  ],
  config = types.GenerateContentConfig(
      temperature=0.5,
  )
)

print(image_response.text)

# Parse the trajectory points from the response
try:
    # Remove markdown code fencing if present
    response_text = image_response.text.strip()
    if response_text.startswith('```'):
        # Remove the first line (```json) and last line (```)
        lines = response_text.split('\n')
        response_text = '\n'.join(lines[1:-1])
    
    points_data = json.loads(response_text)
    
    # Load the image
    image = Image.open('/home/dev/VLM/Screenshot from 2025-11-12 17-38-08.png')
    width, height = image.size
    
    # Create a drawing context
    draw = ImageDraw.Draw(image)
    
    # Try to load a font, fall back to default if not available
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 14)
    except:
        font = ImageFont.load_default()
    
    # Draw each point in the trajectory
    for i, point_obj in enumerate(points_data):
        point = point_obj['point']
        label = point_obj['label']
        
        # Convert normalized coordinates (0-1000) to pixel coordinates
        y = int(point[0] * height / 1000)
        x = int(point[1] * width / 1000)
        
        # Use different colors for start, middle, and end points
        if i == 0:
            color = "green"  # Start point
        elif i == len(points_data) - 1:
            color = "red"  # End point
        else:
            color = "blue"  # Middle points
        
        # Draw a circle for the point
        radius = 8
        draw.ellipse([x - radius, y - radius, x + radius, y + radius], 
                     fill=color, outline="white", width=2)
        
        # Draw label with background
        label_text = str(label)
        text_bbox = draw.textbbox((x + 12, y - 7), label_text, font=font)
        draw.rectangle(text_bbox, fill=color)
        draw.text((x + 12, y - 7), label_text, fill="white", font=font)
        
        # Draw line to next point if not the last point
        if i < len(points_data) - 1:
            next_point = points_data[i + 1]['point']
            next_y = int(next_point[0] * height / 1000)
            next_x = int(next_point[1] * width / 1000)
            draw.line([x, y, next_x, next_y], fill="yellow", width=3)
    
    # Save the image with trajectory points
    output_path = '/home/dev/VLM/trajectory_with_points.png'
    image.save(output_path)
    print(f"\nImage with trajectory points saved to: {output_path}")
    print(f"Total points: {len(points_data)}")
    
except json.JSONDecodeError as e:
    print(f"Error parsing JSON response: {e}")
except Exception as e:
    print(f"Error drawing trajectory points: {e}")