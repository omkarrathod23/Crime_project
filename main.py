import sys
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def main():
    print("\nWelcome to the Crime Management System CLI!\n")
    try:
        from src.dashboard import main as dashboard_main
        dashboard_main()
    except ImportError as e:
        logging.error(f"Failed to launch dashboard: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 