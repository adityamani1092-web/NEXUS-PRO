# NEXUS PROTECTION — Fresh Starter ZIP

## Included baseline
- Premium DM start/help menus and inline navigation
- Game Protection menu with Kill/Rob toggles
- One-time own-contact verification (does **not** collect Telegram OTP/password)
- Basic group admin commands: `/ban`, `/unban`, `/mute`, `/unmute`
- Reply `/kill` and `/rob` command auto-delete attempt (requires bot admin permission to delete messages)
- Owner username display and placeholder owner stats/broadcast responses

## Important limitations / not yet implemented
This is a **starter scaffold**, not a complete production bot. The following requested features still need implementation and persistent storage: MongoDB, complete approve/free system, warnings, timed mutes, kick, purge/pin, locks, anti-spam/flood/link/bio rules, filters/media filters, welcome/rules, group settings, robust stats, broadcast registry, and persistent protection.
Third-party game bots cannot be universally intercepted or have actions undone by Telegram Bot API. Deleting a `/kill` or `/rob` command message does not guarantee that another bot has not already processed it. Game protection works only where the game bot integrates/checks NEXUS protection.

## Windows CMD setup
1. Install Python 3.11+ from python.org and enable **Add Python to PATH**.
2. Extract ZIP.
3. Open CMD in the extracted folder.
4. Run:
   ```bat
   py -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   copy .env.example .env
   notepad .env
   ```
5. Put your BotFather token in `BOT_TOKEN` in `.env`. Never share it publicly.
6. Run:
   ```bat
   python bot.py
   ```

## Telegram setup
- Add the bot to your group and promote it to admin.
- Grant **Delete messages**, **Ban users**, and **Restrict members** as needed.
- Set commands in BotFather:
  `start - Start NEXUS Protection`
  `help - Help menu`
  `gameprotection - Game Protection`
  `ban - Ban a member`
  `unban - Unban by user ID`
  `mute - Mute a member`
  `unmute - Unmute a member`
  `stats - Owner stats`
  `broadcast - Owner broadcast`
