import os
import json
from datetime import datetime, timedelta, timezone
from garminconnect import Garmin

EMAIL = os.environ.get("GARMIN_EMAIL")
PASSWORD = os.environ.get("GARMIN_PASSWORD")

# Часовой пояс Москва (UTC+3), чтобы дата всегда совпадала с твоим локальным днем
TZ_MOSCOW = timezone(timedelta(hours=3))

def main():
    client = Garmin(EMAIL, PASSWORD)
    client.login()

    now_local = datetime.now(TZ_MOSCOW)
    today = now_local.date().isoformat()

    # 1. Сводка дня (шаги, пульс покоя, Body Battery)
    stats = client.get_user_summary(today)
    steps = stats.get("totalSteps") or 0
    step_goal = stats.get("dailyStepGoal") or 10000
    rhr = stats.get("restingHeartRate") or 0
    bb = stats.get("bodyBatteryMostRecentValue") or stats.get("bodyBatteryHighestValue") or 0

    # 2. Сон
    sleep_data = client.get_sleep_data(today)
    sleep_dto = (sleep_data or {}).get("dailySleepDTO") or {}
    sleep_sec = sleep_dto.get("sleepTimeSeconds") or 0
    sleep_hours = round(sleep_sec / 3600, 1)
    sleep_score = sleep_dto.get("sleepScores", {}).get("overall", {}).get("value") or 0

    # 3. Последняя тренировка
    activities = client.get_activities(0, 1)
    last_act_name = "Нет записей"
    last_act_sub = "—"
    has_activity_today = False

    if activities:
        act = activities[0]
        act_date = (act.get("startTimeLocal") or "")[:10]
        has_activity_today = (act_date == today)
        name = act.get("activityName") or "Тренировка"
        dist_km = round((act.get("distance") or 0) / 1000, 1)
        dur_min = round((act.get("duration") or 0) / 60)
        avg_hr = act.get("averageHR") or "—"

        last_act_name = f"{name} • {dist_km} км" if dist_km > 0 else name
        last_act_sub = f"{dur_min} мин • {avg_hr} уд/мин"

    payload = {
        "updatedAt": now_local.strftime("%H:%M"),
        "steps": steps,
        "stepGoal": step_goal,
        "bodyBattery": bb,
        "sleepHours": sleep_hours,
        "sleepScore": sleep_score,
        "restingHr": rhr,
        "lastActivityName": last_act_name,
        "lastActivitySub": last_act_sub,
        "hasActivityToday": has_activity_today
    }

    with open("garmin_data.json", "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
