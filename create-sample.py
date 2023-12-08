import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox
from functools import partial
import os
import rasterio
import numpy as np
import uuid
from rasterio.transform import from_origin
from rasterio.enums import Resampling
from PIL import Image
from skimage import exposure
import subprocess

class ImageProcessorApp:
    def __init__(self, master):
        self.master = master
        master.title("Image Pansharpen")

        # File Paths
        self.multispectral_path = ""
        self.panchromatic_path = ""
        self.pansharpen_path = ""

        # Default Window Size
        self.default_window_size = (256, 256)
        self.window_size_var = tk.StringVar(value=f"{self.default_window_size[0]}x{self.default_window_size[1]}")

        # Default Export Folder
        self.export_folder_var = tk.StringVar(value="")

        # Create and place widgets
        self.create_widgets()

    def create_widgets(self):
        # Multispectral Input
        self.create_input_section("Multispectral", self.set_multispectral_path)

        # Panchromatic Input
        self.create_input_section("Panchromatic", self.set_panchromatic_path)

        # Pansharpen Input
        self.create_input_section("Pansharpen", self.set_pansharpen_path)

        # Window Size Input
        window_size_frame = tk.Frame(self.master, pady=5)
        window_size_frame.pack()

        window_size_label = tk.Label(window_size_frame, text="Window Size:")
        window_size_label.grid(row=0, column=0, padx=5)

        window_size_entry = tk.Entry(window_size_frame, textvariable=self.window_size_var)
        window_size_entry.grid(row=0, column=1, padx=5)

        # Export Folder Input
        export_folder_frame = tk.Frame(self.master, pady=5)
        export_folder_frame.pack()

        export_folder_label = tk.Label(export_folder_frame, text="Export Folder:")
        export_folder_label.grid(row=0, column=0, padx=5)

        export_folder_entry = tk.Entry(export_folder_frame, textvariable=self.export_folder_var)
        export_folder_entry.grid(row=0, column=1, padx=5)

        export_folder_button = tk.Button(export_folder_frame, text="Browse", command=self.browse_export_folder)
        export_folder_button.grid(row=0, column=2, padx=5)

        # Submit Button
        submit_button = tk.Button(self.master, text="Submit", command=self.process_images)
        submit_button.pack(pady=10)

    def create_input_section(self, label_text, set_path_function):
        frame = tk.Frame(self.master, pady=5)
        frame.pack()

        label = tk.Label(frame, text=label_text + " Input:")
        label.grid(row=0, column=0, padx=5)

        entry = tk.Entry(frame, state="disabled", width=30)
        entry.grid(row=0, column=1, padx=5)

        browse_button = tk.Button(frame, text="Browse", command=partial(self.browse_file, set_path_function, entry))
        browse_button.grid(row=0, column=2, padx=5)

    def browse_file(self, set_path_function, entry_widget):
        file_path = filedialog.askopenfilename(title=f"Upload Image", filetypes=[("All files", "*.*")])
        set_path_function(file_path)
        entry_widget.config(state="normal")
        entry_widget.delete(0, tk.END)
        entry_widget.insert(0, file_path)
        entry_widget.config(state="disabled")

    def set_multispectral_path(self, path):
        self.multispectral_path = path

    def set_panchromatic_path(self, path):
        self.panchromatic_path = path

    def set_pansharpen_path(self, path):
        self.pansharpen_path = path

    def browse_export_folder(self):
        folder_path = filedialog.askdirectory(title="Select Export Folder")
        self.export_folder_var.set(folder_path)

    def process_images(self):
        # Get user-defined window size or use default
        try:
            user_defined_size = tuple(map(int, self.window_size_var.get().split('x')))
        except ValueError:
            # Use default if the user input is not valid
            user_defined_size = self.default_window_size

        # Get user-defined export folder or use current working directory
        export_folder = self.export_folder_var.get()
        if not export_folder:
            export_folder = os.getcwd()

        if all([self.multispectral_path, self.panchromatic_path, self.pansharpen_path]):
            multispectral_array, panchromatic_array, pansharpen_array = self.read_images(self.multispectral_path, self.panchromatic_path, self.pansharpen_path)

            for _, coordinates in self.sliding_window(panchromatic_array, user_defined_size):
                start_x, start_y, end_x, end_y = coordinates
                cropped_ms = multispectral_array[start_y:end_y, start_x:end_x, :]
                cropped_p = panchromatic_array[start_y:end_y, start_x:end_x, :]
                cropped_pan = pansharpen_array[start_y:end_y, start_x:end_x, :]
                key = self.generate_random_key_value()

                input_filename = os.path.splitext(os.path.basename(self.multispectral_path))[0]

                export_path_ms = os.path.join(export_folder, f'MS_{input_filename}/MS_{key}.tif')
                export_path_p = os.path.join(export_folder, f'P_{input_filename}/P_{key}.tif')
                export_path_pan = os.path.join(export_folder, f'PAN_{input_filename}/PAN_{key}.tif')

                self.export_array_to_image(cropped_ms, export_path_ms)
                self.export_array_to_image(cropped_p, export_path_p)
                self.export_array_to_image(cropped_pan, export_path_pan)

                print(f"Processed image with key: {key}. Exported to {export_folder}")

                subprocess.run(["echo", f"Processed image with key: {key}. Exported to {export_folder}"])

            subprocess.run(["echo", "Proses selesai!"])
            # Show popup message
            messagebox.showinfo("Selesai", "Proses selesai!")

            # Reset file paths, window size, and export folder for new uploads
            self.reset_application()
        else:
            messagebox.showerror("Error", "Mohon pilih semua gambar input.")

    def reset_application(self):
        # Reset all file paths
        self.multispectral_path = ""
        self.panchromatic_path = ""
        self.pansharpen_path = ""

        # Reset window size to default
        self.window_size_var.set(f"{self.default_window_size[0]}x{self.default_window_size[1]}")

        # Reset export folder to empty
        self.export_folder_var.set("")

        # Clear entries
        for entry_widget in self.master.winfo_children():
            if isinstance(entry_widget, tk.Entry):
                entry_widget.config(state="normal")
                entry_widget.delete(0, tk.END)
                entry_widget.config(state="disabled")

    def read_images(self, multispectral, panchromatic, pansharpen):
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

    def sliding_window(self, image, window_size):
        height, width = image.shape[:2]
        window_width, window_height = window_size

        for y in range(0, height - window_height + 1, window_height):
            for x in range(0, width - window_width + 1, window_width):
                window = image[y:y + window_height, x:x + window_width]
                yield window, (x, y, x + window_width, y + window_height)

    def generate_random_key_value(self):
        # Generate a random key using UUID
        random_key = str(uuid.uuid4())
        return random_key

    def export_array_to_image(self, array, output_path):
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

def main():
    root = tk.Tk()
    app = ImageProcessorApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
