"""Texas QSO Party (TQP) plugin"""

import datetime
import logging
from pathlib import Path
from not1mm.lib.plugin_common import gen_adif
from not1mm.lib.version import __version__

logger = logging.getLogger(__name__)

name = "Texas QSO Party"
cabrillo_name = "TQP"
mode = "BOTH"  # CW, SSB, Digital
columns = [
    "YYYY-MM-DD HH:MM:SS",  # TS
    "Call",
    "Freq",
    "Snt",                  # Sent RST
    "Rcv",                  # Received RST
    "SentNr",               # Sent Serial
    "NR",                   # Received Serial or Exchange
    "Name",                 # Name/Exchange
    "Points",               # QSO Points
]
]

dupe_type = 2  # per band

# List of valid Texas county codes (abbreviated list for brevity)
TEXAS_COUNTY_CODES = {
    "AND": "Anderson", "ANDR": "Andrews", "ANG": "Angelina", "ARC": "Archer",
    "ARM": "Armstrong", "ATAS": "Atascosa", "AUS": "Austin",
    # ... Add all TQP 3-letter/4-letter county codes here ...
    "TRV": "Travis", "WIL": "Williamson", "HAY": "Hays", "DAL": "Dallas",
}

def init_contest(self):
    """Setup plugin"""
    set_tab_next(self)
    set_tab_prev(self)
    interface(self)
    self.next_field = self.other_1

def interface(self):
    """Setup UI labels"""
    self.field1.show()
    self.field2.show()
    self.field3.show()
    self.field4.show()
    self.other_label.setText("Sent Cty/State")
    self.field3.setAccessibleName("Sent Exchange")
    self.exch_label.setText("Rcvd Cty/State")
    self.field4.setAccessibleName("Rcvd Exchange")

def reset_label(self):
    """Reset label after field cleared (required stub)."""
    pass

def set_tab_next(self):
    self.tab_next = {
        self.callsign: self.other_1,
        self.other_1: self.other_2,
        self.other_2: self.callsign,
    }

def set_tab_prev(self):
    self.tab_prev = {
        self.callsign: self.other_2,
        self.other_1: self.callsign,
        self.other_2: self.other_1,
    }

def set_contact_vars(self):
    """Save QSO data, split exchange fields"""
    self.contact["SNT"] = self.sent.text()
    self.contact["RCV"] = self.receive.text()
    self.contact["SentCounty"] = self.other_1.text().strip().upper()
    self.contact["RcvCounty"] = self.other_2.text().strip().upper()

    # Points are handled separately
    self.contact["NR"] = self.other_2.text().strip().upper()

    result = self.database.fetch_call_exists(self.callsign.text().upper())
    self.contact["IsMultiplier1"] = 1 if result and result.get("call_count", 0) == 0 else 0

def check_call_history(self):
    """Auto-fill Rcvd Cty/State from call history or validate county codes."""
    call = self.callsign.text().strip().upper()
    result = self.database.fetch_call_history(call)

    # First, try to pull from history
    if result:
        self.history_info.setText(result.get("UserText", ""))
        exch = result.get("Exch1", "").upper()
        if exch and not self.other_2.text():
            # If code is a valid Texas county, auto-fill with county name
            if exch in TEXAS_COUNTY_CODES:
                self.other_2.setText(f"{exch} ({TEXAS_COUNTY_CODES[exch]}) ")
            else:
                self.other_2.setText(f"{exch} ")
        return

    # No history, validate current text if user typed something
    exch = self.other_2.text().strip().upper()
    if exch in TEXAS_COUNTY_CODES:
        self.history_info.setText(f"TX County: {TEXAS_COUNTY_CODES[exch]}")

def points(self):
    """Assign points based on mode"""
    if self.contact_is_dupe > 0:
        return 0
    mode = self.contact.get("Mode", "").upper()
    if mode == "CW" or mode == "DIGI":
        return 2
    return 1

def show_mults(self):
    result = self.database.fetch_call_count()
    return int(result.get("call_count", 0)) if result else 0

def show_qso(self):
    result = self.database.fetch_qso_count()
    return int(result.get("qsos", 0)) if result else 0

def calc_score(self):
    """Return calculated score safely, even if DB has None values."""
    result = self.database.fetch_points()
    if not result:
        return 0
    points = result.get("Points", 0) or 0
    try:
        points = int(points)
    except (ValueError, TypeError):
        points = 0
    return points * show_mults(self)

def adif(self):
    gen_adif(self, cabrillo_name, "TQP")

def cabrillo(self, file_encoding):
    """Generate Cabrillo file"""
    now = datetime.datetime.now()
    filename = (
        str(Path.home())
        + "/"
        + f"{self.station.get('Call', '').upper()}_{cabrillo_name}_{now.strftime('%Y-%m-%d_%H-%M-%S')}.log"
    )
    log = self.database.fetch_all_contacts_asc()
    try:
        with open(filename, "w", encoding=file_encoding, newline="") as f:
            f.write(f"START-OF-LOG: 3.0\r\n")
            f.write(f"CONTEST: {cabrillo_name}\r\n")
            for contact in log:
                date = contact.get("TS", "")[:10]
                time = contact.get("TS", "")[11:13] + contact.get("TS", "")[14:16]
                freq = str(int(contact.get("Freq", "0"))).rjust(5)
                mode = contact.get("Mode", "").upper()
                if mode in ["LSB", "USB"]: mode = "PH"
                sent = contact.get("SentCounty", "")
                rcvd = contact.get("RcvCounty", "")
                f.write(
                    f"QSO: {freq} {mode} {date} {time} "
                    f"{contact.get('StationPrefix', '').ljust(13)} "
                    f"{sent.ljust(6)} "
                    f"{contact.get('Call', '').ljust(13)} "
                    f"{rcvd.ljust(6)}\r\n"
                )
            f.write("END-OF-LOG:\r\n")
        self.show_message_box(f"Cabrillo saved to: {filename}")
    except IOError as e:
        self.show_message_box(f"Error saving Cabrillo: {e} {filename}")
