from datetime import datetime
from colorama import Fore as f
import time
import requests
import os
from urllib.parse import urlparse
import selenium
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium import webdriver
from html.parser import HTMLParser
import sys
import psutil
import argparse
import subprocess
import re
import shutil
from tqdm import tqdm

def logger(func):
	def out(msg):
		print(f"{f.GREEN}[{datetime.now().strftime('%H:%M:%S')}]{f.RESET} {msg}")

	def wrapper(*args, **kwargs):
		print(f"{f.GREEN}[{datetime.now().strftime('%H:%M:%S')}]{f.RESET} {f.LIGHTBLUE_EX}{func.__name__}{f.RESET}")
		start = time.time()
		val = func(*args, **kwargs, out=out)
		end = time.time()
		print(f"{f.GREEN}[{datetime.now().strftime('%H:%M:%S')}]{f.RESET} {f.LIGHTBLUE_EX}{func.__name__}{f.RESET} {f.LIGHTGREEN_EX}Completed in {round(end-start, 2)}s{f.RESET}")
		return val


	return wrapper

class htmlparser(HTMLParser):
	
	mods = []


	def handle_starttag(self, tag, attrs):
		if (tag == "a"):
			for attr in attrs:
				if (attr[0] == "href"):
					if ("texture-packs" not in attr[1]):
						self.mods.append(attr[1])

	def handle_endtag(self, tag):
		"awdawd"

	def handle_data(self, data):
		"addddd"

@logger
def DownloadFile(link, out=None):

	

	a = urlparse(link)
	path = os.path.basename(a.path)
	out(f"Downloading {path}")

	try:
		r = requests.get(link, stream=True)
	except requests.exceptions.Timeout:
		out("Request timed out.")
		sys.exit()
	
	data = b''
	size = r.headers.get("content-length", None)
	if (size != None):
		bar = tqdm(total=float(size), desc="Downloading", unit="B", leave=False)
	else:
		bar = tqdm(total=None, desc="Downloading", unit="B", leave=False)
	for i in r.iter_content(8192):
		bar.update(len(i))
		data += i
	bar.close()
	return path, data

@logger
def ParseArgs(args, out=None):
	parser = argparse.ArgumentParser(description="Downloads texture packs from minecraft.net")
	parser.add_argument("-n", "--name", help="Name of modpack", required=True)
	parser.add_argument("-l", "--list", help="Lists available versions", action="store_true")
	parser.add_argument("-d", "--download", help="Downloads the specified version")

	return parser.parse_args(args)

class Browser:
	@logger
	def __init__(self, DriverPath: str, BinaryPath: str, out=None) -> None:
		out("Initializing Browser.")
		self.driver_path = DriverPath
		self.binary_path = BinaryPath
		self.browser = None
		
		options = webdriver.ChromeOptions()
		options.binary_location = self.binary_path
		options.add_experimental_option('excludeSwitches', ['enable-logging'])
		options.add_argument('--log-level=OFF')
		#options.add_argument("--window-size=1920x1080")
		#options.add_argument("--start-maximized")
		self.options = options
		self.process = None

	@logger
	def Start(self, hidden: bool = None, out=None) -> None:
		out("Opening Browser.")
		if (hidden):
			self.options.headless = True
			self.options.add_argument("--disable-gpu")
		self.options.add_argument("--disable-infobars")
		self.options.add_argument("--disable-notifications")
		self.browser = webdriver.Chrome(service=Service(self.driver_path), options=self.options)
		self.process = psutil.Process(self.browser.service.process.pid)

	@logger
	def Close(self, out=None) -> None:
		out("Closing Browser.")
		self.browser.close()

	@logger
	def Get(self, url: str, out=None) -> None:
		#out(f"Navigating to {url}.")
		self.browser.get(url)

@logger
def main(out = None):
	args = ParseArgs(sys.argv[1:])
	
	br = Browser(os.path.dirname(__file__) + "\\..\\chromedriver.exe", os.path.dirname(__file__) + "\\..\\chrome-win\\chrome.exe")

	br.Start(hidden=False)
	br.Get(f"https://www.curseforge.com/minecraft/modpacks/{args.name}/files/all")
	time.sleep(1)
	select = br.browser.find_element(By.ID, "filter-game-version").find_elements(By.XPATH, "*")
	versions = {}
	for i in select:
		if ("1." in i.text):
			if ("Minecraft" not in i.text):
				text = i.text[2:]
				versions[text] = i.get_attribute("value")
	
	if (args.list):
		out("Versions: " + ", ".join(versions.keys()))

	if (args.download):
		if (args.download not in versions.keys()):
			out(f"Version {args.download} not found.")
			br.Close()
			br.process.kill()
		for version in versions.keys():
			if (args.download == version):
				br.Get(f"https://www.curseforge.com/minecraft/modpacks/{args.name}/files/all?filter-game-version={versions[version].replace(':', '%')}")
				time.sleep(1)
				link = br.browser.find_elements(By.TAG_NAME, "td")[1].find_elements(By.TAG_NAME, "a")[0].get_attribute("href")
				br.Get(link)
				time.sleep(1)
				name = br.browser.find_elements(By.CLASS_NAME, "text-sm")
				for i in name:
					if (i.tag_name == "span" and ".zip" in i.text):
						name = i.text
						break
				
				id = link.split("/")[-1]

				directlink = f"https://media.forgecdn.net/files/{id[:4]}/{id[4:]}/{name.replace(' ', '+')}"

				out("Downloading manifest.html")
				
				path, data = DownloadFile(directlink)

				with open(path, "wb") as f:
					f.write(data)

				subprocess.run(["7z.exe", "x", path, "-aoa", "-oextracted", "-y"], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

				parser = htmlparser()
				with open("extracted/modlist.html", "r") as f:
					parser.feed(f.read())
				mods = parser.mods
				os.remove(path)
				os.mkdir("".join(name.split(".")[:-1]))
				packname = "".join(name.split(".")[:-1])
				for mod in range(len(mods)):
					r = re.compile("[0-9]{1,}")
					mat = r.match(mods[mod].split("/")[-1])
					if (mat != None): 
						if (mat.group(0) == mods[mod].split("/")[-1]):
							out("Modpack uses deprecated URLs.")
							br.Close()
							br.process.kill()
							sys.exit()

					link = mods[mod]+ "/files/all?filter-game-version=" + str(versions[version].replace(':', '%'))
					br.Get(link)
					link = br.browser.find_elements(By.TAG_NAME, "td")[1].find_element(By.TAG_NAME, "a").get_attribute("href")

					id = link.split("/")[-1]

					br.Get(link)
					name = br.browser.find_elements(By.CLASS_NAME, "text-sm")
					for i in name:
						if (i.tag_name == "span" and ".jar" in i.text):
							name = i.text
							break

					directlink = f"https://media.forgecdn.net/files/{id[:4]}/{id[4:]}/{name.replace(' ', '+')}"
					
					path, data = DownloadFile(directlink)

					with open(f"{packname}/{path}", "wb") as f:
						f.write(data)

					out(f"Downloaded {mod+1}/{len(mods)}")

				shutil.rmtree("extracted", ignore_errors=True)

				out(f"Saved mods to {os.path.abspath(packname)}")

				br.Close()
				br.process.kill()


main()