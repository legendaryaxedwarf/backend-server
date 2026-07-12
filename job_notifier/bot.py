import discord
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

import config
from db import fetch_new_jobs

intents = discord.Intents.default()
client = discord.Client(intents=intents)
scheduler = AsyncIOScheduler(timezone="Asia/Seoul")


def build_messages(jobs):
    """디스코드 임베드 리스트 생성 (2000자/25필드 제한 회피용으로 직무별 분리)"""
    from collections import defaultdict

    grouped = defaultdict(list)
    for j in jobs:
        grouped[j["job_part"]].append(j)

    embeds = []
    for part, items in grouped.items():
        embed = discord.Embed(
            title=f"📢 [{part}] 신규 채용 공고 {len(items)}건",
            color=0x5865F2,
        )
        for j in items[:10]:  # 임베드당 최대 10개
            pay = j["pay"] or "회사내규"
            career = j["personal_history"] or "무관"
            region = j["region"] or "-"
            end_at = j["end_at"] or "상시"
            embed.add_field(
                name=f"{j['company_name']} · {j['post_title']}",
                value=(
                    f"🏷️ {j['source']} | 📍 {region} | 💼 {career}\n"
                    f"💰 {pay} | ⏰ ~{end_at}\n"
                    f"🔗 {j['job_url']}"
                ),
                inline=False,
            )
        if len(items) > 10:
            embed.set_footer(text=f"외 {len(items) - 10}건 더 있음")
        embeds.append(embed)

    return embeds


async def send_notification():
    channel = client.get_channel(config.CHANNEL_ID)
    if channel is None:
        print(f"[ERROR] 채널을 찾을 수 없음: {config.CHANNEL_ID}")
        return

    try:
        jobs = fetch_new_jobs()
    except Exception as e:
        print(f"[ERROR] DB 조회 실패: {e}")
        return

    if not jobs:
        print("[INFO] 신규 공고 없음")
        return

    embeds = build_messages(jobs)
    for embed in embeds:
        await channel.send(embed=embed)
    print(f"[INFO] 알림 전송 완료: {len(jobs)}건")


@client.event
async def on_ready():
    print(f"[INFO] 봇 로그인: {client.user}")

    scheduler.add_job(
        send_notification,
        CronTrigger(hour=config.NOTIFY_HOUR, minute=config.NOTIFY_MINUTE),
        id="daily_job_notify",
        replace_existing=True,
    )
    scheduler.start()
    print(f"[INFO] 스케줄러 시작: 매일 {config.NOTIFY_HOUR:02d}:{config.NOTIFY_MINUTE:02d}")


client.run(config.DISCORD_TOKEN)
