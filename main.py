import cv2
import easyocr
import pandas as pd
import os
from datetime import datetime
import xml.etree.ElementTree as ET

class RomanianTranslator:
    CYRILLIC_TO_LATIN_MAP = {
        'А': 'A', 'Б': 'B', 'В': 'V', 'Г': 'G', 'Д': 'D',
        'Е': 'E', 'Ё': 'Io', 'Ж': 'Jh', 'З': 'Z', 'И': 'I',
        'Й': 'Y', 'К': 'K', 'Л': 'L', 'М': 'M', 'Н': 'N',
        'О': 'O', 'П': 'P', 'Р': 'R', 'С': 'S', 'Т': 'T',
        'У': 'U', 'Ф': 'F', 'Х': 'H', 'Ц': 'Ts', 'Ч': 'Ci',
        'Ш': 'Și', 'Щ': 'Șci', 'Ъ': '', 'Ы': 'Y', 'Ь': '',
        'Э': 'E', 'Ю': 'Iu', 'Я': 'Ia',
        'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd',
        'е': 'e', 'ё': 'io', 'ж': 'jh', 'з': 'z', 'и': 'i',
        'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm', 'н': 'n',
        'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't',
        'у': 'u', 'ф': 'f', 'х': 'h', 'ц': 'ts', 'ч': 'ci',
        'ш': 'și', 'щ': 'șci', 'ъ': '', 'ы': 'y', 'ь': '',
        'э': 'e', 'ю': 'iu', 'я': 'ia'
    }

    @classmethod
    def translate(cls, text):
        return ''.join(cls.CYRILLIC_TO_LATIN_MAP.get(char, char) for char in text)

class MapProcessor:
    def __init__(self, image_path, svg_path):
        self.image_path = image_path
        self.svg_path = svg_path
        self.reader = easyocr.Reader(['ru', 'en'])
        self.results_dir = self._create_results_dir()
        self.translator = RomanianTranslator()

    def _create_results_dir(self):
        base_dir = os.path.dirname(self.image_path)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_dir = os.path.join(base_dir, f"results_{timestamp}")
        os.makedirs(results_dir, exist_ok=True)
        return results_dir

    def load_image(self):
        self.original_image = cv2.imread(self.image_path)
        if self.original_image is None:
            raise Exception("Nu s-a putut încărca imaginea")
        self.gray_image = cv2.cvtColor(self.original_image, cv2.COLOR_BGR2GRAY)
        return self.gray_image

    def process_map_points(self):
        results = self.reader.readtext(self.gray_image, paragraph=False)
        processed_results = []
        for idx, (coords, text, conf) in enumerate(results, 1):
            center_x = int(sum(coord[0] for coord in coords) / 4)
            center_y = int(sum(coord[1] for coord in coords) / 4)
            translated_text = self.translator.translate(text)
            result = {
                'id': idx,
                'text_original': text,
                'text_romanian': translated_text,
                'confidence': conf,
                'coordinates': {'x': center_x, 'y': center_y}
            }
            processed_results.append(result)
        return processed_results

    def place_points_on_svg(self, processed_results):
        try:
            # Încărcare fișier SVG
            tree = ET.parse(self.svg_path)
            root = tree.getroot()
            ET.register_namespace('', 'http://www.w3.org/2000/svg')

            # Dimensiuni SVG
            svg_width = float(root.attrib.get('width', '1000').replace('px', ''))
            svg_height = float(root.attrib.get('height', '1000').replace('px', ''))

            # Dimensiuni imagine
            img_height, img_width = self.gray_image.shape[:2]

            # Calculare rapoarte de scalare
            scale_x = svg_width / img_width
            scale_y = svg_height / img_height

            # Adăugare puncte în SVG
            for result in processed_results:
                # Ajustare coordonate
                x_img, y_img = result['coordinates']['x'], result['coordinates']['y']
                x_svg = int(x_img * scale_x)
                y_svg = int(y_img * scale_y)

                # Text tradus și ID
                text_ro = result['text_romanian']


                # Creare cerc SVG
                circle = ET.Element('circle', {
                    'cx': str(x_svg),
                    'cy': str(y_svg),
                    'r': '5',
                    'fill': 'red',
                    'stroke': 'black',
                    'stroke-width': '1'
                })

                # Creare text SVG
                text = ET.Element('text', {
                    'x': str(x_svg + 10),
                    'y': str(y_svg - 10),
                    'font-size': '12',
                    'fill': 'black'
                })
                text.text = f" {text_ro}"

                # Adăugare elemente la SVG
                root.append(circle)
                root.append(text)

            # Salvare fișier SVG modificat
            output_svg_path = os.path.join(self.results_dir, "map_with_points.svg")
            tree.write(output_svg_path, encoding='utf-8', xml_declaration=True)
            print(f"Harta SVG cu punctele a fost salvată în: {output_svg_path}")
        except Exception as e:
            print(f"Eroare la procesarea fișierului SVG: {str(e)}")

    def process(self):
        print("1. Încărcare și preprocesare imagine...")
        self.load_image()
        print("2. Procesare puncte și text...")
        results = self.process_map_points()
        print("3. Plasare puncte pe hartă SVG...")
        self.place_points_on_svg(results)
        print("Procesare completă!")
        return results


def main():
    image_path = r'C:\Users\user\PycharmProjects\pythonProject12\Harta 57.tif'
    svg_path = r'C:\Users\user\PycharmProjects\pythonProject12\MD.svg'
    processor = MapProcessor(image_path, svg_path)
    try:
        processor.process()
    except Exception as e:
        print(f"Eroare la procesare: {str(e)}")

if __name__ == "__main__":
    main()
