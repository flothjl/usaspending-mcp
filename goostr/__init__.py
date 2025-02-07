import argparse
from .server import mcp


def main():
    parser = argparse.ArgumentParser(
        description="Gives you the ability to interact with usaspending.gov data and also interact with nostr protocol"
    )

    parser.parse_args()
    mcp.run()


if __name__ == "__main__":
    main()
