import requests
import datetime
import pytz
from icalendar import Calendar
import json
import re  # 정규식용

# ✅ CodeEngn 캘린더 iCal 주소
ICAL_URL = "https://calendar.google.com/calendar/ical/iodve4qkhn5qpunvvj3p1tlseg%40group.calendar.google.com/public/basic.ics"

# ✅ Slack Webhook URL
SLACK_WEBHOOK_URL = "https://hooks.slack.com/services/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"

# ✅ 오늘 및 2개월 후 날짜 계산 (KST 기준)
KST = pytz.timezone("Asia/Seoul")
today = datetime.datetime.now(KST).date()
end_date = today + datetime.timedelta(days=60)

# ✅ iCal 캘린더 가져오기
ical_data = requests.get(ICAL_URL).content
calendar = Calendar.from_ical(ical_data)

# ✅ 이벤트 필터링 및 정리
events = []
for component in calendar.walk():
    if component.name == "VEVENT":
        start = component.get("dtstart").dt
        if isinstance(start, datetime.datetime):
            start = start.date()
        if today <= start <= end_date:
            summary = str(component.get("summary"))
            
            url = ""
            description = component.get("description")
            if description:
                # <a href="URL"> 형태에서 URL만 추출
                match = re.search(r'<a href="([^"]+)"', description)
                if match:
                    url = match.group(1)

            dday = (start - today).days
            dday_str = "D-Day" if dday == 0 else f"D-{dday}"
            events.append({
                "date": start,
                "summary": summary,
                "url": url,
                "dday": dday_str
            })

# ✅ 최신순 정렬 (오름차순)
events = sorted(events, key=lambda x: x["date"])

# ✅ Block Kit 메시지 구성
if events:
    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "📢 *다가오는 보안 대회 일정 (60일 이내)*"
            }
        }
    ]
    for e in events:
        date_str = e["date"].strftime("%Y-%m-%d")
        text = f"`{e['dday']}` [{date_str}] {e['summary']}"
        section_block = {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": text
            }
        }
        if e["url"]:
            section_block["accessory"] = {
                "type": "button",
                "text": {
                    "type": "plain_text",
                    "text": "대회 정보 보기"
                },
                "url": e["url"]
            }
        blocks.append(section_block)
        blocks.append({"type": "divider"})
    payload = {
        "blocks": blocks
    }
else:
    payload = {
        "text": "📭 앞으로 60일 이내에 예정된 보안 대회가 없습니다."
    }

# ✅ Slack으로 전송 (requests)
response = requests.post(SLACK_WEBHOOK_URL, json=payload)
if response.status_code != 200:
    print(f"Slack 전송 실패: {response.status_code} - {response.text}")
