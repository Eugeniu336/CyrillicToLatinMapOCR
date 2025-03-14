import cv2
import easyocr
import pandas as pd
import os
from datetime import datetime
import numpy as np


class RomanianTranslator:
    """Traducător avansat din chirilică în română"""

    CYRILLIC_TO_LATIN_MAP = {
        # Caractere de bază
        'А': 'A', 'Б': 'B', 'В': 'V', 'Г': 'G', 'Д': 'D',
        'Е': 'E', 'Ё': 'Io', 'Ж': 'Jh', 'З': 'Z', 'И': 'I',
        'Й': 'Y', 'К': 'K', 'Л': 'L', 'М': 'M', 'Н': 'N',
        'О': 'O', 'П': 'P', 'Р': 'R', 'С': 'S', 'Т': 'T',
        'У': 'U', 'Ф': 'F', 'Х': 'H', 'Ц': 'Ts', 'Ч': 'Ci',
        'Ш': 'Și', 'Щ': 'Șci', 'Ъ': '', 'Ы': 'Y', 'Ь': '',
        'Э': 'E', 'Ю': 'Iu', 'Я': 'Ia',

        # Caractere mici
        'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd',
        'е': 'e', 'ё': 'io', 'ж': 'jh', 'з': 'z', 'и': 'i',
        'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm', 'н': 'n',
        'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't',
        'у': 'u', 'ф': 'f', 'х': 'h', 'ц': 'ts', 'ч': 'ci',
        'ш': 'și', 'щ': 'șci', 'ъ': '', 'ы': 'y', 'ь': '',
        'э': 'e', 'ю': 'iu', 'я': 'ia'
    }

    # Dicționar specializat pentru traduceri specifice
    SPECIAL_TRANSLATIONS = {
        'тынэр': 'tanar',  # traducere corectă pentru "tânăr"
        'тинер': 'tanar',  # variație de scriere
        'тынар': 'tanar',  # altă variantă
        'режиуня': 'regiune',
        'цинутул': 'ținutul',
        'тинерi': 'tineri',
        'тынерi': 'tineri'
    }

    @classmethod
    def translate(cls, text):
        """Traducere avansată din chirilică în română"""
        # Verificăm mai întâi traducerile specializate
        lower_text = text.lower()
        for cyr_word, rom_word in cls.SPECIAL_TRANSLATIONS.items():
            if cyr_word in lower_text:
                text = text.replace(cyr_word, rom_word)

        # Conversie caracter cu caracter pentru restul textului
        translated = ''.join(cls.CYRILLIC_TO_LATIN_MAP.get(char, char) for char in text)

        # Curățare și normalizare
        translated = translated.replace('  ', ' ').strip()

        return translated

    @classmethod
    def clean_text(cls, text):
        """Curățare text pentru a elimina caractere și simboluri nedorite"""
        # Păstrează doar caracterele alfanumerice, spațiile și semnele de punctuație de bază
        import re
        return re.sub(r'[^a-zA-Z0-9\s\.\,\;\:\-]', '', text)


class MapProcessor:
    def __init__(self, image_path):
        self.image_path = image_path
        self.reader = easyocr.Reader(['ru', 'en'])
        self.results_dir = self._create_results_dir()
        self.debug_mode = True
        self.translator = RomanianTranslator()

    def _create_results_dir(self):
        """Creează directorul pentru rezultate"""
        base_dir = os.path.dirname(self.image_path)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_dir = os.path.join(base_dir, f"results_{timestamp}")
        os.makedirs(results_dir, exist_ok=True)
        return results_dir

    def _save_debug_image(self, image, name):
        """Salvează imagini intermediare pentru debugging"""
        if self.debug_mode:
            debug_path = os.path.join(self.results_dir, f"debug_{name}.png")
            cv2.imwrite(debug_path, image)

    def load_image(self):
        """Încarcă și preprocesează imaginea"""
        self.original_image = cv2.imread(self.image_path)
        if self.original_image is None:
            raise Exception("Nu s-a putut încărca imaginea")

        # Conversie la grayscale
        self.gray_image = cv2.cvtColor(self.original_image, cv2.COLOR_BGR2GRAY)

        # Îmbunătățire contrast
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        self.enhanced_image = clahe.apply(self.gray_image)

        self._save_debug_image(self.enhanced_image, "enhanced")

        return self.enhanced_image


    def process_map_points(self):
        """Procesează punctele de pe hartă și textul asociat"""
        # Rulăm OCR pe imagine
        results = self.reader.readtext(
            self.enhanced_image,
            paragraph=False,
            height_ths=3,
            width_ths=3,
            contrast_ths=0.2
        )

        # Procesăm și organizăm rezultatele
        processed_results = []
        for idx, (coords, text, conf) in enumerate(results, 1):
            # Calculăm centrul
            center_x = int(sum(coord[0] for coord in coords) / 4)
            center_y = int(sum(coord[1] for coord in coords) / 4)

            # Traducem textul în română
            translated_text = self.translator.translate(text)

            result = {
                'id': idx,
                'text_original': text,
                'text_romanian': translated_text,
                'confidence': conf,
                'coordinates': {
                    'x': center_x,
                    'y': center_y,
                    'bbox': coords
                }
            }
            processed_results.append(result)

            # Afișăm în consolă pentru debugging
            if self.debug_mode:
                print(f"Punct {idx}: {text} -> {translated_text} ({center_x}, {center_y}) - conf: {conf:.2f}")

        return processed_results

    def create_translated_map(self, processed_results):
        """Creează o nouă hartă cu punctele traduse"""
        translated_map = self.original_image.copy()

        # Setăm parametri pentru text
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.5
        font_thickness = 1
        point_color = (0, 0, 255)  # Roșu pentru puncte
        text_color = (255, 255, 255)  # Alb pentru text
        text_bg_color = (0, 0, 0)  # Negru pentru fundal text

        for result in processed_results:
            # Coordonate punct
            x, y = result['coordinates']['x'], result['coordinates']['y']
            text_ro = result['text_romanian']
            id_text = str(result['id'])

            # Desenăm punct
            cv2.circle(translated_map, (x, y), 7, point_color, -1)

            # Calculăm dimensiunea textului pentru a crea un fundal
            (text_width, text_height), _ = cv2.getTextSize(
                f"{id_text}: {text_ro}", font, font_scale, font_thickness
            )

            # Fundal pentru text pentru lizibilitate
            cv2.rectangle(
                translated_map,
                (x + 10, y - text_height - 10),
                (x + text_width + 20, y),
                text_bg_color, -1
            )

            # Adăugăm text tradus cu ID
            cv2.putText(
                translated_map,
                f"{id_text}: {text_ro}",
                (x + 15, y - 5),
                font, font_scale,
                text_color,
                font_thickness
            )

        return translated_map

    def export_results(self, processed_results, visualization):
        """Exportă rezultatele în formate specificate"""
        # Salvăm vizualizarea
        viz_path = os.path.join(self.results_dir, "visualization_translated.png")
        cv2.imwrite(viz_path, visualization)

        # Exportăm în CSV
        csv_path = os.path.join(self.results_dir, "results.csv")
        df = pd.DataFrame(processed_results)
        df.to_csv(csv_path, index=False, encoding='utf-8')

        # Creăm raport detaliat
        report_path = os.path.join(self.results_dir, "report.txt")
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(f"Raport procesare hartă: {self.image_path}\n")
            f.write(f"Data procesării: {datetime.now()}\n")
            f.write(f"Număr total puncte detectate: {len(processed_results)}\n\n")


            for result in processed_results:
                f.write(f"ID: {result['id']}\n")
                f.write(f"Text original: {result['text_original']}\n")
                f.write(f"Text română: {result['text_romanian']}\n")
                f.write(f"Coordonate: ({result['coordinates']['x']}, {result['coordinates']['y']})\n")
                f.write(f"Încredere: {result['confidence']:.2f}\n")
                f.write("-" * 50 + "\n")

    def process(self):
        """Procesează întreaga hartă"""
        print("1. Încărcare și preprocesare imagine...")
        self.load_image()

        print("3. Procesare puncte și text...")
        results = self.process_map_points()

        print("4. Creare hartă cu traduceri...")
        translated_visualization = self.create_translated_map(results)

        print("5. Export rezultate...")
        self.export_results(results, translated_visualization)

        print(f"\nProcesare completă. Rezultatele au fost salvate în: {self.results_dir}")
        return results


def main():
    # Calea către imagine
    image_path = r'C:\Users\user\PycharmProjects\pythonProject12\Harta 10 bin.tif'

    # Inițializare și rulare processor
    processor = MapProcessor(image_path)
    try:
        results = processor.process()
        print(f"\nAu fost detectate {len(results)} puncte pe hartă.")
    except Exception as e:
        print(f"Eroare la procesare: {str(e)}")


if __name__ == "__main__":
    main()
