import asyncio
import os
import threading
from dotenv import load_dotenv
load_dotenv()
config = os.environ

def start_monitoring():
    from application.helpers import monitoring_run
    import asyncio
    asyncio.run(monitoring_run())

if __name__ == "__main__":
    from application.routes import app
    threading.Thread(target=start_monitoring, daemon=True).start()
    app.run(host="127.0.0.1", debug=True, port=config["START_SERVER_PORT"], threaded=True)







