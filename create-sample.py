import rasterio
import numpy as np
import uuid
from rasterio.transform import from_origin
from rasterio.enums import Resampling
from PIL import Image
from skimage import exposure

# Create a function to read 4 bands and 1 bands image. Store as numpy array
def read_images(multispectral, panchromatic, pansharpen):
    
    with rasterio.open(panchromatic) as src_p:
        panchromatic_image = src_p.read()
        panchromatic_image = np.transpose(panchromatic_image, (1, 2, 0))
    
    with rasterio.open(multispectral) as src_ms:
        #multispectral_image = src_ms.read()
        multispectral_image = src_ms.read(
            out_shape=(src_ms.count, src_p.height, src_p.width),
            resampling=Resampling.nearest
        )
        #multispectral_image = multispectral_image.astype(np.uint8)
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

    # Create a GeoTIFF file
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


if __name__ == "__main__":
    multispectral_path = "./SPOT_RENDER/MS_1/MS_1.tif"
    panchromatic_path = "./SPOT_RENDER/P_1/P_1.tif"
    pansharpen_path = "./SPOT_RENDER/PAN_1/PAN_1.tif"
    window_size = (256,256)

    multispectral_array, panchromatic_array, pansharpen_array = read_images(multispectral_path, panchromatic_path, pansharpen_path)
    for _, coordinates in sliding_window(panchromatic_array, window_size):
        start_x, start_y, end_x, end_y = coordinates
        cropped_ms = multispectral_array[start_y:end_y, start_x:end_x, :]
        cropped_p = panchromatic_array[start_y:end_y, start_x:end_x,:]
        cropped_pan = pansharpen_array[start_y:end_y, start_x:end_x,:]
       # print(cropped_ms.shape, type(cropped_p))
        key = generate_random_key_value()
        export_array_to_image(cropped_ms, f'./DATA/MS/MS_{key}.tif')
        export_array_to_image(cropped_p, f'./DATA/P/P_{key}.tif')
        export_array_to_image(cropped_pan, f'./DATA/PAN/PAN_{key}.tif')
        print(key)