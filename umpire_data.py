UMPIRE_K_BB_TENDENCIES = {'Laz Diaz': {'k_boost': 1.1, 'bb_suppress': 0.9}, 'Angel Hernandez': {'k_boost': 0.92, 'bb_suppress': 1.15}, 'Pat Hoberg': {'k_boost': 1.08, 'bb_suppress': 0.95}, 'CB Bucknor': {'k_boost': 0.95, 'bb_suppress': 1.1}, 'Jim Wolf': {'k_boost': 1.03, 'bb_suppress': 0.97}, 'Mark Wegner': {'k_boost': 1.05, 'bb_suppress': 0.96}, 'Dan Bellino': {'k_boost': 1.04, 'bb_suppress': 0.98}, 'Ed Hickox': {'k_boost': 0.97, 'bb_suppress': 1.02}, 'Alan Porter': {'k_boost': 1.02, 'bb_suppress': 1.0}, 'Chris Guccione': {'k_boost': 1.0, 'bb_suppress': 1.0}, 'Will Little': {'k_boost': 1.06, 'bb_suppress': 0.97}, 'Quinn Wolcott': {'k_boost': 1.01, 'bb_suppress': 1.03}, 'Adrian Johnson': {'k_boost': 1.0, 'bb_suppress': 1.02}, 'Tripp Gibson': {'k_boost': 1.07, 'bb_suppress': 0.94}, 'Andy Fletcher': {'k_boost': 0.93, 'bb_suppress': 1.12}, 'Vic Carapazza': {'k_boost': 1.09, 'bb_suppress': 0.91}, 'Jerry Meals': {'k_boost': 0.98, 'bb_suppress': 1.04}, 'Brian Knight': {'k_boost': 1.0, 'bb_suppress': 1.0}, 'Ted Barrett': {'k_boost': 1.04, 'bb_suppress': 0.99}, 'Marty Foster': {'k_boost': 0.96, 'bb_suppress': 1.08}, 'Nic Lentz': {'k_boost': 1.03, 'bb_suppress': 0.97}, 'Chad Fairchild': {'k_boost': 1.02, 'bb_suppress': 1.0}, 'Carlos Torres': {'k_boost': 1.0, 'bb_suppress': 1.01}, 'Tony Randazzo': {'k_boost': 0.97, 'bb_suppress': 1.05}, 'Nestor Ceja': {'k_boost': 1.01, 'bb_suppress': 0.99}}


def get_umpire_adjustment(umpire_name: str, stat: str) -> float:
    """Return a multiplier based on the umpire and stat type ("strikeout" or "walk")."""
    tendencies = UMPIRE_K_BB_TENDENCIES.get(umpire_name, {})
    if stat == "strikeout":
        return tendencies.get("k_boost", 1.0)
    elif stat == "walk":
        return tendencies.get("bb_suppress", 1.0)
    return 1.0
