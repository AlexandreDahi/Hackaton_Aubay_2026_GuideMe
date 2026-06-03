import asyncio
import json
from playwright.async_api import async_playwright

URL = "https://aubay.com/#contacts"

async def analyser_page(url):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # Ouvre un vrai navigateur
        page = await browser.new_page()

        print(f"🌐 Chargement de : {url}")
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_timeout(3000)  # Attend 3s que le JS se charge

        resultat = await page.evaluate("""() => {
            function getLabel(el) {
                if (el.id) {
                    const lbl = document.querySelector(`label[for="${el.id}"]`);
                    if (lbl) return lbl.innerText.trim();
                }
                if (el.getAttribute('aria-label')) return el.getAttribute('aria-label');
                if (el.placeholder) return el.placeholder;
                if (el.title) return el.title;
                if (el.innerText && el.innerText.trim().length < 80) return el.innerText.trim();
                const parent = el.closest('[aria-label]');
                if (parent) return parent.getAttribute('aria-label');
                return el.name || el.id || el.className.split(' ')[0] || "sans nom";
            }

            function getDescription(el) {
                const ariaDesc = el.getAttribute('aria-describedby');
                if (ariaDesc) {
                    const descEl = document.getElementById(ariaDesc);
                    if (descEl) return descEl.innerText.trim();
                }
                return el.title || el.getAttribute('data-tooltip') || "—";
            }

            // BOUTONS & LIENS
            const boutons = [];
            document.querySelectorAll("button, [role='button'], a[href]").forEach(el => {
                const label = getLabel(el);
                const href = el.href || "";
                const desc = href ? `Lien vers : ${href.substring(0, 80)}` : getDescription(el);
                if (label) boutons.push([label.substring(0, 60), desc.substring(0, 100)]);
            });

            // CHAMPS REMPLISSABLES
            const champs = [];
            document.querySelectorAll("input, textarea, select, [contenteditable='true']").forEach(el => {
                const label = getLabel(el);
                const type = el.type || el.tagName.toLowerCase();
                const desc = `Type: ${type}` + (el.required ? " (obligatoire)" : "");
                champs.push([label.substring(0, 60), desc]);
            });

            // MENUS / NAVIGATION
            const menus = [];
            document.querySelectorAll("nav, [role='navigation'], [role='menu'], [role='menuitem']").forEach(el => {
                const label = getLabel(el);
                if (label) menus.push([label.substring(0, 60), "Élément de navigation"]);
            });

            // IMAGES / ICONES interactives
            const images = [];
            document.querySelectorAll("img[alt], svg[aria-label]").forEach(el => {
                const alt = el.alt || el.getAttribute('aria-label') || "";
                if (alt) images.push([alt.substring(0, 60), "Image/icône"]);
            });

            return { boutons, champs, menus, images };
        }""")

        await browser.close()

        print("\n===== RÉSULTAT DE L'ANALYSE =====\n")

        print(f"🔘 BOUTONS & LIENS ({len(resultat['boutons'])}) :")
        print(json.dumps(resultat['boutons'], ensure_ascii=False, indent=2))

        print(f"\n📝 CHAMPS REMPLISSABLES ({len(resultat['champs'])}) :")
        print(json.dumps(resultat['champs'], ensure_ascii=False, indent=2))

        print(f"\n🧭 MENUS / NAVIGATION ({len(resultat['menus'])}) :")
        print(json.dumps(resultat['menus'], ensure_ascii=False, indent=2))

        print(f"\n🖼️  IMAGES / ICÔNES ({len(resultat['images'])}) :")
        print(json.dumps(resultat['images'], ensure_ascii=False, indent=2))

        # Sauvegarde en JSON
        with open("analyse_page.json", "w", encoding="utf-8") as f:
            json.dump(resultat, f, ensure_ascii=False, indent=2)
        print("\n💾 Résultat sauvegardé dans analyse_page.json")

        return resultat

if __name__ == "__main__":
    asyncio.run(analyser_page(URL))