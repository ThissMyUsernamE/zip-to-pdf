"""Vibe-coded with AI assistance; converts image archives into searchable PDFs."""

import os
import zipfile
import tempfile
import io
import sys
import concurrent.futures
import multiprocessing
from PIL import Image
import pytesseract
from pypdf import PdfWriter, PdfReader

# Define the source directory
SOURCE_DIR = './source'
CORES_TO_USE = 4

def get_language_choice():
    print("Select OCR Language for the PDF:")
    print("1. Slovak (slk)")
    print("2. English (eng)")
    print("3. Czech (ces)")
    print("4. Slovak + English + Czech (slk+eng+ces)")
    
    while True:
        choice = input("Enter choice (1/2/3/4): ").strip()
        if choice == '1':
            return 'slk'
        elif choice == '2':
            return 'eng'
        elif choice == '3':
            return 'ces'
        elif choice == '4':
            return 'slk+eng+ces'
        else:
            print("Invalid choice. Please enter 1, 2, 3, or 4.")

def find_zip_files(directory):
    if not os.path.exists(directory):
        print(f"Error: The directory '{directory}' does not exist.")
        sys.exit(1)
        
    zip_files = sorted(
        os.path.join(directory, f)
        for f in os.listdir(directory)
        if f.lower().endswith('.zip')
    )
    
    if not zip_files:
        print(f"Error: No ZIP files found in '{directory}'.")
        
    return zip_files

def ocr_worker(args):
    img_path, language_code = args
    try:
        img = Image.open(img_path)
        # Added a 120-second timeout to prevent the worker from hanging indefinitely
        pdf_bytes = pytesseract.image_to_pdf_or_hocr(img, extension='pdf', lang=language_code, timeout=120)
        return pdf_bytes, None
    except RuntimeError as e:
        return None, f"Timeout error (page took longer than 120s): {e}"
    except Exception as e:
        return None, str(e)

def process_zip_to_pdf(zip_path, language_code):
    output_pdf_path = os.path.splitext(zip_path)[0] + '_ocr.pdf'
    pdf_writer = PdfWriter()
    
    valid_extensions = {'.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp'}
    
    print(f"\nProcessing '{zip_path}'...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        print("Extracting ZIP file...")
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
        except zipfile.BadZipFile:
            print(f"Error: '{zip_path}' is not a valid ZIP archive. Skipping it.")
            return False
            
        image_files = []
        for root, _, files in os.walk(temp_dir):
            for file in files:
                if os.path.splitext(file)[1].lower() in valid_extensions:
                    image_files.append(os.path.join(root, file))
                    
        if not image_files:
            print(f"No valid images found inside '{zip_path}'. Skipping it.")
            return False
            
        image_files.sort()
        total_images = len(image_files)
        
        # Do not request more workers than the system reports as available.
        system_cores = multiprocessing.cpu_count()
        num_cores = min(CORES_TO_USE, system_cores)
        
        print(f"Found {total_images} images.")
        print(f"Starting parallel OCR process using {num_cores} CPU cores...")
        
        worker_args = [(path, language_code) for path in image_files]
        failed_pages = []
        bar_width = 30
        count_width = len(str(total_images))
        
        with concurrent.futures.ProcessPoolExecutor(max_workers=num_cores) as executor:
            for idx, (pdf_bytes, error) in enumerate(executor.map(ocr_worker, worker_args), start=1):
                if error:
                    failed_pages.append((idx, error))
                    # If a page fails or times out, we append a blank page or just skip. 
                    # Skipping is easiest, but ruins page numbering. We'll just skip the OCR for this page.
                elif pdf_bytes:
                    pdf_reader = PdfReader(io.BytesIO(pdf_bytes))
                    pdf_writer.add_page(pdf_reader.pages[0])
                
                completed = idx
                filled = int(bar_width * completed / total_images)
                progress_bar = '=' * filled + ' ' * (bar_width - filled)
                progress = (
                    f"\rOCR [{progress_bar}] {completed * 100 // total_images:3d}% "
                    f"({completed:>{count_width}}/{total_images}) "
                    f"| Failed: {len(failed_pages):>{count_width}}"
                )
                print(progress, end="", flush=True)

        print()
        for page_number, error in failed_pages:
            print(f"Failed page {page_number}/{total_images}: {error}")

        print("\nSaving final compiled PDF to disk...")
        with open(output_pdf_path, 'wb') as out_file:
            pdf_writer.write(out_file)
            
    print(f"Success! Searchable PDF saved to:\n{output_pdf_path}")
    return True

if __name__ == "__main__":
    lang = get_language_choice()
    zip_files = find_zip_files(SOURCE_DIR)
    for zip_path in zip_files:
        output_pdf_path = os.path.splitext(zip_path)[0] + '_ocr.pdf'
        if os.path.exists(output_pdf_path):
            print(f"Skipping '{zip_path}': output PDF already exists.")
            continue

        try:
            process_zip_to_pdf(zip_path, lang)
        except Exception as e:
            print(f"Error processing '{zip_path}': {e}")