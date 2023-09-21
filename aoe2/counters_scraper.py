from bs4 import BeautifulSoup
import requests
from tqdm.contrib.concurrent import process_map
import json
from multiprocessing import Manager
from functools import partial
from pathlib import Path
from inflect import engine as inflect_engine

class CountersScraper:
    def __init__(self):
        self.units = dict()
        self.image_folder = Path(__file__).resolve().parent.parent / "pictures" / "aoe2" / "unit_icons"
        self.inflector = inflect_engine()
        assert self.image_folder.exists() and self.image_folder.is_dir()

    def run(self):
        """
        Generates the list of units and the counters
        :return: list of units and their counters
        """
        self.get_unit_links()
        self.add_counters()
        print(json.dumps(self.units, sort_keys=True, indent=4))
        return self.units

    def get_unit_links(self, url="https://ageofempires.fandom.com/wiki/Unit_(Age_of_Empires_II)"):
        """
        Gets the list of units and their url from the wiki
        :param url: wiki page with the list of all units
        """
        r = requests.get(url)
        soup = BeautifulSoup(r.text, 'html5lib')

        table = soup.find(class_="article-table")
        for unit_group in table.find_all("td"):
            for link in unit_group.find_all("a"):
                unit_name = link["title"].replace(" (Age of Empires II)", "")
                wiki_link = f"https://ageofempires.fandom.com{link['href']}"
                self.units[unit_name] = dict()
                self.units[unit_name]["wiki_link"] = wiki_link

    def get_unit_data(self, unit, mp_dict):
        """
        Gets the counters for a single unit by scraping its wiki page
        :param unit: key reference in the dict
        :param mp_dict: multiprocessing dict to mutate
        """
        # Get the page
        wiki_page = self.units[unit]["wiki_link"]
        r = requests.get(wiki_page)
        soup = BeautifulSoup(r.text, 'html5lib')

        # Get the counters
        counters_table = soup.find("th", text="Unit strengths and weaknesses\n")
        if counters_table is None:
            # For Camel Scouts
            counters_table = soup.find("th", text="Unit strengths and weaknesses in Feudal Age\n")
        if counters_table is None:
            print(f"Couldn't find counters table for {unit}")
            strong_vs = None
            weak_vs = None
        else:
            strong_vs, weak_vs = list(), list()
            found_strong = counters_table.parent.find_next_sibling("tr").find_all("td")[-1].text.strip().split(", ")
            found_weak = counters_table.parent.find_next_sibling("tr").find_next_sibling("tr").find_all("td")[-1]\
                .text.strip().split(", ")
            for s, w in zip(found_strong, found_weak):
                s, w = s.replace("and ", ""), w.replace("and ", "")

                singular_s = self.inflector.singular_noun(s)
                if singular_s is False:
                    singular_s = s

                singular_w = self.inflector.singular_noun(w)
                if singular_w is False:
                    singular_w = w

                strong_vs.append(singular_s.capitalize())
                weak_vs.append(singular_w.capitalize())

        # Get image
        image = soup.find("figure", "pi-item pi-image").find("a").find("img").attrs
        img_data = requests.get(image["src"]).content
        img_name = image["data-image-name"]
        with open(self.image_folder / img_name, 'wb') as handler:
            handler.write(img_data)

        # Update dict
        mp_dict[unit] = {
            "strong_vs": None,
            "weak_vs": None,
            "image_name": None
        }
        tmp = mp_dict[unit]
        tmp["strong_vs"] = strong_vs
        tmp["weak_vs"] = weak_vs
        tmp["image_name"] = img_name
        mp_dict[unit] = tmp

    def add_counters(self):
        """
        Uses multiprocessing to get all unit counters
        """
        keys = list(self.units.keys())
        manager = Manager()
        mp_dict = manager.dict()
        process_map(partial(self.get_unit_data, mp_dict=mp_dict), keys)

        # Merge the multi-processed dict back into the main one
        for unit in keys:
            if unit in mp_dict:
                self.units[unit]["strong_vs"] = mp_dict[unit]["strong_vs"]
                self.units[unit]["weak_vs"] = mp_dict[unit]["weak_vs"]
                self.units[unit]["image_name"] = mp_dict[unit]["image_name"]


if __name__ == '__main__':
    cs = CountersScraper()
    units = cs.run()
    with open("unit_counters.json", "w") as f:
        f.write(json.dumps(units, sort_keys=True, indent=4))
