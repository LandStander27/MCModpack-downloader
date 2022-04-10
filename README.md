# MCModpack-downloader
Downloads MC modpacks from curseforge without the need of the curseforge desktop app

Install directions:
---
1. Download code as a zip and extract it to anywhere
2. Download a build of chromium (here: https://download-chromium.appspot.com/) and place the chrome-win folder into the root. (Make sure it's named "chrome-win")
4. Run pip install -r requirements.txt using the requirements.txt in the root, using Python 3.10
5. Run py ./app to run

- The folder structure should look like this
```
app -> Program
chrome-win -> Chromium
chromedriver.exe
7z.exe
requirements.txt
```

#Commands
## Help
```
-h, --help
```
- Just shows these commands.
## Name
```
-n NAME, --name NAME
```
- Sets the name of the modpack to download.
## List
```
-l, --list
```
- Lists all available versions for modpack.
## Download
```
-d VERSION, --download VERSION
```
- Downloads the modpack with the given version.