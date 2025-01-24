

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
    STATUS_OCR_DISPENSADO,
    INTERPRETADOR_DEEPGRAM,
    INTERPRETADOR_DEFENSORIA
)

from hashlib import md5
import shutil
import ocrmypdf
# from aTrain  import audio, handle_upload, transcribe, output_files, load_resources

# from aTrain_core import load_resources, transcribe
import torch
from constance import config

from faster_whisper.audio import decode_audio

# ROOT_MEDIA = f'{ROOT_DIR}/media'
ROOT_MEDIA = MEDIA_ROOT
ROOT_LEGENDA = f'{MEDIA_ROOT}/legenda_transcricao'
ROOT_PDF = f'{MEDIA_ROOT}/documento_chat'
CORES_AVATAR = ['#179B14', '#BC1414', '#FA8C0B', '#000000', '#0DA78B', '#0D6FA7', '#510BAA', '#C20FC6', '#F2E03E', '#FF6384', '#4BC0C0', '#8D99AE']


def prepare_audio (file_id,file_path,file_directory):
    ffmpeg_path = 'ffmpeg'
    output_file = file_id + ".wav"
    output_path =  os.path.join(file_directory,output_file)
    stream = ffmpeg.input(file_path)
    stream = ffmpeg.output(stream, output_path)
    
    ffmpeg.run(stream,quiet=True, cmd=ffmpeg_path)
    print(output_path)
    return output_path

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

    def atrain_transcribe_override(self,
        audio_file,
        file_id,
        model,
        language,
        speaker_detection,
        num_speakers,
        device,
        compute_type,
        timestamp,
        original_audio_filename,
        initial_prompt=None):
        from aTrain_core import load_resources, transcribe
        from aTrain_core.GUI_integration import EventSender
        from aTrain_core.globals import MODELS_DIR
        GUI = EventSender()
        required_models_dir=MODELS_DIR
        """Transcribes audio file with specified parameters."""
        # import inside function for faster startup times in GUI app

        audio_array, audio_duration, device, min_speakers, max_speakers, language = (
            transcribe._prepare_metadata_creation(language, num_speakers, device, file_id, audio_file)
        )

        model_path = load_resources.get_model(model, required_models_dir=required_models_dir)
        
        transcript = self.perform_whisper_transcription_override(
            model_path,
            device,
            compute_type,
            audio_array,
            language,
            file_id,
            model,
            GUI,
            initial_prompt
        )

        if speaker_detection:
            transcript_with_speaker = transcribe._perform_pyannote_speaker_diarization(
                audio_duration,
                required_models_dir,
                file_id,
                GUI,
                min_speakers,
                max_speakers,
                audio_array,
                transcript,
            )
            return transcript_with_speaker
        return transcript

    def perform_whisper_transcription_override(
        self,
        model_path,
        device,
        compute_type,
        audio_array,
        language,
        file_id,
        model,
        GUI,
        initial_prompt=None,
    ):
        import torch
        from faster_whisper import WhisperModel, BatchedInferencePipeline

        model = WhisperModel(model_path, device, compute_type=compute_type)
        transcription_model = BatchedInferencePipeline(model=model)
        models_config_path = str(files("aTrain_core.models").joinpath("models.json"))
        f = open(models_config_path, "r")
        models = json.load(f)

        model_type = models[model]["type"]
        max_new_tokens = None if model_type == "distil" else 128
        condition_on_previous_text = False if model_type == "distil" else True


        transcription_segments, info = transcription_model.transcribe(
            audio=audio_array,
            vad_filter=True,
            beam_size=5,
            word_timestamps=True,
            language=language,
            max_new_tokens=max_new_tokens,
            no_speech_threshold=0.6,
            condition_on_previous_text=condition_on_previous_text,
            initial_prompt=initial_prompt
        )

        transcription_segments = transcription_with_progress_bar(
            transcription_segments, info, GUI
        )

        transcript = {
            "segments": [named_tuple_to_dict(segment) for segment in transcription_segments]
        }  # wenn man die beiden umdreht also progress bar zuerst damit er schön läuft, dann ist das segments dict leer, sprich es gibt keine transkription
        write_logfile("Transcription successful", file_id)

        del transcription_model
        gc.collect()
        torch.cuda.empty_cache()
        return transcript

    def preparar_transcricao_defensoria(self):
        print('#########################################################')
        from aTrain_core import load_resources, transcribe
        print('@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@')
        # processed_file = prepare_audio(f'{self.media_transcricao.id}',self.media_transcricao.arquivo.path,ROOT_MEDIA)
        # SAMPLING_RATE = 16000
        # processed_file = decode_audio(self.media_transcricao.arquivo.path, sampling_rate=SAMPLING_RATE)
        # print(processed_file)
        # duration = audio.get_audio_duration(processed_file)
        # duration = int(len(processed_file) / SAMPLING_RATE)
        duration = 0
        self.media_transcricao.duracao = duration
        self.media_transcricao.save()

        models_atrain = {
            "large-v2" : {
                "repo_id" : "arminhaberl/faster-whisper-large-v2",
                "revision" : "f7cc452200bff83d699477d7a947fa0ee1c4b09c"
            },
            "large-v3" : {
                "repo_id" : "Systran/faster-whisper-large-v3",
                "revision" : "edaa852ec7e145841d8ffdb056a99866b5f0a478"
            },
            "large-v3-turbo": {
                "repo_id": "aTrain-core/faster-whisper-large-v3-turbo",
                "revision": "df99141c9f5db0615d025664cff8949373a69593",
                "model_hash": "aba90805f182ff57d1f686595500d299"
            },
            "diarize": {
                "repo_id": "aTrain-core/diarize",
                "revision": "af59b6c3c3261a53bbfb1d78d36a10fcd8de3084",
                "model_hash": "c766bd0c6e2bd8523da2a61b2eff0b9f"
            },
        }

        def _load_model_config_file():
            return models_atrain
        
        load_resources.load_model_config_file = _load_model_config_file
        print('[MODELS]:',load_resources.load_model_config_file())
        try: 
            print('vou iniciar a transcricao usando aTrain')
            self.atualizar_status_transcricao(STATUS_FAZENDO_TRANSCRICAO)

            model = 'large-v3-turbo'
            language = 'pt'
            speaker_detection = 'true'
            num_speakers = 'auto-detect'
            device = 'GPU' if torch.cuda.is_available() else "CPU"
            # melhor texto
            compute_type = 'float32' #8 bits (consome 2gb aprox)

            # maior segregação de frases
            # compute_type = 'float16' #16 bit (consome 4gb aprox)

            # print(processed_file)
            timestamp = datetime.now().strftime("%Y-%m-%d %H-%M-%S")
            # transcricao = transcribe.transcribe(audio_file=self.media_transcricao.arquivo.path, file_id='1', model=model, language=language, speaker_detection=speaker_detection, num_speakers=num_speakers, device=device, compute_type=compute_type, timestamp=timestamp,original_audio_filename=self.media_transcricao.arquivo.path)
            transcricao = self.atrain_transcribe_override(audio_file=self.media_transcricao.arquivo.path, file_id='1', model=model, language=language, speaker_detection=speaker_detection, num_speakers=num_speakers, device=device, compute_type=compute_type, timestamp=timestamp,original_audio_filename=self.media_transcricao.arquivo.path)
            print(transcricao)
            # for step in transcribe.transcribe(audio_file=self.media_transcricao.arquivo.path, file_id='1', model=model, language=language, speaker_detection=speaker_detection, num_speakers=num_speakers, device=device, compute_type=compute_type, timestamp=timestamp,original_audio_filename=self.media_transcricao.arquivo.path):
            #     response = f"data: {step['task']}\n\n"
            #     print(response)
            
            # transcricao = step["result"]
            if transcricao:
                texto_total = ""
                path_media_legenda = f'{ROOT_LEGENDA}/{self.filename_audio}.vtt'
                with open(path_media_legenda, 'w') as vtt:
                    vtt.write('WEBVTT\n')
                    
                    for t in transcricao['segments']:
                        start = convert_to_time(t.get('start'), True)
                        end = convert_to_time(t.get('end'), True)
                        text = t.get('text')

                        vtt.write(f'{start} --> {end}\r')
                        vtt.write(f'{str(text).strip()}\r')

                        texto_total += f'{start} - {end}</br>'
                        texto_total += f'{text}</br>'

                        speaker_id = int(t.get('speaker').split('_')[1]) if t.get('speaker') else 0
                        dict_transcricao = {
                            'media_transcricao': self.media_transcricao,
                            'texto': text,
                            'tempo_inicial': convert_to_time(t.get('start'), False),
                            'tempo_final': convert_to_time(t.get('end'), False),
                            'tempo_inicial_segundos': int(t.get('start')),
                            'speaker': f"Orador {speaker_id}",
                            'cor_speaker': CORES_AVATAR[speaker_id]
                        }
                        
                        transcricao_new = models.Transcricao(**dict_transcricao)
                        transcricao_new.save()
                    
                    self.media_transcricao.legenda = f'legenda_transcricao/{self.filename_audio}.vtt'
                    transcricao_obj = {
                        "segments": transcricao['segments'],
                    }
                    self.media_transcricao.transcricao = json.dumps(transcricao_obj)
                    self.media_transcricao.save()
                        
                vtt.close()
                self.atualizar_status_transcricao(STATUS_CONCLUIDO)

            # os.remove(processed_file)

        except Exception as e:
            print("[EXECPTION:]",e)
            # os.remove(processed_file)
            self.atualizar_status_transcricao(STATUS_FALHA_TRANSCRICAO)

    def preparar_audio(self):
        try:
            self.atualizar_status_transcricao(STATUS_PROCESSANDO_ARQUIVO)

            self.converter_video()

            if self.media_transcricao.interpretador == INTERPRETADOR_DEFENSORIA:
                # aTrain
                self.preparar_transcricao_defensoria()
            
            if self.media_transcricao.interpretador == INTERPRETADOR_DEEPGRAM:
                self.extrair_audio()
                if os.path.exists(self.path_media_audio):
                    self.preparar_transcricao_deepgram()    
                    # preparar_transcricao_openia(media_transcricao_id, audio_file)
                else:
                    self.atualizar_status_transcricao(STATUS_FALHA_PROCESSAMENTO)
        
        except Exception as e:
            print('!!!!!!!!!!!!!!!!!!!!!',e)
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

            #determina device de conversão    
            device = "GPU" if torch.cuda.is_available() else "CPU"
            
            #determina extensão de saida do arquivo comprimido
            ext_output_file = 'mp4' if device == 'GPU' else 'webm'

            path_media_video = f'{ROOT_MEDIA}/arquivo_transcricao/{filename_path}.{ext_output_file}'

            if device == 'CPU':
                subprocess.run(['ffmpeg','-y','-i', self.file_path, '-c:v', 'libvpx', '-s', '640x360', path_media_video])
            else:
                subprocess.run(['ffmpeg','-y','-vsync','0','-hwaccel','cuda','-i', self.file_path, '-vf','scale=640:360', '-c:v', 'h264_nvenc', '-b:v','250k', path_media_video])
            
            self.media_transcricao.arquivo.name = f'arquivo_transcricao/{filename_path}.{ext_output_file}'

            # subprocess.run(['ffmpeg','-y','-i', self.file_path, '-c:v', 'libvpx-vp9', '-crf', '51', '-b:v', '250K', '-c:a', 'libvorbis',  path_media_video])
            
            self.media_transcricao.save()
            self.filename_audio = str(self.media_transcricao.arquivo.name).split('/')[1].split('.')[-2]
            os.remove(self.file_path)
            self.file_path = '{}/{}'.format(ROOT_MEDIA, self.media_transcricao.arquivo)


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
                                    'cor_speaker': CORES_AVATAR[p.speaker]
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


