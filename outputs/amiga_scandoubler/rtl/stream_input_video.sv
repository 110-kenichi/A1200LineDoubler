`timescale 1ns/1ps
// Connect to the clock-guard reset and to a separately timed ADC capture stage.
// The board top must still gate DAC PSAVE/BLANK on clock-guard permission.
module stream_input_video #(
    parameter integer H_SAMPLES=0,VS_ALIGN_CYCLES=-1,
    parameter integer HS_WIDTH=0,X_START=0,X_END=0,Y_START=0,Y_END=0,
    parameter integer MIN_FIELD_HALF_LINES=500,MAX_FIELD_HALF_LINES=660
)(
    input wire clk,reset,sample_ce,hs_n_sampled,vs_n_async,
    input wire [23:0] rgb_sampled,
    output wire [23:0] rgb,
    output wire blank_n,hs_n,vs_n,sync_valid,protocol_error,
    output wire [2:0] fault_history
);
    wire ce,line_event,field_event,reset_core,core_blank;
    wire [23:0] pixels,core_rgb;
    stream_sync_frontend #(.H_SAMPLES(H_SAMPLES),.VS_ALIGN_CYCLES(VS_ALIGN_CYCLES),
      .MIN_FIELD_HALF_LINES(MIN_FIELD_HALF_LINES),.MAX_FIELD_HALF_LINES(MAX_FIELD_HALF_LINES)) front
      (.clk(clk),.reset(reset),.sample_ce(sample_ce),.hs_n_sampled(hs_n_sampled),.vs_n_async(vs_n_async),
       .rgb_sampled(rgb_sampled),.sample_ce_out(ce),.line_start(line_event),.field_start(field_event),
       .rgb_out(pixels),.reset_core(reset_core),.sync_valid(sync_valid),.fault_history(fault_history));
    video_core #(.H_SAMPLES(H_SAMPLES),.HS_WIDTH(HS_WIDTH),.X_START(X_START),.X_END(X_END),
      .Y_START(Y_START),.Y_END(Y_END)) core
      (.clk(clk),.reset(reset_core || !sync_valid),.sample_ce(ce),.line_start(line_event),.field_start(field_event),
       .pixel_in(pixels),.rgb(core_rgb),.blank_n(core_blank),.hs_n(hs_n),.vs_n(vs_n),
       .out_sol(),.frame_start(),.out_x(),.out_y(),.protocol_error(protocol_error));
    assign blank_n=core_blank && sync_valid && !reset_core;
    assign rgb=blank_n?core_rgb:24'b0;
endmodule
