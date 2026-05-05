# Cron/scheduler removed — reward distribution is handled manually.


logger = logging.getLogger(__name__)
scheduler = BackgroundScheduler(timezone="UTC")


def _current_period(schedule: str) -> str:
    now = datetime.utcnow()
    if schedule == "monthly":
        return now.strftime("%Y-%m")
    # Default: weekly ISO
    return now.strftime("%Y-W%W")


def run_referral_rewards():
    """
    For every referred user with an active delegation to cur8,
    calculate and upsert a ReferralReward record for the current period.
    Rewards are NOT distributed automatically — admin triggers distribution manually.
    """
    db: Session = SessionLocal()
    try:
        schedule = get_config(db, "cron_schedule", "weekly")
        bonus_pct = float(get_config(db, "delegation_bonus_percent", "10")) / 100.0
        period = _current_period(schedule)

        referred_users = db.query(JoinUser).filter(
            JoinUser.referrer_steem.isnot(None),
            JoinUser.steem_username.isnot(None),
        ).all()

        logger.info(f"Referral reward run: period={period}, users={len(referred_users)}")

        for user in referred_users:
            try:
                delegation_sp = get_delegation_to_cur8(user.steem_username)
                if delegation_sp <= 0:
                    continue

                # Estimate weekly curation reward from delegation (simplified: 10% APR / 52 weeks)
                estimated_weekly_reward = delegation_sp * 0.10 / 52
                reward_sp = round(estimated_weekly_reward * bonus_pct, 6)

                existing = db.query(ReferralReward).filter_by(
                    referrer_steem=user.referrer_steem,
                    referee_steem=user.steem_username,
                    period=period,
                ).first()

                if existing:
                    existing.delegation_sp = delegation_sp
                    existing.reward_sp = reward_sp
                else:
                    db.add(ReferralReward(
                        id=str(uuid.uuid4()),
                        referrer_steem=user.referrer_steem,
                        referee_steem=user.steem_username,
                        period=period,
                        delegation_sp=delegation_sp,
                        reward_sp=reward_sp,
                    ))

                db.commit()
                logger.info(f"Reward: {user.referrer_steem} ← {user.steem_username} | {reward_sp:.6f} SP")

            except Exception as e:
                logger.error(f"Error processing {user.steem_username}: {e}")
                db.rollback()

    finally:
        db.close()


def start_scheduler():
    db = SessionLocal()
    try:
        schedule = get_config(db, "cron_schedule", "weekly")
    finally:
        db.close()

    if schedule == "monthly":
        scheduler.add_job(run_referral_rewards, "cron", day=1, hour=2, minute=0, id="referral_rewards")
    else:
        scheduler.add_job(run_referral_rewards, "cron", day_of_week="mon", hour=2, minute=0, id="referral_rewards")

    scheduler.start()
    logger.info(f"Scheduler started: referral_rewards ({schedule})")


def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown()
