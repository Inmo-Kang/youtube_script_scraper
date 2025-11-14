# 📑 유튜브 채널 스크래퍼 사용 설명서 (README)

이 프로그램은 2단계로 작동하며, 특정 유튜브 채널의 모든 영상 정보를 수집하고(1단계), 해당 영상들의 스크립트(자막)를 추출합니다(2단계).

## 1. ⚙️ 최초 환경 설정 (한 번만)

이 스크립트들을 사용하기 전에, 파이썬 가상 환경을 설정하고 필요한 라이브러리를 설치해야 합니다.

### 1.1. 가상 환경 생성 및 활성화

```bash
# 1. 'youtube_scraper' 폴더를 만들고 이동합니다.
mkdir youtube_scraper
cd youtube_scraper

# 2. '.venv'라는 이름의 가상 환경을 만듭니다.
python -m venv .venv

# 3. 가상 환경을 활성화합니다.
# (macOS/Linux)
source .venv/bin/activate
# (Windows)
# .\.venv\Scripts\activate
(터미널 앞에 (.venv)가 보이면 성공입니다.)

1.2. 필수 라이브러리 설치
가상 환경이 활성화된 상태에서, 1단계와 2단계 스크립트에 필요한 모든 라이브러리를 설치합니다.

Bash

# 1. 1단계(scraper.py)에 필요한 라이브러리
pip install google-api-python-client python-dotenv

# 2. 2단계(get_transcripts.py)에 필요한 라이브러리
# (주의: 1.2.3 버전의 올바른 문법을 사용하도록 스크립트가 작성되었습니다.)
pip install youtube-transcript-api
1.3. API 키 설정 (.env 파일)
scraper.py (1단계) 스크립트는 Google의 YouTube Data API를 사용합니다.

스크립트가 있는 폴더 (youtube_scraper)에 .env라는 이름의 파일을 만듭니다.

Google Cloud Console에서 발급받은 'YouTube Data API v3' 키를 아래와 같이 저장합니다.

.env

Ini, TOML

YOUTUBE_API_KEY="AIzaSy... (여기에 1단계 API 키를 붙여넣으세요)"
2. 🚀 스크립트 실행 방법
설정이 완료되면, 아래의 2단계를 순서대로 실행합니다.

🎬 1단계: scraper.py (채널 정보 및 영상 목록 수집)
이 스크립트는 채널의 모든 영상 정보(제목, 설명, 길이, 숏츠 여부 등)를 가져와 _videos.json 파일로 저장합니다.

실행 명령어:

Bash

python scraper.py [채널_ID_또는_핸들]
[채널_ID_또는_핸들]: (필수) 정보를 수집할 채널의 UC...로 시작하는 ID 또는 @...로 시작하는 핸들을 입력합니다.

실행 예시:

Bash

# 핸들(@moneycoach)을 기준으로 실행
python scraper.py @moneycoach

# 채널 ID를 기준으로 실행
python scraper.py UCLrRutm_EiL2294pFrTEN4w
결과물: UCLrRutm_EiL2294pFrTEN4w_videos.json과 같은 파일이 생성됩니다.

✍️ 2단계: get_transcripts.py (스크립트 추출)
이 스크립트는 1단계에서 생성된 _videos.json 파일을 읽어, 영상들의 스크립트(자막)를 추출합니다.

실행 명령어:

Bash

python get_transcripts.py [입력_JSON_파일] [옵션]
[입력_JSON_파일]: (필수) 1단계에서 생성된 ..._videos.json 파일 경로를 입력합니다.

옵션 (선택 사항):

-o [파일명] 또는 --output_file [파일명]: 결과를 저장할 파일 이름을 지정합니다. (기본값: result_가 붙은 .jsonl 파일)

--batch_size [숫자]: 한 번에 처리할 영상 개수를 지정합니다. (기본값: 0 = 처리 안 된 영상 전체)

실행 예시:

Bash

# 1. 1단계의 결과물로 "전체 영상"의 스크립트를 추출 (가장 일반적인 사용법)
python get_transcripts.py UCLrRutm_EiL2294pFrTEN4w_videos.json

# 2. "10개"만 테스트로 추출
python get_transcripts.py UCLrRutm_EiL2294pFrTEN4w_videos.json --batch_size 10

# 3. "my_results.jsonl"라는 이름으로 결과 파일 저장
python get_transcripts.py UCLrRutm_EiL2294pFrTEN4w_videos.json -o my_results.jsonl
누적 저장: 이 스크립트를 다시 실행하면, 출력 파일(result_...jsonl)을 읽어 이미 처리된 영상은 건너뛰고 새로 추가된 영상만 처리합니다.

3. 📋 결과물 파일 설명
1. ..._videos.json (1단계 결과물)
채널의 모든 영상 정보가 하나의 큰 리스트로 저장된 일반 JSON 파일입니다.

is_short, duration_seconds 등의 정보가 포함되어 있습니다.

2. result_...jsonl (2단계 결과물)
스크립트 추출 결과가 한 줄에 영상 하나씩 누적 저장되는 JSONL (JSON Lines) 파일입니다.

파일을 열어보면 2가지 유형의 결과를 볼 수 있습니다.

[성공 예시] (자막이 있어서 스크립트가 저장됨)

JSON

{"title": "네이버 플레이스 상위 노출 방법...", "script": "여러분, 네이버가 작정했습니다. ..."}
[실패 예시] (자막이 없어서 오류가 기록됨 - 정상적인 실패)

JSON

{"title": "자막이 없는 어떤 영상...", "script": "ERROR: Transcript not available or disabled. (NoTranscriptFound)"}