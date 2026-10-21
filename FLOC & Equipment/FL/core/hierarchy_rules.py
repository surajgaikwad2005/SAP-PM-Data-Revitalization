"""PMMS inventory tiers and the joined FL + Equipment hierarchy index (AssetHierarchyIndex)."""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from typing import Any

import pandas as pd

from .common import compact_key, normalize_floc, normalize_text


# Inventory Number = tier of the Functional Location in the PMMS asset hierarchy.
#   3  Site/Field            (e.g. BOKOR)
#   4  Plant                 (e.g. BOCP)                     FLOC level 0
#   5A Process Unit          (e.g. BOCP.GAS)                 FLOC level 1
#   5B Sub-Process Unit      (e.g. BOCP.NIT.GEN)             FLOC level 2
#   5C Functional Boundary   (e.g. BOCP.DIS.LIS.DB7732)      FLOC level 3
#   6 / 7 / 7A / 7B          intermediate assemblies / control & shutdown systems
#   8  Tag (equipment is installed here, final segment after "-")   FLOC level 4
LEVEL_ORDER = ["1", "2", "3", "4", "5", "5A", "5B", "5C", "6", "7", "7A", "7B", "8"]
LEVEL_RANK = {level: rank for rank, level in enumerate(LEVEL_ORDER)}
TAG_LEVEL = "8"
PACKAGE_LEVELS = {"6", "7", "7A", "7B"}
BLANK_VALUES = {"", "NONE", "NAN", "NAT", "NULL"}


def clean_value(value: Any) -> str:
    text = normalize_text(value)
    return "" if text in BLANK_VALUES else text


def normalize_inventory(value: Any) -> str:
    text = clean_value(value).replace(" ", "")
    if re.fullmatch(r"\d+\.0+", text):
        text = text.split(".", 1)[0]
    return text


def level_rank(value: Any) -> int | None:
    return LEVEL_RANK.get(normalize_inventory(value))


def plant_prefix(floc: str) -> str:
    return re.split(r"[.-]", normalize_floc(floc), maxsplit=1)[0]


class AssetHierarchyIndex:
    """
    Joined view of the Functional Location and Equipment master data (asset cache).

    Used by the deterministic validators (inventory level, tag-level mapping, cross-sheet
    completion), by the hybrid LLM reviewer (row context) and by the agent tools.
    """

    def __init__(self, cache: dict[str, Any] | None):
        cache = cache if isinstance(cache, dict) else {}
        fl_df = cache.get("fl_df")
        eq_df = cache.get("equipment_df")
        self.fl_records: dict[str, dict[str, str]] = {}
        self.equipment_records: dict[str, dict[str, str]] = {}
        self.parent: dict[str, str] = {}
        self.children: dict[str, list[str]] = defaultdict(list)
        self.inventory: dict[str, str] = {}
        self.equipment_by_floc: dict[str, list[str]] = defaultdict(list)
        self.tag_suffix_index: dict[str, list[str]] = defaultdict(list)

        if isinstance(fl_df, pd.DataFrame) and "Functional Location" in fl_df.columns:
            for record in fl_df.to_dict("records"):
                floc = normalize_floc(record.get("Functional Location", ""))
                if not floc:
                    continue
                self.fl_records[floc] = {str(k): clean_value(v) if k not in {"Functional Location"} else floc for k, v in record.items()}
                superior = normalize_floc(clean_value(record.get("Superior FunctLoc.", "")))
                if superior:
                    self.parent[floc] = superior
                    self.children[superior].append(floc)
                inventory = normalize_inventory(record.get("Inventory Number", ""))
                if inventory:
                    self.inventory[floc] = inventory
                if "-" in floc:
                    self.tag_suffix_index[compact_key(floc.rsplit("-", 1)[1])].append(floc)

        if isinstance(eq_df, pd.DataFrame) and "Equipment" in eq_df.columns:
            for record in eq_df.to_dict("records"):
                equipment = clean_value(record.get("Equipment", ""))
                if not equipment:
                    continue
                self.equipment_records[equipment] = {str(k): clean_value(v) for k, v in record.items()}
                floc = normalize_floc(clean_value(record.get("Functional Location", "")))
                if floc:
                    self.equipment_by_floc[floc].append(equipment)

        self.transition = self._learn_transitions()
        self.eca_tag_links: dict[str, list[tuple[str, str]]] = defaultdict(list)
        self.level8_templates = self._learn_level8_templates()
        self.part_to_manufacturer = self._peer_index(("ManufactPartNo.",), "Manufacturer")
        self.model_to_manufacturer = self._peer_index(("Model number",), "Manufacturer")
        self.part_to_model = self._peer_index(("ManufactPartNo.", "Manufacturer"), "Model number")
        self.model_to_part = self._peer_index(("Model number", "Manufacturer"), "ManufactPartNo.")

    # ------------------------------------------------------------------ hierarchy
    def exists(self, floc: str) -> bool:
        return normalize_floc(floc) in self.fl_records

    def child_count(self, floc: str) -> int:
        return len(self.children.get(normalize_floc(floc), []))

    def has_equipment(self, floc: str) -> bool:
        return bool(self.equipment_by_floc.get(normalize_floc(floc)))

    def resolve_parent(self, floc: str) -> tuple[str, str]:
        """Return (parent, source). Source is 'master' (Superior FunctLoc.) or 'derived' (longest existing prefix)."""
        floc = normalize_floc(floc)
        if floc in self.parent:
            return self.parent[floc], "master"
        candidate = floc
        for _ in range(12):
            if "-" in candidate:
                candidate = candidate.rsplit("-", 1)[0]
            elif "." in candidate:
                candidate = candidate.rsplit(".", 1)[0]
            else:
                return "", ""
            if candidate in self.fl_records:
                return candidate, "derived"
        return "", ""

    def ancestors(self, floc: str, limit: int = 12) -> list[str]:
        output = []
        current = normalize_floc(floc)
        for _ in range(limit):
            parent, _ = self.resolve_parent(current)
            if not parent or parent in output:
                break
            output.append(parent)
            current = parent
        return output

    def is_tag_level(self, floc: str) -> bool:
        """Tag level (inventory 8): leaf FLOC where equipment is/can be installed."""
        floc = normalize_floc(floc)
        if self.child_count(floc) > 0:
            return False
        if self.has_equipment(floc) and self.inventory.get(floc, TAG_LEVEL) == TAG_LEVEL:
            return True
        if "-" in floc and self.inventory.get(floc, TAG_LEVEL) == TAG_LEVEL:
            return True
        return self.inventory.get(floc) == TAG_LEVEL

    # ------------------------------------------------------------------ inventory level
    def expected_inventory(self, floc: str, _depth: int = 0) -> tuple[str, float, str] | None:
        floc = normalize_floc(floc)
        if not floc or _depth > 14:
            return None
        kids = self.child_count(floc)
        has_eq = self.has_equipment(floc)

        parent, parent_source = self.resolve_parent(floc)

        if kids == 0 and "-" in floc and not has_eq:
            boundary = self._dash_boundary_level(floc, parent)
            if boundary:
                return boundary

        if kids == 0 and (has_eq or "-" in floc):
            reason = "equipment is installed on it" if has_eq else "final tag segment after '-'"
            confidence = 0.97
            parent_rank = level_rank(self.inventory.get(parent, ""))
            if parent_source == "derived":
                confidence = 0.90
                if parent_rank is not None and parent_rank < LEVEL_RANK["5B"] and not has_eq:
                    # A tag straight under a plant / process unit is unusual: leave it to review.
                    confidence = 0.78
                    reason += f"; superior not recorded and nearest existing ancestor {parent} is tier {self.inventory.get(parent, '?')}"
            return TAG_LEVEL, confidence, f"Leaf FLOC and {reason}: Tag level => Inventory 8"

        if not parent:
            master = self.inventory.get(floc)
            if master:
                return master, 0.90, "Top node of hierarchy; kept master inventory"
            return None

        parent_inventory = self.inventory.get(parent)
        if not parent_inventory:
            parent_expected = self.expected_inventory(parent, _depth + 1)
            parent_inventory = parent_expected[0] if parent_expected else ""
        parent_rank = level_rank(parent_inventory)
        if parent_rank is None:
            return None

        siblings = [s for s in self.children.get(parent, []) if s != floc and self.inventory.get(s)]
        sibling_levels = Counter(self.inventory[s] for s in siblings)
        confidence_penalty = 0.0 if parent_source == "master" else 0.04

        if kids == 0 and sibling_levels:
            top, count = sibling_levels.most_common(1)[0]
            if top == TAG_LEVEL and count / sum(sibling_levels.values()) >= 0.8:
                return (
                    TAG_LEVEL,
                    0.90 - confidence_penalty,
                    f"Leaf FLOC whose siblings under {parent} are tags ({count}/{sum(sibling_levels.values())} are 8) => Inventory 8",
                )

        allowed = Counter(
            {level: n for level, n in sibling_levels.items() if level != TAG_LEVEL and (level_rank(level) or 0) > parent_rank}
        )
        if allowed:
            level, count = allowed.most_common(1)[0]
            unanimous = count == sum(allowed.values())
            confidence = (0.93 if unanimous else 0.86) - confidence_penalty
            return (
                level,
                confidence,
                f"Non-tag FLOC under {parent} (Inventory {parent_inventory}); sibling non-tag FLOCs use {dict(allowed)}",
            )

        learned = Counter(
            {level: n for level, n in self.transition.get(parent_inventory, Counter()).items() if (level_rank(level) or 0) > parent_rank}
        )
        if learned:
            level, _ = learned.most_common(1)[0]
            return (
                level,
                0.82 - confidence_penalty,
                f"Non-tag FLOC under {parent} (Inventory {parent_inventory}); most common child tier for {parent_inventory} is {level}",
            )
        return None

    def _dash_boundary_level(self, floc: str, parent: str) -> tuple[str, float, str] | None:
        """
        Piping circuit IDs (e.g. BODE.PIN.CG001-02-009) contain '-' but are Functional Boundaries, not Tags.
        If sibling FLOCs of the same code shape are consistently a non-tag tier, the '-' is part of the code.
        """
        shape = self._code_shape(floc, parent)
        peers = Counter(
            self.inventory[s]
            for s in self.children.get(parent, [])
            if s != floc and s in self.inventory and self._code_shape(s, parent) == shape
        )
        if not peers:
            return None
        level, count = peers.most_common(1)[0]
        if level != TAG_LEVEL and count / sum(peers.values()) >= 0.8:
            return (
                level,
                0.92,
                f"'-' is part of the code: {count}/{sum(peers.values())} sibling FLOCs with the same code pattern under {parent} are Inventory {level} (e.g. piping circuit = Functional Boundary)",
            )
        return None

    @staticmethod
    def _code_shape(floc: str, parent: str) -> str:
        """Shape of the code below the parent, e.g. BODE.PIN.CG001-02-009 under BODE.PIN -> .A9-9-9"""
        floc = normalize_floc(floc)
        rest = floc[len(parent):] if parent and floc.startswith(parent) else "~" + floc
        rest = re.sub(r"\([A-Z0-9]*\)|SB$", "", rest)
        return re.sub(r"[A-Z]+", "A", re.sub(r"\d+", "9", rest))

    def _learn_transitions(self) -> dict[str, Counter]:
        transitions: dict[str, Counter] = defaultdict(Counter)
        for floc, parent in self.parent.items():
            child_level = self.inventory.get(floc)
            parent_level = self.inventory.get(parent)
            if child_level and parent_level and child_level != TAG_LEVEL:
                transitions[parent_level][child_level] += 1
        return transitions

    # ------------------------------------------------------------------ Level 8 (Tag) FLOC for equipment
    @staticmethod
    def tag_from_identifiers(floc: str, technical_id: str, description: str = "") -> str:
        prefix = plant_prefix(floc)
        technical_id = clean_value(technical_id)
        if technical_id:
            parts = technical_id.split("-", 1)
            body = parts[1] if len(parts) == 2 and compact_key(parts[0]) == compact_key(prefix) else technical_id
            return compact_key(body)
        description = clean_value(description)
        match = re.search(rf"\b{re.escape(prefix)}-([A-Z0-9-]{{3,}})\s*$", description) if prefix else None
        return compact_key(match.group(1)) if match else ""

    def attach_eca_equipment_links(self, links: pd.DataFrame | None) -> None:
        """ECA report rows link an equipment tag (Equipment Number) to its Level 8 Functional Location."""
        self.eca_tag_links = defaultdict(list)
        if not isinstance(links, pd.DataFrame) or links.empty:
            return
        for record in links.to_dict("records"):
            floc = normalize_floc(clean_value(record.get("functional_location", "")))
            tag = compact_key(clean_value(record.get("equipment_number", "")))
            if floc and tag:
                source = f"{clean_value(record.get('source_file', ''))} page {clean_value(record.get('page_no', ''))}".strip()
                self.eca_tag_links[tag].append((floc, source))

    def boundary_chain(self, floc: str) -> list[str]:
        """Superior chain from `floc` up to and including its Functional Boundary (Inventory 5C)."""
        chain = [normalize_floc(floc)]
        while len(chain) < 12:
            current = chain[-1]
            if self.inventory.get(current) == "5C":
                return chain
            parent = self.parent.get(current, "")
            if not parent or parent in chain:
                return []
            chain.append(parent)
        return []

    def level8_below(self, floc: str, max_depth: int = 4) -> list[str]:
        """Existing Inventory-8 FLOCs reached from `floc` through the Superior FunctLoc. chain (package -> L7 -> L8)."""
        found, frontier = [], [normalize_floc(floc)]
        for _ in range(max_depth):
            next_frontier = []
            for node in frontier:
                for child in self.children.get(node, []):
                    if self.inventory.get(child) == TAG_LEVEL:
                        found.append(child)
                    else:
                        next_frontier.append(child)
            frontier = next_frontier
        return found

    def is_below(self, floc: str, ancestor: str) -> bool:
        return normalize_floc(ancestor) in self.ancestors(floc)

    def _learn_level8_templates(self) -> dict[str, tuple[str, list[str]]]:
        """
        How each package (Inventory 6 / 7 / 7A / 7B) names its Level 8 tags in the FL master:
          "B" = <functional boundary 5C>-<tag>   e.g. BOCP.CHE.AFO.A4044.P4045A -> BOCP.CHE.AFO.A4044-P4045A
          "P" = <package FLOC>-<tag>             e.g. BODC.PCT.ESD.GEN -> BODC.PCT.ESD.GEN-KN001
        """
        templates: dict[str, tuple[str, list[str]]] = {}
        for package, kids in self.children.items():
            if self.inventory.get(package) not in PACKAGE_LEVELS:
                continue
            tags = [kid for kid in kids if self.inventory.get(kid) == TAG_LEVEL and "-" in kid]
            if not tags:
                continue
            chain = self.boundary_chain(package)
            boundary = chain[-1] if chain else ""
            kinds = Counter()
            for kid in tags:
                head = kid.rsplit("-", 1)[0]
                if head == package:
                    kinds["P"] += 1
                elif boundary and head == boundary:
                    kinds["B"] += 1
            if kinds:
                templates[package] = (kinds.most_common(1)[0][0], tags)
        return templates

    def _template_for(self, package: str, boundary: str) -> tuple[str, float, str, list[str]]:
        """Template used by peer packages: same functional boundary first, then same sub-process, then plant-wide."""
        def peers_under(root: str) -> list[str]:
            return [p for p in self.level8_templates if p != package and (p == root or self.is_below(p, root))]

        scopes = [("functional boundary " + boundary, peers_under(boundary))]
        sub_process = self.parent.get(boundary, "")
        if sub_process:
            scopes.append(("sub-process " + sub_process, peers_under(sub_process)))
        prefix = plant_prefix(package)
        scopes.append(("plant " + prefix, [p for p in self.level8_templates if p != package and plant_prefix(p) == prefix]))
        for scope, peers in scopes:
            if not peers:
                continue
            kinds = Counter(self.level8_templates[p][0] for p in peers)
            kind, support = kinds.most_common(1)[0]
            examples = []
            for peer in peers:
                if self.level8_templates[peer][0] != kind:
                    continue
                main = self._main_tag(peer)
                examples.append(f"{peer} (Inv {self.inventory.get(peer, '?')}) -> {main} (Inv 8)")
                if len(examples) >= 3:
                    break
            return kind, support / len(peers), f"{support}/{len(peers)} peer packages in {scope}", examples
        return "", 0.0, "", []

    def _main_tag(self, package: str) -> str:
        """Level 8 tag of a package whose tag equals the package code (the main item), else its first tag."""
        segment = compact_key(package.rsplit(".", 1)[-1])
        tags = self.level8_templates.get(package, ("", []))[1]
        for tag in tags:
            if compact_key(tag.rsplit("-", 1)[1]) == segment:
                return tag
        return tags[0] if tags else ""

    def find_level8_floc(self, floc: str, technical_id: str = "", description: str = "") -> dict[str, Any] | None:
        """
        Level 8 (Tag) Functional Location for equipment installed on `floc` (PTG 12.05.04 s3.2.7).

        Returns a dict with status EXISTS / NEW / AMBIGUOUS / NONE / CHECK, the FLOC, its superior,
        a confidence and the evidence. None when `floc` is already a valid Level 8 FLOC or unknown.
        """
        floc = normalize_floc(floc)
        if not floc or floc not in self.fl_records:
            return None
        level = self.inventory.get(floc, "")
        if level == TAG_LEVEL:
            kids = self.children.get(floc, [])
            if kids:
                return self._level8_result(
                    "CHECK", "", "", 0.0,
                    f"FLOC {floc} is Inventory 8 but has {len(kids)} child FLOCs (e.g. {', '.join(kids[:3])}); a Level 8 Tag must be a leaf",
                )
            return None

        tag = self.tag_from_identifiers(floc, technical_id, description)
        tag_source = f"Technical IdentNo. {clean_value(technical_id)}" if clean_value(technical_id) else "equipment description"
        path_note = f"Equipment is installed on {floc} (Inventory {level or '?'}, {self.fl_records[floc].get('FunctLocDescrip.', '')})"

        # a) existing Level 8 FLOCs under the package through the Superior FunctLoc. chain
        below = self.level8_below(floc)
        candidates: dict[str, str] = {}
        for candidate in below:
            if tag and "-" in candidate and compact_key(candidate.rsplit("-", 1)[1]) == tag:
                candidates[candidate] = f"FL master: {self._path_text(candidate, floc)}"
        # b) ECA report: equipment tag -> Functional Location, accepted only when it is Inventory 8 below this package
        for key in {compact_key(technical_id), tag} - {""}:
            for eca_floc, source in getattr(self, "eca_tag_links", {}).get(key, []):
                if self.inventory.get(eca_floc) == TAG_LEVEL and (self.is_below(eca_floc, floc) or self.parent.get(eca_floc) == floc):
                    note = f"ECA report {source}: Equipment Number {clean_value(technical_id) or tag} -> {eca_floc}"
                    candidates[eca_floc] = f"{candidates[eca_floc]}; {note}" if eca_floc in candidates else note

        if len(candidates) == 1:
            found, how = next(iter(candidates.items()))
            return self._level8_result(
                "EXISTS", found, self.parent.get(found, floc), 0.96,
                f"{path_note}; existing Level 8 FL {found} ({self.fl_records.get(found, {}).get('FunctLocDescrip.', '')}) carries tag {tag} "
                f"[{how}]; equipment must be installed at Level 8 (PTG 12.05.04 s3.2.7)",
            )
        if len(candidates) > 1:
            listed = "; ".join(f"{c} [{how}]" for c, how in candidates.items())
            return self._level8_result("AMBIGUOUS", "", "", 0.0, f"{path_note}; several Level 8 FLs match tag {tag}: {listed}")
        if not tag:
            existing = ", ".join(below[:5]) or "none"
            return self._level8_result(
                "NONE", "", "", 0.0,
                f"{path_note}; no Technical IdentNo. tag to identify its Level 8 FL; Level 8 FLs under this package: {existing}",
            )
        return self._derive_level8(floc, tag, tag_source, path_note, below)

    def _derive_level8(self, package: str, tag: str, tag_source: str, path_note: str, existing: list[str]) -> dict[str, Any]:
        """New Level 8 FL: functional boundary from the Superior chain + equipment tag, named like the peer packages."""
        chain = self.boundary_chain(package)
        if not chain:
            return self._level8_result(
                "NONE", "", "", 0.0, f"{path_note}; no Functional Boundary (Inventory 5C) found in its Superior chain, Level 8 FL cannot be derived",
            )
        boundary = chain[-1]
        kind, ratio, support, examples = self._template_for(package, boundary)
        if not kind:
            return self._level8_result("NONE", "", "", 0.0, f"{path_note}; no peer package with Level 8 tags to learn the naming from")
        candidate = f"{boundary}-{tag}" if kind == "B" else f"{package}-{tag}"
        template = "<functional boundary>-<tag>" if kind == "B" else "<package FLOC>-<tag>"
        if candidate in self.fl_records:
            return self._level8_result(
                "AMBIGUOUS", "", "", 0.0,
                f"{path_note}; derived Level 8 code {candidate} already exists under superior {self.parent.get(candidate, '?')} "
                f"(Inventory {self.inventory.get(candidate, '?')}), not under {package}",
            )
        scope_is_boundary = support.endswith(f"functional boundary {boundary}")
        if ratio >= 0.8 and scope_is_boundary:
            confidence = 0.92
        elif ratio >= 0.8:
            confidence = 0.87
        else:
            confidence = 0.78
        motor_peers = [
            p for p in self.level8_templates
            if p != package and self.is_below(p, boundary)
            and any(t.endswith(compact_key(p.rsplit(".", 1)[-1]) + "M") for t in self.level8_templates[p][1])
        ]
        hint = (
            f"; peer packages also register a motor tag <tag>M (e.g. {self._main_tag(motor_peers[0])}M) - check whether this equipment needs one"
            if motor_peers else ""
        )
        chain_text = " -> ".join(f"{node} (Inv {self.inventory.get(node, '?')})" for node in reversed(chain))
        evidence = (
            f"{path_note}; no Level 8 FL exists under it in FL master or ECA report"
            f"{' (existing Level 8 under package: ' + ', '.join(existing[:3]) + ')' if existing else ''}. "
            f"NEW Level 8 FL to be created: {candidate}, Superior FunctLoc. = {package}, Inventory 8. "
            f"Hierarchy: {chain_text} -> {candidate} (Inv 8). Tag {tag} from {tag_source}. "
            f"Naming {template} learned from {support}: {'; '.join(examples)}{hint}. "
            f"Standards: PTG 12.05.04 s3.2.5-3.2.7 / Table 3.1 (L6 package -> L7 subunit -> L8 tag; equipment only at Level 8); "
            f"UOE MX GU 001 s4 (Tag joined to its functional boundary with '-', e.g. RECP-GCOM.BCT1P303PK-K303H)"
        )
        return self._level8_result("NEW", candidate, package, confidence, evidence)

    def _path_text(self, floc: str, stop: str) -> str:
        nodes = [floc]
        for ancestor in self.ancestors(floc):
            nodes.append(ancestor)
            if ancestor == stop:
                break
        return " -> ".join(f"{node} (Inv {self.inventory.get(node, '?')})" for node in reversed(nodes))

    @staticmethod
    def _level8_result(status: str, floc: str, superior: str, confidence: float, evidence: str) -> dict[str, Any]:
        return {"status": status, "floc": floc, "superior": superior, "confidence": confidence, "evidence": evidence}

    # ------------------------------------------------------------------ peers for manufacturer data
    def _peer_index(self, key_fields: tuple[str, ...], target_field: str) -> dict[tuple[str, ...], Counter]:
        index: dict[tuple[str, ...], Counter] = defaultdict(Counter)
        for record in self.equipment_records.values():
            key = tuple(compact_key(record.get(field, "")) for field in key_fields)
            value = record.get(target_field, "")
            if all(key) and value:
                index[key][value] += 1
        return index

    @staticmethod
    def peer_value(index: dict[tuple[str, ...], Counter], key: tuple[str, ...]) -> tuple[str, int, int]:
        """Return (value, supporting peers, conflicting peers) for a peer lookup."""
        counter = index.get(tuple(compact_key(k) for k in key))
        if not counter:
            return "", 0, 0
        value, support = counter.most_common(1)[0]
        return value, support, sum(counter.values()) - support

    # ------------------------------------------------------------------ context for LLM / agent
    def floc_context(self, floc: str, max_children: int = 12) -> dict[str, Any]:
        floc = normalize_floc(floc)
        if not floc:
            return {}
        record = self.fl_records.get(floc, {})
        parent, parent_source = self.resolve_parent(floc)
        children = self.children.get(floc, [])
        expected = self.expected_inventory(floc)
        sibling_levels = Counter(self.inventory.get(s, "") for s in self.children.get(parent, []) if s != floc)
        return {
            "functional_location": floc,
            "exists_in_master": bool(record),
            "description": record.get("FunctLocDescrip.", ""),
            "master_inventory": self.inventory.get(floc, ""),
            "expected_inventory": expected[0] if expected else "",
            "expected_inventory_reason": expected[2] if expected else "",
            "parent": parent,
            "parent_source": parent_source,
            "parent_inventory": self.inventory.get(parent, ""),
            "parent_description": self.fl_records.get(parent, {}).get("FunctLocDescrip.", ""),
            "ancestors": self.ancestors(floc),
            "child_count": len(children),
            "children_sample": [
                {"floc": child, "inventory": self.inventory.get(child, ""), "description": self.fl_records.get(child, {}).get("FunctLocDescrip.", "")}
                for child in children[:max_children]
            ],
            "sibling_inventory_levels": {k: v for k, v in sibling_levels.items() if k},
            "installed_equipment": [
                {
                    "equipment": eq,
                    "object_description": self.equipment_records.get(eq, {}).get("Object Description", ""),
                    "technical_ident_no": self.equipment_records.get(eq, {}).get("Technical IdentNo.", ""),
                    "abc_indicator": self.equipment_records.get(eq, {}).get("ABC Indicator", ""),
                }
                for eq in self.equipment_by_floc.get(floc, [])[:5]
            ],
            "master_record": {k: v for k, v in record.items() if v},
        }

    def search_flocs(self, text: str, limit: int = 20) -> list[dict[str, str]]:
        query = normalize_text(text)
        compact_query = compact_key(query)
        words = [w for w in re.findall(r"[A-Z0-9]+", query) if len(w) >= 3]
        results = []
        for floc, record in self.fl_records.items():
            description = record.get("FunctLocDescrip.", "")
            if compact_query and compact_query in compact_key(floc):
                score = 3
            elif words and all(w in description for w in words):
                score = 2
            else:
                continue
            results.append((score, floc, description))
        results.sort(key=lambda item: (-item[0], len(item[1])))
        return [
            {"floc": floc, "description": description, "inventory": self.inventory.get(floc, "")}
            for _, floc, description in results[:limit]
        ]
