# BurrbyBot - Telegram Bot

## Overview
A Telegram bot for ordering services from Burrbedy. Users can browse products, apply promo codes, and place orders through the bot interface.

## Project Structure
- `main.py` - Main bot logic with handlers for commands and callbacks
- `logger.py` - Custom logging utility with file-based logging
- `params.json` - Bot configuration (token and admin password)
- `promocodes.json` - Promotional codes configuration
- `admin.id` - Stores the admin user ID

## Technology Stack
- Python 3.12
- pyTelegramBotAPI (telebot)

## Running the Bot
The bot runs via the "Telegram Bot" workflow which executes `python main.py`.

## Configuration
- The bot token is stored in `params.json`
- Admin can be set up using the `/setAdmin` command with the password from params.json
- Promo codes are managed in `promocodes.json`

## Commands
- `/start` - Main menu
- `/setAdmin` - Configure admin account
- `/request` - Admin command to respond to orders

## Recent Changes
- 2026-01-21: Initial import and setup in Replit environment
