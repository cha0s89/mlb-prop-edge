# stadium_factors.py

def get_stadium_factor(stadium_name):
    # Simplified list with normalized keys
    stadium_factors = {
        "dodger stadium": 1.05,
        "coors field": 1.20,
        "yankee stadium": 1.08,
        "fenway park": 1.10,
        "oracle park": 0.90,
        "oakland coliseum": 0.85,
        "wrigley field": 1.07,
        "citizens bank park": 1.06,
        "petco park": 0.94,
        "globe life field": 0.97,
        "tropicana field": 0.93,
        "truist park": 1.04,
        "minute maid park": 1.01,
        "rogers centre": 1.03,
        "progressive field": 1.02,
        "great american ball park": 1.12,
        "guaranteed rate field": 1.00,
        "busch stadium": 0.95,
        "target field": 1.00,
        "t-mobile park": 0.96,
        "chase field": 1.11,
        "pnc park": 0.99,
        "kauffman stadium": 1.00,
        "loanDepot park": 0.98,
        "american family field": 1.08,
        "nationals park": 1.00,
        "citi field": 0.97,
        "angel stadium": 0.96,
        "camden yards": 1.09,
        "comerica park": 0.92,
        "busch stadium": 0.95
    }

    if not stadium_name:
        return 1.0  # default neutral factor

    stadium_key = stadium_name.strip().lower()
    return stadium_factors.get(stadium_key, 1.0)
