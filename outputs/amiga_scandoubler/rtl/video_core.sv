`timescale 1ns/1ps
// Digital integration core, not the ADC capture/PLL or board top level.
// All inputs are synchronous to clk (2x sample frequency). Timing parameters
// MUST be explicitly provided by a validated capture profile.
module video_core #(
    parameter integer H_SAMPLES=0,
    parameter integer HS_WIDTH=0,
    parameter integer X_START=0, X_END=0,
    parameter integer Y_START=0, Y_END=0,
    parameter integer VS_LINES=5,
    parameter integer Y_BITS=12,
    parameter integer AW=(H_SAMPLES>1?$clog2(H_SAMPLES):1)
)(
    input wire clk, reset, sample_ce, line_start, field_start,
    input wire [23:0] pixel_in,
    output wire [23:0] rgb,
    output wire blank_n,
    output reg hs_n, vs_n, out_sol, frame_start,
    output reg [AW-1:0] out_x,
    output reg [Y_BITS-1:0] out_y,
    output wire protocol_error
);
    wire [23:0] line_rgb;
    wire line_valid, line_sol;
    wire [AW-1:0] line_x;
    reg field_delayed;
    wire field_vs, field_frame;
    reg [23:0] rgb1,rgb2;
    reg valid1,valid2,sol1,have_frame;
    reg [AW-1:0] x1;
    initial begin
        if (H_SAMPLES<4 || HS_WIDTH<1 || HS_WIDTH>X_START ||
            X_START>=X_END || X_END>H_SAMPLES || Y_START<VS_LINES ||
            Y_START>=Y_END || Y_END>=(1<<Y_BITS))
            $fatal(1,"Explicit valid video timing profile required");
    end
    line_double #(.H_SAMPLES(H_SAMPLES)) lines
      (.clk(clk),.reset(reset),.sample_ce(sample_ce),.line_start(line_start),
       .pixel_in(pixel_in),.pixel_out(line_rgb),.pixel_valid(line_valid),
       .out_sol(line_sol),.out_x(line_x),.protocol_error(protocol_error));
    // line_sol is registered by line_double. Delay the input event by one
    // clock so field_sync sees both in the same coordinate system.
    always @(posedge clk) begin
        if(reset) field_delayed<=0;
        else field_delayed<=field_start;
    end
    field_sync #(.H_SAMPLES(H_SAMPLES),.VS_LINES(VS_LINES)) fields
      (.clk(clk),.reset(reset),.field_start(field_delayed),.out_sol(line_sol),
       .vs_n(field_vs),.frame_start(field_frame));
    // Two stages after line_double align RGB, HS, VS and vertical line index.
    always @(posedge clk) begin
        if(reset) begin
            rgb1<=0;rgb2<=0;valid1<=0;valid2<=0;sol1<=0;x1<=0;
            out_x<=0;out_y<=0;out_sol<=0;frame_start<=0;
            hs_n<=1;vs_n<=1;have_frame<=0;
        end else begin
            rgb1<=line_rgb;valid1<=line_valid;sol1<=line_sol;x1<=line_x;
            rgb2<=rgb1;valid2<=valid1;out_x<=x1;out_sol<=sol1;
            hs_n<=!(valid1 && x1<HS_WIDTH);vs_n<=field_vs;frame_start<=field_frame;
            if(protocol_error) have_frame<=0;
            else if(field_frame) begin out_y<=0;have_frame<=1;end
            else if(sol1 && have_frame) begin
                // Saturate rather than showing repeated active windows when
                // input fields disappear while line synchronization survives.
                if(out_y!={Y_BITS{1'b1}}) out_y<=out_y+1'b1;
            end
        end
    end
    assign blank_n=!reset && !protocol_error && valid2 && have_frame &&
                   out_x>=X_START && out_x<X_END && out_y>=Y_START && out_y<Y_END;
    assign rgb=blank_n?rgb2:24'b0;
endmodule
