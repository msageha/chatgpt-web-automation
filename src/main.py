import argparse
import logging
import os

from src.client import ChatGPTWebClient
from src.config import Config


def get_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="ChatGPT Web Client with model selection and image input"
    )
    parser.add_argument(
        "--prompt",
        type=str,
        default="Hello, how do you work?",
        help="Prompt to send to ChatGPT",
    )
    parser.add_argument(
        "--headless",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Run Chrome in headless mode",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        help="Log level (DEBUG, INFO, WARNING, ERROR)",
    )
    parser.add_argument(
        "--model", type=str, default="gpt-4", help="Model name to select"
    )
    parser.add_argument("--image", type=str, help="Path to an image to send")
    return parser.parse_args()


def main():
    args = get_args()
    email = os.getenv("CHATGPT_EMAIL")
    password = os.getenv("CHATGPT_PASSWORD")

    config = Config(
        email=email,
        password=password,
        headless=args.headless,
        log_level=args.log_level,
    )
    config.setup_logging()

    logger = logging.getLogger(__name__)
    logger.info("Starting ChatGPT Web Client...")

    client = ChatGPTWebClient(config)
    try:
        client.access_homepage()
        client.login()
        # client.select_model(args.model)
        client.send_message(args.prompt)

        if args.image:
            client.send_image(args.image)
        response = client.wait_for_response()
        logger.info("ChatGPT Response:\n%s", response)
    except Exception as e:
        logger.error("An error occurred during the interaction: %s", e)
    finally:
        client.close()


if __name__ == "__main__":
    main()
