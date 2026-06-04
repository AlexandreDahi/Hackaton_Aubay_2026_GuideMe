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
            function normalize(text) {
                if (!text) return "";
                return text
                    .toString()
                    .replace(/\s+/g, " ")
                    .replace(/[…\.]{2,}$/u, "")
                    .trim();
            }

            function isVisible(el) {
                const style = window.getComputedStyle(el);
                const rect = el.getBoundingClientRect();
                return style.visibility !== "hidden" && style.display !== "none" && rect.width > 0 && rect.height > 0;
            }

            function getLabel(el) {
                if (el.id) {
                    const lbl = document.querySelector(`label[for="${el.id}"]`);
                    if (lbl) return normalize(lbl.innerText);
                }
                if (el.getAttribute('aria-label')) return normalize(el.getAttribute('aria-label'));
                if (el.placeholder) return normalize(el.placeholder);
                if (el.title) return normalize(el.title);
                if (el.innerText) {
                    const text = normalize(el.innerText);
                    if (text.length > 0 && text.length < 80) return text;
                }
                const parent = el.closest('[aria-label]');
                if (parent) return normalize(parent.getAttribute('aria-label'));
                return normalize(el.name || el.id || el.getAttribute('alt') || el.getAttribute('aria-describedby') || "");
            }

            function getDescription(el) {
                const ariaDesc = el.getAttribute('aria-describedby');
                if (ariaDesc) {
                    const descEl = document.getElementById(ariaDesc);
                    if (descEl) return normalize(descEl.innerText);
                }
                return normalize(el.title || el.getAttribute('data-tooltip') || "");
            }

            function addUnique(list, item) {
                if (!item.label || item.label.length === 0) return;
                if (item.label.toLowerCase() === "sans nom") return;
                const exists = list.some(i => i.label === item.label && i.type === item.type);
                if (!exists) list.push(item);
            }

            const boutons = [];
            document.querySelectorAll("button, [role='button'], a[href], input[type='submit'], input[type='button']").forEach(el => {
                if (!isVisible(el)) return;
                const label = getLabel(el);
                if (!label) return;
                const href = el.href || "";
                if (href && href.startsWith("javascript:")) return;
                const desc = href ? `Lien vers : ${href.substring(0, 100)}` : getDescription(el);
                addUnique(boutons, {
                    label: label.substring(0, 80),
                    type: href ? "lien" : "bouton",
                    description: desc || "Action interactive"
                });
            });

            const champs = [];
            document.querySelectorAll("input:not([type=hidden]):not([disabled]), textarea:not([disabled]), select:not([disabled]), [contenteditable='true']").forEach(el => {
                if (!isVisible(el)) return;
                const label = getLabel(el);
                if (!label) return;
                const type = el.tagName.toLowerCase() === 'input' ? (el.type || 'text') : el.tagName.toLowerCase();
                addUnique(champs, {
                    label: label.substring(0, 80),
                    type: `champ ${type}`,
                    description: `Type: ${type}${el.required ? ' (obligatoire)' : ''}`
                });
            });

            const menus = [];
            document.querySelectorAll("nav a, [role='navigation'] a, [role='menuitem']").forEach(el => {
                if (!isVisible(el)) return;
                const label = getLabel(el);
                if (!label) return;
                const href = el.href || "";
                if (href && href.startsWith("javascript:")) return;
                addUnique(menus, {
                    label: label.substring(0, 80),
                    type: "menu",
                    description: href ? `Navigation vers : ${href.substring(0, 100)}` : "Élément de navigation"
                });
            });

            const images = [];
            document.querySelectorAll("img[alt], svg[aria-label], [role='img'][aria-label]").forEach(el => {
                if (!isVisible(el)) return;
                const alt = normalize(el.alt || el.getAttribute('aria-label'));
                if (!alt) return;
                addUnique(images, {
                    label: alt.substring(0, 80),
                    type: "image",
                    description: "Image / icône interactive"
                });
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