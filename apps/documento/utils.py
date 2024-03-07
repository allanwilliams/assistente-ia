import requests
from apps.documento.choices import CHAT_AUTOR_IA
import subprocess
from scipy.io import wavfile
import noisereduce as nr
import torch
from pyannote.audio import Pipeline

def create_questions(*args, **kwargs):
    from .models import Chat, Mensagem 
    chat = kwargs['chat']
    texto = kwargs['texto']
    autor = kwargs['autor']
    not_save = kwargs.get('not_save')


    if not not_save:
        nova_msg = Mensagem(chat_id=chat, texto=texto, autor=autor)
        nova_msg.save()

    chatpdf_source_id = Chat.objects.get(pk=chat).chatpdf_source_id

    headers = {
        'x-api-key': 'sec_16KMXQwy0VcwkGz7xYuDY9PxWGGgsHM6',
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

    resposta_chatpdf = Mensagem(chat_id=chat, texto='', autor=CHAT_AUTOR_IA)
    
    if response.status_code == 200:
        resposta_chatpdf.texto = response.json()['content']
    else:
        resposta_chatpdf.texto = 'Erro ao responder'

    resposta_chatpdf.save()
    return resposta_chatpdf

def convert_mp3_to_wav(mp3_path, wav_path):
    # Comando ffmpeg para converter MP3 para WAV com taxa de amostragem de 16kHz
    # command = ['ffmpeg','-y','-i', mp3_path, '-f', 'wav', '-acodec', 'pcm_s16le', '-ar', '16000', '-ac', '1', 'copy', wav_path]
    command = ['ffmpeg','-y', '-i', mp3_path, '-ar', '16000', '-ac', '1', wav_path]
    subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def process_audio(audio_path):
    convert_mp3_to_wav(audio_path,'converted_mp3.wav')
    rate, data = wavfile.read("converted_mp3.wav")
    # perform noise reduction
    reduced_noise = nr.reduce_noise(y=data, sr=rate)
    wavfile.write("audio_temporario.wav", rate, reduced_noise)

    return "audio_temporario.wav"

def get_diarizations(audio):

    pipeline = Pipeline.from_pretrained(
    "pyannote/speaker-diarization-3.1",
    use_auth_token="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")

    pipeline.to(torch.device("cpu"))

    # apply pretrained pipeline
    diarization = pipeline(audio,num_speakers=2,max_speakers=3)

    # print the result
    result = [{
        'start': f'{turn.start:.1f}',
        'stop': f'{turn.end:.1f}',
        'speaker': speaker
    } for turn, _, speaker in diarization.itertracks(yield_label=True)]
    return unify_speakers(result)

def get_speaker(diarization,start_interval,stop_interval):
    filtered_elements = [element for element in diarization if float(start_interval) >= float(element['start']) and float(stop_interval) <= float(element['stop'])]
    return filtered_elements[0]['speaker'] if filtered_elements else 'Não identificado'

def unify_speakers(data):
    unified = []
    current_speaker = None
    current_start = None
    current_stop = None

    for item in data:
        start = float(item['start'])
        stop = float(item['stop'])
        speaker = item['speaker']

        # Se é o mesmo speaker e o intervalo é contínuo ou se sobrepõe, atualize o 'stop'
        if speaker == current_speaker:
            current_stop = max(current_stop, stop)
        else:
            if current_speaker is not None:
                unified.append({'start': str(current_start), 'stop': str(current_stop), 'speaker': current_speaker})
            
            current_speaker = speaker
            current_start = start
            current_stop = stop

    # Não esqueça de adicionar o último intervalo após sair do loop
    if current_speaker is not None:
        unified.append({'start': str(current_start), 'stop': str(current_stop), 'speaker': current_speaker})

    return unified