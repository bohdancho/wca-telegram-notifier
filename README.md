This bot notifies a selected user via Telegram about competitions that were announced yesterday on WCA.
It runs every day in a scheduled GitHub Action.

Running locally:
```bash
python -m venv venv
source ./venv/bin/activate
pip install -r requirements.txt
python bot.py
```

Don't forget to provide the environment variables and secrets.
