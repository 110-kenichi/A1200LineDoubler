`timescale 1ns/1ps
// Clock supervision plus synchronous video processing. Capture front end,
// device PLL primitive, ADC configuration and physical I/O remain external.
module supervised_video_core #(
    parameter integer H_SAMPLES=0, HS_WIDTH=0,
    parameter integer X_START=0,X_END=0,Y_START=0,Y_END=0,
    parameter integer VS_LINES=5,
    parameter integer AW=(H_SAMPLES>1?$clog2(H_SAMPLES):1),
    parameter integer HEARTBEAT_BITS=8,MIN_EDGE_CYCLES=40,MAX_EDGE_CYCLES=80
)(
    input wire clk_ref,clk_video,reset,qualified_ref,pll_lock,
    input wire sample_ce,line_start,field_start,
    input wire [23:0] pixel_in,
    output wire [23:0] rgb,
    output wire blank_n,hs_n,vs_n,ready_ref,reset_video,protocol_error,dac_psave_n
);
    wire permit, core_blank,core_hs,core_vs;
    wire [23:0] core_rgb;
    video_clock_guard #(.HEARTBEAT_BITS(HEARTBEAT_BITS),
      .MIN_EDGE_CYCLES(MIN_EDGE_CYCLES),.MAX_EDGE_CYCLES(MAX_EDGE_CYCLES)) guard
      (.clk_ref(clk_ref),.clk_video(clk_video),.reset(reset),
       .qualified_ref(qualified_ref),.pll_lock(pll_lock),
       .reset_video(reset_video),.output_permitted(permit),.ready_ref(ready_ref),.dac_psave_n(dac_psave_n));
    video_core #(.H_SAMPLES(H_SAMPLES),.HS_WIDTH(HS_WIDTH),
      .X_START(X_START),.X_END(X_END),.Y_START(Y_START),.Y_END(Y_END),.VS_LINES(VS_LINES)) core
      (.clk(clk_video),.reset(reset_video),.sample_ce(sample_ce),
       .line_start(line_start),.field_start(field_start),.pixel_in(pixel_in),
       .rgb(core_rgb),.blank_n(core_blank),.hs_n(core_hs),.vs_n(core_vs),
       .out_sol(),.frame_start(),.out_x(),.out_y(),.protocol_error(protocol_error));
    // Do not rely on a clocked pixel register to blank a stopped clock.
    assign blank_n=permit && core_blank;
    assign rgb=blank_n?core_rgb:24'b0;
    assign hs_n=permit?core_hs:1'b1;
    assign vs_n=permit?core_vs:1'b1;
endmodule
