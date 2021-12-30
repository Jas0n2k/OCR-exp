import easyocr
import fitz
import os

img_dir = "output_images"

print(fitz.__doc__)
if not tuple(map(int, fitz.version[0].split("."))) >= (1, 18, 18):
    raise SystemExit("require PyMuPDF v1.18.18+")


def extract_pix(pdf_doc, img_item):
    xref = img_item[0]
    # soft_mask = img_item[1]

    if "/ColorSpace" in pdf_doc.xref_object(xref, compressed=True):
        pix = fitz.Pixmap(pdf_doc, xref)
        pix = fitz.Pixmap(fitz.csRGB, pix)
        return {  # create dictionary expected by caller
            "ext": "png",
            "colorspace": 3,
            "image": pix.tobytes("png"),
        }
    return pdf_doc.extract_image(xref)


def convert_scanned_pdf(pdf_doc, pdf_output_dir, mode="rawdata"):
    _img_list = []
    # get image from each page
    with fitz.open() as f_pdf:
        for page_index in range(len(pdf_doc)):
            print("Extracting Image from Page %i" % (page_index + 1))
            for page_img in pdf_doc.get_page_images(page_index):
                if page_img[-2] == 'X2':
                    _img = extract_pix(pdf_doc, page_img)
                    _img_rawdata = _img["image"]
                    if mode == 'pdf':
                        _img_opened = fitz.open(stream=_img["image"], filetype=_img["ext"])
                        _img_rect = _img_opened[0].rect
                        _pdf_byte_stream = _img_opened.convert_to_pdf()
                        _img_opened.close()
                        _img_pdf = fitz.open("pdf", _pdf_byte_stream)
                        _page = f_pdf.new_page(width=_img_rect.width, height=_img_rect.height)
                        _page.show_pdf_page(_img_rect, _img_pdf)
                    if mode == 'rawdata' or mode == 'pdf':
                        _img_list.append(_img_rawdata)
                        continue
                    if mode == 'path':
                        img_file = os.path.join(pdf_output_dir,
                                                "%s-Page%03i.%s" % (pdf_doc.name, page_index, _img["ext"]))
                        with open(img_file, 'wb') as f_out:
                            f_out.write(_img_rawdata)
                            f_out.close()
                            _img_list.append(img_file)
        if mode == 'pdf':
            f_pdf.save(os.path.join(pdf_output_dir, "%s - converted.pdf" % pdf_doc.name))
    return _img_list


def easy_ocr_handler(_doc):
    _pdf_output_dir = os.path.join(img_dir, _doc.name)
    if not os.path.exists(_pdf_output_dir):
        os.makedirs(_pdf_output_dir)
    reader = easyocr.Reader(['ch_sim'])
    image_list = convert_scanned_pdf(_doc, _pdf_output_dir)
    result = []
    for i in range(len(image_list)):
        print('OCR Processing Page %i' % (i + 1))
        ocr_res = reader.readtext(image_list[i], detail=0)
        result.append('\n'.join(ocr_res))

    with open(os.path.join(_pdf_output_dir, "%s - Output.txt" % _doc.name), 'w', encoding='utf-8') as f_text_res:
        f_text_res.write(''.join(result))


if __name__ == "__main__":
    with fitz.open('Test.PDF') as doc:
        easy_ocr_handler(doc)
        # convert_scanned_pdf(doc, mode='pdf')
