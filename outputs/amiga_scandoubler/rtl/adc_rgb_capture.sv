`timescale 1ns/1ps
// Capture candidate for TVP7002 CLK_POL=0: launches RGB/HS on ADC rising edge.
// adc_clock and video_clock MUST be related, phase-constrained clocks.
// This bus transfer is NOT safe for independent/asynchronous clocks.
// video_clock nominally 2x ADC, +180 degrees of its own period (v0.17).
module adc_rgb_capture(
    input wire adc_clock,video_clock,reset,
    input wire [23:0] adc_rgb,
    input wire adc_hs_n,
    output wire [23:0] rgb_sampled,
    output wire hs_n_sampled,sample_ce,stream_reset
);
    (* ASYNC_REG="TRUE" *) reg [2:0] adc_release;
    always @(negedge adc_clock or posedge reset)
        if(reset)adc_release<=3'b111;
        else adc_release<={adc_release[1:0],1'b0};
    reg [24:0] captured;
    reg token;
    always @(negedge adc_clock or posedge reset) begin
        if(reset)begin captured<={1'b1,24'b0};token<=0;end
        else if(!(|adc_release))begin captured<={adc_hs_n,adc_rgb};token<=!token;end
    end
    // Both bus and token take identical registered paths. Ordinary related-
    // clock setup/hold checks must cover captured -> stage1 and token -> tag1.
    // Do NOT set asynchronous clock groups or blanket false paths here.
    reg [24:0] stage1,stage2;
    reg tag1,tag2,last_tag,started;
    always @(posedge video_clock or posedge reset) begin
        if(reset)begin
            stage1<={1'b1,24'b0};stage2<={1'b1,24'b0};
            tag1<=0;tag2<=0;last_tag<=0;started<=0;
        end else begin
            stage1<=captured;stage2<=stage1;
            tag1<=token;tag2<=tag1;last_tag<=tag2;
            if(tag2!=last_tag)started<=1;
        end
    end
    assign sample_ce=tag2!=last_tag;
    assign {hs_n_sampled,rgb_sampled}=stage2;
    // Hold downstream reset during initial token-pipeline fill. Once running,
    // loss of ADC clock is handled by the independent video_clock_guard.
    assign stream_reset=reset || !started;
endmodule
