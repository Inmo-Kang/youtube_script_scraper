import googleapiclient.discovery
import googleapiclient.errors
import os
import argparse
import json
import csv
import re  # 1. ISO 8601 Duration 파싱을 위한 're' 모듈 임포트
from dotenv import load_dotenv

def parse_iso8601_duration(duration_str):
    """
    ISO 8601 형식의 기간(예: 'PT1M30S')을 총 초(second)로 변환합니다.
    숏츠 판별(60초)을 위해 P...T...S 형식만 정확히 파싱합니다.
    """
    if not duration_str:
        return None
    
    # P(n)DT(n)H(n)M(n)S 형식을 찾기 위한 정규식
    match = re.search(
        r'P(?:(\d+)D)?T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', 
        duration_str
    )
    
    if not match:
        # 'P0D' (0초) 같은 특수 케이스 처리
        if duration_str == 'P0D': return 0
        return None

    days = int(match.group(1) or 0)
    hours = int(match.group(2) or 0)
    minutes = int(match.group(3) or 0)
    seconds = int(match.group(4) or 0)
    
    total_seconds = (days * 86400) + (hours * 3600) + (minutes * 60) + seconds
    return total_seconds

def fetch_channel_id_from_handle(youtube, handle):
    """
    핸들 이름을 사용하여 채널 ID를 조회합니다. (이전과 동일)
    """
    try:
        request = youtube.channels().list(
            part="id",
            forHandle=handle.lstrip('@')
        )
        response = request.execute()

        if "items" in response and response["items"]:
            return response["items"][0]["id"]
        else:
            return None
    except googleapiclient.errors.HttpError as e:
        print(f"핸들 조회 중 API 오류 발생: {e}")
        return None

def get_all_channel_videos(youtube, channel_id):
    """
    (수정됨) 채널 ID의 모든 비디오 정보 + '숏츠 여부'를 가져옵니다.
    """
    try:
        # 1. '업로드 플레이리스트 ID' 가져오기 (이전과 동일)
        channel_request = youtube.channels().list(
            part="contentDetails",
            id=channel_id
        )
        channel_response = channel_request.execute()

        if "items" not in channel_response or not channel_response["items"]:
            print(f"오류: 채널 ID '{channel_id}'의 세부 정보를 찾을 수 없습니다.")
            return

        uploads_playlist_id = channel_response["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

        all_videos = []
        next_page_token = None

        print(f"'{channel_id}' 채널의 비디오 목록을 가져오는 중... (API 2배 소모)")

        while True:
            # 2. (API 호출 1) 플레이리스트의 비디오 ID와 스니펫 가져오기
            playlist_request = youtube.playlistItems().list(
                part="snippet",
                playlistId=uploads_playlist_id,
                maxResults=50,
                pageToken=next_page_token
            )
            playlist_response = playlist_request.execute()

            video_ids_on_page = []
            snippets_map = {} # 나중에 합치기 위해 스니펫 정보 임시 저장

            for item in playlist_response.get("items", []):
                snippet = item.get("snippet", {})
                video_id = snippet.get("resourceId", {}).get("videoId")
                if video_id:
                    video_ids_on_page.append(video_id)
                    snippets_map[video_id] = snippet
            
            if not video_ids_on_page:
                # 이 페이지에 비디오가 없으면 종료
                break

            # 3. (API 호출 2) 가져온 ID 목록으로 '영상 길이(duration)' 조회
            ids_string = ",".join(video_ids_on_page)
            videos_request = youtube.videos().list(
                part="contentDetails",
                id=ids_string
            )
            videos_response = videos_request.execute()

            durations_map = {} # 영상 길이 임시 저장
            for item in videos_response.get("items", []):
                duration_str = item.get("contentDetails", {}).get("duration")
                durations_map[item["id"]] = duration_str

            # 4. (데이터 취합) 스니펫 정보와 영상 길이 정보를 합침
            for video_id in video_ids_on_page:
                snippet = snippets_map.get(video_id)
                duration_str = durations_map.get(video_id) # 비디오가 삭제된 경우 None일 수 있음

                if not snippet:
                    continue # 스니펫 정보가 없으면 건너뜀

                duration_sec = parse_iso8601_duration(duration_str)
                is_short = (duration_sec is not None) and (duration_sec <= 60)

                all_videos.append({
                    "title": snippet.get("title"),
                    "description": snippet.get("description"),
                    "url": f"https://www.youtube.com/watch?v={video_id}",
                    "publishedAt": snippet.get("publishedAt"),
                    "duration_iso8601": duration_str, # (추가) 원본 길이 (예: PT1M5S)
                    "duration_seconds": duration_sec,  # (추가) 초 단위 길이 (예: 65)
                    "is_short": is_short               # (추가) 숏츠 여부 (True/False)
                })

            # (이전과 동일) 다음 페이지 토큰 확인
            next_page_token = playlist_response.get("nextPageToken")
            if not next_page_token:
                break

        print(f"총 {len(all_videos)}개의 비디오를 (길이 정보 포함하여) 성공적으로 가져왔습니다.")
        return all_videos

    except googleapiclient.errors.HttpError as e:
        print(f"비디오 목록 조회 중 API 오류가 발생했습니다: {e}")
    except Exception as e:
        print(f"알 수 없는 오류가 발생했습니다: {e}")

# --- 스크립트 실행 (이 하단은 수정할 필요 없음) ---
if __name__ == "__main__":
    
    load_dotenv()
    API_KEY = os.environ.get("YOUTUBE_API_KEY")

    if not API_KEY:
        print("="*50)
        print("오류: 'YOUTUBE_API_KEY'를 .env 파일에서 찾을 수 없습니다.")
        print("="*50)
        exit()

    parser = argparse.ArgumentParser(description="Scrape all video info from a YouTube channel.")
    parser.add_argument("identifier", help="The YouTube Channel ID (e.g., UC...) or Handle (e.g., @moneycoach)")
    
    args = parser.parse_args()
    user_input = args.identifier
    final_channel_id = None

    try:
        youtube = googleapiclient.discovery.build(
            "youtube", "v3", developerKey=API_KEY)

        if user_input.startswith("UC"):
            print(f"입력값 '{user_input}'는 채널 ID로 간주합니다.")
            final_channel_id = user_input
        else:
            print(f"입력값 '{user_input}'는 핸들로 간주합니다. 채널 ID를 조회합니다...")
            final_channel_id = fetch_channel_id_from_handle(youtube, user_input)
            
            if final_channel_id:
                print(f"핸들에 해당하는 채널 ID '{final_channel_id}'를 찾았습니다.")
            else:
                print(f"오류: 핸들 '{user_input}'에 해당하는 채널을 찾을 수 없습니다.")
                exit()

        if final_channel_id:
            videos = get_all_channel_videos(youtube, final_channel_id)
            
            if videos and len(videos) > 0:
                print("\n--- 상위 3개 비디오 샘플 ---")
                for video in videos[:3]:
                    print(f"제목: {video['title']} (길이: {video['duration_seconds']}초, 숏츠: {video['is_short']})")
                    print(f"URL: {video['url']}\n")

                # --- 파일 저장 로직 (자동으로 새 필드 포함) ---
                base_filename = final_channel_id 
                
                # JSON 저장 (새 필드 자동 포함)
                filename_json = f"{base_filename}_videos.json"
                with open(filename_json, 'w', encoding='utf-8') as f_json:
                    json.dump(videos, f_json, ensure_ascii=False, indent=4)
                print(f"✅ JSON 결과가 {filename_json} 파일로 저장되었습니다.")
                
                # CSV 저장 (새 필드 자동 포함)
                filename_csv = f"{base_filename}_videos.csv"
                fieldnames = videos[0].keys() # 헤더에 'duration...', 'is_short' 자동 추가됨
                
                with open(filename_csv, 'w', newline='', encoding='utf-8-sig') as f_csv:
                    writer = csv.DictWriter(f_csv, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(videos)
                
                print(f"✅ CSV 결과가 {filename_csv} 파일로 저장되었습니다. (엑셀에서 열 수 있음)")

            elif videos is not None and len(videos) == 0:
                print("채널은 찾았으나, 업로드된 비디오가 없습니다.")

    except googleapiclient.errors.HttpError as e:
        print(f"API 서비스 빌드 중 오류가 발생했습니다 (API 키를 확인하세요): {e}")
    except Exception as e:
        print(f"스크립트 실행 중 알 수 없는 오류 발생: {e}")