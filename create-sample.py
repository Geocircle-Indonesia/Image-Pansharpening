import rasterio
import numpy as np
import uuid
from rasterio.transform import from_origin
from rasterio.enums import Resampling
from PIL import Image
from skimage import exposure
import tkinter as tk
from tkinter import filedialog
import os

# Create a function to read 4 bands and 1 bands image. Store as numpy array
def read_images(multispectral, panchromatic, pansharpen):
    with rasterio.open(panchromatic) as src_p:
        panchromatic_image = src_p.read()
        panchromatic_image = np.transpose(panchromatic_image, (1, 2, 0))

    with rasterio.open(multispectral) as src_ms:
        multispectral_image = src_ms.read(
            out_shape=(src_ms.count, src_p.height, src_p.width),
            resampling=Resampling.nearest
        )
        multispectral_image = np.transpose(multispectral_image, (1, 2, 0))

    with rasterio.open(pansharpen) as src_pan:
        pansharpen_image = src_pan.read(
            out_shape=(src_pan.count, src_p.height, src_p.width),
            resampling=Resampling.nearest
        )
        pansharpen_image = np.transpose(pansharpen_image, (1, 2, 0))

    return multispectral_image, panchromatic_image, pansharpen_image

def sliding_window(image, window_size):
    height, width = image.shape[:2]
    window_width, window_height = window_size

    for y in range(0, height - window_height + 1, window_height):
        for x in range(0, width - window_width + 1, window_width):
            window = image[y:y + window_height, x:x + window_width]
            yield window, (x, y, x + window_width, y + window_height)

def generate_random_key_value():
    # Generate a random key using UUID
    random_key = str(uuid.uuid4())
    return random_key

def export_array_to_image(array, output_path):
    array = exposure.rescale_intensity(array, out_range='uint8')
    # Get the dimensions of the array
    height, width, bands = array.shape
    projection = 'EPSG:4326'

    # Get the directory of output_path
    output_dir = os.path.dirname(output_path)

    # Create directory if doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    with rasterio.open(
        output_path,
        'w',
        driver='GTiff',
        height=height,
        width=width,
        count=bands,
        dtype=array.dtype,
        crs=projection,
    ) as dst:
        # Write the array data to the GeoTIFF bands
        for band in range(bands):
            dst.write(array[:, :, band], band + 1)


def select_file(file_type):
    file_path = filedialog.askopenfilename(title=f"Upload {file_type} Image", filetypes=[("All files", "*.*")])
    return file_path

def main():
    root = tk.Tk()
    root.withdraw()  # Hide the main window

    multispectral_path = select_file("Multispectral")
    panchromatic_path = select_file("Panchromatic")
    pansharpen_path = select_file("Pansharpen")

    window_size = (256, 256)

    multispectral_array, panchromatic_array, pansharpen_array = read_images(multispectral_path, panchromatic_path, pansharpen_path)
    for _, coordinates in sliding_window(panchromatic_array, window_size):
        start_x, start_y, end_x, end_y = coordinates
        cropped_ms = multispectral_array[start_y:end_y, start_x:end_x, :]
        cropped_p = panchromatic_array[start_y:end_y, start_x:end_x, :]
        cropped_pan = pansharpen_array[start_y:end_y, start_x:end_x, :]
        key = generate_random_key_value()

        input_filename = os.path.splitext(os.path.basename(multispectral_path))[0]

        export_array_to_image(cropped_ms, f'./DATA/MS_{input_filename}/MS_{key}.tif')
        export_array_to_image(cropped_p, f'./DATA/P_{input_filename}/P_{key}.tif')
        export_array_to_image(cropped_pan, f'./DATA/PAN_{input_filename}/PAN_{key}.tif')
        print(key)

if __name__ == "__main__":
    main()
