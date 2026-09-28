`timescale 1ns/1ps
// Candidate physical boundary, NOT fitted or ready for programming.
// Requires Gowin rPLL and ODDR libraries, explicit measured video profile,
// and completed input/output timing constraints. No simulation models here.
module amiga_board_top #(
    parameter integer H_SAMPLES=0,VS_ALIGN_CYCLES=-1,
    parameter integer HS_WIDTH=0,X_START=0,X_END=0,Y_START=0,Y_END=0,
    parameter INPUT_MHZ="28.375", parameter integer VCO_DIV=8
)(
    input wire REF_27M,POWER_GOOD,ADC_CLK,ADC_HS,ADC_VS,
    input wire [7:0] ADC_R,ADC_G,ADC_B,
    inout wire I2C_SCL,I2C_SDA,
    output wire ADC_RESET_N,ADC_PWDN,
    output wire [7:0] DAC_R,DAC_G,DAC_B,
    output wire DAC_CLK_RAW,DAC_BLANK_N,DAC_PSAVE_N,H_OUT_RAW,V_OUT_RAW
);
    wire reset,video_clock,pll_lock,pll_reset,scl_low,sda_low;
    configuration_reset startup(.clk_ref(REF_27M),.reset(reset));
    gowin_video_pll #(.INPUT_MHZ(INPUT_MHZ),.VCO_DIV(VCO_DIV)) clocks
      (.adc_clock(ADC_CLK),.reset_pll(pll_reset),.video_clock(video_clock),.locked(pll_lock));
    assign I2C_SCL=scl_low?1'b0:1'bz;
    assign I2C_SDA=sda_low?1'b0:1'bz;
    amiga_logic_core #(.H_SAMPLES(H_SAMPLES),.VS_ALIGN_CYCLES(VS_ALIGN_CYCLES),
      .HS_WIDTH(HS_WIDTH),.X_START(X_START),.X_END(X_END),.Y_START(Y_START),.Y_END(Y_END)) logic_core
      (.clk_ref(REF_27M),.reset(reset),.power_good(POWER_GOOD),
       .adc_clock(ADC_CLK),.video_clock(video_clock),.pll_lock(pll_lock),
       .adc_rgb({ADC_R,ADC_G,ADC_B}),.adc_hs_n(ADC_HS),.adc_vs_n(ADC_VS),
       .scl_in(I2C_SCL),.sda_in(I2C_SDA),.scl_low(scl_low),.sda_low(sda_low),
       .adc_reset_n(ADC_RESET_N),.adc_pwdn(ADC_PWDN),.pll_reset(pll_reset),
       .dac_rgb({DAC_R,DAC_G,DAC_B}),.dac_blank_n(DAC_BLANK_N),.dac_psave_n(DAC_PSAVE_N),
       .hs_out_n(H_OUT_RAW),.vs_out_n(V_OUT_RAW),
       .configured_ref(),.video_ready_ref(),.configuration_fault(),
       .write_error(),.clock_fault_history(),.sync_fault_history(),.failed_register());
    // Dedicated output DDR, not a LUT-inverted/gated clock. Candidate inverted
    // phase: DAC rising edge follows video falling edge. Board buffer delay,
    // RGB/BLANK skew, duty and actual ODDR latency still require timing closure.
    // Must be placed on an IO-logic-capable pin (candidate: IOL17B, pin 16).
    ODDR #(.TXCLK_POL(1'b0),.INIT(1'b0)) dac_clock_output
      (.CLK(video_clock),.D0(1'b0),.D1(1'b1),.TX(1'b0),.Q0(DAC_CLK_RAW),.Q1());
endmodule
