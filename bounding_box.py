
from google import genai
from google.genai import types
import json
from PIL import Image, ImageDraw, ImageFont
import io

# Initialize the GenAI client and specify the model
MODEL_ID = "gemini-robotics-er-1.5-preview"
client = genai.Client(api_key="AIzaSyCOJjSo9ZoWRy4haWRVBi0ghC2LSll8JcA")

# Load your image and set up your prompt
with open('/home/dev/VLM/scene.jpg', 'rb') as f:
    image_bytes = f.read()

prompt = """
      Return bounding boxes as a JSON array with labels. Never return masks
      or code fencing. Limit to 25 objects. Include as many objects as you
      can identify on the table.
      If an object is present multiple times, name them according to their
      unique characteristic (colors, size, position, unique characteristics, etc..).
      The format should be as follows: [{"box_2d": [ymin, xmin, ymax, xmax],
      "label": <label for the object>}] normalized to 0-1000. The values in
      box_2d must only be integers
      """

image_response = client.models.generate_content(
  model=MODEL_ID,
  contents=[
    types.Part.from_bytes(
      data=image_bytes,
      mime_type='image/jpeg',
    ),
    prompt
  ],
  config = types.GenerateContentConfig(
      temperature=0.5,
      thinking_config=types.ThinkingConfig(thinking_budget=0)
  )
)

print(image_response.text)

# Parse the bounding boxes from the response
try:
    # Remove markdown code fencing if present
    response_text = image_response.text.strip()
    if response_text.startswith('```'):
        # Remove the first line (```json) and last line (```)
        lines = response_text.split('\n')
        response_text = '\n'.join(lines[1:-1])
    
    bounding_boxes = json.loads(response_text)
    
    # Load the image
    image = Image.open('/home/dev/VLM/scene.jpg')
    width, height = image.size
    
    # Create a drawing context
    draw = ImageDraw.Draw(image)
    
    # Try to load a font, fall back to default if not available
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
    except:
        font = ImageFont.load_default()
    
    # Draw each bounding box
    for obj in bounding_boxes:
        box_2d = obj['box_2d']
        label = obj['label']
        
        # Convert normalized coordinates (0-1000) to pixel coordinates
        ymin = int(box_2d[0] * height / 1000)
        xmin = int(box_2d[1] * width / 1000)
        ymax = int(box_2d[2] * height / 1000)
        xmax = int(box_2d[3] * width / 1000)
        
        # Draw rectangle
        draw.rectangle([xmin, ymin, xmax, ymax], outline="red", width=3)
        
        # Draw label background
        text_bbox = draw.textbbox((xmin, ymin - 20), label, font=font)
        draw.rectangle(text_bbox, fill="red")
        
        # Draw label text
        draw.text((xmin, ymin - 20), label, fill="white", font=font)
    
    # Save the image with bounding boxes
    output_path = '/home/dev/VLM/scene_with_boxes.jpg'
    image.save(output_path)
    print(f"\nImage with bounding boxes saved to: {output_path}")
    
except json.JSONDecodeError as e:
    print(f"Error parsing JSON response: {e}")
except Exception as e:
    print(f"Error drawing bounding boxes: {e}")
