`timescale 1ns/1ps
// Candidate primitive configuration, not a fitted/qualified clock solution.
// Static phase/duty settings follow UG286 2.0.2E tables 5-7 and 5-8.
// Use the vendor rPLL library. Do not replace it with a synthesizable oscillator.
module gowin_video_pll #(
    parameter INPUT_MHZ="28.375",
    parameter integer VCO_DIV=8
)(
    input wire adc_clock,reset_pll,
    output wire video_clock,locked
);
    // Check 400 <= 2*input_MHz*VCO_DIV <= 1000 for GW1N-4 C6/I5.
    // Example: 24 MHz needs VCO_DIV=16; VCO_DIV=8 would be below minimum.
    initial if(VCO_DIV!=8 && VCO_DIV!=16) $fatal(1,"Unreviewed VCO divider");
    rPLL #(
      .FCLKIN(INPUT_MHZ),.DEVICE("GW1N-4"),
      .DYN_IDIV_SEL("false"),.IDIV_SEL(0),
      .DYN_FBDIV_SEL("false"),.FBDIV_SEL(1),
      .DYN_ODIV_SEL("false"),.ODIV_SEL(VCO_DIV),
      .DYN_DA_EN("false"),.PSDA_SEL("1000"),.DUTYDA_SEL("1000"),
      .CLKFB_SEL("internal"),.CLKOUT_BYPASS("false"),
      .CLKOUTP_BYPASS("false"),.CLKOUTD_BYPASS("false"),
      .CLKOUT_FT_DIR(1'b1),.CLKOUTP_FT_DIR(1'b1),
      .CLKOUT_DLY_STEP(0),.CLKOUTP_DLY_STEP(0),
      .DYN_SDIV_SEL(2),.CLKOUTD_SRC("CLKOUT"),.CLKOUTD3_SRC("CLKOUT")
    ) pll(
      .CLKIN(adc_clock),.RESET(reset_pll),.RESET_P(1'b0),.CLKFB(1'b0),
      .FBDSEL(6'b0),.IDSEL(6'b0),.ODSEL(6'b0),
      .PSDA(4'b0),.DUTYDA(4'b0),.FDLY(4'b1111),
      .CLKOUT(),.CLKOUTP(video_clock),.CLKOUTD(),.CLKOUTD3(),.LOCK(locked)
    );
endmodule
