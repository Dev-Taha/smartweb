import os
import sys
import django

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

import requests
from services import ai_extraction as ae

PDF_PATH = os.path.join(PROJECT_ROOT, 'media', 'cv', 'Dr_Zaher_Nazzal_CV_Updated_Aug_2020.pdf')

with open(PDF_PATH, 'rb') as f:
    text = ae.extract_text_from_cv_file(f, PDF_PATH)

payload = {
    'model': ae.settings.TOGETHER_MODEL,
    'temperature': 0.1,
    'messages': [
        {'role': 'system', 'content': 'You are a robust JSON extraction assistant.'},
        {'role': 'user', 'content': ae.PROMPT_TEMPLATE.format(cv_text=text)}
    ],
}
headers = {
    'Authorization': f'Bearer {ae.settings.TOGETHER_API_KEY}',
    'Content-Type': 'application/json',
}
response = requests.post(ae.TOGETHER_ENDPOINT, headers=headers, json=payload, timeout=60)
response.raise_for_status()
data = response.json()
choice = data.get('choices', [{}])[0]
print('status_code:', response.status_code)
print('finish_reason:', choice.get('finish_reason'))
print('content_prefix:', repr(choice.get('message', {}).get('content', '')[:500]))
print('raw_keys:', list(data.keys()))
