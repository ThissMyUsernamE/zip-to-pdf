# ZIP to Searchable PDF

A small Python command-line tool that extracts image files from ZIP archives,
runs OCR with Tesseract, and combines the pages into searchable PDF files.
It searches inside nested folders in each archive and processes every ZIP file
in the `source/` directory.

> This project was vibe-coded with AI assistance.

## Requirements

- Python 3.10 or newer
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract)
- Tesseract language data for the language(s) you select:
  - Slovak: `slk`
  - English: `eng`
  - Czech: `ces`
- Python packages listed in [`requirements.txt`](requirements.txt)

For example, on Ubuntu or Debian:

```bash
sudo apt update
sudo apt install tesseract-ocr tesseract-ocr-slk tesseract-ocr-eng tesseract-ocr-ces
```

The exact package names and installation steps may differ by operating system.
Confirm Tesseract can find the required language data with:

```bash
tesseract --list-langs
```

## Setup

Clone the repository, create a virtual environment, and install the Python
dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

On Windows, activate the environment with:

```powershell
.venv\Scripts\Activate.ps1
```

## Usage

1. Put one or more `.zip` archives in the `source/` directory.
2. Run the script from the project directory:

   ```bash
   python script.py
   ```

3. Choose an OCR language when prompted:
   - Slovak
   - English
   - Czech
   - Slovak + English + Czech

For each archive named `example.zip`, the script creates `example_ocr.pdf`
next to it in `source/`. Existing matching output PDFs are skipped. Archives
that are invalid or contain no supported images are reported and skipped.

Supported image formats are JPG, JPEG, PNG, TIFF, TIF, and BMP. The script
searches recursively through folders inside each ZIP archive. OCR progress is
shown on a single updating terminal line; failed pages are reported after
processing.

## Configuration

At the top of `script.py`, set `CORES_TO_USE` to the desired maximum number of
parallel OCR workers. The script will not request more workers than the CPU
count reported by Python.

## Notes

- OCR quality and processing time depend on the image resolution, quality, and
  selected language data.
- The script skips an archive whenever its matching `_ocr.pdf` already exists.
  Remove that output PDF if you want to process the archive again.
- Only add ZIP archives you trust.

## License

This project is licensed under the MIT License. See [`LICENSE`](LICENSE) for
the full text.
