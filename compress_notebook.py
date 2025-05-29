import nbformat
from nbformat.v4 import new_markdown_cell
import os
from base64 import b64decode
from PIL import Image
from io import BytesIO

NOTEBOOK_PATH = "transforms_illustrations.ipynb"
OUTPUT_NOTEBOOK = "transforms_illustrations_compressed.ipynb"
IMAGE_DIR = "notebook_images"
MAX_SIZE_MB = 3  # target max notebook size in megabytes

os.makedirs(IMAGE_DIR, exist_ok=True)

with open(NOTEBOOK_PATH, "r", encoding="utf-8") as f:
    nb = nbformat.read(f, as_version=4)

img_count = 0
new_cells = []
compressed_cells_indices = []  # keep track of code+markdown pairs for possible removal

for cell in nb.cells:
    if cell.cell_type == "code" and "outputs" in cell:
        compressed_this_cell = False
        for output in cell.outputs:
            if output.output_type == "display_data" and ("image/png" in output.data or "image/jpeg" in output.data):
                # Decode image data
                if "image/png" in output.data:
                    img_data = b64decode(output.data["image/png"])
                else:
                    img_data = b64decode(output.data["image/jpeg"])

                img = Image.open(BytesIO(img_data)).convert("RGB")

                img_path = os.path.join(IMAGE_DIR, f"img_{img_count}.jpg")
                img.save(img_path, format="JPEG", quality=50)

                rel_path = os.path.relpath(img_path, os.path.dirname(OUTPUT_NOTEBOOK))
                md_cell = new_markdown_cell(f"![output image]({rel_path})")

                # Clear outputs in code cell
                cell.outputs = []

                # Append compressed code cell and markdown image
                new_cells.append(cell)
                new_cells.append(md_cell)
                compressed_cells_indices.append(len(new_cells)-2)  # index of code cell in new_cells

                img_count += 1
                compressed_this_cell = True
                break  # one output per cell processed
        if not compressed_this_cell:
            new_cells.append(cell)
    else:
        new_cells.append(cell)

# Assign new cells to notebook
nb.cells = new_cells

# Save notebook
with open(OUTPUT_NOTEBOOK, "w", encoding="utf-8") as f_out:
    nbformat.write(nb, f_out)

# Check size and remove last compressed cells if over limit
current_size = os.path.getsize(OUTPUT_NOTEBOOK) / (1024 * 1024)
while current_size > MAX_SIZE_MB and compressed_cells_indices:
    # Remove last compressed code cell and markdown image cell
    idx = compressed_cells_indices.pop()
    # Remove code cell and following markdown cell
    del nb.cells[idx:idx+2]

    with open(OUTPUT_NOTEBOOK, "w", encoding="utf-8") as f_out:
        nbformat.write(nb, f_out)

    current_size = os.path.getsize(OUTPUT_NOTEBOOK) / (1024 * 1024)

print(f"Compressed notebook saved to: {OUTPUT_NOTEBOOK}")
print(f"Final size: {current_size:.2f} MB")
