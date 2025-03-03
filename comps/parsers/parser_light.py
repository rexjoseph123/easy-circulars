import pdfplumber
import pandas as pd
import re
from collections import defaultdict
from comps.parsers.table import Table
from comps.parsers.text import Text

def extract_text_and_tables(pdf_path):
    text_content = []
    tables = []

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_tables = page.find_tables()
            table_bboxes = [table.bbox for table in page_tables]
        
            extracted_text = []
            lines_dict = defaultdict(list)
            words = page.extract_words()
            for word in words:
                word_bbox = (float(word['x0']), float(word['top']), float(word['x1']), float(word['bottom']))
                
                inside_table = any(
                    table_bbox[0] <= word_bbox[0] <= table_bbox[2] and
                    table_bbox[1] <= word_bbox[1] <= table_bbox[3]
                    for table_bbox in table_bboxes
                )

                if not inside_table:
                    extracted_text.append(word['text'])
                    
                lines_dict[word["top"]].append(word["text"])

            page_content = " ".join(extracted_text)

            match = re.search(r'^(.*?)(\s*\d+)\s*$', page_content)

            if match:
                cleaned_content = match.group(1).strip()
                if cleaned_content:
                    text_obj = Text(cleaned_content, None)
                    text_content.append(text_obj)
            else:
                text_obj = Text(page_content, None)
                text_content.append(text_obj)

            sorted_lines = sorted(lines_dict.items(), key=lambda x: x[0])

            for table_bbox, table in zip(table_bboxes, page.extract_tables()):
                heading = None
                above_lines = [text for top, text in sorted_lines if top < table_bbox[1]]
                
                heading_lines = above_lines[-2:] if above_lines else []
                
                if heading_lines:
                    heading = " ".join(word for line in heading_lines for word in line)

                df = pd.DataFrame(table)
                
                table_md = df.to_markdown(index=False)

                table_obj = Table(table_md, heading, None)

                tables.append(table_obj)
    return text_content, tables       