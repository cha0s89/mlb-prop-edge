# umpire_factors.py

# Preloaded umpire tendencies for strikeouts and betting trends
UMPIRE_TRENDS = {
    "Pat Hoberg": {"k_factor": 1.05, "over_tendency": 0.52},
    "Laz Diaz": {"k_factor": 0.92, "over_tendency": 0.58},
    "Angel Hernandez": {"k_factor": 0.90, "over_tendency": 0.60},
    "Doug Eddings": {"k_factor": 1.08, "over_tendency": 0.48},
    "Mark Wegner": {"k_factor": 1.02, "over_tendency": 0.50},
    "Tripp Gibson": {"k_factor": 1.10, "over_tendency": 0.45},
    "C.B. Bucknor": {"k_factor": 0.88, "over_tendency": 0.63},
    "Dan Bellino": {"k_factor": 1.07, "over_tendency": 0.47},
    "Will Little": {"k_factor": 1.04, "over_tendency": 0.49},
    "Alan Porter": {"k_factor": 1.06, "over_tendency": 0.51},
    "Chris Guccione": {"k_factor": 0.95, "over_tendency": 0.55},
    "Jeremie Rehak": {"k_factor": 1.00, "over_tendency": 0.50},
    "Adam Hamari": {"k_factor": 0.97, "over_tendency": 0.53},
    "James Hoye": {"k_factor": 1.03, "over_tendency": 0.48},
    "Gabe Morales": {"k_factor": 1.09, "over_tendency": 0.46},
}

def get_umpire_factors(umpire_name: str) -> dict:
    """
    Returns a dictionary with K-factor and over/under tendency for a given umpire.
    If umpire not found, returns neutral (1.0 and 0.50).
    """
    return UMPIRE_TRENDS.get(umpire_name, {"k_factor": 1.0, "over_tendency": 0.50})
