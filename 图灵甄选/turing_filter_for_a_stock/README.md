# Stock Filter Project

This project is designed to filter and sort stocks based on various criteria using a combination of critical filter and weighted voting.

## Setup

1. Clone the repository
2. Create a `.env` file with necessary environment variables
3. Run `python main.py` to start the application

## Modules

- `scorer/`: Contains all the scoring logic for different stock attributes.
- `filter/`: Contains critical filter organized by type.
- `voting/`: Contains the weighted voting logic for non-critical factors.
- `stock_favor_management/`: Manages the stocks in the stock pool and favorites, and handles notifications.

## Usage

Refer to the `main.py` file for usage examples.
