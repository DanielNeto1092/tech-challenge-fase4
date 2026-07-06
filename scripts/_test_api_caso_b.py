"""Quick API test for Caso B - elevated visual signals."""
import json
import requests

url = "http://127.0.0.1:8000/analyze"
transcript = (
    "Participante apresenta sinais de desengajamento e possivel dificuldade "
    "durante a atividade. A analise busca apoiar triagem e revisao humana a "
    "partir das evidencias multimodais disponiveis."
)
video_path = r"archive\DAiSEE\DataSet\Test\510034\5100342022\5100342022.avi"

with open(video_path, "rb") as vf:
    files = {"video": ("5100342022.avi", vf, "video/avi")}
    data = {"transcript": transcript}
    r = requests.post(url, files=files, data=data, timeout=180)

result = r.json()
print(f"Status: {r.status_code}")
print(f"Score: {result.get('multimodal_score_0_1', '?')}")
print(f"Level: {result.get('level', '?')}")
print(f"Priority: {result.get('priority', {}).get('riskLevel', '?')}")
print(f"Pathway: {result.get('care_assessment', {}).get('carePathway', '?')}")
print(f"Video meta: {json.dumps(result.get('_video_processing', {}), indent=2)}")
print(f"Elapsed: {result.get('_api_elapsed_s', '?')}s")
print(f"Modalities: {list(result.get('modality_scores', {}).keys())}")
