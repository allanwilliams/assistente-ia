#!/bin/bash
source /home/defensoria/assistente_ia/venv/bin/activate 

cd /home/defensoria/assistente_ia 

python manage.py processar_transcricoes
