import time
import logging
from utils.panes import start_pane_printer, printUL, printUR, printLL, printLR, get_user_input, stop_pane_printer

# Configure logging
logging.basicConfig(level=logging.INFO)

# Start the pane printer
start_pane_printer()

# Example usage
time.sleep(1)  # Give some time for the curses application to initialize
printUL("Initial text for the upper left pane")
printUR("Initial text for the upper right pane")
printLR("Initial text for the lower right pane")

# Main loop to process input and update panes
try:
    while True:
        user_input = get_user_input()  # This call will block until there is user input
        logging.info("userinput is " + str(user_input))
        if user_input:
            # Process the input and print to appropriate pane
            if user_input.startswith("UL:"):
                printUL(user_input[3:].strip())
            elif user_input.startswith("UR:"):
                printUR(user_input[3:].strip())
            elif user_input.startswith("LL:"):
                printLL(user_input[3:].strip())
            elif user_input.startswith("LR:"):
                printLR(user_input[3:].strip())
except KeyboardInterrupt:
    print("\nExiting...")
finally:
    stop_pane_printer()  # Ensure the curses loop stops

