

import requests
import subprocess
import json
from datetime import timedelta, datetime
# from openai import OpenAI
from config.settings import ROOT_DIR, DEEPGRAM_API_KEY, OPEN_IA_API_KEY, CHAT_PDF_API_KEY, MEDIA_ROOT
from apps.documento import models

import os
from deepgram import (
    DeepgramClient,
    PrerecordedOptions,
    FileSource,
)

from apps.documento.choices import (
    CHAT_AUTOR_IA, 
    STATUS_PROCESSANDO_ARQUIVO,
    STATUS_FALHA_PROCESSAMENTO,
    STATUS_FAZENDO_TRANSCRICAO,
    STATUS_FALHA_TRANSCRICAO,
    STATUS_CONCLUIDO,
    STATUS_PDF_FALHA_ENVIO,
    TRANSCRICAO_TIPO_VIDEO,
    STATUS_OCR_CONCLUIDO,
    STATUS_OCR_PROCESSANDO,
    STATUS_OCR_FALHA_PROCESSAMENTO,
    STATUS_OCR_DISPENSADO
)

from hashlib import md5
import shutil
import ocrmypdf
from constance import config

# ROOT_MEDIA = f'{ROOT_DIR}/media'
ROOT_MEDIA = MEDIA_ROOT
ROOT_LEGENDA = f'{MEDIA_ROOT}/legenda_transcricao'
ROOT_PDF = f'{MEDIA_ROOT}/documento_chat'


def create_questions(*args, **kwargs):
    from .models import Chat, Mensagem 
    chat = kwargs['chat']
    texto = kwargs['texto']
    autor = kwargs['autor']
    not_save = kwargs.get('not_save')


    if not not_save:
        nova_msg = models.Mensagem(chat_id=chat, texto=texto, autor=autor)
        nova_msg.save()

    chatpdf_source_id = models.Chat.objects.get(pk=chat).chatpdf_source_id

    headers = {
        'x-api-key': CHAT_PDF_API_KEY,
        "Content-Type": "application/json",
    }

    data = {
        "referenceSources": True,
        'sourceId': chatpdf_source_id,
        'messages': [
            {
                'role': "user",
                'content': texto,
            }
        ]
    }

    response = requests.post(
        'https://api.chatpdf.com/v1/chats/message', headers=headers, json=data)

    resposta_chatpdf = models.Mensagem(chat_id=chat, texto='', autor=CHAT_AUTOR_IA)
    
    if response.status_code == 200:
        resposta_chatpdf.texto = response.json()['content']
    else:
        resposta_chatpdf.texto = 'Erro ao responder'

    resposta_chatpdf.save()
    return resposta_chatpdf


def convert_to_time(number, microseconds=False):
    delta_tempo = timedelta(seconds=number)
    time = "{:02}:{:02}:{:02}".format(delta_tempo.seconds // 3600, (delta_tempo.seconds % 3600) // 60, delta_tempo.seconds % 60)
    if microseconds:
        microssegundos_limitados = min(delta_tempo.microseconds // 1000, 999)
        time = "{}.{:03}".format(time, microssegundos_limitados)
    return time

def get_md5File(filepath,fileopen=False):
    BUF_SIZE = 65536
    md5_hexdigits = md5()
    if fileopen == False:
        with open(filepath, 'rb') as f:
            while True:
                data = f.read(BUF_SIZE)
                if not data:
                    break
                md5_hexdigits.update(data)
    else:
        while True:
            data = filepath.read(BUF_SIZE)
            if not data:
                break
            md5_hexdigits.update(data)
    return f'{md5_hexdigits.hexdigest()}'

def martinha_ocupada():
    run_documents_martinha = models.Chat.objects.filter(status=STATUS_OCR_PROCESSANDO, ativo=True,is_martinha_processando=True).count()
    run_documents_tanaka = models.Chat.objects.filter(status=STATUS_OCR_PROCESSANDO, ativo=True,is_martinha_processando=False).count()
    return [
        run_documents_martinha >= config.MARTINHA_NUM_MAX_EXECUTION,
        run_documents_martinha,
        run_documents_tanaka
    ]

def tanaka_ocupado():
    run_transcricoes_tanaka = models.MediaTranscricao.objects.filter(status=STATUS_PROCESSANDO_ARQUIVO, ativo=True,is_tanaka_processando=True).count()
    run_transcricoes_martinha = models.MediaTranscricao.objects.filter(status=STATUS_PROCESSANDO_ARQUIVO, ativo=True,is_tanaka_processando=False).count()
    return [
        run_transcricoes_tanaka >= config.TANAKA_NUM_MAX_EXECUTION,
        run_transcricoes_tanaka,
        run_transcricoes_martinha
    ]
    
class TanakaUtils:
    def __init__(self,media_transcricao_id,is_tanaka):
        self.media_transcricao = models.MediaTranscricao.objects.get(pk=media_transcricao_id)
        self.media_transcricao.is_tanaka_processando = is_tanaka
        self.media_transcricao.save()
        self.filename_audio = str(self.media_transcricao.arquivo.name).split('/')[1].split('.')[-2]
        self.path_media_audio = f'{ROOT_MEDIA}/{self.filename_audio}.mp3'
        self.file_path = '{}/{}'.format(ROOT_MEDIA, self.media_transcricao.arquivo)


    def preparar_audio(self):
        try:
            self.atualizar_status_transcricao(STATUS_PROCESSANDO_ARQUIVO)

            self.extrair_audio()

            self.converter_video()

            if os.path.exists(self.path_media_audio):
                # preparar_transcricao_openia(media_transcricao_id, audio_file)
                self.preparar_transcricao_deepgram()
            else:
                self.atualizar_status_transcricao(STATUS_FALHA_PROCESSAMENTO)
        
        except Exception as e:
            self.atualizar_status_transcricao(STATUS_FALHA_PROCESSAMENTO)


    def atualizar_status_transcricao(self, status):
        self.media_transcricao.status = status
        self.media_transcricao.modificado_em = datetime.now()
        self.media_transcricao.save()


    def converter_video(self):
        # Se o arquivo for de video transforma em webm
        if self.media_transcricao.tipo == TRANSCRICAO_TIPO_VIDEO and not ".webm" in self.file_path:
            current_time = int(datetime.now().replace(microsecond=0).timestamp())

            filename_path = f'{self.filename_audio}_{current_time}'
                
            path_media_video = f'{ROOT_MEDIA}/arquivo_transcricao/{filename_path}.webm'
            subprocess.run(['ffmpeg','-y','-i', self.file_path, '-c:v', 'libvpx', '-s', '640x360', path_media_video])
            # subprocess.run(['ffmpeg','-y','-i', self.file_path, '-c:v', 'libvpx-vp9', '-crf', '51', '-b:v', '250K', '-c:a', 'libvorbis',  path_media_video])
            
            self.media_transcricao.arquivo.name = f'arquivo_transcricao/{filename_path}.webm'
            self.media_transcricao.save()
            self.filename_audio = str(self.media_transcricao.arquivo.name).split('/')[1].split('.')[-2]
            
            os.remove(self.file_path)


    def extrair_audio(self):
        # subprocess.run(['ffmpeg','-y','-i', self.file_path, '-f', 'wav', '-acodec', 'pcm_s16le', '-ar', '22050', '-ac', '1', 'copy', self.path_media_audio])
        subprocess.run(['ffmpeg','-y','-i', self.file_path, '-f', 'mp3', '-ar', '22050', '-ac', '1', 'copy', self.path_media_audio])
        result = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of",
                                 "default=noprint_wrappers=1:nokey=1", self.path_media_audio],
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT
                            )
        duration = round(float(result.stdout))
        self.media_transcricao.duracao = duration
        self.media_transcricao.save()


    def preparar_transcricao_deepgram(self):
        try: 
            path_media_legenda = f'{ROOT_LEGENDA}/{self.filename_audio}.vtt'
            
            self.atualizar_status_transcricao(STATUS_FAZENDO_TRANSCRICAO)

            deepgram = DeepgramClient(DEEPGRAM_API_KEY)

            with open(self.path_media_audio, 'rb') as f:

                payload: FileSource = {
                    "buffer": f.read(),
                }

                options = PrerecordedOptions(
                    model="whisper-large",
                    language="pt-BR",
                    smart_format=True, 
                    punctuate=True, 
                    paragraphs=True, 
                    diarize=True, 
                )

                response = deepgram.listen.prerecorded.v("1").transcribe_file(payload, options, timeout = 900)

                paragrafos = response.results.channels[0].alternatives[0].paragraphs.paragraphs

                if paragrafos:
                    texto_total = ""
                    cores_avatar = ['#179B14', '#BC1414', '#FA8C0B', '#000000', '#0DA78B', '#0D6FA7', '#510BAA', '#C20FC6', '#F2E03E', '#FF6384', '#4BC0C0', '#8D99AE']
                    with open(path_media_legenda, 'w') as vtt:
                        vtt.write('WEBVTT\n')

                        for p in paragrafos:
                            
                            for s in p.sentences:
                                start = convert_to_time(s.start, True)
                                end = convert_to_time(s.end, True)
                                text = s.text

                                vtt.write(f'{start} --> {end}\r')
                                vtt.write(f'{str(text).strip()}\r')

                                texto_total += f'{start} - {end}</br>'
                                texto_total += f'{text}</br>'

                                dict_transcricao = {
                                    'media_transcricao': self.media_transcricao,
                                    'texto': text,
                                    'tempo_inicial': convert_to_time(s.start, False),
                                    'tempo_final': convert_to_time(s.end, False),
                                    'tempo_inicial_segundos': int(s.start),
                                    'speaker': f"Orador {p.speaker}",
                                    'cor_speaker': cores_avatar[p.speaker]
                                }
                                transcricao_new = models.Transcricao(**dict_transcricao)
                                transcricao_new.save()


                        self.media_transcricao.legenda = f'legenda_transcricao/{self.filename_audio}.vtt'
                        self.media_transcricao.save()
                            
                    vtt.close()
                    self.atualizar_status_transcricao(STATUS_CONCLUIDO)
                else:
                    self.atualizar_status_transcricao(STATUS_FALHA_TRANSCRICAO)

                f.close()
            os.remove(self.path_media_audio)

        except Exception as e:
            print(e)
            self.atualizar_status_transcricao(STATUS_FALHA_TRANSCRICAO)


        # def preparar_transcricao_openia(self,audio_file):
    #     try: 
    #         # envia arquivo para OpenAI
    #         path_media_legenda = f'{ROOT_LEGENDA}/{self.filename_audio}.vtt'
            
    #         print("<<<<<<<<<<<< PREPARANDO TRANSCRIÇÃO >>>>>>>>>>>>")
    #         self.atualizar_status_transcricao(STATUS_FAZENDO_TRANSCRICAO)

    #         client = OpenAI(api_key=OPEN_IA_API_KEY)
    #         transcricao = client.audio.transcriptions.create(
    #             model="whisper-1", 
    #             file=audio_file, 
    #             response_format="verbose_json"
    #         )

    #         if transcricao:
    #             print('audio_file.name', audio_file.name)
    #             # diarization = get_diarizations(audio_file.name)
    #             texto_total = ""
    #             with open(path_media_legenda, 'w') as vtt:
    #                 vtt.write('WEBVTT\n')
                    
    #                 for t in transcricao.segments:
    #                     start = convert_to_time(t.get('start'), True)
    #                     end = convert_to_time(t.get('end'), True)
    #                     text = t.get('text')

    #                     vtt.write(f'{start} --> {end}\r')
    #                     vtt.write(f'{str(text).strip()}\r')

    #                     texto_total += f'{start} - {end}</br>'
    #                     texto_total += f'{text}</br>'

    #                     dict_transcricao = {
    #                         'media_transcricao': self.media_transcricao,
    #                         'texto': text,
    #                         'tempo_inicial': convert_to_time(t.get('start'), False),
    #                         'tempo_final': convert_to_time(t.get('end'), False),
    #                         'tempo_inicial_segundos': int(t.get('start')),
    #                         # 'speaker': get_speaker(diarization,t.get('start'),t.get('end'))
    #                         'speaker': 'Não identificado'
    #                     }
    #                     transcricao_new = models.Transcricao(**dict_transcricao)
    #                     transcricao_new.save()
                    
    #                 self.media_transcricao.legenda = f'legenda_transcricao/{self.filename_audio}.vtt'
    #                 # instance.diarizacao = diarization
    #                 transcricao_obj = {
    #                     "segments": transcricao.segments,
    #                 }
    #                 self.media_transcricao.transcricao = json.dumps(transcricao_obj)
    #                 self.media_transcricao.save()
                        
    #             vtt.close()
    #             print("<<<<<<<<<<<< TRANSCRIÇÃO CONCLUIDA >>>>>>>>>>>>")
    #             self.atualizar_status_transcricao(STATUS_CONCLUIDO)
    #         else:
    #             print("<<<<<<<<<<<< FALHA NA TRANSCRIÇÃO >>>>>>>>>>>>")
    #             self.atualizar_status_transcricao(STATUS_FALHA_TRANSCRICAO)

    #     except Exception as e:
    #         print("<<<<<<<<<<<< FALHA NA TRANSCRIÇÃO EXCEPT >>>>>>>>>>>>", e)
    #         self.atualizar_status_transcricao(STATUS_FALHA_TRANSCRICAO)


class MartinhaUtils:
    def __init__(self, chat_id,is_martinha):
        self.chat = models.Chat.objects.get(id=chat_id)
        self.chat.is_martinha_processando = is_martinha
        self.chat.save()
        # self.file_path = f'{ROOT_DIR}/media/{self.chat.documento}'
        self.file_path = f'{ROOT_MEDIA}/{self.chat.documento}'

    def atualizar_status(self, status):
        self.chat.status = status
        self.chat.modificado_em = datetime.now()
        self.chat.save()

    def preparar_ocr_pdf(self):
        try:
            self.atualizar_status(STATUS_OCR_PROCESSANDO)
            ocrmypdf.ocr(input_file=self.file_path, output_file=self.file_path, redo_ocr=True, output_type='pdf', optimize=0, jobs=28, invalidate_digital_signatures=True)
    
            chatpdf_source_id = self.enviar_arquivo_para_chatpdf()

            if chatpdf_source_id:
                self.chat.chatpdf_source_id = chatpdf_source_id
                self.chat.save()
                self.atualizar_status(STATUS_OCR_CONCLUIDO)
            else:
                self.atualizar_status(STATUS_PDF_FALHA_ENVIO)

        except Exception as e:
            print('falha', e)
            chatpdf_source_id = self.enviar_arquivo_para_chatpdf()

            if chatpdf_source_id:
                self.chat.chatpdf_source_id = chatpdf_source_id
                self.chat.log_errors = f'OCR: {e}'
                self.chat.save()
                self.atualizar_status(STATUS_OCR_CONCLUIDO)
            else:
                self.atualizar_status(STATUS_PDF_FALHA_ENVIO)

            # self.atualizar_status(STATUS_OCR_FALHA_PROCESSAMENTO)

    
    def compress_pdf(self, input_pdf_path=None, output_pdf_path=None, power=2):
        input_pdf_path = input_pdf_path if input_pdf_path else self.file_path
        output_pdf_path = output_pdf_path if output_pdf_path else self.file_path

        quality = {
            0: '/default',  # Alta qualidade, menor compressão
            1: '/screen',   # Baixa qualidade, maior compressão
            2: '/ebook',    # Qualidade média
            3: '/prepress', # Alta qualidade, menor compressão
            4: '/printer'   # Qualidade para impressão
        }

        if power not in quality:
            raise ValueError("Nível de compressão inválido. Use um valor entre 0 e 4.")

        temp_output_path = output_pdf_path + ".tmp"

        gs_command = [
            'gs',
            '-sDEVICE=pdfwrite',
            f'-dPDFSETTINGS={quality[power]}',
            '-dNOPAUSE',
            '-dQUIET',
            '-dBATCH',
            f'-sOutputFile={temp_output_path}',
            input_pdf_path
        ]

        try:
            subprocess.run(gs_command, check=True)
            if input_pdf_path == output_pdf_path:
                shutil.move(temp_output_path, output_pdf_path)
            else:
                shutil.move(temp_output_path, output_pdf_path)
        except subprocess.CalledProcessError as e:
            print(f'erro gs {self.chat}:',e)
            if os.path.exists(temp_output_path):
                os.remove(temp_output_path)



    def enviar_arquivo_para_chatpdf(self):
        try:
            self.compress_pdf()
            with open(self.file_path, 'rb') as file:
                files = [
                    ('file', ('file', file, 'application/octet-stream'))
                ]
                headers = {'x-api-key': CHAT_PDF_API_KEY}

                response = requests.post('https://api.chatpdf.com/v1/sources/add-file', headers=headers, files=files)


                if response.status_code == 200:
                    return response.json()['sourceId']

                return None
               
        except Exception as e:
            self.chat.log_errors = f'CHAT_PDF: {e}'
            self.chat.save()
            return None



# def convert_mp3_to_wav(mp3_path, wav_path):
#     # Comando ffmpeg para converter MP3 para WAV com taxa de amostragem de 16kHz
#     # command = ['ffmpeg','-y','-i', mp3_path, '-f', 'wav', '-acodec', 'pcm_s16le', '-ar', '16000', '-ac', '1', 'copy', wav_path]
#     command = ['ffmpeg','-y', '-i', mp3_path, '-ar', '16000', '-ac', '1', wav_path]
#     subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

# def process_audio(audio_path):
#     convert_mp3_to_wav(audio_path,'converted_mp3.wav')
#     rate, data = wavfile.read("converted_mp3.wav")
#     # perform noise reduction
#     reduced_noise = nr.reduce_noise(y=data, sr=rate)
#     wavfile.write("audio_temporario.wav", rate, reduced_noise)

#     return "audio_temporario.wav"

# def get_diarizations(audio):
#     print("<<<<<<<<<<<< PREPARANDO DIARIZAÇAO >>>>>>>>>>>>")
#     try:
#         pipeline = Pipeline.from_pretrained(
#         "pyannote/speaker-diarization-3.1",
#         use_auth_token="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")

#         pipeline.to(torch.device("cpu"))

#         # apply pretrained pipeline
#         diarization = pipeline(audio,num_speakers=2,max_speakers=3)

#         # print the result
#         result = [{
#             'start': f'{turn.start:.1f}',
#             'stop': f'{turn.end:.1f}',
#             'speaker': speaker
#         } for turn, _, speaker in diarization.itertracks(yield_label=True)]
#         print("<<<<<<<<<<<< DIARIZACAO CONCLUIDA >>>>>>>>>>>>")
#         return unify_speakers(result)
#     except Exception as e:
#         print("<<<<<<<<<<<< ERRO DIARIZACAO >>>>>>>>>>>>", e)

# def get_speaker(diarization,start_interval,stop_interval):
#     filtered_elements = [element for element in diarization if float(start_interval) >= float(element['start']) and float(stop_interval) <= float(element['stop'])]
#     return filtered_elements[0]['speaker'] if filtered_elements else 'Não identificado'

# def unify_speakers(data):
#     print("<<<<<<<<<<<< UNIFY SPEAKERS >>>>>>>>>>>>")
#     try:
#         unified = []
#         current_speaker = None
#         current_start = None
#         current_stop = None

#         for item in data:
#             start = float(item['start'])
#             stop = float(item['stop'])
#             speaker = item['speaker']

#             # Se é o mesmo speaker e o intervalo é contínuo ou se sobrepõe, atualize o 'stop'
#             if speaker == current_speaker:
#                 current_stop = max(current_stop, stop)
#             else:
#                 if current_speaker is not None:
#                     unified.append({'start': str(current_start), 'stop': str(current_stop), 'speaker': current_speaker})
                
#                 current_speaker = speaker
#                 current_start = start
#                 current_stop = stop

#         # Não esqueça de adicionar o último intervalo após sair do loop
#         if current_speaker is not None:
#             unified.append({'start': str(current_start), 'stop': str(current_stop), 'speaker': current_speaker})

#         return unified
#     except Exception as e:
#          print("<<<<<<<<<<<< UNIFY SPEAKERS ERROR>>>>>>>>>>>>", e)



# def criar_chat_transcricao():
#     path_media_pdf = f'{ROOT_PDF}/{filename_audio}.pdf'
        
#     pdfkit.from_string(texto_total, path_media_pdf,options={'encoding': "UTF-8",})

#     dict_chat = {
#         'titulo': filename_audio,
#         'documento': f'documento_chat/{filename_audio}.pdf',
#         'ativo': True,
#         'usuario': instance.criado_por,
#     }
    
#     chat = models.Chat(**dict_chat)
#     chat.save()
    
#     instance.chat = chat
#     instance.save()


