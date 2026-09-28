`timescale 1ns/1ps
// Synchronous stream conditioning, NOT an ADC input-register or PLL wrapper.
// rgb_sampled/hs_n_sampled/sample_ce must already meet clk setup/hold.
// vs_n_async is separately synchronized and qualified. Negative VS is assumed.
// Fixed H_SAMPLES only: a different line length deliberately causes reacquisition.
module stream_sync_frontend #(
    parameter integer H_SAMPLES=0,
    parameter integer VS_ALIGN_CYCLES=-1,
    parameter integer HS_GOOD_INTERVALS=3,
    parameter integer VS_FILTER_CYCLES=4,
    parameter integer MIN_FIELD_HALF_LINES=500,MAX_FIELD_HALF_LINES=660,
    parameter integer HW=$clog2(2*H_SAMPLES+2),
    parameter integer VW=$clog2(MAX_FIELD_HALF_LINES*H_SAMPLES+2),
    parameter integer FW=$clog2(VS_FILTER_CYCLES+1),
    parameter integer DW=(VS_ALIGN_CYCLES>0?$clog2(VS_ALIGN_CYCLES+1):1),
    parameter integer GW=$clog2(HS_GOOD_INTERVALS+1)
)(
    input wire clk,reset,sample_ce,hs_n_sampled,vs_n_async,
    input wire [23:0] rgb_sampled,
    output reg sample_ce_out,line_start,field_start,
    output reg [23:0] rgb_out,
    output wire reset_core,sync_valid,
    output reg [2:0] fault_history
);
    localparam MAX_FIELD_CYCLES=MAX_FIELD_HALF_LINES*H_SAMPLES;
    localparam MIN_FIELD_CYCLES=MIN_FIELD_HALF_LINES*H_SAMPLES;
    reg previous_ce,ce_seen,previous_hs,have_hs,h_locked;
    reg [HW-1:0] h_age;
    reg [GW-1:0] h_good;
    (* ASYNC_REG="TRUE" *) reg [1:0] vs_sync;
    reg vs_level,have_vs,v_locked,vs_pending;
    reg [FW-1:0] vs_count;
    reg [VW-1:0] v_age;
    reg [DW-1:0] vs_delay;
    wire h_edge=sample_ce && previous_hs && !hs_n_sampled;
    wire bad_ce=ce_seen && sample_ce==previous_ce;
    wire bad_h=have_hs && ((h_edge && h_age!=2*H_SAMPLES-1) ||
                          (!h_edge && h_age>=2*H_SAMPLES-1));
    wire vs_fall=vs_level && !vs_sync[1] && vs_count==VS_FILTER_CYCLES-1;
    assign reset_core=reset || !h_locked;
    assign sync_valid=!reset && h_locked && v_locked;
    initial begin
        if(H_SAMPLES<4 || H_SAMPLES%2 || VS_ALIGN_CYCLES<0 ||
           VS_ALIGN_CYCLES>=MIN_FIELD_CYCLES || HS_GOOD_INTERVALS<2 ||
           VS_FILTER_CYCLES<2 || MIN_FIELD_HALF_LINES<4 ||
           MAX_FIELD_HALF_LINES<=MIN_FIELD_HALF_LINES)
            $fatal(1,"Explicit stream timing and VS alignment required");
    end
    always @(posedge clk) begin
        if(reset) vs_sync<=2'b11;
        else vs_sync<={vs_sync[0],vs_n_async};
    end
    always @(posedge clk) begin
        if(reset) begin
            previous_ce<=0;ce_seen<=0;previous_hs<=1;have_hs<=0;h_locked<=0;
            h_age<=0;h_good<=0;sample_ce_out<=0;line_start<=0;rgb_out<=0;
            vs_level<=1;vs_count<=0;have_vs<=0;v_locked<=0;v_age<=0;
            vs_pending<=0;vs_delay<=0;field_start<=0;fault_history<=0;
        end else begin
            previous_ce<=sample_ce;ce_seen<=1;
            if(sample_ce) previous_hs<=hs_n_sampled;
            sample_ce_out<=sample_ce;rgb_out<=rgb_sampled;
            line_start<=0;field_start<=0;
            // Horizontal acquisition starts at an observed edge, then requires
            // consecutive complete lines. RGB and line event share one stage.
            if(bad_ce || bad_h) begin
                h_locked<=0;h_good<=0;h_age<=0;
                have_hs<=h_edge && !bad_ce;
                if(bad_ce)fault_history[0]<=1;
                if(bad_h)fault_history[1]<=1;
            end else if(h_edge) begin
                h_age<=0;have_hs<=1;
                if(have_hs) begin
                    if(h_good<HS_GOOD_INTERVALS)h_good<=h_good+1'b1;
                    if(h_good>=HS_GOOD_INTERVALS-1)begin h_locked<=1;line_start<=1;end
                end
            end else if(have_hs) h_age<=h_age+1'b1;

            if(vs_sync[1]==vs_level)vs_count<=0;
            else if(vs_count==VS_FILTER_CYCLES-1) begin
                vs_count<=0;vs_level<=vs_sync[1];
            end else vs_count<=vs_count+1'b1;

            // A first field edge only anchors the period measurement. The next
            // valid interval permits output, without storing a frame of pixels.
            if(!h_locked || bad_ce || bad_h) begin
                have_vs<=0;v_locked<=0;v_age<=0;vs_pending<=0;
            end else if(vs_fall) begin
                v_age<=0;have_vs<=1;vs_pending<=0;
                if(have_vs && v_age+1>=MIN_FIELD_CYCLES && v_age+1<=MAX_FIELD_CYCLES) begin
                    v_locked<=1;
                    if(VS_ALIGN_CYCLES==0)field_start<=1;
                    else begin vs_pending<=1;vs_delay<=VS_ALIGN_CYCLES-1;end
                end else begin
                    v_locked<=0;
                    if(have_vs)fault_history[2]<=1;
                end
            end else begin
                if(have_vs) begin
                    if(v_age>=MAX_FIELD_CYCLES-1) begin
                        v_locked<=0;have_vs<=0;vs_pending<=0;fault_history[2]<=1;
                    end else v_age<=v_age+1'b1;
                end
                if(vs_pending) begin
                    if(vs_delay==0)begin field_start<=1;vs_pending<=0;end
                    else vs_delay<=vs_delay-1'b1;
                end
            end
        end
    end
endmodule
