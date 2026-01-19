# Importing required library.
from rembg import remove
import io

# Removing background from image.
def remove_background(image_bytes):
    return io.BytesIO(remove(image_bytes))