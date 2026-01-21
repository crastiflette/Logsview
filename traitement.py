import re
from datetime import datetime, timedelta
import os
# --- Parsing syslog ---

ISO_SYSLOG_REGEX = re.compile(
    r'^(?P<timestamp>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+\+\d{2}:\d{2})\s+'
    r'(?P<host>\S+)\s+'
    r'(?P<process>[^:]+):\s+'
    r'(?P<message>.+)$'
)


MONTHS = {
    "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4,
    "May": 5, "Jun": 6, "Jul": 7, "Aug": 8,
    "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12
}


def parse_syslog_line(line):
    match = ISO_SYSLOG_REGEX.match(line)
    if not match:
        return None

    try:
        timestamp = datetime.fromisoformat(match.group("timestamp"))
    except ValueError:
        return None

    return {
        "timestamp": timestamp,
        "message": f"{match.group('process')}: {match.group('message')}"
    }

def process_syslog_files(file_paths, max_events=50):
    """
    Lit une liste de fichiers syslog et retourne
    une liste d'événements triés par date décroissante,
    limitée aux `max_events` derniers événements.
    """
    events = []

    for path in file_paths:
        try:
            with open(path, 'r', encoding='utf-8', errors='replace') as f:
                for line in f:
                    event = parse_syslog_line(line.strip())
                    if event:
                        events.append(event)

        except PermissionError as e:
            events.append({
                "timestamp": None,
                "message": f"Erreur de permission sur {path}: {e}"
            })

        except Exception as e:
            events.append({
                "timestamp": None,
                "message": f"Erreur lecture {path}: {e}"
            })
        os.remove(path)

    # TRI DÉCROISSANT (événements les plus récents en premier)
    events.sort(
        key=lambda e: e["timestamp"] or datetime.min,
        reverse=True
    )

    # Limite aux max_events derniers événements
    if max_events > 0:
        events = events[:max_events]

    return events
