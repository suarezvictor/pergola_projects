from nmigen import *

class CustomImageGenerator(Elaboratable):
    def __init__(self, vsync, v_ctr, h_ctr, r, g, b, active, fname):
        self.vsync = vsync
        self.v_ctr = v_ctr
        self.h_ctr = h_ctr
        self.r = r
        self.g = g
        self.b = b
        self.active = active

        with open(fname, 'r') as file:
          self.verilog = file.read()

    def elaborate(self, platform):
        m = Module()
        done = Signal()
        out_clock = Signal()
        m.submodules.framedisplay = Instance("M_frame_display__display",
            i_in_pix_x = self.h_ctr,
            i_in_pix_y = self.v_ctr,
            i_in_pix_active = self.active,
            i_in_pix_vblank = self.vsync,
            o_out_pix_r = self.r,
            o_out_pix_g = self.g,
            o_out_pix_b = self.b,
            o_out_done = done,
            i_reset = ResetSignal(),
            o_out_clock = out_clock,
            i_clock = ClockSignal("sync")
        )
        platform.add_file("framegen_added.v", self.verilog)
        return m


class StaticTestImageGenerator(Elaboratable):
    def __init__(self, vsync, v_ctr, h_ctr, r, g, b):
        self.vsync = vsync
        self.v_ctr = v_ctr
        self.h_ctr = h_ctr
        self.r = r
        self.g = g
        self.b = b

    def elaborate(self, platform):
        m = Module()

        m.d.sync += self.r.eq(self.h_ctr)
        m.d.sync += self.g.eq(self.v_ctr)
        m.d.sync += self.b.eq(127)

        return m


class TestImageGenerator(Elaboratable):
    def __init__(self, vsync, v_ctr, h_ctr, r, g, b, speed=1, width=640, height=480):
        self.vsync = vsync
        self.v_ctr = v_ctr
        self.h_ctr = h_ctr
        self.r = r
        self.g = g
        self.b = b
        self.frame = Signal(16)
        self.speed = speed

    def elaborate(self, platform):
        m = Module()

        vsync = self.vsync
        v_ctr = self.v_ctr
        h_ctr = self.h_ctr
        r = self.r
        g = self.g
        b = self.b

        frame = self.frame
        vsync_r = Signal()
        m.d.sync += vsync_r.eq(vsync)
        with m.If(~vsync_r & vsync):
            m.d.sync += frame.eq(frame + 1)

        frame_tri = Mux(frame[8], ~frame[:8], frame[:8])
        frame_tri2 = Mux(frame[9], ~frame[1:9], frame[1:9])

        X = Mux(v_ctr[6], h_ctr + frame[self.speed:], h_ctr - frame[self.speed:])
        Y = v_ctr

        m.d.sync += r.eq(frame_tri[1:])
        m.d.sync += g.eq(v_ctr * Mux(X & Y, 255, 0))
        m.d.sync += b.eq(~(frame_tri2 + (X ^ Y)) * 255)

        return m


class RotozoomImageGenerator(Elaboratable):
    def __init__(self, vsync, v_ctr, h_ctr, r, g, b, speed=1, width=640, height=480):
        self.vsync = vsync
        self.v_ctr = v_ctr
        self.h_ctr = h_ctr
        self.frame = Signal(11)
        self.speed = speed
        self.width = width
        self.height = height

        self.r = r
        self.g = g
        self.b = b

    # def hsv2rgb(self, m, h, s, v, r, g, b):
    #     region = h[5:]
    #     fpart = (h - (region << 5)) * 6
    #     p = (v * (255 - s)) >> 8
    #     q = (v * (255 - ((s * fpart) >> 8))) >> 8
    #     t = (v * (255 - ((s * (255 - fpart)) >> 8))) >> 8
    #     with m.Switch(region):
    #         with m.Case(0):
    #             m.d.comb += [r.eq(v), g.eq(t), b.eq(p)]
    #         with m.Case(1):
    #             m.d.comb += [r.eq(q), g.eq(v), b.eq(p)]
    #         with m.Case(2):
    #             m.d.comb += [r.eq(p), g.eq(v), b.eq(t)]
    #         with m.Case(3):
    #             m.d.comb += [r.eq(p), g.eq(q), b.eq(v)]
    #         with m.Case(4):
    #             m.d.comb += [r.eq(t), g.eq(p), b.eq(v)]
    #         with m.Case():
    #             m.d.comb += [r.eq(v), g.eq(p), b.eq(q)]

    def elaborate(self, platform):
        m = Module()

        r = self.r
        g = self.g
        b = self.b

        vsync = self.vsync
        v_ctr = self.v_ctr
        h_ctr = self.h_ctr

        frame = self.frame
        vsync_r = Signal()
        m.d.sync += vsync_r.eq(vsync)
        with m.If(~vsync_r & vsync):
            m.d.sync += frame.eq(frame + 1)

        frame_tri = Mux(frame[10], ~frame[:10], frame[:10])

        X = Signal(Shape(width=16, signed=True))
        Y = Signal.like(X)
        T = Signal.like(X)

        XX = Signal.like(X)
        YY = Signal.like(X)
        TT = Signal.like(X)

        m.d.comb += [
            XX.eq(h_ctr),
            YY.eq(v_ctr),
            TT.eq(frame_tri),
            X.eq(XX - (self.width >> 1)),
            Y.eq(YY - (self.height >> 1)),
            T.eq(TT - 512),
        ]

        S = ((X+(Y*T)[6:]) & ((X*T)[6:]-Y))
        ON = (S[3:9] == 0)

        CIRCLE = (X * X + Y * Y)[9:]

        with m.If(CIRCLE[8:]):
            m.d.sync += [r.eq(0), g.eq(0), b.eq(0)]
        with m.Else():
            m.d.sync += r.eq( Mux(ON, 255 - CIRCLE, 0) )

        return m
