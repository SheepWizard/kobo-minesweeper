# Kobo Minesweeper
Play minesweper on your Kobo device. Click on the cells to open, hold to place a flag. Try open all the cells without hitting a mine 😫

![](https://github.com/SheepWizard/kobo-minesweeper/blob/main/screenshots/screenshot_2.png?raw=true)

# Video

https://www.youtube.com/watch?v=MJ06zaX2aZM

# Installation

1. (optional)
  Stop Nickel from scanning hidden directories. Find out how to do this [here](https://github.com/koreader/koreader/wiki/Installation-on-Kobo-devices#important-notes).

2. Install [FBink](https://www.mobileread.com/forums/showthread.php?t=299110"), python, [py-fbink](https://github.com/NiLuJe/py-fbink), and [pillow](https://pypi.org/project/Pillow/). All of this can be done by installing [kobo-stuff](https://www.mobileread.com/forums/showthread.php?t=254214)

3. Add all files and directories from repo (excluding screenshots and readme) into `.adds/minesweeper/` directory on your kobo. (`/mnt/onboard/.adds/minesweeper/` if you have root access)

4. Install [NickelMenu](https://github.com/pgaskin/NickelMenu/releases) to add a way to run the python script

5. Add this too your NickelMenu config
```
menu_item:main:Minesweeper Easy:cmd_spawn:quiet:python /mnt/onboard/.adds/minesweeper/minesweeper.py
```
You can also configure the size of the minesweeper board with arguments
```
python /mnt/onboard/.adds/minesweeper/minesweeper.py -x 16 -y 16 -mines 40
```

*This has only be tested on a Kobo Clara HD*

# More screenshots

![](https://github.com/SheepWizard/kobo-minesweeper/blob/main/screenshots/screenshot_3.png?raw=true)
![](https://github.com/SheepWizard/kobo-minesweeper/blob/main/screenshots/screenshot_4.png?raw=true)
![](https://github.com/SheepWizard/kobo-minesweeper/blob/main/screenshots/screenshot_1.png?raw=true)

