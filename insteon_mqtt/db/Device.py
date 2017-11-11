#===========================================================================
#
# Non-modem device all link database class
#
#===========================================================================
import io
import logging
from .. import message as Msg
from .DeviceEntry import DeviceEntry

LOG = logging.getLogger(__name__)


class Device:
    @staticmethod
    def from_json(data):
        obj = Device()
        
        for d in data['used']:
            entry = DeviceEntry.from_json(d)
            obj._add_used(entry)
            
        for d in data['unused']:
            entry = DeviceEntry.from_json(d)
            obj._add_unused(entry)

        return obj

    #-----------------------------------------------------------------------
    def __init__(self):
        self.entries = []
        self.unused = []
        self.groups = {}

        # Last entry in memory space - the lowest memory address record.
        self._last_entry = None

    #-----------------------------------------------------------------------
    def __len__(self):
        return len(self.entries)
    
    #-----------------------------------------------------------------------
    def add(self, msg):
        assert(isinstance(msg, Msg.InpExtended))
        assert(msg.data[1] == 0x01)  # record response

        entry = DeviceEntry.from_bytes(msg.data)

        if not entry.ctrl.in_use:
            LOG.info("Ignoring device db record in_use = False")
            self._add_unused(entry)
            return

        LOG.info("Adding db record %s grp: %s lev: %s", entry.addr,
                 entry.group, entry.on_level)
        self._add_used(entry)

    #-----------------------------------------------------------------------
    def find_group(self, group):
        entries = self.groups.get(group, [])
        return entries

    #-----------------------------------------------------------------------
    def find(self, addr, group, type):
        assert(type == 'RESP' or type == 'CTRL')
        is_controller = type == 'CTRL'
        
        for entry in self.entries:
            if (entry.addr == addr and entry.group == group and
                entry.ctrl.is_controller == is_controller):
                return entry

        return None
        
    #-----------------------------------------------------------------------
    def to_json(self):
        used = [ i.to_json() for i in self.entries ]
        unused = [ i.to_json() for i in self.unused ]
        return { 'used' : used, 'unused' : unused }

    #-----------------------------------------------------------------------
    def __str__(self):
        o = io.StringIO()
        o.write("DeviceDb:\n")
        for elem in sorted(self.entries, key=lambda i: i.addr.id):
            o.write("  %s\n" % elem)

        o.write("GroupMap\n")
        for grp, elem in self.groups.items():
            o.write( "  %s -> %s\n" % (grp, [i.addr.hex for i in elem]))
                
        return o.getvalue()

    #-----------------------------------------------------------------------
    def _add_used(self, entry):
        self._update_last(entry)
        self.entries.append(entry)

        if entry.ctrl.is_controller:
            responders = self.groups.setdefault(entry.group, [])
            if entry not in responders:
                responders.append(entry)

    #-----------------------------------------------------------------------
    def _add_unused(self, entry):
        self._update_last(entry)
        self._add_unused(entry)

    #-----------------------------------------------------------------------
    def _update_last(self, entry):
        if (self._last_entry is None or
            self._last_entry.mem_loc > entry.mem_loc):
            self._last_entry = entry

    #-----------------------------------------------------------------------

