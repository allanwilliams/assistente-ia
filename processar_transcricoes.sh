#!/bin/bash
source /home/defensoria/assistente-ia/venv/bin/activate 

cd /home/defensoria/assistente-ia 

python manage.py processar_transcricoes
