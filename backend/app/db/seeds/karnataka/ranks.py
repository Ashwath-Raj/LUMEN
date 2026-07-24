from app.db.models import RankORM, DesignationORM

def get_ranks():
    ranks = [
        ("1", "DGP", 1), ("2", "ADGP", 2), ("3", "IGP", 3), ("4", "DIGP", 4),
        ("5", "SSP", 5), ("6", "SP", 6), ("7", "DySP", 7), ("8", "Inspector", 8),
        ("9", "Sub-Inspector", 9), ("10", "Assistant Sub-Inspector", 10),
        ("11", "Head Constable", 11), ("12", "Police Constable", 12)
    ]
    return [RankORM(id=r[0], name=r[1], hierarchy=r[2], active=True) for r in ranks]

def get_designations():
    desigs = [
        ("1", "DGP", 1), ("2", "ADGP", 2), ("3", "IGP", 3), ("4", "DIGP", 4),
        ("5", "SSP", 5), ("6", "SP", 6), ("7", "DySP", 7), ("8", "PI", 8),
        ("9", "PSI", 9), ("10", "ASI", 10), ("11", "HC", 11), ("12", "PC", 12)
    ]
    return [DesignationORM(id=d[0], name=d[1], sort_order=d[2], active=True) for d in desigs]
