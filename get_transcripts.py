import json
import argparse
import os
import logging
# 1. '1.2.3' 버전에 맞는 임포트
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import NoTranscriptFound, TranscriptsDisabled
import os.path 

# --- 로깅 설정 ---
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def get_video_id(url):
    """ 'https://www.youtube.com/watch?v=k88TFoxWNtc'에서 ID 추출 """
    try:
        return url.split('v=')[-1].split('&')[0]
    except Exception:
        return None

def load_processed_urls(output_file):
    """ (누적 저장을 위해) 이미 처리한 URL 목록을 로드합니다. """
    processed_urls = set()
    if os.path.exists(output_file):
        logging.info(f"'{output_file}' 파일에서 기존 처리 내역을 로드합니다.")
        with open(output_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    data = json.loads(line)
                    if 'url' in data:
                        processed_urls.add(data['url'])
                except json.JSONDecodeError:
                    logging.warning(f"결과 파일에 손상된 줄이 있습니다: {line.strip()}")
    logging.info(f"총 {len(processed_urls)}개의 기처리된 영상을 찾았습니다.")
    return processed_urls

def fetch_transcript_v123(api_instance, video_id):
    """
    (완전히 수정됨) '1.2.3' 버전 문법으로 스크립트를 가져옵니다.
    """
    try:
        # 1. (v1.2.3) 자막 리스트 가져오기
        transcript_list = api_instance.list(video_id)
        
        # 2. (v1.2.3) 원하는 자막 찾기 (ko -> en -> a.ko)
        target_transcript = transcript_list.find_transcript(['ko', 'en', 'a.ko'])
        
        # 3. (v1.2.3) 데이터 가져오기
        transcript_data = target_transcript.fetch()
        
        # 4. (v1.2.3) 텍스트 결합 (part.text 사용)
        full_script = " ".join([part.text.strip() for part in transcript_data])
        return full_script
        
    except (NoTranscriptFound, TranscriptsDisabled) as e:
        # '자막 없음' 또는 '비활성화'는 여기서 잡아서 상위로 전달
        logging.warning(f"ID {video_id}: 자막을 찾을 수 없거나 비활성화됨. ({type(e).__name__})")
        raise e
    except Exception as e:
        # 기타 모든 오류 (예: 네트워크, 비디오 ID 오류 등)
        logging.error(f"ID {video_id}: 예상치 못한 오류 발생 ({e})")
        raise e

# --- 메인 스크립트 실행 ---
if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description="Fetch YouTube transcripts (v1.2.3 Syntax).")
    
    parser.add_argument(
        "input_file", 
        help="Path to the input JSON file (e.g., UC..._videos.json)"
    )
    parser.add_argument(
        "-o", "--output_file", 
        help="Path to the output .jsonl file (results will be appended). "
             "Default: 'result_[input_filename].jsonl'",
        default=None
    )
    parser.add_argument(
        "--batch_size", 
        type=int, 
        default=0,
        help="Number of videos to process in this run. "
             "Default: 0 (process all unprocessed videos)"
    )
    
    args = parser.parse_args()

    if args.output_file is None:
        basename = os.path.basename(args.input_file)
        filename_no_ext, _ = os.path.splitext(basename)
        args.output_file = f"result_{filename_no_ext}.jsonl"
        logging.info(f"출력 파일이 지정되지 않았습니다. 기본값으로 '{args.output_file}'을 사용합니다.")

    processed_urls = load_processed_urls(args.output_file)

    try:
        with open(args.input_file, 'r', encoding='utf-8') as f:
            all_videos = json.load(f)
    except FileNotFoundError:
        logging.error(f"입력 파일을 찾을 수 없습니다: {args.input_file}")
        exit()
    except json.JSONDecodeError:
        logging.error(f"입력 파일이 손상되었습니다: {args.input_file}")
        exit()

    videos_to_process = []
    for video in all_videos:
        if video['url'] not in processed_urls:
            videos_to_process.append(video)
            if args.batch_size > 0 and len(videos_to_process) >= args.batch_size:
                break

    if not videos_to_process:
        logging.info("새로 처리할 영상이 없습니다. 모든 작업이 완료되었습니다.")
        exit()

    logging.info(f"총 {len(videos_to_process)}개의 새 영상을 처리합니다.")

    # 5. (v1.2.3) API 인스턴스(객체)를 한 번만 생성
    api = YouTubeTranscriptApi()
    success_count = 0
    
    with open(args.output_file, 'a', encoding='utf-8') as f_out:
        
        for video in videos_to_process:
            video_id = get_video_id(video['url'])
            if not video_id:
                logging.warning(f"잘못된 URL, 건너뜀: {video['url']}")
                continue

            logging.info(f"처리 중: {video['title']} (ID: {video_id})")
            
            script_content = None
            error_message = None
            
            try:
                # 6. (v1.2.3) 수정된 함수 호출
                script_content = fetch_transcript_v123(api, video_id)
                success_count += 1
            except (NoTranscriptFound, TranscriptsDisabled) as e:
                # 자막이 없는 '정상적인 실패'
                error_message = f"ERROR: Transcript not available or disabled. ({type(e).__name__})"
            except Exception as e:
                # 기타 '예상치 못한 실패'
                error_message = f"ERROR: Unknown error during fetch. ({e})"

            output_data = {
                "title": video['title'],
                "description": video['description'],
                "url": video['url'],
                "date": video['publishedAt'],
                "script": script_content if script_content else error_message
            }
            
            json.dump(output_data, f_out, ensure_ascii=False)
            f_out.write('\n')

    logging.info(f"--- 작업 완료 ---")
    logging.info(f"성공: {success_count} / {len(videos_to_process)}")
    logging.info(f"결과가 '{args.output_file}' 파일에 누적 저장되었습니다.")