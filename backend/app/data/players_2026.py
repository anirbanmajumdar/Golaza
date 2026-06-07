"""Marquee players per nation — purely for colour on team pages.
(name, position, club-ish role). Not exhaustive squads."""

from __future__ import annotations

STARS: dict[str, list[tuple[str, str]]] = {
    "ARG": [("Lionel Messi", "FW"), ("Lautaro Martínez", "FW"), ("Enzo Fernández", "MF")],
    "FRA": [("Kylian Mbappé", "FW"), ("Aurélien Tchouaméni", "MF"), ("William Saliba", "DF")],
    "ESP": [("Lamine Yamal", "FW"), ("Pedri", "MF"), ("Rodri", "MF")],
    "BRA": [("Vinícius Júnior", "FW"), ("Rodrygo", "FW"), ("Éder Militão", "DF")],
    "ENG": [("Jude Bellingham", "MF"), ("Harry Kane", "FW"), ("Bukayo Saka", "FW")],
    "POR": [("Cristiano Ronaldo", "FW"), ("Bruno Fernandes", "MF"), ("Rafael Leão", "FW")],
    "NED": [("Virgil van Dijk", "DF"), ("Cody Gakpo", "FW"), ("Frenkie de Jong", "MF")],
    "GER": [("Jamal Musiala", "MF"), ("Florian Wirtz", "MF"), ("Kai Havertz", "FW")],
    "BEL": [("Kevin De Bruyne", "MF"), ("Jérémy Doku", "FW"), ("Romelu Lukaku", "FW")],
    "URU": [("Federico Valverde", "MF"), ("Darwin Núñez", "FW"), ("Ronald Araújo", "DF")],
    "COL": [("Luis Díaz", "FW"), ("James Rodríguez", "MF"), ("Jhon Durán", "FW")],
    "CRO": [("Luka Modrić", "MF"), ("Joško Gvardiol", "DF"), ("Mateo Kovačić", "MF")],
    "MAR": [("Achraf Hakimi", "DF"), ("Brahim Díaz", "MF"), ("Youssef En-Nesyri", "FW")],
    "NOR": [("Erling Haaland", "FW"), ("Martin Ødegaard", "MF"), ("Alexander Sørloth", "FW")],
    "SUI": [("Granit Xhaka", "MF"), ("Manuel Akanji", "DF"), ("Breel Embolo", "FW")],
    "JPN": [("Takefusa Kubo", "FW"), ("Kaoru Mitoma", "FW"), ("Wataru Endō", "MF")],
    "SEN": [("Sadio Mané", "FW"), ("Nicolas Jackson", "FW"), ("Édouard Mendy", "GK")],
    "USA": [("Christian Pulisic", "FW"), ("Weston McKennie", "MF"), ("Antonee Robinson", "DF")],
    "MEX": [("Santiago Giménez", "FW"), ("Edson Álvarez", "MF"), ("Hirving Lozano", "FW")],
    "TUR": [("Arda Güler", "MF"), ("Hakan Çalhanoğlu", "MF"), ("Kenan Yıldız", "FW")],
    "ECU": [("Moisés Caicedo", "MF"), ("Enner Valencia", "FW"), ("Piero Hincapié", "DF")],
    "AUT": [("David Alaba", "DF"), ("Marcel Sabitzer", "MF"), ("Marko Arnautović", "FW")],
    "CIV": [("Sébastien Haller", "FW"), ("Franck Kessié", "MF"), ("Simon Adingra", "FW")],
    "EGY": [("Mohamed Salah", "FW"), ("Omar Marmoush", "FW"), ("Mohamed Elneny", "MF")],
    "IRN": [("Mehdi Taremi", "FW"), ("Sardar Azmoun", "FW"), ("Alireza Jahanbakhsh", "MF")],
    "ALG": [("Riyad Mahrez", "FW"), ("Ismaël Bennacer", "MF"), ("Saïd Benrahma", "FW")],
    "CAN": [("Alphonso Davies", "DF"), ("Jonathan David", "FW"), ("Cyle Larin", "FW")],
    "SWE": [("Alexander Isak", "FW"), ("Viktor Gyökeres", "FW"), ("Dejan Kulusevski", "MF")],
    "SCO": [("Scott McTominay", "MF"), ("Andrew Robertson", "DF"), ("John McGinn", "MF")],
    "CZE": [("Patrik Schick", "FW"), ("Tomáš Souček", "MF"), ("Adam Hložek", "FW")],
    "KOR": [("Son Heung-min", "FW"), ("Lee Kang-in", "MF"), ("Kim Min-jae", "DF")],
    "AUS": [("Mathew Ryan", "GK"), ("Jackson Irvine", "MF"), ("Riley McGree", "MF")],
    "PAR": [("Miguel Almirón", "MF"), ("Antonio Sanabria", "FW"), ("Gustavo Gómez", "DF")],
    "TUN": [("Hannibal Mejbri", "MF"), ("Aïssa Laïdouni", "MF"), ("Youssef Msakni", "FW")],
    "GHA": [("Mohammed Kudus", "MF"), ("Iñaki Williams", "FW"), ("Thomas Partey", "MF")],
    "COD": [("Yoane Wissa", "FW"), ("Cédric Bakambu", "FW"), ("Chancel Mbemba", "DF")],
    "RSA": [("Lyle Foster", "FW"), ("Percy Tau", "FW"), ("Ronwen Williams", "GK")],
    "UZB": [("Eldor Shomurodov", "FW"), ("Abbosbek Fayzullaev", "MF"), ("Khusniddin Alikulov", "DF")],
    "IRQ": [("Aymen Hussein", "FW"), ("Zidane Iqbal", "MF"), ("Jalal Hassan", "GK")],
    "KSA": [("Salem Al-Dawsari", "FW"), ("Firas Al-Buraikan", "FW"), ("Saud Abdulhamid", "DF")],
    "QAT": [("Akram Afif", "FW"), ("Almoez Ali", "FW"), ("Hassan Al-Haydos", "MF")],
    "JOR": [("Mousa Al-Taamari", "FW"), ("Yazan Al-Naimat", "FW"), ("Nour Al-Rawabdeh", "MF")],
    "BIH": [("Edin Džeko", "FW"), ("Sead Kolašinac", "DF"), ("Amar Dedić", "DF")],
    "PAN": [("Adalberto Carrasquilla", "MF"), ("Ismael Díaz", "FW"), ("José Fajardo", "FW")],
    "NZL": [("Chris Wood", "FW"), ("Marko Stamenić", "MF"), ("Liberato Cacace", "DF")],
    "CPV": [("Ryan Mendes", "FW"), ("Bebé", "FW"), ("Jovane Cabral", "FW")],
    "HAI": [("Frantzdy Pierrot", "FW"), ("Danley Jean Jacques", "MF"), ("Duckens Nazon", "FW")],
    "CUW": [("Leandro Bacuna", "MF"), ("Juninho Bacuna", "MF"), ("Tahith Chong", "MF")],
}


def stars_for(code: str) -> list[dict]:
    return [{"name": n, "position": p} for (n, p) in STARS.get(code, [])]
