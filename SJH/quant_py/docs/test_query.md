from bs4 import BeautifulSoup

html_path = r"C:\Users\kosa\.gemini\antigravity-ide\brain\2c12c07b-f08d-485c-bf72-1b6e5048641e\scratch\selenium_render.html"
with open(html_path, "r", encoding="utf-8") as f:
    soup = BeautifulSoup(f.read(), "html.parser")

links_path = r"C:\Users\kosa\.gemini\antigravity-ide\brain\2c12c07b-f08d-485c-bf72-1b6e5048641e\scratch\links_list.txt"
with open(links_path, "w", encoding="utf-8") as f:
    for idx, a in enumerate(soup.find_all("a")):
        text = a.text.strip()
        href = a.get_attribute_list("href")[0] or ""
        cls = " ".join(a.get_attribute_list("class") or [])
        id_attr = a.get("id") or ""
        f.write(f"[{idx}] Text={repr(text)}, href={repr(href)}, class={repr(cls)}, id={repr(id_attr)}\n")
        
print("Wrote links to links_list.txt")





