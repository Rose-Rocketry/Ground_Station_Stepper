#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# SPDX-License-Identifier: GPL-3.0
#
# GNU Radio Python Flow Graph
# Title: bpsk_stage1
# GNU Radio version: 3.8.2.0

from gnuradio import blocks
import pmt
from gnuradio import digital
from gnuradio import filter
from gnuradio.filter import firdes
from gnuradio import gr
import sys
import signal
from argparse import ArgumentParser
from gnuradio.eng_arg import eng_float, intx
from gnuradio import eng_notation
import osmosdr
import time


class bpsk_stage1(gr.top_block):

    def __init__(self):
        gr.top_block.__init__(self, "bpsk_stage1")

        ##################################################
        # Variables
        ##################################################
        self.sps = sps = 4
        self.samp_rate = samp_rate = 32000
        self.excess_bw = excess_bw = 0.35
        self.rrc_taps = rrc_taps = firdes.root_raised_cosine(1.0,samp_rate,samp_rate/sps,excess_bw,11*sps)
        self.bpsk = bpsk = digital.constellation_bpsk().base()

        ##################################################
        # Blocks
        ##################################################
        self.osmosdr_sink_1 = osmosdr.sink(
            args="numchan=" + str(1) + " " + ""
        )
        self.osmosdr_sink_1.set_time_unknown_pps(osmosdr.time_spec_t())
        self.osmosdr_sink_1.set_sample_rate(samp_rate)
        self.osmosdr_sink_1.set_center_freq(426e6, 0)
        self.osmosdr_sink_1.set_freq_corr(0, 0)
        self.osmosdr_sink_1.set_gain(40, 0)
        self.osmosdr_sink_1.set_if_gain(20, 0)
        self.osmosdr_sink_1.set_bb_gain(20, 0)
        self.osmosdr_sink_1.set_antenna('', 0)
        self.osmosdr_sink_1.set_bandwidth(0, 0)
        self.fir_filter_xxx_0 = filter.fir_filter_ccc(1, rrc_taps)
        self.fir_filter_xxx_0.declare_sample_delay(0)
        self.digital_constellation_modulator_0 = digital.generic_mod(
            constellation=bpsk,
            differential=True,
            samples_per_symbol=4,
            pre_diff_code=True,
            excess_bw=0.35,
            verbose=False,
            log=False)
        self.blocks_file_source_0 = blocks.file_source(gr.sizeof_char*1, '/home/pi/nonbi_angleinfo.dat', True, 0, 0)
        self.blocks_file_source_0.set_begin_tag(pmt.PMT_NIL)



        ##################################################
        # Connections
        ##################################################
        self.connect((self.blocks_file_source_0, 0), (self.digital_constellation_modulator_0, 0))
        self.connect((self.digital_constellation_modulator_0, 0), (self.fir_filter_xxx_0, 0))
        self.connect((self.fir_filter_xxx_0, 0), (self.osmosdr_sink_1, 0))


    def get_sps(self):
        return self.sps

    def set_sps(self, sps):
        self.sps = sps
        self.set_rrc_taps(firdes.root_raised_cosine(1.0,self.samp_rate,self.samp_rate/self.sps,self.excess_bw,11*self.sps))

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.set_rrc_taps(firdes.root_raised_cosine(1.0,self.samp_rate,self.samp_rate/self.sps,self.excess_bw,11*self.sps))
        self.osmosdr_sink_1.set_sample_rate(self.samp_rate)

    def get_excess_bw(self):
        return self.excess_bw

    def set_excess_bw(self, excess_bw):
        self.excess_bw = excess_bw
        self.set_rrc_taps(firdes.root_raised_cosine(1.0,self.samp_rate,self.samp_rate/self.sps,self.excess_bw,11*self.sps))

    def get_rrc_taps(self):
        return self.rrc_taps

    def set_rrc_taps(self, rrc_taps):
        self.rrc_taps = rrc_taps
        self.fir_filter_xxx_0.set_taps(self.rrc_taps)

    def get_bpsk(self):
        return self.bpsk

    def set_bpsk(self, bpsk):
        self.bpsk = bpsk





def main(top_block_cls=bpsk_stage1, options=None):
    tb = top_block_cls()

    def sig_handler(sig=None, frame=None):
        tb.stop()
        tb.wait()

        sys.exit(0)

    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)

    tb.start()

    try:
        input('Press Enter to quit: ')
    except EOFError:
        pass
    tb.stop()
    tb.wait()


if __name__ == '__main__':
    main()
