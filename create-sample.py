import rasterio
import numpy as np
from rasterio.transform import from_origin
from rasterio.enums import Resampling
from rasterio.windows import Window

def read_images(multispectral, panchromatic):
    with rasterio.open(multispectral) as src:
        multispectral_image = src.read()

    with rasterio.open(panchromatic) as src:
        panchromatic_image = src.read()  

    return multispectral_image, panchromatic_image

def save_tif_from_array(array, output_path, window_size):
    height, width = array.shape[1:]

    for i in range(0, height, window_size):
        for j in range(0, width, window_size):
            window = Window(j, i, min(window_size, width - j), min(window_size, height - i))

            windowed_array = array[:, window.row_off:window.row_off + window.height, window.col_off:window.col_off + window.width]

            transform = from_origin(window.col_off, window.row_off, window_size, window_size)

            with rasterio.open(output_path, 'w', driver='GTiff', height=window.height, width=window.width, count=array.shape[0], dtype=array.dtype, crs='+proj=latlong', transform=transform) as dst:
                dst.write(windowed_array)


multispectral_path = "IMG_PHR1A_MS_202310170327506_ORT_265b5d70-f3ff-4f64-cf82-62111555cf84-001_R1C1.TIF"
panchromatic_path = "IMG_PHR1A_P_202310170327506_ORT_265b5d70-f3ff-4f64-cf82-62111555cf84-002_R1C1.TIF"

multispectral_array, panchromatic_array = read_images(multispectral_path, panchromatic_path)

window_size = 256
save_tif_from_array(multispectral_array, "output_multispectral.tif", window_size)
save_tif_from_array(panchromatic_array, "output_panchromatic.tif", window_size)