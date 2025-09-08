"""Texas QSO Party (TQP) plugin"""

import logging
from not1mm.lib.plugin_common import gen_adif
from not1mm.lib.version import __version__

logger = logging.getLogger(__name__)

name = "Texas QSO Party"
cabrillo_name = "TEXAS-QSO-PARTY"
mode = "CW"  # or "BOTH" if SSB is allowed
columns = [
    "TS",
    "Call",
    "Freq",
    "SNT",
    "RCV",
    "SentNr",
    "NR",
    "Name",
    "Points",
]
dupe_type = 2  # Work each band

def init_contest(self):
    """Initialize Texas QSO Party plugin."""
    set_tab_next(self)
    set_tab_prev(self)
    interface(self)
    self.next_field = self.other_1

def interface(self):
    """Setup user interface fields."""
    self.field1.show()  # Sent RST
    self.field2.show()  # Received RST
    self.field3.show()  # Sent serial (other_1)
    self.field4.show()  # Received serial/exchange (other_2)
    self.other_label.setText("SentNr")
    self.exch_label.setText("Rcv Info")

def reset_label(self):
    """Reset label stub (required)."""
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
    """Save contact info to database fields."""
    self.contact["SNT"] = self.sent.text()
    self.contact["RCV"] = self.receive.text()
    self.contact["SentNr"] = self.other_1.text()
    self.contact["NR"] = self.other_2.text()
    self.contact["Name"] = self.other_2.text()

    # Always mark as non-multiplier for now
    self.contact["IsMultiplier1"] = 0

def predupe(self):
    pass

def prefill(self):
    pass

def points(self):
    return 1 if self.contact_is_dupe == 0 else 0

def show_mults(self):
    return 0

def show_qso(self):
    return 0

def calc_score(self):
    return 0

def adif(self):
    gen_adif(self, cabrillo_name, "TEXAS-QSO-PARTY")

