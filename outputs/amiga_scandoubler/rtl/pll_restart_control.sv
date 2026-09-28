`timescale 1ns/1ps
// Always-on reference-domain PLL lifecycle. Heartbeat source runs directly
// from ADC clock and is independent of PLL reset and video permission.
module pll_restart_control #(
    parameter integer HEARTBEAT_BITS=8,MIN_EDGE_CYCLES=80,MAX_EDGE_CYCLES=170,
    parameter integer PERIOD_TOLERANCE=2,GOOD_INTERVALS=8,
    parameter integer RESET_HOLD_CYCLES=270,LOCK_TIMEOUT_CYCLES=270000,
    parameter integer TW=$clog2(MAX_EDGE_CYCLES+2),
    parameter integer GW=$clog2(GOOD_INTERVALS+1),
    parameter integer CW=$clog2(LOCK_TIMEOUT_CYCLES+1)
)(
    input wire clk_ref,adc_clock,reset,qualified_ref,pll_lock,video_ready_ref,
    output wire pll_reset,run_ref,input_stable,
    output reg [2:0] fault_history
);
    localparam ACQUIRE=0,HOLD_RESET=1,WAIT_LOCK=2,RUN=3;
    reg [1:0] state;
    reg [HEARTBEAT_BITS-1:0] heartbeat;
    (* ASYNC_REG="TRUE" *)reg [1:0] hb_sync,lock_sync;
    reg last_hb,seen_edge,stable,lock_was_low;
    reg [TW-1:0] age,period_last;
    reg [GW-1:0] good;
    reg [CW-1:0] count;
    wire edge_seen=hb_sync[1]!=last_hb;
    wire period_ok=age+1>=MIN_EDGE_CYCLES && age+1<=MAX_EDGE_CYCLES;
    wire consistent=age+1+PERIOD_TOLERANCE>=period_last && age+1<=period_last+PERIOD_TOLERANCE;
    assign input_stable=stable && qualified_ref && !reset;
    assign pll_reset=reset || !qualified_ref || !stable || state==ACQUIRE || state==HOLD_RESET;
    assign run_ref=state==RUN && !pll_reset;
    initial begin
        if(HEARTBEAT_BITS<2 || MIN_EDGE_CYCLES<4 || MAX_EDGE_CYCLES<=MIN_EDGE_CYCLES ||
           PERIOD_TOLERANCE<1 || GOOD_INTERVALS<2 || RESET_HOLD_CYCLES<2 ||
           LOCK_TIMEOUT_CYCLES<=RESET_HOLD_CYCLES)
            $fatal(1,"Invalid PLL restart timing");
    end
    always @(posedge adc_clock or posedge reset)
        if(reset)heartbeat<=0;else heartbeat<=heartbeat+1'b1;
    always @(posedge clk_ref) begin
        if(reset)begin hb_sync<=0;lock_sync<=0;end
        else begin hb_sync<={hb_sync[0],heartbeat[HEARTBEAT_BITS-1]};lock_sync<={lock_sync[0],pll_lock};end
    end
    always @(posedge clk_ref) begin
        if(reset || !qualified_ref)begin
            last_hb<=hb_sync[1];seen_edge<=0;stable<=0;age<=0;period_last<=0;good<=0;
        end else begin
            last_hb<=hb_sync[1];
            if(edge_seen)begin
                age<=0;seen_edge<=1;period_last<=age+1;
                if(seen_edge && period_ok && (good==0 || consistent))begin
                    if(good<GOOD_INTERVALS)good<=good+1'b1;
                    if(good>=GOOD_INTERVALS-1)stable<=1;
                end else begin good<=0;stable<=0;end
            end else if(age>=MAX_EDGE_CYCLES-1)begin stable<=0;seen_edge<=0;good<=0;age<=MAX_EDGE_CYCLES;end
            else age<=age+1'b1;
        end
    end
    always @(posedge clk_ref) begin
        if(reset)begin state<=ACQUIRE;count<=0;lock_was_low<=0;fault_history<=0;end
        else if(!qualified_ref)begin state<=ACQUIRE;count<=0;lock_was_low<=0;end
        else if(!stable)begin
            if(state==RUN)fault_history[0]<=1;
            state<=ACQUIRE;count<=0;lock_was_low<=0;
        end else case(state)
          ACQUIRE:begin state<=HOLD_RESET;count<=0;lock_was_low<=0;end
          HOLD_RESET:begin
              if(!lock_sync[1])lock_was_low<=1;
              if(count==RESET_HOLD_CYCLES-1)begin state<=WAIT_LOCK;count<=0;end
              else count<=count+1'b1;
          end
          WAIT_LOCK:begin
              if(!lock_sync[1])lock_was_low<=1;
              if(lock_was_low && lock_sync[1] && video_ready_ref)begin state<=RUN;count<=0;end
              else if(count==LOCK_TIMEOUT_CYCLES-1)begin
                  fault_history[2]<=1;state<=HOLD_RESET;count<=0;lock_was_low<=0;
              end else count<=count+1'b1;
          end
          RUN:if(!lock_sync[1] || !video_ready_ref)begin
              fault_history[1]<=1;state<=HOLD_RESET;count<=0;lock_was_low<=0;
          end
          default:begin state<=ACQUIRE;count<=0;lock_was_low<=0;end
        endcase
    end
endmodule
