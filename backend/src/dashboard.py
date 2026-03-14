import sys
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def show_menu():
    print("\n==== Crime Management System Dashboard ====")
    print("1. Explore Data")
    print("2. Predict Crime Type")
    print("3. Detect Hotspots")
    print("4. Analyze Time Trends")
    print("5. Exit")

def handle_choice(choice):
    if choice == '1':
        print("[EDA] Data exploration coming soon...")
    elif choice == '2':
        print("[Predict] Crime type prediction coming soon...")
    elif choice == '3':
        print("[Hotspot] Hotspot detection coming soon...")
    elif choice == '4':
        print("[Trends] Time trend analysis coming soon...")
    elif choice == '5':
        print("Exiting dashboard. Goodbye!")
        sys.exit(0)
    else:
        print("Invalid choice. Please select a valid option.")

def main():
    while True:
        show_menu()
        choice = input("Enter your choice: ")
        handle_choice(choice)

if __name__ == "__main__":
    main() 