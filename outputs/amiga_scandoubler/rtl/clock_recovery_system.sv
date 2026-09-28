`timescale 1ns/1ps
// Reference-domain lifecycle plus video-domain watchdog. The actual PLL
// connects adc_clock -> video_clock, takes pll_reset and supplies pll_lock.
module clock_recovery_system #(
    parameter integer GOOD_INTERVALS=8,RESET_HOLD_CYCLES=270,LOCK_TIMEOUT_CYCLES=270000
)(
    input wire clk_ref,adc_clock,video_clock,reset,qualified_ref,pll_lock,
    output wire pll_reset,reset_video,output_permitted,dac_psave_n,
    output wire run_ref,input_stable,
    output wire [2:0] fault_history
);
    wire ready_ref;
    pll_restart_control #(.GOOD_INTERVALS(GOOD_INTERVALS),.RESET_HOLD_CYCLES(RESET_HOLD_CYCLES),
      .LOCK_TIMEOUT_CYCLES(LOCK_TIMEOUT_CYCLES)) restart
      (.clk_ref(clk_ref),.adc_clock(adc_clock),.reset(reset),.qualified_ref(qualified_ref),
       .pll_lock(pll_lock),.video_ready_ref(ready_ref),.pll_reset(pll_reset),
       .run_ref(run_ref),.input_stable(input_stable),.fault_history(fault_history));
    video_clock_guard guard
      (.clk_ref(clk_ref),.clk_video(video_clock),.reset(reset),
       .qualified_ref(qualified_ref && !pll_reset),.pll_lock(pll_lock),
       .reset_video(reset_video),.output_permitted(output_permitted),
       .ready_ref(ready_ref),.dac_psave_n(dac_psave_n));
endmodule
