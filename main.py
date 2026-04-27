import time
from app.services.outreach import run_outreach


def start_loop():
    print("🚀 Outreach bot started (24/7 mode)\n")

    while True:
        try:
            print("📤 Running outreach cycle...\n")

            run_outreach()

            print("\n✅ Cycle complete")
            print("⏳ Sleeping for 1 hour...\n")

            time.sleep(3600)  # 1 hour delay

        except Exception as e:
            print(f"❌ Error occurred: {e}")
            print("🔁 Retrying in 60 seconds...\n")
            time.sleep(60)


if __name__ == "__main__":
    start_loop()
