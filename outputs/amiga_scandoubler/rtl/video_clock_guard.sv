`timescale 1ns/1ps
// Reference-clock supervisor. This does not generate or model a PLL.
// clk_ref must continue running when clk_video stops. qualified_ref is a
// stable reference-domain configuration/power permission, NOT video_allowed
// from adc_power_sequence (that would create a lock acquisition dependency).
module video_clock_guard #(
    parameter integer HEARTBEAT_BITS=8,
    parameter integer MIN_EDGE_CYCLES=40,
    parameter integer MAX_EDGE_CYCLES=80,
    parameter integer GOOD_INTERVALS=4,
    parameter integer TW=$clog2(MAX_EDGE_CYCLES+2),
    parameter integer GW=$clog2(GOOD_INTERVALS+1)
)(
    input wire clk_ref, clk_video, reset,
    input wire qualified_ref, pll_lock,
    output wire reset_video, output_permitted,
    output wire ready_ref, dac_psave_n
);
    initial begin
        if(HEARTBEAT_BITS<2 || MIN_EDGE_CYCLES<4 ||
           MAX_EDGE_CYCLES<=MIN_EDGE_CYCLES || GOOD_INTERVALS<2)
            $fatal(1,"Invalid clock supervision parameters");
    end
    // Heartbeat is independent of monitor status to allow reacquisition.
    // Only one counter bit crosses domains, never the multi-bit counter.
    reg [HEARTBEAT_BITS-1:0] heartbeat_count;
    always @(posedge clk_video or posedge reset)
        if(reset) heartbeat_count<=0;
        else heartbeat_count<=heartbeat_count+1'b1;

    wire prerequisites=qualified_ref && pll_lock && !reset;
    (* ASYNC_REG="TRUE" *) reg [1:0] heartbeat_sync;
    (* ASYNC_REG="TRUE" *) reg [1:0] prerequisites_sync;
    reg heartbeat_last, seen_edge, healthy;
    reg [TW-1:0] age;
    reg [GW-1:0] good;
    always @(posedge clk_ref or negedge prerequisites) begin
        if(!prerequisites) prerequisites_sync<=0;
        else prerequisites_sync<={prerequisites_sync[0],1'b1};
    end
    always @(posedge clk_ref or posedge reset) begin
        if(reset) heartbeat_sync<=0;
        else heartbeat_sync<={heartbeat_sync[0],heartbeat_count[HEARTBEAT_BITS-1]};
    end
    always @(posedge clk_ref or negedge prerequisites) begin
        if(!prerequisites) begin
            heartbeat_last<=0;seen_edge<=0;healthy<=0;age<=0;good<=0;
        end else if(!prerequisites_sync[1]) begin
            heartbeat_last<=heartbeat_sync[1];seen_edge<=0;
            healthy<=0;age<=0;good<=0;
        end else begin
            heartbeat_last<=heartbeat_sync[1];
            if(heartbeat_sync[1]!=heartbeat_last) begin
                age<=0;seen_edge<=1;
                if(seen_edge && age+1>=MIN_EDGE_CYCLES && age+1<=MAX_EDGE_CYCLES) begin
                    if(good<GOOD_INTERVALS) good<=good+1'b1;
                    if(good>=GOOD_INTERVALS-1) healthy<=1;
                end else begin good<=0;healthy<=0;end
            end else if(age>=MAX_EDGE_CYCLES-1) begin
                age<=MAX_EDGE_CYCLES;seen_edge<=0;good<=0;healthy<=0;
            end else age<=age+1'b1;
        end
    end
    wire permit=prerequisites && prerequisites_sync[1] && healthy;
    // Wake DAC while reset/blank remain asserted for three video edges.
    // Fault assertion does not depend on another video clock edge.
    assign dac_psave_n=permit;
    // Assert even with a stopped video clock; deassert only on video edges.
    (* ASYNC_REG="TRUE" *) reg [2:0] release_pipe;
    always @(posedge clk_video or negedge permit)
        if(!permit) release_pipe<=3'b111;
        else release_pipe<={release_pipe[1:0],1'b0};
    assign reset_video=|release_pipe;
    assign output_permitted=permit && !reset_video;
    (* ASYNC_REG="TRUE" *) reg [1:0] ready_sync;
    always @(posedge clk_ref or negedge prerequisites)
        if(!prerequisites) ready_sync<=0;
        else ready_sync<={ready_sync[0],output_permitted};
    assign ready_ref=ready_sync[1];
endmodule
