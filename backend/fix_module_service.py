import re

with open('app/services/repositories/module_service.py', 'r', encoding='utf-8') as f:
    content = f.read()

# get_dashboard_summary
content = re.sub(
    r'from app\.data\.dashboard import COMMAND_CENTER_SUMMARY\s+return COMMAND_CENTER_SUMMARY',
    '''return {
                "totalCrimes": {"value": 0, "trend": "0%", "trendTone": "neutral"},
                "activeCases": {"value": 0, "trend": "0", "trendTone": "neutral"},
                "highRiskAreas": {"value": 0, "trend": "0", "trendTone": "neutral"},
                "openFirs": {"value": 0, "trend": "0", "trendTone": "neutral"},
            }''',
    content
)

# get_dashboard_crime_trend
content = re.sub(
    r'from app\.data\.dashboard import CRIME_TREND\s+return CRIME_TREND',
    '''return [
                {"label": "Mon", "value": 0},
                {"label": "Tue", "value": 0},
                {"label": "Wed", "value": 0},
                {"label": "Thu", "value": 0},
                {"label": "Fri", "value": 0},
                {"label": "Sat", "value": 0},
                {"label": "Sun", "value": 0},
            ]''',
    content
)

# get_analytics_statistics
content = re.sub(
    r'from app\.data\.analytics import CRIME_STATISTICS\s+return CRIME_STATISTICS',
    '''return {
                "overview": [
                    {"id": "total-incidents", "label": "Total Incidents (30d)", "value": "0", "trend": "0", "trendTone": "neutral"},
                    {"id": "clearance-rate", "label": "Clearance Rate", "value": "0%", "trend": "0", "trendTone": "neutral"},
                    {"id": "repeat-offenders", "label": "Repeat Offenders Flagged", "value": "0", "trend": "0", "trendTone": "neutral"},
                    {"id": "avg-response", "label": "Avg. Response Time", "value": "0", "trend": "0", "trendTone": "neutral"},
                ],
                "behavioralNodes": [],
                "behavioralEdges": [],
                "riskIndex": [],
                "categoryBreakdown": [],
                "recentFeedInjections": [],
            }''',
    content
)

# get_geospatial_parameters
content = re.sub(
    r'from app\.data\.geospatial import GEO_PARAMETERS\s+return GEO_PARAMETERS',
    '''return {
                "activeSession": "GEO-TRK-LIVE",
                "districts": [],
                "incidentTypes": [],
                "overlayLayers": [],
            }''',
    content
)

# get_geospatial_sector_intel
content = re.sub(
    r'from app\.data\.geospatial import SECTOR_INTEL\s+return SECTOR_INTEL\.get\(sector_id\) or SECTOR_INTEL\.get\("default"\)',
    '''return {
            "headline": "No active intelligence available.",
            "body": "System awaiting telemetry or incident correlation.",
            "tags": ["SYSTEM"],
        }''',
    content
)

# get_investigation_fir_intelligence
content = re.sub(
    r'from app\.data\.investigation import FIR_INTELLIGENCE\s+return FIR_INTELLIGENCE',
    '''return {
            "document": {},
            "extractedEntities": [],
            "linkedNetwork": {"nodes": [], "edges": []},
            "suspectPreviousRecords": [],
        }''',
    content
)

# RESOURCE_METRICS in tactical overview
content = re.sub(
    r'from app\.data\.operations import RESOURCE_METRICS\s+metrics = RESOURCE_METRICS',
    '''metrics = {
                "fieldOperatives": {"deployed": 0, "total": 0, "reserves": 0, "deployedPct": 0},
                "tacticalVehicles": {"active": 0, "total": 0, "maintenance": 0},
            }''',
    content
)

# OPERATOR_DOSSIER get
content = re.sub(
    r'from app\.data\.operations import OPERATOR_DOSSIER\s+return OPERATOR_DOSSIER',
    '''return {
            "id": "UNKNOWN",
            "name": "Unknown Operator",
            "rank": "N/A",
            "operatorId": "N/A",
            "assignedUnit": "N/A",
            "dateOfEntry": "N/A",
            "biometricHash": "N/A",
            "clearance": "N/A",
            "status": "INACTIVE",
            "preferences": {},
        }''',
    content
)

# OPERATOR_DOSSIER patch fallback
content = re.sub(
    r'from app\.data\.operations import OPERATOR_DOSSIER\s+return \{\*\*OPERATOR_DOSSIER, "preferences": prefs\}',
    '''return {
            "id": "UNKNOWN",
            "name": "Unknown Operator",
            "rank": "N/A",
            "operatorId": "N/A",
            "assignedUnit": "N/A",
            "dateOfEntry": "N/A",
            "biometricHash": "N/A",
            "clearance": "N/A",
            "status": "INACTIVE",
            "preferences": prefs,
        }''',
    content
)

# OPERATIONS_SUSPECTS
content = re.sub(
    r'from app\.data\.operations import OPERATIONS_SUSPECTS\s+return OPERATIONS_SUSPECTS',
    '''return []''',
    content
)

# FIR_UPLOAD_LOOKUP
content = re.sub(
    r'from app\.data\.operations import FIR_UPLOAD_LOOKUP\s+return FIR_UPLOAD_LOOKUP\["suspectPreviousRecords"\]',
    '''return []''',
    content
)

# SECURITY_POSTURE
content = re.sub(
    r'from app\.data\.administration import SECURITY_POSTURE\s+return SECURITY_POSTURE',
    '''return {
            "systemStatus": "OPTIMAL",
            "activeThreats": 0,
            "vulnerabilities": 0,
            "lastScan": "Just now",
            "complianceScore": 100,
            "recentEvents": [],
        }''',
    content
)

with open('app/services/repositories/module_service.py', 'w', encoding='utf-8') as f:
    f.write(content)
