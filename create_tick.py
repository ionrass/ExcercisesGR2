from PIL import Image, ImageDraw

# Create a new image with a white background
img = Image.new('RGBA', (32, 32), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)

# Draw a green tick
draw.line([(8, 16), (14, 22), (24, 10)], fill=(0, 255, 0), width=3)

# Save the image
img.save('tick.png')