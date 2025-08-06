import cv2
import csv
import os
import re
import easyocr
import json

from glob import glob
from tqdm import tqdm
from loguru import logger


# CONVERTER VIDEO P/ IMAGENS COM OPEN CV
class PlateVerif:

  def __init__(self) -> None:
    self.plates = []
    self.reader = easyocr.Reader(['en'])

  def convert_video_to_images(self, video_path:str, images_folder:str):
    cam = cv2.VideoCapture(video_path)
    try:  # cria o dir de imagens se ele n existir
        if not os.path.exists(images_folder):
            os.makedirs(images_folder)
            first_time = True
        else:
          first_time = False
          logger.info('Dir já existe')

    except OSError:
        logger.error(f'Erro: criando dir {images_folder}')

    if first_time:  # se estivermos processando as imagens pela 1a vez
      currentframe = 0
      while cam.isOpened():
          ret, frame = cam.read()

          if ret:  # processa imagem
              name = f'./{images_folder}/frame_{str(currentframe)}.jpg'
              logger.info(f'Processing Frame: {currentframe}')

              cv2.imwrite(name, frame)
              cam.set(cv2.CAP_PROP_POS_FRAMES, currentframe)
              currentframe += 15  # # process imagem de 15 em 15 frames (2 por seg)
          else:
              cam.release()
              break

      cam.release()
      cv2.destroyAllWindows()
      return True
    
    return False  # fim CONVERTER...

  def is_valid_plate(self, plate):  # descrevendo as caracteristicas do texto d uma placa
    pattern = r"^[A-Z]{3}[0-9][0-9A-Z][0-9]{2}$"
    return bool(re.fullmatch(pattern, plate))

  def read_text_from_image(self, path_image:str, decoder:str):  # lendo o texto da img
      try:
          results = self.reader.readtext(path_image, decoder=decoder)
          return results
      except Exception as e:
          logger.error(e)
          return None

  def filter_plates(self, text_items:str):  # filtrando a placa baseado em caracteristicas / acuracia
      for item in text_items:
          text = item[1].replace('-', '').replace(' ', '').upper()
          precision = item[2]

          logger.info(f'extracted text: {text} precision {precision}')

          is_plate = self.is_valid_plate(text)
          if precision > 0.75 and is_plate:
            return text
      return None

  def list_images(self, path:str):  # LISTANDO TODAS AS IMAGENS no dir
    jpgs = glob(path)
    return jpgs


# Carrega lista de placas autorizadas
def load_auth_plates(caminho_csv="placas_autorizadas.csv"):
    placas = set()
    with open(caminho_csv, newline='', encoding='utf-8') as csvfile:
        leitor = csv.reader(csvfile)
        next(leitor)  # pula o cabeçalho
        for linha in leitor:
            if linha:
                placa = linha[0].strip().upper()
                placas.add(placa)
    return placas


# Verifica se a placa está autorizada
def verify_auth(placa_detectada, placas_autorizadas):
    if placa_detectada.strip().upper() in placas_autorizadas:
        return "seguro"
    else:
        return "não seguro"


def verify_sec_state(placa_detectada, placas_autorizadas):
    if placa_detectada.strip().upper() in placas_autorizadas:
      return True
    else:
      return False


# placeholder de liberar entrada
def liberar_entrada(placa):
    print(f"[LIBERAÇÃO] A placa {placa} está autorizada. Entrada liberada.")


# placeholder alerta
def emitir_alerta(placa):
    print(f"[ALERTA] A placa {placa} **não está** autorizada. Alerta emitido.")


if __name__ == '__main__':
  decoder = 'beamsearch'

  plate_analysis = PlateVerif()
  plate_analysis.convert_video_to_images('./videoplayback.mp4', 'images')  # caminho do input; isso daqui no sistema seria substituido pelo FFMpeg
  images_list = plate_analysis.list_images('./images/*')
  authorized_plates = load_auth_plates()

  for image in tqdm(images_list):

    unprocessed_plate = plate_analysis.read_text_from_image(image, decoder)
    plate = plate_analysis.filter_plates(unprocessed_plate)

    if plate is None:
        logger.warning(f"Nenhuma placa válida detectada na imagem {image}")
        continue  # pula para a próxima imagem

    state = verify_sec_state(plate, authorized_plates)

    if state:
      liberar_entrada(plate)
    else:
      emitir_alerta(plate)

    logger.info('Processing Finished')
