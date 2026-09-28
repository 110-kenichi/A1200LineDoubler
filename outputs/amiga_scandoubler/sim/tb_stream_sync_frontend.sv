`timescale 1ns/1ps
module tb_stream_sync_frontend;
    parameter integer N=32,FL=625,ALIGN=7;
    reg clk=0,reset=1,sample_ce=0,hs_n_sampled=1,vs_n_async=1;
    reg [23:0] rgb_sampled=0;
    wire sample_ce_out,line_start,field_start,reset_core,sync_valid;
    wire [23:0] rgb_out;
    wire [2:0] fault_history;
    integer t=0,fields=0,lines=0,pixels=0,last_field=-1;
    integer line_period=2*N,field_period=N*FL;
    reg no_hs=0,no_vs=0,bad_ce=0,check_fields=1,glitches=0;
    always #5 clk=~clk;
    stream_sync_frontend #(.H_SAMPLES(N),.VS_ALIGN_CYCLES(ALIGN)) dut(.*);
    // Deliberately start fields away from an H boundary; odd FL alternates
    // full and half-line phase. ADC input capture itself is not modeled.
    always @(negedge clk) begin
        if(reset)begin t=0;sample_ce=0;hs_n_sampled=1;vs_n_async=1;rgb_sampled=0;end
        else begin
            sample_ce=bad_ce?1:(t%2==0);
            hs_n_sampled=no_hs || t%line_period>=4;
            vs_n_async=no_vs || (t%field_period<10 || t%field_period>=30);
            if(glitches && t%field_period>=100 && t%field_period<102)vs_n_async=0;
            rgb_sampled=t & 24'hffffff;
            t=t+1;
        end
    end
    always @(posedge clk) begin
        #1;
        if(!reset) begin
            if(sample_ce_out!==sample_ce || rgb_out!==rgb_sampled) $fatal(1,"Stream stage misaligned");
            if(sample_ce_out)pixels=pixels+1;
            if(line_start) begin
                if(!sample_ce_out || hs_n_sampled || reset_core) $fatal(1,"Bad line event");
                lines=lines+1;
            end
            if(field_start && check_fields) begin
                if((t-1)%(N*FL)!=10+5+ALIGN) $fatal(1,"Field qualification/alignment delay t=%0d",t-1);
                if(last_field>=0 && t-last_field!=N*FL) $fatal(1,"Field phase lost");
                if(!sync_valid) $fatal(1,"Unqualified field");
                last_field=t;fields=fields+1;
            end
        end
    end
    task ticks(input integer count);repeat(count)begin @(posedge clk);#2;end endtask
    task restart;
        begin
            @(posedge clk);#2;reset=1;no_hs=0;no_vs=0;bad_ce=0;line_period=2*N;
            check_fields=1;last_field=-1;fields=0;ticks(4);reset=0;
        end
    endtask
    initial begin
        restart();glitches=1;ticks(6*N*FL);
        if(!sync_valid || fields!=4) $fatal(1,"Normal field acquisition %0d",fields);
        if(fault_history!=0) $fatal(1,"Short VS glitch was not filtered");
        check_fields=0;no_vs=1;ticks(661*N);
        if(sync_valid || !fault_history[2]) $fatal(1,"Missing VS not detected");
        no_vs=0;ticks(3*N*FL);if(!sync_valid) $fatal(1,"VS reacquisition failed");
        no_hs=1;ticks(2*N+3);if(!reset_core || sync_valid || !fault_history[1]) $fatal(1,"Missing HS not detected");
        no_hs=0;ticks(3*N*FL);if(!sync_valid) $fatal(1,"HS reacquisition failed");
        bad_ce=1;ticks(5);if(!reset_core || !fault_history[0]) $fatal(1,"Bad CE not detected");
        bad_ce=0;ticks(3*N*FL);if(!sync_valid) $fatal(1,"CE reacquisition failed");
        field_period=100*N;ticks(400*N);if(sync_valid) $fatal(1,"Short field accepted");
        field_period=N*FL;ticks(3*N*FL);if(!sync_valid) $fatal(1,"Field period reacquisition failed");
        line_period=2*N+2;ticks(10*line_period);if(!reset_core) $fatal(1,"Long line silently accepted");
        line_period=2*N-2;ticks(10*line_period);if(!reset_core) $fatal(1,"Short line silently accepted");
        $display("PASS stream_sync_frontend N=%0d FL=%0d ALIGN=%0d: %0d samples, %0d line events; odd/even field phase, missing H/V, bad CE, reacquisition, long/short rejection",N,FL,ALIGN,pixels,lines);
        $finish;
    end
    initial begin #1000000000;$fatal(1,"Timeout");end
endmodule
