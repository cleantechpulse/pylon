__author__ = 'Richard W. Lincoln, r.w.lincoln@gmail.com'

import os
import sys
import logging

from Tkinter import *
from tkFileDialog import askopenfilename, asksaveasfilename

from pylon.readwrite import \
    MATPOWERReader, MATPOWERWriter, ReSTWriter, PSSEReader, PSATReader

from pylon import \
    Network, DCPF, NewtonRaphson, FastDecoupled, DCOPF, ACOPF, UDOPF

logger = logging.getLogger(__name__)

CASE_6_WW = os.path.dirname(__file__) + "/test/data/case6ww.m"
CASE_30   = os.path.dirname(__file__) + "/test/data/case30pwl.m"


class PylonTk:
    def __init__(self, master):
        self.root = master

        self.frame = Frame(master)
        self.frame.pack(expand=YES, fill=BOTH)

        self._init_menubar()
        self._init_toolbar()
        self._init_logframe()

        self.on_new()


    def _init_menubar(self):
        menu = Menu(self.root)
        self.root.config(menu=menu)

        filemenu = Menu(menu, tearoff=False)
        filemenu.add_command(label="New", command=self.on_new)
        filemenu.add_separator()
        filemenu.add_command(label="Open...", command=self.on_open)
        menu.add_cascade(label="Case", menu=filemenu)

        presetmenu = Menu(filemenu, tearoff=False)
        filemenu.add_cascade(label='Preset', menu=presetmenu)
        presetmenu.add_command(label="6 bus", command=self.on_6_bus)
        presetmenu.add_command(label="30 bus", command=self.on_30_bus)
        filemenu.add_separator()

        filemenu.add_command(label="Save As...", command=self.on_save_as)
        filemenu.add_separator()

        importmenu = Menu(filemenu, tearoff=False)
        filemenu.add_cascade(label='Import', menu=importmenu)
        importmenu.add_command(label="Pickle", command=self.on_unpickle)
        importmenu.add_command(label="PSS/E", command=self.on_psse)
        importmenu.add_command(label="PSAT", command=self.on_psat)

        exportmenu = Menu(filemenu, tearoff=False)
        filemenu.add_cascade(label='Export', menu=exportmenu)
        exportmenu.add_command(label="Pickle", command=self.on_pickle)
        exportmenu.add_command(label="Excel", command=self.on_excel)
        exportmenu.add_command(label="CSV", command=self.on_csv)
        exportmenu.add_command(label="ReST", command=self.on_rest)
        filemenu.add_separator()

        filemenu.add_command(label="Exit", command=self.on_exit,
                             accelerator="Alt-X")
        self.root.bind('<Alt-x>', self.on_exit)

        pfmenu = Menu(menu, tearoff=False)
        menu.add_cascade(label="Power Flow", menu=pfmenu)
        pfmenu.add_command(label="DC PF", command=self.on_dcpf)
        pfmenu.add_command(label="Newton-Raphson", command=self.on_newton)
        pfmenu.add_command(label="Fast Decoupled", command=self.on_fd)

        opfmenu = Menu(menu, tearoff=False)
        menu.add_cascade(label="OPF", menu=opfmenu)
        opfmenu.add_command(label="DC OPF", command=self.on_dcopf)
        opfmenu.add_command(label="AC OPF", command=self.on_acopf)
        opfmenu.add_command(label="DC (UD) OPF", command=self.on_duopf)
        opfmenu.add_command(label="AC (UD) OPF", command=self.on_uopf)


    def _init_toolbar(self):
        toolbar = Frame(self.frame)
        toolbar.pack(side=LEFT, fill=Y)
        Button(toolbar, text="Summary",
               command=self.on_summary).pack(fill=X)
        Button(toolbar, text="Bus",
               command=self.on_bus_info).pack(fill=X)
        Button(toolbar, text="Branch",
               command=self.on_branch_info).pack(fill=X)
        Button(toolbar, text="Generator",
               command=self.on_generator_info).pack(fill=X)


    def _init_logframe(self):
        self.ui_log = UILog(self.frame)

#        sys.stdout = self.ui_log
#        sys.stderr = self.ui_log
        logging.basicConfig(stream=self.ui_log, level=logging.DEBUG,
                            format="%(levelname)s: %(message)s")

        self.ui_log.level.set(logger.getEffectiveLevel())


    def on_new(self):
        self.n = Network()


    def on_open(self):
        ftypes = [("MATLAB file", ".m"), ("All files", "*")]
        filename = askopenfilename(filetypes=ftypes, defaultextension='.m')
        if filename:
            self.n = MATPOWERReader().read(filename)


    def on_6_bus(self):
        self.n = MATPOWERReader().read(CASE_6_WW)


    def on_30_bus(self):
        self.n = MATPOWERReader().read(CASE_30)


    def on_save_as(self):
        filename = asksaveasfilename(filetypes=[("MATLAB file", ".m")])
        if filename:
            MATPOWERWriter().write(self.n, filename)

    # Import handlers ---------------------------------------------------------

    def on_unpickle(self):
        ftypes = [("Pickle file", ".pkl"), ("All files", "*")]
        filename = askopenfilename(filetypes=ftypes, defaultextension='.pkl')
        if filename:
            self.n = PickleReader().read(filename)


    def on_psse(self):
        ftypes = [("PSS/E file", ".raw"), ("All files", "*")]
        filename = askopenfilename(filetypes=ftypes, defaultextension='.raw')
        if filename:
            self.n = PSSEReader().read(filename)


    def on_psat(self):
        ftypes = [("PSAT file", ".m"), ("All files", "*")]
        filename = askopenfilename(filetypes=ftypes, defaultextension='.m')
        if filename:
            self.n = PSATReader().read(filename)

    # Export handlers ---------------------------------------------------------

    def on_pickle(self):
        filename = asksaveasfilename(filetypes=[("Pickle file", ".pkl")])
        if filename:
            PickleWriter().write(self.n, filename)


    def on_excel(self):
        filename = asksaveasfilename(filetypes=[("Excel file", ".xls")])
        if filename:
            ExcelWriter().write(self.n, filename)


    def on_csv(self):
        filename = asksaveasfilename(filetypes=[("CSV file", ".csv")])
        if filename:
            CSVWriter().write(self.n, filename)


    def on_rest(self):
        ftypes = [("ReStructuredText file", ".rst")]
        filename = asksaveasfilename(filetypes=ftypes)
        if filename:
            ReSTWriter().write(self.n, filename)

    # -------------------------------------------------------------------------

    def on_summary(self):
        writer = ReSTWriter()
        writer.write_how_many(self.n, self.ui_log)
        writer.write_how_much(self.n, self.ui_log)
        writer.write_min_max(self.n, self.ui_log)
        del writer

    def on_bus_info(self):
        ReSTWriter().write_bus_data(self.n, self.ui_log)


    def on_branch_info(self):
        ReSTWriter().write_branch_data(self.n, self.ui_log)


    def on_generator_info(self):
        ReSTWriter().write_generator_data(self.n, self.ui_log)


    def on_dcpf(self):
        DCPF().solve(self.n)


    def on_newton(self):
        NewtonRaphson().solve(self.n)


    def on_fd(self):
        FastDecoupled().solve(self.n)


    def on_dcopf(self):
        DCOPF().solve(self.n)


    def on_acopf(self):
        ACOPF().solve(self.n)


    def on_duopf(self):
        UDOPF(dc=True).solve(self.n)


    def on_uopf(self):
        UDOPF(dc=False).solve(self.n)


    def on_exit(self, event=None):
        self.root.destroy()
#        sys.exit(0)


class UILog:
    def __init__(self, master):
        self.master = master

        self._init_text()
        self._init_levels()


    def _init_text(self):
        logframe = Frame(self.master)

        logframe.grid_rowconfigure(0, weight=1)
        logframe.grid_columnconfigure(0, weight=1)

        xscrollbar = Scrollbar(logframe, orient=HORIZONTAL)
        xscrollbar.grid(row=1, column=0, sticky=E+W)

        yscrollbar = Scrollbar(logframe)
        yscrollbar.grid(row=0, column=1, sticky=N+S)

        log = self.log = Text(logframe, wrap=NONE, background="white",
                        xscrollcommand=xscrollbar.set,
                        yscrollcommand=yscrollbar.set)

        log.grid(row=0, column=0, sticky=N+S+E+W)

        xscrollbar.config(command=log.xview)
        yscrollbar.config(command=log.yview)

        logframe.pack(expand=YES, fill=BOTH)


    def _init_levels(self):
        loglevels = Frame(self.master)
        loglevels.pack(fill=X)

        level = self.level = IntVar()

        debug = Radiobutton(loglevels, text="DEBUG", variable=level,
                            value=logging.DEBUG, command=self.on_level)
        debug.pack(side=LEFT, anchor=E)
        info = Radiobutton(loglevels, text="INFO", variable=level,
                           value=logging.INFO, command=self.on_level)
        info.pack(side=LEFT, anchor=E)
        warn = Radiobutton(loglevels, text="WARN", variable=level,
                           value=logging.WARNING, command=self.on_level)
        warn.pack(side=LEFT, anchor=E)
        error = Radiobutton(loglevels, text="ERROR", variable=level,
                            value=logging.ERROR, command=self.on_level)
        error.pack(side=LEFT, anchor=E)

        level.set(logger.getEffectiveLevel())


    def write(self, buf):
        self.log.insert(END, buf)
        self.log.see(END)


    def flush(self):
        pass


    def on_level(self):
#        logger.setLevel(self.level.get())

#        print logging.getLogger(__name__).getEffectiveLevel(), self.level.get()
        logging.basicConfig(stream=self, level=self.level.get(),
                            format="%(levelname)s: %(message)s")
#        print logging.getLogger(__name__).getEffectiveLevel(), self.level.get()


def main():
    root = Tk()
    root.minsize(300, 300)
#    root.geometry("666x666")
    root.title('PYLON')
    app = PylonTk(root)
    root.mainloop()


if __name__ == "__main__":
#    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG,
#                        format="%(levelname)s: %(message)s")

#    logger.addHandler(logging.StreamHandler(sys.stdout))
#    logger.setLevel(logging.DEBUG)

    main()
