import os
import requests
from bs4 import BeautifulSoup

# URL de base
base_url = "https://play.pokemonshowdown.com/audio/"
output_dir = "pokemon_audio"
os.makedirs(output_dir, exist_ok=True)

# Récupérer le HTML de la page
r = requests.get(base_url)
soup = BeautifulSoup(r.text, "html.parser")

# Trouver tous les fichiers listés
links = soup.find_all("a", class_="row")

for link in links:
    href = link.get("href")
    if href.endswith(".mp3"):
        file_url = base_url + href.strip("./")
        local_path = os.path.join(output_dir, href.strip("./"))
        try:
            resp = requests.get(file_url)
            if resp.status_code == 200:
                with open(local_path, "wb") as f:
                    f.write(resp.content)
                print(f"{href} téléchargé ✅")
            else:
                print(f"{href} non trouvé ⚠️")
        except Exception as e:
            print(f"Erreur {href}: {e}")

print("✅ Tous les fichiers de la page ont été téléchargés !")
