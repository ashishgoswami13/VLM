from google import genai
from google.genai import types

# Initialize the GenAI client and specify the model
MODEL_ID = "gemini-robotics-er-1.5-preview"
client = genai.Client(api_key="AIzaSyCOJjSo9ZoWRy4haWRVBi0ghC2LSll8JcA")

# Load your image and set up your prompt
with open('/home/dev/VLM/scene.jpg', 'rb') as f:
    image_bytes = f.read()

queries = [
    "pen",
    "Blue box",
    "red box",
]

prompt = f"""
    Describe what you see in the image in short bullet points.
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

