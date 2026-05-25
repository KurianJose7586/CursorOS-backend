from PIL import Image, ImageDraw

def create_placeholder_icon():
    # Create a simple 64x64 blue square with a white "C"
    image = Image.new('RGB', (64, 64), color=(73, 109, 137))
    d = ImageDraw.Draw(image)
    d.text((10, 10), "C", fill=(255, 255, 0))
    image.save("backend/assets/icon.png")

if __name__ == "__main__":
    create_placeholder_icon()
