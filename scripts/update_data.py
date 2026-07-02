#!/usr/bin/env python3
"""
Rebuild the AoE2:DE coach reference files from the SiegeEngineers/aoe2techtree repo.

Usage:
    python3 scripts/update_data.py

Downloads data.json + English strings, then regenerates:
    references/civs/<civ>.md   - one file per civilization (bonuses, tech tree, gaps)
    references/units.md        - stats for every trainable military unit
    references/civ_index.md    - one-line summary of every civ

Run this whenever a new patch / DLC lands to keep the coach accurate.
Requires network access to raw.githubusercontent.com. No third-party packages.
"""

import json
import os
import re
import sys
import urllib.request

BASE = "https://raw.githubusercontent.com/SiegeEngineers/aoe2techtree/master/data"
HERE = os.path.dirname(os.path.abspath(__file__))
REFS = os.path.join(HERE, "..", "references")

UNIT_NAME_OFFSET = 9000   # LanguageNameId + 9000 = key in strings.json (units/buildings)
TECH_NAME_OFFSET = 10000  # LanguageNameId + 10000 = key in strings.json (techs)

ARMOR_CLASSES = {
    1: "Infantry", 2: "Turtle Ships", 3: "pierce", 4: "melee", 5: "War Elephants",
    8: "Cavalry", 11: "All Buildings", 13: "Stone Defense", 14: "Predator Animals",
    15: "Archers", 16: "Ships", 17: "Rams/Trebs/Siege Towers", 18: "Trees",
    19: "Unique Units", 20: "Siege Weapons", 21: "Standard Buildings",
    22: "Walls & Gates", 23: "Gunpowder Units", 24: "Boars", 25: "Monks",
    26: "Castles", 27: "Spearmen", 28: "Cavalry Archers", 29: "Eagle Warriors",
    30: "Camels", 32: "Condottieri", 34: "Fishing Ships", 35: "Mamelukes",
    36: "Heroes and Kings", 37: "Hussite Wagons", 38: "Skirmishers",
}

# Upgrade lines, defined by exact English unit names (self-validating: the script
# fails loudly if a name disappears after a patch, prompting a quick fix here).
LINES = [
    ("Barracks", "Militia line", ["Militia", "Man-at-Arms", "Long Swordsman", "Two-Handed Swordsman", "Champion"]),
    ("Barracks", "Spearman line", ["Spearman", "Pikeman", "Halberdier"]),
    ("Barracks", "Eagle line", ["Eagle Scout", "Eagle Warrior", "Elite Eagle Warrior"]),
    ("Archery Range", "Archer line", ["Archer", "Crossbowman", "Arbalester"]),
    ("Archery Range", "Skirmisher line", ["Skirmisher", "Elite Skirmisher", "Imperial Skirmisher"]),
    ("Archery Range", "Cavalry Archer line", ["Cavalry Archer", "Heavy Cavalry Archer"]),
    ("Archery Range", "Hand Cannoneer", ["Hand Cannoneer"]),
    ("Archery Range", "Elephant Archer line", ["Elephant Archer", "Elite Elephant Archer"]),
    ("Archery Range", "Slinger", ["Slinger"]),
    ("Archery Range", "Genitour line", ["Genitour", "Elite Genitour"]),
    # Winged Hussar replaces Hussar for the civs that have it (Poles, Lithuanians);
    # it is civ-exclusive so it is never reported as "missing" for other civs.
    ("Stable", "Scout line", ["Scout Cavalry", "Light Cavalry", "Hussar", "Winged Hussar"]),
    ("Stable", "Knight line", ["Knight", "Cavalier", "Paladin"]),
    ("Stable", "Camel line", ["Camel Rider", "Heavy Camel Rider", "Imperial Camel Rider"]),
    ("Stable", "Battle Elephant line", ["Battle Elephant", "Elite Battle Elephant"]),
    ("Stable", "Steppe Lancer line", ["Steppe Lancer", "Elite Steppe Lancer"]),
    ("Stable", "Shrivamsha Rider line", ["Shrivamsha Rider", "E. Shrivamsha Rider"]),
    ("Siege Workshop", "Ram line", ["Battering Ram", "Capped Ram", "Siege Ram"]),
    ("Siege Workshop", "Mangonel line", ["Mangonel", "Onager", "Siege Onager"]),
    ("Siege Workshop", "Scorpion line", ["Scorpion", "Heavy Scorpion"]),
    ("Siege Workshop", "Bombard Cannon", ["Bombard Cannon"]),
    ("Siege Workshop", "Armored Elephant line", ["Armored Elephant", "Siege Elephant"]),
    ("Siege Workshop", "Siege Tower", ["Siege Tower"]),
    ("Dock", "Galley line", ["Galley", "War Galley", "Galleon"]),
    ("Dock", "Fire Ship line", ["Fire Galley", "Fire Ship", "Fast Fire Ship"]),
    ("Dock", "Demolition line", ["Demolition Raft", "Demolition Ship", "Heavy Demo Ship"]),
    ("Dock", "Cannon Galleon line", ["Cannon Galleon", "Elite Cannon Galleon"]),
    ("Dock", "Dromon", ["Dromon"]),
    ("Monastery", "Monk", ["Monk"]),
    ("Monastery", "Missionary", ["Missionary"]),
]

# Tech grouping by English tech name -> display group. Ungrouped techs the civ is
# missing still show up under "Other".
TECH_GROUPS = {
    "Blacksmith": ["Forging", "Iron Casting", "Blast Furnace",
                   "Scale Mail Armor", "Chain Mail Armor", "Plate Mail Armor",
                   "Scale Barding Armor", "Chain Barding Armor", "Plate Barding Armor",
                   "Fletching", "Bodkin Arrow", "Bracer",
                   "Padded Archer Armor", "Leather Archer Armor", "Ring Archer Armor"],
    "University": ["Ballistics", "Chemistry", "Siege Engineers", "Murder Holes",
                   "Heated Shot", "Arrowslits", "Treadmill Crane", "Masonry",
                   "Architecture", "Fortified Wall", "Bombard Tower", "Guard Tower", "Keep"],
    "Stable techs": ["Bloodlines", "Husbandry"],
    "Archery techs": ["Thumb Ring", "Parthian Tactics"],
    "Barracks techs": ["Supplies", "Squires", "Arson", "Gambesons"],
    "Monastery": ["Redemption", "Atonement", "Herbal Medicine", "Heresy", "Sanctity",
                  "Fervor", "Faith", "Illumination", "Block Printing", "Theocracy",
                  "Devotion"],
    "Economy": ["Wheelbarrow", "Hand Cart", "Horse Collar", "Heavy Plow", "Crop Rotation",
                "Double-Bit Axe", "Bow Saw", "Two-Man Saw", "Gold Mining", "Gold Shaft Mining",
                "Stone Mining", "Stone Shaft Mining", "Caravan", "Guilds", "Banking",
                "Coinage", "Loom", "Town Watch", "Town Patrol"],
    "Dock techs": ["Gillnets", "Careening", "Dry Dock", "Shipwright"],
}


def fetch(url, dest):
    print(f"Downloading {url}")
    urllib.request.urlretrieve(url, dest)


def strip_html(text):
    """Flatten the in-game help string into clean markdown bullets."""
    text = text.replace("<b>", "**").replace("</b>", "**")
    text = re.sub(r"<[^>]+>", " ", text)          # <br> and other tags -> space
    text = re.sub(r"\s+", " ", text)              # collapse all whitespace
    # bullets and bold section headers start new lines
    text = text.replace("\u2022", "\n- ")
    text = re.sub(r" ?\*\*([^*]+):?\*\* ?", r"\n\n**\1**\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def slug(name):
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def fmt_cost(cost):
    order = ["Food", "Wood", "Gold", "Stone"]
    parts = [f"{cost[k]}{k[0]}" for k in order if cost.get(k)]
    return " ".join(parts) if parts else "free"


def main():
    tmp = "/tmp/aoe2_coach_build"
    os.makedirs(tmp, exist_ok=True)
    data_path = os.path.join(tmp, "data.json")
    strings_path = os.path.join(tmp, "strings.json")
    fetch(f"{BASE}/data.json", data_path)
    fetch(f"{BASE}/locales/en/strings.json", strings_path)

    data = json.load(open(data_path))
    strings = json.load(open(strings_path))
    units = data["data"]["Unit"]
    techs = data["data"]["Tech"]
    civs = data["civs"]

    def clean(name):
        return re.sub(r"\s+", " ", name.replace("<br>", " ")).strip()

    def uname(u):
        return clean(strings.get(str(u["LanguageNameId"] + UNIT_NAME_OFFSET), u["internal_name"]))

    def tname(t):
        return clean(strings.get(str(t["LanguageNameId"] + TECH_NAME_OFFSET), t["internal_name"]))

    unit_by_name = {}
    for uid, u in units.items():
        unit_by_name.setdefault(uname(u), int(uid))
    tech_by_name = {}
    for tid, t in techs.items():
        tech_by_name.setdefault(tname(t), int(tid))

    # Validate line definitions against live data
    missing_defs = [n for _, _, names in LINES for n in names if n not in unit_by_name]
    if missing_defs:
        sys.exit(f"ERROR: unit names no longer in data (update LINES): {missing_defs}")

    all_line_ids = {unit_by_name[n] for _, _, names in LINES for n in names}

    # Generic tech = researchable by >= 40% of civs (filters out unique techs)
    tech_civ_count = {int(tid): 0 for tid in techs}
    for c in civs.values():
        for tid in c["Tech"]:
            if tid in tech_civ_count:
                tech_civ_count[tid] += 1
    n_civs = len(civs)
    generic_techs = {tid for tid, cnt in tech_civ_count.items() if cnt >= 0.4 * n_civs}

    unit_civ_count = {}
    for c in civs.values():
        for uid in c["Unit"]:
            unit_civ_count[uid] = unit_civ_count.get(uid, 0) + 1
    generic_units = {uid for uid, cnt in unit_civ_count.items() if cnt >= 0.4 * n_civs}

    tech_group_of = {}
    for group, names in TECH_GROUPS.items():
        for n in names:
            tech_group_of[n] = group

    os.makedirs(os.path.join(REFS, "civs"), exist_ok=True)

    # ---------- per-civ files ----------
    index_lines = []
    for civ_name in sorted(civs):
        c = civs[civ_name]
        cunits = set(c["Unit"])
        ctechs = set(c["Tech"])
        out = [f"# {civ_name}", ""]

        help_text = strings.get(str(c["help_string_id"]), "")
        out += [strip_html(help_text), ""]

        out.append("## Tech tree: unit lines")
        out.append("(highest unit the civ can reach on each line; units listed as missing are NOT available; "
                   "lines not listed at all are entirely unavailable to this civ)")
        out.append("")
        by_building = {}
        for building, line_name, names in LINES:
            ids = [unit_by_name[n] for n in names]
            have = [n for n, i in zip(names, ids) if i in cunits]
            if not have:
                continue
            top = have[-1]
            miss = [n for n, i in zip(names, ids) if i not in cunits and i in generic_units and names.index(n) > names.index(top)]
            replaces = {"Winged Hussar": "Hussar", "Imperial Skirmisher": "Elite Skirmisher",
                        "Imperial Camel Rider": "Heavy Camel Rider"}
            entry = f"- {line_name}: up to **{top}**"
            if top in replaces:
                entry += f" (upgraded from / replaces {replaces[top]})"
            if miss:
                entry += f" (missing: {', '.join(miss)})"
            by_building.setdefault(building, []).append(entry)
        for building in ["Barracks", "Archery Range", "Stable", "Siege Workshop", "Dock", "Monastery"]:
            if building in by_building:
                out.append(f"**{building}**")
                out += by_building[building]
        out.append("")

        # Unique / regional units not part of generic lines
        specials = sorted({uname(units[str(uid)]) for uid in cunits
                           if uid not in all_line_ids and str(uid) in units
                           and uid not in generic_units})
        # Drop economic/utility clutter
        drop = {"Villager", "Trade Cart", "Trade Cog", "Fishing Ship", "Transport Ship",
                "Petard", "Trebuchet", "Flaming Camel", "Xolotl Warrior", "Condottiero"}
        keep_note = {"Petard", "Trebuchet"}  # everyone has these
        specials = [s for s in specials if s not in drop]
        if specials:
            out.append("## Unique / special units")
            for s in specials:
                u = units[str(unit_by_name[s])]
                out.append(f"- {s} ({fmt_cost(u.get('Cost', {}))}, {u['HP']} HP, {u['Attack']} atk)")
            out.append("")

        # Missing generic techs, grouped
        missing = sorted(generic_techs - ctechs)
        out.append("## Missing technologies (generic techs this civ CANNOT research)")
        grouped = {}
        for tid in missing:
            name = tname(techs[str(tid)])
            grouped.setdefault(tech_group_of.get(name, "Other"), []).append(name)
        if not grouped:
            out.append("- none: full generic tech tree")
        for g in ["Blacksmith", "University", "Stable techs", "Archery techs",
                  "Barracks techs", "Monastery", "Economy", "Dock techs", "Other"]:
            if g in grouped:
                out.append(f"- {g}: {', '.join(sorted(set(grouped[g])))}")
        out.append("")

        path = os.path.join(REFS, "civs", f"{slug(civ_name)}.md")
        with open(path, "w") as f:
            f.write("\n".join(out))

        first_line = strip_html(help_text).split("\n")[0]
        index_lines.append(f"- **{civ_name}** ({first_line}) -> `references/civs/{slug(civ_name)}.md`")

    with open(os.path.join(REFS, "civ_index.md"), "w") as f:
        f.write("# Civilization index\n\nOne file per civ. Always open the civ file before "
                "making tech-tree claims.\n\n" + "\n".join(index_lines) + "\n")

    # ---------- units.md ----------
    trainable = set()
    for c in civs.values():
        trainable.update(c["Unit"])
    rows = []
    seen_names = set()
    for uid in sorted(trainable):
        u = units.get(str(uid))
        if not u:
            continue
        name = uname(u)
        if name in seen_names:
            continue
        seen_names.add(name)
        atk_bonuses = []
        for a in u.get("Attacks", []):
            cls, amt = a["Class"], a["Amount"]
            if cls in (3, 4) or amt <= 0:
                continue
            atk_bonuses.append(f"+{amt} vs {ARMOR_CLASSES.get(cls, f'class {cls}')}")
        rng = f"{u['Range']}" if u.get("Range") else "melee"
        rows.append(
            f"| {name} | {fmt_cost(u.get('Cost', {}))} | {u['HP']} | {u['Attack']} "
            f"| {u['MeleeArmor']}/{u['PierceArmor']} | {rng} | {u['Speed']} "
            f"| {'; '.join(atk_bonuses) or '-'} |"
        )
    with open(os.path.join(REFS, "units.md"), "w") as f:
        f.write(
            "# Unit statistics (base, before blacksmith/civ bonuses)\n\n"
            "Elite/upgraded versions are separate rows. Armor is melee/pierce.\n\n"
            "| Unit | Cost | HP | Atk | Armor | Range | Speed | Attack bonuses |\n"
            "|---|---|---|---|---|---|---|---|\n" + "\n".join(rows) + "\n"
        )

    print(f"Done: {len(civs)} civ files, units.md, civ_index.md written to {os.path.normpath(REFS)}")


if __name__ == "__main__":
    main()
