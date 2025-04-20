import os
from dotenv import load_dotenv
from app import create_app

load_dotenv()

app = create_app()


def main():
    debug = os.environ.get("FLASK_DEBUG", "False").lower() == "true"
    app.run(debug=debug, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))


if __name__ == "__main__":
    main()
