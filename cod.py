import os
from itertools import product
from PIL import Image
import streamlit as st
from io import BytesIO
import zipfile
import random
import time

st.set_page_config(page_title="nft maker", layout="wide", page_icon="chart_with_upwards_trend")

def random_color():
    return tuple(random.randint(0, 255) for _ in range(3))

def darker_color(color, factor=0.7):
    return tuple(int(c * factor) for c in color)

def color_similarity(color1, color2, threshold=50):
    return sum((c1 - c2) ** 2 for c1, c2 in zip(color1, color2)) < threshold**2

def resize_image(image, size=(512, 512)):
    return image.resize(size, Image.NEAREST)

def create_color_variations(img, variations=5, avoid_colors=None, similarity_threshold=50):
    """Create color variations for an input image."""
    data = img.load()
    width, height = img.size
    retain_colors = [(229, 170, 122), (207, 153, 112)]  
    avoid_colors = avoid_colors or []

    variation_images = []
    for _ in range(variations):
        base_color = random_color()

        while any(color_similarity(base_color, avoid, similarity_threshold) for avoid in avoid_colors):
            base_color = random_color()

        output_img = Image.new("RGBA", img.size)
        output_data = output_img.load()

        for y in range(height):
            for x in range(width):
                pixel = data[x, y]
                if pixel[3] == 0:  
                    output_data[x, y] = (0, 0, 0, 0)
                elif pixel[:3] == (0, 0, 0):  
                    output_data[x, y] = (0, 0, 0, 255)
                elif pixel[:3] == (255, 255, 255):  
                    output_data[x, y] = base_color + (255,)
                elif pixel[:3] in retain_colors:
                    output_data[x, y] = pixel
                else:
                    output_data[x, y] = darker_color(base_color) + (255,)

        variation_images.append(output_img)
    return variation_images

def save_images_to_zip(images, zip_name="output_images.zip"):
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zip_file:
        for idx, img in enumerate(images):
            img_bytes = BytesIO()
            img.save(img_bytes, format="PNG")
            zip_file.writestr(f"combined_{idx + 1}.png", img_bytes.getvalue())
    zip_buffer.seek(0)
    return zip_buffer


st.title("nft maker")

with st.expander("📄 Docs: How to Create Templates"):
    st.write("""
    ### Guidelines for Creating Templates
    To ensure your templates work well with the generator, follow these instructions:
    
    1. **Image Format**:
        - Templates must be in `.PNG` format to support transparency.
        - Use RGBA mode for the best results.

    2. **Base Template**:
        - The base template is the background of the final image.
        - Use **black** `(0, 0, 0)` for areas that remain unchanged.
        - Use **white** `(255, 255, 255)` for areas to be recolored with random colors.
        - Use **gray** `(70, 70, 70)` for areas to be recolored with a slightly darker version of the random color.
        - Avoid excessive use of black, white, or gray to allow for better variation.

    3. **Accessory Template**:
        - The accessory template is placed on top of the base.
        - Design these with transparency where the base should show through.
        - Use colors sparingly, as they are recolored randomly in each variation.

    4. **Size**:
        - Templates are resized to **512x512 pixels** for consistency.
        - Design your templates with a square aspect ratio to avoid distortion.

    5. **Retain Specific Colors**:
        - Colors `(229, 170, 122)` and `(207, 153, 112)` are retained by default (e.g., for skin tones).
        - These colors are not modified during the recoloring process.

    6. **Avoid Similar Background Colors**:
        - Background colors similar to the retained colors are filtered out.
        - Ensure good contrast between design elements.

    ### Color Usage Summary
    - **Black (#000000)**: Areas that remain unchanged.
    - **White (#FFFFFF)**: Areas recolored with a random color.
    - **Gray (#464646)**: Areas recolored with a slightly darker version of the random color.

    ### Example Workflow
    1. Create a **base template** with white areas to recolor, black areas to preserve, and gray areas for slightly darker recoloring.
    2. Design an **accessory template** with transparent areas where the base should be visible.
    3. Upload both templates, configure the number of variations, and generate the combinations.
    """)



st.header("1. Upload Templates")
base_file = st.file_uploader("Upload Base Template (.PNG only)", type="png")
accessory_file = st.file_uploader("Upload Accessory Template (.PNG only)", type="png")

st.header("2. Configure Variations")
num_base_variations = st.slider("Number of Base Color Variations", 1, 100, 5)
num_accessory_variations = st.slider("Number of Accessory Color Variations", 1, 100, 5)
st.write("#### Total output: ", num_base_variations*num_accessory_variations, " images")

if st.button("Generate"):
    if not base_file or not accessory_file:
        st.error("Please upload both base and accessory templates!")
    else:
        start_time = time.time() 

        
        base_img = resize_image(Image.open(base_file).convert("RGBA"))
        accessory_img = resize_image(Image.open(accessory_file).convert("RGBA"))

        
        avoid_colors = [(229, 170, 122), (207, 153, 112)]
        base_variations = create_color_variations(base_img, num_base_variations, avoid_colors)
        accessory_variations = create_color_variations(accessory_img, num_accessory_variations, avoid_colors)

        
        combined_images = []
        for base, accessory in product(base_variations, accessory_variations):
            combined = Image.alpha_composite(base, accessory)
            combined_images.append(combined)

        
        end_time = time.time()  
        total_time = end_time - start_time

        st.success(f"Generated {len(combined_images)} valid combinations in {total_time:.2f} seconds!")
        zip_buffer = save_images_to_zip(combined_images)
        st.download_button(
            "Download All Combinations as ZIP",
            data=zip_buffer,
            file_name="combined_images.zip",
            mime="application/zip"
        )
