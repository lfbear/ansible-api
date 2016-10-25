def get_poller(self):
    # code from https://github.com/Supervisor/supervisor/pull/129
    import select
    import errno

    class BasePoller:

        def __init__(self):
            self.initialize()

        def initialize(self):
            pass

        def register_readable(self, fd):
            raise NotImplementedError

        def poll(self, timeout):
            raise NotImplementedError

    class SelectPoller(BasePoller):

        def initialize(self):
            self._select = select
            self.readables = set()

        def register_readable(self, fd):
            self.readables.add(fd)

        def poll(self, timeout):
            try:
                r, w, x = self._select.select(self.readables, [], [], timeout)
            except select.error, err:
                if err[0] == errno.EINTR:
                    display.vvv(u"EINTR encountered in poll")
                    return [], []
                if err[0] == errno.EBADF:
                    display.vvv(u"EBADF encountered in poll")
                    return [], []
                raise
            return r, []

    class PollPoller(BasePoller):

        def initialize(self):
            self._poller = select.poll()
            self.READ = select.POLLIN | select.POLLPRI | select.POLLHUP
            self.readables_fd_map = {}

        def register_readable(self, fd):
            self.readables_fd_map[fd.fileno()] = fd
            self._poller.register(fd, self.READ)

        def poll(self, timeout):
            try:
                fds = self._poller.poll(timeout * 1000)
            except select.error, err:
                if err[0] == errno.EINTR:
                    display.vvv(u"EINTR encountered in poll")
                    return [], []
                raise
            readables = []
            for fd, eventmask in fds:
                if eventmask & select.POLLNVAL:
                    # POLLNVAL means `fd` value is invalid, not open.
                    self._poller.unregister(fd)
                elif eventmask & self.READ:
                    if fd in self.readables_fd_map:
                        readables.append(self.readables_fd_map[fd])
            return readables, []

    class KQueuePoller(BasePoller):

        def initialize(self):
            self.MAX_EVENTS = 1000
            self._kqueue = select.kqueue()
            self.readables_fd_map = {}

        def register_readable(self, fd):
            self.readables_fd_map[fd.fileno()] = fd
            kevent = select.kevent(fd, filter=select.KQ_FILTER_READ,
                                   flags=select.KQ_EV_ADD)
            self._kqueue_control(fd, kevent)

        def _kqueue_control(fd, kevent):
            try:
                self._kqueue.control([kevent], 0)
            except OSError, error:
                if error.errno == errno.EBADF:
                    display.vvv(u"EBADF encountered in kqueue")
                else:
                    raise

        def poll(self, timeout):
            try:
                kevents = self._kqueue.control(None, self.MAX_EVENTS, timeout)
            except OSError, error:
                if error.errno == errno.EINTR:
                    display.vvv(u"EINTR encountered in kqueue")
                    return [], []
                raise
            readables = []
            for kevent in kevents:
                if kevent.filter == select.KQ_FILTER_READ:
                    if kevent.ident in self.readables_fd_map:
                        readables.append(self.readables_fd_map[kevent.ident])
            return readables, []
    if hasattr(select, 'kqueue'):
        Poller = KQueuePoller
    elif hasattr(select, 'poll'):
        Poller = PollPoller
    else:
        Poller = SelectPoller
    return Poller()
