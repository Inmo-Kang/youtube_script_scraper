import json
import argparse
import os
import logging

# --- 로깅 설정 ---
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def format_for_google_doc(video_data):
    """
    단일 JSON 객체를 Google Doc 붙여넣기용 텍스트 형식으로 변환합니다.
    """
    output_lines = []
    
    # 1. Title (부제목 스타일) - 텍스트로 '부제목' 느낌을 줍니다.
    output_lines.append(f"## {video_data.get('title', '제목 없음')}\n")
    
    # 2. Description (제목3 스타일)
    output_lines.append("### Description\n")
    output_lines.append(f"{video_data.get('description', '내용 없음')}\n")
    
    # 3. Date (제목3 스타일)
    output_lines.append("### Date\n")
    output_lines.append(f"{video_data.get('date', '날짜 없음')}\n")
    
    # 4. Script (제목3 스타일)
    output_lines.append("### Script\n")
    script_content = video_data.get('script', '스크립트 없음')
    
    # 스크립트가 성공했는지, 실패했는지 확인
    if script_content and script_content.startswith("ERROR:"):
        # 실패한 경우, 오류 메시지를 그대로 출력
        output_lines.append(f"{script_content}\n")
    else:
        # 성공한 경우, 가독성을 위해 문단처럼 보이도록 처리 (선택 사항)
        # (스크립트가 너무 길 경우, 문단 구분이 유용할 수 있습니다.)
        # 여기서는 단순 텍스트로 붙여넣습니다.
        output_lines.append(f"{script_content}\n")
    
    # 각 영상 사이에 명확한 구분선 추가
    output_lines.append("\n" + "="*80 + "\n\n")
    
    return "".join(output_lines)

# --- 메인 스크립트 실행 ---
if __name__ == "__main__":
    
    # --- 1. 아규먼트 설정 ---
    parser = argparse.ArgumentParser(description="Convert .jsonl transcript file to a text document.")
    
    parser.add_argument(
        "input_file", 
        help="Path to the input .jsonl file (e.g., result_...jsonl)"
    )
    
    args = parser.parse_args()

    # --- 2. 출력 파일 이름 자동 생성 ---
    # 입력 파일(result_...jsonl) -> 출력 파일(doc_result_....txt)
    basename = os.path.basename(args.input_file)
    filename_no_ext, _ = os.path.splitext(basename)
    output_filename = f"doc_{filename_no_ext}.txt"

    logging.info(f"입력 파일: {args.input_file}")
    logging.info(f"출력 파일: {output_filename}")

    # --- 3. JSONL 파일 읽기 및 TXT 파일 쓰기 ---
    total_count = 0
    try:
        # 'w' 모드: 실행할 때마다 txt 파일을 새로 씁니다. (누적 아님)
        with open(output_filename, 'w', encoding='utf-8') as f_out:
            
            with open(args.input_file, 'r', encoding='utf-8') as f_in:
                for line in f_in:
                    try:
                        # JSONL 파일 한 줄 읽기
                        video_data = json.loads(line)
                        
                        # 텍스트 형식으로 변환
                        formatted_text = format_for_google_doc(video_data)
                        
                        # .txt 파일에 쓰기
                        f_out.write(formatted_text)
                        total_count += 1
                        
                    except json.JSONDecodeError:
                        logging.warning(f"손상된 줄(입력) 건너뜀: {line.strip()}")

    except FileNotFoundError:
        logging.error(f"입력 파일을 찾을 수 없습니다: {args.input_file}")
        exit()
    except Exception as e:
        logging.error(f"파일 처리 중 오류 발생: {e}")
        exit()

    logging.info(f"--- 작업 완료 ---")
    logging.info(f"총 {total_count}개의 영상 데이터를 {output_filename} 파일로 변환했습니다.")