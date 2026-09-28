`timescale 1ns/1ps
module tb_line_double;
    parameter integer N = 32;
    localparam AW = $clog2(N);
    reg clk=0, reset=1, ce=0, sol=0;
    reg [23:0] din=0;
    wire [23:0] dout;
    wire valid, osol, error;
    wire [AW-1:0] ox;
    integer l,t,checks=0;
    reg [23:0] expected;
    line_double #(.H_SAMPLES(N)) dut(clk,reset,ce,sol,din,dout,valid,osol,ox,error);
    always #5 clk = !clk;
    function [23:0] pattern(input integer row, input integer x);
        pattern = ((row*24'h319b7) ^ (x*24'h10213)) & 24'hffffff;
    endfunction
    task tick;
        begin @(posedge clk); #1; end
    endtask
    initial begin
        tick(); @(negedge clk); reset=0;
        for(l=0;l<12;l=l+1) begin
            for(t=0;t<2*N;t=t+1) begin
                ce=(t%2==0); sol=(t==0); din=pattern(l,t/2);
                tick();
                if(error) $fatal(1,"unexpected protocol error N=%0d l=%0d t=%0d",N,l,t);
                if(l==0) begin
                    if(valid) $fatal(1,"uninitialized RAM exposed");
                end else begin
                    expected=pattern(l-1,t%N);
                    if(!valid || dout!==expected || ox!==(t%N) || osol!==(t%N==0))
                        $fatal(1,"bad output l=%0d t=%0d got=%h expected=%h x=%d valid=%b sol=%b",l,t,dout,expected,ox,valid,osol);
                    checks=checks+1;
                end
                @(negedge clk);
            end
        end
        // Loss of line boundary must not repeat old imagery indefinitely.
        ce=1; sol=0; tick();
        if(valid || !error) $fatal(1,"missing line was not rejected");
        @(negedge clk); reset=1; tick();
        if(valid || error) $fatal(1,"reset did not clear status");
        @(negedge clk); reset=0; sol=1; ce=1; tick();
        @(negedge clk); sol=0; ce=1; tick();
        if(!error || valid) $fatal(1,"invalid sample cadence was not rejected");
        $display("PASS line_double N=%0d: %0d RGB samples, bank swaps, startup blank, sync loss, cadence error, reset",N,checks);
        $finish;
    end
endmodule
